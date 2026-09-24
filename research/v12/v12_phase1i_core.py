"""Pure run-episode and policy helpers for V12 Phase-1I."""

from __future__ import annotations

import numpy as np
import pandas as pd


CONTRACT_VERSION = "v12-phase1i-run-episode-reverse-engineering-v1"


def classify_run(stopped_units: float, tail_units: float) -> str:
    if tail_units > 0:
        return "TAIL_JOURNEY_RUN"
    if stopped_units > 0:
        return "STOP_ONLY_RUN"
    return "NEUTRAL_RUN"


def annotate_prior_run_state(runs: pd.DataFrame) -> pd.DataFrame:
    ordered = runs.sort_values(["run_start", "run_id"]).reset_index(drop=True).copy()
    prior = None
    consecutive_stops = 0
    records: list[dict] = []
    for _, row in ordered.iterrows():
        item = row.to_dict()
        if prior is None:
            item.update({
                "prior_funded_run_class": "NONE",
                "prior_funded_run_direction": "NONE",
                "known_consecutive_stop_only_runs": 0,
                "prior_funded_run_stopped_units": 0.0,
                "prior_funded_run_net_R_per_unit": 0.0,
                "funded_run_id_gap": 0.0,
                "hours_since_prior_funded_run_start": 0.0,
                "prior_funded_run_known": 1,
            })
        else:
            known = pd.Timestamp(prior["run_exit"]) <= pd.Timestamp(row["run_start"])
            item.update({
                "prior_funded_run_class": prior["run_class"],
                "prior_funded_run_direction": prior["direction"],
                "known_consecutive_stop_only_runs": consecutive_stops,
                "prior_funded_run_stopped_units": float(prior["stopped_units"]),
                "prior_funded_run_net_R_per_unit": (
                    float(prior["net_R_units"]) / float(prior["funded_units"])
                    if float(prior["funded_units"]) else 0.0
                ),
                "funded_run_id_gap": float(row["run_id"] - prior["run_id"]),
                "hours_since_prior_funded_run_start": (
                    pd.Timestamp(row["run_start"]) - pd.Timestamp(prior["run_start"])
                ).total_seconds() / 3600.0,
                "prior_funded_run_known": int(known),
            })
            if not known:
                raise ValueError(f"prior funded run is not resolved at run {row['run_id']}")
        item["after_stop_candidate"] = int(item["prior_funded_run_class"] == "STOP_ONLY_RUN")
        item["repeat_stop_run"] = int(
            item["after_stop_candidate"] == 1 and row["run_class"] == "STOP_ONLY_RUN"
        )
        item["strict_adjacent_repeat_stop_run"] = int(
            item["repeat_stop_run"] == 1 and item["funded_run_id_gap"] == 1.0
        )
        records.append(item)
        if row["run_class"] == "STOP_ONLY_RUN":
            consecutive_stops += 1
        else:
            consecutive_stops = 0
        prior = row
    return pd.DataFrame(records)


def policy_summary(runs: pd.DataFrame, admitted: np.ndarray | pd.Series) -> dict[str, float]:
    mask = np.asarray(admitted, dtype=bool)
    selected = runs.loc[mask]
    funded_units = float(selected["funded_units"].sum())
    children = int(selected["child_count"].sum())
    wins = int(selected["winning_children"].sum())
    return {
        "runs": int(len(selected)),
        "funded_children": children,
        "winning_children": wins,
        "child_win_rate": wins / children if children else np.nan,
        "funded_units": funded_units,
        "stopped_units": float(selected["stopped_units"].sum()),
        "stopped_units_per_100": (
            float(selected["stopped_units"].sum()) / funded_units * 100.0 if funded_units else np.nan
        ),
        "net_R_units": float(selected["net_R_units"].sum()),
        "net_R_per_unit": float(selected["net_R_units"].sum()) / funded_units if funded_units else np.nan,
        "tail_units": float(selected["tail_units"].sum()),
        "tail_journey_runs": int((selected["run_class"] == "TAIL_JOURNEY_RUN").sum()),
        "stop_free_run_rate": float((selected["stopped_units"] == 0).mean()) if len(selected) else np.nan,
        "repeat_stopped_units": float(selected.loc[selected["repeat_stop_run"] == 1, "stopped_units"].sum()),
        "strict_repeat_stopped_units": float(
            selected.loc[selected["strict_adjacent_repeat_stop_run"] == 1, "stopped_units"].sum()
        ),
        "after_stop_candidate_runs": int(selected["after_stop_candidate"].sum()),
    }


