"""Causal diagnostic of information-based add-on re-arm after HA-9 failure.

The audit uses the actual canonical Child opportunities.  Once an accepted
add-on has closed negative by PROOF_TIMEOUT or BREAKOUT_LOCK, later same-Journey
add-on opportunities are blocked until the named information event is visible
at an opportunity's normal entry timestamp.

Skipped Children do not create later failure events.  Child #1 is unchanged.
This first audit does not create replacement opportunities beyond actual C10,
so it is a selection diagnostic rather than a complete counterfactual EA.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ha9_counterfactual_exit_matrix import EPS, sha256, stats


FAILURE_REASONS = {"PROOF_TIMEOUT", "BREAKOUT_LOCK"}
MODES = (
    "actual_all",
    "failed_extreme_break",
    "fresh_raw_swing_close",
    "h1_no_opposition",
    "h4_delta_reexpansion",
    "any_new_information",
    "two_failures_extreme_break",
    "two_failures_any_bar_information",
    "two_failures_any_new_information",
)


def rearm_flags(opportunity: pd.Series, failure: pd.Series) -> dict[str, bool]:
    side = int(opportunity.side)
    extreme_break = (
        float(opportunity.signal_high) > float(failure.signal_high) + EPS
        if side == 1
        else float(opportunity.signal_low) < float(failure.signal_low) - EPS
    )
    raw_swing = str(opportunity.progress_state) == "fresh_close_beyond"
    h1_clear = str(opportunity.signal_h4_internal_h1_path_state) == "no_opposition"
    delta_reexpansion = float(opportunity.signal_h4_abs_delta) > float(
        failure.signal_h4_abs_delta
    ) + EPS
    return {
        "failed_extreme_break": bool(extreme_break),
        "fresh_raw_swing_close": bool(raw_swing),
        "h1_no_opposition": bool(h1_clear),
        "h4_delta_reexpansion": bool(delta_reexpansion),
        "any_new_information": bool(
            extreme_break or raw_swing or h1_clear or delta_reexpansion
        ),
        "any_bar_information": bool(extreme_break or h1_clear or delta_reexpansion),
    }


def simulate(ledger: pd.DataFrame, mode: str) -> pd.DataFrame:
    trigger_failures = 2 if mode.startswith("two_failures_") else 1
    signal_mode = mode.removeprefix("two_failures_")
    if signal_mode == "extreme_break":
        signal_mode = "failed_extreme_break"
    decisions: list[dict] = []
    for _, journey in ledger.groupby("journey", sort=True):
        journey = journey.sort_values(["entry_time", "child"]).copy()
        accepted: list[pd.Series] = []
        processed: set[tuple[int, int]] = set()
        blocking_failure: pd.Series | None = None
        consecutive_failures = 0

        for _, opportunity in journey.iterrows():
            entry_time = pd.Timestamp(opportunity.entry_time)
            # At the first tick of a new H4, timeout/lock closure is known before
            # the next same-color entry request.  Therefore <= is causal here.
            closing = sorted(
                [
                    row
                    for row in accepted
                    if (int(row.journey), int(row.child)) not in processed
                    and pd.Timestamp(row.exit_time) <= entry_time
                ],
                key=lambda row: (pd.Timestamp(row.exit_time), int(row.child)),
            )
            for closed in closing:
                processed.add((int(closed.journey), int(closed.child)))
                if (
                    float(closed.profit_actual) < -EPS
                    and str(closed.exit_reason) in FAILURE_REASONS
                ):
                    consecutive_failures += 1
                    if consecutive_failures >= trigger_failures:
                        blocking_failure = closed
                else:
                    consecutive_failures = 0

            if int(opportunity.child) == 1 or mode == "actual_all":
                take = True
                flags = {name: True for name in MODES if name != "actual_all"}
                reason = "child1" if int(opportunity.child) == 1 else "actual_all"
            elif blocking_failure is None:
                take = True
                flags = {name: False for name in MODES if name != "actual_all"}
                reason = "armed"
            else:
                flags = rearm_flags(opportunity, blocking_failure)
                take = flags[signal_mode]
                reason = mode if take else "blocked_no_new_information"

            decision = {
                "journey": int(opportunity.journey),
                "child": int(opportunity.child),
                "entry_time": opportunity.entry_time,
                "exit_time": opportunity.exit_time,
                "profit_actual": float(opportunity.profit_actual),
                "actual_result": opportunity.actual_result,
                "exit_reason": opportunity.exit_reason,
                "selected": bool(take),
                "decision_reason": reason,
                "blocking_failure_child": int(blocking_failure.child)
                if blocking_failure is not None
                else None,
                "blocking_failure_exit_time": blocking_failure.exit_time
                if blocking_failure is not None
                else None,
                "trigger_failures": trigger_failures,
                "consecutive_failures_before_entry": consecutive_failures,
                **flags,
            }
            decisions.append(decision)
            if take:
                accepted.append(opportunity)
                if blocking_failure is not None and int(opportunity.child) >= 2:
                    blocking_failure = None
                    consecutive_failures = 0
    return pd.DataFrame(decisions)


def selected_stats(decisions: pd.DataFrame) -> dict:
    selected = decisions.loc[decisions.selected].copy()
    skipped = decisions.loc[~decisions.selected].copy()
    selected["scenario_pnl"] = selected.profit_actual
    selected["scenario_exit_time"] = pd.to_datetime(selected.exit_time)
    return {
        "selected": stats(selected, "scenario_pnl", "scenario_exit_time"),
        "selected_children": int(len(selected)),
        "skipped_children": int(len(skipped)),
        "skipped_wins": int((skipped.profit_actual > EPS).sum()),
        "skipped_losses": int((skipped.profit_actual < -EPS).sum()),
        "skipped_flats": int((skipped.profit_actual.abs() <= EPS).sum()),
        "skipped_net_usd": float(skipped.profit_actual.sum()),
        "losses_removed_per_win_removed": (
            float((skipped.profit_actual < -EPS).sum())
            / float((skipped.profit_actual > EPS).sum())
            if (skipped.profit_actual > EPS).any()
            else None
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trade-ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output.mkdir(parents=True, exist_ok=True)

    ledger = pd.read_csv(arguments.trade_ledger)
    for column in ("entry_time", "exit_time"):
        ledger[column] = pd.to_datetime(ledger[column])
    ledger = ledger.sort_values(["entry_time", "journey", "child"]).reset_index(drop=True)

    summaries = {}
    all_decisions = []
    for mode in MODES:
        decisions = simulate(ledger, mode)
        decisions["mode"] = mode
        all_decisions.append(decisions)
        summaries[mode] = selected_stats(decisions)
        summaries[mode]["year"] = {}
        decisions["entry_year"] = pd.to_datetime(decisions.entry_time).dt.year
        for year, group in decisions.groupby("entry_year"):
            summaries[mode]["year"][str(int(year))] = selected_stats(group)

    stacked = pd.concat(all_decisions, ignore_index=True)
    actual = summaries["actual_all"]
    for mode in MODES[1:]:
        summaries[mode]["loss_reduction_vs_actual"] = int(
            actual["selected"]["losses"] - summaries[mode]["selected"]["losses"]
        )
        summaries[mode]["win_reduction_vs_actual"] = int(
            actual["selected"]["wins"] - summaries[mode]["selected"]["wins"]
        )

    summary = {
        "status": "CONSUMED DEVELOPMENT / RE-ARM SELECTION DIAGNOSTIC / NOT ACTION AUTHORITY",
        "source_hash": sha256(arguments.trade_ledger),
        "failure_definition": "accepted add-on closes negative by PROOF_TIMEOUT or BREAKOUT_LOCK",
        "population": {
            "children": len(ledger),
            "journeys": int(ledger.journey.nunique()),
            "actual_wins": int((ledger.profit_actual > EPS).sum()),
            "actual_losses": int((ledger.profit_actual < -EPS).sum()),
        },
        "modes": summaries,
        "boundary": {
            "causal": "only failures closed by the current entry and current completed signal-H4 features",
            "child1": "always retained",
            "limitation": "uses actual C2..C10 opportunity set and does not create replacement opportunities beyond C10",
        },
    }
    stacked.to_csv(arguments.output / "rearm_decisions.csv", index=False)
    (arguments.output / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
