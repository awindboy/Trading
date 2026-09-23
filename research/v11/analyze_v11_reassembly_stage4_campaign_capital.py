"""Stage-4 V11 reassembly: one participation unit per Child, one conviction slot per journey.

Stage 3 showed that staging only k1 capital leaves the portfolio's peak gross
exposure unchanged because independently selected k2+ Children keep pyramiding
their own 3-unit R7G allocations.  This mechanism diagnostic treats every
selected Child as participation-worthy for one unit while the additional two
units become one shared, causal conviction slot per FAST run (`rid`).

Two explicit same-decision priority conventions are retained.  They are a
mechanism frontier, not a rule search: an existing k1 continuation top-up may
claim the slot first, or the independent new k2+ Child may claim it first.
Nothing here has trade, release, sizing, leverage, EA, or production authority.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_v11_reassembly_stage3_portfolio as stage3


POLICY_ONE_UNIT = "ALL_CHILDREN_ONE_UNIT"
POLICY_K1_PRIORITY = "ONE_CAMPAIGN_SLOT_K1_CONTINUATION_PRIORITY"
POLICY_NEW_PRIORITY = "ONE_CAMPAIGN_SLOT_NEW_CHILD_PRIORITY"


def base_tranches(portfolio: pd.DataFrame, policy: str) -> pd.DataFrame:
    rows = []
    for row in portfolio.itertuples(index=False):
        rows.append({
            "policy": policy,
            "signal_id": row.signal_id,
            "rid": int(row.rid),
            "k": int(row.k),
            "dir": int(row.dir),
            "tranche": "PARTICIPATION",
            "open_time": row.entry_time,
            "close_time": row.exit_time,
            "units": 1.0,
            "R_per_unit": float(row.R),
            "R_units": float(row.R),
            "stop_units": float(row.stop_hit),
        })
    return pd.DataFrame(rows)


def extra_candidates(portfolio: pd.DataFrame, ladder: pd.DataFrame) -> pd.DataFrame:
    rows = []
    k1_keys = portfolio[portfolio["k"].eq(1)][["decision_ts", "signal_id", "rid", "dir"]]
    valid_k1 = ladder[ladder["k2_valid"].eq(1)].merge(
        k1_keys, on=["decision_ts", "rid", "dir"], how="inner", validate="one_to_one",
        suffixes=("_stage2", "_portfolio"),
    )
    for row in valid_k1.itertuples(index=False):
        rows.append({
            "signal_id": row.signal_id_portfolio,
            "rid": int(row.rid),
            "k": 1,
            "dir": int(row.dir),
            "candidate_type": "K1_FAST_K2_CONTINUATION",
            "open_time": row.k2_entry_time,
            "close_time": row.k2_exit_time,
            "units": 2.0,
            "R_per_unit": float(row.k2_R),
            "R_units": 2.0 * float(row.k2_R),
            "stop_units": 2.0 * float(row.k2_stop_hit),
        })
    for row in portfolio[portfolio["k"].gt(1) & portfolio["r7g_weight"].eq(3)].itertuples(index=False):
        rows.append({
            "signal_id": row.signal_id,
            "rid": int(row.rid),
            "k": int(row.k),
            "dir": int(row.dir),
            "candidate_type": "NEW_CHILD_R7G_EXTRA",
            "open_time": row.entry_time,
            "close_time": row.exit_time,
            "units": 2.0,
            "R_per_unit": float(row.R),
            "R_units": 2.0 * float(row.R),
            "stop_units": 2.0 * float(row.stop_hit),
        })
    candidates = pd.DataFrame(rows)
    for column in ("open_time", "close_time"):
        candidates[column] = pd.to_datetime(candidates[column])
    return candidates


def allocate_one_slot(candidates: pd.DataFrame, policy: str, k1_priority: bool) -> pd.DataFrame:
    allocations: list[pd.DataFrame] = []
    for _, run in candidates.groupby("rid", sort=False):
        run = run.copy()
        if k1_priority:
            run["priority"] = run["candidate_type"].ne("K1_FAST_K2_CONTINUATION").astype(int)
        else:
            run["priority"] = run["candidate_type"].eq("K1_FAST_K2_CONTINUATION").astype(int)
        run = run.sort_values(["open_time", "priority", "k", "signal_id"]).copy()
        active_until = pd.Timestamp.min
        decisions = []
        blockers = []
        active_signal: str | None = None
        for row in run.itertuples(index=False):
            if pd.Timestamp(row.open_time) >= active_until:
                decisions.append("ALLOCATED")
                blockers.append("")
                active_until = pd.Timestamp(row.close_time)
                active_signal = str(row.signal_id)
            else:
                decisions.append("SLOT_OCCUPIED")
                blockers.append(active_signal or "")
        run["allocation"] = decisions
        run["blocked_by_signal_id"] = blockers
        run["policy"] = policy
        allocations.append(run)
    return pd.concat(allocations, ignore_index=True)


def campaign_policy(
    portfolio: pd.DataFrame,
    allocations: pd.DataFrame,
    policy: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    tranches = [base_tranches(portfolio, policy)]
    funded = allocations[allocations["allocation"].eq("ALLOCATED")].copy()
    funded["policy"] = policy
    funded["tranche"] = funded["candidate_type"]
    tranches.append(funded[[
        "policy", "signal_id", "rid", "k", "dir", "tranche", "open_time",
        "close_time", "units", "R_per_unit", "R_units", "stop_units",
    ]])
    tranche_frame = pd.concat(tranches, ignore_index=True)
    aggregate = tranche_frame.groupby("signal_id", as_index=False).agg(
        combined_R_units=("R_units", "sum"),
        stopped_loss_units=("stop_units", "sum"),
        funded_units=("units", "sum"),
    )
    children = portfolio.merge(aggregate, on="signal_id", how="left", validate="one_to_one")
    children["policy"] = policy
    children["full_3unit_stop"] = children["stopped_loss_units"].ge(3 - 1e-9).astype(int)
    return children, tranche_frame


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
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    portfolio = stage3.load_selected_portfolio(args.events, args.universe)
    ladder = stage3.load_k1_ladder(args.stage2_ledger)
    stage3_children = stage3.child_ledgers(portfolio, ladder)
    stage3_tranches = stage3.build_tranches(portfolio, ladder)

    one_tranches = base_tranches(portfolio, POLICY_ONE_UNIT)
    one_children, _ = campaign_policy(
        portfolio,
        pd.DataFrame(columns=list(extra_candidates(portfolio, ladder).columns) + ["allocation"]),
        POLICY_ONE_UNIT,
    )
    candidates = extra_candidates(portfolio, ladder)
    k1_allocations = allocate_one_slot(candidates, POLICY_K1_PRIORITY, k1_priority=True)
    new_allocations = allocate_one_slot(candidates, POLICY_NEW_PRIORITY, k1_priority=False)
    k1_children, k1_tranches = campaign_policy(portfolio, k1_allocations, POLICY_K1_PRIORITY)
    new_children, new_tranches = campaign_policy(portfolio, new_allocations, POLICY_NEW_PRIORITY)

    children = pd.concat([stage3_children, one_children, k1_children, new_children], ignore_index=True, sort=False)
    tranches = pd.concat([stage3_tranches, one_tranches, k1_tranches, new_tranches], ignore_index=True, sort=False)
    policies = [
        stage3.POLICY_BASELINE,
        stage3.POLICY_LADDER,
        POLICY_ONE_UNIT,
        POLICY_K1_PRIORITY,
        POLICY_NEW_PRIORITY,
    ]
    summary_rows = []
    paths: dict[str, np.ndarray] = {}
    slice_rows = []
    for policy in policies:
        policy_children = children[children["policy"].eq(policy)].copy()
        policy_tranches = tranches[tranches["policy"].eq(policy)].copy()
        summary_rows.append(stage3.summarize_policy(policy_children, policy_tranches))
        paths[policy] = stage3.realized_path(policy_tranches)["R_units"].to_numpy(dtype=float)
        for year, group in policy_children.groupby("year", sort=True):
            slice_rows.append(stage3.summarize_child_slice(group, "YEAR", str(int(year))))
        for direction, group in policy_children.groupby("dir", sort=True):
            slice_rows.append(stage3.summarize_child_slice(
                group, "SIDE", "LONG" if int(direction) > 0 else "SHORT"
            ))
    summary = add_relative_metrics(pd.DataFrame(summary_rows), paths)
    slices = pd.DataFrame(slice_rows)
    allocations = pd.concat([k1_allocations, new_allocations], ignore_index=True)

    quality = {
        "resolved_selected_children": int(len(portfolio)),
        "extra_candidates": {
            "total": int(len(candidates)),
            "k1_fast_k2": int(candidates["candidate_type"].eq("K1_FAST_K2_CONTINUATION").sum()),
            "new_child_r7g": int(candidates["candidate_type"].eq("NEW_CHILD_R7G_EXTRA").sum()),
        },
        "allocation_counts": {
            policy: {
                str(action): int(len(group))
                for action, group in allocations[allocations["policy"].eq(policy)].groupby("allocation")
            }
            for policy in (POLICY_K1_PRIORITY, POLICY_NEW_PRIORITY)
        },
        "invariants": {
            "all_policies_keep_all_children": bool(summary["children"].eq(1649).all()),
            "all_policies_keep_one_unit_per_child": bool(summary["funded_units"].ge(1649).all()),
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
            "The one-slot architecture is a consumed-data mechanism probe. It preserves participation but changes "
            "the ownership of extra capital; costs, execution, margin, and independent validation remain absent."
        ),
    }
    if not all(quality["invariants"].values()):
        raise RuntimeError(f"stage4 invariant failed: {quality['invariants']}")

    outputs = {
        "summary": args.out_dir / "V11_REASSEMBLY_STAGE4_CAMPAIGN_CAPITAL_SUMMARY.csv",
        "slices": args.out_dir / "V11_REASSEMBLY_STAGE4_CAMPAIGN_CAPITAL_SLICES.csv",
        "children": args.out_dir / "V11_REASSEMBLY_STAGE4_CHILD_LEDGER.csv",
        "tranches": args.out_dir / "V11_REASSEMBLY_STAGE4_TRANCHE_LEDGER.csv",
        "allocations": args.out_dir / "V11_REASSEMBLY_STAGE4_SLOT_ALLOCATIONS.csv",
        "quality": args.out_dir / "V11_REASSEMBLY_STAGE4_DATA_QUALITY.json",
    }
    summary.to_csv(outputs["summary"], index=False)
    slices.to_csv(outputs["slices"], index=False)
    children.to_csv(outputs["children"], index=False)
    tranches.to_csv(outputs["tranches"], index=False)
    allocations.to_csv(outputs["allocations"], index=False)
    outputs["quality"].write_text(json.dumps(quality, indent=2), encoding="utf-8")
    manifest = {
        "status": "CONSUMED_DEVELOPMENT_STAGE4_ONLY",
        "authority": "NO TRADE, RELEASE, SIZING, LEVERAGE, EA, EXECUTION, OR PRODUCTION AUTHORITY",
        "question": "Can one shared conviction-capital slot per FAST journey preserve participation while reducing repeated full-size loss?",
        "input_sha256": {
            "events": stage3.sha256_file(args.events),
            "universe": stage3.sha256_file(args.universe),
            "stage2_ledger": stage3.sha256_file(args.stage2_ledger),
        },
        "output_sha256": {key: stage3.sha256_file(path) for key, path in outputs.items()},
    }
    manifest_path = args.out_dir / "V11_REASSEMBLY_STAGE4_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print("\nCAMPAIGN CAPITAL SUMMARY")
    print(summary.to_string(index=False))
    print("\nALLOCATION COUNTS")
    print(json.dumps(quality["allocation_counts"], indent=2))


if __name__ == "__main__":
    main()
