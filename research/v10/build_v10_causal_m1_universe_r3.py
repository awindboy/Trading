"""Build the V10 R3 research universe from the authoritative raw M1 stream.

The builder deliberately does not load pre-exported M15/M30/H1/H4 files.  It
consumes M1 rows in chronological order, finalises higher-timeframe bars only
when a later M1 row proves that their clock interval has ended, and freezes the
feature row before any future run label is attached.

Future run length and Child outcome are answer-sheet fields.  They are added
only after the corresponding FAST run is over.  ``label_available_at`` records
the latest time needed to know all labels so chronological model splits can
purge samples whose answers cross an evaluation boundary.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


SOURCE_TS = "%Y.%m.%d %H:%M:%S"
EXPECTED_M1_SHA256 = "626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2"


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a prefix-causal V10 ML universe from authoritative GOLD M1."
    )
    parser.add_argument("--m1", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument(
        "--parity-ledger",
        type=Path,
        help="Optional R2 ledger used only after generation for a parity receipt.",
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bucket_start(ts: datetime, minutes: int) -> datetime:
    if minutes < 60:
        return ts.replace(minute=(ts.minute // minutes) * minutes, second=0, microsecond=0)
    if minutes == 60:
        return ts.replace(minute=0, second=0, microsecond=0)
    if minutes == 240:
        return ts.replace(hour=(ts.hour // 4) * 4, minute=0, second=0, microsecond=0)
    raise ValueError(f"unsupported timeframe: {minutes}")


@dataclass
class Bar:
    start: datetime
    open: float
    high: float
    low: float
    close: float
    rows: int = 1


class BarAggregator:
    def __init__(self, minutes: int):
        self.minutes = minutes
        self.current: Bar | None = None

    def push(self, ts: datetime, o: float, h: float, l: float, c: float) -> Bar | None:
        start = bucket_start(ts, self.minutes)
        if self.current is None:
            self.current = Bar(start, o, h, l, c)
            return None
        if start != self.current.start:
            done = self.current
            self.current = Bar(start, o, h, l, c)
            return done
        self.current.high = max(self.current.high, h)
        self.current.low = min(self.current.low, l)
        self.current.close = c
        self.current.rows += 1
        return None


@dataclass
class HARecord:
    start: datetime
    raw_open: float
    raw_high: float
    raw_low: float
    raw_close: float
    ha_open: float
    ha_close: float
    ha_high: float
    ha_low: float
    ha_dir: int
    ha_body: float


class HAStream:
    def __init__(self, close_weight: float, alpha: float):
        self.close_weight = close_weight
        self.alpha = alpha
        self.records: list[HARecord] = []

    def append(self, bar: Bar) -> HARecord:
        hc = (
            bar.open + bar.high + bar.low + self.close_weight * bar.close
        ) / (3.0 + self.close_weight)
        if not self.records:
            ho = 0.5 * (bar.open + bar.close)
        else:
            prev = self.records[-1]
            ho = self.alpha * prev.ha_open + (1.0 - self.alpha) * prev.ha_close
        rec = HARecord(
            start=bar.start,
            raw_open=bar.open,
            raw_high=bar.high,
            raw_low=bar.low,
            raw_close=bar.close,
            ha_open=ho,
            ha_close=hc,
            ha_high=max(bar.high, ho, hc),
            ha_low=min(bar.low, ho, hc),
            ha_dir=1 if hc >= ho else -1,
            ha_body=hc - ho,
        )
        self.records.append(rec)
        return rec


class ADXStream:
    """Incremental Wilder ADX matching the existing R2 Python definition."""

    def __init__(self, period: int):
        self.period = period
        self.tr: list[float] = []
        self.pdm: list[float] = []
        self.mdm: list[float] = []
        self.atr: list[float] = []
        self.sp: list[float] = []
        self.sm: list[float] = []
        self.pdi: list[float] = []
        self.mdi: list[float] = []
        self.dx: list[float] = []
        self.adx: list[float] = []

    def append(self, bars: list[Bar]) -> None:
        i = len(bars) - 1
        bar = bars[i]
        if i == 0:
            tr = bar.high - bar.low
            pdm = mdm = 0.0
        else:
            prev = bars[i - 1]
            tr = max(bar.high - bar.low, abs(bar.high - prev.close), abs(bar.low - prev.close))
            up = bar.high - prev.high
            down = prev.low - bar.low
            pdm = up if up > down and up > 0.0 else 0.0
            mdm = down if down > up and down > 0.0 else 0.0
        self.tr.append(tr)
        self.pdm.append(pdm)
        self.mdm.append(mdm)
        nan = float("nan")
        self.atr.append(nan)
        self.sp.append(nan)
        self.sm.append(nan)
        self.pdi.append(nan)
        self.mdi.append(nan)
        self.dx.append(nan)
        self.adx.append(nan)

        n = self.period
        if i == n:
            self.atr[i] = float(sum(self.tr[1 : n + 1]))
            self.sp[i] = float(sum(self.pdm[1 : n + 1]))
            self.sm[i] = float(sum(self.mdm[1 : n + 1]))
        elif i > n:
            self.atr[i] = self.atr[i - 1] - self.atr[i - 1] / n + tr
            self.sp[i] = self.sp[i - 1] - self.sp[i - 1] / n + pdm
            self.sm[i] = self.sm[i - 1] - self.sm[i - 1] / n + mdm

        if i >= n and math.isfinite(self.atr[i]) and self.atr[i] > 0.0:
            self.pdi[i] = 100.0 * self.sp[i] / self.atr[i]
            self.mdi[i] = 100.0 * self.sm[i] / self.atr[i]
            denom = self.pdi[i] + self.mdi[i]
            if denom > 0.0:
                self.dx[i] = 100.0 * abs(self.pdi[i] - self.mdi[i]) / denom

        start = 2 * n
        if i == start:
            vals = [x for x in self.dx[n + 1 : start + 1] if math.isfinite(x)]
            if vals:
                self.adx[i] = float(np.mean(vals))
        elif i > start and math.isfinite(self.dx[i]) and math.isfinite(self.adx[i - 1]):
            self.adx[i] = (self.adx[i - 1] * (n - 1) + self.dx[i]) / n


def finite_median(values: Iterable[float], minimum: int = 1) -> float:
    clean = [float(v) for v in values if math.isfinite(float(v))]
    return float(np.median(clean)) if len(clean) >= minimum else float("nan")


def path_efficiency(closes: list[float], window: int) -> float:
    if len(closes) < window:
        return float("nan")
    values = closes[-window:]
    denom = sum(abs(values[i] - values[i - 1]) for i in range(1, len(values)))
    return abs(values[-1] - values[0]) / denom if denom > 1e-12 else 0.0


def flip_rate(directions: list[int], window: int) -> float:
    if len(directions) < window:
        return float("nan")
    seq = directions[-window:]
    return float(np.mean(np.asarray(seq[1:]) != np.asarray(seq[:-1])))


def window_features(records: list[HARecord], start: datetime, end: datetime, pdir: int, scale: float) -> dict[str, float] | None:
    seq: list[HARecord] = []
    for rec in reversed(records):
        if rec.start >= end:
            continue
        if rec.start < start:
            break
        seq.append(rec)
    seq.reverse()
    if not seq:
        return None

    signs = np.asarray([pdir * x.ha_dir for x in seq], dtype=float)
    transitions = int(np.sum(signs[1:] != signs[:-1])) if len(signs) > 1 else 0
    runs: list[tuple[float, int]] = []
    run_start = 0
    for i in range(1, len(signs) + 1):
        if i == len(signs) or signs[i] != signs[run_start]:
            runs.append((signs[run_start], i - run_start))
            run_start = i
    same = [length for sign, length in runs if sign > 0]
    opposite = [length for sign, length in runs if sign < 0]
    body = np.asarray([pdir * (x.ha_close - x.ha_open) for x in seq], dtype=float)
    ranges = np.maximum(
        np.asarray([x.ha_high - x.ha_low for x in seq], dtype=float), 1e-9
    )
    if pdir > 0:
        wick = np.asarray(
            [max(0.0, min(x.ha_open, x.ha_close) - x.ha_low) for x in seq]
        ) / ranges
    else:
        wick = np.asarray(
            [max(0.0, x.ha_high - max(x.ha_open, x.ha_close)) for x in seq]
        ) / ranges
    last_sign = signs[-1]
    streak = 0
    for sign in signs[::-1]:
        if sign != last_sign:
            break
        streak += 1
    return {
        "aligned": float(np.mean(signs > 0)),
        "transition": transitions / max(1, len(signs) - 1),
        "same_mean": float(np.mean(same)) if same else 0.0,
        "opp_mean": float(np.mean(opposite)) if opposite else 0.0,
        "same_max": float(max(same)) if same else 0.0,
        "opp_max": float(max(opposite)) if opposite else 0.0,
        "len_adv": float((max(same) if same else 0) - (max(opposite) if opposite else 0)),
        "streak": float(streak if last_sign > 0 else -streak),
        "body_sum_atr": float(body.sum() / max(scale, 1e-9)),
        "body_mean_atr": float(body.mean() / max(scale, 1e-9)),
        "body_eff": float(body.sum() / max(np.abs(body).sum(), 1e-9)),
        "body_rng": float(np.mean(body / ranges)),
        "opp_wick": float(np.mean(wick)),
        "no_opp_wick": float(np.mean(wick < 1e-10)),
    }


class UniverseBuilder:
    def __init__(self) -> None:
        self.aggregators = {name: BarAggregator(minutes) for name, minutes in {
            "m15": 15,
            "m30": 30,
            "h1": 60,
            "h4": 240,
        }.items()}
        self.ltf_ha = {
            "m15": HAStream(2.0, 0.25),
            "m30": HAStream(2.0, 0.25),
            "h1": HAStream(1.0, 0.50),
        }
        self.h4_bars: list[Bar] = []
        self.h4_fast = HAStream(2.0, 0.25)
        self.h4_std = HAStream(1.0, 0.50)
        self.h4_slow = HAStream(2.0, 0.75)
        self.atr180: list[float] = []
        self.ema8: list[float] = []
        self.ema21: list[float] = []
        self.adx14 = ADXStream(14)
        self.adx28 = ADXStream(28)
        self.pe4: list[float] = []
        self.pe12: list[float] = []

        self.last_fast_dir = 0
        self.run_id = 0
        self.run_k = 0
        self.run_record_ids: list[int] = []
        self.completed_run_lengths: list[int] = []
        self.records: list[dict[str, object]] = []
        self.active_record_ids: list[int] = []
        self.first_m1: datetime | None = None
        self.last_m1: datetime | None = None
        self.m1_rows = 0

    def _update_h4_indicators(self, bar: Bar) -> None:
        i = len(self.h4_bars) - 1
        if i == 0:
            tr = bar.high - bar.low
        else:
            prev = self.h4_bars[i - 1]
            tr = max(bar.high - bar.low, abs(bar.high - prev.close), abs(bar.low - prev.close))
        if i < 179:
            self.atr180.append(float("nan"))
        elif i == 179:
            trs: list[float] = []
            for j, candidate in enumerate(self.h4_bars[:180]):
                if j == 0:
                    trs.append(candidate.high - candidate.low)
                else:
                    p = self.h4_bars[j - 1]
                    trs.append(max(candidate.high - candidate.low, abs(candidate.high - p.close), abs(candidate.low - p.close)))
            self.atr180.append(float(np.mean(trs)))
        else:
            self.atr180.append((self.atr180[-1] * 179.0 + tr) / 180.0)

        if i == 0:
            self.ema8.append(bar.close)
            self.ema21.append(bar.close)
        else:
            self.ema8.append((2.0 / 9.0) * bar.close + (7.0 / 9.0) * self.ema8[-1])
            self.ema21.append((2.0 / 22.0) * bar.close + (20.0 / 22.0) * self.ema21[-1])
        self.adx14.append(self.h4_bars)
        self.adx28.append(self.h4_bars)
        closes = [x.close for x in self.h4_bars]
        self.pe4.append(path_efficiency(closes, 4))
        self.pe12.append(path_efficiency(closes, 12))

    def _close_record(self, record_id: int, exit_time: datetime, exit_price: float, reason: str, gap: bool = False) -> None:
        rec = self.records[record_id]
        if rec.get("exit_time") is not None:
            return
        direction = int(rec["dir"])
        entry = float(rec["entry"])
        stop = float(rec["stop"])
        pnl = direction * (exit_price - entry)
        risk = abs(entry - stop)
        rec.update(
            exit_time=exit_time,
            exit=exit_price,
            exit_reason=reason,
            stop_hit=int(reason.startswith("HARD_SL")),
            gap_stop=int(gap),
            pnl=pnl,
            R=pnl / risk if risk > 0 else float("nan"),
            position_hours=(exit_time - datetime.fromisoformat(str(rec["entry_time"]))).total_seconds() / 3600.0,
        )

    def _finalise_previous_run(
        self,
        decision: datetime,
        exit_time_actual: datetime,
        exit_open: float,
        exit_high: float,
        exit_low: float,
    ) -> None:
        if self.last_fast_dir == 0:
            return
        finished_len = self.run_k
        for record_id in self.run_record_ids:
            rec = self.records[record_id]
            rec["L"] = finished_len
            rec["run_end_decision"] = decision
            if rec.get("exit_time") is None:
                direction = int(rec["dir"])
                stop = float(rec["stop"])
                same_m1_stop = exit_low <= stop if direction > 0 else exit_high >= stop
                if same_m1_stop:
                    self._close_record(
                        record_id,
                        exit_time_actual,
                        stop,
                        "HARD_SL_NHA_SAME_M1_AMBIGUOUS",
                        exit_open <= stop if direction > 0 else exit_open >= stop,
                    )
                    risk = abs(float(rec["entry"]) - stop)
                    alternative_pnl = direction * (exit_open - float(rec["entry"]))
                    rec["same_m1_exit_stop_ambiguous"] = 1
                    rec["alternative_nha_exit"] = exit_open
                    rec["alternative_nha_pnl"] = alternative_pnl
                    rec["alternative_nha_R"] = alternative_pnl / risk if risk > 0 else float("nan")
                else:
                    self._close_record(record_id, exit_time_actual, exit_open, "FAST_NHA")
            exit_time = datetime.fromisoformat(str(rec["exit_time"]))
            rec["label_available_at"] = max(decision, exit_time)
        self.completed_run_lengths.append(finished_len)
        self.active_record_ids = [
            idx for idx in self.active_record_ids if self.records[idx].get("exit_time") is None
        ]
        self.run_record_ids = []

    def _h4_feature_row(self, bar: Bar, decision: datetime, entry_time: datetime, entry: float) -> dict[str, object] | None:
        i = len(self.h4_bars) - 1
        if i < 181:
            return None
        fast = self.h4_fast.records[i]
        std = self.h4_std.records[i]
        slow = self.h4_slow.records[i]
        pdir = fast.ha_dir
        stop = self.h4_std.records[i - 1].ha_low if pdir > 0 else self.h4_std.records[i - 1].ha_high
        if (pdir > 0 and stop >= entry) or (pdir < 0 and stop <= entry):
            return None
        scale = self.atr180[i - 1]
        if not math.isfinite(scale) or scale <= 0.0:
            return None
        adx_med = finite_median(self.adx28.adx[max(0, i - 180) : i], 60)
        pe4_med = finite_median(self.pe4[max(0, i - 180) : i], 60)
        pe12_med = finite_median(self.pe12[max(0, i - 180) : i], 60)
        if not all(math.isfinite(x) and x > 0.0 for x in (adx_med, pe4_med, pe12_med)):
            return None
        ltf_values: dict[str, dict[str, float]] = {}
        for name in ("m15", "m30", "h1"):
            wf = window_features(self.ltf_ha[name].records, bar.start, decision, pdir, scale)
            if wf is None:
                return None
            ltf_values[name] = wf

        body_range = max(fast.ha_high - fast.ha_low, 1e-9)
        prev_fast = self.h4_fast.records[i - 1]
        prev_body_range = max(prev_fast.ha_high - prev_fast.ha_low, 1e-9)
        prev_lengths = self.completed_run_lengths[-4:]
        previous_run_len = float(prev_lengths[-1]) if prev_lengths else 0.0
        prev4_mean = float(np.mean(prev_lengths)) if prev_lengths else 0.0
        prev4_short_rate = float(np.mean(np.asarray(prev_lengths) <= 2)) if prev_lengths else 0.0
        prev4_std = float(np.std(prev_lengths)) if len(prev_lengths) >= 2 else 0.0
        alignments = np.asarray([ltf_values[x]["aligned"] for x in ("m15", "m30", "h1")])
        direction_votes = [
            float(std.ha_dir == pdir),
            float(slow.ha_dir == pdir),
            float(pdir * (self.adx14.pdi[i] - self.adx14.mdi[i]) > 0.0),
            float(pdir * (self.ema8[i] - self.ema21[i]) > 0.0),
            *[float(x >= 0.5) for x in alignments],
        ]

        rec: dict[str, object] = {
            "signal_id": f"{decision:%Y%m%d%H%M}_{'L' if pdir > 0 else 'S'}_{self.run_k}",
            "decision": decision,
            "entry_time": entry_time,
            "year": decision.year,
            "dir": pdir,
            "k": self.run_k,
            "rid": self.run_id,
            "entry": entry,
            "stop": stop,
            "stop_dist_atr": abs(entry - stop) / scale,
            "fast_body_rng": pdir * fast.ha_body / body_range,
            "fast_body_atr": pdir * fast.ha_body / scale,
            "std_align": int(std.ha_dir == pdir),
            "std_body_rng": pdir * std.ha_body / max(std.ha_high - std.ha_low, 1e-9),
            "slow_align": int(slow.ha_dir == pdir),
            "slow_body_rng": pdir * slow.ha_body / max(slow.ha_high - slow.ha_low, 1e-9),
            "adx14": self.adx14.adx[i],
            "adx28_rel": self.adx28.adx[i] / adx_med,
            "di14_signed": pdir * (self.adx14.pdi[i] - self.adx14.mdi[i]) / 100.0,
            "di28_signed": pdir * (self.adx28.pdi[i] - self.adx28.mdi[i]) / 100.0,
            "ema8_21_signed": pdir * (self.ema8[i] - self.ema21[i]) / scale,
            "ema8_slope": pdir * (self.ema8[i] - self.ema8[i - 1]) / scale,
            "path_eff4_rel": self.pe4[i] / pe4_med,
            "path_eff12_rel": self.pe12[i] / pe12_med,
            "flip4": flip_rate([x.ha_dir for x in self.h4_fast.records], 4),
            "flip8": flip_rate([x.ha_dir for x in self.h4_fast.records], 8),
            "flip12": flip_rate([x.ha_dir for x in self.h4_fast.records], 12),
            # R3 causal morphology: completed-run and trajectory context.
            "prev_run_len": previous_run_len,
            "prev4_run_mean": prev4_mean,
            "prev4_run_std": prev4_std,
            "prev4_short_rate": prev4_short_rate,
            "adx28_delta3_rel": (
                (self.adx28.adx[i] - self.adx28.adx[i - 3]) / adx_med
                if math.isfinite(self.adx28.adx[i - 3])
                else 0.0
            ),
            "path_eff4_delta": self.pe4[i] - self.pe4[i - 1],
            "fast_body_delta": pdir * fast.ha_body / body_range - pdir * prev_fast.ha_body / prev_body_range,
            "ltf_align_mean": float(np.mean(alignments)),
            "ltf_align_std": float(np.std(alignments)),
            "direction_vote": float(np.mean(direction_votes)),
            "exit_time": None,
            "exit": None,
            "exit_reason": None,
            "stop_hit": None,
            "gap_stop": 0,
            "same_m1_exit_stop_ambiguous": 0,
            "alternative_nha_exit": None,
            "alternative_nha_pnl": None,
            "alternative_nha_R": None,
            "pnl": None,
            "R": None,
            "position_hours": None,
            "L": None,
            "run_end_decision": None,
            "label_available_at": None,
        }
        for name, values in ltf_values.items():
            for key, value in values.items():
                rec[f"{name}_{key}"] = value
        return rec

    def _on_h4_complete(
        self,
        bar: Bar,
        tick_ts: datetime,
        tick_open: float,
        tick_high: float,
        tick_low: float,
    ) -> None:
        self.h4_bars.append(bar)
        fast = self.h4_fast.append(bar)
        self.h4_std.append(bar)
        self.h4_slow.append(bar)
        self._update_h4_indicators(bar)
        decision = bar.start + timedelta(hours=4)
        new_direction = fast.ha_dir
        flip = self.last_fast_dir != 0 and new_direction != self.last_fast_dir
        if self.last_fast_dir == 0:
            self.run_id = 1
            self.run_k = 1
        elif flip:
            self._finalise_previous_run(
                decision, tick_ts, tick_open, tick_high, tick_low
            )
            self.run_id += 1
            self.run_k = 1
        else:
            self.run_k += 1
        self.last_fast_dir = new_direction

        if decision.year < 2022 or decision.year > 2026:
            return
        if tick_ts - decision > timedelta(hours=4):
            return
        rec = self._h4_feature_row(bar, decision, tick_ts, tick_open)
        if rec is None:
            return
        record_id = len(self.records)
        self.records.append(rec)
        self.run_record_ids.append(record_id)
        self.active_record_ids.append(record_id)

    def push_m1(self, ts: datetime, o: float, h: float, l: float, c: float) -> None:
        if self.first_m1 is None:
            self.first_m1 = ts
        self.last_m1 = ts
        self.m1_rows += 1
        for name in ("m15", "m30", "h1"):
            done = self.aggregators[name].push(ts, o, h, l, c)
            if done is not None:
                self.ltf_ha[name].append(done)
        h4_done = self.aggregators["h4"].push(ts, o, h, l, c)
        if h4_done is not None:
            self._on_h4_complete(h4_done, ts, o, h, l)

        survivors: list[int] = []
        for record_id in self.active_record_ids:
            rec = self.records[record_id]
            if rec.get("exit_time") is not None:
                continue
            direction = int(rec["dir"])
            stop = float(rec["stop"])
            touched = l <= stop if direction > 0 else h >= stop
            if touched:
                gap = o <= stop if direction > 0 else o >= stop
                self._close_record(record_id, ts, stop, "HARD_SL_GAP" if gap else "HARD_SL", gap)
            else:
                survivors.append(record_id)
        self.active_record_ids = survivors

    def frame(self) -> pd.DataFrame:
        resolved = [
            row
            for row in self.records
            if row.get("L") is not None
            and row.get("exit_time") is not None
            and row.get("label_available_at") is not None
        ]
        frame = pd.DataFrame(resolved).sort_values("decision").reset_index(drop=True)
        if frame.empty:
            return frame
        frame["L"] = frame["L"].astype(int)
        frame["early3"] = (3 * frame["k"] <= frame["L"]).astype(int)
        frame["next_same"] = (frame["k"] < frame["L"]).astype(int)
        frame["trendable3"] = (frame["L"] >= 3).astype(int)
        frame["win"] = (frame["R"] > 0.0).astype(int)
        frame["severe"] = (frame["R"] <= -0.5).astype(int)
        frame["shock"] = ((frame["k"] == frame["L"]) & (frame["R"] <= -0.5)).astype(int)
        frame["remaining_h4"] = frame["L"] - frame["k"]
        return frame


def read_m1(path: Path, builder: UniverseBuilder) -> None:
    previous: datetime | None = None
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        expected = {"<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>"}
        if not expected.issubset(reader.fieldnames or []):
            raise ValueError(f"unexpected M1 schema: {reader.fieldnames}")
        for row in reader:
            ts = datetime.strptime(f"{row['<DATE>']} {row['<TIME>']}", SOURCE_TS)
            if previous is not None and ts <= previous:
                raise ValueError(f"M1 is not strictly chronological at {ts}")
            previous = ts
            builder.push_m1(
                ts,
                float(row["<OPEN>"]),
                float(row["<HIGH>"]),
                float(row["<LOW>"]),
                float(row["<CLOSE>"]),
            )


def parity_receipt(frame: pd.DataFrame, path: Path) -> dict[str, object]:
    reference = pd.read_csv(path, parse_dates=["decision"])
    reference_years = sorted(reference["year"].astype(int).unique())
    candidate = frame[frame["year"].isin(reference_years)].copy()
    candidate["decision"] = pd.to_datetime(candidate["decision"])
    merged = reference.merge(candidate, on="decision", how="outer", suffixes=("_r2", "_r3"), indicator=True)
    common = merged[merged["_merge"] == "both"]
    numeric = [
        "entry", "stop", "stop_dist_atr", "pnl", "R", "fast_body_rng",
        "std_body_rng", "adx28_rel", "di14_signed", "ema8_21_signed",
        "path_eff4_rel", "path_eff12_rel", "flip8", "m15_aligned",
        "m30_aligned", "h1_aligned",
    ]
    differences: dict[str, object] = {}
    for column in numeric:
        left = pd.to_numeric(common[f"{column}_r2"], errors="coerce")
        right = pd.to_numeric(common[f"{column}_r3"], errors="coerce")
        delta = (left - right).abs().dropna()
        differences[column] = {
            "n": int(len(delta)),
            "max_abs": float(delta.max()) if len(delta) else None,
            "p99_abs": float(delta.quantile(0.99)) if len(delta) else None,
            "within_1e-9": int((delta <= 1e-9).sum()),
        }
    return {
        "reference": str(path),
        "reference_rows": int(len(reference)),
        "candidate_rows_in_reference_years": int(len(candidate)),
        "matched_decisions": int(len(common)),
        "reference_only": int((merged["_merge"] == "left_only").sum()),
        "candidate_only": int((merged["_merge"] == "right_only").sum()),
        "direction_mismatches": int((common["dir_r2"].astype(int) != common["dir_r3"].astype(int)).sum()),
        "k_mismatches": int((common["k_r2"].astype(int) != common["k_r3"].astype(int)).sum()),
        "numeric_differences": differences,
        "note": (
            "R3 reconstructs every timeframe from raw M1. When the first M1 of a "
            "new FAST run contains both the decision-open NHA exit and the old "
            "Child stop, exact tick order is unknowable: the primary ledger uses "
            "the conservative stop outcome and persists the NHA-open alternative."
        ),
    }


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    source_hash = sha256_file(args.m1)
    if source_hash.lower() != EXPECTED_M1_SHA256:
        raise ValueError(
            f"M1 SHA256 mismatch: {source_hash}; expected {EXPECTED_M1_SHA256}"
        )
    builder = UniverseBuilder()
    read_m1(args.m1, builder)
    frame = builder.frame()
    out_csv = args.out_dir / "V10_R3_CAUSAL_M1_UNIVERSE_2022_2026.csv"
    frame.to_csv(out_csv, index=False, date_format="%Y-%m-%d %H:%M:%S")

    manifest = {
        "ok": True,
        "source": str(args.m1.resolve()),
        "source_sha256": source_hash,
        "source_rows": builder.m1_rows,
        "source_first": builder.first_m1.isoformat(sep=" ") if builder.first_m1 else None,
        "source_last": builder.last_m1.isoformat(sep=" ") if builder.last_m1 else None,
        "universe_rows": int(len(frame)),
        "year_rows": {str(int(k)): int(v) for k, v in frame.groupby("year").size().items()},
        "resolved_runs": int(frame["rid"].nunique()) if len(frame) else 0,
        "feature_clock": "single-pass chronological raw M1; completed bars only",
        "label_clock": "future answers attached only after FAST run resolution; label_available_at persisted",
        "output": str(out_csv),
    }
    (args.out_dir / "V10_R3_CAUSAL_M1_UNIVERSE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    if args.parity_ledger:
        receipt = parity_receipt(frame, args.parity_ledger)
        (args.out_dir / "V10_R3_R2_UNIVERSE_PARITY.json").write_text(
            json.dumps(receipt, indent=2), encoding="utf-8"
        )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
