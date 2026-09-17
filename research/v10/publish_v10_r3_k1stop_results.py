"""Publish compact, auditable V10 R3 K1-STOP research receipts.

Large regenerated universes, per-event score ledgers, bootstrap draws, and
joblib models remain under ignored ``output/``.  This publisher extracts the
small evidence needed to audit the checkpoint and hashes both its source
artifacts and the code that generated them.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


STAMP = "20260917"


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def main() -> None:
    args = cli()
    src = args.source_root
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    paths = {
        "universe_manifest": src / "V10_R3_CAUSAL_M1_UNIVERSE_MANIFEST.json",
        "universe_parity": src / "V10_R3_R2_UNIVERSE_PARITY.json",
        "meta_heads": src / "meta_danger_k1" / "V10_R3_META_HEAD_METRICS.csv",
        "tuned_metrics": src / "k1stop_validation" / "V10_R3_K1STOP_Q0975_INDEPENDENT_METRICS.csv",
        "tuned_vetoed": src / "k1stop_validation" / "V10_R3_K1STOP_Q0975_VETOED_EVENTS.csv",
        "tuned_bootstrap": src / "k1stop_validation" / "V10_R3_K1STOP_Q0975_BOOTSTRAP_SUMMARY.csv",
        "tuned_validation": src / "k1stop_validation" / "V10_R3_K1STOP_Q0975_VALIDATION.json",
        "stable_metrics": src / "stable_union_validation" / "V10_R3_STABLE_UNION_INDEPENDENT_METRICS.csv",
        "stable_bootstrap": src / "stable_union_validation" / "V10_R3_STABLE_UNION_BOOTSTRAP_SUMMARY.csv",
        "stable_validation": src / "stable_union_validation" / "V10_R3_STABLE_UNION_VALIDATION.json",
        "feature_ablation_year": src / "k1stop_feature_ablation" / "V10_R3_K1STOP_FEATURE_ABLATION_BY_YEAR.csv",
        "feature_ablation_pooled": src / "k1stop_feature_ablation" / "V10_R3_K1STOP_FEATURE_ABLATION_POOLED.csv",
        "model_ablation": src / "k1stop_fixed_specs" / "V10_R3_K1STOP_FIXED_SPEC_POOLED.csv",
        "adaptive_objectives": src / "k1stop_fixed_specs" / "V10_R3_K1STOP_ADAPTIVE_OBJECTIVES.csv",
        "future_manifest": src / "k1stop_future_shadow" / "V10_R3_K1STOP_FUTURE_SHADOW_MANIFEST.json",
        "future_selection": src / "k1stop_future_shadow" / "V10_R3_K1STOP_FUTURE_MODEL_SELECTION.csv",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing publication sources: {missing}")

    write_json(out / f"V10_R3_CAUSAL_UNIVERSE_MANIFEST_{STAMP}.json", load_json(paths["universe_manifest"]))
    write_json(out / f"V10_R3_R2_UNIVERSE_PARITY_{STAMP}.json", load_json(paths["universe_parity"]))
    write_json(out / f"V10_R3_K1STOP_TUNED_VALIDATION_{STAMP}.json", load_json(paths["tuned_validation"]))
    write_json(out / f"V10_R3_K1STOP_STABLE_FRONTIER_VALIDATION_{STAMP}.json", load_json(paths["stable_validation"]))
    write_json(out / f"V10_R3_K1STOP_FUTURE_SHADOW_MANIFEST_{STAMP}.json", load_json(paths["future_manifest"]))

    pd.read_csv(paths["meta_heads"]).to_csv(
        out / f"V10_R3_K1STOP_HEAD_METRICS_{STAMP}.csv", index=False
    )
    tuned_metrics = pd.read_csv(paths["tuned_metrics"])
    tuned_metrics.to_csv(out / f"V10_R3_K1STOP_TUNED_INDEPENDENT_METRICS_{STAMP}.csv", index=False)
    pd.read_csv(paths["tuned_vetoed"]).to_csv(
        out / f"V10_R3_K1STOP_TUNED_VETOED_EVENTS_{STAMP}.csv", index=False
    )
    pd.read_csv(paths["tuned_bootstrap"]).to_csv(
        out / f"V10_R3_K1STOP_TUNED_BOOTSTRAP_SUMMARY_{STAMP}.csv", index=False
    )
    stable_metrics = pd.read_csv(paths["stable_metrics"])
    stable_metrics.to_csv(
        out / f"V10_R3_K1STOP_STABLE_FRONTIER_METRICS_{STAMP}.csv", index=False
    )
    pd.read_csv(paths["stable_bootstrap"]).to_csv(
        out / f"V10_R3_K1STOP_STABLE_FRONTIER_BOOTSTRAP_{STAMP}.csv", index=False
    )
    pd.read_csv(paths["feature_ablation_year"]).to_csv(
        out / f"V10_R3_K1STOP_FEATURE_ABLATION_BY_YEAR_{STAMP}.csv", index=False
    )
    pd.read_csv(paths["feature_ablation_pooled"]).to_csv(
        out / f"V10_R3_K1STOP_FEATURE_ABLATION_POOLED_{STAMP}.csv", index=False
    )
    pd.read_csv(paths["model_ablation"]).to_csv(
        out / f"V10_R3_K1STOP_MODEL_ABLATION_{STAMP}.csv", index=False
    )
    pd.read_csv(paths["adaptive_objectives"]).to_csv(
        out / f"V10_R3_K1STOP_ADAPTIVE_OBJECTIVES_{STAMP}.csv", index=False
    )
    pd.read_csv(paths["future_selection"]).to_csv(
        out / f"V10_R3_K1STOP_FUTURE_MODEL_SELECTION_{STAMP}.csv", index=False
    )

    tuned = tuned_metrics[
        tuned_metrics["period"].eq("POOLED_2024_2026")
        & tuned_metrics["outcome_convention"].eq("conservative_stop")
    ].copy()
    stable = stable_metrics[
        stable_metrics["period"].eq("POOLED_2024_2026")
        & stable_metrics["outcome_convention"].eq("conservative_stop")
    ].copy()
    tuned = tuned[tuned["policy"].eq("META_K1STOP_K1_Q0975")]
    frontier = pd.concat(
        [
            stable[stable["policy"].eq("R2_DEFAULT")],
            tuned,
            stable[stable["policy"].isin(["ROBUST_C05", "SHALLOW_HISTGB", "STABLE_INTERSECTION", "STABLE_UNION"])],
        ],
        ignore_index=True,
    )
    baseline = frontier[frontier["policy"].eq("R2_DEFAULT")].iloc[0]
    frontier["delta_pnl_vs_r2"] = frontier["pnl"] - baseline["pnl"]
    frontier["delta_R_vs_r2"] = frontier["R"] - baseline["R"]
    frontier["delta_dd_R_vs_r2"] = frontier["dd_R"] - baseline["dd_R"]
    frontier["delta_oracle_recall_vs_r2"] = frontier["oracle_recall"] - baseline["oracle_recall"]
    status = {
        "R2_DEFAULT": "frozen comparator research ledger",
        "META_K1STOP_K1_Q0975": "tuned consumed-data diagnostic; not future action member",
        "ROBUST_C05": "primary future shadow candidate; no trade authority",
        "SHALLOW_HISTGB": "diagnostic only; bootstrap lower bound crosses zero",
        "STABLE_INTERSECTION": "diagnostic only",
        "STABLE_UNION": "diagnostic only; realized DD gain but bootstrap lower bound crosses zero",
    }
    frontier["research_status"] = frontier["policy"].map(status)
    frontier.to_csv(out / f"V10_R3_K1STOP_POLICY_FRONTIER_{STAMP}.csv", index=False)

    script_names = [
        "build_v10_causal_m1_universe_r3.py",
        "tune_v10_r3_models.py",
        "probe_v10_r3_meta_danger.py",
        "validate_v10_r3_k1stop_candidate.py",
        "compare_v10_r3_k1stop_specs.py",
        "validate_v10_r3_stable_union.py",
        "ablate_v10_r3_k1stop_features.py",
        "train_v10_r3_k1stop_future_shadow.py",
        "publish_v10_r3_k1stop_results.py",
        "validate_v10_r3_publication.py",
        "requirements-v10-r3-ml.txt",
    ]
    script_root = Path(__file__).resolve().parent
    receipt_name = f"V10_R3_REPRODUCIBILITY_RECEIPT_{STAMP}.json"
    published = sorted(
        path for path in out.iterdir() if path.is_file() and path.name != receipt_name
    )
    receipt = {
        "ok": True,
        "authority": "CONSUMED-DATA SHADOW RESEARCH / NOT STRATEGY AUTHORITY",
        "source_artifact_sha256": {key: sha256(value) for key, value in paths.items()},
        "script_sha256": {name: sha256(script_root / name) for name in script_names},
        "published_sha256": {path.name: sha256(path) for path in published},
        "environment": {
            "numpy": "2.5.3",
            "pandas": "3.0.5",
            "scikit_learn": "1.9.1",
            "joblib": "1.6.0",
            "scipy": "1.18.1",
        },
        "primary_shadow_candidate": "ROBUST_C05",
        "promotion": "NONE",
        "independent_validation": "NONE; 2022-2026 are consumed development evidence",
    }
    write_json(out / receipt_name, receipt)
    print(json.dumps({"published": len(published) + 1, "out_dir": str(out)}, indent=2))


if __name__ == "__main__":
    main()
