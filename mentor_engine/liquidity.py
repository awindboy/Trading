from __future__ import annotations

from collections import defaultdict

from .models import (
    BarSeries,
    Direction,
    LiquidityKind,
    LiquidityPool,
    Side,
    StructureAnalysis,
    SweepEvent,
    WavePoint,
    Zone,
)


def _overlap(first: WavePoint, second: WavePoint) -> tuple[float, float] | None:
    bottom = max(first.wick_bottom, second.wick_bottom)
    top = min(first.wick_top, second.wick_top)
    if top < bottom:
        return None
    return float(bottom), float(top)


def _pool(
    series: BarSeries,
    kind: LiquidityKind,
    side: Side,
    source: list[WavePoint],
    bottom: float,
    top: float,
    available_at: int | None = None,
) -> LiquidityPool:
    created_index = max(item.confirmed_index for item in source)
    stamp = max(item.available_at for item in source) if available_at is None else available_at
    return LiquidityPool(
        object_id=(
            f"{series.timeframe}:liquidity:{kind.value}:{side.value}:"
            f"{int(stamp)}:{':'.join(item.object_id for item in source)}"
        ),
        timeframe=series.timeframe,
        kind=kind,
        side=side,
        created_index=created_index,
        occurred_at=int(series.time[max(item.index for item in source)]),
        available_at=int(stamp),
        bottom=float(min(bottom, top)),
        top=float(max(bottom, top)),
        source_wave_ids=[item.object_id for item in source],
    )


def build_liquidity(
    series: BarSeries,
    structure: StructureAnalysis,
    zones: list[Zone],
) -> tuple[list[LiquidityPool], list[SweepEvent]]:
    pools: list[LiquidityPool] = []
    seen: set[tuple[object, ...]] = set()

    def add(pool: LiquidityPool) -> None:
        key = (
            pool.kind,
            pool.side,
            tuple(pool.source_wave_ids),
            round(pool.bottom, 10),
            round(pool.top, 10),
        )
        if key not in seen:
            seen.add(key)
            pools.append(pool)

    for wave in structure.waves:
        if wave.rank == "external" and wave.rank_available_at is not None:
            add(
                _pool(
                    series,
                    LiquidityKind.EXTERNAL_SWING,
                    wave.side,
                    [wave],
                    wave.wick_bottom,
                    wave.wick_top,
                    wave.rank_available_at,
                )
            )
        compatible_direction = (
            Direction.SHORT if wave.side == Side.HIGH else Direction.LONG
        )
        wave_low = float(series.low[wave.index])
        wave_high = float(series.high[wave.index])
        reaction_zones = [
            zone
            for zone in zones
            if zone.direction == compatible_direction
            and zone.available_at <= int(series.available_time[wave.index])
            and zone.active_at(int(series.available_time[wave.index]))
            and wave_high >= zone.bottom
            and wave_low <= zone.top
        ]
        if reaction_zones:
            add(
                _pool(
                    series,
                    LiquidityKind.REACTION_TRAP,
                    wave.side,
                    [wave],
                    wave.wick_bottom,
                    wave.wick_top,
                )
            )

    # A range needs two defended highs and two defended lows in an alternating
    # four-wave sequence. Pairing distant same-side pivots produces fictional
    # ranges and is deliberately not allowed.
    for offset in range(3, len(structure.waves)):
        combined = structure.waves[offset - 3 : offset + 1]
        if any(
            first.side == second.side for first, second in zip(combined, combined[1:])
        ):
            continue
        highs = [item for item in combined if item.side == Side.HIGH]
        lows = [item for item in combined if item.side == Side.LOW]
        if len(highs) != 2 or len(lows) != 2:
            continue
        high_overlap = _overlap(highs[0], highs[1])
        low_overlap = _overlap(lows[0], lows[1])
        if high_overlap is None or low_overlap is None:
            continue
        # A body close outside either defended edge before the fourth wave is
        # confirmed means the sequence was not a range.
        start = combined[0].index
        end = combined[-1].confirmed_index + 1
        if any(series.close[start:end] > high_overlap[1]) or any(
            series.close[start:end] < low_overlap[0]
        ):
            continue
        range_available_at = max(item.available_at for item in combined)
        add(
            _pool(
                series,
                LiquidityKind.RANGE_EDGE,
                Side.HIGH,
                highs,
                high_overlap[0],
                high_overlap[1],
                range_available_at,
            )
        )
        add(
            _pool(
                series,
                LiquidityKind.RANGE_EDGE,
                Side.LOW,
                lows,
                low_overlap[0],
                low_overlap[1],
                range_available_at,
            )
        )

    for side in (Side.HIGH, Side.LOW):
        same_side = [wave for wave in structure.waves if wave.side == side]
        for index in range(2, len(same_side)):
            first, second, third = same_side[index - 2 : index + 1]
            if second.index == first.index:
                continue
            slope = (second.level - first.level) / (second.index - first.index)
            projected = first.level + slope * (third.index - first.index)
            if third.wick_bottom <= projected <= third.wick_top:
                add(
                    _pool(
                        series,
                        LiquidityKind.TRENDLINE_CLUSTER,
                        side,
                        [first, second, third],
                        third.wick_bottom,
                        third.wick_top,
                    )
                )

    sweeps = _detect_sweeps(series, pools)
    return sorted(pools, key=lambda item: (item.available_at, item.object_id)), sweeps


def _detect_sweeps(
    series: BarSeries, pools: list[LiquidityPool]
) -> list[SweepEvent]:
    by_available_index: dict[int, list[LiquidityPool]] = defaultdict(list)
    for pool in pools:
        index = int(series.available_time.searchsorted(pool.available_at, side="left"))
        by_available_index[index].append(pool)
    active: list[LiquidityPool] = []
    sweeps: list[SweepEvent] = []
    for index in range(len(series)):
        high = float(series.high[index])
        low = float(series.low[index])
        close = float(series.close[index])
        remaining: list[LiquidityPool] = []
        for pool in active:
            if pool.side == Side.HIGH:
                if close > pool.top:
                    pool.consumed_index = index
                    pool.consumed_at = int(series.available_time[index])
                elif high > pool.top and close <= pool.top:
                    pool.consumed_index = index
                    pool.consumed_at = int(series.available_time[index])
                    sweeps.append(
                        SweepEvent(
                            event_id=f"{pool.object_id}:sweep:{int(series.time[index])}",
                            timeframe=series.timeframe,
                            index=index,
                            occurred_at=int(series.time[index]),
                            available_at=int(series.available_time[index]),
                            pool_id=pool.object_id,
                            pool_kind=pool.kind,
                            side=pool.side,
                            extreme=high,
                            close=close,
                        )
                    )
                else:
                    remaining.append(pool)
            else:
                if close < pool.bottom:
                    pool.consumed_index = index
                    pool.consumed_at = int(series.available_time[index])
                elif low < pool.bottom and close >= pool.bottom:
                    pool.consumed_index = index
                    pool.consumed_at = int(series.available_time[index])
                    sweeps.append(
                        SweepEvent(
                            event_id=f"{pool.object_id}:sweep:{int(series.time[index])}",
                            timeframe=series.timeframe,
                            index=index,
                            occurred_at=int(series.time[index]),
                            available_at=int(series.available_time[index]),
                            pool_id=pool.object_id,
                            pool_kind=pool.kind,
                            side=pool.side,
                            extreme=low,
                            close=close,
                        )
                    )
                else:
                    remaining.append(pool)
        active = remaining
        active.extend(by_available_index.get(index, []))
    return sweeps
