from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping

from .data import index_at_or_before
from .models import (
    DestinationPlan,
    Direction,
    EngineConfig,
    LiquidityKind,
    LiquidityPool,
    Scenario,
    ScenarioScope,
    Side,
    StructureEvent,
    SweepEvent,
    Zone,
    ZoneKind,
)


EXTERNAL_OBJECTIVE_KINDS = {
    LiquidityKind.EXTERNAL_SWING,
    LiquidityKind.RANGE_EDGE,
    LiquidityKind.TRENDLINE_CLUSTER,
}


class DestinationPlanner:
    """Build destination-first plans before any sweep is evaluated."""

    def __init__(
        self,
        states: Mapping[str, Any],
        config: EngineConfig,
    ) -> None:
        self.states = states
        self.config = config
        self.zones = [
            zone
            for timeframe in config.context_timeframes
            for zone in states[timeframe].zones
        ]
        self.pools = [
            pool
            for timeframe in config.context_timeframes
            for pool in states[timeframe].liquidity
        ]
        self.zone_by_id = {zone.object_id: zone for zone in self.zones}
        self.pool_by_id = {pool.object_id: pool for pool in self.pools}
        self.events_by_id = {
            event.event_id: event
            for state in states.values()
            for event in state.structure.events
        }
        self.wave_by_id = {
            wave.object_id: wave
            for state in states.values()
            for wave in state.structure.waves
        }
        self.families = self._zone_families(self.zones)
        self._families_by_tf_direction: dict[
            tuple[str, Direction], list[tuple[str, list[Zone]]]
        ] = defaultdict(list)
        for family_id, family in self.families.items():
            source_obs = [
                zone
                for zone in family
                if zone.kind == ZoneKind.LAST_OPPOSITE_OB
                and zone.linked_structure_event_id is not None
            ]
            if not source_obs:
                continue
            self._families_by_tf_direction[
                (source_obs[0].timeframe, source_obs[0].direction)
            ].append((family_id, source_obs))
        self.rejections: list[dict[str, Any]] = []

    @staticmethod
    def _zone_families(zones: Iterable[Zone]) -> dict[str, list[Zone]]:
        grouped: dict[str, list[Zone]] = defaultdict(list)
        for zone in zones:
            grouped[zone.family_id].append(zone)
        for family in grouped.values():
            family.sort(
                key=lambda item: (
                    item.kind != ZoneKind.FVG,
                    item.available_at,
                    item.object_id,
                )
            )
        return dict(grouped)

    def _family_bounds(
        self, family: list[Zone], timestamp: int
    ) -> tuple[float, float]:
        bounds = [zone.bounds_at(timestamp) for zone in family]
        return min(item[0] for item in bounds), max(item[1] for item in bounds)

    def _snapshot(self, timeframe: str, timestamp: int) -> dict[str, Any] | None:
        state = self.states[timeframe]
        index = index_at_or_before(state.series, timestamp)
        if index < 0:
            return None
        low = float(state.structure.range_low[index])
        high = float(state.structure.range_high[index])
        if low != low or high != high or high <= low:
            return None
        protected_high = float(state.structure.protected_high[index])
        protected_low = float(state.structure.protected_low[index])
        return {
            "index": index,
            "trend": int(state.structure.trend[index]),
            "rangeLow": low,
            "rangeHigh": high,
            "protectedHigh": None if protected_high != protected_high else protected_high,
            "protectedLow": None if protected_low != protected_low else protected_low,
        }

    def _destination_context(
        self,
        direction: Direction,
        timestamp: int,
        source_bottom: float,
        source_top: float,
        source_timeframe: str,
        source_pool: LiquidityPool,
    ) -> tuple[
        str,
        ScenarioScope,
        dict[str, Any],
        StructureEvent,
        tuple[str, str, float],
    ] | None:
        source_mid = (source_bottom + source_top) / 2.0
        wanted = 1 if direction == Direction.LONG else -1
        ladder = list(self.config.context_timeframes)
        source_index = ladder.index(source_timeframe)
        candidates: list[
            tuple[
                float,
                int,
                int,
                str,
                ScenarioScope,
                dict[str, Any],
                StructureEvent,
                tuple[str, str, float],
            ]
        ] = []
        for map_order, timeframe in enumerate(self.config.map_timeframes):
            if ladder.index(timeframe) > source_index:
                continue
            snapshot = self._snapshot(timeframe, timestamp)
            if not snapshot or snapshot["trend"] == 0:
                continue
            if not (
                snapshot["rangeLow"] <= source_bottom
                and source_top <= snapshot["rangeHigh"]
            ):
                continue
            midpoint = (snapshot["rangeLow"] + snapshot["rangeHigh"]) / 2.0
            correct_half = (
                source_mid <= midpoint
                if direction == Direction.LONG
                else source_mid >= midpoint
            )
            if not correct_half:
                continue
            owner_events = [
                event
                for event in self.states[timeframe].structure.events
                if event.available_at <= timestamp
                and (1 if event.direction == Direction.LONG else -1)
                == snapshot["trend"]
            ]
            if not owner_events:
                continue
            owner = max(owner_events, key=lambda item: (item.available_at, item.event_id))
            scope = (
                ScenarioScope.EXTERNAL_CONTINUATION
                if snapshot["trend"] == wanted
                else ScenarioScope.INTERNAL_ROTATION
            )
            protected_boundary = (
                snapshot["protectedHigh"]
                if direction == Direction.LONG
                else snapshot["protectedLow"]
            )
            objective = self._objective(
                direction,
                scope,
                timeframe,
                source_timeframe,
                timestamp,
                source_pool.level,
                source_pool.object_id,
                protected_boundary,
            )
            if objective is None:
                continue
            objective_price = objective[2]
            if not snapshot["rangeLow"] <= objective_price <= snapshot["rangeHigh"]:
                continue
            objective_object = self.pool_by_id.get(objective[1]) or self.zone_by_id.get(
                objective[1]
            )
            objective_timeframe = (
                objective_object.timeframe if objective_object is not None else timeframe
            )
            candidates.append(
                (
                    abs(objective_price - source_pool.level),
                    0 if timeframe == objective_timeframe else 1,
                    map_order,
                    timeframe,
                    scope,
                    snapshot,
                    owner,
                    objective,
                )
            )
        if not candidates:
            return None
        _, _, _, timeframe, scope, snapshot, owner, objective = min(
            candidates,
            key=lambda item: (item[0], item[1], item[2], item[6].available_at),
        )
        return timeframe, scope, snapshot, owner, objective

    def _objective(
        self,
        direction: Direction,
        scope: ScenarioScope,
        map_timeframe: str,
        source_timeframe: str,
        timestamp: int,
        source_price: float,
        source_pool_id: str,
        protected_boundary: float | None,
    ) -> tuple[str, str, float] | None:
        side = Side.HIGH if direction == Direction.LONG else Side.LOW

        if scope == ScenarioScope.EXTERNAL_CONTINUATION:
            candidates = [
                pool
                for pool in self.states[map_timeframe].liquidity
                if pool.object_id != source_pool_id
                and pool.kind in EXTERNAL_OBJECTIVE_KINDS
                and pool.side == side
                and pool.active_at(timestamp)
                and (
                    pool.level > source_price
                    if direction == Direction.LONG
                    else pool.level < source_price
                )
            ]
            if not candidates:
                return None
            selected = min(candidates, key=lambda item: abs(item.level - source_price))
            return "external_liquidity", selected.object_id, float(selected.level)

        ladder = list(self.config.context_timeframes)
        map_index = ladder.index(map_timeframe)
        source_index = ladder.index(source_timeframe)
        eligible = set(ladder[map_index : source_index + 1])
        liquidity_candidates = [
            pool
            for pool in self.pools
            if pool.object_id != source_pool_id
            and pool.timeframe in eligible
            and pool.side == side
            and pool.active_at(timestamp)
            and (
                pool.level > source_price
                if direction == Direction.LONG
                else pool.level < source_price
            )
            and (
                protected_boundary is None
                or (
                    pool.level < protected_boundary
                    if direction == Direction.LONG
                    else pool.level > protected_boundary
                )
            )
        ]
        delivery = [
            zone
            for zone in self.zones
            if zone.kind == ZoneKind.FVG
            and zone.timeframe in eligible
            and zone.direction != direction
            and zone.active_at(timestamp)
            and (
                zone.bottom > source_price
                if direction == Direction.LONG
                else zone.top < source_price
            )
            and (
                protected_boundary is None
                or (
                    zone.bottom < protected_boundary
                    if direction == Direction.LONG
                    else zone.top > protected_boundary
                )
            )
        ]
        options: list[tuple[float, str, str, float]] = [
            (
                abs(pool.level - source_price),
                "internal_liquidity",
                pool.object_id,
                float(pool.level),
            )
            for pool in liquidity_candidates
        ]
        options.extend(
            (
                abs(
                    (zone.bottom if direction == Direction.LONG else zone.top)
                    - source_price
                ),
                "delivery_zone",
                zone.object_id,
                float(zone.bottom if direction == Direction.LONG else zone.top),
            )
            for zone in delivery
        )
        if not options:
            return None
        _, kind, object_id, price = min(options, key=lambda item: item[0])
        return kind, object_id, price

    def _source_inside_opposing_zone(
        self,
        direction: Direction,
        timestamp: int,
        source_bottom: float,
        source_top: float,
        source_family_id: str,
    ) -> bool:
        return any(
            zone.family_id != source_family_id
            and zone.direction != direction
            and zone.linked_structure_event_id is not None
            and zone.active_at(timestamp)
            and zone.top >= source_bottom
            and zone.bottom <= source_top
            for zone in self.zones
        )

    def _refinement_lineage(
        self,
        family_id: str,
        timestamp: int,
        bottom: float,
        top: float,
        direction: Direction,
    ) -> tuple[list[str], list[str]] | None:
        family = [
            zone
            for zone in self.families[family_id]
            if zone.kind == ZoneKind.LAST_OPPOSITE_OB
            and zone.linked_structure_event_id is not None
        ]
        if not family:
            return None
        child_tf = family[0].timeframe
        ladder = list(self.config.context_timeframes)
        child_index = ladder.index(child_tf)
        parents: list[tuple[str, list[Zone], float, float]] = []
        for timeframe in ladder[:child_index]:
            matches: list[tuple[str, list[Zone], float, float]] = []
            for candidate_id, candidate in self._families_by_tf_direction.get(
                (timeframe, direction), []
            ):
                if not any(zone.linked_structure_event_id for zone in candidate):
                    continue
                if not all(zone.active_at(timestamp) for zone in candidate):
                    continue
                candidate_bottom, candidate_top = self._family_bounds(candidate, timestamp)
                if candidate_bottom <= bottom and top <= candidate_top:
                    parent_events = [
                        self.events_by_id[zone.linked_structure_event_id]
                        for zone in candidate
                        if zone.linked_structure_event_id in self.events_by_id
                    ]
                    child_events = [
                        self.events_by_id[zone.linked_structure_event_id]
                        for zone in family
                        if zone.linked_structure_event_id in self.events_by_id
                    ]
                    if not parent_events or not child_events:
                        continue
                    parent_start = min(zone.occurred_at for zone in candidate)
                    parent_end = max(event.available_at for event in parent_events)
                    child_start = min(zone.occurred_at for zone in family)
                    child_end = max(event.available_at for event in child_events)
                    if not (
                        parent_start <= child_start
                        and child_end <= parent_end
                    ):
                        continue
                    matches.append(
                        (candidate_id, candidate, candidate_bottom, candidate_top)
                    )
            if len(matches) > 1:
                # Multiple unrelated parent families cannot be resolved by
                # selecting the smallest rectangle.
                return None
            if matches:
                parents.append(matches[0])

        # The baseline entry is a genuine HTF-to-LTF OB refinement. A parentless
        # OB, even if otherwise valid, is not a precision-entry source.
        if not parents:
            return None
        parent_zone_ids = [
            zone.object_id
            for _, parent, _, _ in parents
            for zone in parent
        ]
        refinement_path = [item[0] for item in parents] + [family_id]
        return parent_zone_ids, refinement_path

    def _replay_source_pools(self) -> list[LiquidityPool]:
        # This only narrows enumeration. Plan contents still use information
        # available before each sweep and are validated by planned_at.
        pool_ids = {
            sweep.pool_id
            for timeframe in self.config.context_timeframes
            for sweep in self.states[timeframe].sweeps
            if (self.config.trade_from is None or sweep.available_at >= self.config.trade_from)
            and (self.config.trade_to is None or sweep.available_at < self.config.trade_to)
        }
        return [self.pool_by_id[item] for item in sorted(pool_ids)]

    def _nearest_source_families(
        self,
        source_pool: LiquidityPool,
        direction: Direction,
    ) -> list[tuple[str, list[Zone], int, float, float]]:
        selected: list[tuple[str, list[Zone], int, float, float]] = []
        for timeframe in self.config.context_timeframes:
            candidates: list[tuple[float, str, list[Zone], int, float, float]] = []
            for family_id, family in self._families_by_tf_direction.get(
                (timeframe, direction), []
            ):
                structurally_linked = any(
                    zone.linked_structure_event_id for zone in family
                )
                defended_by_pool = self._family_defended_by_pool(
                    family, source_pool
                )
                if not structurally_linked and not defended_by_pool:
                    continue
                planned_at = max(
                    source_pool.available_at,
                    max(zone.available_at for zone in family),
                )
                if self.config.trade_to is not None and planned_at >= self.config.trade_to:
                    continue
                if not source_pool.active_at(planned_at):
                    continue
                if not all(zone.active_at(planned_at) for zone in family):
                    continue
                bottom, top = self._family_bounds(family, planned_at)
                if direction == Direction.LONG:
                    if source_pool.level < bottom:
                        continue
                    distance = max(0.0, source_pool.level - top)
                else:
                    if source_pool.level > top:
                        continue
                    distance = max(0.0, bottom - source_pool.level)
                candidates.append(
                    (distance, family_id, family, planned_at, bottom, top)
                )
            if not candidates:
                continue
            nearest = min(item[0] for item in candidates)
            selected.extend(
                (family_id, family, planned_at, bottom, top)
                for distance, family_id, family, planned_at, bottom, top in candidates
                if abs(distance - nearest) <= self.config.point / 10.0
            )
        return selected

    def _family_defended_by_pool(
        self,
        family: list[Zone],
        source_pool: LiquidityPool,
    ) -> bool:
        family_available = max(zone.available_at for zone in family)
        waves = [
            self.wave_by_id[wave_id]
            for wave_id in source_pool.source_wave_ids
            if wave_id in self.wave_by_id
        ]
        for wave in waves:
            if family_available > wave.available_at:
                continue
            if not all(zone.active_at(wave.available_at) for zone in family):
                continue
            bottom, top = self._family_bounds(family, wave.available_at)
            if wave.wick_top >= bottom and wave.wick_bottom <= top:
                return True
        return False

    def build(self) -> list[DestinationPlan]:
        plans: list[DestinationPlan] = []
        seen: set[tuple[object, ...]] = set()
        for source_pool in self._replay_source_pools():
            direction = (
                Direction.LONG if source_pool.side == Side.LOW else Direction.SHORT
            )
            families = self._nearest_source_families(source_pool, direction)
            if not families:
                self.rejections.append(
                    {
                        "recordType": "plan_rejection",
                        "sourcePoolId": source_pool.object_id,
                        "availableAt": source_pool.available_at,
                        "reason": "NO_CAUSAL_SOURCE_FAMILY",
                    }
                )
            for family_id, family, planned_at, source_bottom, source_top in families:
                source_timeframe = family[0].timeframe
                if self._source_inside_opposing_zone(
                    direction,
                    planned_at,
                    source_bottom,
                    source_top,
                    family_id,
                ):
                    self.rejections.append(
                        {
                            "recordType": "plan_rejection",
                            "familyId": family_id,
                            "sourcePoolId": source_pool.object_id,
                            "availableAt": planned_at,
                            "reason": "SOURCE_INSIDE_OPPOSING_DELIVERY",
                        }
                    )
                    continue
                lineage = self._refinement_lineage(
                    family_id,
                    planned_at,
                    source_bottom,
                    source_top,
                    direction,
                )
                if lineage is None:
                    self.rejections.append(
                        {
                            "recordType": "plan_rejection",
                            "familyId": family_id,
                            "sourcePoolId": source_pool.object_id,
                            "availableAt": planned_at,
                            "reason": "AMBIGUOUS_PARENT_REFINEMENT",
                        }
                    )
                    continue
                destination_context = self._destination_context(
                    direction,
                    planned_at,
                    source_bottom,
                    source_top,
                    source_timeframe,
                    source_pool,
                )
                if destination_context is None:
                    self.rejections.append(
                        {
                            "recordType": "plan_rejection",
                            "familyId": family_id,
                            "sourcePoolId": source_pool.object_id,
                            "availableAt": planned_at,
                            "reason": "NO_PRE_SWEEP_DESTINATION_CONTEXT",
                        }
                    )
                    continue
                (
                    map_timeframe,
                    scope,
                    snapshot,
                    owner,
                    objective,
                ) = destination_context
                parent_zone_ids, refinement_path = lineage
                key = (
                    direction,
                    owner.event_id,
                    source_pool.object_id,
                    tuple(refinement_path),
                    objective[1],
                )
                if key in seen:
                    continue
                seen.add(key)
                plan_id = (
                    f"plan:{owner.event_id}:{source_pool.object_id}:"
                    f"{family_id}:{objective[1]}"
                )
                map_protected = (
                    snapshot["protectedLow"]
                    if direction == Direction.LONG
                    else snapshot["protectedHigh"]
                )
                plans.append(
                    DestinationPlan(
                        plan_id=plan_id,
                        direction=direction,
                        scope=scope,
                        planned_at=planned_at,
                        map_timeframe=map_timeframe,
                        map_structure_event_id=owner.event_id,
                        map_trend=snapshot["trend"],
                        map_protected_level=map_protected,
                        dealing_range_low=snapshot["rangeLow"],
                        dealing_range_high=snapshot["rangeHigh"],
                        source_timeframe=source_timeframe,
                        source_pool_id=source_pool.object_id,
                        source_zone_ids=[zone.object_id for zone in family],
                        parent_zone_ids=parent_zone_ids,
                        refinement_path=refinement_path,
                        source_bottom=source_bottom,
                        source_top=source_top,
                        objective_kind=objective[0],
                        objective_id=objective[1],
                        objective_price=objective[2],
                    )
                )
        return sorted(plans, key=lambda item: (item.planned_at, item.plan_id))

    def _map_still_valid(self, plan: DestinationPlan, timestamp: int) -> bool:
        snapshot = self._snapshot(plan.map_timeframe, timestamp)
        if not snapshot:
            return False
        wanted = 1 if plan.direction == Direction.LONG else -1
        if plan.scope == ScenarioScope.EXTERNAL_CONTINUATION:
            return snapshot["trend"] == wanted
        return snapshot["trend"] == -wanted

    def _plan_live_for_sweep(
        self, plan: DestinationPlan, sweep: SweepEvent
    ) -> tuple[bool, str | None]:
        if plan.planned_at >= sweep.available_at:
            return False, "PLAN_NOT_KNOWN_BEFORE_SWEEP"
        objective_pool = self.pool_by_id.get(plan.objective_id)
        if objective_pool is not None and not objective_pool.active_at(sweep.available_at):
            return False, "OBJECTIVE_ALREADY_DELIVERED"
        if not self._map_still_valid(plan, sweep.available_at - 1):
            return False, "MAP_SCOPE_CHANGED_BEFORE_SWEEP"
        zones = [self.zone_by_id[item] for item in plan.source_zone_ids]
        if not all(zone.active_at(sweep.available_at - 1) for zone in zones):
            return False, "SOURCE_ZONE_NOT_FRESH_BEFORE_SWEEP"
        state = self.states[sweep.timeframe]
        bar_low = float(state.series.low[sweep.index])
        bar_high = float(state.series.high[sweep.index])
        if bar_high < plan.source_bottom or bar_low > plan.source_top:
            return False, "SWEEP_DID_NOT_TOUCH_PLANNED_SOURCE"
        return True, None

    @staticmethod
    def _nested(plans: list[DestinationPlan]) -> bool:
        ordered = sorted(plans, key=lambda item: item.source_top - item.source_bottom)
        for child, parent in zip(ordered, ordered[1:]):
            if not (
                parent.source_bottom <= child.source_bottom
                and child.source_top <= parent.source_top
            ):
                return False
        return True

    def activate(
        self,
        plans: list[DestinationPlan],
        sweeps: Iterable[SweepEvent],
    ) -> tuple[list[Scenario], list[dict[str, Any]]]:
        by_pool: dict[str, list[DestinationPlan]] = defaultdict(list)
        for plan in plans:
            by_pool[plan.source_pool_id].append(plan)

        scenarios: list[Scenario] = []
        rejections = list(self.rejections)
        physical_sweeps: dict[tuple[object, ...], list[SweepEvent]] = defaultdict(list)
        for sweep in sweeps:
            signature = (
                sweep.timeframe,
                sweep.index,
                sweep.side,
                round(sweep.extreme / self.config.point),
            )
            physical_sweeps[signature].append(sweep)

        ordered_groups = sorted(
            physical_sweeps.values(),
            key=lambda group: (group[0].available_at, group[0].event_id),
        )
        for sweep_group in ordered_groups:
            sweep = sweep_group[0]
            if self.config.trade_from is not None and sweep.available_at < self.config.trade_from:
                continue
            if self.config.trade_to is not None and sweep.available_at >= self.config.trade_to:
                continue
            candidate_pairs: list[tuple[DestinationPlan, SweepEvent]] = []
            for physical_sweep in sweep_group:
                for plan in by_pool.get(physical_sweep.pool_id, []):
                    valid, reason = self._plan_live_for_sweep(plan, physical_sweep)
                    if valid:
                        candidate_pairs.append((plan, physical_sweep))
                    elif plan.planned_at < physical_sweep.available_at:
                        rejections.append(
                            {
                                "recordType": "activation_rejection",
                                "planId": plan.plan_id,
                                "sweepEventId": physical_sweep.event_id,
                                "availableAt": physical_sweep.available_at,
                                "reason": reason,
                            }
                        )
            candidates = [item[0] for item in candidate_pairs]
            if not candidates:
                continue
            ownership = {
                (
                    item.direction,
                    item.map_structure_event_id,
                    item.objective_id,
                )
                for item in candidates
            }
            if len(ownership) != 1 or not self._nested(candidates):
                rejections.append(
                    {
                        "recordType": "activation_rejection",
                        "sweepEventId": sweep.event_id,
                        "availableAt": sweep.available_at,
                        "candidatePlanIds": [item.plan_id for item in candidates],
                        "reason": "COMPETING_DESTINATION_PLANS",
                    }
                )
                for plan in candidates:
                    plan.state = "REJECTED"
                    plan.rejection_reason = "COMPETING_DESTINATION_PLANS"
                continue
            pool_priority = {
                LiquidityKind.REACTION_TRAP: 0,
                LiquidityKind.RANGE_EDGE: 1,
                LiquidityKind.TRENDLINE_CLUSTER: 1,
                LiquidityKind.EXTERNAL_SWING: 2,
            }
            selected, selected_sweep = min(
                candidate_pairs,
                key=lambda item: (
                    item[0].source_top - item[0].source_bottom,
                    -len(item[0].refinement_path),
                    pool_priority[item[1].pool_kind],
                    item[0].plan_id,
                ),
            )
            selected.state = "ACTIVATED"
            selected.sweep_event_id = selected_sweep.event_id
            selected.activated_at = selected_sweep.available_at
            for superseded in candidates:
                if superseded is selected:
                    continue
                superseded.state = "SUPERSEDED_BY_CAUSAL_CHILD"
                superseded.rejection_reason = "CAUSAL_CHILD_REFINEMENT_SELECTED"
            scenarios.append(
                Scenario(
                    scenario_id=f"scenario:{selected.plan_id}:{selected_sweep.event_id}",
                    plan_id=selected.plan_id,
                    direction=selected.direction,
                    scope=selected.scope,
                    map_timeframe=selected.map_timeframe,
                    context_timeframe=selected.source_timeframe,
                    trigger_timeframe=None,
                    source_pool_id=selected.source_pool_id,
                    source_zone_ids=list(selected.source_zone_ids),
                    sweep_event_id=selected_sweep.event_id,
                    created_at=selected_sweep.available_at,
                    source_price=selected_sweep.extreme,
                    objective_kind=selected.objective_kind,
                    objective_id=selected.objective_id,
                    objective_price=selected.objective_price,
                    map_trend=selected.map_trend,
                    dealing_range_low=selected.dealing_range_low,
                    dealing_range_high=selected.dealing_range_high,
                    planned_at=selected.planned_at,
                    map_structure_event_id=selected.map_structure_event_id,
                    parent_zone_ids=list(selected.parent_zone_ids),
                    refinement_path=list(selected.refinement_path),
                    absorbed_sweep_event_ids=[selected_sweep.event_id],
                )
            )
        return scenarios, rejections
