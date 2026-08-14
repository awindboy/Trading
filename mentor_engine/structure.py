from __future__ import annotations

import math

import numpy as np

from .models import (
    BarSeries,
    Direction,
    Side,
    StructureAnalysis,
    StructureEvent,
    WavePoint,
)


def _colour(open_price: float, close_price: float) -> int:
    if close_price > open_price:
        return 1
    if close_price < open_price:
        return -1
    return 0


def _wave(
    series: BarSeries,
    side: Side,
    search_start: int,
    confirmed_index: int,
) -> WavePoint:
    if side == Side.HIGH:
        relative = int(np.argmax(series.high[search_start : confirmed_index + 1]))
        index = search_start + relative
        level = float(series.high[index])
        wick_bottom = float(max(series.open[index], series.close[index]))
        wick_top = level
    else:
        relative = int(np.argmin(series.low[search_start : confirmed_index + 1]))
        index = search_start + relative
        level = float(series.low[index])
        wick_bottom = level
        wick_top = float(min(series.open[index], series.close[index]))
    return WavePoint(
        object_id=f"{series.timeframe}:wave:{side.value}:{int(series.time[index])}",
        timeframe=series.timeframe,
        side=side,
        index=index,
        confirmed_index=confirmed_index,
        occurred_at=int(series.time[index]),
        available_at=int(series.available_time[confirmed_index]),
        level=level,
        wick_bottom=wick_bottom,
        wick_top=wick_top,
    )


