"""Explain V10/V11 FAST-HA continuation and flip events with causal liquidity context.

This consumed-data semantic diagnostic does not predict the next HA and grants
no trading authority.  At each selected Child decision it records, using only
information known at that decision:

* whether the completed PHA consumed same-side H4 liquidity;
* whether a farther same-side H4 destination remained active;
* whether only local H1 arrival/route context existed;
* or whether no known liquidity context existed.

After the run resolves, an immediate opposite FAST-HA bar is described as an
arrival response, in-transit counterflow, local H1 rotation, or unanchored
rotation.  Future fields are used only for explanation/outcome reporting and
never as causal decision features.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analyze_v11_wave_edge import sha256_file


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--objects", required=True, type=Path)
    parser.add_argument("--h4", required=True, type=Path)
    parser.add_argument("--universe", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


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
    h4_arrival = bool(row["same_h4_consumed"])
    h4_route = bool(row["h4_route_open"])
    local_h1 = bool(row["same_h1_consumed"] or row["h1_route_open"])
    if h4_arrival and h4_route:
        return "H4_ARRIVAL_WITH_FARTHER_ROUTE"
    if h4_arrival:
        return "H4_ARRIVAL_NO_FARTHER_KNOWN"
    if h4_route:
        return "TRANSIT_TO_H4"
    if local_h1:
        return "LOCAL_H1_ONLY"
    return "NO_KNOWN_LIQUIDITY_CONTEXT"


def nha_explanation(row: pd.Series) -> str:
    if not bool(row["immediate_nha"]):
        return "NO_IMMEDIATE_NHA"
    if bool(row["same_h4_consumed"]):
        return (
            "ARRIVAL_RESPONSE_ROUTE_REMAINS"
            if bool(row["h4_route_open"])
            else "ARRIVAL_RESPONSE_NO_FARTHER_KNOWN"
        )
    if bool(row["h4_route_open"]):
        if bool(row["route_still_open_after_nha"]) and bool(row["journey_net_progress"]):
            return "IN_TRANSIT_COUNTERFLOW"
        return "ROUTE_PRESENT_NO_NET_PROGRESS"
    if bool(row["same_h1_consumed"] or row["h1_route_open"]):
        return "LOCAL_H1_ROTATION"
    return "UNANCHORED_ROTATION"


def summary_rows(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    cuts = [
        ("CAUSAL_CONTEXT", "causal_context", frame),
        (
            "NHA_EXPLANATION",
            "nha_explanation",
            frame[frame["immediate_nha"].astype(bool)],
        ),
    ]
    for cut, column, source in cuts:
        periods = [("POOLED", source)]
        periods.extend((str(int(y)), g) for y, g in source.groupby("year", sort=True))
        periods.extend(
            (f"{int(y)}_{'LONG' if int(d) > 0 else 'SHORT'}", g)
            for (y, d), g in source.groupby(["year", "dir"], sort=True)
        )
        for period, subset in periods:
            for value, group in subset.groupby(column, dropna=False, sort=True):
                weight = group["r7g_weight"].astype(float)
                rows.append(
                    {
                        "cut": cut,
                        "period": period,
                        "group": value,
                        "n": int(len(group)),
                        "immediate_nha": int(group["immediate_nha"].sum()),
                        "immediate_nha_rate": float(group["immediate_nha"].mean()),
                        "stops": int(group["stop_hit"].sum()),
                        "stop_rate": float(group["stop_hit"].mean()),
                        "one_bar_triplet_rotations": int(
                            group["one_bar_triplet_rotation"].sum()
                        ),
                        "short_run_triplet_rotations": int(
                            group["short_run_triplet_rotation"].sum()
                        ),
                        "weighted_R": float((group["R"] * weight).sum()),
                    }
                )
    return pd.DataFrame(rows)


def build_all_opportunity_frame(
    universe: pd.DataFrame,
    objects: pd.DataFrame,
    h4: pd.DataFrame,
    run_lengths: dict[int, float],
    run_start_open: dict[int, float],
    selected_ids: set[str],
) -> pd.DataFrame:
    objects = objects.copy()
    objects["consume_h4_start"] = objects["consumed_at"].dt.floor("4h")
    consumed_by_h4 = {
        key: group for key, group in objects.dropna(subset=["consumed_at"]).groupby("consume_h4_start")
    }
    rows: list[dict[str, object]] = []
    for opportunity in universe.itertuples(index=False):
        decision = pd.Timestamp(opportunity.decision)
        wave_start = decision - pd.Timedelta(hours=4)
        if wave_start not in h4.index:
            continue
        state = h4.loc[wave_start]
        direction = int(opportunity.dir)
        reference = float(state["close"])
        consumed = consumed_by_h4.get(wave_start, pd.DataFrame())
        same_h4 = int(
            not consumed.empty
            and ((consumed["timeframe"] == "H4") & (consumed["side"] == direction)).any()
        )
        same_h1 = int(
            not consumed.empty
            and ((consumed["timeframe"] == "H1") & (consumed["side"] == direction)).any()
        )
        h4_target, h4_target_id = active_route(objects, decision, direction, reference, "H4")
        h1_target, h1_target_id = active_route(objects, decision, direction, reference, "H1")
        row = {
            "signal_id": opportunity.signal_id,
            "decision": decision,
            "year": int(opportunity.year),
            "dir": direction,
            "k": int(opportunity.k),
            "rid": int(opportunity.rid),
            "L": int(opportunity.L),
            "prev_run_len": float(opportunity.prev_run_len),
            "run_end_decision": opportunity.run_end_decision,
            "stop_hit": int(opportunity.stop_hit),
            "R": float(opportunity.R),
            "r7g_weight": 1.0,
            "selected_r7g": int(str(opportunity.signal_id) in selected_ids),
            "wave_start": wave_start,
            "raw_h4_open": float(state["open"]),
            "raw_h4_close": reference,
            "run_start_open": run_start_open.get(int(opportunity.rid), np.nan),
            "same_h4_consumed": same_h4,
            "same_h1_consumed": same_h1,
            "h4_route_open": int(np.isfinite(h4_target)),
            "h4_route_target": h4_target,
            "h4_route_object_id": h4_target_id,
            "h1_route_open": int(np.isfinite(h1_target)),
            "h1_route_target": h1_target,
            "h1_route_object_id": h1_target_id,
        }
        row["immediate_nha"] = int(row["k"] == row["L"])
        row["next_run_length"] = run_lengths.get(row["rid"] + 1, np.nan)
        row["one_bar_triplet_rotation"] = int(
            bool(row["immediate_nha"])
            and row["prev_run_len"] == 1.0
            and row["L"] == 1
            and float(row["next_run_length"]) == 1.0
        )
        row["short_run_triplet_rotation"] = int(
            bool(row["immediate_nha"])
            and row["prev_run_len"] <= 2.0
            and row["L"] <= 2
            and float(row["next_run_length"]) <= 2.0
        )
        row["nha_raw_close"] = np.nan
        row["pair_net_progress"] = 0
        row["journey_net_progress"] = 0
        row["route_still_open_after_nha"] = 0
        if row["immediate_nha"] and decision in h4.index:
            nha_close = float(h4.loc[decision]["close"])
            row["nha_raw_close"] = nha_close
            row["pair_net_progress"] = int(
                direction * (nha_close - row["raw_h4_open"]) > 0.0
            )
            row["journey_net_progress"] = int(
                np.isfinite(row["run_start_open"])
                and direction * (nha_close - row["run_start_open"]) > 0.0
            )
            if np.isfinite(h4_target):
                target_obj = objects[objects["object_id"] == h4_target_id].iloc[0]
                route_alive = pd.isna(target_obj["consumed_at"]) or pd.Timestamp(
                    target_obj["consumed_at"]
                ) >= pd.Timestamp(row["run_end_decision"])
                target_still_ahead = direction * (h4_target - nha_close) > 0.0
                row["route_still_open_after_nha"] = int(route_alive and target_still_ahead)
        rows.append(row)
    frame = pd.DataFrame(rows)
    frame["causal_context"] = frame.apply(causal_context, axis=1)
    frame["nha_explanation"] = frame.apply(nha_explanation, axis=1)
    return frame


def k1_transfer_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    final_explanation = frame[frame["immediate_nha"].astype(bool)].set_index("rid")[
        "nha_explanation"
    ]
    work = frame.copy()
    work["prior_nha_explanation"] = work["rid"].map(
        lambda rid: final_explanation.get(int(rid) - 1)
    )
    populations = [
        ("ALL_OPPORTUNITIES", work[work["k"] == 1], "r7g_weight"),
        (
            "R7G_SELECTED",
            work[(work["k"] == 1) & work["selected_r7g"].astype(bool)],
            "selected_r7g_weight",
        ),
    ]
    for population, source, weight_column in populations:
        source = source[source["prior_nha_explanation"].notna()]
        periods = [("POOLED", source)]
        periods.extend((str(int(y)), g) for y, g in source.groupby("year", sort=True))
        for period, subset in periods:
            for explanation, group in subset.groupby(
                "prior_nha_explanation", sort=True
            ):
                weight = group[weight_column].astype(float)
                rows.append(
                    {
                        "population": population,
                        "period": period,
                        "prior_nha_explanation": explanation,
                        "n": int(len(group)),
                        "stops": int(group["stop_hit"].sum()),
                        "stop_rate": float(group["stop_hit"].mean()),
                        "mean_run_length": float(group["L"].mean()),
                        "L6plus_rate": float((group["L"] >= 6).mean()),
                        "weighted_R": float((group["R"] * weight).sum()),
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    ledger = pd.read_csv(
        args.ledger,
        parse_dates=[
            "decision",
            "entry_time",
            "exit_time",
            "label_available_at",
            "wave_start",
        ],
    )
    objects = pd.read_csv(
        args.objects,
        parse_dates=["source_time", "known_at", "consumed_at"],
    )
    h4 = pd.read_csv(args.h4, parse_dates=["h4_start"]).set_index("h4_start")
    universe = pd.read_csv(
        args.universe,
        usecols=[
            "signal_id",
            "decision",
            "year",
            "dir",
            "rid",
            "k",
            "L",
            "prev_run_len",
            "run_end_decision",
            "stop_hit",
            "R",
        ],
        parse_dates=["decision", "run_end_decision"],
    )
    ledger = ledger.merge(
        universe[["signal_id", "prev_run_len", "run_end_decision"]],
        on="signal_id",
        how="left",
        validate="one_to_one",
    )
    run_lengths = universe.groupby("rid", sort=True)["L"].first().to_dict()
    run_start_open = {}
    for first in universe[universe["k"] == 1].itertuples(index=False):
        start = pd.Timestamp(first.decision) - pd.Timedelta(hours=4)
        if start in h4.index:
            run_start_open[int(first.rid)] = float(h4.loc[start]["open"])

    rows: list[dict[str, object]] = []
    for child in ledger.itertuples(index=False):
        row = child._asdict()
        decision = pd.Timestamp(child.decision)
        direction = int(child.dir)
        reference = float(child.raw_h4_close)
        h4_target, h4_target_id = active_route(
            objects, decision, direction, reference, "H4"
        )
        h1_target, h1_target_id = active_route(
            objects, decision, direction, reference, "H1"
        )
        row["same_h1_consumed"] = int(
            int(child.same_consumed_count) > 0 and not bool(child.same_h4_consumed)
        )
        row["h4_route_open"] = int(np.isfinite(h4_target))
        row["h4_route_target"] = h4_target
        row["h4_route_object_id"] = h4_target_id
        row["h1_route_open"] = int(np.isfinite(h1_target))
        row["h1_route_target"] = h1_target
        row["h1_route_object_id"] = h1_target_id
        row["immediate_nha"] = int(int(child.k) == int(child.L))
        row["next_run_length"] = run_lengths.get(int(child.rid) + 1, np.nan)
        row["one_bar_triplet_rotation"] = int(
            bool(row["immediate_nha"])
            and float(row["prev_run_len"]) == 1.0
            and int(child.L) == 1
            and float(row["next_run_length"]) == 1.0
        )
        row["short_run_triplet_rotation"] = int(
            bool(row["immediate_nha"])
            and float(row["prev_run_len"]) <= 2.0
            and int(child.L) <= 2
            and float(row["next_run_length"]) <= 2.0
        )

        row["nha_raw_close"] = np.nan
        row["pair_net_progress"] = 0
        row["run_start_open"] = run_start_open.get(int(child.rid), np.nan)
        row["journey_net_progress"] = 0
        row["route_still_open_after_nha"] = 0
        if row["immediate_nha"] and decision in h4.index:
            nha = h4.loc[decision]
            nha_close = float(nha["close"])
            row["nha_raw_close"] = nha_close
            row["pair_net_progress"] = int(
                direction * (nha_close - float(child.raw_h4_open)) > 0.0
            )
            row["journey_net_progress"] = int(
                np.isfinite(row["run_start_open"])
                and direction * (nha_close - row["run_start_open"]) > 0.0
            )
            if np.isfinite(h4_target):
                target_obj = objects[objects["object_id"] == h4_target_id].iloc[0]
                route_alive = pd.isna(target_obj["consumed_at"]) or pd.Timestamp(
                    target_obj["consumed_at"]
                ) >= pd.Timestamp(child.run_end_decision)
                target_still_ahead = direction * (h4_target - nha_close) > 0.0
                row["route_still_open_after_nha"] = int(
                    route_alive and target_still_ahead
                )
        rows.append(row)

    result = pd.DataFrame(rows)
    result["causal_context"] = result.apply(causal_context, axis=1)
    result["nha_explanation"] = result.apply(nha_explanation, axis=1)
    summary = summary_rows(result)
    all_opportunities = build_all_opportunity_frame(
        universe,
        objects,
        h4,
        run_lengths,
        run_start_open,
        set(result["signal_id"].astype(str)),
    )
    selected_weight = result.set_index("signal_id")["r7g_weight"]
    all_opportunities["selected_r7g_weight"] = (
        all_opportunities["signal_id"].map(selected_weight).fillna(0.0)
    )
    all_summary = summary_rows(all_opportunities)
    k1_summary = k1_transfer_summary(all_opportunities)

    ledger_path = args.out_dir / "V11_HA_FLIP_LIQUIDITY_REASON_LEDGER.csv"
    summary_path = args.out_dir / "V11_HA_FLIP_LIQUIDITY_REASON_SUMMARY.csv"
    all_ledger_path = args.out_dir / "V11_HA_FLIP_ALL_OPPORTUNITY_LEDGER.csv"
    all_summary_path = args.out_dir / "V11_HA_FLIP_ALL_OPPORTUNITY_SUMMARY.csv"
    k1_summary_path = args.out_dir / "V11_HA_FLIP_K1_TRANSFER_SUMMARY.csv"
    result.to_csv(ledger_path, index=False, date_format="%Y-%m-%d %H:%M:%S")
    summary.to_csv(summary_path, index=False)
    all_opportunities.to_csv(
        all_ledger_path, index=False, date_format="%Y-%m-%d %H:%M:%S"
    )
    all_summary.to_csv(all_summary_path, index=False)
    k1_summary.to_csv(k1_summary_path, index=False)
    manifest = {
        "status": "CONSUMED_DATA_SEMANTIC_DIAGNOSTIC_ONLY",
        "authority": "NO TRADE OR PRODUCTION AUTHORITY",
        "source_ledger_sha256": sha256_file(args.ledger),
        "source_objects_sha256": sha256_file(args.objects),
        "source_h4_sha256": sha256_file(args.h4),
        "source_universe_sha256": sha256_file(args.universe),
        "rows": int(len(result)),
        "immediate_nha_rows": int(result["immediate_nha"].sum()),
        "one_bar_triplet_rotations": int(result["one_bar_triplet_rotation"].sum()),
        "short_run_triplet_rotations": int(
            result["short_run_triplet_rotation"].sum()
        ),
        "all_opportunity_rows": int(len(all_opportunities)),
        "all_immediate_nha_rows": int(all_opportunities["immediate_nha"].sum()),
        "all_one_bar_triplet_rotations": int(
            all_opportunities["one_bar_triplet_rotation"].sum()
        ),
        "all_short_run_triplet_rotations": int(
            all_opportunities["short_run_triplet_rotation"].sum()
        ),
        "causal_context_definition": {
            "H4_ARRIVAL_WITH_FARTHER_ROUTE": "completed PHA consumed same-side H4 liquidity and another same-side H4 object remains ahead",
            "H4_ARRIVAL_NO_FARTHER_KNOWN": "completed PHA consumed same-side H4 liquidity and no farther known H4 object remains",
            "TRANSIT_TO_H4": "no H4 arrival; a known same-side H4 object remains ahead",
            "LOCAL_H1_ONLY": "no H4 context; same-side H1 arrival or route exists",
            "NO_KNOWN_LIQUIDITY_CONTEXT": "no same-side H4 or H1 arrival and no known same-side H4 or H1 route",
        },
        "future_use_boundary": "immediate_nha, NHA close, next-run length, and explanations are outcome fields only",
        "outputs": {
            "ledger": str(ledger_path.resolve()),
            "summary": str(summary_path.resolve()),
            "all_opportunity_ledger": str(all_ledger_path.resolve()),
            "all_opportunity_summary": str(all_summary_path.resolve()),
            "k1_transfer_summary": str(k1_summary_path.resolve()),
        },
        "output_sha256": {
            "ledger": sha256_file(ledger_path),
            "summary": sha256_file(summary_path),
            "all_opportunity_ledger": sha256_file(all_ledger_path),
            "all_opportunity_summary": sha256_file(all_summary_path),
            "k1_transfer_summary": sha256_file(k1_summary_path),
        },
    }
    manifest_path = args.out_dir / "V11_HA_FLIP_LIQUIDITY_REASON_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print("\nPOOLED SUMMARY")
    print(summary[summary["period"] == "POOLED"].to_string(index=False))
    print("\nALL-OPPORTUNITY POOLED SUMMARY")
    print(all_summary[all_summary["period"] == "POOLED"].to_string(index=False))
    print("\nK1 TRANSFER POOLED SUMMARY")
    print(k1_summary[k1_summary["period"] == "POOLED"].to_string(index=False))


if __name__ == "__main__":
    main()
