"""Build a prefix-causal H4 microstructure ledger directly from raw GOLD M1.

The ledger is intentionally outcome-free.  Each row is frozen only after a
later M1 row proves that the preceding H4 interval has completed.  It adds
information that the existing V10 state ledgers do not retain: settlement
inside the just-completed PHA, M1 path quality, H4 overlap/break behaviour,
and tick-volume/spread context.  Future run length, stop outcome, and policy
selection are joined only in downstream research.
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

import numpy as np


SOURCE_TS = "%Y.%m.%d %H:%M:%S"
EXPECTED_M1_SHA256 = "626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2"


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build causal H4 microstructure features from chronological raw M1."
    )
    parser.add_argument("--m1", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def h4_start(ts: datetime) -> datetime:
    return ts.replace(hour=(ts.hour // 4) * 4, minute=0, second=0, microsecond=0)


def median_prior(values: list[float], window: int = 180, minimum: int = 60) -> float:
    clean = [x for x in values[-window:] if math.isfinite(x)]
    return float(np.median(clean)) if len(clean) >= minimum else float("nan")


def safe_ratio(numerator: float, denominator: float, fallback: float = 0.0) -> float:
    return numerator / denominator if math.isfinite(denominator) and abs(denominator) > 1e-12 else fallback


@dataclass
class M1Row:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: float
    spread: float


@dataclass
class H4Bar:
    start: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass
class HARecord:
    ha_open: float
    ha_close: float
    ha_high: float
    ha_low: float
    direction: int


class HAStream:
    def __init__(self, close_weight: float, alpha: float) -> None:
        self.close_weight = close_weight
        self.alpha = alpha
        self.records: list[HARecord] = []

    def append(self, bar: H4Bar) -> HARecord:
        ha_close = (
            bar.open + bar.high + bar.low + self.close_weight * bar.close
        ) / (3.0 + self.close_weight)
        if not self.records:
            ha_open = 0.5 * (bar.open + bar.close)
        else:
            previous = self.records[-1]
            ha_open = self.alpha * previous.ha_open + (1.0 - self.alpha) * previous.ha_close
        record = HARecord(
            ha_open=ha_open,
            ha_close=ha_close,
            ha_high=max(bar.high, ha_open, ha_close),
            ha_low=min(bar.low, ha_open, ha_close),
            direction=1 if ha_close >= ha_open else -1,
        )
        self.records.append(record)
        return record


class PrefixBuilder:
    def __init__(self) -> None:
        self.current_start: datetime | None = None
        self.current_rows: list[M1Row] = []
        self.h4_bars: list[H4Bar] = []
        self.fast = HAStream(2.0, 0.25)
        self.std = HAStream(1.0, 0.50)
        self.slow = HAStream(2.0, 0.75)
        self.atr180: list[float] = []
        self.fast_directions: list[int] = []
        self.current_run_k = 0
        self.last_fast_direction = 0
        self.completed_run_lengths: list[int] = []
        self.h4_range_atr_history: list[float] = []
        self.tick_volume_history: list[float] = []
        self.spread_history: list[float] = []
        self.rows: list[dict[str, object]] = []
        self.source_rows = 0
        self.first_ts: datetime | None = None
        self.last_ts: datetime | None = None

    def push(self, row: M1Row) -> None:
        if self.first_ts is None:
            self.first_ts = row.ts
        self.last_ts = row.ts
        self.source_rows += 1
        start = h4_start(row.ts)
        if self.current_start is None:
            self.current_start = start
        elif start != self.current_start:
            self._finalise_current()
            self.current_start = start
            self.current_rows = []
        self.current_rows.append(row)

    def _append_atr(self, bar: H4Bar) -> None:
        index = len(self.h4_bars) - 1
        if index == 0:
            true_range = bar.high - bar.low
        else:
            previous = self.h4_bars[index - 1]
            true_range = max(
                bar.high - bar.low,
                abs(bar.high - previous.close),
                abs(bar.low - previous.close),
            )
        if index < 179:
            self.atr180.append(float("nan"))
        elif index == 179:
            true_ranges: list[float] = []
            for offset, candidate in enumerate(self.h4_bars[:180]):
                if offset == 0:
                    true_ranges.append(candidate.high - candidate.low)
                else:
                    previous = self.h4_bars[offset - 1]
                    true_ranges.append(
                        max(
                            candidate.high - candidate.low,
                            abs(candidate.high - previous.close),
                            abs(candidate.low - previous.close),
                        )
                    )
            self.atr180.append(float(np.mean(true_ranges)))
        else:
            self.atr180.append((self.atr180[-1] * 179.0 + true_range) / 180.0)

    def _quarter_returns(self, rows: list[M1Row], direction: int, scale: float) -> list[float]:
        values: list[float] = []
        assert self.current_start is not None
        for quarter in range(4):
            lo = self.current_start + timedelta(hours=quarter)
            hi = lo + timedelta(hours=1)
            segment = [row for row in rows if lo <= row.ts < hi]
            if not segment:
                values.append(float("nan"))
            else:
                values.append(direction * (segment[-1].close - segment[0].open) / scale)
        return values

    def _finalise_current(self) -> None:
        rows = self.current_rows
        if not rows or self.current_start is None:
            return
        bar = H4Bar(
            start=self.current_start,
            open=rows[0].open,
            high=max(row.high for row in rows),
            low=min(row.low for row in rows),
            close=rows[-1].close,
        )
        self.h4_bars.append(bar)
        fast = self.fast.append(bar)
        std = self.std.append(bar)
        slow = self.slow.append(bar)
        self._append_atr(bar)
        index = len(self.h4_bars) - 1

        if self.last_fast_direction == 0:
            self.current_run_k = 1
        elif fast.direction != self.last_fast_direction:
            self.completed_run_lengths.append(self.current_run_k)
            self.current_run_k = 1
        else:
            self.current_run_k += 1
        previous_run_length = self.completed_run_lengths[-1] if self.completed_run_lengths else 0
        self.last_fast_direction = fast.direction
        self.fast_directions.append(fast.direction)

        if index < 181 or not math.isfinite(self.atr180[index - 1]):
            return
        scale = self.atr180[index - 1]
        if scale <= 0.0:
            return

        direction = fast.direction
        raw_range = max(bar.high - bar.low, 1e-9)
        raw_body = direction * (bar.close - bar.open)
        closes = np.asarray([bar.open, *[row.close for row in rows]], dtype=float)
        changes = np.diff(closes)
        absolute_path = float(np.abs(changes).sum())
        signed_changes = direction * changes
        nonzero_signs = np.sign(changes[np.abs(changes) > 1e-12])
        m1_flip_rate = (
            float(np.mean(nonzero_signs[1:] != nonzero_signs[:-1]))
            if len(nonzero_signs) >= 2
            else 0.0
        )
        return_autocorr = (
            float(np.corrcoef(changes[:-1], changes[1:])[0, 1])
            if len(changes) >= 3
            and float(np.std(changes[:-1])) > 1e-12
            and float(np.std(changes[1:])) > 1e-12
            else 0.0
        )
        if not math.isfinite(return_autocorr):
            return_autocorr = 0.0

        if direction > 0:
            favorable = bar.high - bar.open
            adverse = bar.open - bar.low
            settle_from_favorable = bar.high - bar.close
            favorable_index = int(np.argmax([row.high for row in rows]))
            adverse_index = int(np.argmin([row.low for row in rows]))
            opposing_wick = min(bar.open, bar.close) - bar.low
            directional_wick = bar.high - max(bar.open, bar.close)
        else:
            favorable = bar.open - bar.low
            adverse = bar.high - bar.open
            settle_from_favorable = bar.close - bar.low
            favorable_index = int(np.argmin([row.low for row in rows]))
            adverse_index = int(np.argmax([row.high for row in rows]))
            opposing_wick = bar.high - max(bar.open, bar.close)
            directional_wick = min(bar.open, bar.close) - bar.low

        quarter_returns = self._quarter_returns(rows, direction, scale)
        tick_volume_sum = float(sum(row.tick_volume for row in rows))
        spreads = np.asarray([row.spread for row in rows], dtype=float)
        spread_median = float(np.median(spreads))
        range_atr = raw_range / scale

        tick_volume_prior_median = median_prior(self.tick_volume_history)
        spread_prior_median = median_prior(self.spread_history)
        range_prior_median = median_prior(self.h4_range_atr_history)

        previous_bar = self.h4_bars[index - 1]
        previous_range = max(previous_bar.high - previous_bar.low, 1e-9)
        overlap = max(
            0.0,
            min(bar.high, previous_bar.high) - max(bar.low, previous_bar.low),
        )
        if direction > 0:
            close_break_previous = bar.close - previous_bar.high
            wick_break_previous = bar.high - previous_bar.high
        else:
            close_break_previous = previous_bar.low - bar.close
            wick_break_previous = previous_bar.low - bar.low

        decision = bar.start + timedelta(hours=4)
        record: dict[str, object] = {
            "decision": decision,
            "year": decision.year,
            "h4_start": bar.start,
            "h4_rows": len(rows),
            "fast_dir": direction,
            "run_k": self.current_run_k,
            "prev_run_len_micro": previous_run_length,
            "raw_body_atr": raw_body / scale,
            "raw_body_rng": raw_body / raw_range,
            "raw_range_atr": range_atr,
            "raw_close_location": direction * (2.0 * (bar.close - bar.low) / raw_range - 1.0),
            "opposing_wick_rng": max(0.0, opposing_wick) / raw_range,
            "directional_wick_rng": max(0.0, directional_wick) / raw_range,
            "m1_path_eff_signed": safe_ratio(raw_body, absolute_path),
            "m1_aligned_return_rate": float(np.mean(signed_changes > 0.0)) if len(changes) else 0.0,
            "m1_flip_rate": m1_flip_rate,
            "m1_return_autocorr": return_autocorr,
            "mfe_atr": favorable / scale,
            "mae_atr": adverse / scale,
            "settle_giveback_atr": settle_from_favorable / scale,
            "settle_giveback_frac": safe_ratio(settle_from_favorable, favorable),
            "favorable_extreme_time": safe_ratio(favorable_index, max(1, len(rows) - 1)),
            "adverse_extreme_time": safe_ratio(adverse_index, max(1, len(rows) - 1)),
            "q1_signed_return_atr": quarter_returns[0],
            "q2_signed_return_atr": quarter_returns[1],
            "q3_signed_return_atr": quarter_returns[2],
            "q4_signed_return_atr": quarter_returns[3],
            "late_minus_early_atr": (
                quarter_returns[3] - quarter_returns[0]
                if math.isfinite(quarter_returns[0]) and math.isfinite(quarter_returns[3])
                else float("nan")
            ),
            "late_half_minus_early_half_atr": (
                quarter_returns[2] + quarter_returns[3] - quarter_returns[0] - quarter_returns[1]
                if all(math.isfinite(value) for value in quarter_returns)
                else float("nan")
            ),
            "tick_volume_sum": tick_volume_sum,
            "tick_volume_rel": safe_ratio(tick_volume_sum, tick_volume_prior_median, 1.0),
            "spread_median": spread_median,
            "spread_p90": float(np.quantile(spreads, 0.90)),
            "spread_max": float(np.max(spreads)),
            "spread_rel": safe_ratio(spread_median, spread_prior_median, 1.0),
            "range_rel": safe_ratio(range_atr, range_prior_median, 1.0),
            "previous_bar_overlap_current": overlap / raw_range,
            "previous_bar_overlap_min": overlap / min(raw_range, previous_range),
            "inside_previous_bar": int(bar.high <= previous_bar.high and bar.low >= previous_bar.low),
            "close_break_previous_atr": close_break_previous / scale,
            "wick_break_previous_atr": wick_break_previous / scale,
            "wick_break_without_close": int(wick_break_previous > 0.0 and close_break_previous <= 0.0),
            "fast_body_atr_micro": direction * (fast.ha_close - fast.ha_open) / scale,
            "std_body_atr_micro": direction * (std.ha_close - std.ha_open) / scale,
            "slow_body_atr_micro": direction * (slow.ha_close - slow.ha_open) / scale,
        }
        self.rows.append(record)

        self.h4_range_atr_history.append(range_atr)
        self.tick_volume_history.append(tick_volume_sum)
        self.spread_history.append(spread_median)


def build(path: Path) -> PrefixBuilder:
    builder = PrefixBuilder()
    previous: datetime | None = None
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        expected = {
            "<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>",
            "<TICKVOL>", "<SPREAD>",
        }
        if not expected.issubset(reader.fieldnames or []):
            raise ValueError(f"unexpected M1 schema: {reader.fieldnames}")
        for source in reader:
            ts = datetime.strptime(f"{source['<DATE>']} {source['<TIME>']}", SOURCE_TS)
            if previous is not None and ts <= previous:
                raise ValueError(f"M1 is not strictly chronological at {ts}")
            previous = ts
            builder.push(
                M1Row(
                    ts=ts,
                    open=float(source["<OPEN>"]),
                    high=float(source["<HIGH>"]),
                    low=float(source["<LOW>"]),
                    close=float(source["<CLOSE>"]),
                    tick_volume=float(source["<TICKVOL>"]),
                    spread=float(source["<SPREAD>"]),
                )
            )
    return builder


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    source_hash = sha256_file(args.m1)
    if source_hash.lower() != EXPECTED_M1_SHA256:
        raise ValueError(f"M1 SHA256 mismatch: {source_hash}")
    builder = build(args.m1)
    output = args.out_dir / "V10_CAUSAL_H4_MICROSTRUCTURE_2022_2026.csv"
    if not builder.rows:
        raise ValueError("no completed causal H4 feature rows were generated")
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(builder.rows[0]))
        writer.writeheader()
        writer.writerows(builder.rows)
    manifest = {
        "ok": True,
        "source": str(args.m1.resolve()),
        "source_sha256": source_hash,
        "source_rows": builder.source_rows,
        "source_first": builder.first_ts.isoformat(sep=" ") if builder.first_ts else None,
        "source_last": builder.last_ts.isoformat(sep=" ") if builder.last_ts else None,
        "feature_rows": len(builder.rows),
        "feature_clock": "single-pass chronological raw M1; completed H4 only; no outcome labels",
        "output": str(output),
    }
    (args.out_dir / "V10_CAUSAL_H4_MICROSTRUCTURE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
