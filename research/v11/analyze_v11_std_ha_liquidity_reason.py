"""Rebuild FAST and STD H4-HA Children and compare liquidity explanations.

This is a consumed-data mechanism diagnostic.  It reconstructs both HA streams
from causal H4 bars, creates each base's own runs and Children, and replays the
existing structural Hard SL against chronological raw M1.  Liquidity objects
are read only through their causal known/consumed timestamps.

No result from this script has trading or production authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd



def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def active_route(
    objects: pd.DataFrame,
    decision: pd.Timestamp,
    direction: int,
    reference_price: float,
    timeframe: str,
) -> tuple[float, str | None]:
    active = objects[
        (objects["timeframe"] == timeframe)
        & (objects["side"] == direction)
        & (objects["known_at"] <= decision)
        & (objects["consumed_at"].isna() | (objects["consumed_at"] >= decision))
    ]
    if direction == 1:
        active = active[active["price"] > reference_price]
        if active.empty:
            return np.nan, None
        row = active.loc[active["price"].idxmin()]
    else:
        active = active[active["price"] < reference_price]
        if active.empty:
            return np.nan, None
        row = active.loc[active["price"].idxmax()]
    return float(row["price"]), str(row["object_id"])


def causal_context(row: pd.Series) -> str:
    if bool(row["same_h4_consumed"]):
        return "H4_ARRIVAL_WITH_FARTHER_ROUTE" if bool(row["h4_route_open"]) else "H4_ARRIVAL_NO_FARTHER_KNOWN"
    if bool(row["h4_route_open"]):
        return "TRANSIT_TO_H4"
    if bool(row["same_h1_consumed"] or row["h1_route_open"]):
        return "LOCAL_H1_ONLY"
    return "NO_KNOWN_LIQUIDITY_CONTEXT"


def nha_explanation(row: pd.Series) -> str:
    if not bool(row["immediate_nha"]):
        return "NO_IMMEDIATE_NHA"
    if bool(row["same_h4_consumed"]):
        return "ARRIVAL_RESPONSE_ROUTE_REMAINS" if bool(row["h4_route_open"]) else "ARRIVAL_RESPONSE_NO_FARTHER_KNOWN"
    if bool(row["h4_route_open"]):
        if bool(row["route_still_open_after_nha"]) and bool(row["journey_net_progress"]):
            return "IN_TRANSIT_COUNTERFLOW"
        return "ROUTE_PRESENT_NO_NET_PROGRESS"
    if bool(row["same_h1_consumed"] or row["h1_route_open"]):
        return "LOCAL_H1_ROTATION"
    return "UNANCHORED_ROTATION"


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m1", required=True, type=Path)
    parser.add_argument("--h4", required=True, type=Path)
    parser.add_argument("--objects", required=True, type=Path)
    parser.add_argument("--fast-universe", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def build_ha(h4: pd.DataFrame, close_weight: float, alpha: float) -> pd.DataFrame:
    result = h4.copy()
    close = (
        result["open"]
        + result["high"]
        + result["low"]
        + close_weight * result["close"]
    ) / (3.0 + close_weight)
    ha_open = np.empty(len(result), dtype=float)
    ha_open[0] = 0.5 * (float(result.iloc[0]["open"]) + float(result.iloc[0]["close"]))
    close_values = close.to_numpy(dtype=float)
    for i in range(1, len(result)):
        ha_open[i] = alpha * ha_open[i - 1] + (1.0 - alpha) * close_values[i - 1]
    result["ha_open"] = ha_open
    result["ha_close"] = close_values
    result["ha_high"] = np.maximum.reduce(
        [result["high"].to_numpy(dtype=float), ha_open, close_values]
    )
    result["ha_low"] = np.minimum.reduce(
        [result["low"].to_numpy(dtype=float), ha_open, close_values]
    )
    result["dir"] = np.where(result["ha_close"] >= result["ha_open"], 1, -1)
    result["decision"] = result["h4_start"] + pd.Timedelta(hours=4)
    result["rid"] = (result["dir"] != result["dir"].shift()).cumsum().astype(int)
    result["k"] = result.groupby("rid", sort=False).cumcount() + 1
    result["L"] = result.groupby("rid", sort=False)["rid"].transform("size")
    run_lengths = result.groupby("rid", sort=True)["L"].first()
    result["prev_run_len"] = result["rid"].map(lambda rid: run_lengths.get(rid - 1, np.nan))
    result["next_run_len"] = result["rid"].map(lambda rid: run_lengths.get(rid + 1, np.nan))
    result["run_start_open"] = result.groupby("rid", sort=False)["open"].transform("first")
    next_run_decision = result.groupby("rid", sort=True)["decision"].first().shift(-1)
    result["run_end_decision"] = result["rid"].map(next_run_decision)
    return result


def load_m1(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        sep="\t",
        usecols=["<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>"],
        dtype={"<OPEN>": float, "<HIGH>": float, "<LOW>": float},
    )
    frame["timestamp"] = pd.to_datetime(
        frame["<DATE>"].astype(str) + " " + frame["<TIME>"].astype(str),
        format="%Y.%m.%d %H:%M:%S",
    )
    if not frame["timestamp"].is_monotonic_increasing or frame["timestamp"].duplicated().any():
        raise ValueError("M1 must be strictly chronological")
    return frame.rename(
        columns={"<OPEN>": "open", "<HIGH>": "high", "<LOW>": "low"}
    )[["timestamp", "open", "high", "low"]]


def replay_children(
    base: str, ha: pd.DataFrame, stop_ha: pd.DataFrame, m1: pd.DataFrame
) -> pd.DataFrame:
    ts = m1["timestamp"].to_numpy(dtype="datetime64[ns]")
    opens = m1["open"].to_numpy(dtype=float)
    highs = m1["high"].to_numpy(dtype=float)
    lows = m1["low"].to_numpy(dtype=float)
    rows: list[dict[str, object]] = []

    for i in range(181, len(ha)):
        row = ha.iloc[i]
        decision = pd.Timestamp(row["decision"])
        run_end = row["run_end_decision"]
        if decision.year < 2022 or decision.year > 2026 or pd.isna(run_end):
            continue
        entry_idx = int(np.searchsorted(ts, np.datetime64(decision), side="left"))
        exit_idx = int(np.searchsorted(ts, np.datetime64(pd.Timestamp(run_end)), side="left"))
        if entry_idx >= len(ts) or exit_idx >= len(ts):
            continue
        entry_time = pd.Timestamp(ts[entry_idx])
        exit_time = pd.Timestamp(ts[exit_idx])
        if entry_time - decision > pd.Timedelta(hours=4):
            continue
        direction = int(row["dir"])
        entry = float(opens[entry_idx])
        previous = stop_ha.iloc[i - 1]
        stop = float(previous["ha_low"] if direction > 0 else previous["ha_high"])
        if (direction > 0 and stop >= entry) or (direction < 0 and stop <= entry):
            continue
        risk = abs(entry - stop)
        touched = lows[entry_idx : exit_idx + 1] <= stop if direction > 0 else highs[entry_idx : exit_idx + 1] >= stop
        positions = np.flatnonzero(touched)
        stop_hit = int(len(positions) > 0)
        first_stop_idx = entry_idx + int(positions[0]) if stop_hit else -1
        same_m1_ambiguous = int(stop_hit and first_stop_idx == exit_idx)
        actual_exit_time = pd.Timestamp(ts[first_stop_idx]) if stop_hit else exit_time
        actual_exit = stop if stop_hit else float(opens[exit_idx])
        pnl = direction * (actual_exit - entry)
        rows.append(
            {
                "base": base,
                "signal_id": f"{base}_{decision:%Y%m%d%H%M}_{'L' if direction > 0 else 'S'}_{int(row['k'])}",
                "decision": decision,
                "entry_time": entry_time,
                "exit_time": actual_exit_time,
                "year": decision.year,
                "dir": direction,
                "rid": int(row["rid"]),
                "k": int(row["k"]),
                "L": int(row["L"]),
                "prev_run_len": float(row["prev_run_len"]) if pd.notna(row["prev_run_len"]) else np.nan,
                "next_run_length": float(row["next_run_len"]) if pd.notna(row["next_run_len"]) else np.nan,
                "run_end_decision": pd.Timestamp(run_end),
                "wave_start": pd.Timestamp(row["h4_start"]),
                "raw_h4_open": float(row["open"]),
                "raw_h4_close": float(row["close"]),
                "run_start_open": float(row["run_start_open"]),
                "entry": entry,
                "stop": stop,
                "exit": actual_exit,
                "stop_hit": stop_hit,
                "same_m1_exit_stop_ambiguous": same_m1_ambiguous,
                "R": pnl / risk,
            }
        )
    return pd.DataFrame(rows)


def add_liquidity_reason(
    children: pd.DataFrame, objects: pd.DataFrame, h4_by_start: pd.DataFrame
) -> pd.DataFrame:
    work = objects.copy()
    work["consume_h4_start"] = work["consumed_at"].dt.floor("4h")
    consumed_by_h4 = {
        key: group
        for key, group in work.dropna(subset=["consumed_at"]).groupby("consume_h4_start")
    }
    object_lookup = work.set_index("object_id")
    rows: list[dict[str, object]] = []
    for child in children.itertuples(index=False):
        row = child._asdict()
        decision = pd.Timestamp(child.decision)
        direction = int(child.dir)
        reference = float(child.raw_h4_close)
        consumed = consumed_by_h4.get(pd.Timestamp(child.wave_start), pd.DataFrame())
        row["same_h4_consumed"] = int(
            not consumed.empty
            and ((consumed["timeframe"] == "H4") & (consumed["side"] == direction)).any()
        )
        row["same_h1_consumed"] = int(
            not consumed.empty
            and ((consumed["timeframe"] == "H1") & (consumed["side"] == direction)).any()
        )
        h4_target, h4_target_id = active_route(work, decision, direction, reference, "H4")
        h1_target, h1_target_id = active_route(work, decision, direction, reference, "H1")
        row["h4_route_open"] = int(np.isfinite(h4_target))
        row["h4_route_target"] = h4_target
        row["h4_route_object_id"] = h4_target_id
        row["h1_route_open"] = int(np.isfinite(h1_target))
        row["h1_route_target"] = h1_target
        row["h1_route_object_id"] = h1_target_id
        row["immediate_nha"] = int(int(child.k) == int(child.L))
        row["one_bar_triplet_rotation"] = int(
            row["immediate_nha"]
            and float(child.prev_run_len) == 1.0
            and int(child.L) == 1
            and float(child.next_run_length) == 1.0
        )
        row["short_run_triplet_rotation"] = int(
            row["immediate_nha"]
            and float(child.prev_run_len) <= 2.0
            and int(child.L) <= 2
            and float(child.next_run_length) <= 2.0
        )
        row["nha_raw_close"] = np.nan
        row["pair_net_progress"] = 0
        row["journey_net_progress"] = 0
        row["route_still_open_after_nha"] = 0
        if row["immediate_nha"] and decision in h4_by_start.index:
            nha_close = float(h4_by_start.loc[decision]["close"])
            row["nha_raw_close"] = nha_close
            row["pair_net_progress"] = int(
                direction * (nha_close - float(child.raw_h4_open)) > 0.0
            )
            row["journey_net_progress"] = int(
                direction * (nha_close - float(child.run_start_open)) > 0.0
            )
            if np.isfinite(h4_target) and h4_target_id in object_lookup.index:
                target = object_lookup.loc[h4_target_id]
                route_alive = pd.isna(target["consumed_at"]) or pd.Timestamp(
                    target["consumed_at"]
                ) >= pd.Timestamp(child.run_end_decision)
                target_ahead = direction * (h4_target - nha_close) > 0.0
                row["route_still_open_after_nha"] = int(route_alive and target_ahead)
        rows.append(row)
    result = pd.DataFrame(rows)
    result["causal_context"] = result.apply(causal_context, axis=1)
    result["nha_explanation"] = result.apply(nha_explanation, axis=1)
    return result


def summarize(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    overall: list[dict[str, object]] = []
    explanations: list[dict[str, object]] = []
    transfers: list[dict[str, object]] = []
    for base, source in frame.groupby("base", sort=False):
        k1 = source[source["k"] == 1]
        immediate = source[source["immediate_nha"].astype(bool)]
        current_streak = 0
        max_streak = 0
        for stopped in source.sort_values("decision")["stop_hit"].astype(bool):
            current_streak = current_streak + 1 if stopped else 0
            max_streak = max(max_streak, current_streak)
        overall.append(
            {
                "base": base,
                "children": len(source),
                "stops": int(source["stop_hit"].sum()),
                "stop_rate": float(source["stop_hit"].mean()),
                "sum_R": float(source["R"].sum()),
                "mean_R": float(source["R"].mean()),
                "k1_children": len(k1),
                "k1_stops": int(k1["stop_hit"].sum()),
                "k1_stop_rate": float(k1["stop_hit"].mean()),
                "k1_sum_R": float(k1["R"].sum()),
                "immediate_nha": len(immediate),
                "mean_run_length_at_end": float(immediate["L"].mean()),
                "one_bar_triplets": int(immediate["one_bar_triplet_rotation"].sum()),
                "short_run_triplets": int(immediate["short_run_triplet_rotation"].sum()),
                "max_stop_streak": max_streak,
            }
        )
        for explanation, group in immediate.groupby("nha_explanation", sort=True):
            explanations.append(
                {
                    "base": base,
                    "nha_explanation": explanation,
                    "n": len(group),
                    "stops_on_final_pha_child": int(group["stop_hit"].sum()),
                    "final_pha_stop_rate": float(group["stop_hit"].mean()),
                    "sum_R": float(group["R"].sum()),
                }
            )
        prior = immediate.set_index("rid")["nha_explanation"]
        k1 = k1.copy()
        k1["prior_nha_explanation"] = k1["rid"].map(lambda rid: prior.get(int(rid) - 1))
        k1 = k1[k1["prior_nha_explanation"].notna()]
        for explanation, group in k1.groupby("prior_nha_explanation", sort=True):
            transfers.append(
                {
                    "base": base,
                    "prior_nha_explanation": explanation,
                    "n": len(group),
                    "stops": int(group["stop_hit"].sum()),
                    "stop_rate": float(group["stop_hit"].mean()),
                    "mean_run_length": float(group["L"].mean()),
                    "L6plus_rate": float((group["L"] >= 6).mean()),
                    "sum_R": float(group["R"].sum()),
                }
            )
    return pd.DataFrame(overall), pd.DataFrame(explanations), pd.DataFrame(transfers)


def stratified_summary(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["k_bucket"] = np.select(
        [work["k"] == 1, work["k"] == 2, work["k"] == 3],
        ["K1", "K2", "K3"],
        default="K4+",
    )
    rows: list[dict[str, object]] = []
    cuts = [
        ("YEAR", ["base", "year"]),
        ("K", ["base", "k_bucket"]),
        ("SIDE", ["base", "dir"]),
    ]
    for cut, columns in cuts:
        for keys, group in work.groupby(columns, sort=True):
            values = keys if isinstance(keys, tuple) else (keys,)
            record = {"cut": cut, "base": values[0], "group": str(values[1])}
            record.update(
                n=len(group),
                stops=int(group["stop_hit"].sum()),
                stop_rate=float(group["stop_hit"].mean()),
                sum_R=float(group["R"].sum()),
                mean_R=float(group["R"].mean()),
            )
            rows.append(record)
    return pd.DataFrame(rows)


def tail_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for base, group in frame.groupby("base", sort=False):
        values = group["R"].to_numpy(dtype=float)
        price_pnl = (
            group["dir"].to_numpy(dtype=float)
            * (group["exit"].to_numpy(dtype=float) - group["entry"].to_numpy(dtype=float))
        )
        risk = np.abs(
            group["entry"].to_numpy(dtype=float) - group["stop"].to_numpy(dtype=float)
        )
        ordered = np.sort(values)[::-1]
        top_n = max(1, int(np.ceil(len(ordered) * 0.01)))
        for cap in (3.0, 6.0, 10.0, 20.0, 50.0):
            rows.append(
                {
                    "base": base,
                    "view": f"R_CAP_{cap:g}",
                    "n": len(values),
                    "sum_R": float(np.clip(values, -1.0, cap).sum()),
                    "detail": np.nan,
                }
            )
        rows.extend(
            [
                {
                    "base": base,
                    "view": "RAW_SUM_R",
                    "n": len(values),
                    "sum_R": float(values.sum()),
                    "detail": np.nan,
                },
                {
                    "base": base,
                    "view": "TOP_1_PERCENT_SUM_R",
                    "n": top_n,
                    "sum_R": float(ordered[:top_n].sum()),
                    "detail": float(ordered[:top_n].sum() / values.sum()),
                },
                {
                    "base": base,
                    "view": "MAX_R",
                    "n": 1,
                    "sum_R": float(values.max()),
                    "detail": float(risk[int(np.argmax(values))]),
                },
                {
                    "base": base,
                    "view": "RAW_PRICE_PNL",
                    "n": len(values),
                    "sum_R": np.nan,
                    "detail": float(price_pnl.sum()),
                },
            ]
        )
    return pd.DataFrame(rows)


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    h4 = pd.read_csv(args.h4, parse_dates=["h4_start"]).sort_values("h4_start").reset_index(drop=True)
    objects = pd.read_csv(args.objects, parse_dates=["source_time", "known_at", "consumed_at"])
    m1 = load_m1(args.m1)

    fast = build_ha(h4, close_weight=2.0, alpha=0.25)
    std = build_ha(h4, close_weight=1.0, alpha=0.50)
    fast_error = float(np.max(np.abs(fast["ha_open"] - h4["fast_ha_open"])))
    fast_close_error = float(np.max(np.abs(fast["ha_close"] - h4["fast_ha_close"])))
    if fast_error > 1e-9 or fast_close_error > 1e-9 or not np.array_equal(fast["dir"], h4["fast_dir"]):
        raise ValueError("FAST HA reconstruction does not match causal H4 artifact")

    ledgers = []
    for base, stream in (("FAST", fast), ("STD", std)):
        children = replay_children(base, stream, std, m1)
        ledgers.append(add_liquidity_reason(children, objects, h4.set_index("h4_start")))
    ledger = pd.concat(ledgers, ignore_index=True)
    overall, explanations, transfers = summarize(ledger)
    stratified = stratified_summary(ledger)
    tails = tail_summary(ledger)

    official_fast = pd.read_csv(
        args.fast_universe,
        usecols=["decision", "dir", "k", "L", "stop_hit", "R", "entry", "stop"],
        parse_dates=["decision"],
    )
    rebuilt_fast = ledger[ledger["base"] == "FAST"]
    validation = official_fast.merge(
        rebuilt_fast,
        on="decision",
        suffixes=("_official", "_rebuilt"),
        how="outer",
        indicator=True,
    )
    both = validation[validation["_merge"] == "both"]
    mismatch_count = sum(
        int((both[f"{column}_official"] != both[f"{column}_rebuilt"]).sum())
        for column in ("dir", "k", "L", "stop_hit")
    )
    max_r_error = float(np.max(np.abs(both["R_official"] - both["R_rebuilt"])))
    if (
        len(validation) != len(official_fast)
        or not (validation["_merge"] == "both").all()
        or mismatch_count
        or max_r_error > 1e-12
    ):
        raise ValueError("rebuilt FAST baseline does not match official V10 universe")

    ledger_path = args.out_dir / "V11_FAST_STD_HA_LIQUIDITY_REASON_LEDGER.csv"
    overall_path = args.out_dir / "V11_FAST_STD_HA_OVERALL_COMPARISON.csv"
    explanation_path = args.out_dir / "V11_FAST_STD_HA_NHA_EXPLANATION.csv"
    transfer_path = args.out_dir / "V11_FAST_STD_HA_K1_TRANSFER.csv"
    stratified_path = args.out_dir / "V11_FAST_STD_HA_STRATIFIED.csv"
    tail_path = args.out_dir / "V11_FAST_STD_HA_TAIL_SENSITIVITY.csv"
    ledger.to_csv(ledger_path, index=False, date_format="%Y-%m-%d %H:%M:%S")
    overall.to_csv(overall_path, index=False)
    explanations.to_csv(explanation_path, index=False)
    transfers.to_csv(transfer_path, index=False)
    stratified.to_csv(stratified_path, index=False)
    tails.to_csv(tail_path, index=False)

    manifest = {
        "status": "CONSUMED_DATA_MECHANISM_DIAGNOSTIC_ONLY",
        "authority": "NO TRADE OR PRODUCTION AUTHORITY",
        "ha_definitions": {
            "FAST": "close=(O+H+L+2C)/5; open=.25*prior_open+.75*prior_close",
            "STD": "close=(O+H+L+C)/4; open=.5*prior_open+.5*prior_close",
        },
        "child_contract": "base-specific direction/run; entry at first M1 at/after H4 decision; Hard SL at prior STD-HA low/high; exit at first opposite base-HA completion; same-M1 stop/exit resolves conservatively as stop",
        "source_sha256": {
            "m1": sha256_file(args.m1),
            "h4": sha256_file(args.h4),
            "objects": sha256_file(args.objects),
            "fast_universe": sha256_file(args.fast_universe),
        },
        "fast_reconstruction_max_open_error": fast_error,
        "fast_reconstruction_max_close_error": fast_close_error,
        "official_fast_validation": {
            "rows": int(len(official_fast)),
            "matched_rows": int(len(both)),
            "categorical_mismatches": int(mismatch_count),
            "max_R_error": max_r_error,
        },
        "outputs": {
            "ledger": str(ledger_path.resolve()),
            "overall": str(overall_path.resolve()),
            "nha_explanation": str(explanation_path.resolve()),
            "k1_transfer": str(transfer_path.resolve()),
            "stratified": str(stratified_path.resolve()),
            "tail_sensitivity": str(tail_path.resolve()),
        },
        "output_sha256": {
            "ledger": sha256_file(ledger_path),
            "overall": sha256_file(overall_path),
            "nha_explanation": sha256_file(explanation_path),
            "k1_transfer": sha256_file(transfer_path),
            "stratified": sha256_file(stratified_path),
            "tail_sensitivity": sha256_file(tail_path),
        },
    }
    manifest_path = args.out_dir / "V11_FAST_STD_HA_LIQUIDITY_REASON_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print("\nOVERALL")
    print(overall.to_string(index=False))
    print("\nNHA EXPLANATION")
    print(explanations.to_string(index=False))
    print("\nK1 TRANSFER")
    print(transfers.to_string(index=False))


if __name__ == "__main__":
    main()
