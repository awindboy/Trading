"""Pure target-succession primitives for the V12 Phase-1F mechanism study."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

from v12_phase0_core import price_points
from v12_phase1b_core import stable_id


CONTRACT_VERSION = "v12-phase1f-parent-target-succession-v1"


def parse_time(value: object) -> Optional[datetime]:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace(" ", "T"))


def ahead(direction: str, price: float, frontier: float) -> bool:
    if direction == "LONG":
        return price_points(price) > price_points(frontier)
    if direction == "SHORT":
        return price_points(price) < price_points(frontier)
    raise ValueError(f"unsupported direction: {direction}")


def advance_frontier(direction: str, frontier: float, *prices: Optional[float]) -> float:
    values = [frontier] + [float(value) for value in prices if value is not None]
    if direction == "LONG":
        return max(values)
    if direction == "SHORT":
        return min(values)
    raise ValueError(f"unsupported direction: {direction}")


@dataclass(frozen=True)
class Level:
    level_id: str
    family: str
    side: str
    price: float
    known_at: datetime
    consumed_at: Optional[datetime]


def active_at(level: Level, timestamp: datetime) -> bool:
    # A breach stamped on this M1 was not known at the M1 open.
    return level.known_at <= timestamp and (level.consumed_at is None or level.consumed_at >= timestamp)


def choose_external_cluster(
    levels: Iterable[Level], direction: str, timestamp: datetime, frontier: float
) -> list[Level]:
    side = "HIGH" if direction == "LONG" else "LOW"
    eligible = [
        level
        for level in levels
        if level.side == side
        and active_at(level, timestamp)
        and ahead(direction, level.price, frontier)
    ]
    if not eligible:
        return []
    chosen_points = (
        min(price_points(level.price) for level in eligible)
        if direction == "LONG"
        else max(price_points(level.price) for level in eligible)
    )
    return sorted(
        [level for level in eligible if price_points(level.price) == chosen_points],
        key=lambda level: (level.family, level.known_at, level.level_id),
    )


def target_id(journey_id: str, selected_at: datetime, kind: str, price: float, member_ids: list[str]) -> str:
    return stable_id(
        "v12target-",
        {
            "contract": CONTRACT_VERSION,
            "journey_id": journey_id,
            "selected_at": selected_at.isoformat(),
            "kind": kind,
            "price_points": price_points(price),
            "member_ids": sorted(member_ids),
        },
    )


def state_at(
    journey: dict,
    target_outcomes: list[dict],
    query_time: datetime,
) -> dict:
    start = parse_time(journey["start_time"])
    end = parse_time(journey["end_time"])
    if query_time < start:
        return {"target_state": "NO_ACTIVE_PARENT", "target_id": None}
    if end is not None and query_time >= end:
        return {"target_state": "PARENT_INVALIDATED", "target_id": None}
    selected = [row for row in target_outcomes if parse_time(row["selected_at"]) <= query_time]
    if not selected:
        return {"target_state": "TARGET_COMPLETE_REFRAME_PENDING", "target_id": None}
    latest = max(selected, key=lambda row: (parse_time(row["selected_at"]), row["target_id"]))
    completed = parse_time(latest.get("completed_at"))
    if completed is None or completed >= query_time:
        return {
            "target_state": "TARGET_UNFINISHED",
            "target_id": latest["target_id"],
            "target_kind": latest["target_kind"],
            "target_price": latest["target_price"],
            "target_selected_at": latest["selected_at"],
            "target_distance_atr180": latest.get("distance_atr180"),
            "target_member_families": latest.get("member_families", ""),
            "target_selection_reason": latest.get("selection_reason", ""),
            "target_skipped_internal_targets": latest.get("skipped_internal_targets", ""),
        }
    return {
        "target_state": "TARGET_COMPLETE_REFRAME_PENDING",
        "target_id": latest["target_id"],
        "target_kind": latest["target_kind"],
        "target_price": latest["target_price"],
        "target_selected_at": latest["selected_at"],
        "target_completed_at": latest.get("completed_at"),
        "target_member_families": latest.get("member_families", ""),
        "target_selection_reason": latest.get("selection_reason", ""),
        "target_skipped_internal_targets": latest.get("skipped_internal_targets", ""),
    }
