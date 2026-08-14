from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any

import numpy as np

from .casebook import validate_casebook
from .data import build_timeframes, index_at_or_before
from .execution import simulate_order
from .liquidity import build_liquidity
from .models import (
    BarSeries,
    DestinationPlan,
    Direction,
    EngineConfig,
    LiquidityPool,
    OrderPlan,
    Scenario,
    Side,
    StructureAnalysis,
    StructureEvent,
    SweepEvent,
    TradeResult,
    Zone,
    ZoneKind,
)
from .planner import DestinationPlanner
from .structure import analyze_structure
from .zones import detect_zones


@dataclass
class TimeframeState:
    series: BarSeries
    structure: StructureAnalysis
    zones: list[Zone]
    liquidity: list[LiquidityPool]
    sweeps: list[SweepEvent]


def protective_stop(
    direction: Direction,
    sweep_extreme: float,
    entry_bottom: float,
    entry_top: float,
    protective_bottom: float,
    protective_top: float,
    buffer: float,
) -> float:
    if direction == Direction.LONG:
        return min(sweep_extreme, entry_bottom, protective_bottom) - buffer
    return max(sweep_extreme, entry_top, protective_top) + buffer


def correction_leg_matches(direction: Direction, latest_wave_side: Side) -> bool:
    return (
        latest_wave_side == Side.HIGH
        if direction == Direction.LONG
        else latest_wave_side == Side.LOW
    )


