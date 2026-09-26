"""Build the Phase-1V entry-episode and journey-count accounting diagnostic."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
VERSION = "v12-phase1v-entry-episode-accounting-v1"
PREFIX = "V12_PHASE1V_"
POLICIES = ("V10_ENTRY_EPISODE_CONTROL", "ENTRY_OWNERSHIP_AUTHORIZED")


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs", type=Path,
        default=REPO / "output/v12_phase1i_run_episode_reverse_engineering_20260924_a/V12_PHASE1I_RUN_EPISODES.csv",
    )
    parser.add_argument(
        "--children", type=Path,
        default=REPO / "output/v12_phase1k_staged_funding_counterfactual_20260924_a/V12_PHASE1K_CHILD_POLICY_LEDGER.csv",
    )
    parser.add_argument(
        "--ownership", type=Path,
        default=REPO / "output/v12_phase1u_multispeed_ha_ownership_20260926_a/V12_PHASE1U_CHILD_LEDGER.csv",
    )
    parser.add_argument(
        "--contract", type=Path,
        default=REPO / "research/v12/v12_phase1v_contract.json",
    )
    parser.add_argument(
        "--out-dir", type=Path,
        default=REPO / "output/v12_phase1v_entry_episode_accounting_20260926_a",
    )
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(path: Path, expected: str, label: str) -> None:
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"{label} SHA256 mismatch: {actual}; expected {expected}")


def safe_output(path: Path, replace: bool) -> None:
    resolved = path.resolve()
    root = (REPO / "output").resolve()
    if root not in resolved.parents:
        raise ValueError(f"output must be beneath {root}: {resolved}")
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(path)
        for child in path.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def save_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(
        path, index=False, lineterminator="\n", float_format="%.12g",
        date_format="%Y-%m-%d %H:%M:%S",
    )


def save_json(value: object, path: Path) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def load_sources(
    runs_path: Path, children_path: Path, ownership_path: Path, cutoff: pd.Timestamp
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    runs = pd.read_csv(runs_path)
    runs["run_start"] = pd.to_datetime(runs["run_start"])
    runs["run_exit"] = pd.to_datetime(runs["run_exit"])

    children = pd.read_csv(children_path)
    children = children.loc[children["policy"].eq("BASELINE")].copy()
    children["run_start"] = pd.to_datetime(children["run_start"])
    children["entry_time"] = pd.to_datetime(children["entry_time"])

    ownership = pd.read_csv(ownership_path)
    ownership["decision"] = pd.to_datetime(ownership["decision"])

    aggregate = children.groupby("run_id", sort=False).agg(
        child_rows=("signal_id", "size"),
        child_funded_units=("funded_units", "sum"),
        child_stopped_units=("stopped_loss_units", "sum"),
        child_net_R=("combined_R_units", "sum"),
        child_tail_units=("right_tail_ge_5R_units", "sum"),
    ).reset_index()
    parity = runs.merge(aggregate, on="run_id", how="outer", indicator=True, validate="one_to_one")
    common = parity["_merge"].eq("both")
    parity_common = parity.loc[common]
    quality = {
        "source_run_rows": int(len(runs)),
        "source_baseline_child_rows": int(len(children)),
        "source_ownership_rows": int(len(ownership)),
        "run_child_left_only": int((parity["_merge"] == "left_only").sum()),
        "run_child_right_only": int((parity["_merge"] == "right_only").sum()),
        "run_child_count_mismatches": int(
            (parity_common["child_count"].astype(int) != parity_common["child_rows"].astype(int)).sum()
        ),
        "run_child_max_net_R_error": float(
            np.max(np.abs(parity_common["net_R_units"] - parity_common["child_net_R"]))
        ),
        "run_child_max_stopped_unit_error": float(
            np.max(np.abs(parity_common["stopped_units"] - parity_common["child_stopped_units"]))
        ),
        "run_child_max_tail_unit_error": float(
            np.max(np.abs(parity_common["tail_units"] - parity_common["child_tail_units"]))
        ),
    }

    common_runs = runs.loc[runs["run_start"] <= cutoff].copy()
    common_children = children.loc[children["run_id"].isin(common_runs["run_id"])].copy()
    first = common_children.loc[common_children["child_ordinal"].astype(int).eq(1)].copy()
    later = common_children.loc[common_children["child_ordinal"].astype(int).gt(1)].copy()
    first_columns = [
        "run_id", "signal_id", "entry_time", "combined_R_units",
        "stopped_loss_units", "funded_units", "right_tail_ge_5R_units",
    ]
    first = first[first_columns].rename(columns={
        "signal_id": "first_child_signal_id",
        "entry_time": "first_child_entry_time",
        "combined_R_units": "first_child_R",
        "stopped_loss_units": "first_child_stopped_units",
        "funded_units": "first_child_funded_units",
        "right_tail_ge_5R_units": "first_child_tail_units",
    })
    later_agg = later.groupby("run_id", sort=False).agg(
        later_child_count=("signal_id", "size"),
        later_child_R=("combined_R_units", "sum"),
        later_child_stopped_units=("stopped_loss_units", "sum"),
        later_child_funded_units=("funded_units", "sum"),
        later_child_tail_units=("right_tail_ge_5R_units", "sum"),
    ).reset_index()

    state_columns = [
        "signal_id", "decision", "direction", "stage", "k", "ownership_state",
        "event_role", "transition_signature", "fast_dir", "std_dir", "slow_dir",
        "memory_owner_before", "memory_age_h4_before",
    ]
    ownership_state = ownership[state_columns].rename(columns={"direction": "state_direction"})
    first = first.merge(
        ownership_state, left_on="first_child_signal_id", right_on="signal_id",
        how="left", validate="one_to_one",
    ).drop(columns=["signal_id"])
    episodes = common_runs.merge(first, on="run_id", how="left", validate="one_to_one")
    episodes = episodes.merge(later_agg, on="run_id", how="left", validate="one_to_one")
    fill_zero = [
        "later_child_count", "later_child_R", "later_child_stopped_units",
        "later_child_funded_units", "later_child_tail_units",
    ]
    episodes[fill_zero] = episodes[fill_zero].fillna(0)
    episodes["year"] = episodes["run_start"].dt.year.astype(int)
    episodes["first_child_hard_sl"] = episodes["first_child_stopped_units"].gt(0).astype(int)
    episodes["positive_episode"] = episodes["net_R_units"].gt(0).astype(int)
    episodes["negative_episode"] = episodes["net_R_units"].lt(0).astype(int)
    episodes["tail_episode"] = episodes["tail_units"].gt(0).astype(int)
    episodes["episode_count_score"] = np.sign(episodes["net_R_units"]).astype(int)
    episodes["non_tail_count_score"] = np.where(
        episodes["tail_episode"].eq(0), episodes["episode_count_score"], 0
    ).astype(int)
    episodes = episodes.sort_values(["run_start", "run_id"]).reset_index(drop=True)

    quality.update({
        "common_episode_rows": int(len(episodes)),
        "common_child_rows": int(len(common_children)),
        "common_first_child_rows": int(len(first)),
        "common_later_child_rows": int(len(later)),
        "duplicate_common_run_ids": int(episodes["run_id"].duplicated().sum()),
        "duplicate_first_child_signal_ids": int(first["first_child_signal_id"].duplicated().sum()),
        "missing_first_child": int(episodes["first_child_signal_id"].isna().sum()),
        "missing_ownership_state": int(episodes["ownership_state"].isna().sum()),
        "first_signal_id_mismatches": int(
            episodes["first_signal_id"].astype(str).ne(episodes["first_child_signal_id"].astype(str)).sum()
        ),
        "first_entry_decision_mismatches": int(
            episodes["run_start"].ne(episodes["decision"]).sum()
        ),
        "direction_mismatches": int(
            episodes["direction"].astype(str).ne(episodes["state_direction"].astype(str)).sum()
        ),
        "episode_decomposition_max_R_error": float(np.max(np.abs(
            episodes["net_R_units"] - episodes["first_child_R"] - episodes["later_child_R"]
        ))),
        "episode_decomposition_max_stop_error": float(np.max(np.abs(
            episodes["stopped_units"] - episodes["first_child_stopped_units"]
            - episodes["later_child_stopped_units"]
        ))),
        "excluded_post_common_window_episode_rows": int((runs["run_start"] > cutoff).sum()),
    })
    return episodes, common_children, quality


def annotate_policy_sequence(frame: pd.DataFrame) -> pd.DataFrame:
    ordered = frame.sort_values(["run_start", "run_id"]).reset_index(drop=True).copy()
    prior_stop = ordered["first_child_hard_sl"].shift(fill_value=0).astype(int)
    ordered["repeat_first_child_stop"] = (
        ordered["first_child_hard_sl"].eq(1) & prior_stop.eq(1)
    ).astype(int)
    ordered["alternating_repeat_first_stop"] = (
        ordered["repeat_first_child_stop"].eq(1)
        & ordered["direction"].ne(ordered["direction"].shift())
    ).astype(int)
    prior_negative = ordered["negative_episode"].shift(fill_value=0).astype(int)
    ordered["repeat_negative_episode"] = (
        ordered["negative_episode"].eq(1) & prior_negative.eq(1)
    ).astype(int)
    ordered["alternating_repeat_negative_episode"] = (
        ordered["repeat_negative_episode"].eq(1)
        & ordered["direction"].ne(ordered["direction"].shift())
    ).astype(int)
    current = best = 0
    negative_current = negative_best = 0
    streaks: list[int] = []
    negative_streaks: list[int] = []
    for stopped in ordered["first_child_hard_sl"].astype(int):
        current = current + 1 if stopped else 0
        best = max(best, current)
        streaks.append(current)
    for negative in ordered["negative_episode"].astype(int):
        negative_current = negative_current + 1 if negative else 0
        negative_best = max(negative_best, negative_current)
        negative_streaks.append(negative_current)
    ordered["first_stop_streak"] = streaks
    ordered["negative_episode_streak"] = negative_streaks
    ordered.attrs["max_first_stop_streak"] = best
    ordered.attrs["max_negative_episode_streak"] = negative_best
    ordered["cumulative_net_R"] = ordered["net_R_units"].cumsum()
    ordered["cumulative_episode_count_score"] = ordered["episode_count_score"].cumsum()
    ordered["cumulative_non_tail_count_score"] = ordered["non_tail_count_score"].cumsum()
    return ordered


def block_ledger(frame: pd.DataFrame, policy: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    block_id = 0
    buffer: list[pd.Series] = []

    def flush(ended_by_tail: bool) -> None:
        nonlocal block_id, buffer
        if not buffer:
            return
        block_id += 1
        values = pd.DataFrame(buffer)
        rows.append({
            "policy": policy,
            "block_id": block_id,
            "start": values["run_start"].min(),
            "end": values["run_start"].max(),
            "non_tail_episodes": int(len(values)),
            "positive_episodes": int(values["positive_episode"].sum()),
            "negative_episodes": int(values["negative_episode"].sum()),
            "count_score": int(values["episode_count_score"].sum()),
            "net_R": float(values["net_R_units"].sum()),
            "net_R_per_episode": float(values["net_R_units"].mean()),
            "ended_by_tail": int(ended_by_tail),
        })
        buffer = []

    for _, row in frame.sort_values(["run_start", "run_id"]).iterrows():
        if int(row["tail_episode"]) == 1:
            flush(True)
        else:
            buffer.append(row)
    flush(False)
    return pd.DataFrame(rows)


def episode_summary(frame: pd.DataFrame) -> dict[str, float | int]:
    sequenced = annotate_policy_sequence(frame)
    episodes = len(sequenced)
    non_tail = sequenced.loc[sequenced["tail_episode"].eq(0)]
    first_stops = int(sequenced["first_child_hard_sl"].sum())
    positive = int(sequenced["positive_episode"].sum())
    negative = int(sequenced["negative_episode"].sum())
    return {
        "episodes": int(episodes),
        "first_child_hard_sl_episodes": first_stops,
        "first_child_hard_sl_rate": first_stops / episodes if episodes else math.nan,
        "repeat_first_child_stop_episodes": int(sequenced["repeat_first_child_stop"].sum()),
        "alternating_repeat_first_stop_episodes": int(
            sequenced["alternating_repeat_first_stop"].sum()
        ),
        "max_first_stop_streak": int(sequenced.attrs["max_first_stop_streak"]),
        "repeat_negative_episodes": int(sequenced["repeat_negative_episode"].sum()),
        "alternating_repeat_negative_episodes": int(
            sequenced["alternating_repeat_negative_episode"].sum()
        ),
        "max_negative_episode_streak": int(sequenced.attrs["max_negative_episode_streak"]),
        "positive_episodes": positive,
        "negative_episodes": negative,
        "zero_episodes": int(episodes - positive - negative),
        "episode_win_rate": positive / episodes if episodes else math.nan,
        "tail_episodes": int(sequenced["tail_episode"].sum()),
        "episode_count_balance": int(sequenced["episode_count_score"].sum()),
        "episode_count_slope": float(sequenced["episode_count_score"].mean()) if episodes else math.nan,
        "non_tail_episodes": int(len(non_tail)),
        "non_tail_positive_episodes": int(non_tail["positive_episode"].sum()),
        "non_tail_negative_episodes": int(non_tail["negative_episode"].sum()),
        "non_tail_count_balance": int(non_tail["episode_count_score"].sum()),
        "non_tail_count_slope": float(non_tail["episode_count_score"].mean()) if len(non_tail) else math.nan,
        "non_tail_net_R": float(non_tail["net_R_units"].sum()),
        "non_tail_net_R_per_episode": float(non_tail["net_R_units"].mean()) if len(non_tail) else math.nan,
        "first_child_stopped_units": float(sequenced["first_child_stopped_units"].sum()),
        "later_child_stopped_units": float(sequenced["later_child_stopped_units"].sum()),
        "first_child_R": float(sequenced["first_child_R"].sum()),
        "later_child_R": float(sequenced["later_child_R"].sum()),
        "funded_units": float(sequenced["funded_units"].sum()),
        "stopped_units": float(sequenced["stopped_units"].sum()),
        "net_R_units": float(sequenced["net_R_units"].sum()),
        "tail_units": float(sequenced["tail_units"].sum()),
    }


def apply_policy(episodes: pd.DataFrame, policy: str, admit_states: set[str]) -> pd.DataFrame:
    if policy == "V10_ENTRY_EPISODE_CONTROL":
        keep = pd.Series(True, index=episodes.index)
    elif policy == "ENTRY_OWNERSHIP_AUTHORIZED":
        keep = episodes["ownership_state"].isin(admit_states)
    else:
        raise ValueError(policy)
    output = episodes.loc[keep].copy()
    output["policy"] = policy
    return annotate_policy_sequence(output)


def build_scorecards(
    policies: dict[str, pd.DataFrame]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    pooled = pd.DataFrame([
        {"policy": name, **episode_summary(frame)} for name, frame in policies.items()
    ])
    segments: list[dict[str, object]] = []
    for name, frame in policies.items():
        for segment_type, column in (("YEAR", "year"), ("SIDE", "direction")):
            for value, group in frame.groupby(column, sort=True):
                segments.append({
                    "policy": name,
                    "segment_type": segment_type,
                    "segment": str(value),
                    **episode_summary(group),
                })
    blocks = pd.concat(
        [block_ledger(frame, name) for name, frame in policies.items()], ignore_index=True
    )
    return pooled, pd.DataFrame(segments), blocks


def gate_table(
    scorecards: pd.DataFrame, segments: pd.DataFrame, contract: dict[str, object]
) -> tuple[pd.DataFrame, dict[str, object]]:
    cards = scorecards.set_index("policy")
    control = cards.loc["V10_ENTRY_EPISODE_CONTROL"]
    primary = cards.loc["ENTRY_OWNERSHIP_AUTHORIZED"]
    spec = contract["primary_gates"]
    stops_saved = int(control.first_child_hard_sl_episodes - primary.first_child_hard_sl_episodes)
    positive_lost = int(control.positive_episodes - primary.positive_episodes)
    metrics: dict[str, object] = {
        "first_child_hard_sl_reduction": 1.0 - (
            primary.first_child_hard_sl_episodes / control.first_child_hard_sl_episodes
        ),
        "repeat_first_stop_reduction": 1.0 - (
            primary.repeat_first_child_stop_episodes / control.repeat_first_child_stop_episodes
        ),
        "positive_episode_retention": primary.positive_episodes / control.positive_episodes,
        "tail_episode_retention": primary.tail_episodes / control.tail_episodes,
        "avoided_first_stops_per_lost_positive_episode": stops_saved / max(1, positive_lost),
        "episode_win_rate_delta": primary.episode_win_rate - control.episode_win_rate,
        "max_first_stop_streak_delta": int(
            primary.max_first_stop_streak - control.max_first_stop_streak
        ),
        "non_tail_count_slope": float(primary.non_tail_count_slope),
    }
    side_control = segments.loc[
        (segments["policy"] == "V10_ENTRY_EPISODE_CONTROL")
        & (segments["segment_type"] == "SIDE")
    ].set_index("segment")
    side_primary = segments.loc[
        (segments["policy"] == "ENTRY_OWNERSHIP_AUTHORIZED")
        & (segments["segment_type"] == "SIDE")
    ].set_index("segment")
    common_sides = side_control.index.intersection(side_primary.index)
    side_ok = bool((
        side_primary.loc[common_sides, "first_child_hard_sl_rate"]
        <= side_control.loc[common_sides, "first_child_hard_sl_rate"] + 1e-12
    ).all())
    year_control = segments.loc[
        (segments["policy"] == "V10_ENTRY_EPISODE_CONTROL")
        & (segments["segment_type"] == "YEAR")
    ].set_index("segment")
    year_primary = segments.loc[
        (segments["policy"] == "ENTRY_OWNERSHIP_AUTHORIZED")
        & (segments["segment_type"] == "YEAR")
    ].set_index("segment")
    common_years = year_control.index.intersection(year_primary.index)
    worse_years = int((
        year_primary.loc[common_years, "first_child_hard_sl_rate"]
        > year_control.loc[common_years, "first_child_hard_sl_rate"] + 1e-12
    ).sum())
    metrics["side_first_stop_rate_ok"] = side_ok
    metrics["years_with_worse_first_stop_rate"] = worse_years
    checks = [
        ("first_child_hard_sl_reduction", metrics["first_child_hard_sl_reduction"]
         >= spec["first_child_hard_sl_reduction_min"]),
        ("repeat_first_stop_reduction", metrics["repeat_first_stop_reduction"]
         >= spec["repeat_first_stop_reduction_min"]),
        ("positive_episode_retention", metrics["positive_episode_retention"]
         >= spec["positive_episode_retention_min"]),
        ("tail_episode_retention", metrics["tail_episode_retention"]
         >= spec["tail_episode_retention_min"]),
        ("avoided_first_stops_per_lost_positive_episode",
         metrics["avoided_first_stops_per_lost_positive_episode"]
         >= spec["avoided_first_stops_per_lost_positive_episode_min"]),
        ("episode_win_rate_improves", metrics["episode_win_rate_delta"] > 0),
        ("max_first_stop_streak_not_worse", metrics["max_first_stop_streak_delta"] <= 0),
        ("non_tail_count_curve_positive", metrics["non_tail_count_slope"] > 0),
        ("side_first_stop_rate_not_worse", side_ok),
        ("annual_first_stop_rate_stability",
         worse_years <= spec["maximum_years_with_worse_first_stop_rate"]),
    ]
    return pd.DataFrame([{"gate": name, "passed": bool(value)} for name, value in checks]), metrics


def state_scorecards(episodes: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for state, group in episodes.groupby("ownership_state", sort=True):
        rows.append({"ownership_state": state, **episode_summary(group)})
    return pd.DataFrame(rows)


def outcome_role_scorecards(episodes: pd.DataFrame) -> pd.DataFrame:
    frame = episodes.copy()
    frame["start_outcome_role"] = np.select(
        [
            frame["first_child_hard_sl"].eq(1) & frame["positive_episode"].eq(1),
            frame["first_child_hard_sl"].eq(1) & frame["negative_episode"].eq(1),
            frame["first_child_hard_sl"].eq(0) & frame["positive_episode"].eq(1),
            frame["first_child_hard_sl"].eq(0) & frame["negative_episode"].eq(1),
        ],
        [
            "FIRST_STOP_EPISODE_RECOVERED_POSITIVE",
            "FIRST_STOP_EPISODE_NEGATIVE",
            "NO_FIRST_STOP_EPISODE_POSITIVE",
            "NO_FIRST_STOP_EPISODE_NEGATIVE",
        ],
        default="ZERO_EPISODE",
    )
    frame["management_role"] = np.select(
        [
            frame["first_child_R"].gt(0) & frame["negative_episode"].eq(1),
            frame["first_child_R"].le(0) & frame["positive_episode"].eq(1),
        ],
        ["POSITIVE_FIRST_CHILD_LATE_DAMAGE", "NONPOSITIVE_FIRST_CHILD_LATER_RECOVERY"],
        default="SAME_SIGN_OR_UNCHANGED",
    )
    rows: list[dict[str, object]] = []
    for grouping, column in (
        ("START_OUTCOME_ROLE", "start_outcome_role"),
        ("MANAGEMENT_ROLE", "management_role"),
    ):
        for value, group in frame.groupby(column, sort=True):
            rows.append({"grouping": grouping, "role": value, **episode_summary(group)})
    return pd.DataFrame(rows)


def file_receipt(path: Path) -> dict[str, object]:
    return {"name": path.name, "sha256": sha256_file(path), "bytes": path.stat().st_size}


def main() -> None:
    args = cli()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["contract_version"] != VERSION:
        raise ValueError("Phase-1V contract version mismatch")
    hashes = contract["source_hashes"]
    verify(args.runs, hashes["phase1i_run_episodes_sha256"], "Phase-1I run episodes")
    verify(args.children, hashes["phase1k_child_policy_ledger_sha256"], "Phase-1K Child ledger")
    verify(args.ownership, hashes["phase1u_child_ledger_sha256"], "Phase-1U ownership ledger")
    safe_output(args.out_dir, args.replace)

    cutoff = pd.Timestamp(contract["common_window_end_inclusive"])
    episodes, _, quality = load_sources(args.runs, args.children, args.ownership, cutoff)
    admit_states = set(contract["first_entry_policy"]["admit_states"])
    policies = {name: apply_policy(episodes, name, admit_states) for name in POLICIES}
    pooled, segments, blocks = build_scorecards(policies)
    states = state_scorecards(episodes)
    outcome_roles = outcome_role_scorecards(episodes)
    gates, metrics = gate_table(pooled, segments, contract)
    policy_ledger = pd.concat(
        [frame.assign(policy=name) for name, frame in policies.items()], ignore_index=True
    )

    episode_path = args.out_dir / f"{PREFIX}ENTRY_EPISODES.csv"
    policy_path = args.out_dir / f"{PREFIX}POLICY_LEDGER.csv"
    score_path = args.out_dir / f"{PREFIX}POLICY_SCORECARDS.csv"
    segment_path = args.out_dir / f"{PREFIX}POLICY_SEGMENTS.csv"
    state_path = args.out_dir / f"{PREFIX}STATE_SCORECARDS.csv"
    outcome_role_path = args.out_dir / f"{PREFIX}OUTCOME_ROLE_SCORECARDS.csv"
    block_path = args.out_dir / f"{PREFIX}INTER_TAIL_BLOCKS.csv"
    gate_path = args.out_dir / f"{PREFIX}GATES.csv"
    quality_path = args.out_dir / f"{PREFIX}DATA_QUALITY.json"
    summary_path = args.out_dir / f"{PREFIX}SUMMARY.json"
    manifest_path = args.out_dir / f"{PREFIX}MANIFEST.json"

    save_csv(episodes, episode_path)
    save_csv(policy_ledger, policy_path)
    save_csv(pooled, score_path)
    save_csv(segments, segment_path)
    save_csv(states, state_path)
    save_csv(outcome_roles, outcome_role_path)
    save_csv(blocks, block_path)
    save_csv(gates, gate_path)
    quality.update({
        "contract_version": VERSION,
        "source_hashes": hashes,
        "post_common_window_raw_market_rows_parsed": 0,
    })
    save_json(quality, quality_path)
    summary = {
        "action_authority": False,
        "consumed_development_only": True,
        "contract_version": VERSION,
        "primary_gates_passed": int(gates["passed"].sum()),
        "primary_gates_total": int(len(gates)),
        "primary_metrics": metrics,
        "status": "PRIMARY_PASSED_CONSUMED_GATE" if bool(gates["passed"].all())
        else "PRIMARY_FAILED_CONSUMED_GATE",
        "scorecards": pooled.to_dict(orient="records"),
        "unit_caveat": contract["unit_caveat"],
    }
    save_json(summary, summary_path)
    outputs = [
        episode_path, policy_path, score_path, segment_path, state_path, outcome_role_path,
        block_path, gate_path, quality_path, summary_path,
    ]
    manifest = {
        "action_authority": False,
        "contract_version": VERSION,
        "outputs": [file_receipt(path) for path in outputs],
        "source": {
            "contract": file_receipt(args.contract),
            "phase1i_run_episodes": file_receipt(args.runs),
            "phase1k_child_ledger": file_receipt(args.children),
            "phase1u_ownership_ledger": file_receipt(args.ownership),
        },
        "status": summary["status"],
    }
    save_json(manifest, manifest_path)
    print(pooled.to_string(index=False))
    print(gates.to_string(index=False))
    print(f"Wrote {args.out_dir}")


if __name__ == "__main__":
    main()
