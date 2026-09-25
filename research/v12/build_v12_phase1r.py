"""Build the frozen V12 Phase-1R causal full-history M30/V10 comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_v12_phase1o import ablations, fit_head
from v12_phase0_core import sha256_file
from v12_phase1o_core import add_causal_history, train_risk_threshold


VERSION = "v12-phase1r-full-history-m30-v10-comparison-v1"
PREFIX = "V12_PHASE1R_"


def safe_output(path: Path, replace: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(f"output is not empty: {path}")
        for child in path.iterdir():
            if not child.is_file() or not child.name.startswith(PREFIX):
                raise ValueError(f"refusing to replace unexpected output: {child}")
            child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def verify(path: Path, expected: str, label: str) -> None:
    actual = sha256_file(path)
    if actual.lower() != expected.lower():
        raise ValueError(f"{label} hash mismatch: {actual}")


def max_stop_streak(frame: pd.DataFrame) -> int:
    best = current = 0
    for stopped in frame.sort_values(["decision_time", "signal_id"])["stop_hit"].astype(int):
        current = current + 1 if stopped else 0
        best = max(best, current)
    return best


def realized_drawdown(frame: pd.DataFrame) -> float:
    if frame.empty:
        return 0.0
    grouped = frame.groupby("exit_time", sort=True)["return_units"].sum()
    equity = grouped.cumsum()
    running_high = np.maximum.accumulate(np.r_[0.0, equity.to_numpy(float)])
    path = np.r_[0.0, equity.to_numpy(float)]
    return float(np.max(running_high - path))


def score(frame: pd.DataFrame, strategy: str, scope: str) -> dict[str, object]:
    values = frame.copy()
    returns = pd.to_numeric(values["return_units"], errors="raise")
    funded = pd.to_numeric(values["funded_units"], errors="raise")
    stopped = pd.to_numeric(values["stopped_units"], errors="raise")
    gross_profit = float(returns.loc[returns > 0].sum())
    gross_loss = -float(returns.loc[returns < 0].sum())
    tail = returns.where(pd.to_numeric(values["R"], errors="raise") >= 5, 0.0)
    units = float(funded.sum())
    return {
        "strategy": strategy,
        "scope": scope,
        "start": values["entry_time"].min().isoformat() if len(values) else "",
        "end": values["entry_time"].max().isoformat() if len(values) else "",
        "children": int(len(values)),
        "funded_units": units,
        "stopped_children": int(values["stop_hit"].astype(int).sum()),
        "stopped_units": float(stopped.sum()),
        "stopped_units_per_100": float(stopped.sum() / units * 100.0) if units else np.nan,
        "win_rate": float((returns > 0).mean()) if len(values) else np.nan,
        "net_R": float(returns.sum()),
        "R_per_100_funded": float(returns.sum() / units * 100.0) if units else np.nan,
        "profit_factor_R": gross_profit / gross_loss if gross_loss else np.nan,
        "max_drawdown_R": realized_drawdown(values),
        "max_stop_streak": max_stop_streak(values),
        "tail_ge5_R_units": float(tail.sum()),
    }


def normalized_rows(m30: dict, v10: dict, scope: str) -> list[dict[str, object]]:
    funded_scale = v10["funded_units"] / m30["funded_units"]
    stop_scale = v10["stopped_units"] / m30["stopped_units"]
    return [
        {
            "scope": scope,
            "normalization": "NATIVE",
            "m30_scale": 1.0,
            "m30_net_R": m30["net_R"],
            "m30_stopped_units": m30["stopped_units"],
            "m30_funded_units": m30["funded_units"],
            "v10_net_R": v10["net_R"],
            "v10_stopped_units": v10["stopped_units"],
            "v10_funded_units": v10["funded_units"],
        },
        {
            "scope": scope,
            "normalization": "EQUAL_V10_FUNDED_UNITS",
            "m30_scale": funded_scale,
            "m30_net_R": m30["net_R"] * funded_scale,
            "m30_stopped_units": m30["stopped_units"] * funded_scale,
            "m30_funded_units": v10["funded_units"],
            "v10_net_R": v10["net_R"],
            "v10_stopped_units": v10["stopped_units"],
            "v10_funded_units": v10["funded_units"],
        },
        {
            "scope": scope,
            "normalization": "EQUAL_V10_STOPPED_UNITS",
            "m30_scale": stop_scale,
            "m30_net_R": m30["net_R"] * stop_scale,
            "m30_stopped_units": v10["stopped_units"],
            "m30_funded_units": m30["funded_units"] * stop_scale,
            "v10_net_R": v10["net_R"],
            "v10_stopped_units": v10["stopped_units"],
            "v10_funded_units": v10["funded_units"],
        },
    ]


def save_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, lineterminator="\n")


def write_json(value: object, path: Path) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=repo / "research/v12/v12_phase1r_contract.json")
    parser.add_argument("--m30-ledger", type=Path, default=repo / "output/v12_phase1p_intermediate_clock_boundary_20260925_a/V12_PHASE1P_M30_K1_ENRICHED_LEDGER.csv")
    parser.add_argument("--v10-ledger", type=Path, default=repo / "output/v11_reassembly_stage3_20260923/V11_REASSEMBLY_STAGE3_CHILD_LEDGER.csv")
    parser.add_argument("--output", type=Path, default=repo / "output/v12_phase1r_full_history_m30_v10_comparison_20260925_a")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["contract_version"] != VERSION:
        raise ValueError("contract version mismatch")
    verify(args.m30_ledger, contract["source_hashes"]["phase1p_m30_enriched_ledger_sha256"], "M30 ledger")
    verify(args.v10_ledger, contract["source_hashes"]["v10_r7g_comparator_ledger_sha256"], "V10 ledger")
    safe_output(args.output, args.replace)

    m30 = pd.read_csv(args.m30_ledger, low_memory=False)
    for column in ("decision_time", "entry_time", "exit_time", "label_available_at"):
        m30[column] = pd.to_datetime(m30[column])
    m30 = add_causal_history(m30)
    algorithm, numeric, categorical = ablations(m30)[contract["m30_policy"]["model"]]
    if algorithm != "HGB":
        raise ValueError("frozen model must be HGB")
    cohort = m30.loc[m30["after_stop_cohort"] == 1].copy()

    prediction_parts = []
    excluded_ids: set[str] = set()
    for fold in contract["outer_walk_forward_folds"]:
        train_end = pd.Timestamp(fold["train_end"])
        test_start = pd.Timestamp(fold["test_start"])
        test_end = pd.Timestamp(fold["test_end"])
        train = cohort.loc[(cohort["decision_time"] <= train_end) & (cohort["label_available_at"] <= train_end)]
        test = cohort.loc[cohort["decision_time"].between(test_start, test_end)].copy()
        p_train, p_test = fit_head(train, test, numeric, categorical, "stop_hit", algorithm, "M30_K1", contract)
        threshold = train_risk_threshold(p_train)
        local = test[["signal_id", "decision_time", "label_available_at", "direction", "R", "stop_hit"]].copy()
        local.insert(0, "fold", fold["fold"])
        local["train_rows"] = len(train)
        local["p_repeat_stop"] = p_test
        local["train_top_risk_threshold"] = threshold
        local["excluded_high_repeat_risk"] = (local["p_repeat_stop"] >= threshold).astype(int)
        excluded_ids.update(local.loc[local["excluded_high_repeat_risk"] == 1, "signal_id"])
        prediction_parts.append(local)

    predictions = pd.concat(prediction_parts, ignore_index=True)
    m30["policy_allowed"] = (~m30["signal_id"].isin(excluded_ids)).astype(int)
    if int(m30.loc[m30["decision_time"].dt.year == 2022, "policy_allowed"].min()) != 1:
        raise AssertionError("warmup candidates must all be allowed")

    def m30_economic(frame: pd.DataFrame) -> pd.DataFrame:
        out = frame.copy()
        out["return_units"] = pd.to_numeric(out["R"], errors="raise")
        out["funded_units"] = 1.0
        out["stopped_units"] = out["stop_hit"].astype(float)
        return out

    v10 = pd.read_csv(args.v10_ledger, low_memory=False)
    v10 = v10.loc[v10["policy"] == contract["v10_comparator"]["policy"]].copy()
    v10 = v10.rename(columns={"decision_ts": "decision_time"})
    for column in ("decision_time", "entry_time", "exit_time"):
        v10[column] = pd.to_datetime(v10[column])
    v10["direction"] = np.where(pd.to_numeric(v10["dir"]) > 0, "LONG", "SHORT")
    v10["return_units"] = pd.to_numeric(v10["combined_R_units"], errors="raise")
    v10["stopped_units"] = pd.to_numeric(v10["stopped_loss_units"], errors="raise")
    v10["funded_units"] = pd.to_numeric(v10["funded_units"], errors="raise")

    full_base = m30_economic(m30)
    full_policy = m30_economic(m30.loc[m30["policy_allowed"] == 1])
    start = pd.Timestamp(contract["v10_comparator"]["matched_start"])
    end = pd.Timestamp(contract["v10_comparator"]["matched_end"])
    matched_base = full_base.loc[full_base["entry_time"].between(start, end)]
    matched_policy = full_policy.loc[full_policy["entry_time"].between(start, end)]
    matched_v10 = v10.loc[v10["entry_time"].between(start, end)]

    score_rows = [
        score(full_base, "M30_K1_BASELINE", "FULL_M30_HISTORY"),
        score(full_policy, "M30_SESSION_PATH_CAUSAL", "FULL_M30_HISTORY"),
        score(matched_base, "M30_K1_BASELINE", "MATCHED_V10_WINDOW"),
        score(matched_policy, "M30_SESSION_PATH_CAUSAL", "MATCHED_V10_WINDOW"),
        score(matched_v10, "V10_R7G_ACTUAL_UNITS", "MATCHED_V10_WINDOW"),
    ]
    scorecards = pd.DataFrame(score_rows)
    matched_m30_score = score_rows[3]
    matched_v10_score = score_rows[4]
    normalized = pd.DataFrame(normalized_rows(matched_m30_score, matched_v10_score, "MATCHED_V10_WINDOW"))

    annual_rows = []
    for year in range(2022, 2027):
        for strategy, frame in (("M30_K1_BASELINE", full_base), ("M30_SESSION_PATH_CAUSAL", full_policy)):
            annual_rows.append(score(frame.loc[frame["entry_time"].dt.year == year], strategy, str(year)))
    for year in sorted(v10["entry_time"].dt.year.unique()):
        annual_rows.append(score(v10.loc[v10["entry_time"].dt.year == year], "V10_R7G_ACTUAL_UNITS", str(year)))
    annual = pd.DataFrame(annual_rows)

    tested = predictions
    repeat_stops = int(tested["stop_hit"].sum())
    removed_repeat_stops = int(tested.loc[tested["excluded_high_repeat_risk"] == 1, "stop_hit"].sum())
    summary = {
        "contract_version": VERSION,
        "m30_candidates": int(len(m30)),
        "m30_after_stop_candidates": int(len(cohort)),
        "m30_causal_test_after_stop_candidates": int(len(tested)),
        "excluded_test_after_stop_candidates": int(tested["excluded_high_repeat_risk"].sum()),
        "causal_test_repeat_stops": repeat_stops,
        "removed_repeat_stops": removed_repeat_stops,
        "repeat_stop_removal_rate": removed_repeat_stops / repeat_stops if repeat_stops else None,
        "v10_children": int(len(v10)),
        "matched_window": {"start": start.isoformat(), "end": end.isoformat()},
        "trade_authority": False,
        "sizing_authority": False,
    }

    save_csv(predictions, args.output / f"{PREFIX}M30_CAUSAL_PREDICTIONS.csv")
    save_csv(scorecards, args.output / f"{PREFIX}SCORECARDS.csv")
    save_csv(normalized, args.output / f"{PREFIX}NORMALIZED_COMPARISON.csv")
    save_csv(annual, args.output / f"{PREFIX}YEAR_SCORECARDS.csv")
    write_json(summary, args.output / f"{PREFIX}SUMMARY.json")
    manifest = {}
    for path in sorted(args.output.glob(f"{PREFIX}*")):
        manifest[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    write_json(manifest, args.output / f"{PREFIX}RELEASE_MANIFEST.json")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
