"""Audit post-stop selectivity and stateful repeat-stop interventions.

This consumes the frozen causal episode ledger produced by
analyze_v11_neutral_bridge.py. It creates no new market features and grants no
trade authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


EXPECTED_EPISODE_SHA256 = "e4f87448c89472a2322692051e496a9b60c62adbe2401640c3660e3492b54e0d"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def max_streak(values: pd.Series) -> tuple[int, int, int]:
    current = maximum = repeat = third_plus = 0
    for value in values.astype(bool):
        current = current + 1 if value else 0
        maximum = max(maximum, current)
        repeat += int(current >= 2)
        third_plus += int(current >= 3)
    return maximum, repeat, third_plus


def summarize(
    name: str,
    source: pd.DataFrame,
    taken: list[tuple[int, float, int]],
    skipped: list[int],
) -> dict[str, object]:
    trades = pd.DataFrame(taken, columns=["index", "policy_R", "policy_stop"])
    baseline_taken = source.iloc[trades["index"].astype(int).to_numpy()]
    rejected = source.iloc[skipped]
    maximum, repeat, third_plus = max_streak(trades["policy_stop"])
    prevented = int(rejected["stop_hit"].sum()) + int(
        (
            (baseline_taken["stop_hit"].to_numpy() == 1)
            & (trades["policy_stop"].to_numpy() == 0)
        ).sum()
    )
    new_stops = int(
        (
            (baseline_taken["stop_hit"].to_numpy() == 0)
            & (trades["policy_stop"].to_numpy() == 1)
        ).sum()
    )
    return {
        "policy": name,
        "trades": len(trades),
        "skipped_candidates": len(rejected),
        "policy_stops": int(trades["policy_stop"].sum()),
        "baseline_stops_prevented": prevented,
        "new_stops_created": new_stops,
        "skipped_baseline_nonstops": int((rejected["stop_hit"] == 0).sum()),
        "skipped_baseline_positive_R_trades": int((rejected["R"] > 0).sum()),
        "skipped_baseline_positive_R": float(rejected.loc[rejected["R"] > 0, "R"].sum()),
        "sum_R": float(trades["policy_R"].sum()),
        "max_stop_streak": maximum,
        "repeat_stop_events": repeat,
        "third_plus_stop_events": third_plus,
    }


def simulate(
    source: pd.DataFrame,
    name: str,
    qualification: pd.Series,
    mode: str,
    delayed_minutes: pd.Series | None = None,
) -> dict[str, object]:
    defensive = False
    taken: list[tuple[int, float, int]] = []
    skipped: list[int] = []
    for index, row in source.iterrows():
        if not defensive:
            taken.append((index, float(row["R"]), int(row["stop_hit"])))
            defensive = bool(row["stop_hit"])
            continue
        if not bool(qualification.iloc[index]):
            skipped.append(index)
            if mode == "one_skip":
                defensive = False
            continue
        minute = int(delayed_minutes.iloc[index]) if delayed_minutes is not None else 0
        if minute:
            policy_r = float(row[f"b{minute}_R"])
            policy_stop = int(row[f"b{minute}_stop_hit"])
        else:
            policy_r = float(row["R"])
            policy_stop = int(row["stop_hit"])
        taken.append((index, policy_r, policy_stop))
        defensive = bool(policy_stop)
    return summarize(name, source, taken, skipped)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    actual = sha256_file(args.episodes)
    if actual != EXPECTED_EPISODE_SHA256:
        raise ValueError(f"episode ledger SHA mismatch: {actual}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(args.episodes, parse_dates=["decision"]).sort_values("decision").reset_index(drop=True)

    efficiency: dict[int, pd.Series] = {}
    raw_progress: dict[int, pd.Series] = {}
    for minute in (60, 120, 180):
        key = f"b{minute}"
        median = data[f"{key}_wave_efficiency"].shift(1).rolling(180, min_periods=60).median()
        raw_progress[minute] = (data[f"{key}_valid"] == 1) & (data[f"{key}_prefix_return_atr"] > 0)
        efficiency[minute] = raw_progress[minute] & (data[f"{key}_wave_efficiency"] >= median)
    earliest = pd.Series(0, index=data.index, dtype=int)
    for minute in (60, 120, 180):
        earliest[(earliest == 0) & efficiency[minute]] = minute

    depart = (data["nha_fraction_beyond_prev_open"] > 0.5) & (
        data["nha_close_beyond_prev_open_atr"] > 0.0
    )
    settled = data["nha_wave_settlement"] > 0.5
    policies = [
        simulate(data, "AFTER_LOSS_RAW_PROGRESS_60", raw_progress[60], "persistent", pd.Series(60, index=data.index)),
        simulate(data, "AFTER_LOSS_RETURN_EFFICIENT_60", efficiency[60], "persistent", pd.Series(60, index=data.index)),
        simulate(data, "AFTER_LOSS_RETURN_EFFICIENT_120", efficiency[120], "persistent", pd.Series(120, index=data.index)),
        simulate(data, "AFTER_LOSS_EARLIEST_TESTED_EFFICIENT", earliest > 0, "persistent", earliest),
        simulate(data, "AFTER_LOSS_NHA_DEPART_ONE_SKIP", depart, "one_skip"),
        simulate(data, "AFTER_LOSS_NHA_DEPART_PERSISTENT", depart, "persistent"),
        simulate(data, "AFTER_LOSS_NHA_DEPART_SETTLED_ONE_SKIP", depart & settled, "one_skip"),
        simulate(data, "AFTER_LOSS_NHA_DEPART_SETTLED_PERSISTENT", depart & settled, "persistent"),
    ]
    baseline_max, baseline_repeat, baseline_third = max_streak(data["stop_hit"])
    policies.insert(
        0,
        {
            "policy": "BASELINE_IMMEDIATE_K1",
            "trades": len(data),
            "skipped_candidates": 0,
            "policy_stops": int(data["stop_hit"].sum()),
            "baseline_stops_prevented": 0,
            "new_stops_created": 0,
            "skipped_baseline_nonstops": 0,
            "skipped_baseline_positive_R_trades": 0,
            "skipped_baseline_positive_R": 0.0,
            "sum_R": float(data["R"].sum()),
            "max_stop_streak": baseline_max,
            "repeat_stop_events": baseline_repeat,
            "third_plus_stop_events": baseline_third,
        },
    )
    summary = pd.DataFrame(policies)
    out = args.out_dir / "V11_POST_STOP_CHAIN_POLICY_SUMMARY.csv"
    summary.to_csv(out, index=False)
    manifest = {
        "status": "CONSUMED_DATA_SEQUENCE_DIAGNOSTIC_ONLY",
        "authority": "NO TRADE, THRESHOLD, SIZING, OR PRODUCTION AUTHORITY",
        "source_episode_sha256": actual,
        "rows": len(data),
        "output": str(out.resolve()),
        "output_sha256": sha256_file(out),
    }
    manifest_path = args.out_dir / "V11_POST_STOP_CHAIN_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(summary.to_string(index=False))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
