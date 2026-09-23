"""Stage-3 V11 reassembly: place the retained k1 capital ladder in the full R7G portfolio.

This diagnostic does not select a new signal.  It keeps every resolved selected
R7G Child, preserves all k2+ allocations, and replaces only the selected k1
allocation with Stage 2's one-unit participation plus causal FAST-k2 release.
The purpose is to expose overlap, concurrent risk, and full-portfolio economics
before any mechanism is considered for future validation.

All inputs are consumed development evidence.  Nothing in this file has trade,
release, sizing, leverage, EA, execution, or production authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


POLICY_BASELINE = "ORIGINAL_FULL_R7G_PORTFOLIO"
POLICY_LADDER = "K1_ONE_NOW_REST_FAST_K2_PORTFOLIO"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_event_decision(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values.astype(str).str.replace(".", "-", regex=False))


def equity_path(values: Iterable[float], risk_fraction: float) -> tuple[float, float]:
    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for value in values:
        equity *= max(1e-12, 1.0 + risk_fraction * float(value))
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, 1.0 - equity / peak)
    return float(equity), float(max_drawdown)


def equal_drawdown_risk(values: np.ndarray, target_drawdown: float) -> float:
    low, high = 0.0, 0.10
    if equity_path(values, high)[1] < target_drawdown:
        return math.nan
    for _ in range(100):
        middle = (low + high) / 2.0
        if equity_path(values, middle)[1] < target_drawdown:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


def load_selected_portfolio(events_path: Path, universe_path: Path) -> pd.DataFrame:
    events = pd.read_csv(events_path)
    universe = pd.read_csv(universe_path)
    events["decision_ts"] = normalize_event_decision(events["decision"])
    universe["decision_ts"] = pd.to_datetime(universe["decision"])
    if events.duplicated(["decision_ts", "k"]).any():
        raise RuntimeError("event grain is not unique")
    if universe.duplicated(["decision_ts", "k"]).any():
        raise RuntimeError("universe grain is not unique")
    selected = events[
        events["r7g_weight"].gt(0) & events["event"].ne("SHADOW_WARMUP")
    ][["decision_ts", "k", "event", "r7g_weight"]].copy()
    columns = [
        "decision_ts", "k", "signal_id", "entry_time", "exit_time", "year",
        "dir", "rid", "L", "run_end_decision", "R", "stop_hit",
        "same_m1_exit_stop_ambiguous",
    ]
    merged = selected.merge(
        universe[columns], on=["decision_ts", "k"], how="inner", validate="one_to_one"
    ).sort_values(["decision_ts", "k"]).reset_index(drop=True)
    if len(selected) != 1650 or len(merged) != 1649:
        raise RuntimeError(
            f"expected selected/universe counts 1650/1649, got {len(selected)}/{len(merged)}"
        )
    if len(merged[merged["k"].eq(1)]) != 626:
        raise RuntimeError("full portfolio did not retain the 626 Stage-2 k1 Children")
    if not merged["r7g_weight"].isin([1, 3]).all():
        raise RuntimeError("unexpected R7G weight outside {1,3}")
    for column in ("entry_time", "exit_time", "run_end_decision"):
        merged[column] = pd.to_datetime(merged[column])
    return merged


def load_k1_ladder(stage2_ledger_path: Path) -> pd.DataFrame:
    ledger = pd.read_csv(stage2_ledger_path, low_memory=False)
    ladder = ledger[
        ledger["scope"].eq("2024_2026")
        & ledger["policy"].eq("ONE_NOW_REST_FAST_K2")
    ].copy()
    if len(ladder) != 626 or ladder["signal_id"].nunique() != 626:
        raise RuntimeError("Stage-2 ladder must contain 626 unique k1 Children")
    for column in ("decision_ts", "entry_time", "exit_time", "k2_entry_time", "k2_exit_time"):
        ladder[column] = pd.to_datetime(ladder[column])
    return ladder


def child_ledgers(portfolio: pd.DataFrame, ladder: pd.DataFrame) -> pd.DataFrame:
    base = portfolio.copy()
    base["policy"] = POLICY_BASELINE
    base["combined_R_units"] = base["R"] * base["r7g_weight"]
    base["stopped_loss_units"] = base["stop_hit"] * base["r7g_weight"]
    base["funded_units"] = base["r7g_weight"].astype(float)
    base["full_3unit_stop"] = (
        base["r7g_weight"].eq(3) & base["stop_hit"].eq(1)
    ).astype(int)

    staged = portfolio.copy()
    k1 = ladder[[
        "decision_ts", "k", "combined_R_units", "stopped_units", "funded_units",
        "full_3unit_stop", "k2_valid", "k2_reason", "k2_entry_time",
        "k2_exit_time", "k2_R", "k2_stop_hit",
    ]].rename(columns={"stopped_units": "staged_stopped_units"})
    staged = staged.merge(k1, on=["decision_ts", "k"], how="left", validate="one_to_one")
    k1_mask = staged["k"].eq(1)
    if staged.loc[k1_mask, "combined_R_units"].isna().any():
        raise RuntimeError("Stage-2 ladder did not cover every full-portfolio k1 Child")
    staged["policy"] = POLICY_LADDER
    staged.loc[~k1_mask, "combined_R_units"] = (
        staged.loc[~k1_mask, "R"] * staged.loc[~k1_mask, "r7g_weight"]
    )
    staged.loc[k1_mask, "stopped_loss_units"] = staged.loc[k1_mask, "staged_stopped_units"]
    staged.loc[~k1_mask, "stopped_loss_units"] = (
        staged.loc[~k1_mask, "stop_hit"] * staged.loc[~k1_mask, "r7g_weight"]
    )
    staged.loc[~k1_mask, "funded_units"] = staged.loc[~k1_mask, "r7g_weight"].astype(float)
    staged.loc[~k1_mask, "full_3unit_stop"] = (
        staged.loc[~k1_mask, "r7g_weight"].eq(3)
        & staged.loc[~k1_mask, "stop_hit"].eq(1)
    ).astype(int)
    staged["full_3unit_stop"] = staged["full_3unit_stop"].fillna(0).astype(int)
    return pd.concat([base, staged], ignore_index=True, sort=False)


def build_tranches(portfolio: pd.DataFrame, ladder: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for row in portfolio.itertuples(index=False):
        records.append({
            "policy": POLICY_BASELINE,
            "signal_id": row.signal_id,
            "rid": int(row.rid),
            "k": int(row.k),
            "dir": int(row.dir),
            "tranche": "ORIGINAL",
            "open_time": row.entry_time,
            "close_time": row.exit_time,
            "units": float(row.r7g_weight),
            "R_per_unit": float(row.R),
            "R_units": float(row.R) * float(row.r7g_weight),
            "stop_units": float(row.stop_hit) * float(row.r7g_weight),
        })
        if int(row.k) > 1:
            records.append({
                "policy": POLICY_LADDER,
                "signal_id": row.signal_id,
                "rid": int(row.rid),
                "k": int(row.k),
                "dir": int(row.dir),
                "tranche": "ORIGINAL_K2_PLUS",
                "open_time": row.entry_time,
                "close_time": row.exit_time,
                "units": float(row.r7g_weight),
                "R_per_unit": float(row.R),
                "R_units": float(row.R) * float(row.r7g_weight),
                "stop_units": float(row.stop_hit) * float(row.r7g_weight),
            })
    ladder_by_decision = ladder.set_index("decision_ts")
    for row in portfolio[portfolio["k"].eq(1)].itertuples(index=False):
        staged = ladder_by_decision.loc[row.decision_ts]
        records.append({
            "policy": POLICY_LADDER,
            "signal_id": row.signal_id,
            "rid": int(row.rid),
            "k": 1,
            "dir": int(row.dir),
            "tranche": "K1_PARTICIPATION",
            "open_time": row.entry_time,
            "close_time": row.exit_time,
            "units": 1.0,
            "R_per_unit": float(row.R),
            "R_units": float(row.R),
            "stop_units": float(row.stop_hit),
        })
        if int(staged.k2_valid) == 1:
            records.append({
                "policy": POLICY_LADDER,
                "signal_id": row.signal_id,
                "rid": int(row.rid),
                "k": 1,
                "dir": int(row.dir),
                "tranche": "K1_FAST_K2_TOPUP",
                "open_time": staged.k2_entry_time,
                "close_time": staged.k2_exit_time,
                "units": 2.0,
                "R_per_unit": float(staged.k2_R),
                "R_units": 2.0 * float(staged.k2_R),
                "stop_units": 2.0 * float(staged.k2_stop_hit),
            })
    tranches = pd.DataFrame(records)
    if tranches[["open_time", "close_time", "units", "R_units"]].isna().any().any():
        raise RuntimeError("tranche ledger contains missing economic fields")
    if (tranches["close_time"] < tranches["open_time"]).any():
        raise RuntimeError("tranche closes before it opens")
    return tranches.sort_values(["policy", "open_time", "signal_id", "tranche"]).reset_index(drop=True)


def exposure_metrics(tranches: pd.DataFrame, close_before_open: bool) -> dict[str, float]:
    events: list[tuple[pd.Timestamp, int, float, float]] = []
    for row in tranches.itertuples(index=False):
        # rank controls same-timestamp ordering.  Both conventions are retained
        # so an instantaneous ordering assumption cannot manufacture the peak.
        if pd.Timestamp(row.open_time) == pd.Timestamp(row.close_time):
            # A zero-duration intended tranche cannot close before it exists.
            # It affects the open-first instantaneous sensitivity only.
            open_rank, close_rank = (1, 2) if close_before_open else (0, 1)
        else:
            close_rank = 0 if close_before_open else 1
            open_rank = 1 if close_before_open else 0
        events.append((pd.Timestamp(row.open_time), open_rank, float(row.units), float(row.dir) * float(row.units)))
        events.append((pd.Timestamp(row.close_time), close_rank, -float(row.units), -float(row.dir) * float(row.units)))
    events.sort(key=lambda item: (item[0], item[1]))
    gross = net = 0.0
    max_gross = max_abs_net = 0.0
    last_time: pd.Timestamp | None = None
    weighted_gross_seconds = 0.0
    weighted_abs_net_seconds = 0.0
    total_seconds = 0.0
    positive_exposure_seconds = 0.0
    for ts, _, gross_delta, net_delta in events:
        if last_time is not None and ts > last_time:
            seconds = float((ts - last_time).total_seconds())
            weighted_gross_seconds += gross * seconds
            weighted_abs_net_seconds += abs(net) * seconds
            total_seconds += seconds
            if gross > 0:
                positive_exposure_seconds += seconds
        gross += gross_delta
        net += net_delta
        if gross < -1e-9:
            raise RuntimeError("negative gross exposure")
        max_gross = max(max_gross, gross)
        max_abs_net = max(max_abs_net, abs(net))
        last_time = ts
    if abs(gross) > 1e-9 or abs(net) > 1e-9:
        raise RuntimeError("portfolio exposure did not close")
    return {
        "max_gross_units": max_gross,
        "max_abs_net_units": max_abs_net,
        "calendar_mean_gross_units": weighted_gross_seconds / total_seconds,
        "invested_time_mean_gross_units": weighted_gross_seconds / positive_exposure_seconds,
        "calendar_mean_abs_net_units": weighted_abs_net_seconds / total_seconds,
    }


def realized_path(tranches: pd.DataFrame) -> pd.DataFrame:
    return (
        tranches.groupby("close_time", as_index=False)
        .agg(R_units=("R_units", "sum"), stop_units=("stop_units", "sum"))
        .sort_values("close_time")
    )


def summarize_policy(children: pd.DataFrame, tranches: pd.DataFrame) -> dict[str, object]:
    policy = str(children["policy"].iloc[0])
    path = realized_path(tranches)
    ending, drawdown = equity_path(path["R_units"], 0.01)
    close_first = exposure_metrics(tranches, close_before_open=True)
    open_first = exposure_metrics(tranches, close_before_open=False)
    return {
        "policy": policy,
        "children": int(len(children)),
        "participation_retention": 1.0,
        "hard_sl_children": int(children["stop_hit"].sum()),
        "conventional_win_rate": float(children["combined_R_units"].gt(0).mean()),
        "stopped_loss_units": float(children["stopped_loss_units"].sum()),
        "full_3unit_stop_children": int(children["full_3unit_stop"].sum()),
        "funded_units": float(children["funded_units"].sum()),
        "combined_R_units": float(children["combined_R_units"].sum()),
        "tranches": int(len(tranches)),
        "realization_timestamps": int(len(path)),
        "ending_equity_1pct_per_unit": ending,
        "max_drawdown_1pct_per_unit": drawdown,
        "max_gross_units_close_first": close_first["max_gross_units"],
        "max_gross_units_open_first": open_first["max_gross_units"],
        "max_abs_net_units_close_first": close_first["max_abs_net_units"],
        "calendar_mean_gross_units": close_first["calendar_mean_gross_units"],
        "invested_time_mean_gross_units": close_first["invested_time_mean_gross_units"],
    }


def summarize_child_slice(frame: pd.DataFrame, kind: str, value: str) -> dict[str, object]:
    return {
        "policy": str(frame["policy"].iloc[0]),
        "slice_kind": kind,
        "slice_value": value,
        "children": int(len(frame)),
        "hard_sl_children": int(frame["stop_hit"].sum()),
        "conventional_win_rate": float(frame["combined_R_units"].gt(0).mean()),
        "stopped_loss_units": float(frame["stopped_loss_units"].sum()),
        "full_3unit_stop_children": int(frame["full_3unit_stop"].sum()),
        "funded_units": float(frame["funded_units"].sum()),
        "combined_R_units": float(frame["combined_R_units"].sum()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--universe", type=Path, required=True)
    parser.add_argument("--stage2-ledger", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    portfolio = load_selected_portfolio(args.events, args.universe)
    ladder = load_k1_ladder(args.stage2_ledger)
    children = child_ledgers(portfolio, ladder)
    tranches = build_tranches(portfolio, ladder)

    summary_rows: list[dict[str, object]] = []
    paths: dict[str, np.ndarray] = {}
    for policy in (POLICY_BASELINE, POLICY_LADDER):
        policy_children = children[children["policy"].eq(policy)].copy()
        policy_tranches = tranches[tranches["policy"].eq(policy)].copy()
        summary_rows.append(summarize_policy(policy_children, policy_tranches))
        paths[policy] = realized_path(policy_tranches)["R_units"].to_numpy(dtype=float)
    summary = pd.DataFrame(summary_rows)
    slice_rows: list[dict[str, object]] = []
    for policy, policy_frame in children.groupby("policy", sort=False):
        for year, group in policy_frame.groupby("year", sort=True):
            slice_rows.append(summarize_child_slice(group, "YEAR", str(int(year))))
        for direction, group in policy_frame.groupby("dir", sort=True):
            slice_rows.append(summarize_child_slice(
                group, "SIDE", "LONG" if int(direction) > 0 else "SHORT"
            ))
        for event, group in policy_frame.groupby("event", sort=True):
            slice_rows.append(summarize_child_slice(group, "EVENT", str(event)))
        for boundary, group in policy_frame.groupby(policy_frame["k"].eq(1), sort=False):
            slice_rows.append(summarize_child_slice(
                group, "RUN_POSITION", "K1" if bool(boundary) else "K2_PLUS"
            ))
    slices = pd.DataFrame(slice_rows)
    baseline = summary[summary["policy"].eq(POLICY_BASELINE)].iloc[0]
    summary["stop_unit_reduction"] = 1.0 - summary["stopped_loss_units"] / baseline["stopped_loss_units"]
    summary["full_3unit_stop_reduction"] = 1.0 - summary["full_3unit_stop_children"] / baseline["full_3unit_stop_children"]
    summary["combined_R_retention"] = summary["combined_R_units"] / baseline["combined_R_units"]
    summary["funded_unit_retention"] = summary["funded_units"] / baseline["funded_units"]
    target_dd = float(baseline["max_drawdown_1pct_per_unit"])
    risks: list[float] = []
    equal_equity: list[float] = []
    for row in summary.itertuples(index=False):
        risk = equal_drawdown_risk(paths[row.policy], target_dd)
        risks.append(risk)
        equal_equity.append(equity_path(paths[row.policy], risk)[0] if np.isfinite(risk) else math.nan)
    summary["equal_drawdown_risk_fraction"] = risks
    summary["equal_drawdown_ending_equity"] = equal_equity

    k1_valid = ladder[ladder["k2_valid"].eq(1)].copy()
    selected_k2 = portfolio[portfolio["k"].eq(2)][
        ["rid", "decision_ts", "signal_id", "r7g_weight", "event", "stop_hit", "R"]
    ].rename(columns={
        "signal_id": "independent_k2_signal_id",
        "r7g_weight": "independent_k2_weight",
        "event": "independent_k2_event",
        "stop_hit": "independent_k2_stop_hit",
        "R": "independent_k2_R",
    })
    overlap = k1_valid.merge(
        selected_k2, left_on=["rid", "k2_entry_time"], right_on=["rid", "decision_ts"],
        how="left", validate="one_to_one"
    )
    overlap["has_selected_independent_k2"] = overlap["independent_k2_signal_id"].notna().astype(int)
    overlap_summary = {
        "valid_k1_fast_k2_topups": int(len(k1_valid)),
        "topups_with_selected_independent_k2": int(overlap["has_selected_independent_k2"].sum()),
        "topups_without_selected_independent_k2": int((1 - overlap["has_selected_independent_k2"]).sum()),
        "overlap_k2_weight_3": int(overlap["independent_k2_weight"].eq(3).sum()),
        "overlap_k2_weight_1": int(overlap["independent_k2_weight"].eq(1).sum()),
        "overlap_k2_order_fail": int(overlap["independent_k2_event"].eq("ORDER_FAIL").sum()),
    }

    quality = {
        "grain": {
            "children": "one resolved selected R7G Child per policy",
            "tranches": "one independently opened risk tranche",
        },
        "selected_event_rows": 1650,
        "resolved_selected_children": int(len(portfolio)),
        "unmatched_selected_children": {
            "count": 1,
            "decision": "2026-08-28 20:00:00",
            "k": 1,
            "side": "SHORT",
            "r7g_weight": 3,
            "reason": "source chronology ends before a resolved causal outcome is available",
        },
        "children_by_k": {str(int(k)): int(len(group)) for k, group in portfolio.groupby("k")},
        "children_by_event": {str(event): int(len(group)) for event, group in portfolio.groupby("event")},
        "overlap": overlap_summary,
        "same_timestamp_exposure_boundary": (
            "close-before-open and open-before-close peaks are both reported; no exact tick order is invented"
        ),
        "invariants": {
            "both_policies_keep_all_resolved_children": bool(summary["children"].eq(1649).all()),
            "hard_sl_children_unchanged": bool(summary["hard_sl_children"].nunique() == 1),
            "all_k2_plus_weights_unchanged": bool(
                np.isclose(
                    children[(children["policy"].eq(POLICY_BASELINE)) & children["k"].gt(1)]["funded_units"].sum(),
                    children[(children["policy"].eq(POLICY_LADDER)) & children["k"].gt(1)]["funded_units"].sum(),
                )
            ),
            "tranche_R_matches_child_R": bool(
                all(
                    np.isclose(
                        tranches[tranches["policy"].eq(policy)]["R_units"].sum(),
                        children[children["policy"].eq(policy)]["combined_R_units"].sum(),
                    )
                    for policy in (POLICY_BASELINE, POLICY_LADDER)
                )
            ),
            "tranche_stop_units_match_children": bool(
                all(
                    np.isclose(
                        tranches[tranches["policy"].eq(policy)]["stop_units"].sum(),
                        children[children["policy"].eq(policy)]["stopped_loss_units"].sum(),
                    )
                    for policy in (POLICY_BASELINE, POLICY_LADDER)
                )
            ),
        },
        "interpretation_boundary": (
            "This is an intended-strategy portfolio diagnostic. ORDER_FAIL and EXIT_PENDING_BLOCK Children retain "
            "their frozen counterfactual outcomes; execution parity, costs, margin, and live leverage remain unresolved."
        ),
    }
    if not all(quality["invariants"].values()):
        raise RuntimeError(f"stage3 invariant failed: {quality['invariants']}")

    outputs = {
        "summary": args.out_dir / "V11_REASSEMBLY_STAGE3_PORTFOLIO_SUMMARY.csv",
        "slices": args.out_dir / "V11_REASSEMBLY_STAGE3_PORTFOLIO_SLICES.csv",
        "children": args.out_dir / "V11_REASSEMBLY_STAGE3_CHILD_LEDGER.csv",
        "tranches": args.out_dir / "V11_REASSEMBLY_STAGE3_TRANCHE_LEDGER.csv",
        "overlap": args.out_dir / "V11_REASSEMBLY_STAGE3_K2_OVERLAP.csv",
        "quality": args.out_dir / "V11_REASSEMBLY_STAGE3_DATA_QUALITY.json",
    }
    summary.to_csv(outputs["summary"], index=False)
    slices.to_csv(outputs["slices"], index=False)
    children.to_csv(outputs["children"], index=False)
    tranches.to_csv(outputs["tranches"], index=False)
    overlap.to_csv(outputs["overlap"], index=False)
    outputs["quality"].write_text(json.dumps(quality, indent=2), encoding="utf-8")
    manifest = {
        "status": "CONSUMED_DEVELOPMENT_STAGE3_ONLY",
        "authority": "NO TRADE, RELEASE, SIZING, LEVERAGE, EA, EXECUTION, OR PRODUCTION AUTHORITY",
        "question": "Does the retained k1 capital ladder survive full-R7G portfolio overlap and concurrency accounting?",
        "input_sha256": {
            "events": sha256_file(args.events),
            "universe": sha256_file(args.universe),
            "stage2_ledger": sha256_file(args.stage2_ledger),
        },
        "output_sha256": {key: sha256_file(path) for key, path in outputs.items()},
    }
    manifest_path = args.out_dir / "V11_REASSEMBLY_STAGE3_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print("\nPORTFOLIO SUMMARY")
    print(summary.to_string(index=False))
    print("\nOVERLAP")
    print(json.dumps(overlap_summary, indent=2))


if __name__ == "__main__":
    main()
