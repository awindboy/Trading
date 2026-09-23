#!/usr/bin/env python3
"""Build the frozen V12 Phase-1B H4/M5 journey and unchanged V10 overlay pack."""

from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right, insort
from collections import Counter, defaultdict
import csv
from dataclasses import asdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
from statistics import mean, median
from typing import Iterable, Optional

from build_v12_phase0 import PrefixAudit, iter_m1_prefix, parse_cutoff
from v12_phase0_core import (
    CompletedBar,
    MultiTimeframeAggregator,
    attach_wilder_atr,
    bucket_start,
    classify_c2,
    iso_broker_label,
    price_points,
    sha256_file,
)
from v12_phase1a_core import ExecutionBar, select_model1_trigger
from v12_phase1b_core import (
    CONTRACT_VERSION,
    Journey,
    LiquidityBook,
    LiquidityLevel,
    activation_id,
    build_journey_state,
    compute_ha_states,
    journey_at,
    make_level,
    milestone_stage,
)
from render_v12_phase1b_summary import render as render_summary


OUTPUT_PREFIX = "V12_PHASE1B_"
LEVEL_FAMILIES = ("PREVIOUS_H4", "PREVIOUS_DAY", "PREVIOUS_WEEK", "PREVIOUS_MONTH")


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: Optional[list[str]] = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not fieldnames:
            return
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_prepare_output(path: Path, replace: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(f"output directory is not empty: {path}; pass --replace-output")
        for child in path.iterdir():
            if not child.is_file() or not child.name.startswith(OUTPUT_PREFIX):
                raise ValueError(f"refusing to replace unexpected output path: {child}")
            child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def file_rows(path: Path) -> int:
    with path.open("rb") as handle:
        return max(0, sum(1 for _ in handle) - 1)


def file_manifest(path: Path) -> dict:
    return {
        "file": path.name,
        "bytes": path.stat().st_size,
        "rows": file_rows(path) if path.suffix.lower() == ".csv" else None,
        "sha256": sha256_file(path),
    }


def attach_atr_values(bars: list[CompletedBar], period: int) -> dict[datetime, Optional[float]]:
    seed: list[float] = []
    atr: Optional[float] = None
    previous_close: Optional[float] = None
    result: dict[datetime, Optional[float]] = {}
    for bar in bars:
        true_range = bar.range if previous_close is None else max(
            bar.range, abs(bar.high - previous_close), abs(bar.low - previous_close)
        )
        if atr is None:
            seed.append(true_range)
            if len(seed) == period:
                atr = sum(seed) / period
        else:
            atr = ((atr * (period - 1)) + true_range) / period
        result[bar.open_time] = atr
        previous_close = bar.close
    return result


class MonthBuilder:
    def __init__(self) -> None:
        self.key: Optional[tuple[int, int]] = None
        self.source_time: Optional[datetime] = None
        self.high: Optional[float] = None
        self.low: Optional[float] = None

    def observe(self, row) -> Optional[tuple[datetime, float, float, datetime]]:
        key = (row.timestamp.year, row.timestamp.month)
        completed = None
        if self.key is not None and key != self.key:
            completed = (self.source_time, self.high, self.low, row.timestamp)
            self.key = None
        if self.key is None:
            self.key = key
            self.source_time = datetime(row.timestamp.year, row.timestamp.month, 1)
            self.high = row.high
            self.low = row.low
        else:
            self.high = max(float(self.high), row.high)
            self.low = min(float(self.low), row.low)
        return completed


def add_bar_levels(book: LiquidityBook, family: str, bar: CompletedBar) -> None:
    book.add(make_level(family, "HIGH", bar.open_time, bar.high, bar.completed_by_observation))
    book.add(make_level(family, "LOW", bar.open_time, bar.low, bar.completed_by_observation))


def first_pass(m1_path: Path, cutoff: datetime) -> tuple[dict, list[LiquidityLevel], dict, PrefixAudit]:
    aggregator = MultiTimeframeAggregator(("M5", "H4", "D1", "W1"))
    book = LiquidityBook()
    month = MonthBuilder()
    seen_counts = {tf: 0 for tf in aggregator.timeframes}
    reference_opens: dict[str, list[tuple[datetime, datetime, float]]] = defaultdict(list)
    last_reference_key: dict[str, object] = {}
    audit = PrefixAudit()

    for row in iter_m1_prefix(m1_path, cutoff, audit=audit):
        for family, timeframe in (
            ("CURRENT_H4_OPEN", "H4"),
            ("CURRENT_DAY_OPEN", "D1"),
            ("CURRENT_WEEK_OPEN", "W1"),
        ):
            key = bucket_start(row.timestamp, timeframe)
            if last_reference_key.get(family) != key:
                reference_opens[family].append((key, row.timestamp, row.open))
                last_reference_key[family] = key
        month_key = (row.timestamp.year, row.timestamp.month)
        if last_reference_key.get("CURRENT_MONTH_OPEN") != month_key:
            reference_opens["CURRENT_MONTH_OPEN"].append(
                (datetime(row.timestamp.year, row.timestamp.month, 1), row.timestamp, row.open)
            )
            last_reference_key["CURRENT_MONTH_OPEN"] = month_key

        aggregator.observe(row)
        for timeframe, family in (("H4", "PREVIOUS_H4"), ("D1", "PREVIOUS_DAY"), ("W1", "PREVIOUS_WEEK")):
            completed = aggregator.completed[timeframe]
            while seen_counts[timeframe] < len(completed):
                add_bar_levels(book, family, completed[seen_counts[timeframe]])
                seen_counts[timeframe] += 1
        completed_month = month.observe(row)
        if completed_month is not None:
            source_time, high, low, known_at = completed_month
            book.add(make_level("PREVIOUS_MONTH", "HIGH", source_time, high, known_at))
            book.add(make_level("PREVIOUS_MONTH", "LOW", source_time, low, known_at))
        book.observe(row)

    bars = aggregator.completed
    for values in bars.values():
        attach_wilder_atr(values, 14)
    return bars, book.levels, reference_opens, audit


def execution_bars(bars: list[CompletedBar]) -> list[ExecutionBar]:
    return [
        ExecutionBar(
            timeframe=bar.timeframe,
            open_time=bar.open_time,
            close_time=bar.close_time,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            atr14=bar.atr14,
        )
        for bar in bars
    ]


def _dt(value: object) -> str:
    return iso_broker_label(value) if isinstance(value, datetime) else value


def serialize_row(row: dict) -> dict:
    return {key: _dt(value) for key, value in row.items()}


def build_h4_events(
    h4: list[CompletedBar], m5: list[CompletedBar], atr180: dict[datetime, Optional[float]]
) -> tuple[list[dict], list[dict], list[dict]]:
    m5_exec = execution_bars(m5)
    m5_opens = [bar.open_time for bar in m5_exec]
    m5_source = {bar.open_time: bar for bar in m5}
    ha = compute_ha_states(h4)
    ha_by_open = {row["open_time"]: row for row in ha}
    decisions: list[dict] = []
    activations: list[dict] = []

    for index in range(1, len(h4)):
        c1, c2 = h4[index - 1], h4[index]
        state = classify_c2(c1, c2)
        direction = state["direction"]
        interaction = state["interaction"]
        event_id = activation_id(c1, c2, interaction, direction)
        base = {
            "contract_version": CONTRACT_VERSION,
            "h4_event_id": event_id,
            "c1_open_time": c1.open_time,
            "c1_high": c1.high,
            "c1_low": c1.low,
            "c1_midpoint": (c1.high + c1.low) / 2.0,
            "c2_open_time": c2.open_time,
            "c2_close_time": c2.close_time,
            "c2_completed_by": c2.completed_by_observation,
            "c2_open": c2.open,
            "c2_high": c2.high,
            "c2_low": c2.low,
            "c2_close": c2.close,
            "interaction": interaction,
            "direction": direction,
            "h4_atr180": atr180.get(c2.open_time),
            "fast_ha_dir": ha_by_open[c2.open_time]["fast_dir"],
            "std_ha_dir": ha_by_open[c2.open_time]["std_dir"],
            "slow_ha_dir": ha_by_open[c2.open_time]["slow_dir"],
            "activation_status": "NO_DIRECTIONAL_ACTIVATION",
            "activation_time": None,
            "activation_price": None,
            "activation_lag_minutes_from_c2_observation": None,
            "model1_status": "NOT_APPLICABLE",
            "model1_trigger_open_time": None,
            "model1_confirmation_open_time": None,
            "model1_confirmation_known_at": None,
            "model1_eligible_count": 0,
            "outcome_fields_present": False,
        }
        activation_time = None
        activation_price = None
        if interaction in {"HIGH_OUTSIDE_ACCEPTANCE", "LOW_OUTSIDE_ACCEPTANCE"}:
            activation_time = c2.completed_by_observation
            activation_price = c2.close
            base["activation_status"] = "OUTSIDE_ACCEPTANCE_OBSERVATION_ACTIVATED"
        elif interaction in {"HIGH_SWEEP_RETURN", "LOW_SWEEP_RETURN"} and index + 1 < len(h4):
            c3 = h4[index + 1]
            lo = bisect_left(m5_opens, c2.open_time)
            hi = bisect_left(m5_opens, c3.close_time)
            selection, status, eligible = select_model1_trigger(
                direction=direction,
                c1_high=c1.high,
                c1_low=c1.low,
                c2_open_time=c2.open_time,
                c2_close_time=c2.close_time,
                c3_close_time=c3.close_time,
                execution_bars=m5_exec[lo:hi],
            )
            base["model1_status"] = status
            base["model1_eligible_count"] = eligible
            if selection is not None:
                confirmation_source = m5_source[selection.confirmation.open_time]
                activation_time = max(c2.completed_by_observation, confirmation_source.completed_by_observation)
                activation_price = selection.confirmation.close
                base["activation_status"] = "MODEL1_RELATIVE_THICK_M5_V1_ACTIVATED"
                base["model1_trigger_open_time"] = selection.trigger.open_time
                base["model1_confirmation_open_time"] = selection.confirmation.open_time
                base["model1_confirmation_known_at"] = confirmation_source.completed_by_observation
        base["activation_time"] = activation_time
        base["activation_price"] = activation_price
        base["activation_lag_minutes_from_c2_observation"] = (
            (activation_time - c2.completed_by_observation).total_seconds() / 60.0
            if activation_time is not None else None
        )
        decisions.append(base)
        if activation_time is not None:
            activation = dict(base)
            activation["activation_id"] = event_id
            activation["opposite_edge"] = c1.high if direction == "LONG" else c1.low
            activation["broker_weekday"] = activation_time.weekday()
            activation["broker_h4_start_hour"] = c2.open_time.hour
            activations.append(activation)
    return decisions, activations, ha


def reference_snapshot(reference_opens: dict, timestamp: datetime) -> dict:
    result = {}
    for family in ("CURRENT_H4_OPEN", "CURRENT_DAY_OPEN", "CURRENT_WEEK_OPEN", "CURRENT_MONTH_OPEN"):
        values = reference_opens[family]
        known = [item[1] for item in values]
        index = bisect_right(known, timestamp) - 1
        result[family.lower()] = values[index][2] if index >= 0 else None
    return result


def snapshots_for_queries(levels: list[LiquidityLevel], queries: list[tuple[str, datetime, float, Optional[float]]]) -> dict[str, dict]:
    known = sorted(levels, key=lambda level: (level.known_at, level.level_id))
    consumed = sorted(
        [level for level in levels if level.consumed_at is not None],
        key=lambda level: (level.consumed_at, level.level_id),
    )
    active: dict[str, list[tuple[int, str, LiquidityLevel]]] = {family: [] for family in LEVEL_FAMILIES}
    known_index = 0
    consumed_index = 0
    result: dict[str, dict] = {}
    for query_id, timestamp, price, atr in sorted(queries, key=lambda item: (item[1], item[0])):
        while known_index < len(known) and known[known_index].known_at <= timestamp:
            level = known[known_index]
            insort(active[level.family], (price_points(level.price), level.level_id, level))
            known_index += 1
        while consumed_index < len(consumed) and consumed[consumed_index].consumed_at < timestamp:
            level = consumed[consumed_index]
            item = (price_points(level.price), level.level_id, level)
            location = bisect_left(active[level.family], item)
            if location < len(active[level.family]) and active[level.family][location][1] == level.level_id:
                active[level.family].pop(location)
            consumed_index += 1
        snapshot: dict[str, object] = {"active_level_count": sum(len(values) for values in active.values())}
        points = price_points(price)
        for family in LEVEL_FAMILIES:
            values = active[family]
            above_location = bisect_left(values, (points, "", None))
            below_location = bisect_right(values, (points, "\uffff", None)) - 1
            above = values[above_location][2] if above_location < len(values) else None
            below = values[below_location][2] if below_location >= 0 else None
            key = family.lower()
            snapshot[f"{key}_active_count"] = len(values)
            for label, level, distance in (
                ("above", above, (above.price - price) if above else None),
                ("below", below, (price - below.price) if below else None),
            ):
                snapshot[f"{key}_nearest_{label}_id"] = level.level_id if level else None
                snapshot[f"{key}_nearest_{label}_price"] = level.price if level else None
                snapshot[f"{key}_nearest_{label}_distance"] = distance
                snapshot[f"{key}_nearest_{label}_distance_atr180"] = distance / atr if distance is not None and atr else None
        result[query_id] = snapshot
    return result


def evaluate_journeys(
    m1_path: Path,
    cutoff: datetime,
    journeys: list[Journey],
    levels: list[LiquidityLevel],
    h4: list[CompletedBar],
) -> tuple[list[dict], PrefixAudit]:
    state: dict[str, dict] = {}
    for journey in journeys:
        state[journey.journey_id] = {
            "start_price": None,
            "end_price": None,
            "high": None,
            "low": None,
            "midpoint_time": None,
            "opposite_edge_time": None,
            "midpoint_forward_eligible": None,
            "opposite_edge_forward_eligible": None,
            "last_close": None,
        }
    ordered = sorted(journeys, key=lambda item: item.start_time)
    index = 0
    audit = PrefixAudit()
    for row in iter_m1_prefix(m1_path, cutoff, audit=audit):
        while index < len(ordered):
            journey = ordered[index]
            values = state[journey.journey_id]
            terminal = journey.end_reason != "OPEN_AT_CUTOFF" and journey.end_time is not None and row.timestamp >= journey.end_time
            if terminal:
                values["end_price"] = row.open
                index += 1
                continue
            if row.timestamp < journey.start_time:
                break
            if journey.end_reason == "OPEN_AT_CUTOFF" and row.timestamp > journey.end_time:
                index += 1
                continue
            if values["start_price"] is None:
                values["start_price"] = row.open
                if journey.direction == "LONG":
                    values["midpoint_forward_eligible"] = price_points(journey.origin["c1_midpoint"]) > price_points(row.open)
                    values["opposite_edge_forward_eligible"] = price_points(journey.origin["opposite_edge"]) > price_points(row.open)
                else:
                    values["midpoint_forward_eligible"] = price_points(journey.origin["c1_midpoint"]) < price_points(row.open)
                    values["opposite_edge_forward_eligible"] = price_points(journey.origin["opposite_edge"]) < price_points(row.open)
            values["high"] = row.high if values["high"] is None else max(values["high"], row.high)
            values["low"] = row.low if values["low"] is None else min(values["low"], row.low)
            values["last_close"] = row.close
            midpoint = journey.origin["c1_midpoint"]
            opposite = journey.origin["opposite_edge"]
            if values["midpoint_forward_eligible"] and values["midpoint_time"] is None:
                touched = row.high >= midpoint if journey.direction == "LONG" else row.low <= midpoint
                if touched:
                    values["midpoint_time"] = row.timestamp
            if values["opposite_edge_forward_eligible"] and values["opposite_edge_time"] is None:
                touched = row.high >= opposite if journey.direction == "LONG" else row.low <= opposite
                if touched:
                    values["opposite_edge_time"] = row.timestamp
            break
    for journey in ordered:
        values = state[journey.journey_id]
        if values["end_price"] is None:
            values["end_price"] = values["last_close"]

    outcomes: list[dict] = []
    for journey in ordered:
        values = state[journey.journey_id]
        start_price = values["start_price"]
        end_price = values["end_price"]
        direction_sign = 1 if journey.direction == "LONG" else -1
        atr = journey.origin.get("h4_atr180")
        if start_price is not None:
            mfe = (values["high"] - start_price) if journey.direction == "LONG" else (start_price - values["low"])
            mae = (start_price - values["low"]) if journey.direction == "LONG" else (values["high"] - start_price)
        else:
            mfe = mae = None
        path_prices = [start_price] if start_price is not None else []
        for bar in h4:
            if bar.completed_by_observation > journey.start_time and (
                journey.end_time is None or bar.completed_by_observation <= journey.end_time
            ):
                path_prices.append(bar.close)
        if end_price is not None and (not path_prices or path_prices[-1] != end_price):
            path_prices.append(end_price)
        path_distance = sum(abs(b - a) for a, b in zip(path_prices, path_prices[1:]))
        net = direction_sign * (end_price - start_price) if start_price is not None and end_price is not None else None
        efficiency = net / path_distance if net is not None and path_distance > 0 else None
        side = "HIGH" if journey.direction == "LONG" else "LOW"
        arrivals = [
            level
            for level in levels
            if level.side == side
            and level.consumed_at is not None
            and journey.start_time <= level.consumed_at
            and (
                level.consumed_at < journey.end_time
                or (journey.end_reason == "OPEN_AT_CUTOFF" and level.consumed_at <= journey.end_time)
            )
        ]
        arrivals.sort(key=lambda level: (level.consumed_at, level.level_id))
        family_counts = Counter(level.family for level in arrivals)
        outcomes.append(
            {
                "contract_version": CONTRACT_VERSION,
                "journey_id": journey.journey_id,
                "direction": journey.direction,
                "start_time": iso_broker_label(journey.start_time),
                "end_time": iso_broker_label(journey.end_time) if journey.end_time else None,
                "end_reason": journey.end_reason,
                "failure_h4_open_time": iso_broker_label(journey.failure_h4_open_time) if journey.failure_h4_open_time else None,
                "origin_activation_id": journey.origin["activation_id"],
                "terminal_boundary_activation_id": journey.boundary["activation_id"],
                "reinforcement_count": journey.reinforcement_count,
                "activation_count": len(journey.activation_ids),
                "duration_hours": (
                    (journey.end_time - journey.start_time).total_seconds() / 3600.0
                    if journey.end_time else None
                ),
                "completed_h4_observations": sum(
                    journey.start_time < bar.completed_by_observation <= journey.end_time
                    for bar in h4
                ) if journey.end_time else None,
                "start_price": start_price,
                "end_price": end_price,
                "signed_net_price": net,
                "signed_net_atr180": net / atr if net is not None and atr else None,
                "mfe_price": mfe,
                "mfe_atr180": mfe / atr if mfe is not None and atr else None,
                "mae_price": mae,
                "mae_atr180": mae / atr if mae is not None and atr else None,
                "midpoint_time": iso_broker_label(values["midpoint_time"]) if values["midpoint_time"] else None,
                "opposite_edge_time": iso_broker_label(values["opposite_edge_time"]) if values["opposite_edge_time"] else None,
                "midpoint_forward_eligible": values["midpoint_forward_eligible"],
                "opposite_edge_forward_eligible": values["opposite_edge_forward_eligible"],
                "midpoint_attained": values["midpoint_time"] is not None,
                "opposite_edge_attained": values["opposite_edge_time"] is not None,
                "signed_h4_close_path_efficiency": efficiency,
                "same_direction_external_arrivals": len(arrivals),
                "previous_h4_arrivals": family_counts["PREVIOUS_H4"],
                "previous_day_arrivals": family_counts["PREVIOUS_DAY"],
                "previous_week_arrivals": family_counts["PREVIOUS_WEEK"],
                "previous_month_arrivals": family_counts["PREVIOUS_MONTH"],
                "first_external_arrival_time": iso_broker_label(arrivals[0].consumed_at) if arrivals else None,
                "last_external_arrival_time": iso_broker_label(arrivals[-1].consumed_at) if arrivals else None,
                "outcome_fields_present": True,
            }
        )
    return outcomes, audit


def build_v10_overlay(
    selected_path: Path,
    journeys: list[Journey],
    journey_outcomes: list[dict],
    activations: list[dict],
    h4: list[CompletedBar],
    atr180: dict[datetime, Optional[float]],
) -> tuple[list[dict], list[dict], list[tuple[str, datetime, float, Optional[float]]]]:
    selected = [row for row in read_csv(selected_path) if row["policy"] == "ORIGINAL_FULL_R7G_PORTFOLIO"]
    activation_by_id = {row["activation_id"]: row for row in activations}
    h4_known = [bar.completed_by_observation for bar in h4]
    outcome_by_id = {row["journey_id"]: row for row in journey_outcomes}
    aligned_counts: Counter = Counter()
    decisions: list[dict] = []
    outcomes: list[dict] = []
    queries: list[tuple[str, datetime, float, Optional[float]]] = []
    for row in sorted(selected, key=lambda item: (item["decision_ts"], item["signal_id"])):
        timestamp = datetime.fromisoformat(row["decision_ts"])
        direction = "LONG" if int(row["dir"]) == 1 else "SHORT"
        journey = journey_at(journeys, timestamp)
        if journey is None:
            relation = "NO_ACTIVE_JOURNEY"
            stage = "NO_ACTIVE_JOURNEY"
            ordinal = None
        elif journey.direction == direction:
            relation = "ALIGNED_ACTIVE_JOURNEY"
            aligned_counts[journey.journey_id] += 1
            ordinal = aligned_counts[journey.journey_id]
            stage = milestone_stage(journey, timestamp, outcome_by_id[journey.journey_id])
        else:
            relation = "OPPOSED_ACTIVE_JOURNEY"
            stage = milestone_stage(journey, timestamp, outcome_by_id[journey.journey_id])
            ordinal = None
        h4_index = bisect_right(h4_known, timestamp) - 1
        if h4_index < 0:
            raise ValueError(f"no causal H4 settlement for V10 decision {row['signal_id']}")
        coordinate_bar = h4[h4_index]
        coordinate = coordinate_bar.close
        query_id = "v10:" + row["signal_id"]
        atr = atr180.get(coordinate_bar.open_time)
        queries.append((query_id, timestamp, coordinate, atr))
        known_reinforcements = None
        if journey:
            known_reinforcements = max(
                0,
                sum(
                    activation_by_id[activation_id]["activation_time"] <= timestamp
                    for activation_id in journey.activation_ids
                )
                - 1,
            )
        decisions.append(
            {
                "contract_version": CONTRACT_VERSION,
                "signal_id": row["signal_id"],
                "decision_time": iso_broker_label(timestamp),
                "direction": direction,
                "k": int(row["k"]),
                "event": row["event"],
                "r7g_weight": float(row["r7g_weight"]),
                "relation": relation,
                "journey_id": journey.journey_id if journey else None,
                "journey_direction": journey.direction if journey else None,
                "journey_stage": stage,
                "journey_age_hours": (timestamp - journey.start_time).total_seconds() / 3600.0 if journey else None,
                "reinforcement_count_known": known_reinforcements,
                "aligned_child_ordinal": ordinal,
                "level_coordinate_price": coordinate,
                "level_coordinate_source": "LATEST_CAUSALLY_COMPLETED_H4_CLOSE",
                "level_coordinate_h4_open_time": iso_broker_label(coordinate_bar.open_time),
                "level_coordinate_known_at": iso_broker_label(coordinate_bar.completed_by_observation),
                "level_snapshot_query_id": query_id,
                "outcome_fields_present": False,
            }
        )
        outcomes.append(
            {
                "contract_version": CONTRACT_VERSION,
                "signal_id": row["signal_id"],
                "entry_time": row["entry_time"],
                "exit_time": row["exit_time"],
                "R": float(row["R"]),
                "stop_hit": int(row["stop_hit"]),
                "combined_R_units": float(row["combined_R_units"]),
                "stopped_loss_units": float(row["stopped_loss_units"]),
                "funded_units": float(row["funded_units"]),
                "full_3unit_stop": int(row["full_3unit_stop"]),
                "right_tail_ge_5R_units": float(row["combined_R_units"]) if float(row["combined_R_units"]) >= 5.0 else 0.0,
                "outcome_fields_present": True,
            }
        )
    return decisions, outcomes, queries


def build_fast_flips(
    h4: list[CompletedBar],
    ha: list[dict],
    journeys: list[Journey],
    levels: list[LiquidityLevel],
    full_v10_path: Path,
) -> tuple[list[dict], list[dict]]:
    full = read_csv(full_v10_path)
    k1 = {(row["decision"], int(row["dir"])): row for row in full if int(row["k"]) == 1}
    decisions: list[dict] = []
    outcomes: list[dict] = []
    previous_flip_time = ha[0]["known_at"] if ha else None
    flip_indices = [index for index in range(1, len(ha)) if ha[index]["fast_dir"] != ha[index - 1]["fast_dir"]]
    for position, index in enumerate(flip_indices):
        current = ha[index]
        prior = ha[index - 1]
        timestamp = current["known_at"]
        new_direction = "LONG" if current["fast_dir"] == 1 else "SHORT"
        old_direction = "LONG" if prior["fast_dir"] == 1 else "SHORT"
        active = journey_at(journeys, timestamp)
        old = next(
            (
                journey for journey in reversed(journeys)
                if journey.direction == old_direction
                and journey.start_time < timestamp
                and journey.end_time is not None
                and journey.end_time >= timestamp
            ),
            None,
        )
        run_start = previous_flip_time or prior["known_at"]
        same_side = "HIGH" if old_direction == "LONG" else "LOW"
        arrivals = [
            level for level in levels
            if level.side == same_side and level.consumed_at is not None and run_start <= level.consumed_at < timestamp
        ]
        if active is not None and active.direction == new_direction:
            state = "OPPOSITE_CRT_AUTHORIZED"
        elif active is not None and active.direction == old_direction:
            state = "OLD_JOURNEY_AFTER_KEY_ARRIVAL" if arrivals else "OLD_JOURNEY_COUNTERFLOW"
        else:
            failed = any(
                journey.direction == old_direction
                and journey.end_reason == "STRUCTURAL_FAILURE"
                and journey.end_time is not None
                and run_start <= journey.end_time <= timestamp
                for journey in journeys
            )
            state = "OLD_JOURNEY_FAILED_NO_OPPOSITE" if failed else "NEUTRAL_ROTATION"
        flip_id = "v12flip-" + hashlib.sha256(
            f"{CONTRACT_VERSION}|{iso_broker_label(h4[index].open_time)}".encode("utf-8")
        ).hexdigest()[:24]
        scheduled = h4[index].close_time
        decisions.append(
            {
                "contract_version": CONTRACT_VERSION,
                "flip_id": flip_id,
                "h4_open_time": iso_broker_label(h4[index].open_time),
                "scheduled_decision_time": iso_broker_label(scheduled),
                "known_at": iso_broker_label(timestamp),
                "old_fast_direction": old_direction,
                "new_fast_direction": new_direction,
                "explanation_state": state,
                "active_journey_id": active.journey_id if active else None,
                "old_journey_id": old.journey_id if old else None,
                "same_direction_external_arrivals_ending_run": len(arrivals),
                "outcome_fields_present": False,
            }
        )
        next_index = flip_indices[position + 1] if position + 1 < len(flip_indices) else None
        run_bars = (next_index - index) if next_index is not None else (len(h4) - index)
        terminal_close = h4[next_index - 1].close if next_index is not None else h4[-1].close
        signed_move = (terminal_close - h4[index].open) * current["fast_dir"]
        linked = k1.get((iso_broker_label(scheduled).replace("T", " "), current["fast_dir"]))
        outcomes.append(
            {
                "contract_version": CONTRACT_VERSION,
                "flip_id": flip_id,
                "new_fast_run_h4_bars": run_bars,
                "new_fast_run_signed_raw_move": signed_move,
                "linked_v10_k1_signal_id": linked["signal_id"] if linked else None,
                "linked_v10_k1_R": float(linked["R"]) if linked else None,
                "linked_v10_k1_stop_hit": int(linked["stop_hit"]) if linked else None,
                "outcome_fields_present": True,
            }
        )
        previous_flip_time = timestamp
    return decisions, outcomes


def metric_rows(
    journeys: list[Journey],
    journey_outcomes: list[dict],
    h4: list[CompletedBar],
    h4_decisions: list[dict],
    v10_decisions: list[dict],
    v10_outcomes: list[dict],
    flip_decisions: list[dict],
    flip_outcomes: list[dict],
) -> list[dict]:
    rows: list[dict] = []

    def add(section: str, dimension: str, group: str, metric: str, value) -> None:
        rows.append({"section": section, "dimension": dimension, "group": group, "metric": metric, "value": value})

    add("JOURNEY", "ALL", "ALL", "journeys", len(journeys))
    for field in ("end_reason", "direction"):
        counts = Counter(getattr(journey, field) for journey in journeys)
        for group, count in sorted(counts.items()):
            add("JOURNEY", field, str(group), "count", count)
    for target in ("midpoint", "opposite_edge"):
        eligible = [row for row in journey_outcomes if row[f"{target}_forward_eligible"]]
        add("JOURNEY", "ALL", "ALL", f"{target}_forward_eligible", len(eligible))
        add("JOURNEY", "ALL", "ALL", f"{target}_attainment_rate_when_forward", mean(bool(row[f"{target}_attained"]) for row in eligible) if eligible else None)
    efficiencies = [float(row["signed_h4_close_path_efficiency"]) for row in journey_outcomes if row["signed_h4_close_path_efficiency"] not in (None, "")]
    add("JOURNEY", "ALL", "ALL", "median_signed_h4_close_path_efficiency", median(efficiencies) if efficiencies else None)
    durations = [float(row["duration_hours"]) for row in journey_outcomes if row["duration_hours"] not in (None, "")]
    add("JOURNEY", "ALL", "ALL", "median_duration_hours", median(durations) if durations else None)
    active_h4 = sum(journey_at(journeys, bar.completed_by_observation) is not None for bar in h4)
    add("JOURNEY", "H4_COVERAGE", "ACTIVE", "completed_h4", active_h4)
    add("JOURNEY", "H4_COVERAGE", "NEUTRAL", "completed_h4", len(h4) - active_h4)
    add("JOURNEY", "H4_COVERAGE", "ACTIVE", "share", active_h4 / len(h4) if h4 else None)
    lags = [float(row["activation_lag_minutes_from_c2_observation"]) for row in h4_decisions if row["activation_time"] is not None]
    add("JOURNEY", "ALL", "ALL", "median_activation_lag_minutes", median(lags) if lags else None)

    outcome_by_signal = {row["signal_id"]: row for row in v10_outcomes}
    dimensions = {
        "relation": lambda row: row["relation"],
        "journey_stage": lambda row: row["journey_stage"],
        "aligned_ordinal": lambda row: "FIRST" if row["aligned_child_ordinal"] == 1 else "LATER" if row["aligned_child_ordinal"] else "NOT_ALIGNED",
        "direction": lambda row: row["direction"],
        "year": lambda row: row["decision_time"][:4],
        "relation_x_year": lambda row: row["relation"] + "|" + row["decision_time"][:4],
        "relation_x_direction": lambda row: row["relation"] + "|" + row["direction"],
        "aligned_ordinal_x_year": lambda row: (
            "FIRST" if row["aligned_child_ordinal"] == 1 else "LATER" if row["aligned_child_ordinal"] else "NOT_ALIGNED"
        ) + "|" + row["decision_time"][:4],
        "weekday": lambda row: str(datetime.fromisoformat(row["decision_time"]).weekday()),
        "h4_hour": lambda row: str(datetime.fromisoformat(row["decision_time"]).hour),
    }
    for dimension, getter in dimensions.items():
        grouped: dict[str, list[dict]] = defaultdict(list)
        for decision in v10_decisions:
            grouped[getter(decision)].append(outcome_by_signal[decision["signal_id"]])
        for group, values in sorted(grouped.items()):
            add("V10_OVERLAY", dimension, group, "children", len(values))
            add("V10_OVERLAY", dimension, group, "stop_rate", mean(int(row["stop_hit"]) for row in values))
            add("V10_OVERLAY", dimension, group, "stopped_units", sum(float(row["stopped_loss_units"]) for row in values))
            add("V10_OVERLAY", dimension, group, "funded_units", sum(float(row["funded_units"]) for row in values))
            add("V10_OVERLAY", dimension, group, "weighted_R", sum(float(row["combined_R_units"]) for row in values))
            add("V10_OVERLAY", dimension, group, "right_tail_ge_5R_units", sum(float(row["right_tail_ge_5R_units"]) for row in values))
            funded = sum(float(row["funded_units"]) for row in values)
            stopped = sum(float(row["stopped_loss_units"]) for row in values)
            add("V10_OVERLAY", dimension, group, "stopped_units_per_100_funded", 100.0 * stopped / funded if funded else None)
            add("V10_OVERLAY", dimension, group, "weighted_R_per_100_funded", 100.0 * sum(float(row["combined_R_units"]) for row in values) / funded if funded else None)
            ordered = [outcome_by_signal[item["signal_id"]] for item in sorted(
                [decision for decision in v10_decisions if getter(decision) == group],
                key=lambda decision: (decision["decision_time"], decision["signal_id"]),
            )]
            streak = maximum = adjacent_pairs = 0
            previous_stop = False
            for outcome in ordered:
                is_stop = bool(int(outcome["stop_hit"]))
                if is_stop:
                    streak += 1
                    maximum = max(maximum, streak)
                    adjacent_pairs += int(previous_stop)
                else:
                    streak = 0
                previous_stop = is_stop
            add("V10_OVERLAY", dimension, group, "max_child_stop_streak", maximum)
            add("V10_OVERLAY", dimension, group, "adjacent_child_stop_pairs", adjacent_pairs)

    flip_outcome_by_id = {row["flip_id"]: row for row in flip_outcomes}
    for dimension, getter in {
        "explanation_state": lambda row: row["explanation_state"],
        "state_x_year": lambda row: row["explanation_state"] + "|" + row["known_at"][:4],
        "state_x_new_direction": lambda row: row["explanation_state"] + "|" + row["new_fast_direction"],
    }.items():
        grouped_flips: dict[str, list[dict]] = defaultdict(list)
        for decision in flip_decisions:
            grouped_flips[getter(decision)].append(flip_outcome_by_id[decision["flip_id"]])
        for group, values in sorted(grouped_flips.items()):
            add("FAST_FLIP", dimension, group, "flips", len(values))
            linked = [row for row in values if row["linked_v10_k1_R"] is not None]
            add("FAST_FLIP", dimension, group, "linked_v10_k1", len(linked))
            add("FAST_FLIP", dimension, group, "linked_k1_stop_rate", mean(int(row["linked_v10_k1_stop_hit"]) for row in linked) if linked else None)
            add("FAST_FLIP", dimension, group, "linked_k1_net_R", sum(float(row["linked_v10_k1_R"]) for row in linked))
            add("FAST_FLIP", dimension, group, "median_new_run_h4_bars", median(int(row["new_fast_run_h4_bars"]) for row in values))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m1", type=Path, required=True)
    parser.add_argument("--cutoff", default="2026-09-18T23:57:00")
    parser.add_argument("--selected-v10", type=Path, required=True)
    parser.add_argument("--full-v10", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replace-output", action="store_true")
    args = parser.parse_args()
    cutoff = parse_cutoff(args.cutoff)
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["contract_version"] != CONTRACT_VERSION:
        raise ValueError("Phase-1B contract version mismatch")
    safe_prepare_output(args.output, args.replace_output)

    bars, levels, reference_opens, prefix_audit = first_pass(args.m1, cutoff)
    h4, m5 = bars["H4"], bars["M5"]
    atr180 = attach_atr_values(h4, 180)
    h4_decisions, activations, ha = build_h4_events(h4, m5, atr180)
    journeys, journey_decisions = build_journey_state(activations, h4, cutoff)
    journey_outcomes, outcome_prefix_audit = evaluate_journeys(args.m1, cutoff, journeys, levels, h4)

    v10_decisions, v10_outcomes, v10_queries = build_v10_overlay(
        args.selected_v10, journeys, journey_outcomes, activations, h4, atr180
    )
    queries: list[tuple[str, datetime, float, Optional[float]]] = []
    for row in h4_decisions:
        query_time = row["activation_time"] or row["c2_completed_by"]
        query_price = row["activation_price"] or row["c2_close"]
        query_id = "h4:" + row["h4_event_id"]
        row["level_snapshot_query_id"] = query_id
        queries.append((query_id, query_time, float(query_price), row["h4_atr180"]))
    queries.extend(v10_queries)
    snapshots = snapshots_for_queries(levels, queries)
    for row in h4_decisions:
        row.update(snapshots[row["level_snapshot_query_id"]])
        row.update(reference_snapshot(reference_opens, row["activation_time"] or row["c2_completed_by"]))
    for row in journey_decisions:
        query_id = "h4:" + row["h4_event_id"]
        row.update(snapshots[query_id])
        row.update(reference_snapshot(reference_opens, row["activation_time"]))
    for row in v10_decisions:
        query_id = row["level_snapshot_query_id"]
        row.update(snapshots[query_id])

    flip_decisions, flip_outcomes = build_fast_flips(h4, ha, journeys, levels, args.full_v10)
    scorecard = metric_rows(journeys, journey_outcomes, h4, h4_decisions, v10_decisions, v10_outcomes, flip_decisions, flip_outcomes)

    level_decisions = [level.decision_record() for level in sorted(levels, key=lambda item: item.level_id)]
    level_outcomes = [level.outcome_record() for level in sorted(levels, key=lambda item: item.level_id)]
    files = {
        "KEY_LEVEL_DECISIONS.csv": level_decisions,
        "KEY_LEVEL_OUTCOMES.csv": level_outcomes,
        "H4_CRT_DECISIONS.csv": [serialize_row(row) for row in h4_decisions],
        "JOURNEY_DECISIONS.csv": [serialize_row(row) for row in journey_decisions],
        "JOURNEY_OUTCOMES.csv": journey_outcomes,
        "V10_CHILD_DECISION_CONTEXT.csv": v10_decisions,
        "V10_CHILD_OUTCOME_LINK.csv": v10_outcomes,
        "NHA_DECISION_CONTEXT.csv": flip_decisions,
        "NHA_OUTCOME_LINK.csv": flip_outcomes,
        "SCORECARD.csv": scorecard,
    }
    written: list[Path] = []
    for suffix, rows in files.items():
        path = args.output / (OUTPUT_PREFIX + suffix)
        write_csv(path, rows)
        written.append(path)

    selected_weighted_r = sum(float(row["combined_R_units"]) for row in v10_outcomes)
    diagnostics = {
        "contract_version": CONTRACT_VERSION,
        "causal_cutoff": iso_broker_label(cutoff),
        "source": {
            "m1_path": str(args.m1),
            "m1_full_sha256": sha256_file(args.m1),
            "prefix_audit_first_pass": prefix_audit.to_dict(),
            "prefix_audit_outcome_pass": outcome_prefix_audit.to_dict(),
            "selected_v10_path": str(args.selected_v10),
            "selected_v10_sha256": sha256_file(args.selected_v10),
            "full_v10_path": str(args.full_v10),
            "full_v10_sha256": sha256_file(args.full_v10),
            "contract_sha256": sha256_file(args.contract),
        },
        "counts": {
            "m5_completed": len(m5),
            "h4_completed": len(h4),
            "levels": len(levels),
            "levels_consumed": sum(level.consumed_at is not None for level in levels),
            "h4_pair_decisions": len(h4_decisions),
            "activations": len(activations),
            "journeys": len(journeys),
            "journey_state_decisions": len(journey_decisions),
            "selected_v10_children": len(v10_decisions),
            "fast_flips": len(flip_decisions),
        },
        "v10_invariants": {
            "selected_children_expected": 1649,
            "selected_children_actual": len(v10_decisions),
            "combined_R_units": selected_weighted_r,
            "stopped_units": sum(float(row["stopped_loss_units"]) for row in v10_outcomes),
            "funded_units": sum(float(row["funded_units"]) for row in v10_outcomes),
        },
        "decision_outcome_separation": True,
        "post_cutoff_price_rows_parsed": prefix_audit.post_cutoff_price_rows_parsed + outcome_prefix_audit.post_cutoff_price_rows_parsed,
        "trade_authority": False,
        "sizing_authority": False,
    }
    diagnostics_path = args.output / (OUTPUT_PREFIX + "DIAGNOSTICS.json")
    write_json(diagnostics_path, diagnostics)
    written.append(diagnostics_path)
    summary_path = args.output / (OUTPUT_PREFIX + "SUMMARY.png")
    render_summary(args.output, summary_path)
    written.append(summary_path)
    manifest = {
        "contract_version": CONTRACT_VERSION,
        "generated_at": "DETERMINISTIC_NO_WALL_CLOCK",
        "files": [file_manifest(path) for path in sorted(written)],
    }
    manifest_path = args.output / (OUTPUT_PREFIX + "MANIFEST.json")
    write_json(manifest_path, manifest)


if __name__ == "__main__":
    main()
