from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

import numpy as np


class Direction(StrEnum):
    LONG = "long"
    SHORT = "short"


class Side(StrEnum):
    HIGH = "high"
    LOW = "low"


class ScenarioScope(StrEnum):
    EXTERNAL_CONTINUATION = "EXTERNAL_CONTINUATION"
    INTERNAL_ROTATION = "INTERNAL_ROTATION"
    EXTERNAL_REVERSAL = "EXTERNAL_REVERSAL"


class LiquidityKind(StrEnum):
    EXTERNAL_SWING = "EXTERNAL_SWING"
    REACTION_TRAP = "REACTION_TRAP"
    RANGE_EDGE = "RANGE_EDGE"
    TRENDLINE_CLUSTER = "TRENDLINE_CLUSTER"


class ZoneKind(StrEnum):
    FVG = "FVG"
    FVG_ORIGIN_OB = "FVG_ORIGIN_OB"
    LAST_OPPOSITE_OB = "LAST_OPPOSITE_OB"


@dataclass(frozen=True)
class EngineConfig:
    point: float = 0.01
    broker_stops_level_price: float = 0.0
    min_lot: float = 0.01
    map_timeframes: tuple[str, ...] = ("H1", "M30")
    context_timeframes: tuple[str, ...] = ("H1", "M30", "M15", "M5")
    # M5 describes the correction context; only M1 may authorize execution.
    trigger_timeframes: tuple[str, ...] = ("M1",)
    trade_from: int | None = None
    trade_to: int | None = None


@dataclass(frozen=True)
class BarSeries:
    timeframe: str
    seconds: int
    time: np.ndarray
    available_time: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    spread_points: np.ndarray

    def __len__(self) -> int:
        return int(self.time.size)


@dataclass
class WavePoint:
    object_id: str
    timeframe: str
    side: Side
    index: int
    confirmed_index: int
    occurred_at: int
    available_at: int
    level: float
    wick_bottom: float
    wick_top: float
    rank: str = "internal"
    rank_available_at: int | None = None


@dataclass(frozen=True)
class StructureEvent:
    event_id: str
    timeframe: str
    index: int
    occurred_at: int
    available_at: int
    direction: Direction
    event_type: str
    broken_swing_id: str
    broken_level: float
    protected_swing_id: str | None
    protected_level: float | None
    range_low: float | None
    range_high: float | None


@dataclass
class StructureAnalysis:
    timeframe: str
    waves: list[WavePoint]
    events: list[StructureEvent]
    trend: np.ndarray
    protected_high: np.ndarray
    protected_low: np.ndarray
    range_low: np.ndarray
    range_high: np.ndarray


@dataclass
class Zone:
    object_id: str
    family_id: str
    timeframe: str
    kind: ZoneKind
    direction: Direction
    origin_index: int
    confirmed_index: int
    occurred_at: int
    available_at: int
    bottom: float
    top: float
    linked_structure_event_id: str | None = None
    first_touch_index: int | None = None
    consumed_index: int | None = None
    consumed_at: int | None = None
    partial_fills: list[tuple[int, float, float]] = field(default_factory=list)

    def active_at(self, timestamp: int) -> bool:
        return self.available_at <= timestamp and (
            self.consumed_at is None or timestamp < self.consumed_at
        )

    def bounds_at(self, timestamp: int) -> tuple[float, float]:
        bottom = self.bottom
        top = self.top
        for fill_at, remaining_bottom, remaining_top in self.partial_fills:
            if fill_at > timestamp:
                break
            bottom = remaining_bottom
            top = remaining_top
        return float(bottom), float(top)


@dataclass
class LiquidityPool:
    object_id: str
    timeframe: str
    kind: LiquidityKind
    side: Side
    created_index: int
    occurred_at: int
    available_at: int
    bottom: float
    top: float
    source_wave_ids: list[str]
    consumed_index: int | None = None
    consumed_at: int | None = None

    @property
    def level(self) -> float:
        return self.top if self.side == Side.HIGH else self.bottom

    def active_at(self, timestamp: int) -> bool:
        return self.available_at <= timestamp and (
            self.consumed_at is None or timestamp < self.consumed_at
        )


@dataclass(frozen=True)
class SweepEvent:
    event_id: str
    timeframe: str
    index: int
    occurred_at: int
    available_at: int
    pool_id: str
    pool_kind: LiquidityKind
    side: Side
    extreme: float
    close: float


@dataclass
class DestinationPlan:
    plan_id: str
    direction: Direction
    scope: ScenarioScope
    planned_at: int
    map_timeframe: str
    map_structure_event_id: str
    map_trend: int
    map_protected_level: float | None
    dealing_range_low: float
    dealing_range_high: float
    source_timeframe: str
    source_pool_id: str
    source_zone_ids: list[str]
    parent_zone_ids: list[str]
    refinement_path: list[str]
    source_bottom: float
    source_top: float
    objective_kind: str
    objective_id: str
    objective_price: float
    state: str = "PLANNED"
    sweep_event_id: str | None = None
    activated_at: int | None = None
    rejection_reason: str | None = None


@dataclass
class Scenario:
    scenario_id: str
    plan_id: str
    direction: Direction
    scope: ScenarioScope
    map_timeframe: str
    context_timeframe: str
    trigger_timeframe: str | None
    source_pool_id: str
    source_zone_ids: list[str]
    sweep_event_id: str
    created_at: int
    source_price: float
    objective_kind: str
    objective_id: str
    objective_price: float
    map_trend: int
    dealing_range_low: float | None
    dealing_range_high: float | None
    state: str = "CONTEXT_ARMED"
    rejection_reason: str | None = None
    trigger_event_id: str | None = None
    entry_zone_id: str | None = None
    planned_at: int | None = None
    map_structure_event_id: str | None = None
    parent_zone_ids: list[str] = field(default_factory=list)
    refinement_path: list[str] = field(default_factory=list)
    absorbed_sweep_event_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class OrderPlan:
    order_id: str
    scenario_id: str
    direction: Direction
    created_at: int
    entry: float
    stop_loss: float
    take_profit: float
    entry_zone_id: str
    entry_zone_bottom: float
    entry_zone_top: float
    source_sweep_extreme: float
    spread_price: float
    map_timeframe: str
    context_timeframe: str
    trigger_timeframe: str
    objective_id: str
    cancel_structure_level: float | None
    protective_zone_bottom: float
    protective_zone_top: float
    entry_family_zone_ids: tuple[str, ...] = ()
    parent_zone_ids: tuple[str, ...] = ()


@dataclass
class TradeResult:
    trade_id: str
    order_id: str
    scenario_id: str
    direction: Direction
    order_time: int
    entry_time: int | None
    exit_time: int | None
    entry: float
    stop_loss: float
    take_profit: float
    exit_price: float | None
    result: str
    pnl_r: float
    holding_minutes: int | None
    explanation: list[str] = field(default_factory=list)


def jsonable(value: Any) -> Any:
    if hasattr(value, "value"):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {key: jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value
