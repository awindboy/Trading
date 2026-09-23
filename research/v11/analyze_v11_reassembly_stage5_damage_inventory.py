"""Stage-5 V11 reassembly: audit what the one-slot policy removed, then test damage-responsive inventory.

The one-slot result cannot be judged by raw R retention alone because it also
cuts exposure.  This diagnostic first asks whether its blocked capital was
selectively concentrated in stopped or back-and-forth loss.  It then tests one
fixed, causal inventory state machine instead of scanning slot counts:

* every selected Child receives one participation unit;
* k1 conviction capital remains delayed to the causal FAST-k2 event;
* otherwise eligible extra capital remains available while the journey is healthy;
* any known Child Hard SL damages the journey's extra-capital inventory;
* all later Children still receive one unit;
* extra capital is repaired only after a post-damage Child remains alive into a
  later selected-Child decision in the same FAST run.

This changes only extra-capital ownership.  It does not veto a Child, predict a
direction, move a Hard SL, or resurrect a stopped Child.  All evidence is
consumed development evidence with no trade, release, sizing, leverage, EA, or
production authority.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_v11_reassembly_stage3_portfolio as stage3
import analyze_v11_reassembly_stage4_campaign_capital as stage4


POLICY_DAMAGE_CONSERVATIVE = "ELASTIC_DAMAGE_REPAIR_STOP_AT_DECISION_FIRST"
POLICY_DAMAGE_PERMISSIVE = "ELASTIC_DAMAGE_REPAIR_REQUEST_FIRST"


def allocate_damage_repair(
    candidates: pd.DataFrame,
    portfolio: pd.DataFrame,
    policy: str,
    stop_at_decision_first: bool,
) -> pd.DataFrame:
    results: list[pd.DataFrame] = []
    for rid, run_candidates in candidates.groupby("rid", sort=False):
        children = portfolio[portfolio["rid"].eq(rid)].sort_values(["entry_time", "k"]).copy()
        stops = children[children["stop_hit"].eq(1)][["signal_id", "exit_time"]].sort_values("exit_time")
        run_candidates = run_candidates.sort_values([
            "open_time", "candidate_type", "k", "signal_id"
        ]).copy()
        damaged = False
        last_damage_time = pd.NaT
        last_damage_signal = ""
        stop_cursor = 0
        decisions: list[str] = []
        reasons: list[str] = []
        damage_times: list[object] = []
        damage_signals: list[str] = []
        repair_signals: list[str] = []
        same_time_stop_flags: list[int] = []
        stop_rows = list(stops.itertuples(index=False))

        for candidate in run_candidates.itertuples(index=False):
            request_time = pd.Timestamp(candidate.open_time)
            same_time_stop = any(
                pd.Timestamp(stop.exit_time) == request_time for stop in stop_rows
            )
            while stop_cursor < len(stop_rows):
                stop = stop_rows[stop_cursor]
                stop_time = pd.Timestamp(stop.exit_time)
                known = stop_time <= request_time if stop_at_decision_first else stop_time < request_time
                if not known:
                    break
                damaged = True
                last_damage_time = stop_time
                last_damage_signal = str(stop.signal_id)
                stop_cursor += 1

            repaired_by = ""
            if damaged:
                probes = children[
                    (children["entry_time"] > last_damage_time)
                    & (children["entry_time"] < request_time)
                    & (children["exit_time"] >= request_time)
                ]
                if len(probes):
                    repaired_by = str(probes.iloc[-1]["signal_id"])
                    damaged = False

            if damaged:
                decisions.append("DAMAGE_BLOCKED")
                reasons.append("KNOWN_HARD_SL_AWAITING_SURVIVING_CHILD")
            else:
                decisions.append("ALLOCATED")
                reasons.append("HEALTHY_OR_REPAIRED")
            damage_times.append(last_damage_time)
            damage_signals.append(last_damage_signal)
            repair_signals.append(repaired_by)
            same_time_stop_flags.append(int(same_time_stop))

        run_candidates["allocation"] = decisions
        run_candidates["allocation_reason"] = reasons
        run_candidates["last_damage_time"] = damage_times
        run_candidates["last_damage_signal_id"] = damage_signals
        run_candidates["repaired_by_signal_id"] = repair_signals
        run_candidates["same_time_stop_at_request"] = same_time_stop_flags
        run_candidates["policy"] = policy
        results.append(run_candidates)
    return pd.concat(results, ignore_index=True)


def chain_metrics(children: pd.DataFrame) -> dict[str, int]:
    frame = children.sort_values(["decision_ts", "k"]).copy()
    full = frame["full_3unit_stop"].eq(1)
    previous = full.shift(1, fill_value=False)
    pair = full & previous
    alternating = pair & frame["dir"].ne(frame["dir"].shift(1))
    same_direction = pair & frame["dir"].eq(frame["dir"].shift(1))
    same_run = pair & frame["rid"].eq(frame["rid"].shift(1))
    cross_run = pair & frame["rid"].ne(frame["rid"].shift(1))
    previous_exit = pd.to_datetime(frame["exit_time"].shift(1))
    current_entry = pd.to_datetime(frame["entry_time"])
    prior_stop_known = pair & previous_exit.le(current_entry)
    overlapping_before_prior_stop = pair & previous_exit.gt(current_entry)
    best = current = 0
    for value in full:
        current = current + 1 if bool(value) else 0
        best = max(best, current)
    return {
        "adjacent_full3_pairs": int(pair.sum()),
        "alternating_direction_full3_pairs": int(alternating.sum()),
        "same_direction_full3_pairs": int(same_direction.sum()),
        "same_run_full3_pairs": int(same_run.sum()),
        "cross_run_full3_pairs": int(cross_run.sum()),
        "prior_stop_known_full3_pairs": int(prior_stop_known.sum()),
        "overlapping_before_prior_stop_full3_pairs": int(overlapping_before_prior_stop.sum()),
        "max_full3_stop_streak": int(best),
    }


def candidate_selectivity(frame: pd.DataFrame, policy: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for allocation, group in frame.groupby("allocation", sort=True):
        positive = group["R_units"].clip(lower=0.0)
        negative = group["R_units"].clip(upper=0.0)
        rows.append({
            "policy": policy,
            "allocation": str(allocation),
            "requests": int(len(group)),
            "stopped_requests": int(group["stop_units"].gt(0).sum()),
            "stopped_request_rate": float(group["stop_units"].gt(0).mean()),
            "candidate_R_units": float(group["R_units"].sum()),
            "candidate_positive_R_units": float(positive.sum()),
            "candidate_negative_R_units": float(negative.sum()),
            "candidate_stop_units": float(group["stop_units"].sum()),
        })
    return rows


def add_relative_metrics(summary: pd.DataFrame, paths: dict[str, np.ndarray]) -> pd.DataFrame:
    result = summary.copy()
    baseline = result[result["policy"].eq(stage3.POLICY_BASELINE)].iloc[0]
    result["stop_unit_reduction"] = 1.0 - result["stopped_loss_units"] / baseline["stopped_loss_units"]
    result["full_3unit_stop_reduction"] = 1.0 - result["full_3unit_stop_children"] / baseline["full_3unit_stop_children"]
    result["combined_R_retention"] = result["combined_R_units"] / baseline["combined_R_units"]
    result["funded_unit_retention"] = result["funded_units"] / baseline["funded_units"]
    target_dd = float(baseline["max_drawdown_1pct_per_unit"])
    risks = []
    equities = []
    for row in result.itertuples(index=False):
        risk = stage3.equal_drawdown_risk(paths[row.policy], target_dd)
        risks.append(risk)
        equities.append(stage3.equity_path(paths[row.policy], risk)[0] if np.isfinite(risk) else math.nan)
    result["equal_drawdown_risk_fraction"] = risks
    result["equal_drawdown_ending_equity"] = equities
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--universe", type=Path, required=True)
    parser.add_argument("--stage2-ledger", type=Path, required=True)
    parser.add_argument("--stage4-allocations", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    portfolio = stage3.load_selected_portfolio(args.events, args.universe)
    ladder = stage3.load_k1_ladder(args.stage2_ledger)
    stage3_children = stage3.child_ledgers(portfolio, ladder)
    stage3_tranches = stage3.build_tranches(portfolio, ladder)
    candidates = stage4.extra_candidates(portfolio, ladder)

    conservative_allocations = allocate_damage_repair(
        candidates, portfolio, POLICY_DAMAGE_CONSERVATIVE, stop_at_decision_first=True
    )
    permissive_allocations = allocate_damage_repair(
        candidates, portfolio, POLICY_DAMAGE_PERMISSIVE, stop_at_decision_first=False
    )
    conservative_children, conservative_tranches = stage4.campaign_policy(
        portfolio, conservative_allocations, POLICY_DAMAGE_CONSERVATIVE
    )
    permissive_children, permissive_tranches = stage4.campaign_policy(
        portfolio, permissive_allocations, POLICY_DAMAGE_PERMISSIVE
    )

    stage4_allocations = pd.read_csv(args.stage4_allocations)
    one_slot = stage4_allocations[
        stage4_allocations["policy"].eq(stage4.POLICY_NEW_PRIORITY)
    ].copy()
    for column in ("open_time", "close_time"):
        one_slot[column] = pd.to_datetime(one_slot[column])
    one_slot_children, one_slot_tranches = stage4.campaign_policy(
        portfolio, one_slot, stage4.POLICY_NEW_PRIORITY
    )

    children = pd.concat([
        stage3_children,
        one_slot_children,
        conservative_children,
        permissive_children,
    ], ignore_index=True, sort=False)
    tranches = pd.concat([
        stage3_tranches,
        one_slot_tranches,
        conservative_tranches,
        permissive_tranches,
    ], ignore_index=True, sort=False)
    policies = [
        stage3.POLICY_BASELINE,
        stage3.POLICY_LADDER,
        stage4.POLICY_NEW_PRIORITY,
        POLICY_DAMAGE_CONSERVATIVE,
        POLICY_DAMAGE_PERMISSIVE,
    ]

    summary_rows = []
    chain_rows = []
    slice_rows = []
    paths: dict[str, np.ndarray] = {}
    for policy in policies:
        policy_children = children[children["policy"].eq(policy)].copy()
        policy_tranches = tranches[tranches["policy"].eq(policy)].copy()
        row = stage3.summarize_policy(policy_children, policy_tranches)
        row.update(chain_metrics(policy_children))
        summary_rows.append(row)
        chain_rows.append({"policy": policy, **chain_metrics(policy_children)})
        paths[policy] = stage3.realized_path(policy_tranches)["R_units"].to_numpy(dtype=float)
        for year, group in policy_children.groupby("year", sort=True):
            slice_rows.append(stage3.summarize_child_slice(group, "YEAR", str(int(year))))
        for direction, group in policy_children.groupby("dir", sort=True):
            slice_rows.append(stage3.summarize_child_slice(
                group, "SIDE", "LONG" if int(direction) > 0 else "SHORT"
            ))
    summary = add_relative_metrics(pd.DataFrame(summary_rows), paths)
    slices = pd.DataFrame(slice_rows)

    selectivity_rows = []
    selectivity_rows.extend(candidate_selectivity(one_slot, stage4.POLICY_NEW_PRIORITY))
    selectivity_rows.extend(candidate_selectivity(conservative_allocations, POLICY_DAMAGE_CONSERVATIVE))
    selectivity_rows.extend(candidate_selectivity(permissive_allocations, POLICY_DAMAGE_PERMISSIVE))
    selectivity = pd.DataFrame(selectivity_rows)

    baseline_k1 = children[
        children["policy"].eq(stage3.POLICY_BASELINE) & children["k"].eq(1)
    ].sort_values("decision_ts").copy()
    staged_k1 = children[
        children["policy"].eq(stage3.POLICY_LADDER) & children["k"].eq(1)
    ][["signal_id", "full_3unit_stop"]].rename(columns={"full_3unit_stop": "staged_full3"})
    baseline_k1["previous_k1_stop"] = baseline_k1["stop_hit"].shift(1, fill_value=0)
    baseline_k1["next_k1_stop"] = baseline_k1["stop_hit"].shift(-1, fill_value=0)
    baseline_k1["k1_round_trip_chain"] = (
        baseline_k1["stop_hit"].eq(1)
        & (baseline_k1["previous_k1_stop"].eq(1) | baseline_k1["next_k1_stop"].eq(1))
    ).astype(int)
    k1_audit = baseline_k1.merge(staged_k1, on="signal_id", how="left", validate="one_to_one")
    k1_audit["full3_avoided_by_k1_ladder"] = (
        k1_audit["full_3unit_stop"].eq(1) & k1_audit["staged_full3"].eq(0)
    ).astype(int)

    quality = {
        "resolved_selected_children": int(len(portfolio)),
        "extra_capital_requests": int(len(candidates)),
        "same_time_damage_requests": {
            POLICY_DAMAGE_CONSERVATIVE: int(conservative_allocations["same_time_stop_at_request"].sum()),
            POLICY_DAMAGE_PERMISSIVE: int(permissive_allocations["same_time_stop_at_request"].sum()),
        },
        "k1_transition_audit": {
            "baseline_k1_full3_stops": int(k1_audit["full_3unit_stop"].sum()),
            "full3_stops_avoided_by_ladder": int(k1_audit["full3_avoided_by_k1_ladder"].sum()),
            "avoided_inside_k1_round_trip_chain": int(
                (k1_audit["full3_avoided_by_k1_ladder"].eq(1) & k1_audit["k1_round_trip_chain"].eq(1)).sum()
            ),
            "avoided_isolated_k1_stops": int(
                (k1_audit["full3_avoided_by_k1_ladder"].eq(1) & k1_audit["k1_round_trip_chain"].eq(0)).sum()
            ),
        },
        "invariants": {
            "all_policies_keep_all_children": bool(summary["children"].eq(1649).all()),
            "hard_sl_children_unchanged": bool(summary["hard_sl_children"].nunique() == 1),
            "tranche_R_matches_child_R": bool(all(
                np.isclose(
                    tranches[tranches["policy"].eq(policy)]["R_units"].sum(),
                    children[children["policy"].eq(policy)]["combined_R_units"].sum(),
                ) for policy in policies
            )),
            "tranche_stop_units_match_children": bool(all(
                np.isclose(
                    tranches[tranches["policy"].eq(policy)]["stop_units"].sum(),
                    children[children["policy"].eq(policy)]["stopped_loss_units"].sum(),
                ) for policy in policies
            )),
        },
        "interpretation_boundary": (
            "Candidate selectivity is an outcome audit, not causal authority. The damage/repair state itself uses only "
            "Hard SL and Child-survival information available by each request timestamp."
        ),
    }
    if not all(quality["invariants"].values()):
        raise RuntimeError(f"stage5 invariant failed: {quality['invariants']}")

    allocations = pd.concat([
        one_slot.assign(allocation_family="ONE_SLOT"),
        conservative_allocations.assign(allocation_family="DAMAGE_REPAIR_CONSERVATIVE"),
        permissive_allocations.assign(allocation_family="DAMAGE_REPAIR_PERMISSIVE"),
    ], ignore_index=True, sort=False)
    outputs = {
        "summary": args.out_dir / "V11_REASSEMBLY_STAGE5_DAMAGE_INVENTORY_SUMMARY.csv",
        "slices": args.out_dir / "V11_REASSEMBLY_STAGE5_DAMAGE_INVENTORY_SLICES.csv",
        "selectivity": args.out_dir / "V11_REASSEMBLY_STAGE5_REQUEST_SELECTIVITY.csv",
        "allocations": args.out_dir / "V11_REASSEMBLY_STAGE5_ALLOCATIONS.csv",
        "k1_audit": args.out_dir / "V11_REASSEMBLY_STAGE5_K1_TRANSITION_AUDIT.csv",
        "quality": args.out_dir / "V11_REASSEMBLY_STAGE5_DATA_QUALITY.json",
    }
    summary.to_csv(outputs["summary"], index=False)
    slices.to_csv(outputs["slices"], index=False)
    selectivity.to_csv(outputs["selectivity"], index=False)
    allocations.to_csv(outputs["allocations"], index=False)
    k1_audit.to_csv(outputs["k1_audit"], index=False)
    outputs["quality"].write_text(json.dumps(quality, indent=2), encoding="utf-8")
    manifest = {
        "status": "CONSUMED_DEVELOPMENT_STAGE5_ONLY",
        "authority": "NO TRADE, RELEASE, SIZING, LEVERAGE, EA, OR PRODUCTION AUTHORITY",
        "question": "Did the one-slot policy target round-trip loss, and can actual damage manage elastic inventory more selectively?",
        "input_sha256": {
            "events": stage3.sha256_file(args.events),
            "universe": stage3.sha256_file(args.universe),
            "stage2_ledger": stage3.sha256_file(args.stage2_ledger),
            "stage4_allocations": stage3.sha256_file(args.stage4_allocations),
        },
        "output_sha256": {key: stage3.sha256_file(path) for key, path in outputs.items()},
    }
    manifest_path = args.out_dir / "V11_REASSEMBLY_STAGE5_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print("\nDAMAGE INVENTORY SUMMARY")
    print(summary.to_string(index=False))
    print("\nREQUEST SELECTIVITY")
    print(selectivity.to_string(index=False))
    print("\nK1 TRANSITION AUDIT")
    print(json.dumps(quality["k1_transition_audit"], indent=2))


if __name__ == "__main__":
    main()
