"""Audit fixed V10 MA-band coordinates on genuinely forward candidates.

No threshold or composite score is fitted.  Each predeclared coordinate is
reported independently with direction fixed by its semantic meaning.  Run
block bootstrap intervals describe sampling uncertainty only.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


FEATURE_ORIENTATION = {
    "h4_wma_oc2_n20_slope_atr": "higher_healthier",
    "h4_wma_oc2_n20_span_atr": "higher_healthier",
    "h1_wma_oc2_n20_edge_atr": "higher_healthier",
    "h1_wma_oc2_n20_span_atr": "higher_healthier",
    "m15_sma_close_n60_support": "higher_healthier",
    "m15_sma_close_n60_order": "higher_healthier",
    "m15_sma_close_n60_deterioration4h": "higher_riskier",
    "m15_sma_oc2_n60_support": "higher_healthier",
    "m15_sma_oc2_n60_order": "higher_healthier",
    "m15_sma_oc2_n60_deterioration4h": "higher_riskier",
    "m15_wma_oc2_n60_support": "higher_healthier",
    "m15_wma_oc2_n60_order": "higher_healthier",
    "m15_wma_oc2_n60_deterioration4h": "higher_riskier",
}


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--bootstrap-draws", type=int, default=5000)
    return parser.parse_args()


def risk_score(frame: pd.DataFrame, feature: str) -> pd.Series:
    values = pd.to_numeric(frame[feature], errors="coerce")
    return -values if FEATURE_ORIENTATION[feature] == "higher_healthier" else values


def safe_auc(target: pd.Series, score: pd.Series) -> float:
    valid = target.notna() & score.notna() & np.isfinite(score)
    if valid.sum() == 0 or target[valid].nunique() < 2:
        return float("nan")
    return float(roc_auc_score(target[valid].astype(int), score[valid]))


def run_block_auc(
    frame: pd.DataFrame, feature: str, draws: int, rng: np.random.Generator
) -> tuple[float, float, float, int]:
    runs = np.asarray(sorted(frame["rid"].dropna().unique()))
    blocks = []
    for run_id in runs:
        block = frame[frame["rid"] == run_id]
        blocks.append(
            (
                block["stop_hit"].to_numpy(dtype=int),
                risk_score(block, feature).to_numpy(dtype=float),
            )
        )
    values: list[float] = []
    for _ in range(draws):
        selected = rng.integers(0, len(blocks), size=len(blocks))
        target = np.concatenate([blocks[index][0] for index in selected])
        score = np.concatenate([blocks[index][1] for index in selected])
        valid = np.isfinite(score)
        if valid.sum() and np.unique(target[valid]).size == 2:
            values.append(float(roc_auc_score(target[valid], score[valid])))
    if not values:
        return float("nan"), float("nan"), float("nan"), 0
    array = np.asarray(values)
    return (
        float(np.quantile(array, 0.025)),
        float(np.quantile(array, 0.5)),
        float(np.quantile(array, 0.975)),
        len(values),
    )


def max_stop_streak(values: pd.Series) -> int:
    best = current = 0
    for value in values.fillna(0).astype(bool):
        current = current + 1 if value else 0
        best = max(best, current)
    return best


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(
        args.ledger,
        parse_dates=["decision", "exit_time", "run_end_decision", "label_available_at"],
    )
    resolved = frame[frame["outcome_available"].astype(str).str.lower() == "true"].copy()
    resolved["stop_hit"] = pd.to_numeric(resolved["stop_hit"], errors="coerce")
    if resolved["stop_hit"].nunique() < 2:
        raise ValueError("forward ledger does not contain both stopped and non-stopped outcomes")

    rng = np.random.default_rng(20260921)
    rows: list[dict[str, object]] = []
    for feature, orientation in FEATURE_ORIENTATION.items():
        score = risk_score(resolved, feature)
        stopped = resolved.loc[resolved["stop_hit"] == 1, feature]
        survived = resolved.loc[resolved["stop_hit"] == 0, feature]
        q025, q50, q975, valid_draws = run_block_auc(
            resolved, feature, args.bootstrap_draws, rng
        )
        rows.append(
            {
                "feature": feature,
                "orientation": orientation,
                "rows": int(len(resolved)),
                "stops": int((resolved["stop_hit"] == 1).sum()),
                "auc_stop_risk": safe_auc(resolved["stop_hit"], score),
                "stopped_median": float(pd.to_numeric(stopped, errors="coerce").median()),
                "nonstop_median": float(pd.to_numeric(survived, errors="coerce").median()),
                "bootstrap_q025_auc": q025,
                "bootstrap_q50_auc": q50,
                "bootstrap_q975_auc": q975,
                "bootstrap_valid_draws": valid_draws,
            }
        )
    summary = pd.DataFrame(rows).sort_values("auc_stop_risk", ascending=False)
    summary_path = args.out_dir / "V10_MA_BAND_FORWARD_FEATURE_AUDIT.csv"
    summary.to_csv(summary_path, index=False)

    concentration = (
        resolved.groupby(["dir", "k"], dropna=False)
        .agg(candidates=("decision", "size"), stops=("stop_hit", "sum"), mean_R=("R", "mean"))
        .reset_index()
    )
    concentration["stop_rate"] = concentration["stops"] / concentration["candidates"]
    concentration_path = args.out_dir / "V10_MA_BAND_FORWARD_CONCENTRATION.csv"
    concentration.to_csv(concentration_path, index=False)

    audit = {
        "ok": True,
        "authority": "FORWARD DESCRIPTIVE EVIDENCE / NO THRESHOLD OR TRADE AUTHORITY",
        "ledger": str(args.ledger.resolve()),
        "candidates": int(len(frame)),
        "resolved_candidates": int(len(resolved)),
        "runs": int(resolved["rid"].nunique()),
        "hard_stops": int((resolved["stop_hit"] == 1).sum()),
        "hard_stop_rate": float(resolved["stop_hit"].mean()),
        "max_hard_stop_streak": max_stop_streak(
            resolved.sort_values("decision")["stop_hit"]
        ),
        "feature_count": len(FEATURE_ORIENTATION),
        "threshold_scan": False,
        "composite_score": False,
        "bootstrap_unit": "FAST run id",
        "bootstrap_draws": args.bootstrap_draws,
        "feature_audit": str(summary_path.resolve()),
        "concentration": str(concentration_path.resolve()),
    }
    audit_path = args.out_dir / "V10_MA_BAND_FORWARD_ANALYSIS_AUDIT.json"
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
