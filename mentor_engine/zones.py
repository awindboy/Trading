from __future__ import annotations

from bisect import bisect_left
from collections import defaultdict

import numpy as np

from .models import (
    BarSeries,
    Direction,
    StructureAnalysis,
    StructureEvent,
    Zone,
    ZoneKind,
)


def _last_opposite_index(
    series: BarSeries,
    direction: Direction,
    end_index: int,
    lower_bound: int,
) -> int | None:
    for index in range(end_index, lower_bound - 1, -1):
        # Do not attach an order block from a closed prior session to a
        # structure event that first appeared after the session gap.
        if (
            index < end_index
            and int(series.time[index + 1]) - int(series.time[index]) != series.seconds
        ):
            break
        bullish = series.close[index] > series.open[index]
        bearish = series.close[index] < series.open[index]
        if direction == Direction.LONG and bearish:
            return index
        if direction == Direction.SHORT and bullish:
            return index
    return None


def _zone(
    series: BarSeries,
    family_id: str,
    kind: ZoneKind,
    direction: Direction,
    origin_index: int,
    confirmed_index: int,
    bottom: float,
    top: float,
    linked_event: StructureEvent | None,
) -> Zone:
    event_suffix = linked_event.event_id if linked_event else "none"
    return Zone(
        object_id=(
            f"{series.timeframe}:zone:{kind.value}:{direction.value}:"
            f"{int(series.time[origin_index])}:{event_suffix}"
        ),
        family_id=family_id,
        timeframe=series.timeframe,
        kind=kind,
        direction=direction,
        origin_index=origin_index,
        confirmed_index=confirmed_index,
        occurred_at=int(series.time[origin_index]),
        available_at=int(series.available_time[confirmed_index]),
        bottom=float(min(bottom, top)),
        top=float(max(bottom, top)),
        linked_structure_event_id=linked_event.event_id if linked_event else None,
    )


def detect_zones(series: BarSeries, structure: StructureAnalysis) -> list[Zone]:
    waves = sorted(structure.waves, key=lambda item: item.index)
    wave_indexes = [wave.index for wave in waves]
    zones: list[Zone] = []
    linked_event_ids: set[str] = set()
    seen: set[tuple[object, ...]] = set()

    def add(candidate: Zone) -> None:
        key = (
            candidate.kind,
            candidate.direction,
            candidate.origin_index,
            candidate.confirmed_index,
            round(candidate.bottom, 10),
            round(candidate.top, 10),
            candidate.linked_structure_event_id,
        )
        if key not in seen and candidate.top > candidate.bottom:
            seen.add(key)
            zones.append(candidate)

    for index in range(2, len(series)):
        # A price gap across a market closure cannot be a three-candle FVG or
        # create a causal OB family with bars from the prior session.
        if not np.all(np.diff(series.time[index - 2 : index + 1]) == series.seconds):
            continue
        direction: Direction | None = None
        fvg_bottom = 0.0
        fvg_top = 0.0
        if series.low[index] > series.high[index - 2]:
            direction = Direction.LONG
            fvg_bottom = float(series.high[index - 2])
            fvg_top = float(series.low[index])
        elif series.high[index] < series.low[index - 2]:
            direction = Direction.SHORT
            fvg_bottom = float(series.high[index])
            fvg_top = float(series.low[index - 2])
        if direction is None:
            continue
        wave_position = bisect_left(wave_indexes, index)
        leg_start = wave_indexes[wave_position - 1] if wave_position else 0
        leg_end = (
            waves[wave_position].confirmed_index
            if wave_position < len(waves)
            else len(series) - 1
        )
        # A displacement FVG can form before price closes through structure.
        # Link the first same-direction break in the same wave leg instead of
        # requiring the BOS/CHoCH candle to be one of the FVG's three bars.
        candidates = [
            event
            for event in structure.events
            if event.direction == direction
            and leg_start <= event.index <= leg_end
            and event.index >= index - 2
        ]
        linked = min(candidates, key=lambda item: item.index) if candidates else None
        family_id = f"{series.timeframe}:family:{direction.value}:{int(series.time[index - 2])}"
        add(
            _zone(
                series,
                family_id,
                ZoneKind.FVG,
                direction,
                index - 2,
                index,
                fvg_bottom,
                fvg_top,
                linked,
            )
        )
        add(
            _zone(
                series,
                family_id,
                ZoneKind.FVG_ORIGIN_OB,
                direction,
                index - 2,
                index,
                float(series.low[index - 2]),
                float(series.high[index - 2]),
                linked,
            )
        )
        position = bisect_left(wave_indexes, index - 1)
        lower_bound = wave_indexes[position - 1] if position else 0
        opposite_index = _last_opposite_index(series, direction, index - 1, lower_bound)
        if opposite_index is not None:
            add(
                _zone(
                    series,
                    family_id,
                    ZoneKind.LAST_OPPOSITE_OB,
                    direction,
                    opposite_index,
                    index,
                    float(series.low[opposite_index]),
                    float(series.high[opposite_index]),
                    linked,
                )
            )
        if linked:
            linked_event_ids.add(linked.event_id)

    for event in structure.events:
        if event.event_id in linked_event_ids:
            continue
        position = bisect_left(wave_indexes, event.index)
        lower_bound = wave_indexes[position - 1] if position else 0
        opposite_index = _last_opposite_index(
            series, event.direction, event.index - 1, lower_bound
        )
        if opposite_index is None:
            continue
        family_id = f"{series.timeframe}:family:structure:{event.event_id}"
        add(
            _zone(
                series,
                family_id,
                ZoneKind.LAST_OPPOSITE_OB,
                event.direction,
                opposite_index,
                event.index,
                float(series.low[opposite_index]),
                float(series.high[opposite_index]),
                event,
            )
        )

    _advance_zone_lifecycles(series, zones)
    return sorted(zones, key=lambda item: (item.available_at, item.kind.value, item.object_id))


def _advance_zone_lifecycles(series: BarSeries, zones: list[Zone]) -> None:
    by_confirmation: dict[int, list[Zone]] = defaultdict(list)
    for zone in zones:
        by_confirmation[zone.confirmed_index].append(zone)
    active: list[Zone] = []
    remaining_bounds = {
        zone.object_id: (zone.bottom, zone.top) for zone in zones
    }
    for index in range(len(series)):
        remaining: list[Zone] = []
        low = float(series.low[index])
        high = float(series.high[index])
        for zone in active:
            remaining_bottom, remaining_top = remaining_bounds[zone.object_id]
            intersects = high >= remaining_bottom and low <= remaining_top
            if not intersects:
                remaining.append(zone)
                continue
            if zone.first_touch_index is None:
                zone.first_touch_index = index
            fully_filled = (
                low <= zone.bottom
                if zone.direction == Direction.LONG
                else high >= zone.top
            )
            if fully_filled:
                zone.consumed_index = index
                zone.consumed_at = int(series.available_time[index])
            else:
                if zone.kind == ZoneKind.FVG:
                    if zone.direction == Direction.LONG and low < remaining_top:
                        remaining_top = max(zone.bottom, low)
                    elif zone.direction == Direction.SHORT and high > remaining_bottom:
                        remaining_bottom = min(zone.top, high)
                    new_bounds = (float(remaining_bottom), float(remaining_top))
                    if new_bounds != remaining_bounds[zone.object_id]:
                        remaining_bounds[zone.object_id] = new_bounds
                        zone.partial_fills.append(
                            (
                                int(series.available_time[index]),
                                new_bounds[0],
                                new_bounds[1],
                            )
                        )
                remaining.append(zone)
        active = remaining
        active.extend(by_confirmation.get(index, []))