class MentorScenarioEngine:
    def __init__(self, m1: BarSeries, config: EngineConfig | None = None) -> None:
        self.config = config or EngineConfig()
        self.series = build_timeframes(m1)
        self.states: dict[str, TimeframeState] = {}
        self.plans: list[DestinationPlan] = []
        self.scenarios: list[Scenario] = []
        self.candidate_orders: list[OrderPlan] = []
        self.orders: list[OrderPlan] = []
        self.trades: list[TradeResult] = []
        self.rejections: list[dict[str, Any]] = []
        self._trigger_diagnostics: set[tuple[str, str]] = set()

    def prepare(self) -> None:
        for timeframe, series in self.series.items():
            structure = analyze_structure(series)
            zones = detect_zones(series, structure)
            liquidity, sweeps = build_liquidity(series, structure, zones)
            self.states[timeframe] = TimeframeState(
                series=series,
                structure=structure,
                zones=zones,
                liquidity=liquidity,
                sweeps=sweeps,
            )

    def run(self) -> dict[str, Any]:
        if not self.states:
            self.prepare()
        self.plans = []
        self.scenarios = []
        self.candidate_orders = []
        self.orders = []
        self.trades = []
        self.rejections = []
        self._trigger_diagnostics = set()

        planner = DestinationPlanner(self.states, self.config)
        self.plans = planner.build()
        sweeps = [
            sweep
            for timeframe in self.config.context_timeframes
            for sweep in self.states[timeframe].sweeps
        ]
        self.scenarios, self.rejections = planner.activate(self.plans, sweeps)
        self._bind_triggers_and_orders()
        self.candidate_orders = list(self.orders)
        self.orders = []
        self._execute_candidate_orders()
        return self.summary()

    def _zone_by_id(self) -> dict[str, Zone]:
        return {
            zone.object_id: zone
            for state in self.states.values()
            for zone in state.zones
        }

    def _sweep_by_id(self) -> dict[str, SweepEvent]:
        return {
            sweep.event_id: sweep
            for state in self.states.values()
            for sweep in state.sweeps
        }

    def _snapshot(self, timeframe: str, timestamp: int) -> dict[str, Any] | None:
        state = self.states[timeframe]
        index = index_at_or_before(state.series, timestamp)
        if index < 0:
            return None
        return {
            "index": index,
            "trend": int(state.structure.trend[index]),
            "protectedHigh": _finite(state.structure.protected_high[index]),
            "protectedLow": _finite(state.structure.protected_low[index]),
            "rangeLow": _finite(state.structure.range_low[index]),
            "rangeHigh": _finite(state.structure.range_high[index]),
        }

    def _scenario_bounds(self, scenario: Scenario) -> tuple[float, float]:
        zones = self._zone_by_id()
        selected = [
            zones[zone_id]
            for zone_id in scenario.source_zone_ids + scenario.parent_zone_ids
            if zone_id in zones
        ]
        bounds = [zone.bounds_at(scenario.created_at - 1) for zone in selected]
        return min(item[0] for item in bounds), max(item[1] for item in bounds)

    def _objective_delivered_before(self, scenario: Scenario, timestamp: int) -> bool:
        m1 = self.series["M1"]
        start = int(np.searchsorted(m1.available_time, scenario.created_at, side="left"))
        end = int(np.searchsorted(m1.available_time, timestamp, side="left"))
        if end <= start:
            return False
        if scenario.direction == Direction.LONG:
            return bool(np.max(m1.high[start:end]) >= scenario.objective_price)
        spread = m1.spread_points[start:end] * self.config.point
        return bool(np.min(m1.low[start:end] + spread) <= scenario.objective_price)

    def _source_invalid_before(self, scenario: Scenario, timestamp: int) -> bool:
        bottom, top = self._scenario_bounds(scenario)
        m1 = self.series["M1"]
        start = int(np.searchsorted(m1.available_time, scenario.created_at, side="left"))
        end = int(np.searchsorted(m1.available_time, timestamp, side="left"))
        if end <= start:
            return False
        if scenario.direction == Direction.LONG:
            return bool(np.any(m1.close[start:end] < bottom))
        return bool(np.any(m1.close[start:end] > top))

    def _linked_entry_family(
        self, event: StructureEvent
    ) -> tuple[Zone, list[Zone]] | None:
        linked = [
            zone
            for zone in self.states[event.timeframe].zones
            if zone.direction == event.direction
            and zone.linked_structure_event_id == event.event_id
            and zone.kind == ZoneKind.LAST_OPPOSITE_OB
            and zone.available_at >= event.available_at
        ]
        families: dict[str, list[Zone]] = {}
        for zone in linked:
            families.setdefault(zone.family_id, []).append(zone)
        family_entries: list[tuple[Zone, list[Zone]]] = []
        for family in families.values():
            selected = min(
                family,
                key=lambda item: (
                    item.available_at,
                    item.top - item.bottom,
                    item.object_id,
                ),
            )
            family_entries.append((selected, family))
        if len(family_entries) != 1:
            return None
        return family_entries[0]

    def _execution_chain_key(
        self,
        scenario: Scenario,
        order: OrderPlan,
    ) -> tuple[object, ...]:
        return (
            scenario.map_structure_event_id,
            scenario.source_pool_id,
            tuple(scenario.refinement_path),
            tuple(scenario.absorbed_sweep_event_ids or [scenario.sweep_event_id]),
            scenario.trigger_event_id,
            order.entry_zone_id,
            order.objective_id,
        )

    def _execute_candidate_orders(self) -> None:
        zone_by_id = self._zone_by_id()
        scenario_by_id = {item.scenario_id: item for item in self.scenarios}
        m1 = self.series["M1"]
        replay_end = (
            self.config.trade_to
            if self.config.trade_to is not None
            else int(m1.available_time[-1]) + int(m1.seconds)
        )
        active_until: int | None = None
        active_order_id: str | None = None
        used_chains: set[tuple[object, ...]] = set()

        for order in sorted(
            self.candidate_orders,
            key=lambda item: (item.created_at, item.order_id),
        ):
            scenario = scenario_by_id[order.scenario_id]
            chain_key = self._execution_chain_key(scenario, order)
            if chain_key in used_chains:
                scenario.state = "REJECTED_EXECUTION_POLICY"
                scenario.rejection_reason = "DUPLICATE_CAUSAL_CHAIN"
                self.rejections.append(
                    {
                        "recordType": "execution_rejection",
                        "scenarioId": scenario.scenario_id,
                        "orderId": order.order_id,
                        "availableAt": order.created_at,
                        "reason": "DUPLICATE_CAUSAL_CHAIN",
                    }
                )
                continue
            if active_until is not None and order.created_at <= active_until:
                scenario.state = "REJECTED_EXECUTION_POLICY"
                scenario.rejection_reason = "ACTIVE_ORDER_OR_POSITION"
                self.rejections.append(
                    {
                        "recordType": "execution_rejection",
                        "scenarioId": scenario.scenario_id,
                        "orderId": order.order_id,
                        "blockedByOrderId": active_order_id,
                        "availableAt": order.created_at,
                        "reason": "ACTIVE_ORDER_OR_POSITION",
                    }
                )
                continue

            trade = simulate_order(
                m1,
                order,
                zone_by_id[order.entry_zone_id],
                self.config.point,
                self.config.trade_to,
            )
            trade.explanation = self._explain(scenario, order, trade)
            self.orders.append(order)
            self.trades.append(trade)
            used_chains.add(chain_key)
            active_order_id = order.order_id
            active_until = trade.exit_time
            if trade.result == "OPEN" or active_until is None:
                active_until = replay_end

    def _m1_confirms_m5_correction(
        self, event: StructureEvent, scenario: Scenario
    ) -> tuple[bool, str | None]:
        at_sweep = self._snapshot("M5", scenario.created_at - 1)
        before_trigger = self._snapshot("M5", event.available_at - 1)
        if not at_sweep or not before_trigger:
            return False, "M5_SNAPSHOT_UNAVAILABLE"
        waves = [
            wave
            for wave in self.states["M5"].structure.waves
            if wave.available_at < scenario.created_at
        ]
        if not waves:
            return False, "NO_PRE_SWEEP_M5_WAVE"
        latest_wave = max(waves, key=lambda item: (item.available_at, item.object_id))
        if not correction_leg_matches(scenario.direction, latest_wave.side):
            return False, "M5_LEG_IS_NOT_CORRECTING_TOWARD_SOURCE"
        zones = self._zone_by_id()
        source = [zones[item] for item in scenario.source_zone_ids]
        source_bottom = min(
            zone.bounds_at(scenario.created_at - 1)[0] for zone in source
        )
        source_top = max(
            zone.bounds_at(scenario.created_at - 1)[1] for zone in source
        )
        if (
            at_sweep["rangeLow"] is None
            or at_sweep["rangeHigh"] is None
            or not at_sweep["rangeLow"] <= scenario.source_price <= at_sweep["rangeHigh"]
            or not (
                at_sweep["rangeLow"] <= event.broken_level <= at_sweep["rangeHigh"]
            )
        ):
            return False, "M1_BREAK_NOT_INSIDE_M5_CORRECTION_RANGE"
        wanted = 1 if scenario.direction == Direction.LONG else -1
        if before_trigger["trend"] in {-wanted, wanted}:
            return True, None
        parent_reversals = [
            item
            for item in self.states["M5"].structure.events
            if item.event_type == "CHOCH"
            and item.direction == scenario.direction
            and scenario.created_at < item.available_at <= event.available_at
        ]
        if not parent_reversals:
            return False, "NO_M5_REVERSAL_PARENT_FOR_M1_CHILD"
        parent = max(parent_reversals, key=lambda item: item.available_at)
        valid = (
            parent.range_low is not None
            and parent.range_high is not None
            and parent.range_low <= event.broken_level <= parent.range_high
        )
        return valid, None if valid else "M1_BREAK_OUTSIDE_M5_REVERSAL_PARENT"

    def _trigger_belongs_to_scenario(
        self, event: StructureEvent, scenario: Scenario
    ) -> bool:
        if event.timeframe != "M1":
            return False
        if event.available_at <= scenario.created_at:
            return False
        if event.direction != scenario.direction:
            return False
        if self._source_invalid_before(scenario, event.available_at):
            scenario.state = "REJECTED"
            scenario.rejection_reason = "PARENT_SOURCE_INVALIDATED"
            return False
        if self._objective_delivered_before(scenario, event.available_at):
            scenario.state = "REJECTED"
            scenario.rejection_reason = "OBJECTIVE_DELIVERED_BEFORE_TRIGGER"
            return False
        valid, reason = self._m1_confirms_m5_correction(event, scenario)
        if not valid and reason is not None:
            key = (scenario.scenario_id, reason)
            if key not in self._trigger_diagnostics:
                self._trigger_diagnostics.add(key)
                self.rejections.append(
                    {
                        "recordType": "trigger_rejection",
                        "scenarioId": scenario.scenario_id,
                        "triggerEventId": event.event_id,
                        "availableAt": event.available_at,
                        "reason": reason,
                    }
                )
        return valid

    def _bind_triggers_and_orders(self) -> None:
        trigger_events = sorted(
            (
                event
                for event in self.states["M1"].structure.events
                if event.event_type == "CHOCH"
            ),
            key=lambda item: (item.available_at, item.timeframe, item.event_id),
        )
        plan_by_id = {plan.plan_id: plan for plan in self.plans}
        sweep_by_id = self._sweep_by_id()
        zone_by_id = self._zone_by_id()
        m1 = self.series["M1"]

        for event in trigger_events:
            entry_family = self._linked_entry_family(event)
            if entry_family is None:
                continue
            entry_zone, protective_family = entry_family
            candidates = [
                scenario
                for scenario in self.scenarios
                if scenario.state == "CONTEXT_ARMED"
                and self._trigger_belongs_to_scenario(event, scenario)
            ]
            if not candidates:
                continue
            owners = {
                (
                    scenario.direction,
                    scenario.map_structure_event_id,
                    scenario.objective_id,
                    tuple(scenario.source_zone_ids),
                    tuple(scenario.refinement_path),
                )
                for scenario in candidates
            }
            if len(owners) != 1:
                for scenario in candidates:
                    scenario.state = "REJECTED"
                    scenario.rejection_reason = "AMBIGUOUS_PLAN_TRIGGER_OWNERSHIP"
                continue
            # Repeated sweeps inside one source-zone touch episode are one
            # causal chain. The final sweep owns the trigger while every
            # episode extreme remains part of the protective stop.
            scenario = max(
                candidates,
                key=lambda item: (item.created_at, item.scenario_id),
            )
            absorbed = sorted(
                {
                    sweep_id
                    for item in candidates
                    for sweep_id in (
                        item.absorbed_sweep_event_ids or [item.sweep_event_id]
                    )
                }
            )
            scenario.absorbed_sweep_event_ids = absorbed
            for merged in candidates:
                if merged is scenario:
                    continue
                merged.state = "MERGED_TOUCH_EPISODE"
                merged.rejection_reason = "MERGED_INTO_FINAL_SOURCE_SWEEP"
            if self._objective_delivered_before(scenario, entry_zone.available_at):
                scenario.state = "REJECTED"
                scenario.rejection_reason = "OBJECTIVE_DELIVERED_BEFORE_ORDER"
                continue
            m1_index = index_at_or_before(m1, entry_zone.available_at)
            if m1_index < 0:
                scenario.state = "REJECTED"
                scenario.rejection_reason = "NO_M1_EXECUTION_BAR"
                continue

            spread_price = float(m1.spread_points[m1_index]) * self.config.point
            buffer = max(
                self.config.broker_stops_level_price,
                spread_price,
                self.config.point,
            )
            entry_bottom, entry_top = entry_zone.bounds_at(entry_zone.available_at)
            entry = entry_top if scenario.direction == Direction.LONG else entry_bottom
            episode_sweeps = [sweep_by_id[item] for item in absorbed]
            sweep_extreme = (
                min(item.extreme for item in episode_sweeps)
                if scenario.direction == Direction.LONG
                else max(item.extreme for item in episode_sweeps)
            )
            protective_bounds = [
                zone.bounds_at(entry_zone.available_at) for zone in protective_family
            ]
            protective_bottom = min(item[0] for item in protective_bounds)
            protective_top = max(item[1] for item in protective_bounds)
            stop = protective_stop(
                scenario.direction,
                sweep_extreme,
                entry_bottom,
                entry_top,
                protective_bottom,
                protective_top,
                buffer,
            )
            valid_geometry = (
                stop < entry < scenario.objective_price
                if scenario.direction == Direction.LONG
                else scenario.objective_price < entry < stop
            )
            if not valid_geometry:
                scenario.state = "REJECTED"
                scenario.rejection_reason = "INVALID_ENTRY_SL_TP_GEOMETRY"
                continue

            destination_plan = plan_by_id[scenario.plan_id]
            scenario.trigger_timeframe = event.timeframe
            scenario.trigger_event_id = event.event_id
            scenario.entry_zone_id = entry_zone.object_id
            scenario.state = "ORDERED"
            self.orders.append(
                OrderPlan(
                    order_id=f"order:{scenario.scenario_id}:{event.event_id}",
                    scenario_id=scenario.scenario_id,
                    direction=scenario.direction,
                    created_at=entry_zone.available_at,
                    entry=float(entry),
                    stop_loss=float(stop),
                    take_profit=float(scenario.objective_price),
                    entry_zone_id=entry_zone.object_id,
                    entry_zone_bottom=float(entry_bottom),
                    entry_zone_top=float(entry_top),
                    source_sweep_extreme=float(sweep_extreme),
                    spread_price=spread_price,
                    map_timeframe=scenario.map_timeframe,
                    context_timeframe=scenario.context_timeframe,
                    trigger_timeframe=event.timeframe,
                    objective_id=scenario.objective_id,
                    cancel_structure_level=destination_plan.map_protected_level,
                    protective_zone_bottom=float(protective_bottom),
                    protective_zone_top=float(protective_top),
                    entry_family_zone_ids=tuple(
                        zone.object_id for zone in protective_family
                    ),
                    parent_zone_ids=tuple(scenario.parent_zone_ids),
                )
            )

        replay_end = self.config.trade_to or int(m1.available_time[-1]) + 1
        for scenario in self.scenarios:
            if scenario.state != "CONTEXT_ARMED":
                continue
            scenario.state = "REJECTED"
            if self._source_invalid_before(scenario, replay_end):
                scenario.rejection_reason = "PARENT_SOURCE_ENDED_WITHOUT_TRIGGER"
            elif self._objective_delivered_before(scenario, replay_end):
                scenario.rejection_reason = "OBJECTIVE_DELIVERED_WITHOUT_TRIGGER"
            else:
                scenario.rejection_reason = "NO_CAUSAL_TRIGGER_BEFORE_REPLAY_END"

    def _explain(
        self, scenario: Scenario, order: OrderPlan, trade: TradeResult
    ) -> list[str]:
        direction = "상승" if scenario.direction == Direction.LONG else "하락"
        return [
            f"{scenario.map_timeframe}의 {scenario.map_structure_event_id}가 {direction} 시나리오의 지배 구조를 먼저 확정했다.",
            f"목적지는 sweep 전에 {scenario.objective_id}의 {scenario.objective_price:.2f}로 동결됐다.",
            f"반대편 source liquidity {scenario.source_pool_id}와 {scenario.context_timeframe} zone이 한 계획으로 연결됐다.",
            f"refinement 계보는 {' -> '.join(scenario.refinement_path)}이며, {scenario.sweep_event_id}가 그 source에서 발생했다.",
            f"{order.trigger_timeframe} {scenario.trigger_event_id}가 correction 종료를 확인하고 그 displacement의 {scenario.entry_zone_id}를 만들었다.",
            f"진입 {order.entry:.2f}, SL {order.stop_loss:.2f}는 entry·sweep·parent source 바깥에 배치됐다.",
            f"고정 TP {order.take_profit:.2f}까지의 결과는 {trade.result}, 손익은 {trade.pnl_r:.2f}R이다.",
        ]

    def summary(self) -> dict[str, Any]:
        filled = [trade for trade in self.trades if trade.entry_time is not None]
        closed = [trade for trade in filled if trade.result in {"TP", "SL"}]
        wins = [trade for trade in closed if trade.result == "TP"]
        losses = [trade for trade in closed if trade.result == "SL"]
        gross_profit = sum(max(0.0, trade.pnl_r) for trade in closed)
        gross_loss = abs(sum(min(0.0, trade.pnl_r) for trade in closed))
        cumulative = 0.0
        peak = 0.0
        max_drawdown = 0.0
        for trade in sorted(closed, key=lambda item: item.exit_time or 0):
            cumulative += trade.pnl_r
            peak = max(peak, cumulative)
            max_drawdown = max(max_drawdown, peak - cumulative)

        rejection_reasons = Counter(
            item.get("reason", "UNKNOWN") for item in self.rejections
        )
        scenario_reasons = Counter(
            scenario.rejection_reason
            for scenario in self.scenarios
            if scenario.rejection_reason
        )
        plan_states = Counter(plan.state for plan in self.plans)
        considered_sweeps = sum(
            1
            for timeframe in self.config.context_timeframes
            for sweep in self.states[timeframe].sweeps
            if (self.config.trade_from is None or sweep.available_at >= self.config.trade_from)
            and (self.config.trade_to is None or sweep.available_at < self.config.trade_to)
        )
        return {
            "schema": "mentor-engine-summary-v2-destination-first",
            "timeframes": {
                timeframe: {
                    "bars": len(state.series),
                    "waves": len(state.structure.waves),
                    "structureEvents": len(state.structure.events),
                    "zones": len(state.zones),
                    "liquidityPools": len(state.liquidity),
                    "sweeps": len(state.sweeps),
                }
                for timeframe, state in self.states.items()
            },
            "funnel": {
                "eligibleLiquiditySweeps": considered_sweeps,
                "destinationPlans": len(self.plans),
                "destinationPlanStates": dict(sorted(plan_states.items())),
                "planAndActivationRejections": len(self.rejections),
                "planAndActivationRejectionReasons": dict(
                    sorted(rejection_reasons.items())
                ),
                "activatedScenarios": len(self.scenarios),
                "scenarioRejectionReasons": dict(sorted(scenario_reasons.items())),
                "candidateOrders": len(self.candidate_orders),
                "orders": len(self.orders),
                "fills": len(filled),
                "closedTrades": len(closed),
                "takeProfits": len(wins),
                "stopLosses": len(losses),
            },
            "economics": {
                "winRate": len(wins) / len(closed) if closed else 0.0,
                "profitFactor": gross_profit / gross_loss if gross_loss > 0 else None,
                "netR": sum(trade.pnl_r for trade in closed),
                "maxDrawdownR": max_drawdown,
                "spreadIncluded": True,
                "commissionIncluded": False,
                "swapIncluded": False,
            },
            "acceptance": {
                "winRate50": bool(closed) and len(wins) / len(closed) >= 0.50,
                "profitFactor13": gross_loss > 0 and gross_profit / gross_loss >= 1.30,
                "netPositive": sum(trade.pnl_r for trade in closed) > 0,
                "maxDrawdownPercent20": None,
                "maxDrawdownPercentReason": (
                    "Python replay is denominated in R and has no account-equity model."
                ),
            },
        }

    def validate_casebook(self, path: str | Path) -> dict[str, Any]:
        return validate_casebook(path)


def _finite(value: float) -> float | None:
    return float(value) if math.isfinite(float(value)) else None
