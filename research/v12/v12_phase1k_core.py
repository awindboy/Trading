"""Pure policy and capital helpers for V12 Phase 1K."""

from __future__ import annotations

import numpy as np
import pandas as pd


CONTRACT_VERSION = "v12-phase1k-staged-funding-counterfactual-v1"
POLICIES = (
    "BASELINE", "PROGRESSION_RELEASE", "DAMAGE_STOP",
    "PROGRESSION_OR_REPAIRED_DEPARTURE", "FIRST_CHILD_ONLY",
)


def admit_child(policy: str, ordinal: int, entry_time: pd.Timestamp,
                favorable_time: pd.Timestamp | None, opposed_time: pd.Timestamp | None,
                repaired_departure_time: pd.Timestamp | None) -> bool:
    if policy == "BASELINE":
        return True
    if ordinal == 1:
        return True
    if policy == "FIRST_CHILD_ONLY":
        return False
    if policy == "PROGRESSION_RELEASE":
        return favorable_time is not None and favorable_time <= entry_time
    if policy == "DAMAGE_STOP":
        return opposed_time is None or opposed_time > entry_time
    if policy == "PROGRESSION_OR_REPAIRED_DEPARTURE":
        return (
            (favorable_time is not None and favorable_time <= entry_time)
            or (repaired_departure_time is not None and repaired_departure_time <= entry_time)
        )
    raise ValueError(policy)


def capital_summary(children: pd.DataFrame) -> dict[str, float]:
    funded = float(children["funded_units"].sum())
    stopped = float(children["stopped_loss_units"].sum())
    net = float(children["combined_R_units"].sum())
    return {
        "funded_children": int(len(children)),
        "winning_children": int((children["combined_R_units"] > 0).sum()),
        "child_win_rate": float((children["combined_R_units"] > 0).mean()) if len(children) else np.nan,
        "funded_units": funded,
        "stopped_units": stopped,
        "stopped_units_per_100": stopped / funded * 100 if funded else np.nan,
        "repeat_stopped_units": float(children.loc[children["repeat_stop_run"] == 1, "stopped_loss_units"].sum()),
        "net_R_units": net,
        "net_R_per_unit": net / funded if funded else np.nan,
        "tail_units": float(children["right_tail_ge_5R_units"].sum()),
        "tail_journey_runs": int(children.loc[children["right_tail_ge_5R_units"] > 0, "run_id"].nunique()),
    }


def compare_summary(summary: dict[str, float], baseline: dict[str, float]) -> dict[str, float]:
    result = dict(summary)
    def ratio(key: str) -> float:
        return summary[key] / baseline[key] if baseline[key] else 1.0
    result.update({
        "child_retention": ratio("funded_children"),
        "funded_unit_retention": ratio("funded_units"),
        "tail_unit_retention": ratio("tail_units"),
        "tail_journey_run_retention": ratio("tail_journey_runs"),
        "all_stopped_units_removed_fraction": 1.0 - ratio("stopped_units"),
        "repeat_stopped_units_removed_fraction": 1.0 - ratio("repeat_stopped_units"),
        "child_win_rate_change_pp": 100.0 * (summary["child_win_rate"] - baseline["child_win_rate"]),
        "baseline_net_R_per_unit": baseline["net_R_per_unit"],
    })
    scale = baseline["stopped_units_per_100"] / summary["stopped_units_per_100"] if summary["stopped_units_per_100"] > 0 else np.nan
    result["equal_stop_budget_scale"] = scale
    result["equal_stop_budget_net_R_per_baseline_unit"] = (
        summary["net_R_units"] * scale / baseline["funded_units"] if np.isfinite(scale) else np.nan
    )
    return result
