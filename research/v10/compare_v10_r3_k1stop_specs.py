"""Ablate fixed preprocessing/model specifications for the V10 R3 K1 STOP head.

The purpose is deployment simplicity and overfit diagnosis: a useful danger
gate should not depend on a different model family every outer year.  Every
score is still calibrated from prior-only chronological OOF predictions and
the veto remains the prior OOF q97.5 tail.  Results are consumed-data shadow
research only.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from probe_v10_r3_meta_danger import (
    K1_STOP_FEATURES,
    meta_inner_folds,
    reconstruct_r2_policy,
)
from tune_v10_r3_models import (
    Head,
    ModelSpec,
    policy_metrics,
    safe_metrics,
    selected_oof_and_test,
)


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", required=True, type=Path)
    parser.add_argument("--r2-model-json", required=True, type=Path)
    parser.add_argument("--r2-ledger", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def fixed_specs() -> list[ModelSpec]:
    result: list[ModelSpec] = []
    for weight in ("decision", "run_sqrt"):
        for c_value in (0.02, 0.1, 0.5):
            result.append(ModelSpec("robust_logit", weight, C=c_value))
        for c_value in (0.02, 0.1):
            result.append(ModelSpec("spline_logit", weight, C=c_value, n_knots=3))
        result.append(
            ModelSpec(
                "histgb",
                weight,
                learning_rate=0.03,
                max_iter=180,
                max_leaf_nodes=7,
                min_samples_leaf=45,
                l2_regularization=3.0,
            )
        )
    return result


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(
        args.universe,
        parse_dates=["decision", "entry_time", "exit_time", "run_end_decision", "label_available_at"],
    ).sort_values("decision", kind="mergesort").reset_index(drop=True)
    frame = reconstruct_r2_policy(frame, args.r2_model_json)

    reference = pd.read_csv(args.r2_ledger, parse_dates=["decision"])[["decision", "W"]]
    check = frame[frame["year"].ge(2024)].merge(
        reference, on="decision", how="outer", validate="one_to_one", indicator=True
    )
    if not check["_merge"].eq("both").all():
        raise RuntimeError("R2 reference rows differ")
    both = check["_merge"].eq("both")
    if not np.allclose(check.loc[both, "r2_W"], check.loc[both, "W"]):
        raise RuntimeError("R2 reference policy differs")

    candidates = frame[(frame["year"].ge(2023)) & frame["r2_W"].gt(0.0)].copy()
    head = Head("META_K1_STOP", "stop_hit", K1_STOP_FEATURES, "K1")
    detail: list[dict[str, object]] = []
    unit_by_spec_year: dict[tuple[str, int], np.ndarray] = {}

    for year in (2024, 2025, 2026):
        boundary = pd.Timestamp(year=year, month=1, day=1)
        train = candidates[
            (candidates["decision"] < boundary)
            & (candidates["label_available_at"] < boundary)
        ].copy()
        test = candidates[candidates["year"].eq(year)].copy()
        all_test = frame[frame["year"].eq(year)].copy()
        folds = meta_inner_folds(train, head)
        if len(folds) < 2:
            raise RuntimeError(f"insufficient chronological folds for {year}")

        for spec in fixed_specs():
            oof, probability, _, _ = selected_oof_and_test(
                candidates, train, test, head, spec, folds
            )
            prior_k1 = train["k"].eq(1) & oof.notna()
            threshold = float(np.quantile(oof.loc[prior_k1], 0.975))
            prior_metrics = safe_metrics(
                train.loc[prior_k1, head.target], oof.loc[prior_k1].to_numpy(dtype=float)
            )
            prior_ap = float(
                average_precision_score(
                    train.loc[prior_k1, head.target],
                    oof.loc[prior_k1].to_numpy(dtype=float),
                )
            )
            prior_tail_index = oof.loc[prior_k1][oof.loc[prior_k1].ge(threshold)].index
            prior_tail = candidates.loc[prior_tail_index]
            prior_tail_gain_r = float(
                -(prior_tail["r2_W"] * prior_tail["R"]).sum()
            )
            prior_tail_positive_r_removed = float(
                (
                    prior_tail.loc[prior_tail["R"].gt(0.0), "r2_W"]
                    * prior_tail.loc[prior_tail["R"].gt(0.0), "R"]
                ).sum()
            )
            test_k1 = test["k"].eq(1).to_numpy()
            veto = test_k1 & (probability >= threshold)
            candidate_units = test["r2_W"].to_numpy(dtype=float).copy()
            candidate_units[veto] = 0.0
            full_units = all_test["r2_W"].to_numpy(dtype=float).copy()
            positions = {value: pos for pos, value in enumerate(all_test["decision"])}
            for decision, units in zip(test["decision"], candidate_units):
                full_units[positions[decision]] = units
            unit_by_spec_year[(spec.spec_id, year)] = full_units

            population = test["k"].eq(1).to_numpy()
            metrics = safe_metrics(test.loc[population, head.target], probability[population])
            economics = policy_metrics(all_test, full_units, spec.spec_id, str(year))
            detail.append(
                {
                    "outer_year": year,
                    "spec_id": spec.spec_id,
                    **asdict(spec),
                    "prior_oof_k1_n": int(prior_k1.sum()),
                    "q0975": threshold,
                    "vetoed": int(veto.sum()),
                    "prior_oof_auc": prior_metrics["auc"],
                    "prior_oof_logloss": prior_metrics["logloss"],
                    "prior_oof_brier": prior_metrics["brier"],
                    "prior_oof_average_precision": prior_ap,
                    "prior_tail_n": int(len(prior_tail)),
                    "prior_tail_stop_precision": float(prior_tail["stop_hit"].mean()),
                    "prior_tail_gain_R": prior_tail_gain_r,
                    "prior_tail_positive_R_removed": prior_tail_positive_r_removed,
                    **{f"model_{key}": value for key, value in metrics.items()},
                    **{f"policy_{key}": value for key, value in economics.items() if key not in {"year", "policy"}},
                }
            )

    full = frame[frame["year"].between(2024, 2026)].copy()
    pooled: list[dict[str, object]] = []
    baseline = full["r2_W"].to_numpy(dtype=float)
    pooled.append(policy_metrics(full, baseline, "R2_DEFAULT", "POOLED_2024_2026"))
    for spec in fixed_specs():
        units = np.concatenate([unit_by_spec_year[(spec.spec_id, year)] for year in (2024, 2025, 2026)])
        pooled.append(policy_metrics(full, units, spec.spec_id, "POOLED_2024_2026"))

    detail_frame = pd.DataFrame(detail)
    detail_frame.to_csv(args.out_dir / "V10_R3_K1STOP_FIXED_SPEC_BY_YEAR.csv", index=False)
    pooled_frame = pd.DataFrame(pooled).sort_values("R", ascending=False)
    pooled_frame.to_csv(args.out_dir / "V10_R3_K1STOP_FIXED_SPEC_POOLED.csv", index=False)

    objective_specs = {
        "MIN_LOGLOSS": (["prior_oof_logloss", "prior_oof_brier", "prior_oof_auc"], [True, True, False]),
        "MAX_AVERAGE_PRECISION": (["prior_oof_average_precision", "prior_oof_logloss"], [False, True]),
        "MAX_TAIL_STOP_PRECISION": (["prior_tail_stop_precision", "prior_tail_gain_R", "prior_oof_logloss"], [False, False, True]),
        "MAX_TAIL_GAIN_R": (["prior_tail_gain_R", "prior_tail_stop_precision", "prior_oof_logloss"], [False, False, True]),
    }
    adaptive_rows: list[dict[str, object]] = []
    adaptive_selection: list[dict[str, object]] = []
    for objective, (columns, ascending) in objective_specs.items():
        yearly_units: list[np.ndarray] = []
        for year in (2024, 2025, 2026):
            ranked = detail_frame[detail_frame["outer_year"].eq(year)].sort_values(
                columns, ascending=ascending, kind="mergesort"
            )
            chosen = ranked.iloc[0]
            chosen_id = str(chosen["spec_id"])
            yearly_units.append(unit_by_spec_year[(chosen_id, year)])
            adaptive_selection.append(
                {
                    "objective": objective,
                    "outer_year": year,
                    "selected_spec": chosen_id,
                    **{column: chosen[column] for column in columns},
                    "realized_test_R": chosen["policy_R"],
                    "realized_test_pf_R": chosen["policy_pf_R"],
                    "realized_test_dd_R": chosen["policy_dd_R"],
                }
            )
        adaptive_rows.append(
            policy_metrics(
                full,
                np.concatenate(yearly_units),
                objective,
                "POOLED_2024_2026",
            )
        )
    pd.DataFrame(adaptive_selection).to_csv(
        args.out_dir / "V10_R3_K1STOP_ADAPTIVE_SELECTION.csv", index=False
    )
    adaptive_frame = pd.DataFrame(adaptive_rows).sort_values("R", ascending=False)
    adaptive_frame.to_csv(args.out_dir / "V10_R3_K1STOP_ADAPTIVE_OBJECTIVES.csv", index=False)

    # Cross-family consensus is a purpose-specific robustness check.  These are
    # the only two fixed specifications whose q97.5 gate improved structural R
    # in every outer year.  Intersection asks both models to flag the same K1;
    # union asks either model.  Neither is promoted by this consumed-data scan.
    robust_id = "robust_logit|decision|C=0.5"
    histgb_id = (
        "histgb|decision|learning_rate=0.03|max_iter=180|max_leaf_nodes=7|"
        "min_samples_leaf=45|l2_regularization=3.0"
    )
    consensus_rows: list[dict[str, object]] = []
    consensus_pooled: dict[str, list[np.ndarray]] = {
        "STABLE_INTERSECTION": [],
        "STABLE_UNION": [],
    }
    consensus_action_parts: list[pd.DataFrame] = []
    for year in (2024, 2025, 2026):
        all_test = frame[frame["year"].eq(year)].copy()
        base = all_test["r2_W"].to_numpy(dtype=float)
        robust_units = unit_by_spec_year[(robust_id, year)]
        histgb_units = unit_by_spec_year[(histgb_id, year)]
        robust_veto = (base > 0.0) & (robust_units == 0.0)
        histgb_veto = (base > 0.0) & (histgb_units == 0.0)
        actions = all_test[
            ["signal_id", "decision", "entry_time", "exit_time", "year", "dir", "rid", "k", "L", "pnl", "R", "early3", "stop_hit", "same_m1_exit_stop_ambiguous"]
        ].copy()
        actions["r2_W"] = base
        actions["robust_c05_veto"] = robust_veto.astype(int)
        actions["shallow_histgb_veto"] = histgb_veto.astype(int)
        actions["stable_intersection_veto"] = (robust_veto & histgb_veto).astype(int)
        actions["stable_union_veto"] = (robust_veto | histgb_veto).astype(int)
        actions["stable_intersection_W"] = np.where(robust_veto & histgb_veto, 0.0, base)
        actions["stable_union_W"] = np.where(robust_veto | histgb_veto, 0.0, base)
        consensus_action_parts.append(actions)
        for name, veto in (
            ("STABLE_INTERSECTION", robust_veto & histgb_veto),
            ("STABLE_UNION", robust_veto | histgb_veto),
        ):
            units = base.copy()
            units[veto] = 0.0
            consensus_pooled[name].append(units)
            row = policy_metrics(all_test, units, name, str(year))
            row["vetoed"] = int(veto.sum())
            consensus_rows.append(row)
    for name, parts in consensus_pooled.items():
        units = np.concatenate(parts)
        row = policy_metrics(full, units, name, "POOLED_2024_2026")
        row["vetoed"] = int(((baseline > 0.0) & (units == 0.0)).sum())
        consensus_rows.append(row)
    consensus_frame = pd.DataFrame(consensus_rows)
    consensus_frame.to_csv(args.out_dir / "V10_R3_K1STOP_STABLE_CONSENSUS.csv", index=False)
    pd.concat(consensus_action_parts, ignore_index=True).to_csv(
        args.out_dir / "V10_R3_K1STOP_STABLE_CONSENSUS_ACTION_LEDGER.csv", index=False
    )
    print(
        pooled_frame[
            ["policy", "entries", "units", "pnl", "pf", "R", "pf_R", "dd_R", "oracle_recall", "l6_positive_child_retention"]
        ].to_string(index=False)
    )
    print("\nADAPTIVE INNER-SELECTION OBJECTIVES")
    print(
        adaptive_frame[
            ["policy", "entries", "units", "pnl", "pf", "R", "pf_R", "dd_R", "oracle_recall", "l6_positive_child_retention"]
        ].to_string(index=False)
    )
    print("\nSTABLE CROSS-FAMILY CONSENSUS")
    print(
        consensus_frame[consensus_frame["year"].eq("POOLED_2024_2026")][
            ["policy", "vetoed", "entries", "units", "pnl", "pf", "R", "pf_R", "dd_R", "oracle_recall", "l6_positive_child_retention"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
