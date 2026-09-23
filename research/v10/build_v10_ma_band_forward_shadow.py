"""Build the frozen V10 normalized MA-band state on new chronology.

The input is read once in strict M1 order.  Higher timeframes and every MA
coordinate are updated only when a later M1 row proves that the relevant bar
has completed.  The script records continuous state; it does not scan a
threshold, create a score, veto a Child, or alter an order.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from build_v10_causal_m1_universe_r3 import Bar, BarAggregator, UniverseBuilder


SOURCE_TS = "%Y.%m.%d %H:%M:%S"
TIMEFRAMES = {"m15": 15, "h1": 60, "h4": 240}
CUTOFF_DEFAULT = "2026-08-28 23:57:00"


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m1", required=True, type=Path)
    parser.add_argument("--r7g-events", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--cutoff", default=CUTOFF_DEFAULT)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class TimeframeSeries:
    bars: list[Bar] = field(default_factory=list)
    true_ranges: list[float] = field(default_factory=list)
    atr180: list[float] = field(default_factory=list)

    def append(self, bar: Bar) -> None:
        if self.bars:
            previous = self.bars[-1]
            true_range = max(
                bar.high - bar.low,
                abs(bar.high - previous.close),
                abs(bar.low - previous.close),
            )
        else:
            true_range = bar.high - bar.low
        self.bars.append(bar)
        self.true_ranges.append(float(true_range))
        index = len(self.bars) - 1
        if index < 179:
            self.atr180.append(float("nan"))
        elif index == 179:
            self.atr180.append(float(np.mean(self.true_ranges[:180])))
        else:
            self.atr180.append(
                (self.atr180[-1] * 179.0 + true_range) / 180.0
            )


def source_value(bar: Bar, source: str) -> float:
    if source == "close":
        return float(bar.close)
    if source == "oc2":
        return 0.5 * (float(bar.open) + float(bar.close))
    raise ValueError(source)


def average(values: list[float], kind: str) -> float:
    if kind == "sma":
        return float(np.mean(values))
    if kind == "wma":
        weights = np.arange(1.0, len(values) + 1.0)
        return float(np.dot(np.asarray(values, dtype=float), weights) / weights.sum())
    raise ValueError(kind)


def ribbon_snapshot(
    series: TimeframeSeries,
    source: str,
    length: int,
    kind: str,
    direction: int,
    offset: int = 0,
) -> dict[str, float] | None:
    index = len(series.bars) - 1 - offset
    if index < length - 1:
        return None
    atr = float(series.atr180[index])
    if not math.isfinite(atr) or atr <= 0.0:
        return None
    values = [source_value(bar, source) for bar in series.bars[: index + 1]]
    ma_values = [average(values[-period:], kind) for period in range(1, length + 1)]
    current = values[-1]
    slower = ma_values[1:]
    if direction > 0:
        support = float(np.mean([current > value for value in slower]))
        order = float(np.mean([left > right for left, right in zip(ma_values[:-1], ma_values[1:])]))
    else:
        support = float(np.mean([current < value for value in slower]))
        order = float(np.mean([left < right for left, right in zip(ma_values[:-1], ma_values[1:])]))
    sign = 1.0 if direction > 0 else -1.0
    return {
        "support": support,
        "order": order,
        "span_atr": sign * (ma_values[0] - ma_values[-1]) / atr,
        "edge_atr": sign * (current - ma_values[-1]) / atr,
        "center": 0.5 * (ma_values[0] + ma_values[-1]),
        "atr": atr,
    }


class MAForwardState:
    def __init__(self, selected: dict[datetime, dict[str, object]]) -> None:
        self.selected = selected
        self.aggregators = {
            name: BarAggregator(minutes) for name, minutes in TIMEFRAMES.items()
        }
        self.series = {name: TimeframeSeries() for name in TIMEFRAMES}
        self.rows: list[dict[str, object]] = []

    def _m15_state(
        self, source: str, kind: str, direction: int
    ) -> dict[str, float] | None:
        current = ribbon_snapshot(
            self.series["m15"], source, 60, kind, direction
        )
        if current is None:
            return None
        support_history: list[float] = []
        for offset in range(15, -1, -1):
            snapshot = ribbon_snapshot(
                self.series["m15"], source, 60, kind, direction, offset
            )
            if snapshot is not None:
                support_history.append(float(snapshot["support"]))
        deterioration = (
            max(support_history) - float(current["support"])
            if support_history
            else float("nan")
        )
        return {
            "support": float(current["support"]),
            "order": float(current["order"]),
            "deterioration4h": float(deterioration),
        }

    def _record(self, decision: datetime) -> None:
        event = self.selected.get(decision)
        if event is None:
            return
        direction = int(event["dir_num"])
        h4_current = ribbon_snapshot(
            self.series["h4"], "oc2", 20, "wma", direction
        )
        h4_previous = ribbon_snapshot(
            self.series["h4"], "oc2", 20, "wma", direction, 1
        )
        h1_current = ribbon_snapshot(
            self.series["h1"], "oc2", 20, "wma", direction
        )
        m15_sma_close = self._m15_state("close", "sma", direction)
        m15_sma_oc2 = self._m15_state("oc2", "sma", direction)
        m15_wma_oc2 = self._m15_state("oc2", "wma", direction)
        required = (
            h4_current,
            h4_previous,
            h1_current,
            m15_sma_close,
            m15_sma_oc2,
            m15_wma_oc2,
        )
        if any(value is None for value in required):
            raise ValueError(f"insufficient causal MA history at {decision}")
        assert h4_current is not None and h4_previous is not None
        assert h1_current is not None
        assert m15_sma_close is not None
        assert m15_sma_oc2 is not None
        assert m15_wma_oc2 is not None
        sign = 1.0 if direction > 0 else -1.0
        row = dict(event)
        row.update(
            {
                "h4_wma_oc2_n20_slope_atr": sign
                * (h4_current["center"] - h4_previous["center"])
                / h4_current["atr"],
                "h4_wma_oc2_n20_span_atr": h4_current["span_atr"],
                "h1_wma_oc2_n20_edge_atr": h1_current["edge_atr"],
                "h1_wma_oc2_n20_span_atr": h1_current["span_atr"],
            }
        )
        for prefix, state in (
            ("m15_sma_close_n60", m15_sma_close),
            ("m15_sma_oc2_n60", m15_sma_oc2),
            ("m15_wma_oc2_n60", m15_wma_oc2),
        ):
            for key, value in state.items():
                row[f"{prefix}_{key}"] = value
        self.rows.append(row)

    def push(self, ts: datetime, o: float, h: float, l: float, c: float) -> None:
        h4_done: Bar | None = None
        for name in ("m15", "h1", "h4"):
            done = self.aggregators[name].push(ts, o, h, l, c)
            if done is not None:
                self.series[name].append(done)
                if name == "h4":
                    h4_done = done
        if h4_done is not None:
            self._record(h4_done.start + timedelta(hours=4))


def load_selected_events(path: Path, cutoff: pd.Timestamp) -> pd.DataFrame:
    events = pd.read_csv(path)
    required = {
        "decision",
        "event",
        "dir",
        "k",
        "r4_weight",
        "r7g_weight",
        "entry_chart",
        "stop",
    }
    if not required.issubset(events.columns):
        raise ValueError(f"R7G event schema missing: {sorted(required - set(events.columns))}")
    events["decision"] = pd.to_datetime(
        events["decision"], format="%Y.%m.%d %H:%M", errors="raise"
    )
    selected = events[
        (events["decision"] > cutoff) & (events["r7g_weight"] > 0)
    ].copy()
    selected["dir_num"] = selected["dir"].map({"LONG": 1, "SHORT": -1})
    if selected["dir_num"].isna().any():
        raise ValueError("unknown direction in selected R7G events")
    if selected["decision"].duplicated().any():
        raise ValueError("duplicate selected decision timestamps")
    return selected.sort_values("decision").reset_index(drop=True)


def stream_m1(
    path: Path,
    ma_state: MAForwardState,
    universe: UniverseBuilder,
) -> tuple[int, datetime, datetime]:
    count = 0
    first: datetime | None = None
    previous: datetime | None = None
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        expected = {"<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>"}
        if not expected.issubset(reader.fieldnames or []):
            raise ValueError(f"unexpected M1 schema: {reader.fieldnames}")
        for row in reader:
            ts = datetime.strptime(f"{row['<DATE>']} {row['<TIME>']}", SOURCE_TS)
            if previous is not None and ts <= previous:
                raise ValueError(f"M1 is not strictly chronological at {ts}")
            values = tuple(float(row[name]) for name in ("<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>"))
            ma_state.push(ts, *values)
            universe.push_m1(ts, *values)
            first = ts if first is None else first
            previous = ts
            count += 1
    if first is None or previous is None:
        raise ValueError("M1 source contains no rows")
    return count, first, previous


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    cutoff = pd.Timestamp(args.cutoff)
    selected = load_selected_events(args.r7g_events, cutoff)
    selected_records = {
        row["decision"].to_pydatetime(): row
        for row in selected.to_dict("records")
    }
    ma_state = MAForwardState(selected_records)
    universe = UniverseBuilder()
    m1_rows, m1_first, m1_last = stream_m1(args.m1, ma_state, universe)

    state = pd.DataFrame(ma_state.rows)
    if len(state) != len(selected):
        missing = sorted(set(selected["decision"]) - set(pd.to_datetime(state.get("decision", []))))
        raise ValueError(
            f"MA-state coverage mismatch: selected={len(selected)} state={len(state)} missing={missing[:5]}"
        )

    outcomes = pd.DataFrame(universe.records)
    outcome_columns = [
        "signal_id",
        "decision",
        "dir",
        "rid",
        "k",
        "entry",
        "stop",
        "exit_time",
        "exit",
        "exit_reason",
        "stop_hit",
        "pnl",
        "R",
        "L",
        "run_end_decision",
        "label_available_at",
    ]
    outcomes = outcomes[outcome_columns].rename(
        columns={
            "dir": "universe_dir",
            "k": "universe_k",
            "entry": "universe_entry",
            "stop": "universe_stop",
        }
    )
    outcomes["decision"] = pd.to_datetime(outcomes["decision"])
    ledger = state.merge(outcomes, on="decision", how="left", validate="one_to_one")
    ledger["direction_match"] = ledger["dir_num"] == ledger["universe_dir"]
    ledger["k_match"] = ledger["k"].astype(float) == ledger["universe_k"].astype(float)
    ledger["entry_abs_diff"] = (
        ledger["entry_chart"].astype(float) - ledger["universe_entry"].astype(float)
    ).abs()
    ledger["stop_abs_diff"] = (
        ledger["stop"].astype(float) - ledger["universe_stop"].astype(float)
    ).abs()
    ledger["outcome_available"] = ledger["label_available_at"].notna()

    feature_columns = [
        column
        for column in ledger.columns
        if column.startswith(("h4_", "h1_", "m15_"))
    ]
    output_csv = args.out_dir / "V10_MA_BAND_FORWARD_STATE_LEDGER.csv"
    ledger.to_csv(output_csv, index=False, date_format="%Y-%m-%d %H:%M:%S")

    audit = {
        "ok": bool(
            ledger["direction_match"].all()
            and ledger["k_match"].all()
            and ledger[feature_columns].notna().all().all()
        ),
        "authority": "FORWARD SHADOW OBSERVATION ONLY / NO TRADE AUTHORITY",
        "cutoff": cutoff.isoformat(sep=" "),
        "m1_source": str(args.m1.resolve()),
        "m1_sha256": sha256_file(args.m1),
        "m1_rows": m1_rows,
        "m1_first": m1_first.isoformat(sep=" "),
        "m1_last": m1_last.isoformat(sep=" "),
        "r7g_events": str(args.r7g_events.resolve()),
        "r7g_events_sha256": sha256_file(args.r7g_events),
        "selected_candidates": int(len(ledger)),
        "feature_complete_candidates": int(ledger[feature_columns].notna().all(axis=1).sum()),
        "outcome_available_candidates": int(ledger["outcome_available"].sum()),
        "hard_stops_with_available_outcome": int(
            pd.to_numeric(
                ledger.loc[ledger["outcome_available"], "stop_hit"], errors="coerce"
            ).fillna(0).sum()
        ),
        "direction_mismatches": int((~ledger["direction_match"]).sum()),
        "k_mismatches": int((~ledger["k_match"]).sum()),
        "max_entry_abs_diff": float(ledger["entry_abs_diff"].max()),
        "max_stop_abs_diff": float(ledger["stop_abs_diff"].max()),
        "features": feature_columns,
        "threshold_scan": False,
        "score_created": False,
        "order_changes": False,
        "output": str(output_csv.resolve()),
        "output_sha256": sha256_file(output_csv),
    }
    audit_path = args.out_dir / "V10_MA_BAND_FORWARD_AUDIT.json"
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
