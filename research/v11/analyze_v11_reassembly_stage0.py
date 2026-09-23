"""Stage-0 audit for rebuilding V10 components into a V11 capital-timing design.

This is consumed-development evidence only.  It does not promote the fixed
60/120/180-minute probes.  The purpose is to test the user's revised economic
criterion on the frozen R7G-intended k1 population: participation retained,
Hard-SL burden, win rate, structural/weighted R, and descriptive risk capacity.

The script also inventories the retained V10 feature families and checks whether
the existing R5 P(STOP) and E[R|non-stop] outputs explain the relative value of
waiting to fund a Child.  They are kept separate instead of collapsed into EV.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


RISK_GRID = (0.0025, 0.005, 0.01, 0.02)
POLICIES = (
    ("IMMEDIATE", None, "R", "stop_hit"),
    ("WAIT_60M_ALL", "b60_valid", "b60_R", "b60_stop_hit"),
    ("WAIT_120M_ALL", "b120_valid", "b120_R", "b120_stop_hit"),
    ("WAIT_180M_ALL", "b180_valid", "b180_R", "b180_stop_hit"),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_event_decision(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values.astype(str).str.replace(".", "-", regex=False))


def equity_path(values: np.ndarray, risk_fraction: float) -> tuple[float, float]:
    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for value in values:
        equity *= max(1e-12, 1.0 + risk_fraction * float(value))
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, 1.0 - equity / peak)
    return float(equity), float(max_drawdown)


def equal_drawdown_risk(values: np.ndarray, target_drawdown: float) -> float:
    low = 0.0
    high = 0.10
    if equity_path(values, high)[1] < target_drawdown:
        return float("nan")
    for _ in range(100):
        middle = (low + high) / 2.0
        if equity_path(values, middle)[1] < target_drawdown:
            low = middle
        else:
            high = middle
    return float((low + high) / 2.0)


def max_stop_streak(values: pd.Series) -> int:
    best = 0
    current = 0
    for value in values.fillna(0).astype(int):
        current = current + 1 if value == 1 else 0
        best = max(best, current)
    return best


def policy_frame(population: pd.DataFrame, valid_column: str | None) -> pd.DataFrame:
    if valid_column is None:
        return population.copy()
    return population[population[valid_column].eq(1)].copy()


def policy_metrics(
    population: pd.DataFrame,
    policy: str,
    valid_column: str | None,
    r_column: str,
    stop_column: str,
    scope: str = "ALL",
    scope_value: str = "ALL",
) -> dict[str, object]:
    frame = policy_frame(population, valid_column).sort_values("decision_ts")
    r_values = pd.to_numeric(frame[r_column], errors="coerce")
    weights = pd.to_numeric(frame["r7g_weight"], errors="coerce")
    stops = pd.to_numeric(frame[stop_column], errors="coerce").fillna(0).astype(int)
    baseline_n = len(population)
    return {
        "scope": scope,
        "scope_value": scope_value,
        "policy": policy,
        "trades": int(len(frame)),
        "trade_retention": float(len(frame) / baseline_n) if baseline_n else math.nan,
        "hard_sl": int(stops.sum()),
        "hard_sl_rate": float(stops.mean()) if len(frame) else math.nan,
        "wins": int((r_values > 0).sum()),
        "win_rate": float((r_values > 0).mean()) if len(frame) else math.nan,
        "structural_R": float(r_values.sum()),
        "r7g_weighted_R": float((r_values * weights).sum()),
        "max_stop_streak": max_stop_streak(stops),
    }


def load_population(
    events_path: Path,
    episodes_path: Path,
    selected_audit_path: Path,
) -> tuple[pd.DataFrame, dict[str, int]]:
    events = pd.read_csv(events_path)
    episodes = pd.read_csv(episodes_path)
    selected_audit = pd.read_csv(selected_audit_path)

    events["decision_ts"] = normalize_event_decision(events["decision"])
    episodes["decision_ts"] = pd.to_datetime(episodes["decision"])
    merged = episodes.merge(
        events,
        on=["decision_ts", "k"],
        how="inner",
        suffixes=("_episode", "_event"),
        validate="one_to_one",
    )
    population = merged[
        merged["r7g_weight"].gt(0)
        & merged["event"].ne("SHADOW_WARMUP")
    ].copy()
    population = population.sort_values("decision_ts").reset_index(drop=True)

    selected_k1 = selected_audit[
        selected_audit["k"].eq(1) & selected_audit["selected_r7g"].eq(1)
    ].copy()
    selected_k1["decision_ts"] = pd.to_datetime(selected_k1["decision"])
    expected_keys = set(zip(selected_k1["decision_ts"], selected_k1["k"]))
    actual_keys = set(zip(population["decision_ts"], population["k"]))
    if expected_keys != actual_keys:
        raise RuntimeError(
            "R7G-intended k1 parity failed: "
            f"expected={len(expected_keys)} actual={len(actual_keys)} "
            f"missing={len(expected_keys - actual_keys)} extra={len(actual_keys - expected_keys)}"
        )
    parity = {
        "event_rows": int(len(events)),
        "episode_rows": int(len(episodes)),
        "merged_rows": int(len(merged)),
        "selected_r7g_k1_rows": int(len(population)),
        "selected_audit_rows": int(len(selected_k1)),
    }
    return population, parity


def build_policy_outputs(population: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    overall_rows: list[dict[str, object]] = []
    slice_rows: list[dict[str, object]] = []
    for policy, valid, r_col, stop_col in POLICIES:
        overall_rows.append(policy_metrics(population, policy, valid, r_col, stop_col))
        for year, group in population.groupby("year_episode", sort=True):
            slice_rows.append(
                policy_metrics(
                    group,
                    policy,
                    valid,
                    r_col,
                    stop_col,
                    scope="YEAR",
                    scope_value=str(int(year)),
                )
            )
        for direction, group in population.groupby("dir_episode", sort=True):
            slice_rows.append(
                policy_metrics(
                    group,
                    policy,
                    valid,
                    r_col,
                    stop_col,
                    scope="SIDE",
                    scope_value="LONG" if int(direction) > 0 else "SHORT",
                )
            )
    summary = pd.DataFrame(overall_rows)
    baseline = summary.loc[summary["policy"].eq("IMMEDIATE")].iloc[0]
    summary["trade_change"] = summary["trades"] - int(baseline["trades"])
    summary["hard_sl_change"] = summary["hard_sl"] - int(baseline["hard_sl"])
    summary["hard_sl_reduction"] = 1.0 - summary["hard_sl"] / float(baseline["hard_sl"])
    summary["win_rate_delta_pp"] = 100.0 * (
        summary["win_rate"] - float(baseline["win_rate"])
    )
    summary["structural_R_retention"] = (
        summary["structural_R"] / float(baseline["structural_R"])
    )
    summary["weighted_R_retention"] = (
        summary["r7g_weighted_R"] / float(baseline["r7g_weighted_R"])
    )
    return summary, pd.DataFrame(slice_rows)


def build_capacity_outputs(
    population: pd.DataFrame, summary: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    policy_values: dict[str, np.ndarray] = {}
    for policy, valid, r_col, _ in POLICIES:
        frame = policy_frame(population, valid).sort_values("decision_ts")
        values = (
            pd.to_numeric(frame[r_col], errors="coerce")
            * pd.to_numeric(frame["r7g_weight"], errors="coerce")
        ).to_numpy(dtype=float)
        policy_values[policy] = values
        for risk_fraction in RISK_GRID:
            ending_equity, max_drawdown = equity_path(values, risk_fraction)
            rows.append(
                {
                    "policy": policy,
                    "risk_fraction_per_unit": risk_fraction,
                    "trades": int(len(values)),
                    "ending_equity_multiple": ending_equity,
                    "max_drawdown": max_drawdown,
                }
            )

    baseline_values = policy_values["IMMEDIATE"]
    baseline_equity, baseline_drawdown = equity_path(baseline_values, 0.01)
    equal_rows: list[dict[str, object]] = []
    for policy, values in policy_values.items():
        matched_risk = equal_drawdown_risk(values, baseline_drawdown)
        if math.isnan(matched_risk):
            matched_equity = math.nan
            matched_drawdown = math.nan
        else:
            matched_equity, matched_drawdown = equity_path(values, matched_risk)
        equal_rows.append(
            {
                "policy": policy,
                "target_baseline_risk_fraction_per_unit": 0.01,
                "target_baseline_ending_equity_multiple": baseline_equity,
                "target_baseline_max_drawdown": baseline_drawdown,
                "equal_drawdown_risk_fraction_per_unit": matched_risk,
                "equal_drawdown_ending_equity_multiple": matched_equity,
                "equal_drawdown_observed": matched_drawdown,
                "weighted_R_retention": float(
                    summary.loc[
                        summary["policy"].eq(policy), "weighted_R_retention"
                    ].iloc[0]
                ),
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(equal_rows)


def build_r5_interaction(population: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = population.copy()
    frame["base_weighted_R"] = frame["R"] * frame["r7g_weight"]
    frame["wait180_weighted_R"] = np.where(
        frame["b180_valid"].eq(1),
        frame["b180_R"] * frame["r7g_weight"],
        0.0,
    )
    frame["wait180_delta_weighted_R"] = (
        frame["wait180_weighted_R"] - frame["base_weighted_R"]
    )
    frame["p_stop_half"] = pd.qcut(
        frame["p_stop"], 2, labels=["PSTOP_LOW", "PSTOP_HIGH"], duplicates="drop"
    )
    frame["mu_half"] = pd.qcut(
        frame["mu_nonstop"], 2, labels=["MU_LOW", "MU_HIGH"], duplicates="drop"
    )
    grouped = (
        frame.groupby(
            ["year_episode", "p_stop_half", "mu_half"], observed=True
        )
        .agg(
            rows=("signal_id", "size"),
            immediate_stop_rate=("stop_hit", "mean"),
            immediate_weighted_R=("base_weighted_R", "sum"),
            wait180_weighted_R=("wait180_weighted_R", "sum"),
            wait180_delta_weighted_R=("wait180_delta_weighted_R", "sum"),
        )
        .reset_index()
    )
    correlations = (
        frame[["p_stop", "mu_nonstop", "wait180_delta_weighted_R"]]
        .corr(method="spearman")
        .reset_index(names="coordinate")
    )
    return grouped, correlations


def feature_family(name: str) -> str:
    if name.startswith("rk_"):
        return "causal_prior_rank"
    if name.startswith("e_"):
        return "engineered_cross_scale"
    if name.startswith(("m15_", "m30_", "h1_")):
        return "lower_timeframe_summary"
    if name.startswith(("fast_", "std_", "slow_")):
        return "multi_ha_geometry"
    if name.startswith(("adx", "di", "ema")):
        return "trend_direction"
    if name.startswith(("path_eff", "flip")):
        return "path_churn"
    if name == "stop_dist_atr":
        return "child_risk_geometry"
    return "other"


def build_feature_inventory(registry_path: Path) -> pd.DataFrame:
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    rows = [{"feature": name, "family": feature_family(name)} for name in payload["features"]]
    return (
        pd.DataFrame(rows)
        .groupby("family", as_index=False)
        .agg(feature_count=("feature", "size"), features=("feature", "|".join))
        .sort_values(["feature_count", "family"], ascending=[False, True])
    )


def build_component_catalog() -> pd.DataFrame:
    rows = [
        ("verified raw M1", "causal execution truth", "keep", "touch ordering and HTF rebuild"),
        ("FAST H4 HA", "campaign and participation clock", "keep/reassign", "candidate creation and campaign shell"),
        ("STD H4 HA", "stop geometry and smoother observation", "keep/reassign", "interruption/restart coordinate, not whole base"),
        ("SLOW H4 HA", "deep HA context", "keep/reassign", "capital ceiling or parent persistence coordinate"),
        ("ATR180 normalization", "cross-era scale", "keep", "normalize every distance and rate"),
        ("M15/M30/H1 summaries", "multi-scale causal context", "keep as evidence", "funding-state inputs, no direction veto"),
        ("R4 selected-score heads", "0/1/3 participation", "decompose", "candidate eligibility separate from funding amount"),
        ("R5 STOP heads", "P(current Hard SL touch)", "keep separate", "capital-timing risk coordinate"),
        ("R5 conditional-R heads", "E[R | non-stop]", "keep separate", "survival value coordinate"),
        ("R5 scalar EV", "collapse STOP and conditional R", "demote", "audit only; do not erase two-axis state"),
        ("R7G feedback", "prior-exited 180-H4 sizing overlay", "keep/reassign", "maximum funding ceiling after readiness"),
        ("normalized MA state", "parent health instrumentation", "shadow", "context only; not Child safety"),
        ("Wave/M5 process", "intrabar settlement/process", "shadow", "funding transition evidence only if incremental"),
        ("liquidity event grammar", "NHA context semantics", "shadow", "interpret interruption; no broad veto"),
        ("Hard SL", "Child falsification", "keep", "freeze before any observation phase"),
        ("first opposite FAST HA", "campaign exit", "keep comparator", "exit clock independent of funding clock"),
    ]
    return pd.DataFrame(
        rows, columns=["component", "v10_role", "reassembly_status", "candidate_v11_role"]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--episodes", type=Path, required=True)
    parser.add_argument("--selected-audit", type=Path, required=True)
    parser.add_argument("--feature-registry", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    population, parity = load_population(args.events, args.episodes, args.selected_audit)
    summary, slices = build_policy_outputs(population)
    capacity, equal_drawdown = build_capacity_outputs(population, summary)
    r5_interaction, correlations = build_r5_interaction(population)
    feature_inventory = build_feature_inventory(args.feature_registry)
    components = build_component_catalog()

    outputs = {
        "policy_summary": args.out_dir / "V11_REASSEMBLY_STAGE0_POLICY_SUMMARY.csv",
        "policy_slices": args.out_dir / "V11_REASSEMBLY_STAGE0_POLICY_SLICES.csv",
        "capacity_grid": args.out_dir / "V11_REASSEMBLY_STAGE0_CAPACITY_GRID.csv",
        "equal_drawdown": args.out_dir / "V11_REASSEMBLY_STAGE0_EQUAL_DRAWDOWN.csv",
        "r5_interaction": args.out_dir / "V11_REASSEMBLY_STAGE0_R5_INTERACTION.csv",
        "r5_correlations": args.out_dir / "V11_REASSEMBLY_STAGE0_R5_CORRELATIONS.csv",
        "feature_inventory": args.out_dir / "V11_REASSEMBLY_STAGE0_FEATURE_FAMILIES.csv",
        "component_catalog": args.out_dir / "V11_REASSEMBLY_STAGE0_COMPONENT_CATALOG.csv",
    }
    frames = {
        "policy_summary": summary,
        "policy_slices": slices,
        "capacity_grid": capacity,
        "equal_drawdown": equal_drawdown,
        "r5_interaction": r5_interaction,
        "r5_correlations": correlations,
        "feature_inventory": feature_inventory,
        "component_catalog": components,
    }
    for key, path in outputs.items():
        frames[key].to_csv(path, index=False)

    manifest = {
        "status": "CONSUMED_DEVELOPMENT_STAGE0_ONLY",
        "authority": "NO TRADE, WAIT, SIZING, OR PRODUCTION AUTHORITY",
        "population": "R7G-intended non-warmup FAST k1 Children matched to causal transition episodes",
        "fixed_waits": "mechanism probes only; 180m is not promoted",
        "parity": parity,
        "input_sha256": {
            "events": sha256_file(args.events),
            "episodes": sha256_file(args.episodes),
            "selected_audit": sha256_file(args.selected_audit),
            "feature_registry": sha256_file(args.feature_registry),
        },
        "output_sha256": {key: sha256_file(path) for key, path in outputs.items()},
    }
    manifest_path = args.out_dir / "V11_REASSEMBLY_STAGE0_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(json.dumps(manifest, indent=2))
    print("\nPOLICY SUMMARY")
    print(summary.to_string(index=False))
    print("\nEQUAL DRAWDOWN")
    print(equal_drawdown.to_string(index=False))
    print("\nR5 SPEARMAN")
    print(correlations.to_string(index=False))


if __name__ == "__main__":
    main()
