"""Fit the future-facing V10 R3 K1 extreme-STOP shadow bundle.

The generic inner-logloss winner is retained as a diagnostic, but it is not
silently treated as the right model for a 2.5% danger-tail action.  The shadow
study fits the two fixed preprocessing/model families that improved structural
R in every completed 2024/2025/2026 outer walk-forward year: robust-scaled
logistic C=0.5 and shallow histogram gradient boosting.  Run-block bootstrap
keeps only robust C=0.5 as the action-bearing shadow member; HistGB remains a
non-authoritative disagreement diagnostic because its pooled lower bound
crossed zero.

The stability screen and q97.5 policy are both consumed-data research choices.
This artifact is for future shadow scoring, not live trading or promotion.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from probe_v10_r3_meta_danger import (
    K1_STOP_FEATURES,
    meta_inner_folds,
    meta_specs,
    reconstruct_r2_policy,
)
from tune_v10_r3_models import (
    Head,
    evaluate_spec,
    safe_metrics,
    selected_oof_and_test,
    sha256_file,
)


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", required=True, type=Path)
    parser.add_argument("--r2-model-json", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(
        args.universe,
        parse_dates=["decision", "entry_time", "exit_time", "run_end_decision", "label_available_at"],
    ).sort_values("decision", kind="mergesort").reset_index(drop=True)
    frame = reconstruct_r2_policy(frame, args.r2_model_json)
    candidates = frame[(frame["year"].ge(2023)) & frame["r2_W"].gt(0.0)].copy()
    head = Head("META_K1_STOP", "stop_hit", K1_STOP_FEATURES, "K1")
    folds = meta_inner_folds(candidates, head, max_folds=8)
    if len(folds) < 3:
        raise RuntimeError("not enough chronological folds for future model selection")

    selection: list[dict[str, object]] = []
    for spec in meta_specs():
        aggregate, fold_rows = evaluate_spec(candidates, head, spec, folds)
        selection.append({**aggregate, **asdict(spec)})
        for row in fold_rows:
            row["spec_id"] = spec.spec_id
    selection_frame = pd.DataFrame(selection).sort_values(
        ["logloss", "brier", "auc"], ascending=[True, True, False], kind="mergesort"
    )
    winner_id = str(selection_frame.iloc[0]["spec_id"])
    selection_frame["inner_logloss_winner"] = selection_frame["spec_id"].eq(winner_id).astype(int)

    stable_ids = {
        "robust_c05": "robust_logit|decision|C=0.5",
        "shallow_histgb": (
            "histgb|decision|learning_rate=0.03|max_iter=180|max_leaf_nodes=7|"
            "min_samples_leaf=45|l2_regularization=3.0"
        ),
    }
    selection_frame["stable_shadow_member"] = selection_frame["spec_id"].isin(
        stable_ids.values()
    ).astype(int)
    all_specs = {spec.spec_id: spec for spec in meta_specs()}
    missing = [spec_id for spec_id in stable_ids.values() if spec_id not in all_specs]
    if missing:
        raise RuntimeError(f"stable shadow specs missing from tournament: {missing}")

    member_artifacts: dict[str, dict[str, object]] = {}
    member_oof: dict[str, pd.Series] = {}
    member_thresholds: dict[str, float] = {}
    member_metrics: dict[str, dict[str, float]] = {}
    for name, spec_id in stable_ids.items():
        spec = all_specs[spec_id]
        # Passing candidates as the score frame returns final-fit probabilities
        # only as a diagnostic.  Each threshold comes exclusively from that
        # member's chronological calibrated OOF K1 scores.
        oof, _, final_model, platt = selected_oof_and_test(
            candidates, candidates, candidates, head, spec, folds
        )
        k1_oof = candidates["k"].eq(1) & oof.notna()
        threshold = float(np.quantile(oof.loc[k1_oof], 0.975))
        member_oof[name] = oof
        member_thresholds[name] = threshold
        member_metrics[name] = safe_metrics(
            candidates.loc[k1_oof, head.target], oof.loc[k1_oof].to_numpy(dtype=float)
        )
        member_artifacts[name] = {
            "spec": asdict(spec),
            "platt": asdict(platt),
            "q0975": threshold,
            "model": final_model,
        }

    common = candidates["k"].eq(1)
    for oof in member_oof.values():
        common &= oof.notna()
    reference = candidates.loc[
        common,
        ["signal_id", "decision", "year", "rid", "k", "L", "stop_hit", "pnl", "R"],
    ].copy()
    for name, oof in member_oof.items():
        score_column = f"{name}_calibrated_oof_k1_stop"
        flag_column = f"{name}_extreme_tail"
        reference[score_column] = oof.loc[common].to_numpy(dtype=float)
        reference[f"{name}_q0975"] = member_thresholds[name]
        reference[flag_column] = reference[score_column].ge(member_thresholds[name]).astype(int)
    reference["primary_shadow_veto"] = reference["robust_c05_extreme_tail"].astype(int)
    reference["diagnostic_histgb_disagreement"] = (
        reference["robust_c05_extreme_tail"]
        != reference["shallow_histgb_extreme_tail"]
    ).astype(int)

    bundle = {
        "authority": "CONSUMED-DATA SHADOW RESEARCH / NOT STRATEGY AUTHORITY",
        "head": head.name,
        "target": head.target,
        "population": head.population,
        "features": list(head.features),
        "policy": "veto R2-selected K1 only when robust_c05 score >= its calibrated OOF q97.5",
        "primary_action_member": "robust_c05",
        "diagnostic_only_member": "shallow_histgb",
        "members": member_artifacts,
    }
    joblib.dump(bundle, args.out_dir / "V10_R3_K1STOP_FUTURE_SHADOW_BUNDLE.joblib")
    selection_frame.to_csv(args.out_dir / "V10_R3_K1STOP_FUTURE_MODEL_SELECTION.csv", index=False)
    reference.to_csv(args.out_dir / "V10_R3_K1STOP_FUTURE_OOF_REFERENCE.csv", index=False)

    manifest = {
        "ok": True,
        "authority": "CONSUMED-DATA SHADOW RESEARCH / NOT STRATEGY AUTHORITY",
        "universe_sha256": sha256_file(args.universe),
        "r2_model_sha256": sha256_file(args.r2_model_json),
        "candidate_rows": int(len(candidates)),
        "k1_training_rows": int(candidates["k"].eq(1).sum()),
        "chronological_folds": len(folds),
        "inner_logloss_winner_not_deployed": winner_id,
        "stable_shadow_members": stable_ids,
        "stability_screen": "fixed spec produced positive structural-R delta in each 2024, 2025, and 2026 outer walk-forward year",
        "primary_action_member": "robust_c05",
        "primary_reason": "positive delta-R in every outer year and positive pooled 95% run-block bootstrap lower bound; HistGB and union lower bounds crossed zero",
        "diagnostic_only_member": "shallow_histgb",
        "generic_selection_objective": "minimum chronological-fold log loss; Brier then AUC tie-break",
        "calibration": "Platt sigmoid from chronological OOF predictions only",
        "member_q0975": member_thresholds,
        "member_oof_metrics": member_metrics,
        "oof_k1_rows": int(common.sum()),
        "oof_primary_tail_rows": int(reference["primary_shadow_veto"].sum()),
        "shadow_rule": "score only R2-selected K1 candidates; shadow-veto only when robust_c05 crosses calibrated OOF q97.5; log HistGB disagreement without action authority",
        "limitations": [
            "all 2022-2026 evidence is consumed development evidence",
            "the q97.5 policy family was selected after a consumed-data scan",
            "the primary member was selected with post-hoc outer-year and bootstrap stability evidence",
            "historical meta features use their causal R2 era while future inference uses the R2 FUTURE era",
            "no MQL export or EA integration is authorized by this shadow artifact",
        ],
    }
    (args.out_dir / "V10_R3_K1STOP_FUTURE_SHADOW_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
