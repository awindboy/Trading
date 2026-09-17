"""Selection-conditioned V10 R3 meta-danger experiment.

The R2 RUNWAY_PERSIST + conditional-NEUTRAL policy remains the immutable
candidate generator.  This script asks a narrower question: among candidates
already selected causally by R2, can a model identify only an extreme future
loss tail without deleting the profitable right tail?

All model selection is chronological and all veto references are quantiles of
prior-only calibrated out-of-fold scores.  The scan is consumed-data research,
not threshold or strategy authority.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from tune_v10_r3_models import (
    Head,
    ModelSpec,
    evaluate_spec,
    inner_folds,
    policy_metrics,
    population_mask,
    right_tail_rows,
    safe_metrics,
    selected_oof_and_test,
    sha256_file,
)


R2_FEATURES = [
    "k", "stop_dist_atr", "fast_body_rng", "std_align", "std_body_rng",
    "slow_align", "adx28_rel", "di14_signed", "ema8_21_signed",
    "path_eff4_rel", "path_eff12_rel", "flip8",
]
for _tf in ("m15", "m30", "h1"):
    R2_FEATURES.extend(
        [f"{_tf}_{name}" for name in ("aligned", "streak", "body_sum_atr", "body_rng", "opp_wick")]
    )

META_FEATURES = (
    "r2_p_runway",
    "r2_p_persist",
    "r2_p_severe",
    "r2_p_stop",
    "r2_p_shock",
    "r2_score",
    "r2_W",
    "k",
    "stop_dist_atr",
    "fast_body_rng",
    "std_body_rng",
    "adx28_rel",
    "path_eff4_rel",
    "path_eff12_rel",
    "flip8",
    "prev_run_len",
    "prev4_short_rate",
    "di14_signed",
    "ema8_21_signed",
    "ltf_align_mean",
    "ltf_align_std",
    "direction_vote",
)

K1_STOP_FEATURES = (
    "r2_p_runway",
    "r2_p_severe",
    "r2_p_stop",
    "r2_p_shock",
    "r2_score",
    "r2_W",
    "stop_dist_atr",
    "fast_body_rng",
    "std_body_rng",
    "adx28_rel",
    "path_eff4_rel",
    "path_eff12_rel",
    "flip8",
    "prev_run_len",
    "prev4_run_mean",
    "prev4_short_rate",
    "di14_signed",
    "ema8_21_signed",
    "ltf_align_mean",
    "ltf_align_std",
    "direction_vote",
)


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", required=True, type=Path)
    parser.add_argument("--r2-model-json", required=True, type=Path)
    parser.add_argument("--r2-ledger", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def manual_predict(spec: dict[str, object], frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    values = frame[features].to_numpy(dtype=float)
    mean = np.asarray(spec["mean"], dtype=float)
    scale = np.asarray(spec["scale"], dtype=float)
    scale = np.where(np.abs(scale) < 1e-12, 1.0, scale)
    coef = np.asarray(spec["coef"], dtype=float)
    z = float(spec["intercept"]) + ((values - mean) / scale) @ coef
    z = np.clip(z, -35.0, 35.0)
    return 1.0 / (1.0 + np.exp(-z))


def reconstruct_r2_policy(frame: pd.DataFrame, model_path: Path) -> pd.DataFrame:
    model = json.loads(model_path.read_text(encoding="utf-8"))
    if model["features"] != R2_FEATURES:
        raise ValueError("R2 feature contract differs from expected order")
    result = frame.copy()
    for name in ("RUNWAY", "PERSIST", "SEVERE", "STOP", "SHOCK"):
        result[f"r2_p_{name.lower()}"] = np.nan
    result["r2_score"] = np.nan
    result["r2_W"] = 0.0
    result["r2_chop"] = (
        (result["adx28_rel"] < 1.0) & (result["path_eff4_rel"] < 1.0)
    ).astype(int)
    result["r2_confirm"] = (
        (result["di14_signed"] > 0.0) | (result["ema8_21_signed"] > 0.0)
    ).astype(int)

    for year in (2023, 2024, 2025, 2026):
        mask = result["year"].eq(year)
        if not mask.any():
            continue
        era = model["eras"][str(year)]
        subset = result.loc[mask]
        for name in ("RUNWAY", "PERSIST", "SEVERE", "STOP", "SHOCK"):
            result.loc[mask, f"r2_p_{name.lower()}"] = manual_predict(
                era[name], subset, R2_FEATURES
            )
        k = result.loc[mask, "k"].to_numpy(dtype=int)
        runway = result.loc[mask, "r2_p_runway"].to_numpy(dtype=float)
        persist = result.loc[mask, "r2_p_persist"].to_numpy(dtype=float)
        score = runway * np.where(k >= 2, persist, 1.0)
        result.loc[mask, "r2_score"] = score
        q50 = float(era["THRESHOLDS"]["RUNWAY_PERSIST"]["q50"])
        q75 = float(era["THRESHOLDS"]["RUNWAY_PERSIST"]["q75"])
        tier = np.where(score < q50, 0.0, np.where(score < q75, 1.0, 3.0))
        shock = result.loc[mask, "r2_p_shock"].to_numpy(dtype=float)
        tier[(k == 1) & (shock >= float(era["THRESHOLDS"]["shock_q95"]))] = 0.0
        result.loc[mask, "r2_W_pre_regime"] = tier

    # The committed R2 policy ledger applies the conditional-NEUTRAL gate to
    # every Child row.  The current EA latches admission for the rest of a FAST
    # run, which differs on six 2024-2026 rows; this experiment follows the
    # persisted research ledger and records that EA parity issue separately.
    usable = result["year"].ge(2023) & (
        result["r2_chop"].eq(0) | result["r2_confirm"].eq(1)
    )
    result.loc[usable, "r2_W"] = result.loc[usable, "r2_W_pre_regime"].fillna(0.0)
    return result


def meta_specs() -> list[ModelSpec]:
    specs: list[ModelSpec] = []
    for weight in ("decision", "run_sqrt"):
        for c_value in (0.02, 0.1, 0.5):
            specs.append(ModelSpec("robust_logit", weight, C=c_value))
        for c_value in (0.02, 0.1):
            specs.append(ModelSpec("spline_logit", weight, C=c_value, n_knots=3))
        specs.extend(
            [
                ModelSpec(
                    "histgb", weight, learning_rate=0.03, max_iter=180,
                    max_leaf_nodes=7, min_samples_leaf=45, l2_regularization=3.0,
                ),
                ModelSpec(
                    "histgb", weight, learning_rate=0.03, max_iter=220,
                    max_leaf_nodes=11, min_samples_leaf=75, l2_regularization=6.0,
                ),
            ]
        )
    return specs


def meta_inner_folds(
    frame: pd.DataFrame, head: Head, max_folds: int = 6
) -> list[tuple[pd.Index, pd.Index, str]]:
    """Expanding quarterly folds for the smaller selected-candidate cohort."""
    start = frame["decision"].min().to_period("Q").start_time
    end = frame["decision"].max()
    boundaries = list(pd.date_range(start=start, end=end, freq="QS"))
    mask_head = population_mask(frame, head)
    folds: list[tuple[pd.Index, pd.Index, str]] = []
    for pos in range(1, len(boundaries)):
        valid_start = boundaries[pos]
        valid_end = boundaries[pos + 1] if pos + 1 < len(boundaries) else end + pd.Timedelta(seconds=1)
        train_idx = frame.index[
            (frame["decision"] < valid_start)
            & (frame["label_available_at"] < valid_start)
            & mask_head
        ]
        valid_idx = frame.index[
            (frame["decision"] >= valid_start)
            & (frame["decision"] < valid_end)
            & mask_head
        ]
        if len(train_idx) < 70 or len(valid_idx) < 25:
            continue
        if frame.loc[train_idx, head.target].nunique() < 2 or frame.loc[valid_idx, head.target].nunique() < 2:
            continue
        folds.append((train_idx, valid_idx, str(valid_start.to_period("Q"))))
    return folds[-max_folds:]


def stage_mask(frame: pd.DataFrame, stage: str) -> np.ndarray:
    k = frame["k"].to_numpy(dtype=int)
    if stage == "K1":
        return k == 1
    if stage == "K2":
        return k == 2
    if stage == "K3PLUS":
        return k >= 3
    if stage == "K1_K2":
        return k <= 2
    return np.ones(len(frame), dtype=bool)


def danger_score(kind: str, p_stop: np.ndarray, p_negative: np.ndarray) -> np.ndarray:
    if kind == "STOP":
        return p_stop
    if kind == "NEGATIVE":
        return p_negative
    if kind == "GEOMETRIC":
        return np.sqrt(np.clip(p_stop * p_negative, 0.0, 1.0))
    if kind == "UNION":
        return 1.0 - (1.0 - p_stop) * (1.0 - p_negative)
    raise ValueError(kind)


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(
        args.universe,
        parse_dates=["decision", "entry_time", "exit_time", "run_end_decision", "label_available_at"],
    ).sort_values("decision").reset_index(drop=True)
    frame["negative_R"] = (frame["R"] < 0.0).astype(int)
    frame = reconstruct_r2_policy(frame, args.r2_model_json)

    reference = pd.read_csv(args.r2_ledger, parse_dates=["decision"])[["decision", "W"]]
    parity = frame[frame["year"].ge(2024)].merge(reference, on="decision", how="outer", indicator=True)
    parity_mismatches = int(
        (parity["_merge"] != "both").sum()
        + (parity.loc[parity["_merge"] == "both", "r2_W"].to_numpy() != parity.loc[parity["_merge"] == "both", "W"].to_numpy()).sum()
    )
    if parity_mismatches:
        raise RuntimeError(f"R2 policy reconstruction mismatches: {parity_mismatches}")

    candidates = frame[(frame["year"].ge(2023)) & (frame["r2_W"] > 0.0)].copy().reset_index(drop=True)
    heads = [
        Head("META_STOP", "stop_hit", META_FEATURES, "UNAMBIGUOUS"),
        Head("META_NEGATIVE", "negative_R", META_FEATURES, "UNAMBIGUOUS"),
        Head("META_K1_STOP", "stop_hit", K1_STOP_FEATURES, "K1"),
    ]
    selection_rows: list[dict[str, object]] = []
    head_rows: list[dict[str, object]] = []
    scan_rows: list[dict[str, object]] = []
    tail_rows: list[dict[str, object]] = []
    score_rows: list[pd.DataFrame] = []
    bundle: dict[str, object] = {"source_sha256": sha256_file(args.universe), "years": {}}

    for outer_year in (2024, 2025, 2026):
        boundary = pd.Timestamp(year=outer_year, month=1, day=1)
        train = candidates[
            (candidates["decision"] < boundary)
            & (candidates["label_available_at"] < boundary)
        ].copy()
        test = candidates[candidates["year"].eq(outer_year)].copy()
        all_test = frame[frame["year"].eq(outer_year)].copy()
        bundle["years"][str(outer_year)] = {}
        oof: dict[str, pd.Series] = {}
        test_prob: dict[str, np.ndarray] = {}
        for head in heads:
            folds = meta_inner_folds(train, head)
            if len(folds) < 2:
                raise RuntimeError(f"not enough folds for {outer_year} {head.name}")
            summaries: list[dict[str, object]] = []
            for spec in meta_specs():
                aggregate, _ = evaluate_spec(candidates, head, spec, folds)
                aggregate["outer_year"] = outer_year
                summaries.append(aggregate)
            winner = sorted(summaries, key=lambda x: (x["logloss"], x["brier"], -x["auc"]))[0]
            for row in summaries:
                row["selected"] = int(row["spec_id"] == winner["spec_id"])
                selection_rows.append(row)
            spec = next(item for item in meta_specs() if item.spec_id == winner["spec_id"])
            oof_score, test_score, final_model, platt = selected_oof_and_test(
                candidates, train, test, head, spec, folds
            )
            oof[head.name] = oof_score
            test_prob[head.name] = test_score
            pop = population_mask(test, head).to_numpy()
            metrics = safe_metrics(test.loc[pop, head.target], test_score[pop])
            head_rows.append(
                {
                    "outer_year": outer_year,
                    "head": head.name,
                    "train_n": int(population_mask(train, head).sum()),
                    "test_n": int(pop.sum()),
                    "selected_spec": spec.spec_id,
                    "platt_slope": platt.slope,
                    "platt_intercept": platt.intercept,
                    **metrics,
                }
            )
            bundle["years"][str(outer_year)][head.name] = {
                "features": list(head.features),
                "spec": asdict(spec),
                "platt": asdict(platt),
                "model": final_model,
            }

        common = train.index
        for values in oof.values():
            common = common.intersection(values.index[values.notna()])
        prior = train.loc[common].copy()
        prior_stop = oof["META_STOP"].loc[common].to_numpy(dtype=float)
        prior_negative = oof["META_NEGATIVE"].loc[common].to_numpy(dtype=float)
        prior_k1_stop = oof["META_K1_STOP"].loc[common].to_numpy(dtype=float)
        test_stop = test_prob["META_STOP"]
        test_negative = test_prob["META_NEGATIVE"]
        test_k1_stop = test_prob["META_K1_STOP"]

        score = test[
            ["signal_id", "decision", "year", "dir", "rid", "k", "L", "early3", "r2_W", "pnl", "R"]
        ].copy()
        score["meta_p_stop"] = test_stop
        score["meta_p_negative"] = test_negative
        score["meta_p_k1_stop"] = test_k1_stop

        policies: dict[str, np.ndarray] = {"R2_DEFAULT": all_test["r2_W"].to_numpy(dtype=float)}
        for kind in ("STOP", "NEGATIVE", "GEOMETRIC", "UNION", "K1STOP"):
            if kind == "K1STOP":
                prior_score = prior_k1_stop
                current_score = test_k1_stop
            else:
                prior_score = danger_score(kind, prior_stop, prior_negative)
                current_score = danger_score(kind, test_stop, test_negative)
            score[f"danger_{kind.lower()}"] = current_score
            stages = ("K1",) if kind == "K1STOP" else ("K1", "K2", "K3PLUS", "K1_K2", "ALL")
            for stage in stages:
                prior_stage = stage_mask(prior, stage)
                current_stage = stage_mask(test, stage)
                if prior_stage.sum() < 40:
                    continue
                for quantile in (0.90, 0.95, 0.975):
                    threshold = float(np.quantile(prior_score[prior_stage], quantile))
                    keep = ~((current_score >= threshold) & current_stage)
                    candidate_units = test["r2_W"].to_numpy(dtype=float) * keep.astype(float)
                    full_units = all_test["r2_W"].to_numpy(dtype=float).copy()
                    position = {decision: i for i, decision in enumerate(all_test["decision"])}
                    for decision, units in zip(test["decision"], candidate_units):
                        full_units[position[decision]] = units
                    name = f"META_{kind}_{stage}_Q{str(quantile).replace('.', '')}"
                    policies[name] = full_units
                    scan_rows.append(
                        {
                            "outer_year": outer_year,
                            "kind": kind,
                            "stage": stage,
                            "quantile": quantile,
                            "prior_threshold": threshold,
                            "prior_oof_n": int(prior_stage.sum()),
                            "test_candidates": len(test),
                            "vetoed": int(((current_score >= threshold) & current_stage).sum()),
                        }
                    )
        for name, units in policies.items():
            scan_rows.append(policy_metrics(all_test, units, name, str(outer_year)))
            tail_rows.extend(right_tail_rows(all_test, units, name, str(outer_year)))
        score_rows.append(score)

    scores = pd.concat(score_rows, ignore_index=True).sort_values("decision")
    policies_by_year = pd.DataFrame([x for x in scan_rows if "policy" in x])
    for policy in policies_by_year["policy"].unique():
        full = frame[frame["year"].between(2024, 2026)].copy()
        units = full["r2_W"].to_numpy(dtype=float).copy()
        for year in (2024, 2025, 2026):
            yearly_metrics = policies_by_year[
                (policies_by_year["year"].astype(str) == str(year))
                & (policies_by_year["policy"] == policy)
            ]
            if yearly_metrics.empty:
                continue
            if policy == "R2_DEFAULT":
                continue
            spec = policy.split("_")
            kind = spec[1]
            if kind not in {"STOP", "NEGATIVE", "GEOMETRIC", "UNION", "K1STOP"}:
                continue
            # Reconstruct pooled units from persisted per-year score/threshold rows.
            scan = pd.DataFrame([x for x in scan_rows if "kind" in x])
            stage = spec[2] if spec[2] != "K1" or spec[3].startswith("Q") else "K1_K2"
            q_token = spec[-1]
            quantile = {"Q09": 0.90, "Q095": 0.95, "Q0975": 0.975}.get(q_token)
            if quantile is None:
                continue
            match = scan[
                (scan["outer_year"] == year)
                & (scan["kind"] == kind)
                & (scan["stage"] == stage)
                & np.isclose(scan["quantile"], quantile)
            ]
            if match.empty:
                continue
            threshold = float(match.iloc[0]["prior_threshold"])
            year_mask = full["year"].eq(year)
            candidate_mask = year_mask & full["r2_W"].gt(0)
            yearly_scores = scores[scores["year"].eq(year)].set_index("decision")
            danger_col = f"danger_{kind.lower()}"
            current_score = full.loc[candidate_mask, "decision"].map(yearly_scores[danger_col]).to_numpy(dtype=float)
            stage_values = stage_mask(full.loc[candidate_mask], stage)
            veto = (current_score >= threshold) & stage_values
            candidate_positions = np.flatnonzero(candidate_mask.to_numpy())
            units[candidate_positions[veto]] = 0.0
        scan_rows.append(policy_metrics(full, units, policy, "POOLED_2024_2026"))
        tail_rows.extend(right_tail_rows(full, units, policy, "POOLED_2024_2026"))
    full = frame[frame["year"].between(2024, 2026)].copy()
    scan_rows.append(
        policy_metrics(full, full["r2_W"].to_numpy(dtype=float), "R2_DEFAULT", "POOLED_2024_2026")
    )
    tail_rows.extend(
        right_tail_rows(full, full["r2_W"].to_numpy(dtype=float), "R2_DEFAULT", "POOLED_2024_2026")
    )

    pd.DataFrame(selection_rows).to_csv(args.out_dir / "V10_R3_META_MODEL_SELECTION.csv", index=False)
    pd.DataFrame(head_rows).to_csv(args.out_dir / "V10_R3_META_HEAD_METRICS.csv", index=False)
    pd.DataFrame([x for x in scan_rows if "kind" in x]).to_csv(
        args.out_dir / "V10_R3_META_VETO_REFERENCES.csv", index=False
    )
    policy_summary = pd.DataFrame([x for x in scan_rows if "policy" in x])
    policy_summary.to_csv(args.out_dir / "V10_R3_META_POLICY_SUMMARY.csv", index=False)
    pd.DataFrame(tail_rows).to_csv(args.out_dir / "V10_R3_META_RIGHT_TAIL.csv", index=False)
    scores.to_csv(args.out_dir / "V10_R3_META_SCORE_LEDGER.csv", index=False)
    joblib.dump(bundle, args.out_dir / "V10_R3_META_MODEL_BUNDLE.joblib")

    validation = {
        "ok": True,
        "r2_policy_parity_mismatches": parity_mismatches,
        "universe_sha256": sha256_file(args.universe),
        "r2_model_sha256": sha256_file(args.r2_model_json),
        "r2_ledger_sha256": sha256_file(args.r2_ledger),
        "candidate_rows": len(candidates),
        "authority": "CONSUMED-DATA SHADOW RESEARCH / NOT STRATEGY AUTHORITY",
        "veto_rule": "prior-only calibrated OOF score percentile; explicit kind/stage/quantile scan",
    }
    (args.out_dir / "V10_R3_META_VALIDATION.json").write_text(
        json.dumps(validation, indent=2), encoding="utf-8"
    )
    print(pd.DataFrame(head_rows).to_string(index=False))
    pooled = policy_summary[policy_summary["year"].astype(str) == "POOLED_2024_2026"]
    if len(pooled):
        print("\nTOP POOLED BY R")
        print(
            pooled.sort_values("R", ascending=False)
            [["policy", "entries", "units", "pnl", "pf", "R", "pf_R", "dd_R", "oracle_recall", "l6_positive_child_retention"]]
            .head(15)
            .to_string(index=False)
        )


if __name__ == "__main__":
    main()