def retention(value: float, baseline: float) -> float:
    return float(value / baseline) if baseline else 1.0


def enrich_comparison(summary: dict[str, float], baseline: dict[str, float]) -> dict[str, float]:
    output = dict(summary)
    output.update({
        "run_retention": retention(summary["runs"], baseline["runs"]),
        "child_retention": retention(summary["funded_children"], baseline["funded_children"]),
        "funded_unit_retention": retention(summary["funded_units"], baseline["funded_units"]),
        "tail_unit_retention": retention(summary["tail_units"], baseline["tail_units"]),
        "tail_journey_run_retention": retention(summary["tail_journey_runs"], baseline["tail_journey_runs"]),
        "after_stop_candidate_retention": retention(
            summary["after_stop_candidate_runs"], baseline["after_stop_candidate_runs"]
        ),
        "all_stopped_units_removed_fraction": (
            1.0 - retention(summary["stopped_units"], baseline["stopped_units"])
        ),
        "repeat_stopped_units_removed_fraction": (
            1.0 - retention(summary["repeat_stopped_units"], baseline["repeat_stopped_units"])
        ),
        "strict_repeat_stopped_units_removed_fraction": (
            1.0 - retention(summary["strict_repeat_stopped_units"], baseline["strict_repeat_stopped_units"])
        ),
        "child_win_rate_change_pp": 100.0 * (summary["child_win_rate"] - baseline["child_win_rate"]),
        "stop_free_run_rate_change_pp": 100.0 * (
            summary["stop_free_run_rate"] - baseline["stop_free_run_rate"]
        ),
    })
    if summary["stopped_units_per_100"] > 0:
        scale = baseline["stopped_units_per_100"] / summary["stopped_units_per_100"]
    else:
        scale = np.nan
    output["equal_stop_budget_scale"] = scale
    output["equal_stop_budget_net_R_per_baseline_unit"] = (
        summary["net_R_units"] * scale / baseline["funded_units"]
        if np.isfinite(scale) and baseline["funded_units"] else np.nan
    )
    output["baseline_net_R_per_unit"] = baseline["net_R_per_unit"]
    return output


def policy_mask(runs: pd.DataFrame, scores: np.ndarray, threshold: float) -> np.ndarray:
    candidate = runs["after_stop_candidate"].to_numpy(int) == 1
    return (~candidate) | (np.asarray(scores, dtype=float) >= threshold)


def choose_train_threshold(runs: pd.DataFrame, scores: np.ndarray, constraints: dict) -> tuple[float, list[dict]]:
    values = np.asarray(scores, dtype=float)
    candidate_values = values[runs["after_stop_candidate"].to_numpy(int) == 1]
    if not len(candidate_values):
        return float("-inf"), []
    cuts = np.unique(np.concatenate((
        [np.nextafter(candidate_values.min(), -np.inf)],
        np.quantile(candidate_values, np.linspace(0.0, 1.0, 21)),
    )))
    baseline = policy_summary(runs, np.ones(len(runs), dtype=bool))
    records: list[dict] = []
    feasible: list[dict] = []
    for threshold in cuts:
        admitted = policy_mask(runs, values, float(threshold))
        summary = enrich_comparison(policy_summary(runs, admitted), baseline)
        passed = (
            summary["tail_unit_retention"] >= constraints["overall_tail_units_retained"]
            and summary["tail_journey_run_retention"] >= constraints["overall_tail_journey_runs_retained"]
            and summary["child_retention"] >= constraints["overall_funded_children_retained"]
            and summary["after_stop_candidate_retention"] >= constraints["after_stop_candidate_runs_retained"]
        )
        record = {"threshold": float(threshold), "constraints_passed": bool(passed), **summary}
        records.append(record)
        if passed:
            feasible.append(record)
    if not feasible:
        return float(np.nextafter(candidate_values.min(), -np.inf)), records
    feasible.sort(key=lambda row: (
        row["repeat_stopped_units_removed_fraction"],
        row["net_R_units"],
        -row["threshold"],
    ), reverse=True)
    return float(feasible[0]["threshold"]), records
