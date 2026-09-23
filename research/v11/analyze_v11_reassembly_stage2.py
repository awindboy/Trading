"""Stage-2 V11 reassembly: separate participation from size deployment.

Stage 1 showed that a binary fund/skip clock still discards too many Children.
This diagnostic keeps one unit of participation on every frozen R7G-intended
k1 Child and treats the remaining R7G ceiling as separately deployable capital.
It measures stopped loss-units as well as stopped Children so a lower drawdown
cannot be misreported as a higher conventional win rate.

Fixed checkpoints and the Stage-1 model are mechanism probes only.  Nothing in
this file has trade, wait, sizing, or production authority.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


STOP_COSTS = (0.0, 0.25, 0.50, 1.0, 2.0)
SOURCE_TS = "%Y.%m.%d %H:%M:%S"


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


def max_stop_streak(frame: pd.DataFrame) -> tuple[int, float]:
    best_children = current_children = 0
    best_units = current_units = 0.0
    for row in frame.sort_values("decision").itertuples(index=False):
        if int(row.stop_child) == 1:
            current_children += 1
            current_units += float(row.stopped_units)
        else:
            current_children = 0
            current_units = 0.0
        best_children = max(best_children, current_children)
        best_units = max(best_units, current_units)
    return best_children, best_units


def load_population(events_path: Path, episodes_path: Path) -> pd.DataFrame:
    events = pd.read_csv(events_path)
    episodes = pd.read_csv(episodes_path)
    events["decision_ts"] = normalize_event_decision(events["decision"])
    episodes["decision_ts"] = pd.to_datetime(episodes["decision"])
    if events.duplicated(["decision_ts", "k"]).any():
        raise RuntimeError("event grain is not unique")
    if episodes.duplicated(["decision_ts", "k"]).any():
        raise RuntimeError("episode grain is not unique")
    columns = ["decision_ts", "k", "event", "r4_weight", "r7g_weight", "p_stop", "mu_nonstop"]
    merged = episodes.merge(events[columns], on=["decision_ts", "k"], how="inner", validate="one_to_one")
    selected = merged[
        merged["r7g_weight"].gt(0) & merged["event"].ne("SHADOW_WARMUP")
    ].copy().sort_values("decision_ts").reset_index(drop=True)
    if len(selected) != 626:
        raise RuntimeError(f"expected 626 selected k1 Children, got {len(selected)}")
    if not selected["r7g_weight"].isin([1, 3]).all():
        raise RuntimeError("unexpected R7G ceiling outside {1,3}")
    for minute in (60, 120, 180):
        valid = selected[f"b{minute}_valid"].eq(1)
        if (valid & selected[f"b{minute}_R"].isna()).any():
            raise RuntimeError(f"valid {minute}m top-up missing R")
        if (valid & selected[f"b{minute}_stop_hit"].isna()).any():
            raise RuntimeError(f"valid {minute}m top-up missing stop label")
    return selected


def causal_fast_k2_release(m1_path: Path, population: pd.DataFrame) -> pd.DataFrame:
    """Replay a same-direction FAST-k2 top-up with the original k1 Hard SL.

    The M1 file is consumed once in timestamp order.  A candidate is eligible at
    decision+4h only when the frozen FAST run has a k2 (L>=2), its original stop
    has not touched, and an M1 open appears within 15 minutes of that decision.
    """
    records: list[dict[str, object]] = []
    for row in population.itertuples(index=False):
        records.append({
            "decision_ts": pd.Timestamp(row.decision_ts),
            "checkpoint": pd.Timestamp(row.decision_ts) + pd.Timedelta(hours=4),
            "run_end": pd.Timestamp(row.run_end_decision),
            "dir": int(row.dir),
            "stop": float(row.stop),
            "eligible": int(row.L) >= 2 and int(row.r7g_weight) == 3,
            "guard_touched": 0,
            "valid": 0,
            "entry_time": pd.NaT,
            "entry": math.nan,
            "exit_time": pd.NaT,
            "exit": math.nan,
            "stop_hit": math.nan,
            "R": math.nan,
            "done": False,
            "reason": "PENDING" if (int(row.L) >= 2 and int(row.r7g_weight) == 3) else "NOT_ELIGIBLE",
        })
    decision_order = sorted(range(len(records)), key=lambda i: records[i]["decision_ts"])
    next_decision = 0
    pending: set[int] = set()
    active: set[int] = set()
    previous_ts: datetime | None = None

    with m1_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        expected = {"<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>"}
        if not expected.issubset(reader.fieldnames or []):
            raise RuntimeError(f"unexpected raw-M1 schema: {reader.fieldnames}")
        for source in reader:
            ts_dt = datetime.strptime(f"{source['<DATE>']} {source['<TIME>']}", SOURCE_TS)
            if previous_ts is not None and ts_dt <= previous_ts:
                raise RuntimeError(f"raw M1 not strictly chronological at {ts_dt}")
            previous_ts = ts_dt
            ts = pd.Timestamp(ts_dt)
            o = float(source["<OPEN>"])
            high = float(source["<HIGH>"])
            low = float(source["<LOW>"])

            while next_decision < len(decision_order):
                index = decision_order[next_decision]
                if records[index]["decision_ts"] > ts:
                    break
                next_decision += 1
                if records[index]["eligible"]:
                    pending.add(index)

            # Campaign exit occurs at the decision open, before this M1 range.
            for index in list(active):
                record = records[index]
                if record["run_end"] <= ts:
                    risk = abs(float(record["entry"]) - float(record["stop"]))
                    record["exit_time"] = ts
                    record["exit"] = o
                    record["stop_hit"] = 0
                    record["R"] = int(record["dir"]) * (o - float(record["entry"])) / risk
                    record["done"] = True
                    active.remove(index)

            # At the k2 decision, entry is the first causal M1 open.  Its range
            # belongs to the funded tranche, not to the pre-entry guard.
            for index in list(pending):
                record = records[index]
                if record["checkpoint"] <= ts:
                    pending.remove(index)
                    if ts - record["checkpoint"] > pd.Timedelta(minutes=15):
                        record["done"] = True
                        record["reason"] = "NO_OBSERVATION"
                        continue
                    stop = float(record["stop"])
                    direction = int(record["dir"])
                    if (direction > 0 and stop >= o) or (direction < 0 and stop <= o):
                        record["done"] = True
                        record["reason"] = "STOP_INVALID_AT_RELEASE"
                        continue
                    record["valid"] = 1
                    record["reason"] = "FUNDED"
                    record["entry_time"] = ts
                    record["entry"] = o
                    active.add(index)

            # Candidates still waiting for k2 retain the frozen Hard-SL guard.
            for index in list(pending):
                record = records[index]
                touched = low <= float(record["stop"]) if int(record["dir"]) > 0 else high >= float(record["stop"])
                if touched:
                    record["guard_touched"] = 1
                    record["done"] = True
                    record["reason"] = "GUARD_DIED"
                    pending.remove(index)

            # Funded k2 tranches use the same original k1 Hard SL.
            for index in list(active):
                record = records[index]
                touched = low <= float(record["stop"]) if int(record["dir"]) > 0 else high >= float(record["stop"])
                if touched:
                    record["exit_time"] = ts
                    record["exit"] = float(record["stop"])
                    record["stop_hit"] = 1
                    record["R"] = -1.0
                    record["done"] = True
                    active.remove(index)

    if active:
        raise RuntimeError(f"raw M1 ended with {len(active)} active FAST-k2 releases")
    release = pd.DataFrame(records)
    return release[[
        "decision_ts", "eligible", "guard_touched", "valid", "entry_time",
        "entry", "exit_time", "exit", "stop_hit", "R", "reason",
    ]].rename(columns={column: f"k2_{column}" for column in (
        "eligible", "guard_touched", "valid", "entry_time", "entry",
        "exit_time", "exit", "stop_hit", "R", "reason",
    )})


def immediate_full(population: pd.DataFrame, policy: str = "IMMEDIATE_FULL_R7G") -> pd.DataFrame:
    frame = population.copy()
    frame["policy"] = policy
    frame["combined_R_units"] = frame["R"] * frame["r7g_weight"]
    frame["stop_child"] = frame["stop_hit"].astype(int)
    frame["stopped_units"] = frame["stop_hit"] * frame["r7g_weight"]
    frame["funded_units"] = frame["r7g_weight"].astype(float)
    frame["topup_units"] = (frame["r7g_weight"] - 1).clip(lower=0).astype(float)
    frame["topup_action"] = "IMMEDIATE"
    return finalize_ledger(frame)


def one_unit_only(population: pd.DataFrame) -> pd.DataFrame:
    frame = population.copy()
    frame["policy"] = "ONE_UNIT_ONLY"
    frame["combined_R_units"] = frame["R"]
    frame["stop_child"] = frame["stop_hit"].astype(int)
    frame["stopped_units"] = frame["stop_hit"].astype(float)
    frame["funded_units"] = 1.0
    frame["topup_units"] = 0.0
    frame["topup_action"] = "NONE"
    return finalize_ledger(frame)


def fixed_topup(population: pd.DataFrame, minute: int) -> pd.DataFrame:
    frame = population.copy()
    extra = (frame["r7g_weight"] - 1).clip(lower=0).astype(float)
    valid = frame[f"b{minute}_valid"].eq(1)
    deployed = extra * valid.astype(float)
    frame["policy"] = f"ONE_NOW_REST_{minute}M"
    frame["combined_R_units"] = frame["R"] + np.where(
        valid, deployed * frame[f"b{minute}_R"], 0.0
    )
    frame["stop_child"] = frame["stop_hit"].astype(int)
    frame["stopped_units"] = frame["stop_hit"].astype(float) + np.where(
        valid, deployed * frame[f"b{minute}_stop_hit"], 0.0
    )
    frame["funded_units"] = 1.0 + deployed
    frame["topup_units"] = deployed
    frame["topup_action"] = np.where(deployed > 0, f"TOPUP_{minute}M", "NONE")
    return finalize_ledger(frame)


def event_k2_topup(population: pd.DataFrame, release: pd.DataFrame) -> pd.DataFrame:
    frame = population.merge(release, on="decision_ts", how="left", validate="one_to_one")
    extra = (frame["r7g_weight"] - 1).clip(lower=0).astype(float)
    valid = frame["k2_valid"].eq(1)
    deployed = extra * valid.astype(float)
    frame["policy"] = "ONE_NOW_REST_FAST_K2"
    frame["combined_R_units"] = frame["R"] + np.where(valid, deployed * frame["k2_R"], 0.0)
    frame["stop_child"] = frame["stop_hit"].astype(int)
    frame["stopped_units"] = frame["stop_hit"].astype(float) + np.where(
        valid, deployed * frame["k2_stop_hit"], 0.0
    )
    frame["funded_units"] = 1.0 + deployed
    frame["topup_units"] = deployed
    frame["topup_action"] = np.where(deployed > 0, "TOPUP_FAST_K2", "NONE")
    return finalize_ledger(frame)


def split_topup(population: pd.DataFrame) -> pd.DataFrame:
    frame = population.copy()
    eligible = frame["r7g_weight"].eq(3).astype(float)
    add120 = eligible * frame["b120_valid"].eq(1).astype(float)
    add180 = eligible * frame["b180_valid"].eq(1).astype(float)
    frame["policy"] = "ONE_NOW_ONE_120M_ONE_180M"
    frame["combined_R_units"] = (
        frame["R"]
        + add120 * frame["b120_R"].fillna(0.0)
        + add180 * frame["b180_R"].fillna(0.0)
    )
    frame["stop_child"] = frame["stop_hit"].astype(int)
    frame["stopped_units"] = (
        frame["stop_hit"].astype(float)
        + add120 * frame["b120_stop_hit"].fillna(0.0)
        + add180 * frame["b180_stop_hit"].fillna(0.0)
    )
    frame["funded_units"] = 1.0 + add120 + add180
    frame["topup_units"] = add120 + add180
    frame["topup_action"] = np.select(
        [(add120 > 0) & (add180 > 0), add120 > 0, add180 > 0],
        ["TOPUP_120M_AND_180M", "TOPUP_120M", "TOPUP_180M"],
        default="NONE",
    )
    return finalize_ledger(frame)


def model_topup(
    population: pd.DataFrame,
    stage1_ledger: pd.DataFrame,
    stop_cost: float,
) -> pd.DataFrame:
    policy = stage1_ledger[
        stage1_ledger["view"].eq("V10_84_PROCESS_HEADS")
        & stage1_ledger["stop_cost"].eq(stop_cost)
        & stage1_ledger["test_year"].isin([2025, 2026])
    ][["decision", "funded_action"]].copy()
    policy["decision_ts"] = pd.to_datetime(policy["decision"])
    if policy.duplicated("decision_ts").any():
        raise RuntimeError("Stage-1 policy ledger has duplicate decisions")
    frame = population[population["year"].isin([2025, 2026])].merge(
        policy[["decision_ts", "funded_action"]], on="decision_ts", how="left", validate="one_to_one"
    )
    if frame["funded_action"].isna().any():
        raise RuntimeError("Stage-1 policy ledger did not cover all 2025-2026 selected Children")
    extra = (frame["r7g_weight"] - 1).clip(lower=0).astype(float)
    combined = frame["R"].astype(float).copy()
    stopped_units = frame["stop_hit"].astype(float).copy()
    deployed = pd.Series(0.0, index=frame.index)
    for minute in (0, 60, 120, 180):
        mask = frame["funded_action"].eq(f"FUND_{minute}") & extra.gt(0)
        r_value = frame["R"] if minute == 0 else frame[f"b{minute}_R"]
        stop_value = frame["stop_hit"] if minute == 0 else frame[f"b{minute}_stop_hit"]
        combined += np.where(mask, extra * r_value.fillna(0.0), 0.0)
        stopped_units += np.where(mask, extra * stop_value.fillna(0.0), 0.0)
        deployed += np.where(mask, extra, 0.0)
    frame["policy"] = f"ONE_NOW_MODEL_TOPUP_SC{stop_cost:.2f}"
    frame["combined_R_units"] = combined
    frame["stop_child"] = frame["stop_hit"].astype(int)
    frame["stopped_units"] = stopped_units
    frame["funded_units"] = 1.0 + deployed
    frame["topup_units"] = deployed
    frame["topup_action"] = frame["funded_action"].str.replace("FUND_", "TOPUP_", regex=False)
    frame.loc[deployed.eq(0), "topup_action"] = "NONE"
    return finalize_ledger(frame)


def finalize_ledger(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["intended_units"] = frame["r7g_weight"].astype(float)
    frame["full_ceiling_stop"] = (
        frame["stop_child"].eq(1)
        & np.isclose(frame["stopped_units"], frame["intended_units"])
    ).astype(int)
    frame["full_3unit_stop"] = (
        frame["r7g_weight"].eq(3) & frame["stopped_units"].ge(3 - 1e-9)
    ).astype(int)
    frame["partial_3unit_stop"] = (
        frame["r7g_weight"].eq(3)
        & frame["stop_child"].eq(1)
        & frame["stopped_units"].lt(3 - 1e-9)
    ).astype(int)
    frame["combined_win"] = frame["combined_R_units"].gt(0).astype(int)
    return frame


def summarize(frame: pd.DataFrame, scope: str) -> dict[str, object]:
    frame = frame.sort_values("decision_ts")
    ending, drawdown = equity_path(frame["combined_R_units"], 0.01)
    stop_streak, stop_unit_streak = max_stop_streak(frame)
    full3 = frame["full_3unit_stop"].astype(int)
    positive = frame.loc[frame["combined_R_units"].gt(0), "combined_R_units"].sort_values(ascending=False)
    l6_positive = frame.loc[frame["L"].ge(6), "combined_R_units"].clip(lower=0).sum()
    return {
        "scope": scope,
        "policy": str(frame["policy"].iloc[0]),
        "children": int(len(frame)),
        "trade_retention": 1.0,
        "hard_sl_children": int(frame["stop_child"].sum()),
        "hard_sl_child_rate": float(frame["stop_child"].mean()),
        "stopped_loss_units": float(frame["stopped_units"].sum()),
        "mean_loss_units_per_stopped_child": float(
            frame.loc[frame["stop_child"].eq(1), "stopped_units"].mean()
        ),
        "full_ceiling_stop_children": int(frame["full_ceiling_stop"].sum()),
        "full_3unit_stop_children": int(frame["full_3unit_stop"].sum()),
        "adjacent_full_3unit_stop_pairs": int(
            (full3.eq(1) & full3.shift(1).eq(1)).sum()
        ),
        "adjacent_full_3unit_stop_triplets": int(
            (full3.eq(1) & full3.shift(1).eq(1) & full3.shift(2).eq(1)).sum()
        ),
        "partial_3unit_stop_children": int(frame["partial_3unit_stop"].sum()),
        "funded_units": float(frame["funded_units"].sum()),
        "mean_funded_units_per_child": float(frame["funded_units"].mean()),
        "topup_units": float(frame["topup_units"].sum()),
        "combined_wins": int(frame["combined_win"].sum()),
        "combined_win_rate": float(frame["combined_win"].mean()),
        "combined_R_units": float(frame["combined_R_units"].sum()),
        "max_stop_child_streak": stop_streak,
        "max_adjacent_stopped_units": stop_unit_streak,
        "ending_equity_1pct_per_unit": ending,
        "max_drawdown_1pct_per_unit": drawdown,
        "L6_positive_R_units": float(l6_positive),
        "top10_positive_R_share": float(positive.head(10).sum() / positive.sum()) if positive.sum() > 0 else math.nan,
    }


def add_relative_metrics(summary: pd.DataFrame, ledgers: dict[tuple[str, str], pd.DataFrame]) -> pd.DataFrame:
    result = summary.copy()
    result["stop_unit_reduction"] = math.nan
    result["combined_R_retention"] = math.nan
    result["L6_positive_R_retention"] = math.nan
    result["equal_drawdown_risk_fraction"] = math.nan
    result["equal_drawdown_ending_equity"] = math.nan
    for scope in result["scope"].unique():
        baseline = result[
            result["scope"].eq(scope) & result["policy"].eq("IMMEDIATE_FULL_R7G")
        ].iloc[0]
        target_dd = float(baseline["max_drawdown_1pct_per_unit"])
        for index, row in result[result["scope"].eq(scope)].iterrows():
            result.loc[index, "stop_unit_reduction"] = 1.0 - row["stopped_loss_units"] / baseline["stopped_loss_units"]
            result.loc[index, "combined_R_retention"] = row["combined_R_units"] / baseline["combined_R_units"]
            result.loc[index, "L6_positive_R_retention"] = row["L6_positive_R_units"] / baseline["L6_positive_R_units"]
            values = ledgers[(scope, row["policy"])].sort_values("decision_ts")["combined_R_units"].to_numpy(dtype=float)
            risk = equal_drawdown_risk(values, target_dd)
            result.loc[index, "equal_drawdown_risk_fraction"] = risk
            result.loc[index, "equal_drawdown_ending_equity"] = equity_path(values, risk)[0] if np.isfinite(risk) else math.nan
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--episodes", type=Path, required=True)
    parser.add_argument("--stage1-ledger", type=Path, required=True)
    parser.add_argument("--m1", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    population = load_population(args.events, args.episodes)
    stage1 = pd.read_csv(args.stage1_ledger)
    k2_release = causal_fast_k2_release(args.m1, population)
    fixed_ledgers = [
        immediate_full(population), one_unit_only(population),
        fixed_topup(population, 60), fixed_topup(population, 120), fixed_topup(population, 180),
        split_topup(population), event_k2_topup(population, k2_release),
    ]
    model_ledgers = [model_topup(population, stage1, stop_cost) for stop_cost in STOP_COSTS]

    ledger_map: dict[tuple[str, str], pd.DataFrame] = {}
    summary_rows: list[dict[str, object]] = []
    slice_rows: list[dict[str, object]] = []
    all_ledgers: list[pd.DataFrame] = []
    for scope, years, candidates in (
        ("2024_2026", (2024, 2025, 2026), population),
        ("2025_2026", (2025, 2026), population[population["year"].isin([2025, 2026])]),
    ):
        scope_ledgers = [frame[frame["year"].isin(years)].copy() for frame in fixed_ledgers]
        if scope == "2025_2026":
            scope_ledgers.extend(model_ledgers)
        for frame in scope_ledgers:
            policy = str(frame["policy"].iloc[0])
            frame["scope"] = scope
            ledger_map[(scope, policy)] = frame
            all_ledgers.append(frame)
            summary_rows.append(summarize(frame, scope))
            for year, group in frame.groupby("year", sort=True):
                row = summarize(group, f"YEAR_{int(year)}")
                row["parent_scope"] = scope
                slice_rows.append(row)
            for direction, group in frame.groupby("dir", sort=True):
                row = summarize(group, "SIDE_LONG" if int(direction) > 0 else "SIDE_SHORT")
                row["parent_scope"] = scope
                slice_rows.append(row)

    summary = add_relative_metrics(pd.DataFrame(summary_rows), ledger_map)
    ledger = pd.concat(all_ledgers, ignore_index=True)
    action_counts = (
        ledger.groupby(["scope", "policy", "topup_action"], dropna=False)
        .agg(children=("signal_id", "size"), funded_units=("funded_units", "sum"), stopped_units=("stopped_units", "sum"))
        .reset_index()
    )
    quality = {
        "grain": "one selected FAST-k1 Child per policy",
        "selected_children": int(len(population)),
        "selected_by_year": {str(int(year)): int(len(group)) for year, group in population.groupby("year")},
        "r7g_ceiling_counts": {str(int(weight)): int(len(group)) for weight, group in population.groupby("r7g_weight")},
        "stage1_policy_rows": int(len(stage1)),
        "fast_k2_release": {
            "eligible": int(k2_release["k2_eligible"].sum()),
            "guard_touched_before_release": int(k2_release["k2_guard_touched"].sum()),
            "valid": int(k2_release["k2_valid"].sum()),
            "stop_hit_after_release": int(k2_release["k2_stop_hit"].fillna(0).sum()),
            "reason_counts": {
                str(reason): int(len(group))
                for reason, group in k2_release.groupby("k2_reason", dropna=False)
            },
        },
        "invariants": {
            "all_policies_keep_one_immediate_unit": bool(ledger["funded_units"].ge(1).all()),
            "funded_units_never_exceed_ceiling": bool((ledger["funded_units"] <= ledger["intended_units"] + 1e-9).all()),
            "stopped_units_never_exceed_funded": bool((ledger["stopped_units"] <= ledger["funded_units"] + 1e-9).all()),
            "hard_sl_children_identical_within_scope": bool(
                summary.groupby("scope")["hard_sl_children"].nunique().eq(1).all()
            ),
            "trade_retention_is_one": bool(summary["trade_retention"].eq(1.0).all()),
        },
        "interpretation_boundary": (
            "staging may reduce stopped loss-units and full-ceiling stops; it does not reduce "
            "the number of k1 Children touching Hard SL because one unit is always funded"
        ),
    }
    if not all(quality["invariants"].values()):
        raise RuntimeError(f"stage2 invariant failed: {quality['invariants']}")

    outputs = {
        "summary": args.out_dir / "V11_REASSEMBLY_STAGE2_STAGED_FUNDING_SUMMARY.csv",
        "slices": args.out_dir / "V11_REASSEMBLY_STAGE2_STAGED_FUNDING_SLICES.csv",
        "ledger": args.out_dir / "V11_REASSEMBLY_STAGE2_STAGED_FUNDING_LEDGER.csv",
        "actions": args.out_dir / "V11_REASSEMBLY_STAGE2_TOPUP_ACTIONS.csv",
        "quality": args.out_dir / "V11_REASSEMBLY_STAGE2_DATA_QUALITY.json",
    }
    summary.to_csv(outputs["summary"], index=False)
    pd.DataFrame(slice_rows).to_csv(outputs["slices"], index=False)
    ledger.to_csv(outputs["ledger"], index=False)
    action_counts.to_csv(outputs["actions"], index=False)
    outputs["quality"].write_text(json.dumps(quality, indent=2), encoding="utf-8")
    manifest = {
        "status": "CONSUMED_DEVELOPMENT_STAGE2_ONLY",
        "authority": "NO TRADE, WAIT, MODEL, SIZING, OR PRODUCTION AUTHORITY",
        "retained_question": "Can one-unit participation plus separately released ceiling capital improve scalable performance?",
        "fixed_topups": "60/120/180 minutes remain post-hoc mechanism probes, not rules",
        "input_sha256": {
            "events": sha256_file(args.events),
            "episodes": sha256_file(args.episodes),
            "stage1_ledger": sha256_file(args.stage1_ledger),
            "raw_m1": sha256_file(args.m1),
        },
        "output_sha256": {key: sha256_file(path) for key, path in outputs.items()},
    }
    manifest_path = args.out_dir / "V11_REASSEMBLY_STAGE2_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print("\nSTAGED FUNDING SUMMARY")
    print(summary.sort_values(["scope", "stopped_loss_units", "combined_R_units"], ascending=[True, True, False]).to_string(index=False))


if __name__ == "__main__":
    main()
