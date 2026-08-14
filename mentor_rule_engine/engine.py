from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from typing import Iterable

import numpy as np

from mentor_engine.data import index_at_or_before
from mentor_engine.models import BarSeries
from mentor_engine.structure import analyze_structure


@dataclass(frozen=True)
class EngineConfig:
    source_timeframes: tuple[str, ...] = ("M15", "M5")
    trigger_timeframe: str = "M1"
    source_confirmation_bars: int = 8
    source_max_age_minutes: int = 48 * 60
    sweep_pivot_lookback: int = 90
    sweep_recovery_bars: int = 2
    reaction_window_minutes: int = 25
    source_distance_width_factor: float = 0.75
    source_distance_floor: float = 0.50
    permanent_invalidation_closes: int = 2
    point: float = 0.01


@dataclass(frozen=True)
class Pivot:
    pivot_id: str
    side: str
    index: int
    confirmed_index: int
    occurred_at: int
    available_at: int
    level: float


@dataclass(frozen=True)
class OrderBlock:
    source_id: str
    timeframe: str
    direction: str
    origin_index: int
    confirm_index: int
    occurred_at: int
    available_at: int
    bottom: float
    top: float
    invalidated_at: int | None

    @property
    def width(self) -> float:
        return self.top - self.bottom

    def active_at(self, timestamp: int) -> bool:
        return self.available_at <= timestamp and (
            self.invalidated_at is None or timestamp < self.invalidated_at
        )


@dataclass(frozen=True)
class SweepEpisode:
    sweep_id: str
    direction: str
    pivot_id: str
    index: int
    recovery_index: int
    occurred_at: int
    recovered_at: int
    liquidity_level: float
    extreme: float


@dataclass(frozen=True)
class Fvg:
    fvg_id: str
    direction: str
    origin_index: int
    confirmed_index: int
    occurred_at: int
    available_at: int
    bottom: float
    top: float

    @property
    def proximal(self) -> float:
        return self.bottom if self.direction == "short" else self.top


@dataclass(frozen=True)
class LiquidityLevel:
    liquidity_id: str
    timeframe: str
    side: str
    occurred_at: int
    available_at: int
    level: float
    rank: str
    kind: str
    consumed_at: int | None

    def active_at(self, timestamp: int) -> bool:
        return self.available_at <= timestamp and (
            self.consumed_at is None or timestamp < self.consumed_at
        )


@dataclass
class RuleCandidate:
    candidate_id: str
    direction: str
    created_at: int
    source_id: str
    source_timeframe: str
    source_bottom: float
    source_top: float
    parent_source_id: str
    refinement_path: list[str]
    sweep_id: str
    sweep_at: int
    sweep_extreme: float
    shift_at: int
    shift_reference: float
    shift_reference_kind: str
    fvg_id: str
    fvg_bottom: float
    fvg_top: float
    entry: float
    structural_invalidation: float
    stop: float
    map_direction: str
    scope: str
    objective: float | None
    objective_id: str | None
    objective_kind: str | None
    objective_frozen_at: int
    objective_alternatives: list[dict[str, object]] = field(default_factory=list)
    chain_key: str = ""
    retest_at: int | None = None
    owner_id: str | None = None
    entry_model: str = "HTF_OB_REACTION"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class RuleEngineResult:
    candidates: list[RuleCandidate]
    authorized_candidates: list[RuleCandidate]
    sources: list[OrderBlock]
    sweeps: list[SweepEpisode]
    fvgs: list[Fvg]
    liquidity: list[LiquidityLevel]
    audit: dict[str, object]


def _contiguous(series: BarSeries, left: int, right: int) -> bool:
    if left < 0 or right >= len(series):
        return False
    if right <= left:
        return True
    return bool(np.all(np.diff(series.time[left : right + 1]) == series.seconds))


def _directional_close(
    direction: str,
    close: float,
    level: float,
) -> bool:
    return close < level if direction == "short" else close > level


def _opposite_candle(series: BarSeries, index: int, direction: str) -> bool:
    if direction == "short":
        return bool(series.close[index] > series.open[index])
    return bool(series.close[index] < series.open[index])


