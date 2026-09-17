"""Purpose-specific feature-family ablation for the V10 R3 K1 STOP gate.

The experiment fixes preprocessing and model complexity (RobustScaler 10-90,
logistic C=0.5) and changes only semantically coherent feature families.  This
tests the user's central hypothesis that more inputs are not automatically
better.  Every threshold remains prior-only calibrated OOF q97.5 and every
reported year is an outer walk-forward test.  Results are consumed-data shadow
research.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from probe_v10_r3_meta_danger import (
    K1_STOP_FEATURES,
    meta_inner_folds,
    reconstruct_r2_policy,
)
from tune_v10_r3_models import Head, ModelSpec, policy_metrics, safe_metrics, selected_oof_and_test


R2_META = (
    "r2_p_runway", "r2_p_severe", "r2_p_stop", "r2_p_shock", "r2_score", "r2_W"
)

GEOMETRY = (
    "stop_dist_atr", "fast_body_rng", "std_body_rng", "adx28_rel",
    "path_eff4_rel", "path_eff12_rel", "flip8", "prev_run_len",
    "prev4_run_mean", "prev4_short_rate", "di14_signed", "ema8_21_signed",
    "ltf_align_mean", "ltf_align_std", "direction_vote",
)

FEATURE_FAMILIES = {
    "FULL_21": tuple(K1_STOP_FEATURES),
    "R2_META_ONLY_6": R2_META,
    "CAUSAL_GEOMETRY_15": GEOMETRY,
    "COMPACT_HYBRID_12": (
        "r2_p_stop", "r2_p_shock", "r2_score", "stop_dist_atr",
        "fast_body_rng", "path_eff12_rel", "flip8", "prev_run_len",
        "prev4_short_rate", "ltf_align_mean", "ltf_align_std", "direction_vote",
    ),
    "COMPACT_GEOMETRY_10": (
        "stop_dist_atr", "fast_body_rng", "std_body_rng", "path_eff12_rel",
        "flip8", "prev_run_len", "prev4_run_mean", "prev4_short_rate",
        "ltf_align_mean", "direction_vote",
    ),
}


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", required=True, type=Path)
    parser.add_argument("--r2-model-json", required=True, type=Path)
    parser.add_argument("--r2-ledger", required=True, type=Path)
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
    reference = pd.read_csv(args.r2_ledger, parse_dates=["decision"])[["decision", "W"]]
    parity = frame[frame["year"].ge(2024)].merge(reference, on="decision", how="outer", indicator=True)
    both = parity["_merge"].eq("both")
    if not parity["_merge"].eq("both").all() or not np.allclose(
        parity.loc[both, "r2_W"], parity.loc[both, "W"]
    ):
        raise RuntimeError("R2 ledger parity failed")

    candidates = frame[(frame["year"].ge(2023)) & frame["r2_W"].gt(0.0)].copy()
    spec = ModelSpec("robust_logit", "decision", C=0.5)
    detail: list[dict[str, object]] = []
    units_by_family_year: dict[tuple[str, int], np.ndarray] = {}

    for year in (2024, 2025, 2026):
        boundary = pd.Timestamp(year=year, month=1, day=1)
        train = candidates[
            (candidates["decision"] < boundary)
            & (candidates["label_available_at"] < boundary)
        ].copy()
        test = candidates[candidates["year"].eq(year)].copy()
        all_test = frame[frame["year"].eq(year)].copy()
        positions = {decision: pos for pos, decision in enumerate(all_test["decision"])}

        for family, features in FEATURE_FAMILIES.items():
            head = Head(f"META_K1_STOP_{family}", "stop_hit", features, "K1")
            folds = meta_inner_folds(train, head)
            oof, probability, _, _ = selected_oof_and_test(
                candidates, train, test, head, spec, folds
            )
            prior = train["k"].eq(1) & oof.notna()
            threshold = float(np.quantile(oof.loc[prior], 0.975))
            test_k1 = test["k"].eq(1).to_numpy()
            veto = test_k1 & (probability >= threshold)
            candidate_units = test["r2_W"].to_numpy(dtype=float).copy()
            candidate_units[veto] = 0.0
            full_units = all_test["r2_W"].to_numpy(dtype=float).copy()
            for decision, units in zip(test["decision"], candidate_units):
                full_units[positions[decision]] = units
            units_by_family_year[(family, year)] = full_units
            model_metrics = safe_metrics(
                test.loc[test_k1, "stop_hit"], probability[test_k1]
            )
            economics = policy_metrics(all_test, full_units, family, str(year))
            detail.append(
                {
                    "outer_year": year,
                    "feature_family": family,
                    "feature_count": len(features),
                    "features": "|".join(features),
                    "prior_oof_n": int(prior.sum()),
                    "q0975": threshold,
                    "vetoed": int(veto.sum()),
                    **{f"model_{key}": value for key, value in model_metrics.items()},
                    **{f"policy_{key}": value for key, value in economics.items() if key not in {"year", "policy"}},
                }
            )

    full = frame[frame["year"].between(2024, 2026)].copy()
    pooled: list[dict[str, object]] = [
        policy_metrics(
            full,
            full["r2_W"].to_numpy(dtype=float),
            "R2_DEFAULT",
            "POOLED_2024_2026",
        )
    ]
    for family in FEATURE_FAMILIES:
        units = np.concatenate(
            [units_by_family_year[(family, year)] for year in (2024, 2025, 2026)]
        )
        pooled.append(policy_metrics(full, units, family, "POOLED_2024_2026"))

    pd.DataFrame(detail).to_csv(args.out_dir / "V10_R3_K1STOP_FEATURE_ABLATION_BY_YEAR.csv", index=False)
    pooled_frame = pd.DataFrame(pooled).sort_values("R", ascending=False)
    pooled_frame.to_csv(args.out_dir / "V10_R3_K1STOP_FEATURE_ABLATION_POOLED.csv", index=False)
    print(
        pooled_frame[
            ["policy", "entries", "units", "pnl", "pf", "R", "pf_R", "dd_R", "oracle_recall", "l6_positive_child_retention"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
