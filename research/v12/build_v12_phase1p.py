#!/usr/bin/env python3
"""Build the frozen V12 Phase-1P H2/M30 intermediate-clock audit."""

from __future__ import annotations

import argparse
from collections import deque
from datetime import timedelta
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from build_v12_phase0 import PrefixAudit, iter_m1_prefix, parse_cutoff
from build_v12_phase1d import build_clusters, load_calendar, load_market, write_json
from build_v12_phase1g import EventIndex
from build_v12_phase1n import (
    Aggregator, add_event_features, add_static_and_clock, attach_parent, causal_scale,
    current_ha_features, higher_features, path_enrich, predict_ha, subset_records,
)
from build_v12_phase1o import evaluate_gates, run_population
from build_v12_phase1l import LaneEngine
from v12_phase0_core import sha256_file
from v12_phase1g_core import MarketIndex, daily_prior_medians, generate_boxes
from v12_phase1l_core import HAStream
from v12_phase1n_core import micro_path_features, wave_distribution_features
from v12_phase1o_core import policy_metrics


PREFIX = "V12_PHASE1P_"
CONTRACT_VERSION = "v12-phase1p-intermediate-clock-boundary-v1"


def safe_output(path: Path, replace: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(path)
        for child in path.iterdir():
            if not child.is_file() or not child.name.startswith(PREFIX):
                raise ValueError(f"refusing to replace unexpected output: {child}")
            child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def verify(path: Path, expected: str, label: str) -> None:
    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(f"{label} hash mismatch: {observed} != {expected}")


def build_ledgers(m1_path: Path, cutoff) -> tuple[dict[str, pd.DataFrame], PrefixAudit]:
    audit = PrefixAudit()
    aggregators = {minutes: Aggregator(minutes) for minutes in (5, 30, 60, 120, 240)}
    m5 = HAStream(2.0, 0.25)
    h4 = LaneEngine("H4", 240)
    h1 = LaneEngine("H1", 60)
    h2 = LaneEngine("H2", 120)
    m30 = LaneEngine("M30", 30)
    recent_m1: deque[SimpleNamespace] = deque(maxlen=180)
    for number, row in enumerate(iter_m1_prefix(m1_path, cutoff, audit=audit), 1):
        recent_m1.append(SimpleNamespace(
            start=row.timestamp, raw_open=row.open, raw_high=row.high, raw_low=row.low, raw_close=row.close,
        ))
        completed = {minutes: agg.push(row.timestamp, row.open, row.high, row.low, row.close)
                     for minutes, agg in aggregators.items()}
        if completed[5] is not None:
            m5.append(completed[5])
        if completed[240] is not None:
            h4.on_complete(completed[240], row.timestamp, row.open, row.high, row.low)
        if completed[60] is not None:
            h1.on_complete(completed[60], row.timestamp, row.open, row.high, row.low)
        if completed[30] is not None:
            bar = completed[30]
            decision = bar.start + timedelta(minutes=30)
            scale = causal_scale(m30, bar)
            direction, _ = predict_ha(m30.fast, bar)
            features = {}
            if math.isfinite(scale):
                features.update(current_ha_features(m30, bar, direction, scale))
                features.update(higher_features(h1, direction, "h1"))
                features.update(higher_features(h4, direction, "h4"))
                lower = subset_records(m5.records, bar.start, decision, 6)
                features.update(micro_path_features(lower, direction, bar.open, scale, "m5"))
                raw = [value for value in recent_m1 if bar.start <= value.start < decision]
                features.update(wave_distribution_features(raw, direction, bar.open, bar.high, bar.low, scale))
            m30.on_complete(bar, row.timestamp, row.open, row.high, row.low, features)
        if completed[120] is not None:
            bar = completed[120]
            decision = bar.start + timedelta(minutes=120)
            scale = causal_scale(h2, bar)
            direction, _ = predict_ha(h2.fast, bar)
            features = {}
            if math.isfinite(scale):
                features.update(current_ha_features(h2, bar, direction, scale))
                features.update(higher_features(h4, direction, "h4"))
                lower = subset_records(m30.fast.records, bar.start, decision, 4)
                features.update(micro_path_features(lower, direction, bar.open, scale, "m30"))
                wave = subset_records(m5.records, bar.start, decision, 24)
                features.update(wave_distribution_features(wave, direction, bar.open, bar.high, bar.low, scale))
            h2.on_complete(bar, row.timestamp, row.open, row.high, row.low, features)
        for lane in (h4, h1, h2, m30):
            lane.check_stops(row.timestamp, row.open, row.high, row.low)
        if number % 500000 == 0:
            print(f"streamed {number} M1 rows")

    output = {}
    for population, lane in (("H2_K1", h2), ("M30_K1", m30)):
        frame = lane.frame()
        frame = frame.loc[frame["k"] == 1].copy()
        frame["population"] = population
        frame["direction"] = np.where(frame["dir"] > 0, "LONG", "SHORT")
        frame["decision_time"] = pd.to_datetime(frame["decision"])
        frame["right_tail_ge_3"] = (frame["R"] >= 3).astype(int)
        frame["right_tail_ge_5"] = (frame["R"] >= 5).astype(int)
        output[population] = frame.sort_values(["decision_time", "signal_id"]).reset_index(drop=True)
    return output, audit


def save(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, lineterminator="\n")


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=repo / "research/v12/v12_phase1p_contract.json")
    parser.add_argument("--m1", type=Path, default=repo / "data/GOLD#/GOLD#_M1_202201030100_202609222358.csv")
    parser.add_argument("--calendar", type=Path, default=Path.home() / "AppData/Roaming/MetaQuotes/Terminal/Common/Files/V12_PHASE1E_MQL5_CALENDAR_SNAPSHOT.csv")
    parser.add_argument("--calendar-overrides", type=Path, default=repo / "research/v12/v12_calendar_time_overrides.json")
    parser.add_argument("--phase0", type=Path, default=repo / "output/v12_phase0_event_universe_20260923/V12_PHASE0_PARENT_EVENTS.csv")
    parser.add_argument("--phase1b", type=Path, default=repo / "output/v12_phase1b_h4m5_journey_overlay_20260923/V12_PHASE1B_H4_CRT_DECISIONS.csv")
    parser.add_argument("--source-boxes", type=Path, default=repo / "output/v12_phase1g_continuous_intraday_path_20260924_a/V12_PHASE1G_SOURCE_BOXES.csv")
    parser.add_argument("--output", type=Path, default=repo / "output/v12_phase1p_intermediate_clock_boundary_20260925_a")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["contract_version"] != CONTRACT_VERSION:
        raise ValueError("contract mismatch")
    safe_output(args.output, args.replace)
    hashes = contract["source_hashes"]
    for path, key, label in (
        (args.m1, "raw_m1_full_sha256", "raw M1"), (args.calendar, "calendar_snapshot_sha256", "calendar"),
        (args.phase0, "phase0_parent_events_sha256", "Phase0"),
        (args.phase1b, "phase1b_h4_crt_decisions_sha256", "Phase1B"),
        (args.source_boxes, "phase1g_source_boxes_sha256", "source boxes"),
    ):
        verify(path, hashes[key], label)
    cutoff = parse_cutoff("2026-09-18T23:57:00")
    populations, audit = build_ledgers(args.m1, cutoff)
    if audit.prefix_sha256 != hashes["raw_m1_prefix_sha256"]:
        raise ValueError("prefix mismatch")
    market, market_audit = load_market(args.m1, cutoff)
    if market_audit.prefix_sha256 != hashes["raw_m1_prefix_sha256"]:
        raise ValueError("market prefix mismatch")
    calendar, _ = load_calendar(args.calendar, cutoff, args.calendar_overrides)
    clusters = build_clusters(calendar)
    event_index = EventIndex(clusters)
    boxes = generate_boxes(MarketIndex(market), market["timestamp"].min().date(), cutoff.date())
    medians = daily_prior_medians(market)
    phase0 = pd.read_csv(args.phase0)
    phase0 = phase0.loc[phase0["lane"] == "D1_TO_H1"].copy()
    phase1b = pd.read_csv(args.phase1b)

    metrics_parts, prediction_parts, policy_parts, inventory_parts = [], [], [], []
    candidate_counts, cohort_counts, scorecards = {}, {}, []
    for population, frame in populations.items():
        candidate_counts[population] = len(frame)
        base = policy_metrics(frame)
        scorecards.append({"population": population, "scope": "COMPLETE", **base})
        work = add_static_and_clock(frame)
        work = add_event_features(work, clusters)
        work = path_enrich(work, market, boxes, event_index, medians)
        if population == "H2_K1":
            work = attach_parent(work, phase0, "completion_observed_at", "hypothesis_direction", "parent")
        else:
            work = attach_parent(work, phase1b, "c2_completed_by", "direction", "parent")
        work["decision_time"] = pd.to_datetime(work["decision_time"])
        work["label_available_at"] = pd.to_datetime(work["label_available_at"])
        save(work, args.output / f"{PREFIX}{population}_ENRICHED_LEDGER.csv")
        sequenced, metrics, predictions, policies, inventory = run_population(population, work, contract)
        cohort_counts[population] = int(sequenced["after_stop_cohort"].sum())
        metrics_parts.append(metrics); prediction_parts.append(predictions)
        policy_parts.append(policies); inventory_parts.append(inventory)

    metrics = pd.concat(metrics_parts, ignore_index=True)
    predictions = pd.concat(prediction_parts, ignore_index=True)
    policies = pd.concat(policy_parts, ignore_index=True)
    inventory = pd.concat(inventory_parts, ignore_index=True)
    gates = evaluate_gates(metrics, policies)
    save(pd.DataFrame(scorecards), args.output / f"{PREFIX}POPULATION_SCORECARDS.csv")
    save(metrics, args.output / f"{PREFIX}WALK_FORWARD_METRICS.csv")
    save(predictions, args.output / f"{PREFIX}AFTER_STOP_TEST_PREDICTIONS.csv")
    save(policies, args.output / f"{PREFIX}POLICY_SCORECARDS.csv")
    save(inventory, args.output / f"{PREFIX}FEATURE_INVENTORY.csv")
    save(gates, args.output / f"{PREFIX}GATES.csv")
    summary = {
        "contract_version": CONTRACT_VERSION, "candidate_counts": candidate_counts,
        "cohort_counts": cohort_counts, "prefix_rows": audit.parsed_price_rows,
        "prefix_sha256": audit.prefix_sha256,
        "passing_models": gates.loc[gates["all_primary_gates_pass"], ["population", "model"]].to_dict("records"),
        "trade_authority": False, "sizing_authority": False,
    }
    write_json(args.output / f"{PREFIX}SUMMARY.json", summary)
    manifest = {path.name: sha256_file(path) for path in sorted(args.output.glob(f"{PREFIX}*"))
                if path.name != f"{PREFIX}RELEASE_MANIFEST.json"}
    write_json(args.output / f"{PREFIX}RELEASE_MANIFEST.json", manifest)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
