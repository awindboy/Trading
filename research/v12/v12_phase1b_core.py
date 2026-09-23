"""Deterministic primitives for the V12 Phase-1B journey observation study.

The module contains no trading authority.  It turns causally completed H4 CRT
activations into one canonical observation journey and keeps all future answer
fields outside decision records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import heapq
import json
from typing import Iterable, Optional

from v12_phase0_core import CompletedBar, M1Row, iso_broker_label, price_points


CONTRACT_VERSION = "v12-phase1b-h4m5-journey-v1.1"
POINT_SIZE = 0.01


def stable_id(prefix: str, payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return prefix + hashlib.sha256(raw).hexdigest()[:24]


@dataclass
class LiquidityLevel:
    level_id: str
    family: str
    side: str
    source_time: datetime
    price: float
    known_at: datetime
    consumed_at: Optional[datetime] = None
    birth_and_consumption_same_m1: bool = False

    def decision_record(self) -> dict:
        return {
            "contract_version": CONTRACT_VERSION,
            "level_id": self.level_id,
            "family": self.family,
            "side": self.side,
            "source_time": iso_broker_label(self.source_time),
            "price": self.price,
            "known_at": iso_broker_label(self.known_at),
            "outcome_fields_present": False,
        }

    def outcome_record(self) -> dict:
        return {
            "contract_version": CONTRACT_VERSION,
            "level_id": self.level_id,
            "consumed_at": iso_broker_label(self.consumed_at) if self.consumed_at else None,
            "birth_and_consumption_same_m1": self.birth_and_consumption_same_m1,
            "ordering_precision": "M1",
            "outcome_fields_present": True,
        }


class LiquidityBook:
    """Consume one-use levels by first strict point-rounded M1 breach."""

    def __init__(self) -> None:
        self.high_heap: list[tuple[int, str, LiquidityLevel]] = []
        self.low_heap: list[tuple[int, str, LiquidityLevel]] = []
        self.levels: list[LiquidityLevel] = []

    def add(self, level: LiquidityLevel) -> None:
        self.levels.append(level)
        points = price_points(level.price)
        if level.side == "HIGH":
            heapq.heappush(self.high_heap, (points, level.level_id, level))
        elif level.side == "LOW":
            heapq.heappush(self.low_heap, (-points, level.level_id, level))
        else:
            raise ValueError(f"unsupported level side: {level.side}")

    def observe(self, row: M1Row) -> list[LiquidityLevel]:
        consumed: list[LiquidityLevel] = []
        high_points = price_points(row.high)
        low_points = price_points(row.low)
        while self.high_heap and self.high_heap[0][0] < high_points:
            _, _, level = heapq.heappop(self.high_heap)
            level.consumed_at = row.timestamp
            level.birth_and_consumption_same_m1 = level.known_at == row.timestamp
            consumed.append(level)
        while self.low_heap and -self.low_heap[0][0] > low_points:
            _, _, level = heapq.heappop(self.low_heap)
            level.consumed_at = row.timestamp
            level.birth_and_consumption_same_m1 = level.known_at == row.timestamp
            consumed.append(level)
        return consumed


def make_level(family: str, side: str, source_time: datetime, price: float, known_at: datetime) -> LiquidityLevel:
    return LiquidityLevel(
        level_id=stable_id(
            "v12lvl-",
            {
                "contract": CONTRACT_VERSION,
                "family": family,
                "side": side,
                "source_time": iso_broker_label(source_time),
                "price_points": price_points(price),
                "known_at": iso_broker_label(known_at),
            },
        ),
        family=family,
        side=side,
        source_time=source_time,
        price=price,
        known_at=known_at,
    )


def active_levels_at(levels: Iterable[LiquidityLevel], timestamp: datetime) -> list[LiquidityLevel]:
    # A level consumed on the decision M1 is still present at that M1 open.
    return [
        level
        for level in levels
        if level.known_at <= timestamp
        and (level.consumed_at is None or level.consumed_at >= timestamp)
    ]


def level_snapshot(levels: Iterable[LiquidityLevel], timestamp: datetime, price: float, atr180: Optional[float]) -> dict:
    active = active_levels_at(levels, timestamp)
    result: dict[str, object] = {"active_level_count": len(active)}
    for family in ("PREVIOUS_H4", "PREVIOUS_DAY", "PREVIOUS_WEEK", "PREVIOUS_MONTH"):
        subset = [level for level in active if level.family == family]
        above = [level for level in subset if price_points(level.price) >= price_points(price)]
        below = [level for level in subset if price_points(level.price) <= price_points(price)]
        high = min(above, key=lambda level: (level.price, level.level_id), default=None)
        low = max(below, key=lambda level: (level.price, level.level_id), default=None)
        key = family.lower()
        result[f"{key}_active_count"] = len(subset)
        result[f"{key}_nearest_above_id"] = high.level_id if high else None
        result[f"{key}_nearest_above_price"] = high.price if high else None
        result[f"{key}_nearest_above_distance"] = high.price - price if high else None
        result[f"{key}_nearest_above_distance_atr180"] = (
            (high.price - price) / atr180 if high and atr180 else None
        )
        result[f"{key}_nearest_below_id"] = low.level_id if low else None
        result[f"{key}_nearest_below_price"] = low.price if low else None
        result[f"{key}_nearest_below_distance"] = price - low.price if low else None
        result[f"{key}_nearest_below_distance_atr180"] = (
            (price - low.price) / atr180 if low and atr180 else None
        )
    return result


def compute_ha_states(bars: list[CompletedBar]) -> list[dict]:
    specs = {"fast": (2.0, 0.25), "std": (1.0, 0.50), "slow": (2.0, 0.75)}
    previous: dict[str, tuple[float, float]] = {}
    rows: list[dict] = []
    for bar in bars:
        row: dict[str, object] = {
            "open_time": bar.open_time,
            "known_at": bar.completed_by_observation,
        }
        for name, (weight, alpha) in specs.items():
            close = (bar.open + bar.high + bar.low + weight * bar.close) / (3.0 + weight)
            if name not in previous:
                open_ = 0.5 * (bar.open + bar.close)
            else:
                prev_open, prev_close = previous[name]
                open_ = alpha * prev_open + (1.0 - alpha) * prev_close
            direction = 1 if close >= open_ else -1
            row[f"{name}_open"] = open_
            row[f"{name}_close"] = close
            row[f"{name}_dir"] = direction
            previous[name] = (open_, close)
        rows.append(row)
    return rows


def activation_id(c1: CompletedBar, c2: CompletedBar, branch: str, direction: str) -> str:
    return stable_id(
        "v12act-",
        {
            "contract": CONTRACT_VERSION,
            "c1": iso_broker_label(c1.open_time),
            "c2": iso_broker_label(c2.open_time),
            "branch": branch,
            "direction": direction,
        },
    )


def journey_id(activation: dict) -> str:
    return stable_id(
        "v12journey-",
        {
            "contract": CONTRACT_VERSION,
            "activation_id": activation["activation_id"],
            "activation_time": iso_broker_label(activation["activation_time"]),
        },
    )


def boundary_failed(boundary: dict, bar: CompletedBar) -> bool:
    close = price_points(bar.close)
    branch = boundary["interaction"]
    if branch == "LOW_SWEEP_RETURN":
        return close < price_points(boundary["c2_low"])
    if branch == "HIGH_SWEEP_RETURN":
        return close > price_points(boundary["c2_high"])
    if branch == "HIGH_OUTSIDE_ACCEPTANCE":
        return close <= price_points(boundary["c1_high"])
    if branch == "LOW_OUTSIDE_ACCEPTANCE":
        return close >= price_points(boundary["c1_low"])
    raise ValueError(f"unsupported boundary branch: {branch}")


@dataclass
class Journey:
    journey_id: str
    direction: str
    start_time: datetime
    origin: dict
    boundary: dict
    reinforcement_count: int = 0
    activation_ids: list[str] = field(default_factory=list)
    end_time: Optional[datetime] = None
    end_reason: Optional[str] = None
    failure_h4_open_time: Optional[datetime] = None


def _decision_row(activation: dict, action: str, journey: Optional[Journey], prior_journey_id: Optional[str]) -> dict:
    row = dict(activation)
    row.update(
        {
            "contract_version": CONTRACT_VERSION,
            "state_action": action,
            "journey_id": journey.journey_id if journey else None,
            "prior_journey_id": prior_journey_id,
            "reinforcement_ordinal": journey.reinforcement_count if journey else None,
            "outcome_fields_present": False,
        }
    )
    return row


def build_journey_state(
    activations: list[dict], h4_bars: list[CompletedBar], cutoff: datetime
) -> tuple[list[Journey], list[dict]]:
    """Resolve H4 failures before same-timestamp activation groups."""

    by_time: dict[datetime, list[dict]] = {}
    for activation in activations:
        by_time.setdefault(activation["activation_time"], []).append(activation)
    bars_by_time: dict[datetime, list[CompletedBar]] = {}
    for bar in h4_bars:
        bars_by_time.setdefault(bar.completed_by_observation, []).append(bar)

    timeline = sorted(set(by_time) | set(bars_by_time))
    journeys: list[Journey] = []
    decisions: list[dict] = []
    current: Optional[Journey] = None

    def end_current(timestamp: datetime, reason: str, failure_bar: Optional[CompletedBar] = None) -> None:
        nonlocal current
        if current is None:
            return
        current.end_time = timestamp
        current.end_reason = reason
        current.failure_h4_open_time = failure_bar.open_time if failure_bar else None
        current = None

    for timestamp in timeline:
        if timestamp > cutoff:
            break
        for bar in sorted(bars_by_time.get(timestamp, []), key=lambda item: item.open_time):
            if current is not None and boundary_failed(current.boundary, bar):
                end_current(timestamp, "STRUCTURAL_FAILURE", bar)

        group = sorted(
            by_time.get(timestamp, []),
            key=lambda item: (item["c2_open_time"], item["activation_id"]),
        )
        if not group:
            continue
        directions = {item["direction"] for item in group}
        if len(directions) > 1:
            prior = current.journey_id if current else None
            end_current(timestamp, "SIMULTANEOUS_CONFLICT")
            decisions.extend(_decision_row(item, "CONFLICT_NO_START", None, prior) for item in group)
            continue

        direction = group[0]["direction"]
        if current is not None and current.direction != direction:
            prior = current.journey_id
            end_current(timestamp, "OPPOSITE_ACTIVATION")
        else:
            prior = current.journey_id if current else None

        for index, activation in enumerate(group):
            if current is None:
                current = Journey(
                    journey_id=journey_id(activation),
                    direction=direction,
                    start_time=timestamp,
                    origin=activation,
                    boundary=activation,
                    activation_ids=[activation["activation_id"]],
                )
                journeys.append(current)
                decisions.append(_decision_row(activation, "START", current, prior))
            else:
                current.reinforcement_count += 1
                current.boundary = activation
                current.activation_ids.append(activation["activation_id"])
                decisions.append(_decision_row(activation, "REINFORCEMENT", current, prior if index == 0 else None))

    if current is not None:
        current.end_time = cutoff
        current.end_reason = "OPEN_AT_CUTOFF"
    return journeys, decisions


def journey_at(journeys: list[Journey], timestamp: datetime) -> Optional[Journey]:
    # Journey intervals are [start, end); OPEN_AT_CUTOFF includes the cutoff.
    for journey in journeys:
        if journey.start_time <= timestamp and (
            journey.end_time is None
            or timestamp < journey.end_time
            or (journey.end_reason == "OPEN_AT_CUTOFF" and timestamp <= journey.end_time)
        ):
            return journey
    return None


def milestone_stage(journey: Journey, timestamp: datetime, outcome: dict) -> str:
    opposite = outcome.get("opposite_edge_time")
    midpoint = outcome.get("midpoint_time")
    if opposite and datetime.fromisoformat(opposite) < timestamp:
        return "AFTER_OPPOSITE_EDGE"
    if outcome.get("opposite_edge_forward_eligible") is False:
        return "AFTER_OPPOSITE_EDGE_AT_ACTIVATION"
    if midpoint and datetime.fromisoformat(midpoint) < timestamp:
        return "AFTER_MIDPOINT"
    if outcome.get("midpoint_forward_eligible") is False:
        return "AFTER_MIDPOINT_AT_ACTIVATION"
    return "BEFORE_MIDPOINT"
