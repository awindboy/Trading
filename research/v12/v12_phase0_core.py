"""Causal Phase-0 primitives for the V12 CRT event universe.

The module deliberately has no pandas dependency and never needs to load the
complete M1 source.  A caller reveals rows in chronological order, aggregates
completed broker-clock bars, and constructs exhaustive C1/C2 observations.
No trigger, entry, or P/L authority is implemented here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, Iterator, Mapping, MutableMapping, Optional


SCHEMA_VERSION = "12.0.0-phase0"
EVENT_DEFINITION_VERSION = "v12-phase0-c1c2-v1"
POINT_SIZE = 0.01

TIMEFRAME_MINUTES: Mapping[str, int] = {
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1_440,
    "W1": 10_080,
}

LANE_PARENT_TF: Mapping[str, str] = {
    "W1_TO_H4": "W1",
    "D1_TO_H1": "D1",
}


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json_file(path: Path) -> str:
    return hashlib.sha256(canonical_json_bytes(json.loads(path.read_text(encoding="utf-8")))).hexdigest()


def parse_broker_timestamp(date_text: str, time_text: Optional[str] = None) -> datetime:
    if time_text:
        return datetime.strptime(f"{date_text} {time_text}", "%Y.%m.%d %H:%M:%S")
    return datetime.strptime(date_text, "%Y.%m.%d")


def iso_broker_label(value: datetime) -> str:
    """Return an offset-free ISO label in the frozen MT5 broker namespace."""

    return value.isoformat(timespec="seconds")


def bucket_start(timestamp: datetime, timeframe: str) -> datetime:
    if timeframe not in TIMEFRAME_MINUTES:
        raise ValueError(f"unsupported timeframe: {timeframe}")
    base = timestamp.replace(second=0, microsecond=0)
    if timeframe == "M5":
        return base.replace(minute=(base.minute // 5) * 5)
    if timeframe == "M15":
        return base.replace(minute=(base.minute // 15) * 15)
    if timeframe == "M30":
        return base.replace(minute=(base.minute // 30) * 30)
    if timeframe == "H1":
        return base.replace(minute=0)
    if timeframe == "H4":
        return base.replace(hour=(base.hour // 4) * 4, minute=0)
    if timeframe == "D1":
        return base.replace(hour=0, minute=0)
    # Python Monday=0.  MT5 export proves this broker's W1 label is Sunday.
    days_since_sunday = (base.weekday() + 1) % 7
    return (base - timedelta(days=days_since_sunday)).replace(hour=0, minute=0)


def bucket_end(start: datetime, timeframe: str) -> datetime:
    return start + timedelta(minutes=TIMEFRAME_MINUTES[timeframe])


def price_points(value: float, point_size: float = POINT_SIZE) -> int:
    # MT5 prices in this source have two decimals.  The tiny epsilon protects
    # values such as 1929.229999999 after binary float parsing.
    return int(round((value / point_size) + 1e-9))


@dataclass(frozen=True)
class M1Row:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    volume: int
    spread: int


@dataclass
class CompletedBar:
    timeframe: str
    open_time: datetime
    close_time: datetime
    first_m1_time: datetime
    last_m1_time: datetime
    completed_by_observation: datetime
    open: float
    high: float
    low: float
    close: float
    m1_rows: int
    tick_volume: int
    volume: int
    last_spread: int
    max_spread: int
    true_range: Optional[float] = None
    atr14: Optional[float] = None

    @property
    def range(self) -> float:
        return self.high - self.low

    @property
    def body_ratio(self) -> Optional[float]:
        if self.range <= 0:
            return None
        return abs(self.close - self.open) / self.range

    @property
    def range_atr(self) -> Optional[float]:
        if not self.atr14:
            return None
        return self.range / self.atr14

    @property
    def first_offset_minutes(self) -> int:
        return int((self.first_m1_time - self.open_time).total_seconds() // 60)

    @property
    def last_offset_minutes(self) -> int:
        return int((self.last_m1_time - self.open_time).total_seconds() // 60)

    @property
    def internal_missing_minutes(self) -> int:
        span = int((self.last_m1_time - self.first_m1_time).total_seconds() // 60) + 1
        return max(0, span - self.m1_rows)


@dataclass
class _BarBuilder:
    timeframe: str
    open_time: datetime
    first_m1_time: datetime
    last_m1_time: datetime
    open: float
    high: float
    low: float
    close: float
    m1_rows: int
    tick_volume: int
    volume: int
    last_spread: int
    max_spread: int

    @classmethod
    def start(cls, timeframe: str, key: datetime, row: M1Row) -> "_BarBuilder":
        return cls(
            timeframe=timeframe,
            open_time=key,
            first_m1_time=row.timestamp,
            last_m1_time=row.timestamp,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            m1_rows=1,
            tick_volume=row.tick_volume,
            volume=row.volume,
            last_spread=row.spread,
            max_spread=row.spread,
        )

    def update(self, row: M1Row) -> None:
        self.last_m1_time = row.timestamp
        self.high = max(self.high, row.high)
        self.low = min(self.low, row.low)
        self.close = row.close
        self.m1_rows += 1
        self.tick_volume += row.tick_volume
        self.volume += row.volume
        self.last_spread = row.spread
        self.max_spread = max(self.max_spread, row.spread)

    def finish(self, completed_by: datetime) -> CompletedBar:
        return CompletedBar(
            timeframe=self.timeframe,
            open_time=self.open_time,
            close_time=bucket_end(self.open_time, self.timeframe),
            first_m1_time=self.first_m1_time,
            last_m1_time=self.last_m1_time,
            completed_by_observation=completed_by,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            m1_rows=self.m1_rows,
            tick_volume=self.tick_volume,
            volume=self.volume,
            last_spread=self.last_spread,
            max_spread=self.max_spread,
        )


@dataclass
class StreamQuality:
    rows: int = 0
    first_timestamp: Optional[datetime] = None
    last_timestamp: Optional[datetime] = None
    duplicate_timestamps: int = 0
    non_monotonic_timestamps: int = 0
    invalid_ohlc_rows: int = 0
    negative_volume_rows: int = 0
    off_grid_price_rows: int = 0
    one_minute_steps: int = 0
    gap_steps: int = 0
    largest_gap_minutes: int = 0
    gap_histogram: MutableMapping[str, int] = field(default_factory=dict)

    def observe(self, row: M1Row, previous: Optional[M1Row]) -> None:
        self.rows += 1
        if self.first_timestamp is None:
            self.first_timestamp = row.timestamp
        self.last_timestamp = row.timestamp
        if not (
            row.high >= max(row.open, row.close)
            and row.low <= min(row.open, row.close)
            and row.high >= row.low
        ):
            self.invalid_ohlc_rows += 1
        if row.tick_volume < 0 or row.volume < 0 or row.spread < 0:
            self.negative_volume_rows += 1
        if any(abs((price / POINT_SIZE) - round(price / POINT_SIZE)) > 1e-7 for price in (row.open, row.high, row.low, row.close)):
            self.off_grid_price_rows += 1
        if previous is None:
            return
        delta_minutes = int((row.timestamp - previous.timestamp).total_seconds() // 60)
        if delta_minutes == 0:
            self.duplicate_timestamps += 1
        elif delta_minutes < 0:
            self.non_monotonic_timestamps += 1
        elif delta_minutes == 1:
            self.one_minute_steps += 1
        else:
            self.gap_steps += 1
            self.largest_gap_minutes = max(self.largest_gap_minutes, delta_minutes)
            if delta_minutes <= 5:
                key = "2_5_MIN"
            elif delta_minutes <= 60:
                key = "6_60_MIN"
            elif delta_minutes <= 1_440:
                key = "61_1440_MIN"
            else:
                key = "GT_1440_MIN"
            self.gap_histogram[key] = self.gap_histogram.get(key, 0) + 1

    def to_dict(self) -> dict:
        value = asdict(self)
        value["first_timestamp"] = iso_broker_label(self.first_timestamp) if self.first_timestamp else None
        value["last_timestamp"] = iso_broker_label(self.last_timestamp) if self.last_timestamp else None
        value["gap_histogram"] = dict(sorted(self.gap_histogram.items()))
        return value


class MultiTimeframeAggregator:
    def __init__(self, timeframes: Iterable[str] = TIMEFRAME_MINUTES) -> None:
        self.timeframes = tuple(timeframes)
        self.current: Dict[str, _BarBuilder] = {}
        self.completed: Dict[str, list[CompletedBar]] = {tf: [] for tf in self.timeframes}

    def observe(self, row: M1Row) -> None:
        for timeframe in self.timeframes:
            key = bucket_start(row.timestamp, timeframe)
            current = self.current.get(timeframe)
            if current is None:
                self.current[timeframe] = _BarBuilder.start(timeframe, key, row)
                continue
            if key < current.open_time:
                raise ValueError(f"non-monotonic {timeframe} bucket at {row.timestamp}")
            if key == current.open_time:
                current.update(row)
                continue
            self.completed[timeframe].append(current.finish(row.timestamp))
            self.current[timeframe] = _BarBuilder.start(timeframe, key, row)

    def terminal_buckets(self) -> dict[str, dict]:
        result: dict[str, dict] = {}
        for timeframe, current in self.current.items():
            result[timeframe] = {
                "open_time": iso_broker_label(current.open_time),
                "close_time": iso_broker_label(bucket_end(current.open_time, timeframe)),
                "first_m1_time": iso_broker_label(current.first_m1_time),
                "last_m1_time": iso_broker_label(current.last_m1_time),
                "m1_rows": current.m1_rows,
                "status": "EXCLUDED_TERMINAL_UNCONFIRMED",
            }
        return result


def attach_wilder_atr(bars: list[CompletedBar], period: int = 14) -> None:
    seed: list[float] = []
    atr: Optional[float] = None
    previous_close: Optional[float] = None
    for bar in bars:
        true_range = bar.range if previous_close is None else max(
            bar.range,
            abs(bar.high - previous_close),
            abs(bar.low - previous_close),
        )
        bar.true_range = true_range
        if atr is None:
            seed.append(true_range)
            if len(seed) == period:
                atr = sum(seed) / period
                bar.atr14 = atr
        else:
            atr = ((atr * (period - 1)) + true_range) / period
            bar.atr14 = atr
        previous_close = bar.close


def classify_c2(c1: CompletedBar, c2: CompletedBar) -> dict:
    c1_high = price_points(c1.high)
    c1_low = price_points(c1.low)
    c2_high = price_points(c2.high)
    c2_low = price_points(c2.low)
    c2_close = price_points(c2.close)

    high_breach = c2_high > c1_high
    low_breach = c2_low < c1_low
    close_above = c2_close > c1_high
    close_below = c2_close < c1_low
    close_inside = c1_low <= c2_close <= c1_high

    if high_breach and low_breach:
        interaction = "DUAL_SWEEP_INSIDE" if close_inside else "DUAL_OR_CONFLICTED"
        direction = "NONE"
    elif high_breach:
        if close_above:
            interaction = "HIGH_OUTSIDE_ACCEPTANCE"
            direction = "LONG"
        else:
            interaction = "HIGH_SWEEP_RETURN"
            direction = "SHORT"
    elif low_breach:
        if close_below:
            interaction = "LOW_OUTSIDE_ACCEPTANCE"
            direction = "SHORT"
        else:
            interaction = "LOW_SWEEP_RETURN"
            direction = "LONG"
    else:
        interaction = "NO_EXTREME_TRADE"
        direction = "NONE"

    if interaction.startswith("HIGH_"):
        sweep_depth = max(0.0, c2.high - c1.high)
    elif interaction.startswith("LOW_"):
        sweep_depth = max(0.0, c1.low - c2.low)
    else:
        sweep_depth = None

    c1_range = c1.range
    return {
        "interaction": interaction,
        "direction": direction,
        "traded_high": high_breach,
        "traded_low": low_breach,
        "equal_high_touch": c2_high == c1_high,
        "equal_low_touch": c2_low == c1_low,
        "raw_high_breach": c2.high > c1.high,
        "raw_low_breach": c2.low < c1.low,
        "high_sweep_depth_price": max(0.0, c2.high - c1.high) if high_breach else None,
        "low_sweep_depth_price": max(0.0, c1.low - c2.low) if low_breach else None,
        "sweep_depth_price": sweep_depth,
        "sweep_depth_c1_range": (sweep_depth / c1_range) if sweep_depth is not None and c1_range > 0 else None,
        "sweep_depth_atr": (sweep_depth / c2.atr14) if sweep_depth is not None and c2.atr14 else None,
        "close_location_c1": ((c2.close - c1.low) / c1_range) if c1_range > 0 else 0.5,
    }


def parent_id(
    *,
    symbol: str,
    lane: str,
    c1_open: datetime,
    c2_open: datetime,
    broker_clock_spec_sha256: str,
    source_prefix_sha256: str,
) -> str:
    payload = {
        "symbol": symbol,
        "lane": lane,
        "c1_open": iso_broker_label(c1_open),
        "c2_open": iso_broker_label(c2_open),
        "broker_clock_spec_sha256": broker_clock_spec_sha256,
        "source_prefix_sha256": source_prefix_sha256,
    }
    return "v12p0-" + hashlib.sha256(canonical_json_bytes(payload)).hexdigest()[:24]


def schema_bar(bar: CompletedBar) -> dict:
    return {
        "open_time": iso_broker_label(bar.open_time),
        "close_time": iso_broker_label(bar.close_time),
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
        "complete": True,
        "range_atr": bar.range_atr,
        "body_ratio": bar.body_ratio,
    }


def make_phase0_decision(
    *,
    symbol: str,
    lane: str,
    c1: CompletedBar,
    c2: CompletedBar,
    source_prefix_sha256: str,
    broker_clock_spec_sha256: str,
    ordering_precision: str = "M1",
) -> tuple[dict, dict]:
    state = classify_c2(c1, c2)
    pid = parent_id(
        symbol=symbol,
        lane=lane,
        c1_open=c1.open_time,
        c2_open=c2.open_time,
        broker_clock_spec_sha256=broker_clock_spec_sha256,
        source_prefix_sha256=source_prefix_sha256,
    )
    interaction = state["interaction"]
    if interaction == "NO_EXTREME_TRADE":
        parent_state = "C2_CLOSED_NO_TRADE"
    elif interaction in {"HIGH_SWEEP_RETURN", "LOW_SWEEP_RETURN"}:
        parent_state = "C2_REJECTION_OBSERVED"
    elif interaction in {"HIGH_OUTSIDE_ACCEPTANCE", "LOW_OUTSIDE_ACCEPTANCE"}:
        parent_state = "C2_OUTSIDE_ACCEPTANCE_OBSERVED"
    else:
        parent_state = "C2_CONFLICTED"

    direction = state["direction"]
    risk_extreme = c2.low if direction == "LONG" else c2.high if direction == "SHORT" else None
    opposite = c1.high if direction == "LONG" else c1.low if direction == "SHORT" else None

    decision = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "decision",
        "generation": "V12",
        "symbol": symbol,
        "lane": lane,
        "source_dataset_sha256": source_prefix_sha256,
        "broker_clock_spec_sha256": broker_clock_spec_sha256,
        "event_definition_version": EVENT_DEFINITION_VERSION,
        "parent_id": pid,
        "child_id": None,
        "decision_time": iso_broker_label(c2.close_time),
        "c1": schema_bar(c1),
        "c1_midpoint": (c1.high + c1.low) / 2.0,
        "c2": {
            "bar": schema_bar(c2),
            "interaction": interaction,
            "traded_high": state["traded_high"],
            "traded_low": state["traded_low"],
            "sweep_depth_price": state["sweep_depth_price"],
            "sweep_depth_c1_range": state["sweep_depth_c1_range"],
            "sweep_depth_atr": state["sweep_depth_atr"],
            "close_location_c1": state["close_location_c1"],
            "ordering_precision": ordering_precision,
        },
        "parent_state": parent_state,
        "hypothesis_direction": direction,
        "trigger": {
            "status": "NOT_OBSERVED",
            "family": "NONE",
            "trigger_time": None,
            "confirmation_time": None,
            "level_price": None,
            "trigger_bar": None,
            "close_through_strength_atr": None,
            "fvg_present": None,
            "definition_version": None,
        },
        "risk_variants": {
            "c2_extreme": risk_extreme,
            "trigger_structure": None,
            "active_variant": "NONE",
        },
        "targets": {
            "c1_midpoint": (c1.high + c1.low) / 2.0,
            "opposite_c1_extreme": opposite,
            "older_liquidity": None,
        },
        "features": {
            "atr": {"value": c2.atr14, "period": 14, "source_timeframe": c2.timeframe},
            "ha": {
                "fast_color": "MISSING",
                "std_color": "MISSING",
                "slow_color": "MISSING",
                "agreement": None,
                "feature_version": "not-computed-phase0",
            },
            "wave": {
                "available": False,
                "settlement_direction": None,
                "path_efficiency": None,
                "feature_version": "not-computed-phase0",
            },
            "liquidity": {
                "prior_day_high_atr": None,
                "prior_day_low_atr": None,
                "prior_week_high_atr": None,
                "prior_week_low_atr": None,
                "feature_version": "not-computed-phase0",
            },
            "smt": {
                "available": False,
                "paired_symbol": None,
                "state": "NOT_EVALUATED",
                "feature_version": "not-computed-phase0",
            },
        },
        "compliance": {
            "causal_prefix": True,
            "completed_c2": True,
            "future_fields_absent": True,
            "incident_codes": [],
        },
    }

    rich = {
        "parent_id": pid,
        "lane": lane,
        "parent_timeframe": c2.timeframe,
        "decision_time": iso_broker_label(c2.close_time),
        "completion_observed_at": iso_broker_label(c2.completed_by_observation),
        "interaction": interaction,
        "hypothesis_direction": direction,
        "c1_open_time": iso_broker_label(c1.open_time),
        "c1_close_time": iso_broker_label(c1.close_time),
        "c1_open": c1.open,
        "c1_high": c1.high,
        "c1_low": c1.low,
        "c1_close": c1.close,
        "c1_midpoint": (c1.high + c1.low) / 2.0,
        "c1_range": c1.range,
        "c1_range_atr": c1.range_atr,
        "c1_body_ratio": c1.body_ratio,
        "c1_m1_rows": c1.m1_rows,
        "c1_first_offset_minutes": c1.first_offset_minutes,
        "c1_last_offset_minutes": c1.last_offset_minutes,
        "c1_internal_missing_minutes": c1.internal_missing_minutes,
        "c2_open_time": iso_broker_label(c2.open_time),
        "c2_close_time": iso_broker_label(c2.close_time),
        "c2_open": c2.open,
        "c2_high": c2.high,
        "c2_low": c2.low,
        "c2_close": c2.close,
        "c2_range": c2.range,
        "c2_range_atr": c2.range_atr,
        "c2_body_ratio": c2.body_ratio,
        "c2_m1_rows": c2.m1_rows,
        "c2_first_offset_minutes": c2.first_offset_minutes,
        "c2_last_offset_minutes": c2.last_offset_minutes,
        "c2_internal_missing_minutes": c2.internal_missing_minutes,
        "traded_high": state["traded_high"],
        "traded_low": state["traded_low"],
        "equal_high_touch": state["equal_high_touch"],
        "equal_low_touch": state["equal_low_touch"],
        "raw_high_breach": state["raw_high_breach"],
        "raw_low_breach": state["raw_low_breach"],
        "high_sweep_depth_price": state["high_sweep_depth_price"],
        "low_sweep_depth_price": state["low_sweep_depth_price"],
        "sweep_depth_price": state["sweep_depth_price"],
        "sweep_depth_c1_range": state["sweep_depth_c1_range"],
        "sweep_depth_atr": state["sweep_depth_atr"],
        "close_location_c1": state["close_location_c1"],
        "first_high_breach_time": None,
        "first_low_breach_time": None,
        "extreme_ordering": "NOT_APPLICABLE",
        "ordering_precision": ordering_precision,
        "outcome_fields_present": False,
    }
    return decision, rich


def build_parent_events(
    bars_by_timeframe: Mapping[str, list[CompletedBar]],
    *,
    symbol: str,
    source_prefix_sha256: str,
    broker_clock_spec_sha256: str,
) -> tuple[list[dict], list[dict]]:
    decisions: list[dict] = []
    rich_rows: list[dict] = []
    for lane, parent_tf in LANE_PARENT_TF.items():
        bars = bars_by_timeframe[parent_tf]
        for c1, c2 in zip(bars, bars[1:]):
            decision, rich = make_phase0_decision(
                symbol=symbol,
                lane=lane,
                c1=c1,
                c2=c2,
                source_prefix_sha256=source_prefix_sha256,
                broker_clock_spec_sha256=broker_clock_spec_sha256,
            )
            decisions.append(decision)
            rich_rows.append(rich)
    order = sorted(range(len(decisions)), key=lambda i: (decisions[i]["decision_time"], decisions[i]["lane"]))
    return [decisions[i] for i in order], [rich_rows[i] for i in order]


def enrich_extreme_times(rows: Iterable[M1Row], rich_events: list[dict]) -> None:
    """Attach the first causal M1 that breached each C1 extreme.

    The function mutates only observation fields.  It never reads future prices
    beyond each event's completed C2 bucket and never creates a trade outcome.
    """

    lookup: dict[tuple[str, datetime], dict] = {}
    for event in rich_events:
        c2_open = datetime.fromisoformat(event["c2_open_time"])
        lookup[(event["parent_timeframe"], c2_open)] = event

    for row in rows:
        for timeframe in ("D1", "W1"):
            event = lookup.get((timeframe, bucket_start(row.timestamp, timeframe)))
            if event is None:
                continue
            if event["traded_high"] and event["first_high_breach_time"] is None:
                if price_points(row.high) > price_points(event["c1_high"]):
                    event["first_high_breach_time"] = iso_broker_label(row.timestamp)
            if event["traded_low"] and event["first_low_breach_time"] is None:
                if price_points(row.low) < price_points(event["c1_low"]):
                    event["first_low_breach_time"] = iso_broker_label(row.timestamp)

    for event in rich_events:
        high_time = event["first_high_breach_time"]
        low_time = event["first_low_breach_time"]
        if high_time and low_time:
            if high_time == low_time:
                event["extreme_ordering"] = "SAME_M1_AMBIGUOUS"
                event["ordering_precision"] = "AMBIGUOUS"
            elif high_time < low_time:
                event["extreme_ordering"] = "HIGH_THEN_LOW"
            else:
                event["extreme_ordering"] = "LOW_THEN_HIGH"
        elif high_time:
            event["extreme_ordering"] = "HIGH_ONLY"
        elif low_time:
            event["extreme_ordering"] = "LOW_ONLY"
        else:
            event["extreme_ordering"] = "NO_BREACH"


def bar_to_flat_dict(bar: CompletedBar) -> dict:
    return {
        "timeframe": bar.timeframe,
        "open_time": iso_broker_label(bar.open_time),
        "close_time": iso_broker_label(bar.close_time),
        "first_m1_time": iso_broker_label(bar.first_m1_time),
        "last_m1_time": iso_broker_label(bar.last_m1_time),
        "completed_by_observation": iso_broker_label(bar.completed_by_observation),
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
        "m1_rows": bar.m1_rows,
        "tick_volume": bar.tick_volume,
        "volume": bar.volume,
        "last_spread": bar.last_spread,
        "max_spread": bar.max_spread,
        "true_range": bar.true_range,
        "atr14": bar.atr14,
        "range_atr": bar.range_atr,
        "body_ratio": bar.body_ratio,
        "first_offset_minutes": bar.first_offset_minutes,
        "last_offset_minutes": bar.last_offset_minutes,
        "internal_missing_minutes": bar.internal_missing_minutes,
    }
