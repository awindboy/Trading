"""Quasi-holdout check for the natural one-H1 HA-9 timeout extension.

The candidate is frozen from the canonical 2024-01-01..2026-08-28 consumed
sample before this script inspects post-cutoff Child-level states:

1. extend every actionable no-proof timeout by one completed H1; and
2. extend only persistent-opposition or unrepaired-mixed timeout states.

The post-cutoff period is only a quasi-holdout because full-report aggregate
counts were already known.  It is not production validation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ha9_counterfactual_exit_matrix import (
    EPS,
    add_ha,
    executable_exit_price,
    first_opposite_exit,
    load_bars,
    sha256,
    stats,
)
from ha9_trade_mode_phase1 import M1Window, parse_mt5_report, path_state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--m1", type=Path, required=True)
    parser.add_argument("--h1", type=Path, required=True)
    parser.add_argument("--h4", type=Path, required=True)
    parser.add_argument("--cutoff", default="2026-08-28 20:00:00")
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output.mkdir(parents=True, exist_ok=True)

    actual, report_quality = parse_mt5_report(arguments.report)
    h1 = add_ha(load_bars(arguments.h1), fast=False)
    h4_raw = load_bars(arguments.h4)
    h4 = add_ha(h4_raw, fast=False)
    h4_fast = add_ha(h4_raw, fast=True)
    m1_frame = load_bars(arguments.m1)
    m1 = M1Window(
        m1_frame.rename(columns={"spread": "spread_points"}).assign(tick_volume=0)
    )
    cutoff = pd.Timestamp(arguments.cutoff)
    last_usable_h1_open = pd.Timestamp(h1.known_at.dropna().max())

    child1_exits = actual.loc[
        actual.child == 1, ["journey", "exit_time", "exit_price_actual"]
    ].rename(
        columns={
            "exit_time": "journey_end_time",
            "exit_price_actual": "journey_exit_price_actual",
        }
    )
    actual = actual.merge(child1_exits, on="journey", how="left", validate="many_to_one")
    actual = actual.loc[
        (actual.entry_time > cutoff)
        & (actual.exit_time <= last_usable_h1_open)
        & actual.journey_end_time.notna()
    ].copy()

    h4_times = h4.time.to_numpy(dtype="datetime64[ns]")
    records: list[dict] = []
    for row in actual.itertuples(index=False):
        record = row._asdict()
        record["actual_exit_time"] = pd.Timestamp(row.exit_time)
        record["actual_pnl"] = float(row.profit_actual)
        record["actionable_timeout"] = False
        record["h1_path_state_at_timeout"] = "not_addon"
        record["extension_available"] = False
        record["exit_reason_reconstructed"] = "CHILD1_OR_UNKNOWN"
        record["one_h1_extension_exit_time"] = pd.Timestamp(row.exit_time)
        record["one_h1_extension_exit_price"] = float(row.exit_price_actual)
        record["one_h1_extension_pnl"] = float(row.profit_actual)
        record["h1_aligned_acceptance_by_exit"] = False
        record["first_acceptance_time"] = pd.NaT
        record["fast_runner_exit_time"] = pd.Timestamp(row.exit_time)
        record["fast_runner_exit_price"] = float(row.exit_price_actual)
        record["fast_runner_pnl"] = float(row.profit_actual)

        if int(row.child) >= 2:
            entry_time = pd.Timestamp(row.entry_time)
            proof_index = int(
                np.searchsorted(
                    h4_times,
                    np.datetime64(entry_time, "ns"),
                    side="right",
                )
                - 1
            )
            if proof_index <= 0 or proof_index + 1 >= len(h4):
                records.append(record)
                continue
            signal = h4.iloc[proof_index - 1]
            proof_bar = h4.iloc[proof_index]
            proof_end = pd.Timestamp(h4.iloc[proof_index + 1].time)
            side = int(row.side)
            target = float(signal.high if side == 1 else signal.low)
            proof_time = m1.proof_time(entry_time, proof_end, side, target)
            actionable_timeout = proof_time is None and int(proof_bar.ha_color) == side
            record.update(
                {
                    "signal_h4_start": pd.Timestamp(signal.time),
                    "proof_h4_start": pd.Timestamp(proof_bar.time),
                    "proof_h4_end": proof_end,
                    "proof_target": target,
                    "proof_time_m1": proof_time,
                    "proof_h4_color": int(proof_bar.ha_color),
                    "actionable_timeout": actionable_timeout,
                    "signal_high": float(signal.high),
                    "signal_low": float(signal.low),
                    "signal_h4_abs_delta": abs(
                        float(signal.ha_close) - float(signal.ha_open)
                    ),
                }
            )

            signal_inside = h1.loc[
                (h1.time >= pd.Timestamp(signal.time))
                & (h1.time < pd.Timestamp(proof_bar.time))
                & (h1.known_at <= entry_time)
            ]
            signal_state, _, _ = path_state(
                (signal_inside.ha_color != side).astype(bool).tolist()
            )
            record["signal_h4_internal_h1_path_state"] = signal_state
            if proof_time is None and int(proof_bar.ha_color) == side:
                record["exit_reason_reconstructed"] = "PROOF_TIMEOUT"
            elif (
                proof_time is not None
                and pd.Timestamp(row.exit_time)
                < pd.Timestamp(row.journey_end_time) - pd.Timedelta(seconds=1)
            ):
                record["exit_reason_reconstructed"] = "BREAKOUT_LOCK"
            else:
                record["exit_reason_reconstructed"] = "HA_EXIT"

            observed_proof_h1 = h1.loc[
                (h1.time >= pd.Timestamp(proof_bar.time))
                & (h1.time < proof_end)
                & (h1.known_at <= pd.Timestamp(row.exit_time))
            ].copy()
            if side == 1:
                accepted = observed_proof_h1.close > target + EPS
            else:
                accepted = observed_proof_h1.close < target - EPS
            aligned = accepted & (observed_proof_h1.ha_color == side)
            if aligned.any():
                first_acceptance = pd.Timestamp(
                    observed_proof_h1.loc[aligned, "known_at"].iloc[0]
                )
                record["h1_aligned_acceptance_by_exit"] = True
                record["first_acceptance_time"] = first_acceptance
                fast_exit = first_opposite_exit(
                    h4_fast,
                    first_acceptance,
                    pd.Timestamp(row.journey_end_time),
                    side,
                )
                if fast_exit is None:
                    fast_time = pd.Timestamp(row.journey_end_time)
                    fast_price = float(row.journey_exit_price_actual)
                else:
                    fast_time, fast_price = fast_exit
                record["fast_runner_exit_time"] = fast_time
                record["fast_runner_exit_price"] = fast_price
                record["fast_runner_pnl"] = side * (
                    fast_price - float(row.entry_price_actual)
                )

            if actionable_timeout:
                inside = h1.loc[
                    (h1.time >= pd.Timestamp(proof_bar.time))
                    & (h1.time < proof_end)
                    & (h1.known_at <= pd.Timestamp(row.exit_time))
                ]
                state, path, trailing = path_state(
                    (inside.ha_color != side).astype(bool).tolist()
                )
                record["h1_path_state_at_timeout"] = state
                record["h1_path_at_timeout"] = path
                record["h1_trailing_opposed_at_timeout"] = trailing

                next_h1 = h1.loc[h1.known_at > pd.Timestamp(row.exit_time)]
                if len(next_h1):
                    extension = next_h1.iloc[0]
                    extension_time = pd.Timestamp(extension.known_at)
                    if (
                        extension_time <= pd.Timestamp(row.journey_end_time)
                        and extension_time <= last_usable_h1_open
                    ):
                        exit_price = executable_exit_price(
                            side,
                            float(extension.execution_bid_open),
                            float(extension.execution_spread),
                        )
                        record["extension_available"] = True
                        record["one_h1_extension_exit_time"] = extension_time
                        record["one_h1_extension_exit_price"] = exit_price
                        record["one_h1_extension_pnl"] = side * (
                            exit_price - float(row.entry_price_actual)
                        )
        records.append(record)

    out = pd.DataFrame(records)
    actionable = out.actionable_timeout.astype(bool) & out.extension_available.astype(bool)
    opposed_mixed = actionable & out.h1_path_state_at_timeout.isin(
        ["persistent_opposition", "unrepaired_mixed"]
    )

    for name, selector in (
        ("extend_all_actionable", actionable),
        ("extend_opposed_mixed", opposed_mixed),
    ):
        out[f"{name}_pnl"] = out.actual_pnl
        out[f"{name}_exit_time"] = out.actual_exit_time
        out.loc[selector, f"{name}_pnl"] = out.loc[selector, "one_h1_extension_pnl"]
        out.loc[selector, f"{name}_exit_time"] = out.loc[
            selector, "one_h1_extension_exit_time"
        ]

    scenarios = ["actual", "extend_all_actionable", "extend_opposed_mixed"]
    add_ons = out.loc[out.child >= 2].copy()
    timeout_rows = out.loc[actionable].copy()

    def simulate_two_failure_rearm(frame: pd.DataFrame) -> pd.DataFrame:
        selected_keys: set[tuple[int, int]] = set()
        for _, journey in frame.groupby("journey", sort=True):
            journey = journey.sort_values(["entry_time", "child"])
            accepted: list[pd.Series] = []
            processed: set[tuple[int, int]] = set()
            failure_count = 0
            blocker: pd.Series | None = None
            for _, opportunity in journey.iterrows():
                entry_time = pd.Timestamp(opportunity.entry_time)
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
                        and str(closed.exit_reason_reconstructed)
                        in {"PROOF_TIMEOUT", "BREAKOUT_LOCK"}
                    ):
                        failure_count += 1
                        if failure_count >= 2:
                            blocker = closed
                    else:
                        failure_count = 0

                take = True
                if int(opportunity.child) >= 2 and blocker is not None:
                    side = int(opportunity.side)
                    extreme = (
                        float(opportunity.signal_high) > float(blocker.signal_high) + EPS
                        if side == 1
                        else float(opportunity.signal_low) < float(blocker.signal_low) - EPS
                    )
                    h1_clear = (
                        str(opportunity.signal_h4_internal_h1_path_state)
                        == "no_opposition"
                    )
                    delta = float(opportunity.signal_h4_abs_delta) > float(
                        blocker.signal_h4_abs_delta
                    ) + EPS
                    take = bool(extreme or h1_clear or delta)
                if take:
                    selected_keys.add((int(opportunity.journey), int(opportunity.child)))
                    accepted.append(opportunity)
                    if blocker is not None and int(opportunity.child) >= 2:
                        blocker = None
                        failure_count = 0
        return frame.assign(
            selected_two_failure_any_bar=[
                (int(row.journey), int(row.child)) in selected_keys
                for row in frame.itertuples(index=False)
            ]
        )

    out = simulate_two_failure_rearm(out)
    rearm_selected = out.loc[out.selected_two_failure_any_bar].copy()
    rearm_skipped = out.loc[~out.selected_two_failure_any_bar].copy()
    rearm_selected["rearm_pnl"] = rearm_selected.profit_actual
    rearm_selected["rearm_exit_time"] = rearm_selected.actual_exit_time

    out["first_accepted_runner"] = False
    for _, journey in out.loc[
        (out.child >= 2) & out.h1_aligned_acceptance_by_exit.astype(bool)
    ].groupby("journey"):
        first_index = journey.sort_values(["first_acceptance_time", "child"]).index[0]
        out.loc[first_index, "first_accepted_runner"] = True
    out["first_accepted_fast_pnl"] = out.profit_actual
    out["first_accepted_fast_exit_time"] = out.actual_exit_time
    out.loc[out.first_accepted_runner, "first_accepted_fast_pnl"] = out.loc[
        out.first_accepted_runner, "fast_runner_pnl"
    ]
    out.loc[out.first_accepted_runner, "first_accepted_fast_exit_time"] = out.loc[
        out.first_accepted_runner, "fast_runner_exit_time"
    ]
    runner_rows = out.loc[out.first_accepted_runner].copy()

    def summarize(frame: pd.DataFrame) -> dict:
        return {name: stats(frame, f"{name}_pnl", f"{name}_exit_time") for name in scenarios}

    summary = {
        "status": "POST-CUTOFF QUASI-HOLDOUT / PRELIMINARY / NOT ACTION AUTHORITY",
        "candidate_frozen_before_post_cutoff_state_inspection": {
            "extend_all_actionable": "one completed H1 after an actionable no-proof timeout",
            "extend_opposed_mixed": "same extension only for persistent_opposition or unrepaired_mixed",
        },
        "source_hashes": {
            "report": sha256(arguments.report),
            "m1": sha256(arguments.m1),
            "h1": sha256(arguments.h1),
            "h4": sha256(arguments.h4),
        },
        "report_quality": report_quality,
        "window": {
            "after": str(cutoff),
            "last_usable_h1_open": str(last_usable_h1_open),
            "first_entry": str(out.entry_time.min()) if len(out) else None,
            "last_counterfactual_exit": str(
                pd.to_datetime(out.extend_all_actionable_exit_time).max()
            )
            if len(out)
            else None,
        },
        "population": {
            "children": len(out),
            "add_ons": len(add_ons),
            "actionable_timeouts_with_extension": int(actionable.sum()),
            "opposed_mixed_selected": int(opposed_mixed.sum()),
        },
        "combined": summarize(out),
        "add_ons": summarize(add_ons),
        "actionable_timeout_population": {
            "n": len(timeout_rows),
            "actual": stats(timeout_rows, "actual_pnl", "actual_exit_time"),
            "one_h1_extension": stats(
                timeout_rows,
                "one_h1_extension_pnl",
                "one_h1_extension_exit_time",
            ),
        },
        "state_counts": timeout_rows.h1_path_state_at_timeout.value_counts().to_dict(),
        "two_failure_any_bar_rearm": {
            "selected": stats(rearm_selected, "rearm_pnl", "rearm_exit_time"),
            "selected_children": len(rearm_selected),
            "skipped_children": len(rearm_skipped),
            "skipped_wins": int((rearm_skipped.profit_actual > EPS).sum()),
            "skipped_losses": int((rearm_skipped.profit_actual < -EPS).sum()),
            "skipped_net_usd": float(rearm_skipped.profit_actual.sum()),
            "limitation": "actual C2..C10 opportunity set; no replacement opportunities beyond C10",
        },
        "first_accepted_fast_runner": {
            "combined": stats(
                out, "first_accepted_fast_pnl", "first_accepted_fast_exit_time"
            ),
            "runner_children": len(runner_rows),
            "runner_actual_net_usd": float(runner_rows.profit_actual.sum()),
            "runner_counterfactual_net_usd": float(runner_rows.fast_runner_pnl.sum()),
            "runner_actual_wins": int((runner_rows.profit_actual > EPS).sum()),
            "runner_actual_losses": int((runner_rows.profit_actual < -EPS).sum()),
            "runner_counterfactual_wins": int((runner_rows.fast_runner_pnl > EPS).sum()),
            "runner_counterfactual_losses": int((runner_rows.fast_runner_pnl < -EPS).sum()),
        },
        "limitations": [
            "Only the short post-cutoff period covered by both report and raw H1 is used.",
            "Full-report aggregate outcomes were already known, so this is not a pristine holdout.",
            "Counterfactual SHORT exits use bar-open Bid plus exported spread, not real ticks.",
            "The report lacks explicit exit-reason events; actionable timeout is reconstructed causally from raw M1/H4.",
        ],
    }

    out.to_csv(arguments.output / "post_cutoff_timeout_extension_ledger.csv", index=False)
    (arguments.output / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
