"""Pure helpers for the V12 Phase-1C carry/repair shadow study."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


CONTRACT_VERSION = "v12-phase1c-crt-protected-carry-repair-v1"
ELIGIBLE_FLIP_STATES = {
    "OLD_JOURNEY_COUNTERFLOW",
    "OLD_JOURNEY_AFTER_KEY_ARRIVAL",
}


def parse_time(value: str | None) -> Optional[datetime]:
    if value in (None, ""):
        return None
    return datetime.fromisoformat(str(value).replace(" ", "T"))


def direction_name(value: int | str) -> str:
    if isinstance(value, str) and value in {"LONG", "SHORT"}:
        return value
    return "LONG" if int(value) == 1 else "SHORT"


def direction_sign(value: int | str) -> int:
    return 1 if direction_name(value) == "LONG" else -1


def target_open_at(journey_outcome: dict, timestamp: datetime) -> bool:
    if str(journey_outcome.get("opposite_edge_forward_eligible", "")).lower() != "true":
        return False
    touched = parse_time(journey_outcome.get("opposite_edge_time"))
    return touched is None or touched >= timestamp


def carry_is_eligible(child_context: dict, full_child: dict, flip: dict) -> bool:
    return (
        child_context.get("relation") == "ALIGNED_ACTIVE_JOURNEY"
        and full_child.get("exit_reason") == "FAST_NHA"
        and bool(child_context.get("journey_id"))
        and flip.get("explanation_state") in ELIGIBLE_FLIP_STATES
        and flip.get("active_journey_id") == child_context.get("journey_id")
        and flip.get("old_fast_direction") == child_context.get("direction")
    )


def repair_is_confirmed(start_flip: dict, repair_flip: dict, journey_id: str) -> bool:
    return (
        repair_flip.get("new_fast_direction") == start_flip.get("old_fast_direction")
        and repair_flip.get("active_journey_id") == journey_id
    )


@dataclass
class GuardSpec:
    spec_id: str
    kind: str
    direction: int
    entry: float
    stop: float
    start_time: datetime
    terminal_time: datetime
    include_start_m1: bool
    journey_id: str
    bridge_id: str
    target_open: bool
    signal_id: Optional[str] = None
    units: float = 1.0

    @property
    def risk(self) -> float:
        return abs(self.entry - self.stop)


def stop_touched(spec: GuardSpec, high: float, low: float) -> bool:
    return low <= spec.stop if spec.direction > 0 else high >= spec.stop


def stop_gap(spec: GuardSpec, open_price: float) -> bool:
    return open_price <= spec.stop if spec.direction > 0 else open_price >= spec.stop


def realized_r(spec: GuardSpec, exit_price: float) -> float:
    if spec.risk <= 0.0:
        raise ValueError(f"non-positive risk for {spec.spec_id}")
    return spec.direction * (exit_price - spec.entry) / spec.risk


def max_stop_chain(rows: list[dict]) -> int:
    longest = current = 0
    for row in sorted(rows, key=lambda item: (parse_time(item["exit_time"]), item["signal_id"])):
        if int(row["stop_hit"]):
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def maximum_drawdown(rows: list[dict]) -> float:
    grouped: dict[datetime, float] = {}
    for row in rows:
        timestamp = parse_time(row["exit_time"])
        grouped[timestamp] = grouped.get(timestamp, 0.0) + float(row["combined_R_units"])
    equity = peak = drawdown = 0.0
    for timestamp in sorted(grouped):
        equity += grouped[timestamp]
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return drawdown


def maximum_concurrent_units(rows: list[dict]) -> float:
    times = sorted({parse_time(row["entry_time"]) for row in rows} | {parse_time(row["exit_time"]) for row in rows})
    live = maximum = 0.0
    for timestamp in times:
        live -= sum(
            float(row["funded_units"])
            for row in rows
            if parse_time(row["exit_time"]) == timestamp and parse_time(row["entry_time"]) < timestamp
        )
        live += sum(
            float(row["funded_units"])
            for row in rows
            if parse_time(row["entry_time"]) == timestamp and parse_time(row["exit_time"]) > timestamp
        )
        maximum = max(maximum, live)
    return maximum


def exposure_metrics(rows: list[dict]) -> dict:
    exits: dict[datetime, float] = {}
    entries: dict[datetime, float] = {}
    for row in rows:
        entry = parse_time(row["entry_time"])
        exit_ = parse_time(row["exit_time"])
        units = float(row["funded_units"])
        if exit_ > entry:
            entries[entry] = entries.get(entry, 0.0) + units
            exits[exit_] = exits.get(exit_, 0.0) + units
    times = sorted(set(entries) | set(exits))
    if not times:
        return {"funded_unit_hours": 0.0, "calendar_mean_gross_units": 0.0, "invested_time_mean_gross_units": 0.0}
    live = weighted_seconds = invested_seconds = 0.0
    first_time = last_time = times[0]
    for timestamp in times:
        elapsed = (timestamp - last_time).total_seconds()
        weighted_seconds += elapsed * live
        if live > 0.0:
            invested_seconds += elapsed
        live -= exits.get(timestamp, 0.0)
        live += entries.get(timestamp, 0.0)
        if live < -1e-9:
            raise ValueError("negative concurrent exposure")
        last_time = timestamp
    total_seconds = (last_time - first_time).total_seconds()
    return {
        "funded_unit_hours": weighted_seconds / 3600.0,
        "calendar_mean_gross_units": weighted_seconds / total_seconds if total_seconds else 0.0,
        "invested_time_mean_gross_units": weighted_seconds / invested_seconds if invested_seconds else 0.0,
    }


def summarize(rows: list[dict]) -> dict:
    gross_profit = sum(max(0.0, float(row["combined_R_units"])) for row in rows)
    gross_loss = -sum(min(0.0, float(row["combined_R_units"])) for row in rows)
    funded = sum(float(row["funded_units"]) for row in rows)
    stopped = sum(float(row["stopped_loss_units"]) for row in rows)
    net_r = sum(float(row["combined_R_units"]) for row in rows)
    result = {
        "children": len(rows),
        "funded_units": funded,
        "stops": sum(int(row["stop_hit"]) for row in rows),
        "stopped_units": stopped,
        "stopped_units_per_100_funded": 100.0 * stopped / funded if funded else None,
        "net_R": net_r,
        "R_per_100_funded": 100.0 * net_r / funded if funded else None,
        "profit_factor_R": gross_profit / gross_loss if gross_loss else None,
        "right_tail_ge_5R_units": sum(
            float(row["combined_R_units"])
            for row in rows
            if float(row["combined_R_units"]) >= 5.0
        ),
        "max_stop_chain": max_stop_chain(rows),
        "realized_close_grouped_max_drawdown_R": maximum_drawdown(rows),
        "max_concurrent_units": maximum_concurrent_units(rows),
    }
    result.update(exposure_metrics(rows))
    return result
