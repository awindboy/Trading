#!/usr/bin/env python3
"""V9 hindsight-free dual-clock semantic runtime (implementation gate).

Streams the authoritative GOLD# M1 source chronologically.  For every source row:

1. parse the row timestamp only;
2. finalize all prior M5/M15/H1/H4 buckets proven complete by that timestamp;
3. process completed-bar semantic events in deterministic known_at order;
4. only then parse/expose the current M1 OHLC.

The runtime never uses H1/H4/M15/M5 exports as decision inputs.  Those exports are
allowed only in external parity tests.

This module implements the continuous market-state layer.  Child/order execution is
kept in a separate manager so the market grammar does not silently acquire trade
filters.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Deque, Iterable, Iterator, Optional

AUTHORITATIVE_SHA256 = "626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2"
EXPECTED_HEADER = [
    "<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>",
    "<TICKVOL>", "<VOL>", "<SPREAD>",
]
TS_FMT = "%Y.%m.%d %H:%M:%S"
CLI_FMT = "%Y-%m-%d %H:%M:%S"
RUNTIME_VERSION = "v9-semantic-runtime-1"
EVENT_PLAN_VERSION = "v9-parent-child-flow-20260912-impl1"

# Strict consumed-data blocks.  No July OHLC and no Dec-2025 warmup.
BLOCKS = (
    ("2025H1", datetime(2025, 1, 1), datetime(2025, 7, 1)),
    ("2026JF", datetime(2026, 1, 1), datetime(2026, 3, 1)),
)
BLOCK_END = {name: end for name, _, end in BLOCKS}

# When multiple completed bars become known at the same logical time, higher scale
# is processed first.  This reproduces H1 merge_asof against the latest known H4.
TF_PRIORITY = {240: 10, 60: 20, 5: 30, 15: 40}
TF_NAME = {5: "M5", 15: "M15", 60: "H1", 240: "H4"}


class RuntimeErrorV9(RuntimeError):
    pass


def fmt(ts: Optional[datetime]) -> Optional[str]:
    return ts.strftime(CLI_FMT) if ts is not None else None


def parse_cli(value: str) -> datetime:
    return datetime.strptime(value, CLI_FMT)


def fast_ts(date_s: str, time_s: str) -> datetime:
    # Broker source uses YYYY.MM.DD HH:MM:SS.
    return datetime(
        int(date_s[0:4]), int(date_s[5:7]), int(date_s[8:10]),
        int(time_s[0:2]), int(time_s[3:5]), int(time_s[6:8]),
    )


def block_for_ts(ts: datetime) -> Optional[str]:
    for name, start, end in BLOCKS:
        if start <= ts < end:
            return name
    return None


def bucket_start(ts: datetime, minutes: int) -> datetime:
    if minutes == 240:
        return ts.replace(hour=(ts.hour // 4) * 4, minute=0, second=0, microsecond=0)
    if minutes == 60:
        return ts.replace(minute=0, second=0, microsecond=0)
    return ts.replace(minute=(ts.minute // minutes) * minutes, second=0, microsecond=0)


def sha256_file(path: Path, chunk: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                return h.hexdigest()
            h.update(b)


def majority3(values: Iterable[str]) -> str:
    vals = list(values)
    counts: dict[str, int] = {}
    order: list[str] = []
    for v in vals:
        if v not in counts:
            order.append(v)
            counts[v] = 0
        counts[v] += 1
    # pandas value_counts tie order is not used when max<2.  With 3 values a max>=2
    # is unique; otherwise AMBIGUOUS.
    best = max(counts.values()) if counts else 0
    if best < 2:
        return "AMBIGUOUS"
    return next(v for v in order if counts[v] == best)


def agree_n(values: Iterable[str]) -> int:
    counts: dict[str, int] = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    return max(counts.values()) if counts else 0


def state_side(st: str) -> str:
    if st.endswith("_UP"):
        return "UP"
    if st.endswith("_DOWN"):
        return "DOWN"
    if st == "BALANCE":
        return "BALANCE"
    if st == "WARMUP":
        return "WARMUP"
    return "AMBIGUOUS"


def role_state(slow: str, fast: str) -> str:
    if slow == "BAL":
        return "BALANCE"
    if fast == slow:
        return "MIG_" + slow
    if fast == "BAL":
        return "PAUSE_" + slow
    return "REPAIR_" + slow


def combine_slow(a: str, b: str) -> str:
    if a == b and a in ("UP", "DOWN"):
        return a
    if a in ("UP", "DOWN") and b == "BAL":
        return a
    if b in ("UP", "DOWN") and a == "BAL":
        return b
    return "BAL"


@dataclass
class M1Row:
    ts: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass
class CompletedBar:
    block: str
    minutes: int
    start: datetime
    known_at: datetime
    price_revealed_cutoff: datetime
    open: float
    high: float
    low: float
    close: float
    observed_rows: int


@dataclass
class Bucket:
    block: str
    minutes: int
    start: datetime
    open: float
    high: float
    low: float
    close: float
    last_ts: datetime
    observed_rows: int = 1

    def update(self, row: M1Row) -> None:
        self.high = max(self.high, row.high)
        self.low = min(self.low, row.low)
        self.close = row.close
        self.last_ts = row.ts
        self.observed_rows += 1

    @property
    def known_at(self) -> datetime:
        return self.start + timedelta(minutes=self.minutes)

    def complete(self) -> CompletedBar:
        return CompletedBar(
            block=self.block,
            minutes=self.minutes,
            start=self.start,
            known_at=self.known_at,
            price_revealed_cutoff=self.last_ts,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            observed_rows=self.observed_rows,
        )


class BucketSet:
    def __init__(self) -> None:
        self.current: dict[int, Optional[Bucket]] = {m: None for m in TF_PRIORITY}

    def due_before_row(self, ts: datetime, block: Optional[str]) -> list[CompletedBar]:
        due: list[CompletedBar] = []
        for minutes in TF_PRIORITY:
            b = self.current[minutes]
            if b is None:
                continue
            next_start = bucket_start(ts, minutes) if block == b.block else None
            if block != b.block or next_start != b.start:
                if b.known_at < BLOCK_END[b.block]:
                    due.append(b.complete())
                self.current[minutes] = None
        due.sort(key=lambda x: (x.known_at, TF_PRIORITY[x.minutes]))
        return due

    def add_row(self, block: str, row: M1Row) -> None:
        for minutes in TF_PRIORITY:
            start = bucket_start(row.ts, minutes)
            b = self.current[minutes]
            if b is None:
                self.current[minutes] = Bucket(
                    block=block, minutes=minutes, start=start,
                    open=row.open, high=row.high, low=row.low, close=row.close,
                    last_ts=row.ts,
                )
            else:
                if b.block != block or b.start != start:
                    raise RuntimeErrorV9("bucket transition was not finalized before OHLC exposure")
                b.update(row)

    def flush_block(self, block: str) -> list[CompletedBar]:
        due: list[CompletedBar] = []
        for minutes in TF_PRIORITY:
            b = self.current[minutes]
            if b is not None and b.block == block:
                if b.known_at < BLOCK_END[block]:
                    due.append(b.complete())
                self.current[minutes] = None
        due.sort(key=lambda x: (x.known_at, TF_PRIORITY[x.minutes]))
        return due


class EMA:
    def __init__(self, span: int) -> None:
        self.alpha = 2.0 / (span + 1.0)
        self.value: Optional[float] = None
        self.count = 0

    def update(self, x: float) -> float:
        if self.value is None:
            self.value = x
        else:
            self.value = self.alpha * x + (1.0 - self.alpha) * self.value
        self.count += 1
        return self.value


@dataclass
class H4State:
    block: str
    start: datetime
    known_at: datetime
    price_revealed_cutoff: datetime
    state_A: str
    state_B: str
    state_C: str
    role_state_majority: str
    role_agree_n: int
    macro_state_majority: str
    macro_agree_n: int
    flow_state: str
    open: float
    high: float
    low: float
    close: float


@dataclass
class LTFState:
    block: str
    timeframe: str
    start: datetime
    known_at: datetime
    price_revealed_cutoff: datetime
    state_ema20: str
    state_net_mid: str
    state_ema_stack: str
    consensus: str
    agree_n: int
    open: float
    high: float
    low: float
    close: float


class H4Calculator:
    def __init__(self) -> None:
        self.block: Optional[str] = None
        self.count = 0
        self.ema20 = EMA(20)
        self.ema50 = EMA(50)
        self.closes: Deque[float] = deque(maxlen=21)
        self.highs: Deque[float] = deque(maxlen=20)
        self.lows: Deque[float] = deque(maxlen=20)
        self.e20: Deque[float] = deque(maxlen=5)
        self.e50: Deque[float] = deque(maxlen=6)

    def reset(self, block: str) -> None:
        self.__init__()
        self.block = block

    def update(self, b: CompletedBar) -> H4State:
        if self.block != b.block:
            self.reset(b.block)
        self.count += 1
        e20 = self.ema20.update(b.close)
        e50 = self.ema50.update(b.close)
        self.closes.append(b.close); self.highs.append(b.high); self.lows.append(b.low)
        self.e20.append(e20); self.e50.append(e50)

        e20_lag3 = self.e20[-4] if len(self.e20) >= 4 else math.nan
        e50_lag4 = self.e50[-5] if len(self.e50) >= 5 else math.nan
        c8 = self.closes[-9] if len(self.closes) >= 9 else math.nan
        c20 = self.closes[-21] if len(self.closes) >= 21 else math.nan
        c6 = self.closes[-7] if len(self.closes) >= 7 else math.nan
        hi8 = max(list(self.highs)[-8:]) if len(self.highs) >= 8 else math.nan
        lo8 = min(list(self.lows)[-8:]) if len(self.lows) >= 8 else math.nan
        hi20 = max(self.highs) if len(self.highs) >= 20 else math.nan
        lo20 = min(self.lows) if len(self.lows) >= 20 else math.nan
        hi6 = max(list(self.highs)[-6:]) if len(self.highs) >= 6 else math.nan
        lo6 = min(list(self.lows)[-6:]) if len(self.lows) >= 6 else math.nan

        slow_a1 = "UP" if b.close > e20 and e20 > e20_lag3 else ("DOWN" if b.close < e20 and e20 < e20_lag3 else "BAL")
        slow_a2 = "UP" if b.close > e20 and e20 > e50 else ("DOWN" if b.close < e20 and e20 < e50 else "BAL")
        slow_a = combine_slow(slow_a1, slow_a2)
        mid8 = (hi8 + lo8) / 2.0
        fast_a = "UP" if b.close > c8 and b.close > mid8 else ("DOWN" if b.close < c8 and b.close < mid8 else "BAL")
        state_a = role_state(slow_a, fast_a)

        mid20 = (hi20 + lo20) / 2.0
        slow_b = "UP" if b.close > c20 and b.close > mid20 else ("DOWN" if b.close < c20 and b.close < mid20 else "BAL")
        mid6 = (hi6 + lo6) / 2.0
        fast_b = "UP" if b.close > c6 and b.close > mid6 else ("DOWN" if b.close < c6 and b.close < mid6 else "BAL")
        state_b = role_state(slow_b, fast_b)

        slow_c = "UP" if b.close > e50 and e50 > e50_lag4 else ("DOWN" if b.close < e50 and e50 < e50_lag4 else "BAL")
        state_c = role_state(slow_c, slow_a1)

        if self.count <= 56:
            state_a = state_b = state_c = "WARMUP"
        states = [state_a, state_b, state_c]
        role_major = majority3(states)
        sides = [state_side(x) for x in states]
        macro = majority3(sides)
        flow = role_major
        if role_major == "AMBIGUOUS" and macro in ("UP", "DOWN"):
            flow = "UNRESOLVED_" + macro
        return H4State(
            block=b.block, start=b.start, known_at=b.known_at,
            price_revealed_cutoff=b.price_revealed_cutoff,
            state_A=state_a, state_B=state_b, state_C=state_c,
            role_state_majority=role_major, role_agree_n=agree_n(states),
            macro_state_majority=macro, macro_agree_n=agree_n(sides), flow_state=flow,
            open=b.open, high=b.high, low=b.low, close=b.close,
        )


class LTFCalculator:
    def __init__(self, timeframe: str, warmup: int = 50) -> None:
        self.timeframe = timeframe
        self.warmup = warmup
        self.block: Optional[str] = None
        self.count = 0
        self.ema20 = EMA(20)
        self.ema50 = EMA(50)
        self.closes: Deque[float] = deque(maxlen=9)
        self.highs: Deque[float] = deque(maxlen=8)
        self.lows: Deque[float] = deque(maxlen=8)
        self.e20: Deque[float] = deque(maxlen=4)

    def reset(self, block: str) -> None:
        tf, w = self.timeframe, self.warmup
        self.__init__(tf, w)
        self.block = block

    def update(self, b: CompletedBar) -> LTFState:
        if self.block != b.block:
            self.reset(b.block)
        self.count += 1
        e20 = self.ema20.update(b.close)
        e50 = self.ema50.update(b.close)
        self.closes.append(b.close); self.highs.append(b.high); self.lows.append(b.low); self.e20.append(e20)
        e20_lag3 = self.e20[-4] if len(self.e20) >= 4 else math.nan
        c8 = self.closes[-9] if len(self.closes) >= 9 else math.nan
        hi8 = max(self.highs) if len(self.highs) >= 8 else math.nan
        lo8 = min(self.lows) if len(self.lows) >= 8 else math.nan
        mid8 = (hi8 + lo8) / 2.0
        s1 = "UP" if b.close > e20 and e20 > e20_lag3 else ("DOWN" if b.close < e20 and e20 < e20_lag3 else "BALANCE")
        s2 = "UP" if b.close > c8 and b.close > mid8 else ("DOWN" if b.close < c8 and b.close < mid8 else "BALANCE")
        s3 = "UP" if b.close > e20 and e20 > e50 else ("DOWN" if b.close < e20 and e20 < e50 else "BALANCE")
        if self.count <= self.warmup:
            s1 = s2 = s3 = "WARMUP"
        states = [s1, s2, s3]
        return LTFState(
            block=b.block, timeframe=self.timeframe, start=b.start, known_at=b.known_at,
            price_revealed_cutoff=b.price_revealed_cutoff,
            state_ema20=s1, state_net_mid=s2, state_ema_stack=s3,
            consensus=majority3(states), agree_n=agree_n(states),
            open=b.open, high=b.high, low=b.low, close=b.close,
        )


@dataclass
class SemanticEvent:
    sequence: int
    kind: str
    known_at: datetime
    price_revealed_cutoff: Optional[datetime]
    block: str
    parent_id: Optional[str] = None
    parent_side: Optional[str] = None
    h1_cycle_id: Optional[str] = None
    relation: Optional[str] = None
    prior_relation: Optional[str] = None
    anchor_price: Optional[float] = None
    payload: dict = field(default_factory=dict)

    def row(self) -> dict:
        d = asdict(self)
        d["known_at"] = fmt(self.known_at)
        d["price_revealed_cutoff"] = fmt(self.price_revealed_cutoff)
        d["payload"] = json.dumps(self.payload, sort_keys=True, separators=(",", ":"))
        return d


@dataclass
class Parent:
    parent_id: str
    block: str
    side: str
    start: datetime


@dataclass
class H1Cycle:
    cycle_id: str
    block: str
    side: str
    start: datetime
    parent_id: Optional[str]


class MarketMachine:
    def __init__(self, observer=None) -> None:
        self.observer = observer
        self.h4_calc = H4Calculator()
        self.h1_calc = LTFCalculator("H1")
        self.m15_calc = LTFCalculator("M15")
        self.m5_calc = LTFCalculator("M5")
        self.latest_h4: Optional[H4State] = None
        self.latest_h1: Optional[LTFState] = None
        self.latest_m15: Optional[LTFState] = None
        self.latest_m5: Optional[LTFState] = None
        self.parent: Optional[Parent] = None
        self.parent_counter = {"2025H1": 0, "2026JF": 0}
        self.cycle_counter = {"2025H1": 0, "2026JF": 0}
        self.active_cycle: Optional[H1Cycle] = None
        self.h1_run_side: Optional[str] = None
        self.h1_run_relation: Optional[str] = None
        self.h1_run_last_at: Optional[datetime] = None
        self.current_h1_relation: Optional[str] = None
        self.current_m15_relation: Optional[str] = None
        self.m15_parent_id: Optional[str] = None
        self.seq = 0
        self.events: list[SemanticEvent] = []
        self.h4_states: list[H4State] = []
        self.h1_states: list[dict] = []
        self.m15_states: list[LTFState] = []
        self.m5_states: list[LTFState] = []
        self.cycles: list[dict] = []
        self.parents: list[dict] = []
        self.price_revealed_cutoff: Optional[datetime] = None
        self.information_known_at: Optional[datetime] = None
        self.last_price: Optional[M1Row] = None

    def emit(self, kind: str, known_at: datetime, cutoff: Optional[datetime], block: str, **kw) -> SemanticEvent:
        self.seq += 1
        ev = SemanticEvent(self.seq, kind, known_at, cutoff, block, **kw)
        self.events.append(ev)
        if self.observer is not None and hasattr(self.observer, "on_semantic_event"):
            self.observer.on_semantic_event(ev, self)
        return ev

    @staticmethod
    def relation(consensus: str, side: Optional[str]) -> str:
        if side not in ("UP", "DOWN"):
            return "NO_PARENT"
        if consensus == side:
            return "ALIGNED"
        if consensus in ("UP", "DOWN"):
            return "COUNTERFLOW"
        if consensus == "BALANCE":
            return "LOCAL_BALANCE"
        if consensus == "WARMUP":
            return "WARMUP"
        return "UNRESOLVED"

    def process_bar(self, b: CompletedBar) -> None:
        if self.information_known_at is not None and b.known_at < self.information_known_at:
            raise RuntimeErrorV9("semantic time moved backward")
        self.information_known_at = b.known_at
        # Price cutoff is the last actual M1 used to construct this bar, not logical time.
        if self.price_revealed_cutoff is None or b.price_revealed_cutoff > self.price_revealed_cutoff:
            self.price_revealed_cutoff = b.price_revealed_cutoff
        if b.minutes == 240:
            self._process_h4(b)
        elif b.minutes == 60:
            self._process_h1(b)
        elif b.minutes == 15:
            self._process_m15(b)
        elif b.minutes == 5:
            self._process_m5(b)
        else:
            raise RuntimeErrorV9(f"unsupported timeframe {b.minutes}")
        if self.observer is not None and hasattr(self.observer, "on_completed_bar"):
            self.observer.on_completed_bar(b, self)

    def _process_h4(self, b: CompletedBar) -> None:
        st = self.h4_calc.update(b); self.latest_h4 = st; self.h4_states.append(st)
        if st.flow_state == "WARMUP":
            return
        macro = st.macro_state_majority
        mig = st.flow_state.split("_", 1)[1] if st.flow_state.startswith("MIG_") else None
        if self.parent is not None and macro != self.parent.side:
            old = self.parent
            self.emit("PARENT_AUTHORITY_LOST", b.known_at, b.price_revealed_cutoff, b.block,
                      parent_id=old.parent_id, parent_side=old.side,
                      payload={"new_macro": macro, "flow_state": st.flow_state})
            self.parents.append({"parent_id": old.parent_id, "block": old.block, "side": old.side,
                                 "start": old.start, "end": b.known_at, "end_macro": macro})
            self.parent = None
            # H1 cycle resolution by side change is detected at H1 state time in the Atlas.
        if self.parent is None and mig in ("UP", "DOWN"):
            self.parent_counter[b.block] += 1
            pid = f"{b.block}-MP{self.parent_counter[b.block]:03d}"
            self.parent = Parent(pid, b.block, mig, b.known_at)
            self.emit("PARENT_EARNED", b.known_at, b.price_revealed_cutoff, b.block,
                      parent_id=pid, parent_side=mig,
                      payload={"flow_state": st.flow_state, "macro_agree_n": st.macro_agree_n})
            # Parent-side relation of the latest M15 is re-evaluated on next M15 completion;
            # do not synthesize a M15 transition at Parent creation.
            self.current_m15_relation = None
            self.m15_parent_id = pid

    def _h1_relation(self, st: LTFState) -> tuple[Optional[str], str]:
        macro = self.latest_h4.macro_state_majority if self.latest_h4 is not None else None
        if macro not in ("UP", "DOWN"):
            return macro, "H4_NON_DIRECTIONAL"
        if st.consensus == macro:
            return macro, "ALIGNED"
        if st.consensus in ("UP", "DOWN"):
            return macro, "COUNTERFLOW"
        return macro, "LOCAL_BALANCE"

    def _process_h1(self, b: CompletedBar) -> None:
        st = self.h1_calc.update(b); self.latest_h1 = st
        side, rel = self._h1_relation(st)
        self.h1_states.append({**asdict(st), "macro_state_majority": side, "h1_vs_h4_relation": rel})
        if side not in ("UP", "DOWN") or st.consensus == "WARMUP":
            # Offline build_cycles drops these rows.  Break run continuity.
            self.h1_run_side = side
            self.h1_run_relation = rel
            self.h1_run_last_at = b.known_at
            self.current_h1_relation = rel
            return

        gap = None if self.h1_run_last_at is None else b.known_at - self.h1_run_last_at
        new_run = (
            self.h1_run_last_at is None or
            side != self.h1_run_side or
            rel != self.h1_run_relation or
            (gap is not None and gap > timedelta(hours=2))
        )
        if new_run:
            prev_side, prev_rel = self.h1_run_side, self.h1_run_relation
            self.emit("H1_RUN_STARTED", b.known_at, b.price_revealed_cutoff, b.block,
                      parent_id=self.parent.parent_id if self.parent and self.parent.side == side else None,
                      parent_side=side, relation=rel, prior_relation=prev_rel,
                      payload={"h1_consensus": st.consensus})
            # Resolve an existing cycle at the first run that realigns or changes side.
            if self.active_cycle is not None:
                c = self.active_cycle
                if side != c.side:
                    self.cycles.append({"h1_cycle_id": c.cycle_id, "block": c.block, "h4_side": c.side,
                                        "start": c.start, "resolution": b.known_at, "outcome": "H4_SIDE_CHANGED",
                                        "parent_id": c.parent_id})
                    self.emit("H1_CYCLE_RESOLVED_SIDE_CHANGE", b.known_at, b.price_revealed_cutoff, b.block,
                              parent_id=c.parent_id, parent_side=c.side, h1_cycle_id=c.cycle_id)
                    self.active_cycle = None
                elif rel == "ALIGNED":
                    self.cycles.append({"h1_cycle_id": c.cycle_id, "block": c.block, "h4_side": c.side,
                                        "start": c.start, "resolution": b.known_at, "outcome": "H1_REALIGN",
                                        "parent_id": c.parent_id})
                    # Only the same active Parent gets strategy H1_REALIGN authority.
                    same_parent = self.parent is not None and self.parent.parent_id == c.parent_id and self.parent.side == c.side
                    self.emit("H1_REALIGN" if same_parent else "H1_CYCLE_REALIGN_RESET_GAP",
                              b.known_at, b.price_revealed_cutoff, b.block,
                              parent_id=c.parent_id, parent_side=c.side, h1_cycle_id=c.cycle_id,
                              anchor_price=(b.low if c.side == "UP" else b.high) if same_parent else None,
                              payload={"h1_close": b.close})
                    self.active_cycle = None
            # Start a new cycle from ALIGNED run -> interrupt run, matching Atlas run grammar.
            if self.active_cycle is None and prev_rel == "ALIGNED" and prev_side == side and rel in ("COUNTERFLOW", "LOCAL_BALANCE"):
                self.cycle_counter[b.block] += 1
                cid = f"{b.block}-H1C{self.cycle_counter[b.block]:03d}"
                pid = self.parent.parent_id if self.parent is not None and self.parent.side == side else None
                self.active_cycle = H1Cycle(cid, b.block, side, b.known_at, pid)
                self.emit("H1_INTERRUPT_START", b.known_at, b.price_revealed_cutoff, b.block,
                          parent_id=pid, parent_side=side, h1_cycle_id=cid,
                          anchor_price=b.high if side == "UP" else b.low,
                          payload={"relation": rel, "h1_close": b.close})

            self.h1_run_side = side; self.h1_run_relation = rel
        self.h1_run_last_at = b.known_at
        old = self.current_h1_relation
        self.current_h1_relation = rel
        if old != rel:
            self.emit("H1_RELATION_CHANGED", b.known_at, b.price_revealed_cutoff, b.block,
                      parent_id=self.parent.parent_id if self.parent else None,
                      parent_side=self.parent.side if self.parent else None,
                      relation=rel, prior_relation=old,
                      payload={"macro_side": side, "h1_consensus": st.consensus})

    def _process_m15(self, b: CompletedBar) -> None:
        st = self.m15_calc.update(b); self.latest_m15 = st; self.m15_states.append(st)
        pid = self.parent.parent_id if self.parent else None
        side = self.parent.side if self.parent else None
        rel = self.relation(st.consensus, side)
        # Parent change creates a new relation context.  First observed M15 state is a snapshot,
        # not a synthetic fresh transition.
        if pid != self.m15_parent_id:
            self.m15_parent_id = pid
            self.current_m15_relation = rel
            self.emit("M15_RELATION_SNAPSHOT", b.known_at, b.price_revealed_cutoff, b.block,
                      parent_id=pid, parent_side=side, relation=rel,
                      payload={"m15_consensus": st.consensus})
            return
        old = self.current_m15_relation
        self.current_m15_relation = rel
        if old != rel:
            self.emit("M15_RELATION_CHANGED", b.known_at, b.price_revealed_cutoff, b.block,
                      parent_id=pid, parent_side=side, relation=rel, prior_relation=old,
                      payload={"m15_consensus": st.consensus, "h1_relation": self.current_h1_relation})

    def _process_m5(self, b: CompletedBar) -> None:
        st = self.m5_calc.update(b); self.latest_m5 = st; self.m5_states.append(st)

    def process_price(self, row: M1Row, block: str) -> None:
        if self.price_revealed_cutoff is not None and row.ts <= self.price_revealed_cutoff:
            raise RuntimeErrorV9("price chronology moved backward")
        self.price_revealed_cutoff = row.ts
        if self.information_known_at is None or self.information_known_at < row.ts:
            self.information_known_at = row.ts
        self.last_price = row
        if self.observer is not None and hasattr(self.observer, "on_price"):
            self.observer.on_price(row, block, self)

    def finish_block(self, block: str) -> None:
        # Block-end Parent is censored rather than authority-loss event.
        if self.parent is not None and self.parent.block == block:
            p = self.parent
            self.parents.append({"parent_id": p.parent_id, "block": p.block, "side": p.side,
                                 "start": p.start, "end": BLOCK_END[block], "end_macro": "BLOCK_END"})
            self.parent = None
        self.active_cycle = None
        self.h1_run_side = self.h1_run_relation = None
        self.h1_run_last_at = None
        self.current_h1_relation = None
        self.current_m15_relation = None
        self.m15_parent_id = None
        self.latest_h4 = None
        self.latest_h1 = None
        self.latest_m15 = None
        self.latest_m5 = None
        if self.observer is not None and hasattr(self.observer, "on_block_end"):
            self.observer.on_block_end(block, self)


class RawM1Feed:
    def __init__(self, source: Path, expected_sha: str = AUTHORITATIVE_SHA256) -> None:
        self.source = source
        actual = sha256_file(source)
        if actual.lower() != expected_sha.lower():
            raise RuntimeErrorV9(f"source SHA mismatch expected={expected_sha} actual={actual}")
        self.expected_sha = expected_sha

    @staticmethod
    def _process_due(machine: MarketMachine, due: list[CompletedBar]) -> None:
        """Process completed bars in known-at batches, then expose one strategy barrier.

        Internal timeframe priority is deterministic calculation order only.  Strategy /
        order logic must not act on a partial set of facts that share the same
        INFORMATION_KNOWN_AT.
        """
        i = 0
        while i < len(due):
            known = due[i].known_at
            j = i
            while j < len(due) and due[j].known_at == known:
                machine.process_bar(due[j])
                j += 1
            if machine.observer is not None and hasattr(machine.observer, "on_information_batch_complete"):
                machine.observer.on_information_batch_complete(known, machine)
            i = j

    def replay(self, machine: MarketMachine) -> None:
        buckets = BucketSet()
        active_block: Optional[str] = None
        with self.source.open("rb") as f:
            header = f.readline().decode("utf-8-sig").rstrip("\r\n").split("\t")
            if header != EXPECTED_HEADER:
                raise RuntimeErrorV9(f"unexpected M1 header {header!r}")
            idx = {v: i for i, v in enumerate(header)}
            last_ts: Optional[datetime] = None
            for raw in f:
                # Timestamp-only parse first.  No OHLC conversion before due semantic events.
                head = raw.split(b"\t", 2)
                if len(head) < 3:
                    raise RuntimeErrorV9("malformed M1 row")
                ds = head[0].decode("ascii"); ts_s = head[1].decode("ascii")
                ts = fast_ts(ds, ts_s)
                if last_ts is not None and ts <= last_ts:
                    raise RuntimeErrorV9("source is not strictly chronological")
                last_ts = ts
                block = block_for_ts(ts)
                # Leaving a consumed block: next timestamp proves due prior buckets complete.
                if active_block is not None and block != active_block:
                    self._process_due(machine, buckets.due_before_row(ts, block))
                    # Any remaining bucket with known_at before strict block end is also proven complete
                    # by this later timestamp; bars known exactly at the boundary remain excluded.
                    self._process_due(machine, buckets.flush_block(active_block))
                    machine.finish_block(active_block)
                    active_block = None
                if block is None:
                    continue
                if active_block is None:
                    active_block = block
                # Complete prior buckets before current OHLC is exposed.
                self._process_due(machine, buckets.due_before_row(ts, block))
                # Only now parse current OHLC.
                p = raw.decode("ascii").rstrip("\r\n").split("\t")
                row = M1Row(ts, float(p[idx["<OPEN>"]]), float(p[idx["<HIGH>"]]),
                            float(p[idx["<LOW>"]]), float(p[idx["<CLOSE>"]]))
                machine.process_price(row, block)
                buckets.add_row(block, row)
            if active_block is not None:
                self._process_due(machine, buckets.flush_block(active_block))
                machine.finish_block(active_block)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader(); w.writerows(rows)


def state_to_row(x) -> dict:
    d = asdict(x)
    for k, v in list(d.items()):
        if isinstance(v, datetime):
            d[k] = fmt(v)
    return d


def replay_consumed(source: Path, out_dir: Path) -> dict:
    m = MarketMachine(); RawM1Feed(source).replay(m)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "semantic_events.csv", [e.row() for e in m.events])
    write_csv(out_dir / "h4_states.csv", [state_to_row(x) for x in m.h4_states])
    # h1 state dict contains datetimes nested directly.
    h1rows=[]
    for d in m.h1_states:
        z={}
        for k,v in d.items(): z[k]=fmt(v) if isinstance(v,datetime) else v
        h1rows.append(z)
    write_csv(out_dir / "h1_states.csv", h1rows)
    write_csv(out_dir / "m15_states.csv", [state_to_row(x) for x in m.m15_states])
    write_csv(out_dir / "m5_states.csv", [state_to_row(x) for x in m.m5_states])
    cyc=[]
    for d in m.cycles:
        z={k:(fmt(v) if isinstance(v,datetime) else v) for k,v in d.items()};cyc.append(z)
    write_csv(out_dir / "h1_cycles.csv", cyc)
    par=[]
    for d in m.parents:
        z={k:(fmt(v) if isinstance(v,datetime) else v) for k,v in d.items()};par.append(z)
    write_csv(out_dir / "parents.csv", par)
    summary={
        "runtime_version":RUNTIME_VERSION,
        "event_plan_version":EVENT_PLAN_VERSION,
        "source_sha256":AUTHORITATIVE_SHA256,
        "h4_states":len(m.h4_states), "h1_states":len(m.h1_states),
        "m15_states":len(m.m15_states), "m5_states":len(m.m5_states),
        "h1_cycles":len(m.cycles), "parents":len(m.parents),
        "events":len(m.events),
        "event_counts":{},
        "future_hidden_2025_07":"LOCKED / OHLC not parsed",
    }
    for e in m.events: summary["event_counts"][e.kind]=summary["event_counts"].get(e.kind,0)+1
    (out_dir/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return summary


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--out-dir",type=Path,required=True)
    a=p.parse_args(argv)
    try:
        print(json.dumps(replay_consumed(a.source,a.out_dir),indent=2,sort_keys=True))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__=="__main__":
    raise SystemExit(main())
