#!/usr/bin/env python3
"""Post-hoc, consumed-development diagnostics for Phase-1N passing heads."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from v12_phase0_core import sha256_file


PREFIX = "V12_PHASE1N_"


def max_stop_streak(frame: pd.DataFrame) -> int:
    best = current = 0
    for value in frame.sort_values(["decision_time", "signal_id"])["stop_hit"].astype(int):
        current = current + 1 if value else 0
        best = max(best, current)
    return best


def capital(frame: pd.DataFrame) -> dict[str, float]:
    children = len(frame)
    stops = int(frame["stop_hit"].sum())
    tail = frame.loc[frame["R"] >= 5, "R"]
    return {
        "children": children,
        "stops": stops,
        "stops_per_100": 100 * stops / children if children else np.nan,
        "net_R": float(frame["R"].sum()),
        "net_R_per_child": float(frame["R"].mean()) if children else np.nan,
        "tail_ge5_R": float(tail.sum()),
        "max_stop_streak": max_stop_streak(frame) if children else 0,
    }


def add_recurrent_stop_labels(base: pd.DataFrame) -> pd.DataFrame:
    output = base.sort_values(["decision_time", "signal_id"]).copy()
    stopped = output["stop_hit"].astype(bool)
    output["recurrent_stop"] = stopped & (stopped.shift(fill_value=False) | stopped.shift(-1, fill_value=False))
    output["isolated_stop"] = stopped & ~output["recurrent_stop"]
    output["non_stop"] = ~stopped
    return output


def churn_diagnostics(predictions: pd.DataFrame, passing: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    capital_rows, retention_rows = [], []
    for population in sorted(predictions["population"].unique()):
        base = predictions.loc[(predictions["population"] == population) & (predictions["model"] == "HA_ONLY")].copy()
        base = add_recurrent_stop_labels(base)
        labels = base[["signal_id", "recurrent_stop", "isolated_stop", "non_stop"]]
        baseline_capital = capital(base)
        models = passing.loc[passing["population"] == population, "model"].tolist()
        for model in models:
            local = predictions.loc[(predictions["population"] == population) & (predictions["model"] == model)].copy()
            local = local.merge(labels, on="signal_id", how="left", validate="one_to_one")
            for fold, fold_rows in list(local.groupby("fold")) + [("POOLED", local)]:
                all_summary = capital(fold_rows)
                q5 = fold_rows.loc[fold_rows["conviction_band"] == 5]
                q5_summary = capital(q5)
                capital_rows.append({
                    "population": population, "model": model, "fold": fold,
                    **{f"baseline_{key}": value for key, value in all_summary.items()},
                    **{f"q5_{key}": value for key, value in q5_summary.items()},
                    "q5_child_retention": len(q5) / len(fold_rows) if len(fold_rows) else np.nan,
                    "q5_stop_retention": q5_summary["stops"] / all_summary["stops"] if all_summary["stops"] else np.nan,
                    "q5_net_R_retention": q5_summary["net_R"] / all_summary["net_R"] if all_summary["net_R"] else np.nan,
                    "q5_tail_R_retention": q5_summary["tail_ge5_R"] / all_summary["tail_ge5_R"] if all_summary["tail_ge5_R"] else np.nan,
                })
            selected = local["conviction_band"] == 5
            for label in ("recurrent_stop", "isolated_stop", "non_stop"):
                count = int(local[label].sum())
                kept = int((local[label] & selected).sum())
                retention_rows.append({
                    "population": population, "model": model, "class": label.upper(),
                    "baseline_children": count, "q5_retained_children": kept,
                    "q5_retention_rate": kept / count if count else np.nan,
                    "removed_children": count - kept,
                })
    return pd.DataFrame(capital_rows), pd.DataFrame(retention_rows)


def time_level_diagnostics(output: Path, predictions: pd.DataFrame, passing: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for population in sorted(predictions["population"].unique()):
        models = passing.loc[(passing["population"] == population) & passing["model"].str.contains("STATIC_TIME"), "model"]
        if models.empty:
            continue
        ledger = pd.read_csv(
            output / f"{PREFIX}{population}_ENRICHED_LEDGER.csv",
            usecols=["signal_id", "session_phase", "broker_hour", "new_york_weekday"],
        )
        for model in models:
            local = predictions.loc[(predictions["population"] == population) & (predictions["model"] == model)].merge(
                ledger, on="signal_id", how="left", validate="one_to_one"
            )
            for dimension in ("session_phase", "broker_hour", "new_york_weekday"):
                for level, cell in local.groupby(dimension):
                    for segment, selected in (("ALL", cell), ("Q5", cell.loc[cell["conviction_band"] == 5])):
                        rows.append({"population": population, "model": model, "dimension": dimension.upper(),
                                     "level": level, "segment": segment, **capital(selected)})
    return pd.DataFrame(rows)


def micro_band_diagnostics(output: Path, predictions: pd.DataFrame, passing: pd.DataFrame) -> pd.DataFrame:
    rows = []
    population = "H1_K1"
    models = passing.loc[(passing["population"] == population) & passing["model"].str.contains("MICRO_PATH"), "model"]
    if models.empty:
        return pd.DataFrame()
    ledger = pd.read_csv(output / f"{PREFIX}{population}_ENRICHED_LEDGER.csv")
    fields = [column for column in ledger if column.startswith("m15_")]
    ledger = ledger[["signal_id", *fields]]
    for model in models:
        local = predictions.loc[(predictions["population"] == population) & (predictions["model"] == model)].merge(
            ledger, on="signal_id", how="left", validate="one_to_one"
        )
        for band, cell in local.groupby("conviction_band"):
            for field in fields:
                values = pd.to_numeric(cell[field], errors="coerce").dropna()
                rows.append({"population": population, "model": model, "conviction_band": int(band),
                             "feature": field, "rows": len(values), "mean": float(values.mean()),
                             "median": float(values.median()), "q25": float(values.quantile(.25)),
                             "q75": float(values.quantile(.75))})
    return pd.DataFrame(rows)


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    predictions = pd.read_csv(args.output / f"{PREFIX}TEST_PREDICTIONS.csv", parse_dates=["decision_time"])
    screen = pd.read_csv(args.output / f"{PREFIX}PROMOTION_SCREEN.csv")
    passing = screen.loc[screen["promotion_screen_pass"]].copy()
    capital_rows, retention_rows = churn_diagnostics(predictions, passing)
    time_rows = time_level_diagnostics(args.output, predictions, passing)
    micro_rows = micro_band_diagnostics(args.output, predictions, passing)
    outputs = {
        f"{PREFIX}POSTHOC_PASSING_CAPITAL.csv": capital_rows,
        f"{PREFIX}POSTHOC_STOP_CLASS_RETENTION.csv": retention_rows,
        f"{PREFIX}POSTHOC_STATIC_TIME_LEVELS.csv": time_rows,
        f"{PREFIX}POSTHOC_MICRO_PATH_BANDS.csv": micro_rows,
    }
    for name, frame in outputs.items():
        frame.to_csv(args.output / name, index=False, lineterminator="\n")
    receipt = pd.DataFrame([{"file": name, "sha256": sha256_file(args.output / name), "rows": len(frame),
                             "status": "POSTHOC_CONSUMED_DEVELOPMENT_DIAGNOSTIC_ONLY"}
                            for name, frame in outputs.items()])
    receipt.to_csv(args.output / f"{PREFIX}POSTHOC_RECEIPT.csv", index=False, lineterminator="\n")


if __name__ == "__main__":
    main()
