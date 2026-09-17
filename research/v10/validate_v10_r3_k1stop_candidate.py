"""Independent audit for the V10 R3 K1 extreme-STOP shadow candidate.

This validator intentionally does not import the research metric helpers.  It
reconstructs the selected policy from persisted score and threshold ledgers,
then recomputes economics, execution ambiguity sensitivity, EA-policy parity,
and run-block bootstrap uncertainty from first principles.

The candidate is consumed-data research.  Passing this validator does not
promote a model, threshold, EA, or production strategy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


POLICY = "META_K1STOP_K1_Q0975"
RANDOM_SEED = 20260917


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", required=True, type=Path)
    parser.add_argument("--score-ledger", required=True, type=Path)
    parser.add_argument("--veto-references", required=True, type=Path)
    parser.add_argument("--r2-ledger", required=True, type=Path)
    parser.add_argument("--r2-model-json", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--bootstrap-draws", type=int, default=20_000)
    return parser.parse_args()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def maximum_drawdown(values: np.ndarray, times: pd.Series) -> float:
    ordered = pd.DataFrame({"time": times, "value": values}).sort_values(
        ["time"], kind="mergesort"
    )
    equity = ordered["value"].cumsum().to_numpy(dtype=float)
    if not len(equity):
        return 0.0
    high_water = np.maximum.accumulate(np.r_[0.0, equity])[1:]
    return float(np.max(high_water - equity))


def peak_concurrent_units(frame: pd.DataFrame, units: np.ndarray) -> float:
    events: list[tuple[pd.Timestamp, int, float]] = []
    for entry, exit_, size in zip(frame["entry_time"], frame["exit_time"], units):
        if size <= 0.0:
            continue
        events.append((entry, 1, float(size)))
        events.append((exit_, 0, -float(size)))
    running = 0.0
    peak = 0.0
    for _, _, change in sorted(events, key=lambda item: (item[0], item[1])):
        running += change
        peak = max(peak, running)
    return peak


def economic_row(
    frame: pd.DataFrame,
    units: np.ndarray,
    policy: str,
    period: str,
    pnl_column: str = "pnl",
    r_column: str = "R",
) -> dict[str, object]:
    pnl = frame[pnl_column].to_numpy(dtype=float) * units
    risk_r = frame[r_column].to_numpy(dtype=float) * units
    selected = units > 0.0
    gains = pnl[pnl > 0.0]
    losses = pnl[pnl < 0.0]
    r_gains = risk_r[risk_r > 0.0]
    r_losses = risk_r[risk_r < 0.0]
    oracle = frame["early3"].eq(1).to_numpy()
    positive_l6 = frame["L"].ge(6).to_numpy() & frame[pnl_column].gt(0.0).to_numpy()
    selected_l6_value = float(frame.loc[selected & positive_l6, pnl_column].sum())
    all_l6_value = float(frame.loc[positive_l6, pnl_column].sum())
    return {
        "period": period,
        "policy": policy,
        "outcome_convention": (
            "alternative_nha_first" if pnl_column.startswith("audit_") else "conservative_stop"
        ),
        "rows": int(len(frame)),
        "entries": int(selected.sum()),
        "units": float(units.sum()),
        "pnl": float(pnl.sum()),
        "gross_profit": float(gains.sum()),
        "gross_loss": float(losses.sum()),
        "pf": float(gains.sum() / -losses.sum()) if losses.sum() < 0.0 else float("inf"),
        "R": float(risk_r.sum()),
        "pf_R": float(r_gains.sum() / -r_losses.sum()) if r_losses.sum() < 0.0 else float("inf"),
        "dd_pnl": maximum_drawdown(pnl, frame["exit_time"]),
        "dd_R": maximum_drawdown(risk_r, frame["exit_time"]),
        "oracle_recall": float((selected & oracle).sum() / max(int(oracle.sum()), 1)),
        "oracle_precision": float(oracle[selected].mean()) if selected.any() else float("nan"),
        "weighted_position_hours": float(
            np.sum(units * frame["position_hours"].to_numpy(dtype=float))
        ),
        "max_single_units": float(units.max()) if len(units) else 0.0,
        "max_committed_units": peak_concurrent_units(frame, units),
        "l6_positive_child_retention": (
            selected_l6_value / all_l6_value if all_l6_value > 0.0 else float("nan")
        ),
        "ambiguous_selected": int(
            (selected & frame["same_m1_exit_stop_ambiguous"].eq(1).to_numpy()).sum()
        ),
    }


def reconstruct_ea_latched_units(
    frame: pd.DataFrame, model_json: Path
) -> np.ndarray:
    """Mirror the current EA's run-latched conditional-NEUTRAL admission."""
    model = json.loads(model_json.read_text(encoding="utf-8"))
    units = np.zeros(len(frame), dtype=float)
    work = frame.reset_index(drop=True)
    for _, group in work.sort_values(["decision"]).groupby("rid", sort=False):
        admitted = False
        for row in group.itertuples():
            era = model["eras"][str(int(row.year))]
            thresholds = era["THRESHOLDS"]["RUNWAY_PERSIST"]
            tier = 0.0 if row.score < thresholds["q50"] else (
                1.0 if row.score < thresholds["q75"] else 3.0
            )
            if row.k == 1 and row.shock_score >= era["THRESHOLDS"]["shock_q95"]:
                tier = 0.0
            chop = row.adx28_rel < 1.0 and row.path_eff4_rel < 1.0
            confirm = row.di14_signed > 0.0 or row.ema8_21_signed > 0.0
            if not admitted and (not chop or confirm):
                admitted = True
            units[int(row.Index)] = tier if admitted else 0.0
    return units


