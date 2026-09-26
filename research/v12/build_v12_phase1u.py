"""Build the Phase-1U causal FAST/STD/SLOW ownership-transition diagnostic.

The experiment keeps the exact supplied MT5 V10 R7G Child population and asks
whether chronological STD/SLOW ownership memory changes the meaning of FAST
events.  It is consumed-development evidence only and has no action authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "research" / "v10"))
sys.path.insert(0, str(REPO / "research" / "v11"))

from analyze_v11_new_skeleton_phase_space import rebuild_market  # noqa: E402
from build_v10_causal_m1_universe_r3 import (  # noqa: E402
    UniverseBuilder,
    read_m1,
    sha256_file,
)


VERSION = "v12-phase1u-multispeed-ha-ownership-v1"
EXPECTED_M1 = "626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2"
EXPECTED_MT5 = "c4348a34aa35d1e9793283cebbf1a028327c10e3e1c5a4fde2a9e74e3ff801a7"
START = pd.Timestamp("2024-10-01 00:00:00")
END = pd.Timestamp("2026-08-28 12:00:00")
KEEP_STATES = {"FAST_WITH_MEMORY", "TRANSFER_CONFIRMED"}


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--m1",
        type=Path,
        default=REPO / "GOLD#_M1_202201030100_202608282357.csv",
    )
    parser.add_argument(
        "--mt5-events",
        type=Path,
        default=Path.home() / "Downloads" / "V10_R7G_full_embedded_ml_events.csv",
    )
    parser.add_argument("--contract", type=Path, default=REPO / "research/v12/v12_phase1u_contract.json")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=REPO / "output/v12_phase1u_multispeed_ha_ownership_20260926_a",
    )
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def verify(path: Path, expected: str, label: str) -> None:
    actual = sha256_file(path).lower()
    if actual != expected.lower():
        raise ValueError(f"{label} SHA256 mismatch: {actual}; expected {expected}")


def safe_output(path: Path, replace: bool) -> None:
    resolved = path.resolve()
    output_root = (REPO / "output").resolve()
    if output_root not in resolved.parents:
        raise ValueError(f"output must be beneath {output_root}: {resolved}")
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(f"output is not empty: {path}")
        for child in path.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def save_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(
        path,
        index=False,
        lineterminator="\n",
        float_format="%.12g",
        date_format="%Y-%m-%d %H:%M:%S",
    )


def save_json(value: object, path: Path) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def classify_h4(h4: pd.DataFrame) -> pd.DataFrame:
    frame = h4.sort_values("decision").reset_index(drop=True).copy()
    memory = 0
    memory_established_at = pd.NaT
    previous_fast = 0
    previous_std = 0
    previous_slow = 0
    previous_state = "MEMORY_UNAVAILABLE"
    run_k = 0
    rows: list[dict[str, object]] = []
    for source in frame.itertuples(index=False):
        fast = int(source.fast_dir)
        std = int(source.std_dir)
        slow = int(source.slow_dir)
        decision = pd.Timestamp(source.decision)
        fast_flip = int(previous_fast != 0 and fast != previous_fast)
        run_k = 1 if previous_fast == 0 or fast_flip else run_k + 1
        before = memory
        if before == 0:
            state = "MEMORY_UNAVAILABLE"
        elif fast == before:
            state = "FAST_WITH_MEMORY"
        elif std == fast and slow == fast:
            state = "TRANSFER_CONFIRMED"
        elif std == fast and slow != fast:
            state = "STD_LEADS_TRANSFER"
        elif slow == fast and std != fast:
            state = "SLOW_ONLY_CONFLICT"
        else:
            state = "FAST_ONLY_CHALLENGE"

        if state == "FAST_WITH_MEMORY":
            event_role = "RETURN_TO_MEMORY" if fast_flip else "MEMORY_CONTINUATION"
        elif state == "TRANSFER_CONFIRMED":
            event_role = "OWNERSHIP_TRANSFER_AT_DECISION"
        elif state == "STD_LEADS_TRANSFER":
            event_role = "TRANSFER_DEVELOPING"
        elif state == "FAST_ONLY_CHALLENGE":
            event_role = "COUNTERFLOW_CHALLENGE"
        elif state == "SLOW_ONLY_CONFLICT":
            event_role = "CONFLICTED_CHALLENGE"
        else:
            event_role = "MEMORY_WARMUP"

        if previous_fast == 0:
            transition_signature = "INITIAL"
        else:
            prior_std_new = int(previous_std == fast)
            prior_slow_new = int(previous_slow == fast)
            current_std_new = int(std == fast)
            current_slow_new = int(slow == fast)
            transition_signature = (
                f"{prior_std_new}{prior_slow_new}_TO_{current_std_new}{current_slow_new}"
            )

        age = (
            int((decision - pd.Timestamp(memory_established_at)) / pd.Timedelta(hours=4))
            if before != 0 and pd.notna(memory_established_at)
            else -1
        )
        if std == slow:
            if memory != std:
                memory_established_at = decision
            memory = std
        rows.append(
            {
                "h4_start": pd.Timestamp(source.h4_start),
                "decision": decision,
                "fast_dir": fast,
                "std_dir": std,
                "slow_dir": slow,
                "fast_flip": fast_flip,
                "fast_run_k": run_k,
                "previous_fast_dir": previous_fast,
                "previous_std_dir": previous_std,
                "previous_slow_dir": previous_slow,
                "previous_ownership_state": previous_state,
                "transition_signature": transition_signature,
                "memory_owner_before": before,
                "memory_age_h4_before": age,
                "ownership_state": state,
                "event_role": event_role,
                "std_slow_agree_current": int(std == slow),
                "memory_owner_after": memory,
            }
        )
        previous_fast = fast
        previous_std = std
        previous_slow = slow
        previous_state = state
    return pd.DataFrame(rows)


def build_universe(m1_path: Path) -> pd.DataFrame:
    builder = UniverseBuilder()
    read_m1(m1_path, builder)
    frame = builder.frame()
    frame["decision"] = pd.to_datetime(frame["decision"])
    frame["entry_time"] = pd.to_datetime(frame["entry_time"])
    frame["exit_time"] = pd.to_datetime(frame["exit_time"])
    frame["direction"] = np.where(frame["dir"].astype(int) > 0, "LONG", "SHORT")
    frame["stage"] = np.where(frame["k"].eq(1), "k1", np.where(frame["k"].eq(2), "k2", "k3p"))
    return frame.sort_values("decision").reset_index(drop=True)


def load_mt5(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["decision"] = pd.to_datetime(frame["decision"], format="%Y.%m.%d %H:%M")
    frame["direction"] = frame["dir"].astype(str)
    for column in ("r4_weight", "r7g_weight"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0).astype(int)
    return frame


def join_population(
    universe: pd.DataFrame, h4_state: pd.DataFrame, mt5: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, object]]:
    state_columns = [
        "decision", "fast_dir", "std_dir", "slow_dir", "fast_flip", "fast_run_k",
        "previous_fast_dir", "previous_std_dir", "previous_slow_dir",
        "previous_ownership_state", "transition_signature",
        "memory_owner_before", "memory_age_h4_before", "ownership_state", "event_role",
        "std_slow_agree_current", "memory_owner_after",
    ]
    featured = universe.merge(
        h4_state[state_columns], on="decision", how="left", validate="many_to_one"
    )
    in_window = featured.loc[featured["decision"].between(START, END)].copy()
    mt5_window = mt5.loc[mt5["decision"].between(START, END)].copy()
    mt5_columns = [
        "decision", "direction", "event", "score", "q50", "q75", "r4_weight",
        "p_stop", "mu_nonstop", "EV", "feedback_R", "r7g_weight",
    ]
    joined = in_window.merge(
        mt5_window[mt5_columns],
        on=["decision", "direction"],
        how="outer",
        indicator=True,
        validate="one_to_one",
    )
    common = joined["_merge"].eq("both")
    quality = {
        "universe_rows": int(len(universe)),
        "universe_duplicate_signal_ids": int(universe["signal_id"].duplicated().sum()),
        "universe_h4_state_missing": int(featured["ownership_state"].isna().sum()),
        "universe_fast_direction_mismatches": int(
            (featured["dir"].astype(float) != featured["fast_dir"].astype(float)).sum()
        ),
        "universe_fast_k_mismatches": int(
            (featured["k"].astype(float) != featured["fast_run_k"].astype(float)).sum()
        ),
        "economic_universe_rows": int(len(in_window)),
        "mt5_window_rows": int(len(mt5_window)),
        "joined_rows": int(common.sum()),
        "universe_only_rows": int((joined["_merge"] == "left_only").sum()),
        "mt5_only_rows": int((joined["_merge"] == "right_only").sum()),
    }
    joined = joined.loc[common].drop(columns=["_merge"]).sort_values("decision").reset_index(drop=True)
    return joined, quality


def maximum_stop_streak(frame: pd.DataFrame) -> int:
    best = current = 0
    for value in frame.sort_values("decision")["stop_hit"].astype(int):
        current = current + 1 if value else 0
        best = max(best, current)
    return best


def outcome_counts(frame: pd.DataFrame) -> dict[str, float | int]:
    ordered = frame.sort_values("decision").copy()
    stopped = ordered["stop_hit"].astype(int).eq(1)
    values = ordered["R"].astype(float)
    weights = ordered["r7g_weight"].astype(float)
    prior_stopped = stopped.shift(fill_value=False)
    prior_two = stopped.shift(1, fill_value=False) & stopped.shift(2, fill_value=False)
    alternating = stopped & prior_stopped & ordered["dir"].ne(ordered["dir"].shift())
    return {
        "children": int(len(ordered)),
        "hard_sl_children": int(stopped.sum()),
        "hard_sl_rate": float(stopped.mean()) if len(ordered) else math.nan,
        "negative_children": int(values.lt(0).sum()),
        "positive_children": int(values.gt(0).sum()),
        "win_rate": float(values.gt(0).mean()) if len(ordered) else math.nan,
        "positive_lt1r": int(((values > 0) & (values < 1)).sum()),
        "positive_1_to_3r": int(((values >= 1) & (values < 3)).sum()),
        "positive_3_to_5r": int(((values >= 3) & (values < 5)).sum()),
        "positive_ge3r": int(values.ge(3).sum()),
        "positive_ge5r": int(values.ge(5).sum()),
        "repeat_stop_children": int((stopped & prior_stopped).sum()),
        "third_plus_stop_children": int((stopped & prior_two).sum()),
        "alternating_stop_pairs": int(alternating.sum()),
        "max_stop_streak": int(maximum_stop_streak(ordered)),
        "funded_units": int(weights.sum()),
        "stopped_units": int(weights[stopped].sum()),
        "weighted_R": float((values * weights).sum()),
    }


def apply_policy(selected: pd.DataFrame, policy: str) -> pd.DataFrame:
    if policy == "V10_CONTROL":
        keep = pd.Series(True, index=selected.index)
    elif policy == "OWNERSHIP_AUTHORIZED":
        keep = selected["ownership_state"].isin(KEEP_STATES)
    elif policy == "K1_OWNERSHIP_ONLY":
        keep = selected["stage"].ne("k1") | selected["ownership_state"].isin(KEEP_STATES)
    else:
        raise ValueError(policy)
    output = selected.loc[keep].copy()
    output["policy"] = policy
    return output


def scorecards(selected: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, pd.DataFrame]]:
    policies = {
        name: apply_policy(selected, name)
        for name in ("V10_CONTROL", "OWNERSHIP_AUTHORIZED", "K1_OWNERSHIP_ONLY")
    }
    pooled = pd.DataFrame([{"policy": name, **outcome_counts(frame)} for name, frame in policies.items()])
    segments: list[dict[str, object]] = []
    for name, frame in policies.items():
        for segment_type, column in (("YEAR", "year"), ("SIDE", "direction"), ("STAGE", "stage")):
            for value, group in frame.groupby(column, sort=True):
                segments.append(
                    {
                        "policy": name,
                        "segment_type": segment_type,
                        "segment": str(value),
                        **outcome_counts(group),
                    }
                )
    return pooled, pd.DataFrame(segments), policies


def state_scorecard(frame: pd.DataFrame, population: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (stage, state), group in frame.groupby(["stage", "ownership_state"], sort=True):
        rows.append(
            {
                "population": population,
                "stage": stage,
                "ownership_state": state,
                **outcome_counts(group),
            }
        )
    for state, group in frame.groupby("ownership_state", sort=True):
        rows.append(
            {
                "population": population,
                "stage": "ALL",
                "ownership_state": state,
                **outcome_counts(group),
            }
        )
    return pd.DataFrame(rows)


def transition_scorecard(frame: pd.DataFrame, population: str) -> pd.DataFrame:
    k1 = frame.loc[frame["stage"].eq("k1")].copy()
    rows: list[dict[str, object]] = []
    for signature, group in k1.groupby("transition_signature", sort=True):
        rows.append(
            {
                "population": population,
                "transition_signature": signature,
                **outcome_counts(group),
            }
        )
    return pd.DataFrame(rows)


def removal_audit(control: pd.DataFrame, policy_frame: pd.DataFrame, policy: str) -> dict[str, object]:
    kept = set(policy_frame["signal_id"].astype(str))
    removed = control.loc[~control["signal_id"].astype(str).isin(kept)].copy()
    return {"policy": policy, **outcome_counts(removed)}


def gate_table(
    pooled: pd.DataFrame, segments: pd.DataFrame, contract: dict[str, object]
) -> tuple[pd.DataFrame, dict[str, object]]:
    indexed = pooled.set_index("policy")
    control = indexed.loc["V10_CONTROL"]
    primary = indexed.loc["OWNERSHIP_AUTHORIZED"]
    gates = contract["primary_count_gates"]
    positive_lost = int(control.positive_children - primary.positive_children)
    hard_sl_avoided = int(control.hard_sl_children - primary.hard_sl_children)
    ratio = hard_sl_avoided / max(1, positive_lost)
    year_control = segments.loc[
        (segments["policy"] == "V10_CONTROL") & (segments["segment_type"] == "YEAR")
    ].set_index("segment")
    year_primary = segments.loc[
        (segments["policy"] == "OWNERSHIP_AUTHORIZED") & (segments["segment_type"] == "YEAR")
    ].set_index("segment")
    common_years = year_control.index.intersection(year_primary.index)
    worse_years = int(
        (year_primary.loc[common_years, "hard_sl_rate"] > year_control.loc[common_years, "hard_sl_rate"] + 1e-12).sum()
    )
    side_control = segments.loc[
        (segments["policy"] == "V10_CONTROL") & (segments["segment_type"] == "SIDE")
    ].set_index("segment")
    side_primary = segments.loc[
        (segments["policy"] == "OWNERSHIP_AUTHORIZED") & (segments["segment_type"] == "SIDE")
    ].set_index("segment")
    common_sides = side_control.index.intersection(side_primary.index)
    side_ok = bool(
        (side_primary.loc[common_sides, "hard_sl_rate"] <= side_control.loc[common_sides, "hard_sl_rate"] + 1e-12).all()
    )
    metrics = {
        "hard_sl_reduction": 1.0 - primary.hard_sl_children / control.hard_sl_children,
        "positive_child_retention": primary.positive_children / control.positive_children,
        "ge3r_child_retention": primary.positive_ge3r / control.positive_ge3r,
        "ge5r_child_retention": primary.positive_ge5r / control.positive_ge5r,
        "avoided_hard_sl_per_lost_positive": ratio,
        "win_rate_delta": primary.win_rate - control.win_rate,
        "max_stop_streak_delta": int(primary.max_stop_streak - control.max_stop_streak),
        "side_hard_sl_rate_ok": side_ok,
        "years_with_worse_hard_sl_rate": worse_years,
    }
    checks = [
        ("hard_sl_reduction", metrics["hard_sl_reduction"] >= gates["hard_sl_reduction_min"]),
        ("positive_child_retention", metrics["positive_child_retention"] >= gates["positive_child_retention_min"]),
        ("ge3r_child_retention", metrics["ge3r_child_retention"] >= gates["ge3r_child_retention_min"]),
        ("ge5r_child_retention", metrics["ge5r_child_retention"] >= gates["ge5r_child_retention_min"]),
        (
            "avoided_hard_sl_per_lost_positive",
            metrics["avoided_hard_sl_per_lost_positive"] >= gates["avoided_hard_sl_per_lost_positive_min"],
        ),
        ("win_rate_not_worse", metrics["win_rate_delta"] >= -1e-12),
        ("max_stop_streak_not_worse", metrics["max_stop_streak_delta"] <= 0),
        ("side_hard_sl_rate_not_worse", side_ok),
        (
            "annual_hard_sl_rate_stability",
            worse_years <= gates["maximum_years_with_worse_hard_sl_rate"],
        ),
    ]
    table = pd.DataFrame([{"gate": name, "passed": bool(value)} for name, value in checks])
    return table, metrics


def file_receipt(path: Path) -> dict[str, object]:
    return {"name": path.name, "sha256": sha256_file(path), "bytes": path.stat().st_size}


def main() -> None:
    args = cli()
    safe_output(args.out_dir, args.replace)
    verify(args.m1, EXPECTED_M1, "raw M1 prefix")
    verify(args.mt5_events, EXPECTED_MT5, "MT5 V10 event ledger")
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["contract_version"] != VERSION:
        raise ValueError("Phase-1U contract version mismatch")

    _, h4, m1_quality = rebuild_market(args.m1)
    h4_state = classify_h4(h4)
    universe = build_universe(args.m1)
    mt5 = load_mt5(args.mt5_events)
    joined, join_quality = join_population(universe, h4_state, mt5)
    selected = joined.loc[joined["r7g_weight"].astype(int) > 0].copy()

    pooled, segments, policies = scorecards(selected)
    full_state = state_scorecard(joined.assign(r7g_weight=1), "ALL_V10_WINDOW_OPPORTUNITIES")
    selected_state = state_scorecard(selected, "MT5_SELECTED")
    states = pd.concat([full_state, selected_state], ignore_index=True)
    transitions = pd.concat(
        [
            transition_scorecard(joined.assign(r7g_weight=1), "ALL_V10_WINDOW_OPPORTUNITIES"),
            transition_scorecard(selected, "MT5_SELECTED"),
        ],
        ignore_index=True,
    )
    removal = pd.DataFrame(
        [
            removal_audit(policies["V10_CONTROL"], policies[name], name)
            for name in ("OWNERSHIP_AUTHORIZED", "K1_OWNERSHIP_ONLY")
        ]
    )
    gates, gate_metrics = gate_table(pooled, segments, contract)

    quality = {
        "contract_version": VERSION,
        "raw_m1_sha256": sha256_file(args.m1),
        "mt5_event_ledger_sha256": sha256_file(args.mt5_events),
        "raw_m1": {
            key: (value.isoformat() if isinstance(value, pd.Timestamp) else value)
            for key, value in m1_quality.items()
        },
        "h4_state_rows": int(len(h4_state)),
        "h4_duplicate_decisions": int(h4_state["decision"].duplicated().sum()),
        "memory_unavailable_h4": int(h4_state["ownership_state"].eq("MEMORY_UNAVAILABLE").sum()),
        **join_quality,
        "selected_children": int(len(selected)),
        "selected_duplicate_signal_ids": int(selected["signal_id"].duplicated().sum()),
        "selected_missing_state": int(selected["ownership_state"].isna().sum()),
        "post_cutoff_price_rows_parsed": 0,
    }

    selected_path = args.out_dir / "V12_PHASE1U_CHILD_LEDGER.csv"
    h4_path = args.out_dir / "V12_PHASE1U_H4_OWNERSHIP_STATE.csv"
    pooled_path = args.out_dir / "V12_PHASE1U_POLICY_SCORECARDS.csv"
    segment_path = args.out_dir / "V12_PHASE1U_POLICY_SEGMENTS.csv"
    state_path = args.out_dir / "V12_PHASE1U_STATE_SCORECARDS.csv"
    removal_path = args.out_dir / "V12_PHASE1U_REMOVAL_AUDIT.csv"
    transition_path = args.out_dir / "V12_PHASE1U_K1_TRANSITION_SCORECARDS.csv"
    gate_path = args.out_dir / "V12_PHASE1U_GATES.csv"
    quality_path = args.out_dir / "V12_PHASE1U_DATA_QUALITY.json"
    summary_path = args.out_dir / "V12_PHASE1U_SUMMARY.json"
    manifest_path = args.out_dir / "V12_PHASE1U_MANIFEST.json"

    child_columns = [
        "signal_id", "decision", "entry_time", "exit_time", "year", "direction", "dir",
        "stage", "k", "rid", "L", "R", "stop_hit", "r7g_weight", "fast_dir", "std_dir",
        "slow_dir", "fast_flip", "fast_run_k", "memory_owner_before", "memory_age_h4_before",
        "previous_fast_dir", "previous_std_dir", "previous_slow_dir",
        "previous_ownership_state", "transition_signature", "ownership_state", "event_role",
        "memory_owner_after",
    ]
    save_csv(selected[child_columns], selected_path)
    save_csv(h4_state, h4_path)
    save_csv(pooled, pooled_path)
    save_csv(segments, segment_path)
    save_csv(states, state_path)
    save_csv(removal, removal_path)
    save_csv(transitions, transition_path)
    save_csv(gates, gate_path)
    save_json(quality, quality_path)
    summary = {
        "contract_version": VERSION,
        "status": "PRIMARY_PASSED_CONSUMED_GATE" if bool(gates["passed"].all()) else "PRIMARY_FAILED_CONSUMED_GATE",
        "primary_policy": "OWNERSHIP_AUTHORIZED",
        "primary_gates_passed": int(gates["passed"].sum()),
        "primary_gates_total": int(len(gates)),
        "primary_metrics": gate_metrics,
        "pooled": pooled.to_dict(orient="records"),
        "action_authority": False,
        "consumed_development_only": True,
    }
    save_json(summary, summary_path)
    outputs = [
        selected_path, h4_path, pooled_path, segment_path, state_path,
        removal_path, transition_path, gate_path, quality_path, summary_path,
    ]
    manifest = {
        "contract_version": VERSION,
        "status": summary["status"],
        "source": {
            "raw_m1_prefix": file_receipt(args.m1),
            "mt5_event_ledger": file_receipt(args.mt5_events),
            "contract": file_receipt(args.contract),
        },
        "outputs": [file_receipt(path) for path in outputs],
        "action_authority": False,
    }
    save_json(manifest, manifest_path)
    print(pooled.to_string(index=False))
    print(gates.to_string(index=False))
    print(f"Wrote {args.out_dir}")


if __name__ == "__main__":
    main()
