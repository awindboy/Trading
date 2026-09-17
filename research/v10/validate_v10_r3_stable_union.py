"""Independent economics audit for the V10 R3 stable-model frontier.

The input action ledger is produced by the model/preprocessing ablation.  This
validator does not import its scoring or policy-metric helpers; it joins the
actions back to the causal universe and committed R2 ledger, checks Boolean
policy algebra, recomputes outcomes, and bootstraps run-level delta R.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from validate_v10_r3_k1stop_candidate import (
    bootstrap_delta,
    economic_row,
    file_hash,
)


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", required=True, type=Path)
    parser.add_argument("--action-ledger", required=True, type=Path)
    parser.add_argument("--r2-ledger", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--bootstrap-draws", type=int, default=20_000)
    return parser.parse_args()


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    dates = ["decision", "entry_time", "exit_time", "run_end_decision", "label_available_at"]
    universe = pd.read_csv(args.universe, parse_dates=dates)
    universe = universe[universe["year"].between(2024, 2026)].copy()
    actions = pd.read_csv(
        args.action_ledger, parse_dates=["decision", "entry_time", "exit_time"]
    )
    r2 = pd.read_csv(args.r2_ledger, parse_dates=["decision"])[["decision", "W"]]
    if universe["decision"].duplicated().any() or actions["decision"].duplicated().any():
        raise RuntimeError("decision keys are not unique")
    frame = universe.merge(
        actions[
            [
                "decision", "r2_W", "robust_c05_veto", "shallow_histgb_veto",
                "stable_intersection_veto", "stable_union_veto",
                "stable_intersection_W", "stable_union_W",
            ]
        ],
        on="decision",
        how="outer",
        validate="one_to_one",
        indicator=True,
    )
    if not frame["_merge"].eq("both").all():
        raise RuntimeError("universe and consensus action decisions differ")
    frame = frame.drop(columns="_merge").merge(
        r2, on="decision", how="left", validate="one_to_one"
    ).sort_values("decision", kind="mergesort").reset_index(drop=True).copy()
    if frame["W"].isna().any() or not np.allclose(frame["r2_W"], frame["W"]):
        raise RuntimeError("consensus baseline differs from committed R2 ledger")

    robust = frame["robust_c05_veto"].eq(1).to_numpy()
    histgb = frame["shallow_histgb_veto"].eq(1).to_numpy()
    expected_union = robust | histgb
    expected_intersection = robust & histgb
    if not np.array_equal(expected_union.astype(int), frame["stable_union_veto"].to_numpy(dtype=int)):
        raise RuntimeError("union Boolean policy mismatch")
    if not np.array_equal(expected_intersection.astype(int), frame["stable_intersection_veto"].to_numpy(dtype=int)):
        raise RuntimeError("intersection Boolean policy mismatch")
    expected_units = np.where(expected_union, 0.0, frame["W"].to_numpy(dtype=float))
    if not np.allclose(expected_units, frame["stable_union_W"]):
        raise RuntimeError("union units mismatch")

    frame["audit_pnl_alt_nha"] = frame["pnl"].astype(float)
    frame["audit_R_alt_nha"] = frame["R"].astype(float)
    ambiguous = frame["same_m1_exit_stop_ambiguous"].eq(1)
    frame.loc[ambiguous, "audit_pnl_alt_nha"] = frame.loc[ambiguous, "alternative_nha_pnl"]
    frame.loc[ambiguous, "audit_R_alt_nha"] = frame.loc[ambiguous, "alternative_nha_R"]

    baseline = frame["W"].to_numpy(dtype=float)
    policies = {
        "R2_DEFAULT": baseline,
        "ROBUST_C05": np.where(robust, 0.0, baseline),
        "SHALLOW_HISTGB": np.where(histgb, 0.0, baseline),
        "STABLE_INTERSECTION": np.where(expected_intersection, 0.0, baseline),
        "STABLE_UNION": frame["stable_union_W"].to_numpy(dtype=float),
    }
    metrics: list[dict[str, object]] = []
    for period, mask in [
        ("2024", frame["year"].eq(2024).to_numpy()),
        ("2025", frame["year"].eq(2025).to_numpy()),
        ("2026", frame["year"].eq(2026).to_numpy()),
        ("POOLED_2024_2026", np.ones(len(frame), dtype=bool)),
    ]:
        subset = frame.loc[mask].reset_index(drop=True)
        for name, all_units in policies.items():
            units = all_units[mask]
            metrics.append(economic_row(subset, units, name, period))
            metrics.append(
                economic_row(
                    subset,
                    units,
                    name,
                    period,
                    "audit_pnl_alt_nha",
                    "audit_R_alt_nha",
                )
            )

    bootstrap_parts: list[pd.DataFrame] = []
    bootstrap_summary: list[dict[str, object]] = []
    for name, units in policies.items():
        if name == "R2_DEFAULT":
            continue
        draws, summary = bootstrap_delta(frame, baseline, units, args.bootstrap_draws)
        draws.insert(0, "policy", name)
        bootstrap_parts.append(draws)
        for row in summary:
            bootstrap_summary.append({"policy": name, **row})
    bootstrap = pd.concat(bootstrap_parts, ignore_index=True)
    policy_masks = {
        "ROBUST_C05": robust,
        "SHALLOW_HISTGB": histgb,
        "STABLE_INTERSECTION": expected_intersection,
        "STABLE_UNION": expected_union,
    }
    frontier_veto_summaries: dict[str, dict[str, object]] = {}
    for name, veto_mask in policy_masks.items():
        selected = frame.loc[veto_mask].copy()
        selected["weighted_pnl_removed"] = selected["W"] * selected["pnl"]
        selected["weighted_R_removed"] = selected["W"] * selected["R"]
        frontier_veto_summaries[name] = {
            "rows": int(len(selected)),
            "units_removed": float(selected["W"].sum()),
            "wins_removed": int(selected["pnl"].gt(0.0).sum()),
            "losses_removed": int(selected["pnl"].lt(0.0).sum()),
            "stop_hits_removed": int(selected["stop_hit"].sum()),
            "oracle_early3_removed": int(selected["early3"].sum()),
            "L6plus_positive_removed": int((selected["L"].ge(6) & selected["pnl"].gt(0.0)).sum()),
            "candidate_delta_pnl": float(-selected["weighted_pnl_removed"].sum()),
            "candidate_delta_R": float(-selected["weighted_R_removed"].sum()),
        }
    vetoed = frame.loc[expected_union].copy()
    vetoed["weighted_pnl_removed"] = vetoed["W"] * vetoed["pnl"]
    vetoed["weighted_R_removed"] = vetoed["W"] * vetoed["R"]
    veto_summary = {
        **frontier_veto_summaries["STABLE_UNION"],
        "robust_only": int((robust & ~histgb).sum()),
        "histgb_only": int((histgb & ~robust).sum()),
        "both": int((robust & histgb).sum()),
    }

    pd.DataFrame(metrics).to_csv(
        args.out_dir / "V10_R3_STABLE_UNION_INDEPENDENT_METRICS.csv", index=False
    )
    bootstrap.to_csv(args.out_dir / "V10_R3_STABLE_UNION_BOOTSTRAP_DRAWS.csv", index=False)
    pd.DataFrame(bootstrap_summary).to_csv(
        args.out_dir / "V10_R3_STABLE_UNION_BOOTSTRAP_SUMMARY.csv", index=False
    )
    vetoed.to_csv(args.out_dir / "V10_R3_STABLE_UNION_VETOED_EVENTS.csv", index=False)

    receipt = {
        "ok": True,
        "authority": "CONSUMED-DATA SHADOW RESEARCH / NOT STRATEGY AUTHORITY",
        "policy": "STABLE MODEL FRONTIER",
        "policy_algebra": "R2-selected K1 vetoed when robust-C0.5 OR shallow-HistGB score crosses its own prior-OOF q97.5",
        "veto_summary": veto_summary,
        "frontier_veto_summaries": frontier_veto_summaries,
        "bootstrap_summary": bootstrap_summary,
        "same_m1_ambiguous_rows": int(ambiguous.sum()),
        "source_hashes": {
            "universe": file_hash(args.universe),
            "action_ledger": file_hash(args.action_ledger),
            "r2_ledger": file_hash(args.r2_ledger),
        },
        "limitations": [
            "member families and union policy were selected from consumed 2024-2026 development evidence",
            "no untouched temporal or external validation exists",
            "same-M1 NHA-versus-SL ordering remains a sensitivity bound",
        ],
    }
    (args.out_dir / "V10_R3_STABLE_UNION_VALIDATION.json").write_text(
        json.dumps(receipt, indent=2), encoding="utf-8"
    )
    pooled = pd.DataFrame(metrics)
    pooled = pooled[
        pooled["period"].eq("POOLED_2024_2026")
        & pooled["outcome_convention"].eq("conservative_stop")
    ]
    print(pooled[["policy", "entries", "units", "pnl", "pf", "R", "pf_R", "dd_R", "oracle_recall", "l6_positive_child_retention"]].to_string(index=False))
    print("\nVETO SUMMARY")
    print(json.dumps(veto_summary, indent=2))
    print("\nBOOTSTRAP SUMMARY")
    print(pd.DataFrame(bootstrap_summary).to_string(index=False))


if __name__ == "__main__":
    main()