def bootstrap_delta(
    frame: pd.DataFrame,
    baseline: np.ndarray,
    candidate: np.ndarray,
    draws: int,
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    work = frame[["year", "rid"]].copy()
    work["delta_R"] = (candidate - baseline) * frame["R"].to_numpy(dtype=float)
    run_gain = work.groupby(["year", "rid"], as_index=False)["delta_R"].sum()
    rng = np.random.default_rng(RANDOM_SEED)
    samples: list[pd.DataFrame] = []
    summaries: list[dict[str, object]] = []

    for label, years in [
        ("2024", [2024]),
        ("2025", [2025]),
        ("2026", [2026]),
        ("POOLED_STRATIFIED_2024_2026", [2024, 2025, 2026]),
    ]:
        total = np.zeros(draws, dtype=float)
        run_count = 0
        observed = 0.0
        for year in years:
            values = run_gain.loc[run_gain["year"].eq(year), "delta_R"].to_numpy(dtype=float)
            run_count += len(values)
            observed += float(values.sum())
            indices = rng.integers(0, len(values), size=(draws, len(values)))
            total += values[indices].sum(axis=1)
        samples.append(
            pd.DataFrame(
                {
                    "period": label,
                    "draw": np.arange(draws, dtype=int),
                    "delta_R": total,
                }
            )
        )
        summaries.append(
            {
                "period": label,
                "runs": run_count,
                "observed_delta_R": observed,
                "bootstrap_mean_delta_R": float(total.mean()),
                "q025_delta_R": float(np.quantile(total, 0.025)),
                "q50_delta_R": float(np.quantile(total, 0.5)),
                "q975_delta_R": float(np.quantile(total, 0.975)),
                "probability_delta_R_gt_zero": float(np.mean(total > 0.0)),
                "draws": draws,
            }
        )
    return pd.concat(samples, ignore_index=True), summaries


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    dates = ["decision", "entry_time", "exit_time", "run_end_decision", "label_available_at"]
    universe = pd.read_csv(args.universe, parse_dates=dates)
    universe = universe[universe["year"].between(2024, 2026)].sort_values(
        "decision", kind="mergesort"
    ).reset_index(drop=True)
    scores = pd.read_csv(args.score_ledger, parse_dates=["decision"])
    references = pd.read_csv(args.veto_references)
    r2 = pd.read_csv(args.r2_ledger, parse_dates=["decision"]).sort_values(
        "decision", kind="mergesort"
    ).reset_index(drop=True)

    if universe["decision"].duplicated().any() or r2["decision"].duplicated().any():
        raise RuntimeError("decision keys are not unique")
    joined = universe.merge(
        r2[["decision", "W", "score", "shock_score"]],
        on="decision",
        how="outer",
        validate="one_to_one",
        indicator=True,
    ).copy()
    if not joined["_merge"].eq("both").all():
        raise RuntimeError("universe and R2 ledger decisions differ")
    joined = joined.drop(columns="_merge").sort_values("decision", kind="mergesort").reset_index(drop=True)
    joined = joined.merge(
        scores[["decision", "meta_p_k1_stop"]],
        on="decision",
        how="left",
        validate="one_to_one",
    ).copy()
    if joined.loc[joined["W"].gt(0.0), "meta_p_k1_stop"].isna().any():
        raise RuntimeError("selected R2 rows are missing K1-STOP scores")

    chosen_refs = references[
        references["kind"].eq("K1STOP")
        & references["stage"].eq("K1")
        & np.isclose(references["quantile"], 0.975)
    ].copy()
    if set(chosen_refs["outer_year"].astype(int)) != {2024, 2025, 2026}:
        raise RuntimeError("expected one q97.5 K1STOP reference for each outer year")
    threshold_by_year = chosen_refs.set_index(chosen_refs["outer_year"].astype(int))[
        "prior_threshold"
    ].to_dict()
    joined["prior_oof_q0975"] = joined["year"].map(threshold_by_year)
    joined["veto"] = (
        joined["W"].gt(0.0)
        & joined["k"].eq(1)
        & joined["meta_p_k1_stop"].ge(joined["prior_oof_q0975"])
    )
    joined["candidate_W"] = np.where(joined["veto"], 0.0, joined["W"]).astype(float)

    # Alternative chronology is used only as a sensitivity bound.  It is not
    # asserted as the true intraminute order for same-M1 NHA/SL touches.
    joined["audit_pnl_alt_nha"] = joined["pnl"].astype(float)
    joined["audit_R_alt_nha"] = joined["R"].astype(float)
    ambiguous = joined["same_m1_exit_stop_ambiguous"].eq(1)
    joined.loc[ambiguous, "audit_pnl_alt_nha"] = joined.loc[ambiguous, "alternative_nha_pnl"]
    joined.loc[ambiguous, "audit_R_alt_nha"] = joined.loc[ambiguous, "alternative_nha_R"]

    metrics: list[dict[str, object]] = []
    for year in (2024, 2025, 2026):
        mask = joined["year"].eq(year).to_numpy()
        year_frame = joined.loc[mask].reset_index(drop=True)
        for policy, units in (
            ("R2_DEFAULT", joined.loc[mask, "W"].to_numpy(dtype=float)),
            (POLICY, joined.loc[mask, "candidate_W"].to_numpy(dtype=float)),
        ):
            metrics.append(economic_row(year_frame, units, policy, str(year)))
            metrics.append(
                economic_row(
                    year_frame,
                    units,
                    policy,
                    str(year),
                    "audit_pnl_alt_nha",
                    "audit_R_alt_nha",
                )
            )
    for policy, units in (
        ("R2_DEFAULT", joined["W"].to_numpy(dtype=float)),
        (POLICY, joined["candidate_W"].to_numpy(dtype=float)),
    ):
        metrics.append(economic_row(joined, units, policy, "POOLED_2024_2026"))
        metrics.append(
            economic_row(
                joined,
                units,
                policy,
                "POOLED_2024_2026",
                "audit_pnl_alt_nha",
                "audit_R_alt_nha",
            )
        )

    baseline_units = joined["W"].to_numpy(dtype=float)
    candidate_units = joined["candidate_W"].to_numpy(dtype=float)
    bootstrap, bootstrap_summary = bootstrap_delta(
        joined, baseline_units, candidate_units, args.bootstrap_draws
    )

    ea_units = reconstruct_ea_latched_units(joined, args.r2_model_json)
    ea_mismatch = ~np.isclose(ea_units, baseline_units)
    ea_ledger = joined.loc[
        ea_mismatch,
        ["signal_id", "decision", "year", "rid", "k", "dir", "W", "score", "shock_score"],
    ].copy()
    ea_ledger["ea_latched_W"] = ea_units[ea_mismatch]

    vetoed = joined.loc[joined["veto"]].copy()
    vetoed["baseline_weighted_pnl"] = vetoed["W"] * vetoed["pnl"]
    vetoed["baseline_weighted_R"] = vetoed["W"] * vetoed["R"]
    veto_summary = {
        "rows": int(len(vetoed)),
        "units_removed": float(vetoed["W"].sum()),
        "wins_removed": int(vetoed["pnl"].gt(0.0).sum()),
        "losses_removed": int(vetoed["pnl"].lt(0.0).sum()),
        "flat_removed": int(vetoed["pnl"].eq(0.0).sum()),
        "stop_hits_removed": int(vetoed["stop_hit"].sum()),
        "oracle_early3_removed": int(vetoed["early3"].sum()),
        "L6plus_positive_removed": int((vetoed["L"].ge(6) & vetoed["pnl"].gt(0.0)).sum()),
        "baseline_weighted_pnl_removed": float(vetoed["baseline_weighted_pnl"].sum()),
        "baseline_weighted_R_removed": float(vetoed["baseline_weighted_R"].sum()),
        "candidate_delta_pnl": float(-vetoed["baseline_weighted_pnl"].sum()),
        "candidate_delta_R": float(-vetoed["baseline_weighted_R"].sum()),
    }

    action_columns = [
        "signal_id", "decision", "entry_time", "exit_time", "year", "dir", "rid", "k", "L",
        "entry", "stop", "exit", "exit_reason", "stop_hit", "same_m1_exit_stop_ambiguous",
        "pnl", "R", "early3", "W", "meta_p_k1_stop", "prior_oof_q0975", "veto", "candidate_W",
    ]
    joined[action_columns].to_csv(
        args.out_dir / "V10_R3_K1STOP_Q0975_ACTION_LEDGER.csv", index=False
    )
    vetoed[action_columns + ["baseline_weighted_pnl", "baseline_weighted_R"]].to_csv(
        args.out_dir / "V10_R3_K1STOP_Q0975_VETOED_EVENTS.csv", index=False
    )
    pd.DataFrame(metrics).to_csv(
        args.out_dir / "V10_R3_K1STOP_Q0975_INDEPENDENT_METRICS.csv", index=False
    )
    bootstrap.to_csv(args.out_dir / "V10_R3_K1STOP_Q0975_BOOTSTRAP_DRAWS.csv", index=False)
    pd.DataFrame(bootstrap_summary).to_csv(
        args.out_dir / "V10_R3_K1STOP_Q0975_BOOTSTRAP_SUMMARY.csv", index=False
    )
    ea_ledger.to_csv(args.out_dir / "V10_R2_EA_LEDGER_POLICY_MISMATCH.csv", index=False)

    expected_veto_counts = chosen_refs.set_index(chosen_refs["outer_year"].astype(int))["vetoed"].astype(int)
    actual_veto_counts = vetoed.groupby("year").size().reindex([2024, 2025, 2026], fill_value=0)
    reference_veto_match = bool((expected_veto_counts.reindex(actual_veto_counts.index) == actual_veto_counts).all())

    receipt = {
        "ok": bool(reference_veto_match and len(ea_ledger) == 6),
        "policy": POLICY,
        "authority": "CONSUMED-DATA SHADOW RESEARCH / NOT STRATEGY AUTHORITY",
        "reference_veto_counts_match": reference_veto_match,
        "veto_counts_by_year": {str(k): int(v) for k, v in actual_veto_counts.items()},
        "veto_summary": veto_summary,
        "bootstrap_summary": bootstrap_summary,
        "ea_vs_research_ledger_mismatch_rows": int(len(ea_ledger)),
        "same_m1_ambiguous_rows_in_universe": int(ambiguous.sum()),
        "source_hashes": {
            "universe": file_hash(args.universe),
            "score_ledger": file_hash(args.score_ledger),
            "veto_references": file_hash(args.veto_references),
            "r2_ledger": file_hash(args.r2_ledger),
            "r2_model_json": file_hash(args.r2_model_json),
        },
        "bootstrap_seed": RANDOM_SEED,
        "bootstrap_draws": args.bootstrap_draws,
        "limitations": [
            "q97.5 was selected after an explicit consumed-data threshold scan",
            "2022-2026 are consumed development evidence and provide no independent validation",
            "same-M1 NHA-versus-SL ordering is unknowable from M1 OHLC and is reported as a sensitivity bound",
            "the current R2 EA run-latched admission differs from the committed per-Child research ledger",
        ],
    }
    (args.out_dir / "V10_R3_K1STOP_Q0975_VALIDATION.json").write_text(
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
    print(f"\nEA / research-ledger mismatches: {len(ea_ledger)}")


if __name__ == "__main__":
    main()