def analyze_structure(series: BarSeries) -> StructureAnalysis:
    size = len(series)
    trend = np.zeros(size, dtype=np.int8)
    protected_high = np.full(size, np.nan)
    protected_low = np.full(size, np.nan)
    range_low = np.full(size, np.nan)
    range_high = np.full(size, np.nan)
    colours = np.array(
        [_colour(float(o), float(c)) for o, c in zip(series.open, series.close)],
        dtype=np.int8,
    )
    waves: list[WavePoint] = []
    events: list[StructureEvent] = []
    highs: list[WavePoint] = []
    lows: list[WavePoint] = []
    broken: set[str] = set()
    current_trend = 0
    current_protected_high: WavePoint | None = None
    current_protected_low: WavePoint | None = None
    external_high: WavePoint | None = None
    external_low: WavePoint | None = None
    current_range_low = math.nan
    current_range_high = math.nan
    last_wave: WavePoint | None = None
    session_start = 0

    def accepts_session_break(direction: Direction, level: float, index: int) -> bool:
        """Require a post-gap re-entry before an old level can break again."""
        if session_start == 0:
            return True
        prior_closes = series.close[session_start:index]
        if not len(prior_closes):
            return False
        if direction == Direction.LONG:
            return bool(np.any(prior_closes <= level))
        return bool(np.any(prior_closes >= level))

    def latest_before(points: list[WavePoint], index: int) -> WavePoint | None:
        for point in reversed(points):
            if point.confirmed_index < index:
                return point
        return None

    def promote(point: WavePoint | None, timestamp: int) -> None:
        if point is None:
            return
        point.rank = "external"
        if point.rank_available_at is None:
            point.rank_available_at = timestamp

    for index in range(size):
        close = float(series.close[index])
        # A market closure/gap is not physical displacement. It cannot itself
        # confirm a body break, and it must not complete a three-candle wave.
        if index and int(series.time[index]) - int(series.time[index - 1]) != series.seconds:
            session_start = index
            close = math.nan
            if series.seconds == 60 and int(series.time[index]) - int(series.time[index - 1]) > series.seconds * 4:
                # Keep H1-M5 maps across a closure, but rebuild M1 execution
                # structure so an opening gap cannot inherit an old trigger.
                current_trend = 0
                current_protected_high = None
                current_protected_low = None
                external_high = None
                external_low = None
                current_range_low = math.nan
                current_range_high = math.nan
                last_wave = None
                highs = []
                lows = []
        event_direction: Direction | None = None
        event_type: str | None = None
        broken_wave: WavePoint | None = None
        protected_wave: WavePoint | None = None

        if current_trend > 0:
            if (
                current_protected_low
                and accepts_session_break(Direction.SHORT, current_protected_low.level, index)
                and close < current_protected_low.level
            ):
                event_direction = Direction.SHORT
                event_type = "CHOCH"
                broken_wave = current_protected_low
                protected_wave = external_high or latest_before(highs, index)
            elif (
                external_high
                and external_high.object_id not in broken
                and accepts_session_break(Direction.LONG, external_high.level, index)
                and close > external_high.level
            ):
                event_direction = Direction.LONG
                event_type = "BOS"
                broken_wave = external_high
                protected_wave = latest_before(lows, index)
        elif current_trend < 0:
            if (
                current_protected_high
                and accepts_session_break(Direction.LONG, current_protected_high.level, index)
                and close > current_protected_high.level
            ):
                event_direction = Direction.LONG
                event_type = "CHOCH"
                broken_wave = current_protected_high
                protected_wave = external_low or latest_before(lows, index)
            elif (
                external_low
                and external_low.object_id not in broken
                and accepts_session_break(Direction.SHORT, external_low.level, index)
                and close < external_low.level
            ):
                event_direction = Direction.SHORT
                event_type = "BOS"
                broken_wave = external_low
                protected_wave = latest_before(highs, index)
        else:
            latest_high = latest_before(highs, index)
            latest_low = latest_before(lows, index)
            if (
                latest_high
                and accepts_session_break(Direction.LONG, latest_high.level, index)
                and close > latest_high.level
            ):
                event_direction = Direction.LONG
                event_type = "INITIAL_BOS"
                broken_wave = latest_high
                protected_wave = latest_low
            elif (
                latest_low
                and accepts_session_break(Direction.SHORT, latest_low.level, index)
                and close < latest_low.level
            ):
                event_direction = Direction.SHORT
                event_type = "INITIAL_BOS"
                broken_wave = latest_low
                protected_wave = latest_high

        if event_direction and broken_wave:
            broken.add(broken_wave.object_id)
            timestamp = int(series.available_time[index])
            # The broken swing has already been delivered. Only the opposite
            # protected point becomes newly actionable liquidity at this close.
            promote(protected_wave, timestamp)
            if event_direction == Direction.LONG:
                current_trend = 1
                current_protected_low = protected_wave if protected_wave and protected_wave.side == Side.LOW else latest_before(lows, index)
                current_protected_high = None
                promote(current_protected_low, timestamp)
                current_range_low = current_protected_low.level if current_protected_low else float(series.low[index])
                current_range_high = max(float(broken_wave.level), float(series.high[index]))
                external_high = None
                external_low = current_protected_low
            else:
                current_trend = -1
                current_protected_high = protected_wave if protected_wave and protected_wave.side == Side.HIGH else latest_before(highs, index)
                current_protected_low = None
                promote(current_protected_high, timestamp)
                current_range_high = current_protected_high.level if current_protected_high else float(series.high[index])
                current_range_low = min(float(broken_wave.level), float(series.low[index]))
                external_low = None
                external_high = current_protected_high
            event_id = f"{series.timeframe}:structure:{event_type}:{int(series.time[index])}"
            events.append(
                StructureEvent(
                    event_id=event_id,
                    timeframe=series.timeframe,
                    index=index,
                    occurred_at=int(series.time[index]),
                    available_at=int(series.available_time[index]),
                    direction=event_direction,
                    event_type=event_type,
                    broken_swing_id=broken_wave.object_id,
                    broken_level=float(broken_wave.level),
                    protected_swing_id=protected_wave.object_id if protected_wave else None,
                    protected_level=float(protected_wave.level) if protected_wave else None,
                    range_low=None if math.isnan(current_range_low) else float(current_range_low),
                    range_high=None if math.isnan(current_range_high) else float(current_range_high),
                )
            )

        if index < 2:
            trend[index] = current_trend
            range_low[index] = current_range_low
            range_high[index] = current_range_high
            continue
        three = colours[index - 2 : index + 1]
        contiguous_three = np.all(np.diff(series.time[index - 2 : index + 1]) == series.seconds)
        next_side: Side | None = None
        if contiguous_three and np.all(three == -1) and (last_wave is None or last_wave.side != Side.HIGH):
            next_side = Side.HIGH
        elif contiguous_three and np.all(three == 1) and (last_wave is None or last_wave.side != Side.LOW):
            next_side = Side.LOW
        if next_side is not None:
            search_start = last_wave.index + 1 if last_wave else 0
            if search_start <= index:
                point = _wave(series, next_side, search_start, index)
                if last_wave is None or point.index > last_wave.index:
                    waves.append(point)
                    last_wave = point
                    timestamp = int(series.available_time[index])
                    if point.side == Side.HIGH:
                        highs.append(point)
                        if current_trend > 0 and (
                            external_high is None
                            or point.level >= external_high.level
                        ) and (
                            math.isnan(current_range_high)
                            or point.level >= current_range_high
                        ):
                            promote(point, timestamp)
                            external_high = point
                            current_range_high = point.level
                    else:
                        lows.append(point)
                        if current_trend < 0 and (
                            external_low is None
                            or point.level <= external_low.level
                        ) and (
                            math.isnan(current_range_low)
                            or point.level <= current_range_low
                        ):
                            promote(point, timestamp)
                            external_low = point
                            current_range_low = point.level

        if current_trend > 0:
            current_range_high = max(current_range_high, float(series.high[index]))
        elif current_trend < 0:
            current_range_low = min(current_range_low, float(series.low[index]))
        trend[index] = current_trend
        if current_protected_high:
            protected_high[index] = current_protected_high.level
        if current_protected_low:
            protected_low[index] = current_protected_low.level
        range_low[index] = current_range_low
        range_high[index] = current_range_high

    return StructureAnalysis(
        timeframe=series.timeframe,
        waves=waves,
        events=events,
        trend=trend,
        protected_high=protected_high,
        protected_low=protected_low,
        range_low=range_low,
        range_high=range_high,
    )
