"""Test a raw-settlement capital ladder on the new STD+SLOW journey skeleton.

The journey, Child, and Hard SL are generated independently from raw M1 by
``analyze_v11_new_skeleton_phase_space``.  No V10 entry, stop, run, selected
trade, or R7G weight is used.

The progress ladder gives every new journey one risk-normalized probe unit.
It can earn at most two additional units only when a later completed H4 raw
close establishes a new favorable journey settlement while STD and SLOW agree
with the journey direction.  The original transition-bridge Hard SL remains
fixed.  This is consumed-data architecture research, not trade authority.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from analyze_v11_new_skeleton_phase_space import (
    add_state_machines,
    build_journeys,
    file_receipt,
    first_m1_index,
    json_default,
    maximum_streak,
    rebuild_market,
)


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m1", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def progress_topups(
    journey: pd.Series,
    h4: pd.DataFrame,
    m1_ts: np.ndarray,
    stop_index: int | None,
) -> list[dict[str, object]]:
    direction = int(journey["direction"])
    signal_index = int(journey["signal_h4_index"])
    exit_decision = pd.Timestamp(journey["exit_decision"])
    best_close = float(h4.iloc[signal_index]["close"])
    result: list[dict[str, object]] = []
    for index in range(signal_index + 1, len(h4)):
        row = h4.iloc[index]
        decision = pd.Timestamp(row["decision"])
        if decision >= exit_decision:
            break
        close = float(row["close"])
        new_favorable = close > best_close if direction > 0 else close < best_close
        if new_favorable:
            best_close = close
        if not new_favorable or int(row["phase_core"]) != direction:
            continue
        entry_index = first_m1_index(m1_ts, decision)
        if entry_index is None:
            continue
        if stop_index is not None and entry_index > stop_index:
            break
        result.append({
            "decision": decision,
            "entry_index": entry_index,
            "h4_index": index,
            "settlement": close,
        })
        if len(result) == 2:
            break
    return result


def build_policy_ledger(m1: pd.DataFrame, h4: pd.DataFrame, journeys: pd.DataFrame) -> pd.DataFrame:
    ts = m1["timestamp"].to_numpy(dtype="datetime64[ns]")
    opens = m1["open"].to_numpy(dtype=float)
    highs = m1["high"].to_numpy(dtype=float)
    lows = m1["low"].to_numpy(dtype=float)
    rows: list[dict[str, object]] = []

    for journey in journeys.itertuples(index=False):
        source = pd.Series(journey._asdict())
        direction = int(source["direction"])
        stop = float(source["stop"])
        entry_index = first_m1_index(ts, pd.Timestamp(source["decision"]))
        exit_index = first_m1_index(ts, pd.Timestamp(source["exit_decision"]))
        if entry_index is None or exit_index is None or exit_index <= entry_index:
            continue
        segment_high = highs[entry_index : exit_index + 1]
        segment_low = lows[entry_index : exit_index + 1]
        touched = segment_low <= stop if direction > 0 else segment_high >= stop
        locations = np.flatnonzero(touched)
        stop_index = entry_index + int(locations[0]) if len(locations) else None
        stopped = int(stop_index is not None)
        same_m1_ambiguous = int(stop_index == exit_index) if stop_index is not None else 0
        liquidation_index = stop_index if stop_index is not None else exit_index
        liquidation = stop if stopped else float(opens[exit_index])
        topups = progress_topups(source, h4, ts, stop_index)
        initial = {
            "decision": pd.Timestamp(source["decision"]),
            "entry_index": entry_index,
            "h4_index": int(source["signal_h4_index"]),
            "settlement": float(h4.iloc[int(source["signal_h4_index"])]["close"]),
        }

        policies = {
            "ONE_PROBE": [initial],
            "IMMEDIATE_THREE": [initial, initial, initial],
            "RAW_SETTLEMENT_LADDER": [initial, *topups],
        }
        for policy, tranches in policies.items():
            tranche_rs: list[float] = []
            valid_tranches: list[dict[str, object]] = []
            for tranche in tranches:
                tranche_entry = float(opens[int(tranche["entry_index"])])
                risk = direction * (tranche_entry - stop)
                if risk <= 0:
                    continue
                tranche_r = direction * (liquidation - tranche_entry) / risk
                tranche_rs.append(float(tranche_r))
                valid_tranches.append(tranche)
            if not valid_tranches:
                continue
            combined_r = float(sum(tranche_rs))
            units = len(valid_tranches)
            rows.append({
                "policy": policy,
                "journey_id": source["journey_id"],
                "decision": pd.Timestamp(source["decision"]),
                "year": int(source["year"]),
                "direction": direction,
                "entry_time": pd.Timestamp(ts[entry_index]),
                "exit_time": pd.Timestamp(ts[liquidation_index]),
                "stop": stop,
                "stop_hit": stopped,
                "same_m1_exit_stop_ambiguous": same_m1_ambiguous,
                "funded_units": units,
                "stopped_units": units if stopped else 0,
                "full_size_stop": int(stopped and units == 3),
                "combined_R_units": combined_r,
                "first_R": tranche_rs[0],
                "second_R": tranche_rs[1] if len(tranche_rs) > 1 else math.nan,
                "third_R": tranche_rs[2] if len(tranche_rs) > 2 else math.nan,
                "second_decision": valid_tranches[1]["decision"] if len(valid_tranches) > 1 else pd.NaT,
                "third_decision": valid_tranches[2]["decision"] if len(valid_tranches) > 2 else pd.NaT,
            })
    return pd.DataFrame(rows)


def summarize(group: pd.DataFrame) -> dict[str, object]:
    values = group.sort_values("decision")["combined_R_units"].to_numpy(dtype=float)
    positive = values[values > 0]
    top_cut = float(np.quantile(positive, 0.9)) if len(positive) else math.nan
    return {
        "children": len(group),
        "funded_units": int(group["funded_units"].sum()),
        "mean_units": float(group["funded_units"].mean()),
        "one_unit_children": int(group["funded_units"].eq(1).sum()),
        "two_unit_children": int(group["funded_units"].eq(2).sum()),
        "three_unit_children": int(group["funded_units"].eq(3).sum()),
        "stops": int(group["stop_hit"].sum()),
        "stop_rate": float(group["stop_hit"].mean()),
        "stopped_units": int(group["stopped_units"].sum()),
        "full_size_stops": int(group["full_size_stop"].sum()),
        "wins": int(group["combined_R_units"].gt(0).sum()),
        "win_rate": float(group["combined_R_units"].gt(0).mean()),
        "total_R_units": float(values.sum()),
        "R_per_child": float(values.mean()),
        "R_per_funded_unit": float(values.sum() / group["funded_units"].sum()),
        "R_over_3": float(values[values >= 3.0].sum()),
        "positive_R_top_decile_share": (
            float(positive[positive >= top_cut].sum() / positive.sum()) if len(positive) and positive.sum() > 0 else math.nan
        ),
        "max_stop_streak": maximum_streak(group.sort_values("decision")["stop_hit"].eq(1)),
        "max_full_size_stop_streak": maximum_streak(group.sort_values("decision")["full_size_stop"].eq(1)),
        "same_m1_ambiguous": int(group["same_m1_exit_stop_ambiguous"].sum()),
    }


def summary_table(ledger: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for policy, group in ledger.groupby("policy", sort=False):
        rows.append({"policy": policy, "segment": "ALL", **summarize(group)})
        for year, year_group in group.groupby("year", sort=True):
            rows.append({"policy": policy, "segment": str(int(year)), **summarize(year_group)})
        for direction, side_group in group.groupby("direction", sort=True):
            rows.append({"policy": policy, "segment": "LONG" if direction > 0 else "SHORT", **summarize(side_group)})
    return pd.DataFrame(rows)


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    m1, h4, quality = rebuild_market(args.m1)
    h4 = add_state_machines(h4)
    journeys = build_journeys(m1, h4, "STD_SLOW_MEMORY", "state_std_slow_memory")
    ledger = build_policy_ledger(m1, h4, journeys)
    summary = summary_table(ledger)

    journey_path = args.out_dir / "V11_NEW_SKELETON_PROGRESS_JOURNEYS.csv"
    ledger_path = args.out_dir / "V11_NEW_SKELETON_PROGRESS_LEDGER.csv"
    summary_path = args.out_dir / "V11_NEW_SKELETON_PROGRESS_SUMMARY.csv"
    manifest_path = args.out_dir / "V11_NEW_SKELETON_PROGRESS_MANIFEST.json"
    journeys.to_csv(journey_path, index=False)
    ledger.to_csv(ledger_path, index=False)
    summary.to_csv(summary_path, index=False)
    manifest = {
        "status": "CONSUMED_DEVELOPMENT_EVIDENCE_ONLY",
        "source": file_receipt(args.m1),
        "data_quality": quality,
        "contract": {
            "journey": "STD+SLOW agreement establishes direction; disagreement preserves memory",
            "candidate": "one Child per journey reversal",
            "hard_sl": "fixed opposite raw-H4 extreme of transition bridge",
            "progress": "later completed raw-H4 close establishes a new favorable journey settlement while STD+SLOW agree",
            "capital": "one initial risk unit plus at most two progress-earned risk units",
            "v10_trade_ledger_used": False,
            "fast_used": False,
            "costs": "not modeled",
            "authority": "none",
        },
        "outputs": [file_receipt(journey_path), file_receipt(ledger_path), file_receipt(summary_path)],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, default=json_default) + "\n", encoding="utf-8")
    print(summary[summary["segment"].eq("ALL")].to_string(index=False))
    print(f"\nWrote {args.out_dir}")


if __name__ == "__main__":
    main()