class MentorRuleEngine:
    """Discover causal mentor-style setup candidates from as-of OHLC only."""

    def __init__(
        self,
        frames: dict[str, BarSeries],
        config: EngineConfig | None = None,
    ) -> None:
        self.frames = frames
        self.config = config or EngineConfig()
        self.m1 = frames[self.config.trigger_timeframe]
        self._m1_index_by_time = {
            int(timestamp): index for index, timestamp in enumerate(self.m1.time)
        }

    def run(self, trade_from: int, trade_to: int) -> RuleEngineResult:
        pivots = self._detect_pivots()
        fvgs = self._detect_fvgs()
        sources = self._detect_sources()
        sweeps = self._detect_sweeps(pivots)
        liquidity = self._detect_liquidity()
        candidates = self._build_candidates(
            trade_from,
            trade_to,
            pivots,
            fvgs,
            sources,
            sweeps,
            liquidity,
        )
        authorized_candidates = self._authorize_candidates(candidates, sources)
        audit = {
            "runtimeReadsCasebook": False,
            "hardcodedTradeDates": False,
            "hardcodedTradePrices": False,
            "sourceCount": len(sources),
            "sweepCount": len(sweeps),
            "fvgCount": len(fvgs),
            "candidateCount": len(candidates),
            "retestEligibleEvidenceCount": len(authorized_candidates),
            "allSourcesKnownBeforeCandidate": all(
                self._source_by_id(sources, candidate.source_id).available_at
                <= candidate.created_at
                for candidate in candidates
            ),
            "allFvgsKnownBeforeCandidate": all(
                self._fvg_by_id(fvgs, candidate.fvg_id).available_at
                <= candidate.created_at
                for candidate in candidates
            ),
        }
        return RuleEngineResult(
            candidates=candidates,
            authorized_candidates=authorized_candidates,
            sources=sources,
            sweeps=sweeps,
            fvgs=fvgs,
            liquidity=liquidity,
            audit=audit,
        )

    def _apply_owner_state(self, candidates: list[RuleCandidate]) -> None:
        active: dict[str, RuleCandidate] = {}
        for candidate in sorted(
            candidates,
            key=lambda item: (item.created_at, item.direction, item.entry),
        ):
            if candidate.scope != "EXTERNAL_CONTINUATION":
                candidate.owner_id = candidate.candidate_id
                continue
            owner = active.get(candidate.direction)
            owner_live = bool(
                owner
                and owner.objective is not None
                and not self._price_traversed_between(
                    candidate.direction,
                    float(owner.objective),
                    owner.created_at,
                    candidate.created_at,
                )
            )
            lies_on_delivery_path = bool(
                owner_live
                and (
                    float(owner.objective) < candidate.entry <= owner.stop
                    if candidate.direction == "short"
                    else owner.stop <= candidate.entry < float(owner.objective)
                )
            )
            if owner is not None and lies_on_delivery_path:
                candidate.owner_id = owner.owner_id or owner.candidate_id
                candidate.objective = owner.objective
                candidate.objective_id = owner.objective_id
                candidate.objective_kind = owner.objective_kind
                candidate.objective_frozen_at = owner.objective_frozen_at
                candidate.entry_model = (
                    "HTF_OB_REARM"
                    if abs(candidate.entry - owner.entry)
                    <= max(
                        self.config.point * 3,
                        abs(owner.entry - owner.stop) * 0.25,
                    )
                    else "DELIVERY_FVG_ADDON"
                )
                continue
            candidate.owner_id = candidate.candidate_id
            active[candidate.direction] = candidate

    def _price_traversed_between(
        self,
        direction: str,
        level: float,
        start_at: int,
        end_at: int,
    ) -> bool:
        start = int(np.searchsorted(self.m1.time, start_at, side="left"))
        end = int(np.searchsorted(self.m1.time, end_at, side="left"))
        if end <= start:
            return False
        if direction == "short":
            return bool(np.any(self.m1.low[start:end] < level))
        return bool(np.any(self.m1.high[start:end] > level))

    def _authorize_candidates(
        self,
        candidates: list[RuleCandidate],
        sources: list[OrderBlock],
    ) -> list[RuleCandidate]:
        """Convert evidence combinations into first-retest order candidates."""
        source_by_id = {source.source_id: source for source in sources}
        authorized: list[RuleCandidate] = []
        used_chains: set[tuple[object, ...]] = set()
        for candidate in sorted(
            candidates,
            key=lambda item: (item.created_at, item.direction, item.entry),
        ):
            if candidate.objective is None:
                continue
            risk_ok = (
                candidate.stop > candidate.entry > candidate.objective
                if candidate.direction == "short"
                else candidate.stop < candidate.entry < candidate.objective
            )
            if not risk_ok:
                continue
            source = source_by_id[candidate.source_id]
            retest_at = self._first_valid_retest(candidate, source)
            if retest_at is None:
                continue
            # Different source labels can describe the same physical M1 chain.
            # A single sweep/shift/FVG family may authorize only one order.
            physical_chain = (
                candidate.direction,
                candidate.sweep_at,
                candidate.shift_at,
                candidate.fvg_id,
            )
            if physical_chain in used_chains:
                continue
            used_chains.add(physical_chain)
            candidate.retest_at = retest_at
            authorized.append(candidate)
        return authorized

    def _first_valid_retest(
        self,
        candidate: RuleCandidate,
        source: OrderBlock,
    ) -> int | None:
        start = int(
            np.searchsorted(self.m1.time, candidate.created_at, side="left")
        )
        last_time = candidate.created_at + 24 * 3600
        for index in range(start, len(self.m1)):
            bar_time = int(self.m1.time[index])
            available_at = int(self.m1.available_time[index])
            if bar_time > last_time:
                return None
            if (
                source.invalidated_at is not None
                and source.invalidated_at <= available_at
            ):
                return None
            spread = max(
                self.config.point,
                float(self.m1.spread_points[index]) * self.config.point,
            )
            bid_low = float(self.m1.low[index])
            bid_high = float(self.m1.high[index])
            ask_low = bid_low + spread
            ask_high = bid_high + spread
            touched = (
                bid_low <= candidate.entry <= bid_high
                if candidate.direction == "short"
                else ask_low <= candidate.entry <= ask_high
            )
            if touched:
                return available_at
        return None

    def _detect_pivots(self) -> list[Pivot]:
        pivots: list[Pivot] = []
        series = self.m1
        for index in range(1, len(series) - 1):
            if not _contiguous(series, index - 1, index + 1):
                continue
            if (
                series.high[index] > series.high[index - 1]
                and series.high[index] >= series.high[index + 1]
            ):
                pivots.append(
                    Pivot(
                        pivot_id=f"M1:pivot:high:{int(series.time[index])}",
                        side="high",
                        index=index,
                        confirmed_index=index + 1,
                        occurred_at=int(series.time[index]),
                        available_at=int(series.available_time[index + 1]),
                        level=float(series.high[index]),
                    )
                )
            if (
                series.low[index] < series.low[index - 1]
                and series.low[index] <= series.low[index + 1]
            ):
                pivots.append(
                    Pivot(
                        pivot_id=f"M1:pivot:low:{int(series.time[index])}",
                        side="low",
                        index=index,
                        confirmed_index=index + 1,
                        occurred_at=int(series.time[index]),
                        available_at=int(series.available_time[index + 1]),
                        level=float(series.low[index]),
                    )
                )
        return pivots

    def _detect_fvgs(self) -> list[Fvg]:
        series = self.m1
        result: list[Fvg] = []
        for index in range(2, len(series)):
            if not _contiguous(series, index - 2, index):
                continue
            direction: str | None = None
            bottom = 0.0
            top = 0.0
            if series.high[index] < series.low[index - 2]:
                direction = "short"
                bottom = float(series.high[index])
                top = float(series.low[index - 2])
            elif series.low[index] > series.high[index - 2]:
                direction = "long"
                bottom = float(series.high[index - 2])
                top = float(series.low[index])
            if direction is None:
                continue
            result.append(
                Fvg(
                    fvg_id=f"M1:FVG:{direction}:{int(series.time[index])}",
                    direction=direction,
                    origin_index=index - 2,
                    confirmed_index=index,
                    occurred_at=int(series.time[index - 2]),
                    available_at=int(series.available_time[index]),
                    bottom=bottom,
                    top=top,
                )
            )
        return result

    def _detect_sources(self) -> list[OrderBlock]:
        candidates: list[OrderBlock] = []
        for timeframe in self.config.source_timeframes:
            series = self.frames[timeframe]
            for origin in range(len(series)):
                for direction in ("short", "long"):
                    if not _opposite_candle(series, origin, direction):
                        continue
                    confirmation: int | None = None
                    end = min(
                        len(series),
                        origin + self.config.source_confirmation_bars + 1,
                    )
                    distal = (
                        float(series.low[origin])
                        if direction == "short"
                        else float(series.high[origin])
                    )
                    for index in range(origin + 1, end):
                        if not _contiguous(series, index - 1, index):
                            break
                        if _directional_close(
                            direction,
                            float(series.close[index]),
                            distal,
                        ):
                            confirmation = index
                            break
                    if confirmation is None:
                        continue
                    if any(
                        _opposite_candle(series, index, direction)
                        for index in range(origin + 1, confirmation)
                    ):
                        continue
                    bottom = float(series.low[origin])
                    top = float(series.high[origin])
                    available_at = int(series.available_time[confirmation])
                    candidates.append(
                        OrderBlock(
                            source_id=(
                                f"{timeframe}:OB:{direction}:"
                                f"{int(series.time[origin])}:{available_at}"
                            ),
                            timeframe=timeframe,
                            direction=direction,
                            origin_index=origin,
                            confirm_index=confirmation,
                            occurred_at=int(series.time[origin]),
                            available_at=available_at,
                            bottom=bottom,
                            top=top,
                            invalidated_at=self._source_invalidation_at(
                                direction,
                                bottom,
                                top,
                                available_at,
                            ),
                        )
                    )
        return self._deduplicate_sources(candidates)

    def _source_invalidation_at(
        self,
        direction: str,
        bottom: float,
        top: float,
        available_at: int,
    ) -> int | None:
        start = int(
            np.searchsorted(self.m1.available_time, available_at, side="right")
        )
        consecutive = 0
        for index in range(start, len(self.m1)):
            close = float(self.m1.close[index])
            outside = close > top if direction == "short" else close < bottom
            consecutive = consecutive + 1 if outside else 0
            if consecutive >= self.config.permanent_invalidation_closes:
                first = index - self.config.permanent_invalidation_closes + 1
                return int(self.m1.available_time[first])
        return None

    @staticmethod
    def _deduplicate_sources(sources: list[OrderBlock]) -> list[OrderBlock]:
        by_key: dict[tuple[object, ...], OrderBlock] = {}
        for source in sources:
            key = (
                source.timeframe,
                source.direction,
                source.occurred_at,
                round(source.bottom, 6),
                round(source.top, 6),
            )
            prior = by_key.get(key)
            if prior is None or source.available_at < prior.available_at:
                by_key[key] = source
        return sorted(
            by_key.values(),
            key=lambda item: (
                item.available_at,
                item.timeframe,
                item.occurred_at,
            ),
        )

    def _detect_sweeps(self, pivots: list[Pivot]) -> list[SweepEpisode]:
        by_side: dict[str, list[Pivot]] = {"high": [], "low": []}
        for pivot in pivots:
            by_side[pivot.side].append(pivot)
        result: list[SweepEpisode] = []
        for index in range(1, len(self.m1)):
            for side, direction in (("high", "short"), ("low", "long")):
                recent = [
                    pivot
                    for pivot in by_side[side]
                    if (
                        index - self.config.sweep_pivot_lookback
                        <= pivot.index
                        < index
                        and pivot.confirmed_index <= index
                    )
                ]
                if not recent:
                    continue
                recoverable: list[tuple[Pivot, int]] = []
                last = min(
                    len(self.m1) - 1,
                    index + self.config.sweep_recovery_bars,
                )
                for pivot in recent:
                    breached = (
                        float(self.m1.high[index]) > pivot.level
                        if side == "high"
                        else float(self.m1.low[index]) < pivot.level
                    )
                    if not breached:
                        continue
                    for recovery in range(index, last + 1):
                        close = float(self.m1.close[recovery])
                        inside = (
                            close < pivot.level
                            if side == "high"
                            else close > pivot.level
                        )
                        if inside:
                            recoverable.append((pivot, recovery))
                            break
                if not recoverable:
                    continue
                # Select the furthest level among levels that were actually
                # reclaimed. A more distant breach that never recovered must
                # not hide a valid nearer sweep.
                pivot, recovery_index = (
                    max(recoverable, key=lambda item: item[0].level)
                    if side == "high"
                    else min(recoverable, key=lambda item: item[0].level)
                )
                result.append(
                    SweepEpisode(
                        sweep_id=(
                            f"M1:sweep:{direction}:{int(self.m1.time[index])}:"
                            f"{pivot.pivot_id}"
                        ),
                        direction=direction,
                        pivot_id=pivot.pivot_id,
                        index=index,
                        recovery_index=recovery_index,
                        occurred_at=int(self.m1.time[index]),
                        recovered_at=int(self.m1.available_time[recovery_index]),
                        liquidity_level=pivot.level,
                        extreme=float(
                            self.m1.high[index]
                            if side == "high"
                            else self.m1.low[index]
                        ),
                    )
                )
        return result

    def _detect_liquidity(self) -> list[LiquidityLevel]:
        result: list[LiquidityLevel] = []
        for timeframe in ("H1", "M30", "M15", "M5", "M1"):
            series = self.frames[timeframe]
            analysis = analyze_structure(series)
            for wave in analysis.waves:
                side = wave.side.value
                consumed_at = self._liquidity_consumed_at(
                    side,
                    wave.level,
                    wave.available_at,
                )
                result.append(
                    LiquidityLevel(
                        liquidity_id=f"{wave.object_id}:wave",
                        timeframe=timeframe,
                        side=side,
                        occurred_at=wave.occurred_at,
                        available_at=wave.available_at,
                        level=wave.level,
                        rank=wave.rank,
                        kind="WAVE",
                        consumed_at=consumed_at,
                    )
                )
        result.extend(self._equal_liquidity_levels())
        result.extend(self._structural_pivot_liquidity())
        return result

    def _structural_pivot_liquidity(self) -> list[LiquidityLevel]:
        """Keep confirmed M30/M5 reaction extremes as objective evidence.

        The map objective is not an arbitrary RR projection and not every M1
        pivot. Completed M30 map and M5 reaction extremes are reproducible
        representations of external and bounded internal liquidity. Each one
        becomes knowable only after the following timeframe bar closes.
        """
        result: list[LiquidityLevel] = []
        for timeframe in ("M30", "M5"):
            series = self.frames[timeframe]
            for index in range(1, len(series) - 1):
                if not _contiguous(series, index - 1, index + 1):
                    continue
                cases: list[tuple[str, float]] = []
                if (
                    series.high[index] > series.high[index - 1]
                    and series.high[index] >= series.high[index + 1]
                ):
                    cases.append(("high", float(series.high[index])))
                if (
                    series.low[index] < series.low[index - 1]
                    and series.low[index] <= series.low[index + 1]
                ):
                    cases.append(("low", float(series.low[index])))
                for side, level in cases:
                    available_at = int(series.available_time[index + 1])
                    result.append(
                        LiquidityLevel(
                            liquidity_id=(
                                f"{timeframe}:STRUCTURAL_PIVOT:{side}:"
                                f"{int(series.time[index])}"
                            ),
                            timeframe=timeframe,
                            side=side,
                            occurred_at=int(series.time[index]),
                            available_at=available_at,
                            level=level,
                            rank=(
                                "external"
                                if timeframe == "M30"
                                else "internal"
                            ),
                            kind="STRUCTURAL_PIVOT",
                            consumed_at=self._liquidity_consumed_at(
                                side,
                                level,
                                available_at,
                            ),
                        )
                    )
        return result

    def _equal_liquidity_levels(self) -> list[LiquidityLevel]:
        # Equal pools are derived from confirmed M1 pivots and rounded only to
        # the instrument tick. The pool is known when its second pivot confirms.
        pivots = self._detect_pivots()
        result: list[LiquidityLevel] = []
        for side in ("high", "low"):
            values = [pivot for pivot in pivots if pivot.side == side]
            used: set[str] = set()
            for index, pivot in enumerate(values):
                if pivot.pivot_id in used:
                    continue
                cluster = [
                    other
                    for other in values[index + 1 :]
                    if (
                        60 <= other.occurred_at - pivot.occurred_at <= 24 * 3600
                        and abs(other.level - pivot.level)
                        <= max(self.config.point * 3, abs(pivot.level) * 0.000015)
                    )
                ]
                if not cluster:
                    continue
                members = [pivot, cluster[0]]
                used.update(member.pivot_id for member in members)
                level = round(
                    float(np.median([member.level for member in members]))
                    / self.config.point
                ) * self.config.point
                available_at = max(member.available_at for member in members)
                result.append(
                    LiquidityLevel(
                        liquidity_id=(
                            f"M1:EQ:{side}:{pivot.occurred_at}:"
                            f"{cluster[0].occurred_at}"
                        ),
                        timeframe="M1",
                        side=side,
                        occurred_at=min(member.occurred_at for member in members),
                        available_at=available_at,
                        level=level,
                        rank="external",
                        kind="EQUAL_POOL",
                        consumed_at=self._liquidity_consumed_at(
                            side,
                            level,
                            available_at,
                        ),
                    )
                )
        return result

    def _liquidity_consumed_at(
        self,
        side: str,
        level: float,
        available_at: int,
    ) -> int | None:
        start = int(
            np.searchsorted(self.m1.available_time, available_at, side="right")
        )
        for index in range(start, len(self.m1)):
            traversed = (
                float(self.m1.high[index]) > level
                if side == "high"
                else float(self.m1.low[index]) < level
            )
            if traversed:
                return int(self.m1.available_time[index])
        return None

    def _build_candidates(
        self,
        trade_from: int,
        trade_to: int,
        pivots: list[Pivot],
        fvgs: list[Fvg],
        sources: list[OrderBlock],
        sweeps: list[SweepEpisode],
        liquidity: list[LiquidityLevel],
    ) -> list[RuleCandidate]:
        result: list[RuleCandidate] = []
        seen: set[tuple[object, ...]] = set()
        for fvg in fvgs:
            if not (trade_from <= fvg.available_at < trade_to):
                continue
            sweep_options = [
                sweep
                for sweep in sweeps
                if (
                    sweep.direction == fvg.direction
                    and sweep.recovered_at <= fvg.available_at
                    and 0
                    <= fvg.confirmed_index - sweep.index
                    <= self.config.reaction_window_minutes
                )
            ]
            if not sweep_options:
                continue
            paired = [
                (sweep, self._sources_for_sweep(sources, sweep))
                for sweep in sweep_options
            ]
            paired = [(sweep, items) for sweep, items in paired if items]
            if not paired:
                continue
            # Separate distinct reactions first. An older, larger excursion
            # must not steal a later setup merely because both sit inside the
            # broad reaction window. Within the latest physical episode, keep
            # the furthest reclaimed level.
            paired.sort(key=lambda item: item[0].occurred_at)
            episodes: list[list[tuple[SweepEpisode, list[OrderBlock]]]] = []
            episode_source_available_at: list[int] = []
            for item in paired:
                newest_source = max(source.available_at for source in item[1])
                source_reset = bool(
                    episodes
                    and newest_source > episode_source_available_at[-1]
                    and newest_source <= item[0].occurred_at
                )
                if (
                    not episodes
                    or item[0].occurred_at
                    - episodes[-1][-1][0].occurred_at
                    > 10 * 60
                    or source_reset
                ):
                    episodes.append([item])
                    episode_source_available_at.append(newest_source)
                else:
                    episodes[-1].append(item)
                    episode_source_available_at[-1] = max(
                        episode_source_available_at[-1],
                        newest_source,
                    )
            latest_episode = episodes[-1]
            if fvg.direction == "short":
                sweep, source_options = max(
                    latest_episode,
                    key=lambda item: (
                        item[0].extreme,
                        -item[0].occurred_at,
                    ),
                )
            else:
                sweep, source_options = min(
                    latest_episode,
                    key=lambda item: (
                        item[0].extreme,
                        item[0].occurred_at,
                    ),
                )
            shift = self._find_shift(pivots, sweep, fvg)
            if shift is None:
                continue
            parent, execution_source, refinement = self._select_source(
                source_options,
                sweep,
            )
            key = (
                execution_source.source_id,
                sweep.sweep_id,
                fvg.fvg_id,
            )
            if key in seen:
                continue
            seen.add(key)
            map_direction = self._map_direction_at(fvg.available_at)
            scope = (
                "EXTERNAL_CONTINUATION"
                if map_direction == fvg.direction
                else "INTERNAL_ROTATION"
            )
            objective_frozen_at = (
                parent.available_at
                if scope == "EXTERNAL_CONTINUATION"
                else fvg.available_at
            )
            alternatives = self._objective_candidates(
                fvg.direction,
                scope,
                objective_frozen_at,
                fvg.available_at,
                fvg.proximal,
                liquidity,
            )
            primary = alternatives[0] if alternatives else None
            invalidation = (
                max(parent.top, execution_source.top, sweep.extreme)
                if fvg.direction == "short"
                else min(parent.bottom, execution_source.bottom, sweep.extreme)
            )
            spread = self._spread_price_at(fvg.available_at)
            buffer = max(spread, self.config.point)
            stop = (
                invalidation + buffer
                if fvg.direction == "short"
                else invalidation - buffer
            )
            result.append(
                RuleCandidate(
                    candidate_id=(
                        f"SETUP:{fvg.direction}:{fvg.available_at}:"
                        f"{execution_source.source_id}"
                    ),
                    direction=fvg.direction,
                    created_at=fvg.available_at,
                    source_id=execution_source.source_id,
                    source_timeframe=execution_source.timeframe,
                    source_bottom=execution_source.bottom,
                    source_top=execution_source.top,
                    parent_source_id=parent.source_id,
                    refinement_path=refinement,
                    sweep_id=sweep.sweep_id,
                    sweep_at=sweep.occurred_at,
                    sweep_extreme=sweep.extreme,
                    shift_at=shift[0],
                    shift_reference=shift[1],
                    shift_reference_kind=shift[2],
                    fvg_id=fvg.fvg_id,
                    fvg_bottom=fvg.bottom,
                    fvg_top=fvg.top,
                    entry=fvg.proximal,
                    structural_invalidation=invalidation,
                    stop=stop,
                    map_direction=map_direction,
                    scope=scope,
                    objective=float(primary["level"]) if primary else None,
                    objective_id=str(primary["id"]) if primary else None,
                    objective_kind=str(primary["kind"]) if primary else None,
                    objective_frozen_at=objective_frozen_at,
                    objective_alternatives=alternatives,
                    chain_key=(
                        f"{parent.source_id}|{sweep.pivot_id}|"
                        f"{shift[0]}|{fvg.fvg_id}"
                    ),
                )
            )
        return sorted(
            result,
            key=lambda item: (item.created_at, item.direction, item.entry),
        )

    def _sources_for_sweep(
        self,
        sources: list[OrderBlock],
        sweep: SweepEpisode,
    ) -> list[OrderBlock]:
        result: list[OrderBlock] = []
        for source in sources:
            if source.direction != sweep.direction:
                continue
            if source.available_at >= sweep.occurred_at:
                continue
            if not source.active_at(sweep.recovered_at):
                continue
            if not self._source_created_displacement_fvg(source):
                continue
            age_minutes = (sweep.occurred_at - source.occurred_at) / 60
            if not (0 <= age_minutes <= self.config.source_max_age_minutes):
                continue
            # A short reaction must physically reach the OB bottom; a long
            # reaction must reach the OB top. Distance on the approach side is
            # not a touch and cannot be rescued by a broad tolerance.
            if source.direction == "short" and sweep.extreme < source.bottom:
                continue
            if source.direction == "long" and sweep.extreme > source.top:
                continue
            if sweep.extreme > source.top:
                distance = sweep.extreme - source.top
            elif sweep.extreme < source.bottom:
                distance = source.bottom - sweep.extreme
            else:
                distance = 0.0
            allowed = max(
                self.config.source_distance_floor,
                source.width * self.config.source_distance_width_factor,
            )
            if distance <= allowed:
                result.append(source)
        return result

    def _source_created_displacement_fvg(
        self,
        source: OrderBlock,
    ) -> bool:
        series = self.frames[source.timeframe]
        start = max(2, source.confirm_index)
        end = min(len(series), source.confirm_index + 4)
        for index in range(start, end):
            if (
                source.direction == "short"
                and float(series.high[index]) < float(series.low[index - 2])
            ):
                return True
            if (
                source.direction == "long"
                and float(series.low[index]) > float(series.high[index - 2])
            ):
                return True
        return False

    def _select_source(
        self,
        options: list[OrderBlock],
        sweep: SweepEpisode,
    ) -> tuple[OrderBlock, OrderBlock, list[str]]:
        m15 = [source for source in options if source.timeframe == "M15"]
        if m15:
            if sweep.direction == "short":
                parent = max(
                    m15,
                    key=lambda item: (
                        item.top,
                        item.occurred_at,
                        item.available_at,
                    ),
                )
            else:
                parent = min(
                    m15,
                    key=lambda item: (
                        item.bottom,
                        -item.occurred_at,
                        -item.available_at,
                    ),
                )
        else:
            parent = max(
                options,
                key=lambda item: (
                    1 if item.timeframe == "M5" else 0,
                    item.occurred_at,
                    item.available_at,
                ),
            )
        children = [
            source
            for source in options
            if (
                source.timeframe == "M5"
                and parent.timeframe == "M15"
                and parent.occurred_at
                <= source.occurred_at
                < parent.occurred_at + 15 * 60
                and source.bottom >= parent.bottom - self.config.point * 2
                and source.top <= parent.top + self.config.point * 2
            )
        ]
        # A child is unique only if the actual sweep path touched exactly one
        # nested causal candle. Competing children leave execution at M15.
        touched_children = [
            child
            for child in children
            if child.bottom <= sweep.extreme <= child.top
        ]
        if len(touched_children) == 1:
            child = touched_children[0]
            return parent, child, [parent.source_id, child.source_id]
        return parent, parent, [parent.source_id]

    def _find_shift(
        self,
        pivots: list[Pivot],
        sweep: SweepEpisode,
        fvg: Fvg,
    ) -> tuple[int, float, str] | None:
        side = "low" if fvg.direction == "short" else "high"
        start = sweep.recovery_index
        end = fvg.confirmed_index
        pivot_breaks: list[tuple[int, float, str, int]] = []
        for pivot in pivots:
            if not (
                pivot.side == side
                and sweep.index - 45 <= pivot.index < end
                and pivot.confirmed_index < end
            ):
                continue
            first = max(start, pivot.confirmed_index + 1)
            for index in range(first, end + 1):
                close = float(self.m1.close[index])
                if _directional_close(fvg.direction, close, pivot.level):
                    pivot_breaks.append(
                        (
                            int(self.m1.time[index]),
                            pivot.level,
                            "CONFIRMED_PIVOT",
                            pivot.index,
                        )
                    )
                    break
        if pivot_breaks:
            chosen = (
                min(
                    pivot_breaks,
                    key=lambda item: (item[1], -item[3]),
                )
                if fvg.direction == "short"
                else max(
                    pivot_breaks,
                    key=lambda item: (item[1], item[3]),
                )
            )
            return chosen[0], chosen[1], chosen[2]

        # A compact reaction can reverse before a three-candle pivot is
        # confirmable. In that case the live body origin is allowed only as
        # the latest first-time break completed by this FVG displacement.
        body_breaks: list[tuple[int, float, str, int]] = []
        for origin in range(max(0, sweep.index - 1), end):
            if not _opposite_candle(self.m1, origin, fvg.direction):
                continue
            origin_body = abs(
                float(self.m1.close[origin]) - float(self.m1.open[origin])
            )
            origin_spread = max(
                self.config.point,
                float(self.m1.spread_points[origin]) * self.config.point,
            )
            if origin_body < origin_spread:
                continue
            reference = float(self.m1.open[origin])
            for index in range(max(start, origin + 1), end + 1):
                if _directional_close(
                    fvg.direction,
                    float(self.m1.close[index]),
                    reference,
                ):
                    body_breaks.append(
                        (
                            int(self.m1.time[index]),
                            reference,
                            "LIVE_BODY_ORIGIN",
                            origin,
                        )
                    )
                    break
        if not body_breaks:
            return None
        chosen = max(body_breaks, key=lambda item: (item[0], item[3]))
        return chosen[0], chosen[1], chosen[2]

    def _map_direction_at(self, timestamp: int) -> str:
        series = self.frames["M30"]
        analysis = analyze_structure(series)
        events = [
            event for event in analysis.events if event.available_at <= timestamp
        ]
        if events:
            return events[-1].direction.value
        index = index_at_or_before(series, timestamp)
        if index < 2:
            return "long"
        return (
            "long"
            if float(series.close[index]) >= float(series.close[index - 2])
            else "short"
        )

    def _objective_candidates(
        self,
        direction: str,
        scope: str,
        known_at: int,
        as_of: int,
        entry: float,
        liquidity: list[LiquidityLevel],
    ) -> list[dict[str, object]]:
        side = "low" if direction == "short" else "high"
        active = [
            level
            for level in liquidity
            if (
                level.side == side
                and level.available_at <= known_at
                and level.active_at(as_of)
                and (level.level < entry if direction == "short" else level.level > entry)
                and (
                    scope != "EXTERNAL_CONTINUATION"
                    or level.timeframe in {"H1", "M30", "M15"}
                )
                and (
                    scope != "INTERNAL_ROTATION"
                    or level.timeframe in {"H1", "M30", "M15", "M5"}
                )
            )
        ]
        wave_levels = [level.level for level in active if level.kind == "WAVE"]
        boundary_levels: list[float] = []
        for timeframe in ("H1", "M30"):
            series = self.frames[timeframe]
            analysis = analyze_structure(series)
            index = index_at_or_before(series, known_at)
            if index < 0:
                continue
            values = (
                (analysis.range_low[index], analysis.protected_low[index])
                if direction == "short"
                else (analysis.range_high[index], analysis.protected_high[index])
            )
            boundary_levels.extend(
                float(value) for value in values if np.isfinite(value)
            )
        active = [
            level
            for level in active
            if (
                level.kind == "WAVE"
                or any(
                    abs(level.level - wave_level) <= self.config.point * 3
                    for wave_level in wave_levels
                )
                or any(
                    abs(level.level - boundary) <= self.config.point * 3
                    for boundary in boundary_levels
                )
            )
        ]
        timeframe_rank = {"H1": 5, "M30": 4, "M15": 3, "M5": 2, "M1": 1}

        def quality(level: LiquidityLevel) -> tuple[float, ...]:
            objective_class = (
                0
                if (
                    level.timeframe in {"H1", "M30", "M15"}
                    and level.rank == "external"
                )
                else 1
            )
            kind_class = (
                0
                if level.kind == "WAVE"
                else 1
                if level.kind == "STRUCTURAL_PIVOT"
                else 2
            )
            structural = (
                3
                if level.kind == "EQUAL_POOL"
                else 2
                if level.rank == "external"
                else 1
            )
            if scope == "EXTERNAL_CONTINUATION":
                structural += 1 if timeframe_rank[level.timeframe] >= 3 else 0
            distance = abs(entry - level.level)
            return (
                float(objective_class),
                distance,
                float(kind_class),
                float(-structural),
                float(-timeframe_rank[level.timeframe]),
            )

        ordered = sorted(active, key=quality)
        return [
            {
                "id": level.liquidity_id,
                "level": level.level,
                "timeframe": level.timeframe,
                "kind": level.kind,
                "rank": level.rank,
                "distance": abs(entry - level.level),
            }
            for level in ordered
        ]

    def _spread_price_at(self, timestamp: int) -> float:
        index = int(
            np.searchsorted(self.m1.available_time, timestamp, side="right") - 1
        )
        if index < 0:
            return self.config.point
        return max(
            self.config.point,
            float(self.m1.spread_points[index]) * self.config.point,
        )

    @staticmethod
    def _source_by_id(
        sources: Iterable[OrderBlock],
        source_id: str,
    ) -> OrderBlock:
        return next(source for source in sources if source.source_id == source_id)

    @staticmethod
    def _fvg_by_id(fvgs: Iterable[Fvg], fvg_id: str) -> Fvg:
        return next(fvg for fvg in fvgs if fvg.fvg_id == fvg_id)
