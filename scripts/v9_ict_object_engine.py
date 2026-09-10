#!/usr/bin/env python3
"""Build exact ICT candidate objects from an already-revealed V9 M1 prefix.

The engine creates a reproducible candidate universe. It does NOT decide which
objects are strategically important. AI selects important objects from the
candidate ledger after reading the chart-native H1/H4 map.

Input must be an already-revealed prefix produced by v9_causal_m1.py. This tool
never opens the authoritative future source file.
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable
from bisect import bisect_right

HEADER = [
    "<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>",
    "<TICKVOL>", "<VOL>", "<SPREAD>",
]
TS_FMT = "%Y.%m.%d %H:%M:%S"
CLI_FMT = "%Y-%m-%d %H:%M:%S"
ENGINE_VERSION = "v9-ict-candidate-engine-1"


class ObjectEngineError(RuntimeError):
    pass


@dataclass(frozen=True)
class Bar:
    start: datetime
    minutes: int
    open: float
    high: float
    low: float
    close: float

    @property
    def end(self) -> datetime:
        return self.start + timedelta(minutes=self.minutes - 1)


@dataclass
class Obj:
    object_id: str
    timeframe: str
    family: str
    direction: str
    source_start: str
    source_mid: str | None
    source_end: str
    born_at: str
    price_low: float
    price_high: float
    body_low: float | None = None
    body_high: float | None = None
    mean_threshold: float | None = None
    break_reference_id: str | None = None
    break_bar: str | None = None
    first_touch_at: str | None = None
    full_fill_at: str | None = None
    first_mitigation_at: str | None = None
    distal_invalidation_at: str | None = None
    raid_at: str | None = None
    geometric_state: str = "ACTIVE"
    geometric_end_at: str | None = None


def cli_ts(value: str) -> datetime:
    try:
        return datetime.strptime(value, CLI_FMT)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timestamp must be YYYY-MM-DD HH:MM:SS") from exc


def fmt(ts: datetime | None) -> str | None:
    return ts.strftime(CLI_FMT) if ts else None


def bucket_start(ts: datetime, minutes: int) -> datetime:
    if minutes == 60:
        return ts.replace(minute=0, second=0, microsecond=0)
    if minutes == 240:
        return ts.replace(hour=(ts.hour // 4) * 4, minute=0, second=0, microsecond=0)
    raise ValueError(minutes)


def load_revealed_m1(path: Path) -> tuple[list[tuple[datetime, float, float, float, float]], datetime]:
    rows: list[tuple[datetime, float, float, float, float]] = []
    previous = None
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ObjectEngineError("revealed prefix is empty") from exc
        if header != HEADER:
            raise ObjectEngineError(f"unexpected revealed header: {header!r}")
        for row in reader:
            if len(row) != len(HEADER):
                raise ObjectEngineError("malformed revealed row")
            ts = datetime.strptime(row[0] + " " + row[1], TS_FMT)
            if previous is not None and ts <= previous:
                raise ObjectEngineError("revealed rows are not strictly chronological")
            previous = ts
            o, h, l, c = map(float, row[2:6])
            rows.append((ts, o, h, l, c))
    if not rows:
        raise ObjectEngineError("revealed prefix contains no M1 rows")
    return rows, rows[-1][0]


def aggregate(rows: Iterable[tuple[datetime, float, float, float, float]], minutes: int, cutoff: datetime) -> list[Bar]:
    bars: list[Bar] = []
    current: Bar | None = None
    for ts, o, h, l, c in rows:
        start = bucket_start(ts, minutes)
        if current is None or current.start != start:
            if current is not None:
                bars.append(current)
            current = Bar(start, minutes, o, h, l, c)
        else:
            current = Bar(
                current.start, minutes, current.open,
                max(current.high, h), min(current.low, l), c,
            )
    if current is not None:
        bars.append(current)
    # Normal object creation uses completed bars only.
    return [b for b in bars if b.end <= cutoff]


def pivot_candidates(bars: list[Bar], tf: str) -> list[Obj]:
    out: list[Obj] = []
    for i in range(2, len(bars) - 2):
        b = bars[i]
        left = bars[i-2:i]
        right = bars[i+1:i+3]
        born = right[-1].end
        if b.high > max(x.high for x in left) and b.high >= max(x.high for x in right):
            out.append(Obj(
                object_id=f"{tf}_SWING_HIGH_{b.start:%Y%m%d_%H%M}", timeframe=tf,
                family="SWING", direction="HIGH", source_start=fmt(b.start),
                source_mid=None, source_end=fmt(b.start), born_at=fmt(born),
                price_low=b.high, price_high=b.high,
            ))
        if b.low < min(x.low for x in left) and b.low <= min(x.low for x in right):
            out.append(Obj(
                object_id=f"{tf}_SWING_LOW_{b.start:%Y%m%d_%H%M}", timeframe=tf,
                family="SWING", direction="LOW", source_start=fmt(b.start),
                source_mid=None, source_end=fmt(b.start), born_at=fmt(born),
                price_low=b.low, price_high=b.low,
            ))
    return out


def m1_after(rows, times, after: datetime):
    return rows[bisect_right(times, after):]


def first_m1(rows, predicate):
    return next((r for r in rows if predicate(r)), None)


def fvg_candidates(bars: list[Bar], tf: str, cutoff: datetime, m1_rows, m1_times) -> list[Obj]:
    out: list[Obj] = []
    for i in range(2, len(bars)):
        a, b, c = bars[i-2], bars[i-1], bars[i]
        born = c.end
        later_m1 = m1_after(m1_rows, m1_times, born)
        if a.high < c.low:
            lo, hi = a.high, c.low
            touch = first_m1(later_m1, lambda x: x[3] <= hi and x[2] >= lo)
            full = first_m1(later_m1, lambda x: x[3] <= lo)
            end = full[0] if full else cutoff
            out.append(Obj(
                object_id=f"{tf}_FVG_BULL_{c.start:%Y%m%d_%H%M}", timeframe=tf,
                family="FVG", direction="BULL", source_start=fmt(a.start),
                source_mid=fmt(b.start), source_end=fmt(c.start), born_at=fmt(born),
                price_low=lo, price_high=hi, first_touch_at=fmt(touch[0] if touch else None),
                full_fill_at=fmt(full[0] if full else None),
                geometric_state="FULLY_FILLED" if full else ("TOUCHED" if touch else "ACTIVE"),
                geometric_end_at=fmt(end),
            ))
        if a.low > c.high:
            lo, hi = c.high, a.low
            touch = first_m1(later_m1, lambda x: x[3] <= hi and x[2] >= lo)
            full = first_m1(later_m1, lambda x: x[2] >= hi)
            end = full[0] if full else cutoff
            out.append(Obj(
                object_id=f"{tf}_FVG_BEAR_{c.start:%Y%m%d_%H%M}", timeframe=tf,
                family="FVG", direction="BEAR", source_start=fmt(a.start),
                source_mid=fmt(b.start), source_end=fmt(c.start), born_at=fmt(born),
                price_low=lo, price_high=hi, first_touch_at=fmt(touch[0] if touch else None),
                full_fill_at=fmt(full[0] if full else None),
                geometric_state="FULLY_FILLED" if full else ("TOUCHED" if touch else "ACTIVE"),
                geometric_end_at=fmt(end),
            ))
    return out


def liquidity_candidates(bars: list[Bar], swings: list[Obj], tf: str, cutoff: datetime, m1_rows, m1_times) -> list[Obj]:
    out: list[Obj] = []
    for s in swings:
        born = datetime.strptime(s.born_at, CLI_FMT)
        price = s.price_low
        later = m1_after(m1_rows, m1_times, born)
        if s.direction == "HIGH":
            raid = first_m1(later, lambda x: x[2] > price)
            direction = "BUY_SIDE"
        else:
            raid = first_m1(later, lambda x: x[3] < price)
            direction = "SELL_SIDE"
        end = raid[0] if raid else cutoff
        out.append(Obj(
            object_id=s.object_id.replace("SWING_HIGH", "BSL").replace("SWING_LOW", "SSL"),
            timeframe=tf, family="LIQUIDITY", direction=direction,
            source_start=s.source_start, source_mid=None, source_end=s.source_end,
            born_at=s.born_at, price_low=price, price_high=price,
            raid_at=fmt(raid[0] if raid else None),
            geometric_state="RAIDED" if raid else "ACTIVE", geometric_end_at=fmt(end),
        ))
    return out


def last_opposite_candle(bars: list[Bar], break_index: int, bullish_break: bool) -> Bar | None:
    for j in range(break_index - 1, -1, -1):
        b = bars[j]
        if bullish_break and b.close < b.open:
            return b
        if (not bullish_break) and b.close > b.open:
            return b
    return None


def ob_candidates(bars: list[Bar], swings: list[Obj], tf: str, cutoff: datetime, m1_rows, m1_times) -> list[Obj]:
    out: list[Obj] = []
    seen: set[tuple[str, str, str]] = set()
    swing_order = sorted(swings, key=lambda x: x.born_at)
    for s in swing_order:
        born = datetime.strptime(s.born_at, CLI_FMT)
        for i, b in enumerate(bars):
            if b.end <= born:
                continue
            bullish_break = s.direction == "HIGH" and b.close > s.price_high
            bearish_break = s.direction == "LOW" and b.close < s.price_low
            if not (bullish_break or bearish_break):
                continue
            src = last_opposite_candle(bars, i, bullish_break)
            if src is None:
                break
            direction = "BULL" if bullish_break else "BEAR"
            key = (direction, fmt(src.start), s.object_id)
            if key in seen:
                break
            seen.add(key)
            later = m1_after(m1_rows, m1_times, b.end)
            touch = first_m1(later, lambda x: x[3] <= src.high and x[2] >= src.low)
            if bullish_break:
                inval = first_m1(later, lambda x: x[3] < src.low)
            else:
                inval = first_m1(later, lambda x: x[2] > src.high)
            end = inval[0] if inval else cutoff
            out.append(Obj(
                object_id=f"{tf}_OB_{direction}_{src.start:%Y%m%d_%H%M}_VIA_{b.start:%Y%m%d_%H%M}",
                timeframe=tf, family="OB", direction=direction,
                source_start=fmt(src.start), source_mid=None, source_end=fmt(src.start),
                born_at=fmt(b.end), price_low=src.low, price_high=src.high,
                body_low=min(src.open, src.close), body_high=max(src.open, src.close),
                mean_threshold=(src.low + src.high) / 2.0,
                break_reference_id=s.object_id, break_bar=fmt(b.start),
                first_mitigation_at=fmt(touch[0] if touch else None),
                distal_invalidation_at=fmt(inval[0] if inval else None),
                geometric_state="INVALIDATED" if inval else ("MITIGATED" if touch else "ACTIVE"),
                geometric_end_at=fmt(end),
            ))
            break  # first close break of this swing is the candidate event
    # One source candle may be associated with several nearby broken pivots. Preserve first born object.
    dedup: dict[tuple[str, str, str], Obj] = {}
    for o in sorted(out, key=lambda x: x.born_at):
        dedup.setdefault((o.timeframe, o.direction, o.source_start), o)
    return list(dedup.values())


def write_csv(path: Path, objects: list[Obj]) -> None:
    fields = list(asdict(Obj(
        object_id="", timeframe="", family="", direction="", source_start="",
        source_mid=None, source_end="", born_at="", price_low=0.0, price_high=0.0
    )).keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for o in objects:
            w.writerow(asdict(o))


def build(input_path: Path, out_dir: Path) -> dict:
    rows, cutoff = load_revealed_m1(input_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    all_objects: list[Obj] = []
    counts = {}
    m1_times = [r[0] for r in rows]
    for tf, minutes in (("H1", 60), ("H4", 240)):
        bars = aggregate(rows, minutes, cutoff)
        swings = pivot_candidates(bars, tf)
        fvgs = fvg_candidates(bars, tf, cutoff, rows, m1_times)
        liq = liquidity_candidates(bars, swings, tf, cutoff, rows, m1_times)
        obs = ob_candidates(bars, swings, tf, cutoff, rows, m1_times)
        family_map = {"swings": swings, "fvg": fvgs, "liquidity": liq, "ob": obs}
        for name, objs in family_map.items():
            write_csv(out_dir / f"{tf}_{name}.csv", objs)
            counts[f"{tf}_{name}"] = len(objs)
            all_objects.extend(objs)
    write_csv(out_dir / "ict_candidate_universe.csv", all_objects)
    meta = {
        "engine_version": ENGINE_VERSION,
        "input": str(input_path),
        "revealed_cutoff": fmt(cutoff),
        "counts": counts,
        "authority_note": "candidate geometry only; AI owns strategic importance",
    }
    (out_dir / "object_engine_manifest.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True, help="already-revealed M1 TSV prefix")
    p.add_argument("--out-dir", type=Path, required=True)
    a = p.parse_args(argv)
    try:
        print(json.dumps(build(a.input, a.out_dir), indent=2))
        return 0
    except ObjectEngineError as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
