"""Separate an existing proven runner from new tactical add-on permission.

Actual MT5 entries are the opportunity set.  A runner is designated only after
its proof timestamp.  Its exit is replaced by the predeclared FAST-R25 H4 or
standard-H4 horizon.  Other selected Children keep actual HA-9 management.

Suppression variants skip later actual add-on opportunities while a
counterfactual runner remains open.  They do not synthesize replacement
opportunities beyond actual C10 and are therefore selection diagnostics.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ha9_counterfactual_exit_matrix import EPS, sha256, stats


SCENARIOS = (
    "actual",
    "first_proven_fast",
    "rolling_proven_fast",
    "first_accepted_fast",
    "first_aligned_accepted_fast",
    "first_proven_std",
    "first_proven_fast_suppress_adds",
    "rolling_proven_fast_suppress_adds",
    "first_proven_std_suppress_adds",
)


def run_scenario(frame: pd.DataFrame, scenario: str) -> pd.DataFrame:
    if scenario == "actual":
        out = frame.copy()
        out["selected"] = True
        out["scenario_pnl"] = out.actual_pnl
        out["scenario_exit_time"] = out.actual_exit_time
        out["runner"] = False
        return out

    horizon = "std_h4" if "_std" in scenario else "fast_h4_opposite"
    rolling = scenario.startswith("rolling_")
    suppress = scenario.endswith("_suppress_adds")
    require_acceptance = "accepted_fast" in scenario
    require_aligned_acceptance = "aligned_accepted_fast" in scenario
    output: list[dict] = []

    for _, journey in frame.groupby("journey", sort=True):
        journey = journey.sort_values(["entry_time", "child"])
        active_runner_exit: pd.Timestamp | None = None
        runner_ever_assigned = False
        for _, row in journey.iterrows():
            entry_time = pd.Timestamp(row.entry_time)
            selected = True
            if (
                suppress
                and int(row.child) >= 2
                and active_runner_exit is not None
                and entry_time < active_runner_exit
            ):
                selected = False

            record = row.to_dict()
            record["selected"] = selected
            record["runner"] = False
            record["scenario_pnl"] = float(row.actual_pnl)
            record["scenario_exit_time"] = pd.Timestamp(row.actual_exit_time)

            activation_time = pd.Timestamp(row.proof_time_m1) if pd.notna(row.proof_time_m1) else pd.NaT
            accepted = bool(row.h1_acceptance_by_exit)
            aligned_accepted = bool(row.h1_aligned_acceptance_by_exit)
            if require_acceptance and pd.notna(row.first_accept_h1_by_exit):
                activation_time = pd.Timestamp(row.proof_h4_start) + pd.Timedelta(
                    hours=float(row.first_accept_h1_by_exit)
                )
            state_qualifies = (
                aligned_accepted
                if require_aligned_acceptance
                else accepted
                if require_acceptance
                else True
            )
            can_assign = (
                selected
                and int(row.child) >= 2
                and bool(row.proven)
                and state_qualifies
                and pd.notna(activation_time)
                and activation_time <= pd.Timestamp(row.actual_exit_time)
                and activation_time < pd.Timestamp(row[f"{horizon}_exit_time"])
                and (
                    not runner_ever_assigned
                    or (
                        rolling
                        and active_runner_exit is not None
                        and activation_time >= active_runner_exit
                    )
                )
            )
            if can_assign:
                record["runner"] = True
                record["runner_proof_time"] = pd.Timestamp(row.proof_time_m1)
                record["runner_activation_time"] = activation_time
                record["scenario_pnl"] = float(row[f"{horizon}_pnl"])
                record["scenario_exit_time"] = pd.Timestamp(
                    row[f"{horizon}_exit_time"]
                )
                active_runner_exit = pd.Timestamp(record["scenario_exit_time"])
                runner_ever_assigned = True

            output.append(record)
    return pd.DataFrame(output)


def summarize(scenario_frame: pd.DataFrame) -> dict:
    selected = scenario_frame.loc[scenario_frame.selected].copy()
    skipped = scenario_frame.loc[~scenario_frame.selected].copy()
    runners = selected.loc[selected.runner].copy()
    result = {
        "selected": stats(selected, "scenario_pnl", "scenario_exit_time"),
        "selected_children": len(selected),
        "runner_children": len(runners),
        "skipped_children": len(skipped),
        "skipped_wins": int((skipped.actual_pnl > EPS).sum()),
        "skipped_losses": int((skipped.actual_pnl < -EPS).sum()),
        "skipped_net_usd": float(skipped.actual_pnl.sum()),
        "runner_actual_net_usd": float(runners.actual_pnl.sum()),
        "runner_counterfactual_net_usd": float(runners.scenario_pnl.sum()),
        "runner_actual_wins": int((runners.actual_pnl > EPS).sum()),
        "runner_actual_losses": int((runners.actual_pnl < -EPS).sum()),
        "runner_counterfactual_wins": int((runners.scenario_pnl > EPS).sum()),
        "runner_counterfactual_losses": int((runners.scenario_pnl < -EPS).sum()),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exit-ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output.mkdir(parents=True, exist_ok=True)

    ledger = pd.read_csv(arguments.exit_ledger)
    for column in (
        "entry_time",
        "actual_exit_time",
        "proof_time_m1",
        "proof_h4_start",
        "fast_h4_opposite_exit_time",
        "std_h4_exit_time",
    ):
        ledger[column] = pd.to_datetime(ledger[column], errors="coerce")
    ledger["proven"] = ledger.proven.astype(str).str.lower().eq("true")
    ledger = ledger.sort_values(["entry_time", "journey", "child"]).reset_index(drop=True)

    summaries = {}
    frames = []
    for scenario in SCENARIOS:
        result = run_scenario(ledger, scenario)
        result["scenario"] = scenario
        frames.append(result)
        summaries[scenario] = summarize(result)
        summaries[scenario]["year"] = {}
        result["entry_year"] = result.entry_time.dt.year
        for year, group in result.groupby("entry_year"):
            summaries[scenario]["year"][str(int(year))] = summarize(group)

    child_stats = {}
    for child, group in ledger.loc[ledger.child >= 2].groupby("child"):
        values = group.actual_pnl
        child_stats[str(int(child))] = {
            "n": len(group),
            "wins": int((values > EPS).sum()),
            "losses": int((values < -EPS).sum()),
            "win_rate_nonflat": float((values > EPS).sum() / (values.abs() > EPS).sum()),
            "net_usd": float(values.sum()),
            "median_usd": float(values.median()),
        }

    summary = {
        "status": "CONSUMED DEVELOPMENT / RUNNER-TACTICAL ROLE AUDIT / NOT ACTION AUTHORITY",
        "source_hash": sha256(arguments.exit_ledger),
        "population": {
            "children": len(ledger),
            "journeys": int(ledger.journey.nunique()),
            "proven_add_ons": int(((ledger.child >= 2) & ledger.proven).sum()),
        },
        "scenarios": summaries,
        "actual_add_on_child_ordinal": child_stats,
        "causal_contract": {
            "runner_assignment": "only after actual proof_time_m1",
            "first": "at most one runner assignment per Journey",
            "rolling": "a later proven add-on may become runner only after the prior FAST runner exit",
            "suppression": "later actual add-on opportunity is skipped while runner counterfactually remains open",
            "limitation": "no replacement opportunities beyond actual C10",
        },
    }
    pd.concat(frames, ignore_index=True).to_csv(
        arguments.output / "runner_tactical_decisions.csv", index=False
    )
    (arguments.output / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
