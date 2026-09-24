#!/usr/bin/env python3
"""Build the frozen V12 Phase-1H compact competing-risk study."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_v12_phase0 import parse_cutoff
from build_v12_phase1d import load_market, write_csv, write_json
from v12_phase0_core import sha256_file
from v12_phase1g_core import Encoder, fit_ridge_logistic, predict_logistic, weighted_metrics
from v12_phase1h_core import (
    CONTRACT_VERSION,
    Gate,
    apply_quintile_thresholds,
    attach_ha_features,
    build_h4_ha_features,
    capital_summary,
    compact_path_derivatives,
    tilt_summary,
    train_quintile_thresholds,
)


PREFIX = "V12_PHASE1H_"
FOLDS = (
    ("F1", "2025-03-31T23:59:59", "2025-04-01T00:00:00", "2025-09-30T23:59:59"),
    ("F2", "2025-09-30T23:59:59", "2025-10-01T00:00:00", "2026-03-31T23:59:59"),
    ("F3", "2026-03-31T23:59:59", "2026-04-01T00:00:00", "2026-09-18T23:57:00"),
)
OUTCOMES = {
    "STOP_HIT": "stop_hit",
    "GE5R_RIGHT_TAIL": "right_tail_presence",
}


def safe_output(path: Path, replace: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(path)
        for child in path.iterdir():
            if not child.is_file() or not child.name.startswith(PREFIX):
                raise ValueError(f"refusing to replace unexpected output: {child}")
            child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def verify_hash(path: Path, expected: str, label: str) -> None:
    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(f"{label} hash mismatch: {observed} != {expected}")


def feature_specs(contract: dict) -> dict[str, tuple[list[str], list[str]]]:
    structure_num = list(contract["structure_numeric_fields"])
    structure_cat = list(contract["structure_categorical_fields"])
    clocks = list(contract["continuous_clock_fields"])
    path = [
        f"{family}_{suffix}"
        for family in contract["source_box_families"]
        for suffix in contract["compact_path_fields_per_family"]
    ]
    ha = list(contract["ha_ablation_fields"])
    wave = list(contract["wave_ablation_fields"])
    compact_num = structure_num + clocks + path
    return {
        "STRUCTURE_CONTROL": (structure_num, structure_cat),
        "CLOCK_CONTROL": (structure_num + clocks, structure_cat),
        "COMPACT_PATH": (compact_num, structure_cat),
        "COMPACT_PATH_PLUS_HA": (compact_num + ha, structure_cat),
        "COMPACT_PATH_PLUS_WAVE": (compact_num + wave, structure_cat),
        "COMPACT_PATH_PLUS_HA_WAVE": (compact_num + ha + wave, structure_cat),
    }


def prepare_population(path_context: Path, wave_path: Path, market: pd.DataFrame,
                       contract: dict) -> tuple[pd.DataFrame, dict]:
    children = pd.read_csv(path_context, low_memory=False)
    children = children.loc[children["event"] == "ENTRY"].copy()
    children["decision_time"] = pd.to_datetime(children["decision_time"])
    children = compact_path_derivatives(children, tuple(contract["source_box_families"]))
    children = attach_ha_features(children, build_h4_ha_features(market))

    wave = pd.read_csv(wave_path, low_memory=False)
    wave = wave.rename(columns={
        "outer_close_location_aligned": "wave_outer_close_location_aligned",
        "outer_ha_body_aligned_atr": "wave_fast_body_reference",
    })
    wave_fields = ["signal_id", "wave_fast_body_reference"] + list(contract["wave_ablation_fields"])
    if wave["signal_id"].duplicated().any():
        raise ValueError("wave ledger contains duplicate signal_id")
    children = children.merge(wave[wave_fields], on="signal_id", how="left", validate="one_to_one")
    missing_wave = int(children["wave_efficiency"].isna().sum())
    if missing_wave:
        raise ValueError(f"missing Wave rows for {missing_wave} entry children")
    parity = np.abs(
        pd.to_numeric(children["ha_fast_body_aligned_atr180"], errors="coerce")
        - pd.to_numeric(children["wave_fast_body_reference"], errors="coerce")
    )
    children["right_tail_presence"] = (
        pd.to_numeric(children["right_tail_ge_5R_units"], errors="coerce") > 0
    ).astype(int)
    children = children.sort_values(["decision_time", "signal_id"]).reset_index(drop=True)
    return children, {
        "entry_children": len(children),
        "wave_missing_rows": missing_wave,
        "ha_fast_wave_reference_max_abs_difference": float(parity.max()),
        "ha_fast_wave_reference_mean_abs_difference": float(parity.mean()),
    }


def fit_all(population: pd.DataFrame, specs: dict[str, tuple[list[str], list[str]]],
            ridges: list[float]) -> tuple[list[dict], pd.DataFrame, dict]:
    metrics: list[dict] = []
    prediction_parts: list[pd.DataFrame] = []
    threshold_records: list[dict] = []
    liquidity_thresholds: dict[tuple[str, str], np.ndarray] = {}
    work = population.copy()
    work["_time"] = pd.to_datetime(work["decision_time"])

    for fold, train_end, test_start, test_end in FOLDS:
        train = work.loc[work["_time"] <= train_end].sort_values(["_time", "signal_id"])
        test = work.loc[(work["_time"] >= test_start) & (work["_time"] <= test_end)].sort_values(["_time", "signal_id"])
        liquidity_cuts = np.quantile(
            pd.to_numeric(train["prior60_daily_range_median"], errors="coerce").dropna(), [1 / 3, 2 / 3]
        )
        for model, (numeric, categorical) in specs.items():
            source_count = len(numeric) + len(categorical)
            head_predictions: dict[str, tuple[np.ndarray, np.ndarray]] = {}
            for outcome, target in OUTCOMES.items():
                y_train = pd.to_numeric(train[target], errors="raise").to_numpy(int)
                y_test = pd.to_numeric(test[target], errors="raise").to_numpy(int)
                w_train = pd.to_numeric(train["funded_units"], errors="raise").to_numpy(float)
                w_test = pd.to_numeric(test["funded_units"], errors="raise").to_numpy(float)
                cut = max(50, int(len(train) * 0.8))
                inner_train, inner_valid = train.iloc[:cut], train.iloc[cut:]
                best_ridge, best_loss = None, float("inf")
                for ridge in ridges:
                    encoder = Encoder(numeric, categorical).fit(inner_train)
                    beta = fit_ridge_logistic(
                        encoder.transform(inner_train),
                        pd.to_numeric(inner_train[target]).to_numpy(int),
                        pd.to_numeric(inner_train["funded_units"]).to_numpy(float),
                        ridge,
                    )
                    probability = predict_logistic(encoder.transform(inner_valid), beta)
                    loss = weighted_metrics(
                        pd.to_numeric(inner_valid[target]).to_numpy(int), probability,
                        pd.to_numeric(inner_valid["funded_units"]).to_numpy(float),
                    )["logloss"]
                    if loss < best_loss:
                        best_ridge, best_loss = ridge, loss
                encoder = Encoder(numeric, categorical).fit(train)
                beta = fit_ridge_logistic(encoder.transform(train), y_train, w_train, float(best_ridge))
                train_probability = predict_logistic(encoder.transform(train), beta)
                test_probability = predict_logistic(encoder.transform(test), beta)
                head_predictions[outcome] = (train_probability, test_probability)
                score = weighted_metrics(y_test, test_probability, w_test)
                metrics.append({
                    "model": model,
                    "outcome": outcome,
                    "fold": fold,
                    "train_rows": len(train),
                    "test_rows": len(test),
                    "positive_rate": float(np.average(y_test, weights=w_test)),
                    "selected_lambda": best_ridge,
                    "inner_logloss": best_loss,
                    "numeric_features": len(numeric),
                    "categorical_features": len(categorical),
                    "source_field_count": source_count,
                    **score,
                })

            train_score = head_predictions["GE5R_RIGHT_TAIL"][0] - head_predictions["STOP_HIT"][0]
            test_score = head_predictions["GE5R_RIGHT_TAIL"][1] - head_predictions["STOP_HIT"][1]
            score_cuts = train_quintile_thresholds(train_score)
            bands = apply_quintile_thresholds(test_score, score_cuts)
            for number, cut_value in enumerate(score_cuts, 1):
                threshold_records.append({
                    "model": model, "fold": fold, "threshold_number": number,
                    "conviction_score_threshold": float(cut_value),
                    "source": "TRAIN_PREDICTION_ECDF",
                })
            local = test[[
                "signal_id", "decision_time", "direction", "prior60_daily_range_median",
                "funded_units", "stopped_loss_units", "combined_R_units", "right_tail_ge_5R_units",
                "stop_hit", "right_tail_presence",
            ]].copy()
            local.insert(0, "model", model)
            local.insert(1, "fold", fold)
            local["p_stop"] = head_predictions["STOP_HIT"][1]
            local["p_tail"] = head_predictions["GE5R_RIGHT_TAIL"][1]
            local["conviction_score"] = test_score
            local["conviction_band"] = bands
            local["band_threshold_source"] = "TRAIN_PREDICTION_ECDF"
            local["liquidity_tercile"] = np.searchsorted(
                liquidity_cuts,
                pd.to_numeric(local["prior60_daily_range_median"], errors="coerce").to_numpy(float),
                side="right",
            ) + 1
            prediction_parts.append(local)
            liquidity_thresholds[(model, fold)] = liquidity_cuts
    predictions = pd.concat(prediction_parts, ignore_index=True)
    diagnostics = {
        "band_thresholds": threshold_records,
        "liquidity_thresholds": [
            {"model": model, "fold": fold, "low_mid": float(values[0]), "mid_high": float(values[1]),
             "source": "TRAIN_PRIOR60_DAILY_RANGE_TERCILES"}
            for (model, fold), values in sorted(liquidity_thresholds.items())
        ],
    }
    return metrics, predictions, diagnostics


def summarize_capital(predictions: pd.DataFrame) -> tuple[list[dict], list[dict], list[dict]]:
    bands: list[dict] = []
    tilts: list[dict] = []
    stability: list[dict] = []
    for (model, fold), group in predictions.groupby(["model", "fold"], sort=True):
        base = capital_summary(group)
        bands.append({"model": model, "fold": fold, "segment": "ALL", **base})
        for band, cell in group.groupby("conviction_band"):
            bands.append({"model": model, "fold": fold, "segment": f"Q{int(band)}", **capital_summary(cell)})
        tilts.append({"model": model, "fold": fold, "allocation": "BASELINE", **base})
        tilts.append({"model": model, "fold": fold, "allocation": "SHADOW_TILT", **tilt_summary(group)})
        for direction, cell in group.groupby("direction"):
            stability.append({"model": model, "fold": fold, "dimension": "DIRECTION",
                              "level": direction, "segment": "ALL", **capital_summary(cell)})
            stability.append({"model": model, "fold": fold, "dimension": "DIRECTION",
                              "level": direction, "segment": "Q5",
                              **capital_summary(cell.loc[cell["conviction_band"] == 5])})
        for era, cell in group.groupby("liquidity_tercile"):
            stability.append({"model": model, "fold": fold, "dimension": "LIQUIDITY_TERCILE",
                              "level": f"T{int(era)}", "segment": "ALL", **capital_summary(cell)})
            stability.append({"model": model, "fold": fold, "dimension": "LIQUIDITY_TERCILE",
                              "level": f"T{int(era)}", "segment": "Q5",
                              **capital_summary(cell.loc[cell["conviction_band"] == 5])})

    for model, group in predictions.groupby("model", sort=True):
        base = capital_summary(group)
        bands.append({"model": model, "fold": "POOLED", "segment": "ALL", **base})
        for band, cell in group.groupby("conviction_band"):
            bands.append({"model": model, "fold": "POOLED", "segment": f"Q{int(band)}", **capital_summary(cell)})
        tilts.append({"model": model, "fold": "POOLED", "allocation": "BASELINE", **base})
        tilts.append({"model": model, "fold": "POOLED", "allocation": "SHADOW_TILT", **tilt_summary(group)})
        for direction, cell in group.groupby("direction"):
            stability.append({"model": model, "fold": "POOLED", "dimension": "DIRECTION",
                              "level": direction, "segment": "ALL", **capital_summary(cell)})
            stability.append({"model": model, "fold": "POOLED", "dimension": "DIRECTION",
                              "level": direction, "segment": "Q5",
                              **capital_summary(cell.loc[cell["conviction_band"] == 5])})
    return bands, tilts, stability


def model_capital_gates(model: str, bands: pd.DataFrame, tilts: pd.DataFrame,
                        stability: pd.DataFrame) -> list[Gate]:
    gates: list[Gate] = []
    fold_bands = bands.loc[(bands["model"] == model) & (bands["fold"] != "POOLED")]
    stop_ok, econ_ok, coverage_ok = [], [], []
    for fold in ("F1", "F2", "F3"):
        all_row = fold_bands.loc[(fold_bands["fold"] == fold) & (fold_bands["segment"] == "ALL")].iloc[0]
        q5 = fold_bands.loc[(fold_bands["fold"] == fold) & (fold_bands["segment"] == "Q5")].iloc[0]
        stop_ok.append(q5["stopped_units_per_100"] < all_row["stopped_units_per_100"])
        econ_ok.append(q5["net_R_per_unit"] > 0 and q5["net_R_per_unit"] >= all_row["net_R_per_unit"])
        coverage_ok.append(q5["funded_units"] >= 0.10 * all_row["funded_units"])
    gates.extend([
        Gate("Q5_STOP_EVERY_FOLD", all(stop_ok), str(stop_ok)),
        Gate("Q5_ECONOMICS_EVERY_FOLD", all(econ_ok), str(econ_ok)),
        Gate("Q5_COVERAGE_EVERY_FOLD", all(coverage_ok), str(coverage_ok)),
    ])

    local_tilts = tilts.loc[tilts["model"] == model]
    stop_tilt, econ_tilt = [], []
    for fold in ("F1", "F2", "F3"):
        base = local_tilts.loc[(local_tilts["fold"] == fold) & (local_tilts["allocation"] == "BASELINE")].iloc[0]
        tilt = local_tilts.loc[(local_tilts["fold"] == fold) & (local_tilts["allocation"] == "SHADOW_TILT")].iloc[0]
        stop_tilt.append(tilt["stopped_units_per_100"] < base["stopped_units_per_100"])
        econ_tilt.append(tilt["net_R_per_unit"] >= 0.95 * base["net_R_per_unit"])
    pooled_base = local_tilts.loc[(local_tilts["fold"] == "POOLED") & (local_tilts["allocation"] == "BASELINE")].iloc[0]
    pooled_tilt = local_tilts.loc[(local_tilts["fold"] == "POOLED") & (local_tilts["allocation"] == "SHADOW_TILT")].iloc[0]
    pooled_econ = pooled_tilt["net_R_per_unit"] >= 0.95 * pooled_base["net_R_per_unit"]
    pooled_tail = pooled_tilt["right_tail_per_unit"] >= 0.90 * pooled_base["right_tail_per_unit"]
    gates.extend([
        Gate("TILT_STOP_EVERY_FOLD", all(stop_tilt), str(stop_tilt)),
        Gate("TILT_ECONOMICS", sum(econ_tilt) >= 2 and pooled_econ,
             f"folds={econ_tilt}; pooled={bool(pooled_econ)}"),
        Gate("TILT_TAIL_POOLED", bool(pooled_tail),
             f"ratio={pooled_tilt['right_tail_per_unit'] / pooled_base['right_tail_per_unit']:.6f}"),
    ])

    sides = stability.loc[(stability["model"] == model) & (stability["fold"] == "POOLED")
                          & (stability["dimension"] == "DIRECTION")]
    side_ok = []
    for level in ("LONG", "SHORT"):
        base = sides.loc[(sides["level"] == level) & (sides["segment"] == "ALL")].iloc[0]
        q5 = sides.loc[(sides["level"] == level) & (sides["segment"] == "Q5")].iloc[0]
        side_ok.append(q5["stopped_units_per_100"] < base["stopped_units_per_100"] and q5["net_R_per_unit"] > 0)
    gates.append(Gate("SIDE_STABILITY", all(side_ok), str(side_ok)))

    eras = stability.loc[(stability["model"] == model) & (stability["fold"] != "POOLED")
                         & (stability["dimension"] == "LIQUIDITY_TERCILE")]
    era_ok, checked = [], []
    for (fold, level), cell in eras.groupby(["fold", "level"]):
        base = cell.loc[cell["segment"] == "ALL"].iloc[0]
        q5 = cell.loc[cell["segment"] == "Q5"].iloc[0]
        if q5["funded_units"] >= 30:
            passed = q5["stopped_units_per_100"] < base["stopped_units_per_100"] and q5["net_R_per_unit"] > 0
            era_ok.append(passed)
            checked.append(f"{fold}:{level}={bool(passed)}")
    gates.append(Gate("LIQUIDITY_STABILITY", bool(era_ok) and all(era_ok), ";".join(checked)))
    return gates


def evaluate_gates(metrics_rows: list[dict], bands_rows: list[dict], tilts_rows: list[dict],
                   stability_rows: list[dict], specs: dict[str, tuple[list[str], list[str]]],
                   maximum_fields: int) -> list[dict]:
    metrics = pd.DataFrame(metrics_rows)
    bands, tilts, stability = map(pd.DataFrame, (bands_rows, tilts_rows, stability_rows))
    output: list[dict] = []
    capital_cache: dict[str, list[Gate]] = {}
    for model in specs:
        capital_cache[model] = model_capital_gates(model, bands, tilts, stability)

    compact = "COMPACT_PATH"
    gates = [Gate("COMPACTNESS", len(specs[compact][0]) + len(specs[compact][1]) <= maximum_fields,
                  f"fields={len(specs[compact][0]) + len(specs[compact][1])}")]
    for outcome in OUTCOMES:
        c = metrics.loc[(metrics["model"] == compact) & (metrics["outcome"] == outcome)].set_index("fold")
        b = metrics.loc[(metrics["model"] == "CLOCK_CONTROL") & (metrics["outcome"] == outcome)].set_index("fold")
        deltas = c["logloss"] - b["logloss"]
        passed = c["logloss"].mean() <= b["logloss"].mean() and int((deltas < 0).sum()) >= 2
        gates.append(Gate(f"HEAD_METRICS_{outcome}", bool(passed),
                          f"mean_delta={deltas.mean():.9f}; fold_deltas={deltas.to_dict()}"))
    gates.extend(capital_cache[compact])
    primary_pass = all(gate.passed for gate in gates)
    for gate in gates:
        output.append({"assessment": "PRIMARY", "model": compact, "gate": gate.gate,
                       "passed": gate.passed, "detail": gate.detail})
    output.append({"assessment": "PRIMARY", "model": compact, "gate": "OVERALL",
                   "passed": primary_pass, "detail": "all frozen primary gates"})

    for model in ("COMPACT_PATH_PLUS_HA", "COMPACT_PATH_PLUS_WAVE", "COMPACT_PATH_PLUS_HA_WAVE"):
        incremental: list[Gate] = []
        for outcome in OUTCOMES:
            a = metrics.loc[(metrics["model"] == model) & (metrics["outcome"] == outcome)].set_index("fold")
            c = metrics.loc[(metrics["model"] == compact) & (metrics["outcome"] == outcome)].set_index("fold")
            deltas = a["logloss"] - c["logloss"]
            passed = deltas.mean() < 0 and float(deltas.max()) <= 0.02
            incremental.append(Gate(f"INCREMENTAL_{outcome}", bool(passed),
                                    f"mean_delta={deltas.mean():.9f}; max_delta={deltas.max():.9f}"))
        incremental.extend(capital_cache[model])
        overall = all(gate.passed for gate in incremental)
        for gate in incremental:
            output.append({"assessment": "INCREMENTAL", "model": model, "gate": gate.gate,
                           "passed": gate.passed, "detail": gate.detail})
        output.append({"assessment": "INCREMENTAL", "model": model, "gate": "OVERALL",
                       "passed": overall, "detail": "both head and all capital gates"})
    return output


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=repo / "research/v12/v12_phase1h_contract.json")
    parser.add_argument("--phase1g", type=Path, default=repo / "output/v12_phase1g_continuous_intraday_path_20260924_a")
    parser.add_argument("--wave", type=Path, default=repo / "output/v11_wave_edge_20260922/V11_COMPLETED_WAVE_LEDGER.csv")
    parser.add_argument("--m1", type=Path, default=repo / "data/GOLD#/GOLD#_M1_202201030100_202609222358.csv")
    parser.add_argument("--output", type=Path, default=repo / "output/v12_phase1h_compact_conviction_head_20260924_a")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["contract_version"] != CONTRACT_VERSION:
        raise ValueError("contract/core version mismatch")
    safe_output(args.output, args.replace)

    phase1g_manifest = args.phase1g / "V12_PHASE1G_MANIFEST.json"
    path_context = args.phase1g / "V12_PHASE1G_V10_CHILD_PATH_CONTEXT.csv"
    hashes = contract["source_hashes"]
    verify_hash(phase1g_manifest, hashes["phase1g_manifest_sha256"], "Phase-1G manifest")
    verify_hash(args.wave, hashes["v11_completed_wave_ledger_sha256"], "Wave ledger")
    verify_hash(args.m1, hashes["raw_m1_full_sha256"], "raw M1")
    cutoff = parse_cutoff(contract["mechanism_cutoff"])
    market, audit = load_market(args.m1, cutoff)
    if audit.prefix_sha256 != hashes["raw_m1_prefix_sha256"]:
        raise ValueError("raw M1 prefix hash mismatch")

    population, source_diagnostics = prepare_population(path_context, args.wave, market, contract)
    specs = feature_specs(contract)
    required = sorted({field for numeric, categorical in specs.values() for field in numeric + categorical})
    missing = [field for field in required if field not in population.columns]
    if missing:
        raise ValueError(f"missing contracted fields: {missing}")
    feature_rows = [
        {"model": model, "feature": field, "kind": kind, "source_field_count": len(numeric) + len(categorical)}
        for model, (numeric, categorical) in specs.items()
        for kind, values in (("NUMERIC", numeric), ("CATEGORICAL", categorical))
        for field in values
    ]
    metrics, predictions, fit_diagnostics = fit_all(population, specs, list(contract["regularization_grid"]))
    bands, tilts, stability = summarize_capital(predictions)
    gates = evaluate_gates(metrics, bands, tilts, stability, specs, contract["maximum_primary_source_fields"])

    outputs = {
        "FEATURE_SCHEMA.csv": feature_rows,
        "MODEL_METRICS.csv": metrics,
        "PREDICTIONS.csv": predictions.to_dict("records"),
        "CAPITAL_BANDS.csv": bands,
        "SHADOW_TILT.csv": tilts,
        "STABILITY.csv": stability,
        "GATES.csv": gates,
    }
    paths: list[Path] = []
    for name, rows in outputs.items():
        path = args.output / f"{PREFIX}{name}"
        write_csv(path, rows)
        paths.append(path)
    diagnostics = {
        "contract_version": contract["contract_version"],
        "contract_sha256": sha256_file(args.contract),
        "cutoff": cutoff.isoformat(),
        "raw_m1_sha256": sha256_file(args.m1),
        "m1_prefix_rows": audit.parsed_price_rows,
        "m1_prefix_sha256": audit.prefix_sha256,
        "first_unrevealed_timestamp": audit.first_unrevealed_timestamp.isoformat() if audit.first_unrevealed_timestamp else None,
        "post_cutoff_price_rows_parsed": audit.post_cutoff_price_rows_parsed,
        "source": source_diagnostics,
        "feature_source_counts": {model: len(numeric) + len(categorical)
                                  for model, (numeric, categorical) in specs.items()},
        "model_metric_rows": len(metrics),
        "prediction_rows": len(predictions),
        "primary_overall_pass": next(row["passed"] for row in gates if row["assessment"] == "PRIMARY" and row["gate"] == "OVERALL"),
        "incremental_overall": {row["model"]: row["passed"] for row in gates
                                if row["assessment"] == "INCREMENTAL" and row["gate"] == "OVERALL"},
        **fit_diagnostics,
        "evidence_status": contract["evidence_status"],
        "trade_authority": False,
        "sizing_authority": False,
    }
    diagnostics_path = args.output / f"{PREFIX}DIAGNOSTICS.json"
    write_json(diagnostics_path, diagnostics)
    paths.append(diagnostics_path)
    manifest = {
        "contract_version": contract["contract_version"],
        "files": [{"name": path.name, "sha256": sha256_file(path), "bytes": path.stat().st_size}
                  for path in paths],
    }
    write_json(args.output / f"{PREFIX}MANIFEST.json", manifest)
    print(json.dumps(diagnostics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
