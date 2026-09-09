#!/usr/bin/env python3
"""V9 causal numeric replay helper.

Purpose
-------
Provide a deterministic, prefix-only market-data layer for V9 discretionary replay.
This helper DOES NOT generate trade signals. It standardizes:
- authoritative M1 hash verification
- monotonic causal reveal
- completed M15/H1/H4 aggregation
- H1 EMA9 / Stochastic(14,3,3) shadow outputs
- previous completed H4 Wilder ATR14 (S)
- guarded Hard-SL / Local-Bridge destination chronology

The source file is expected to be tab-separated with MT5-style columns:
<DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> <TICKVOL> <VOL> <SPREAD>

Important causal design
-----------------------
The helper does not preload the full future price file. It streams source rows and
stops at the requested cutoff. When deciding whether the next source row is beyond
that cutoff, it reads the DATE/TIME prefix first; future OHLC bytes are not parsed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

EXPECTED_SHA256 = "626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2"
TS_FMT = "%Y-%m-%d %H:%M"
SOURCE_TS_FMT = "%Y.%m.%d %H:%M:%S"
HEADER = ["<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>", "<TICKVOL>", "<VOL>", "<SPREAD>"]


def parse_ts(text: str) -> datetime:
    text = text.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y.%m.%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError(f"Unsupported timestamp: {text}")


def fmt_ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


@dataclass
class State:
    version: int
    source_path: str
    source_sha256: str
    cache_path: str
    cache_start: str
    revealed_cutoff: str
    source_byte_offset: int
    contaminated_intervals: List[Dict[str, str]]

    @property
    def cutoff_dt(self) -> datetime:
        return parse_ts(self.revealed_cutoff)


def load_state(path: Path) -> State:
    data = json.loads(path.read_text(encoding="utf-8"))
    return State(**data)


def save_state(path: Path, state: State) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(asdict(state), indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def _read_field_until_tab(f) -> bytes:
    out = bytearray()
    while True:
        b = f.read(1)
        if not b:
            return bytes(out)
        if b == b"\t":
            return bytes(out)
        if b in (b"\r", b"\n"):
            raise ValueError("Unexpected line ending before tab")
        out.extend(b)


def _peek_row_timestamp_and_remainder(f) -> Tuple[Optional[datetime], Optional[bytes], int]:
    """Read DATE/TIME first. Return (timestamp, full_row_if_consumed_prefix, row_start).

    The returned bytes contain only DATE and TIME plus their tabs. Caller decides
    whether to read the rest of the row. If EOF, timestamp is None.
    """
    row_start = f.tell()
    first = f.read(1)
    if not first:
        return None, None, row_start
    f.seek(row_start)
    date_b = _read_field_until_tab(f)
    if not date_b:
        return None, None, row_start
    time_b = _read_field_until_tab(f)
    ts = datetime.strptime(f"{date_b.decode('ascii')} {time_b.decode('ascii')}", SOURCE_TS_FMT)
    prefix = date_b + b"\t" + time_b + b"\t"
    return ts, prefix, row_start


def _read_remainder_line(f) -> bytes:
    return f.readline()


def _ensure_source_and_hash(source: Path, expected_hash: str) -> str:
    if not source.exists():
        raise FileNotFoundError(source)
    actual = sha256_file(source)
    if actual != expected_hash:
        raise RuntimeError(f"FAIL CLOSED: SHA256 mismatch\nexpected={expected_hash}\nactual={actual}")
    return actual


def init_state(source: Path, state_path: Path, cutoff: datetime, cache_start: datetime, expected_hash: str) -> None:
    actual_hash = _ensure_source_and_hash(source, expected_hash)
    cache_path = state_path.with_suffix(".revealed.tsv")
    if cache_path.exists():
        cache_path.unlink()

    last_revealed: Optional[datetime] = None
    next_offset = 0

    with source.open("rb") as src, cache_path.open("wb") as cache:
        header = src.readline()
        if not header:
            raise RuntimeError("Empty source file")
        cache.write(header)

        while True:
            ts, prefix, row_start = _peek_row_timestamp_and_remainder(src)
            if ts is None:
                next_offset = src.tell()
                break
            if ts > cutoff:
                src.seek(row_start)
                next_offset = row_start
                break
            remainder = _read_remainder_line(src)
            if ts >= cache_start:
                cache.write(prefix + remainder)
            last_revealed = ts
            next_offset = src.tell()

    if last_revealed is None or last_revealed < cutoff:
        # It is valid for the requested cutoff to fall inside a market-closed gap.
        # revealed_cutoff is the actual latest source row exposed, not an invented minute.
        effective = last_revealed
    else:
        effective = cutoff
    if effective is None:
        raise RuntimeError("No source rows exist at or before requested cutoff")

    state = State(
        version=1,
        source_path=str(source.resolve()),
        source_sha256=actual_hash,
        cache_path=str(cache_path.resolve()),
        cache_start=fmt_ts(cache_start),
        revealed_cutoff=fmt_ts(effective),
        source_byte_offset=next_offset,
        contaminated_intervals=[],
    )
    save_state(state_path, state)
    print(f"initialized cutoff={state.revealed_cutoff} offset={state.source_byte_offset}")


def _event_for_row(side: Optional[str], sl: Optional[float], destination: Optional[float], low: float, high: float) -> Optional[str]:
    if not side:
        return None
    side = side.lower()
    if side not in ("long", "short"):
        raise ValueError("side must be long or short")
    stop_hit = False
    dest_hit = False
    if sl is not None:
        stop_hit = low <= sl if side == "long" else high >= sl
    if destination is not None:
        dest_hit = high >= destination if side == "long" else low <= destination
    if stop_hit and dest_hit:
        return "INTRAMINUTE_EXECUTION_AMBIGUOUS"
    if stop_hit:
        return "HARD_SL"
    if dest_hit:
        return "DESTINATION"
    return None


def advance_state(
    state_path: Path,
    target: datetime,
    side: Optional[str] = None,
    sl: Optional[float] = None,
    destination: Optional[float] = None,
) -> None:
    state = load_state(state_path)
    source = Path(state.source_path)
    cache_path = Path(state.cache_path)
    if sha256_file(source) != state.source_sha256:
        raise RuntimeError("FAIL CLOSED: source hash changed since state initialization")
    if target < state.cutoff_dt:
        raise RuntimeError(f"FAIL CLOSED: cannot move cutoff backward ({target} < {state.cutoff_dt})")

    event = None
    event_ts = None
    event_low = event_high = None
    last_revealed = state.cutoff_dt
    next_offset = state.source_byte_offset

    with source.open("rb") as src, cache_path.open("ab") as cache:
        src.seek(state.source_byte_offset)
        while True:
            ts, prefix, row_start = _peek_row_timestamp_and_remainder(src)
            if ts is None:
                next_offset = src.tell()
                break
            if ts > target:
                src.seek(row_start)
                next_offset = row_start
                break
            remainder = _read_remainder_line(src)
            full = prefix + remainder
            cache.write(full)
            last_revealed = ts
            next_offset = src.tell()

            if side and (sl is not None or destination is not None):
                parts = full.decode("utf-8").rstrip("\r\n").split("\t")
                low = float(parts[4])
                high = float(parts[3])
                event = _event_for_row(side, sl, destination, low, high)
                if event:
                    event_ts = ts
                    event_low, event_high = low, high
                    break

    state.revealed_cutoff = fmt_ts(last_revealed)
    state.source_byte_offset = next_offset
    save_state(state_path, state)

    if event:
        print(json.dumps({
            "event": event,
            "timestamp": fmt_ts(event_ts),
            "low": event_low,
            "high": event_high,
            "cutoff": state.revealed_cutoff,
        }, ensure_ascii=False))
    else:
        print(json.dumps({"event": None, "cutoff": state.revealed_cutoff}, ensure_ascii=False))


def read_cache(path: Path) -> List[Dict[str, float]]:
    rows: List[Dict[str, float]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for x in r:
            ts = datetime.strptime(f"{x['<DATE>']} {x['<TIME>']}", SOURCE_TS_FMT)
            rows.append({
                "ts": ts,
                "open": float(x["<OPEN>"]),
                "high": float(x["<HIGH>"]),
                "low": float(x["<LOW>"]),
                "close": float(x["<CLOSE>"]),
            })
    return rows


def floor_bucket(ts: datetime, minutes: int) -> datetime:
    if minutes == 240:
        h = (ts.hour // 4) * 4
        return ts.replace(hour=h, minute=0, second=0, microsecond=0)
    total = ts.hour * 60 + ts.minute
    floored = (total // minutes) * minutes
    return ts.replace(hour=floored // 60, minute=floored % 60, second=0, microsecond=0)


def aggregate(rows: List[Dict[str, float]], minutes: int, cutoff: datetime) -> List[Dict[str, float]]:
    buckets: Dict[datetime, Dict[str, float]] = {}
    for r in rows:
        b = floor_bucket(r["ts"], minutes)
        if b not in buckets:
            buckets[b] = {"ts": b, "open": r["open"], "high": r["high"], "low": r["low"], "close": r["close"], "last_ts": r["ts"]}
        else:
            q = buckets[b]
            q["high"] = max(q["high"], r["high"])
            q["low"] = min(q["low"], r["low"])
            q["close"] = r["close"]
            q["last_ts"] = r["ts"]

    out = []
    for b in sorted(buckets):
        end = b + timedelta(minutes=minutes) - timedelta(minutes=1)
        # Only a clock-completed bucket gets ordinary HTF authority.
        if cutoff >= end:
            out.append(buckets[b])
    return out


def ema(values: List[float], span: int) -> List[Optional[float]]:
    if not values:
        return []
    alpha = 2.0 / (span + 1.0)
    out: List[Optional[float]] = []
    prev = None
    for v in values:
        prev = v if prev is None else alpha * v + (1 - alpha) * prev
        out.append(prev)
    return out


def sma(values: List[Optional[float]], n: int) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    for i in range(len(values)):
        window = values[max(0, i - n + 1): i + 1]
        if len(window) < n or any(v is None for v in window):
            out.append(None)
        else:
            out.append(sum(float(v) for v in window) / n)
    return out


def stochastic_1433(h1: List[Dict[str, float]]) -> Tuple[List[Optional[float]], List[Optional[float]]]:
    raw: List[Optional[float]] = []
    for i, b in enumerate(h1):
        if i < 13:
            raw.append(None)
            continue
        w = h1[i - 13:i + 1]
        hh = max(x["high"] for x in w)
        ll = min(x["low"] for x in w)
        if hh == ll:
            raw.append(None)
        else:
            raw.append(100.0 * (b["close"] - ll) / (hh - ll))
    k = sma(raw, 3)
    d = sma(k, 3)
    return k, d


def wilder_atr(h4: List[Dict[str, float]], n: int = 14) -> List[Optional[float]]:
    tr: List[float] = []
    prev_close: Optional[float] = None
    for b in h4:
        if prev_close is None:
            x = b["high"] - b["low"]
        else:
            x = max(b["high"] - b["low"], abs(b["high"] - prev_close), abs(b["low"] - prev_close))
        tr.append(x)
        prev_close = b["close"]
    out: List[Optional[float]] = [None] * len(tr)
    if len(tr) < n:
        return out
    atr = sum(tr[:n]) / n
    out[n - 1] = atr
    for i in range(n, len(tr)):
        atr = (atr * (n - 1) + tr[i]) / n
        out[i] = atr
    return out


def row_to_text(b: Dict[str, float]) -> str:
    return f"{b['ts'].strftime('%Y-%m-%d %H:%M')} O={b['open']:.2f} H={b['high']:.2f} L={b['low']:.2f} C={b['close']:.2f}"


def snapshot(state_path: Path, mode: str, h4_n: int, h1_n: int, m15_n: int, m5_n: int, m1_n: int) -> None:
    state = load_state(state_path)
    cutoff = state.cutoff_dt
    rows = read_cache(Path(state.cache_path))
    h4 = aggregate(rows, 240, cutoff)
    h1 = aggregate(rows, 60, cutoff)
    m15 = aggregate(rows, 15, cutoff)
    m5 = aggregate(rows, 5, cutoff)

    ema9 = ema([b["close"] for b in h1], 9)
    sk, sd = stochastic_1433(h1)
    atr = wilder_atr(h4, 14)
    # S = previous fully completed H4 ATR relative to the latest completed H4 bar.
    s_val = atr[-2] if len(atr) >= 2 else None

    print(f"CUTOFF {state.revealed_cutoff}")
    print(f"MODE {mode}")
    print(f"SOURCE_SHA256 {state.source_sha256}")
    print("\nH4 COMPLETED")
    for b in h4[-h4_n:]:
        print(row_to_text(b))
    print("\nH1 COMPLETED")
    for b in h1[-h1_n:]:
        print(row_to_text(b))

    if h1:
        i = len(h1) - 1
        print("\nSHADOW")
        print(f"H1_EMA9={ema9[i]:.4f}" if ema9[i] is not None else "H1_EMA9=NA")
        print(f"H1_STOCH_K={sk[i]:.4f}" if sk[i] is not None else "H1_STOCH_K=NA")
        print(f"H1_STOCH_D={sd[i]:.4f}" if sd[i] is not None else "H1_STOCH_D=NA")
        print(f"S_PREV_COMPLETED_H4_ATR14={s_val:.4f}" if s_val is not None else "S_PREV_COMPLETED_H4_ATR14=NA")

    if mode in ("candidate", "warning", "local", "exact"):
        print("\nM15 COMPLETED")
        for b in m15[-m15_n:]:
            print(row_to_text(b))
    if mode in ("exact",):
        print("\nM5 COMPLETED")
        for b in m5[-m5_n:]:
            print(row_to_text(b))
        print("\nM1 REVEALED")
        for r in rows[-m1_n:]:
            print(row_to_text(r))


def contaminate(state_path: Path, start: datetime, end: datetime, reason: str) -> None:
    state = load_state(state_path)
    state.contaminated_intervals.append({"start": fmt_ts(start), "end": fmt_ts(end), "reason": reason})
    save_state(state_path, state)
    print("recorded contamination interval")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="V9 causal numeric replay helper")
    sub = p.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("init")
    q.add_argument("--source", required=True, type=Path)
    q.add_argument("--state", required=True, type=Path)
    q.add_argument("--cutoff", required=True, type=parse_ts)
    q.add_argument("--cache-start", default=parse_ts("2025-01-01 00:00"), type=parse_ts)
    q.add_argument("--expected-sha256", default=EXPECTED_SHA256)

    q = sub.add_parser("advance")
    q.add_argument("--state", required=True, type=Path)
    q.add_argument("--to", required=True, type=parse_ts)
    q.add_argument("--side", choices=["long", "short"])
    q.add_argument("--hard-sl", type=float)
    q.add_argument("--destination", type=float)

    q = sub.add_parser("snapshot")
    q.add_argument("--state", required=True, type=Path)
    q.add_argument("--mode", choices=["flat", "candidate", "parent", "warning", "local", "exact"], default="flat")
    q.add_argument("--h4-bars", type=int, default=20)
    q.add_argument("--h1-bars", type=int, default=24)
    q.add_argument("--m15-bars", type=int, default=16)
    q.add_argument("--m5-bars", type=int, default=12)
    q.add_argument("--m1-bars", type=int, default=30)

    q = sub.add_parser("contaminate")
    q.add_argument("--state", required=True, type=Path)
    q.add_argument("--start", required=True, type=parse_ts)
    q.add_argument("--end", required=True, type=parse_ts)
    q.add_argument("--reason", required=True)

    return p


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.cmd == "init":
            init_state(args.source, args.state, args.cutoff, args.cache_start, args.expected_sha256)
        elif args.cmd == "advance":
            advance_state(args.state, args.to, args.side, args.hard_sl, args.destination)
        elif args.cmd == "snapshot":
            snapshot(args.state, args.mode, args.h4_bars, args.h1_bars, args.m15_bars, args.m5_bars, args.m1_bars)
        elif args.cmd == "contaminate":
            contaminate(args.state, args.start, args.end, args.reason)
        else:
            raise RuntimeError("unknown command")
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
