"""Test liquidity-relative Wave Candle information against V10 R7G Children.

This is a consumed-data representation diagnostic with no trade authority.
It rebuilds H1/H4 2-left/2-right swing-liquidity objects in one chronological
M1 pass, records which pre-existing objects the completed pre-entry H4 candle
consumed, snapshots the still-active destination topology at the decision, and
then asks whether Wave settlement relative to the consumed boundary adds stop
information beyond the outer HA shell and liquidity topology.

The Wave reference uses a semantic timeframe hierarchy rather than allowing a
denser H1 object to hide a consumed H4 object: use the terminal consumed H4
boundary when one exists, otherwise use the terminal consumed H1 boundary.

The three fixed comparison layers are:

1. outer H4/FAST-HA shell only;
2. outer shell plus arrival/destination topology;
3. layer 2 plus Wave settlement relative to the consumed liquidity boundary.

No threshold, feature, or model produced here is a V11 trading rule.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss

from analyze_v11_wave_edge import (
    ACTIVE_START,
    QUANTILES,
    TEST_YEARS,
    load_m1,
    load_selected_children,
    max_true_streak,
    model_pipeline,
    safe_auc,
    sha256_file,
)


OUTER_FEATURES = [
    "k",
    "r7g_weight",
    "outer_ha_body_aligned_atr",
    "outer_range_atr",
    "outer_close_location_aligned",
]

TOPOLOGY_FEATURES = [
    "same_consumed_count",
    "opposite_consumed_count",
    "same_h4_consumed",
    "opposite_h4_consumed",
    "nearest_same_distance_atr",
    "nearest_opposite_distance_atr",
    "destination_log_ratio",
    "same_destination_missing",
    "opposite_destination_missing",
    "nearest_same_is_h4",
    "nearest_opposite_is_h4",
]

LIQUIDITY_WAVE_FEATURES = [
    "liq_raw_close_beyond_atr",
    "liq_density_peak_beyond_atr",
    "liq_settlement_beyond_fraction",
    "liq_density_beyond_fraction",
]

MODEL_DEFINITIONS = {
    "OUTER_ONLY": OUTER_FEATURES,
    "OUTER_PLUS_TOPOLOGY": OUTER_FEATURES + TOPOLOGY_FEATURES,
    "OUTER_PLUS_TOPOLOGY_WAVE": OUTER_FEATURES
    + TOPOLOGY_FEATURES
    + LIQUIDITY_WAVE_FEATURES,
}


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m1", required=True, type=Path)
    parser.add_argument("--universe", required=True, type=Path)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


@dataclass
class LiquidityObject:
    object_id: str
    timeframe: str
    side: int
    price: float
    source_time: pd.Timestamp
    known_at: pd.Timestamp


class CausalSwingState:
    """Exact V9 H1/H4 2L/2R swing semantics, replayed chronologically."""

    def __init__(self, hours: int) -> None:
        self.hours = hours
        self.current: dict[str, object] | None = None
        self.recent: list[dict[str, object]] = []
        self.active: dict[str, LiquidityObject] = {}

    def bucket(self, ts: pd.Timestamp) -> pd.Timestamp:
        return ts.floor(f"{self.hours}h")

    def due_before(self, ts: pd.Timestamp) -> bool:
        if self.current is None:
            return False
        start = pd.Timestamp(self.current["start"])
        return ts >= start + pd.Timedelta(hours=self.hours) and self.bucket(ts) != start

    def finalize(self) -> list[LiquidityObject]:
        if self.current is None:
            return []
        self.recent.append(self.current)
        self.current = None
        self.recent = self.recent[-5:]
        if len(self.recent) < 5:
            return []

        bars = self.recent[-5:]
        center = bars[2]
        left = bars[:2]
        right = bars[3:]
        known_at = pd.Timestamp(bars[-1]["start"]) + pd.Timedelta(hours=self.hours)
        source_time = pd.Timestamp(center["start"])
        timeframe = f"H{self.hours}"
        born: list[LiquidityObject] = []

        if float(center["high"]) > max(float(x["high"]) for x in left) and float(
            center["high"]
        ) >= max(float(x["high"]) for x in right):
            obj = LiquidityObject(
                object_id=f"{timeframe}_BSL_{source_time:%Y%m%d_%H%M}",
                timeframe=timeframe,
                side=1,
                price=float(center["high"]),
                source_time=source_time,
                known_at=known_at,
            )
            self.active[obj.object_id] = obj
            born.append(obj)

        if float(center["low"]) < min(float(x["low"]) for x in left) and float(
            center["low"]
        ) <= min(float(x["low"]) for x in right):
            obj = LiquidityObject(
                object_id=f"{timeframe}_SSL_{source_time:%Y%m%d_%H%M}",
                timeframe=timeframe,
                side=-1,
                price=float(center["low"]),
                source_time=source_time,
                known_at=known_at,
            )
            self.active[obj.object_id] = obj
            born.append(obj)
        return born

    def update(self, ts: pd.Timestamp, o: float, h: float, l: float, c: float) -> None:
        start = self.bucket(ts)
        if self.current is None:
            self.current = {
                "start": start,
                "open": o,
                "high": h,
                "low": l,
                "close": c,
            }
            return
        if pd.Timestamp(self.current["start"]) != start:
            raise RuntimeError("bar must be finalized before a new bucket is updated")
        self.current["high"] = max(float(self.current["high"]), h)
        self.current["low"] = min(float(self.current["low"]), l)
        self.current["close"] = c

    def raid(self, high: float, low: float) -> list[LiquidityObject]:
        hits: list[LiquidityObject] = []
        for object_id, obj in list(self.active.items()):
            if (obj.side == 1 and obj.price < high) or (obj.side == -1 and obj.price > low):
                hits.append(obj)
                del self.active[object_id]
        return hits


class CausalMarketBuilder:
    """Build completed M5/H4 numeric observations during the M1 reveal."""

    def __init__(self) -> None:
        self.current_m5: dict[str, object] | None = None
        self.current_h4: dict[str, object] | None = None
        self.m5_rows: list[dict[str, object]] = []
        self.h4_rows: list[dict[str, object]] = []
        self.previous_h4_close = np.nan
        self.previous_atr = np.nan
        self.true_ranges: list[float] = []
        self.previous_fast_open = np.nan
        self.previous_fast_close = np.nan

    @staticmethod
    def _update_bar(
        current: dict[str, object] | None,
        start: pd.Timestamp,
        o: float,
        h: float,
        l: float,
        c: float,
    ) -> dict[str, object]:
        if current is None:
            return {
                "start": start,
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "rows": 1,
            }
        if pd.Timestamp(current["start"]) != start:
            raise RuntimeError("market bar must be finalized before new bucket")
        current["high"] = max(float(current["high"]), h)
        current["low"] = min(float(current["low"]), l)
        current["close"] = c
        current["rows"] = int(current["rows"]) + 1
        return current

    def _finalize_m5(self) -> None:
        if self.current_m5 is None:
            return
        bar = self.current_m5
        self.m5_rows.append(
            {
                "m5_start": pd.Timestamp(bar["start"]),
                "h4_start": pd.Timestamp(bar["start"]).floor("4h"),
                "open": float(bar["open"]),
                "high": float(bar["high"]),
                "low": float(bar["low"]),
                "close": float(bar["close"]),
                "rows": int(bar["rows"]),
            }
        )
        self.current_m5 = None

    def _finalize_h4(self) -> None:
        if self.current_h4 is None:
            return
        bar = self.current_h4
        o = float(bar["open"])
        h = float(bar["high"])
        l = float(bar["low"])
        c = float(bar["close"])
        if np.isfinite(self.previous_h4_close):
            true_range = max(h - l, abs(h - self.previous_h4_close), abs(l - self.previous_h4_close))
        else:
            true_range = h - l
        causal_scale = self.previous_atr
        self.true_ranges.append(float(true_range))
        if len(self.true_ranges) == 180:
            atr180 = float(np.mean(self.true_ranges))
        elif len(self.true_ranges) > 180:
            atr180 = (self.previous_atr * 179.0 + true_range) / 180.0
        else:
            atr180 = np.nan

        fast_close = (o + h + l + 2.0 * c) / 5.0
        if np.isfinite(self.previous_fast_open):
            fast_open = 0.25 * self.previous_fast_open + 0.75 * self.previous_fast_close
        else:
            fast_open = 0.5 * (o + c)
        self.h4_rows.append(
            {
                "h4_start": pd.Timestamp(bar["start"]),
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "m1_rows": int(bar["rows"]),
                "atr180": atr180,
                "causal_scale": causal_scale,
                "fast_ha_open": fast_open,
                "fast_ha_close": fast_close,
                "fast_dir": 1 if fast_close >= fast_open else -1,
            }
        )
        self.previous_h4_close = c
        self.previous_atr = atr180
        self.previous_fast_open = fast_open
        self.previous_fast_close = fast_close
        self.current_h4 = None

    def finalize_due(self, ts: pd.Timestamp) -> None:
        m5_start = ts.floor("5min")
        h4_start = ts.floor("4h")
        if self.current_m5 is not None and pd.Timestamp(self.current_m5["start"]) != m5_start:
            self._finalize_m5()
        if self.current_h4 is not None and pd.Timestamp(self.current_h4["start"]) != h4_start:
            self._finalize_h4()

    def update(self, ts: pd.Timestamp, o: float, h: float, l: float, c: float) -> None:
        self.current_m5 = self._update_bar(
            self.current_m5, ts.floor("5min"), o, h, l, c
        )
        self.current_h4 = self._update_bar(
            self.current_h4, ts.floor("4h"), o, h, l, c
        )

    def frames(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        return pd.DataFrame(self.h4_rows), pd.DataFrame(self.m5_rows)


def topology_snapshot(
    states: list[CausalSwingState], direction: int, reference_price: float
) -> dict[str, object]:
    active = [obj for state in states for obj in state.active.values()]
    if direction == 1:
        same = [obj for obj in active if obj.side == 1 and obj.price > reference_price]
        opposite = [obj for obj in active if obj.side == -1 and obj.price < reference_price]
        nearest_same = min(same, key=lambda x: x.price) if same else None
        nearest_opposite = max(opposite, key=lambda x: x.price) if opposite else None
    else:
        same = [obj for obj in active if obj.side == -1 and obj.price < reference_price]
        opposite = [obj for obj in active if obj.side == 1 and obj.price > reference_price]
        nearest_same = max(same, key=lambda x: x.price) if same else None
        nearest_opposite = min(opposite, key=lambda x: x.price) if opposite else None

    return {
        "reference_price": reference_price,
        "nearest_same_price": np.nan if nearest_same is None else nearest_same.price,
        "nearest_same_tf": None if nearest_same is None else nearest_same.timeframe,
        "nearest_opposite_price": np.nan if nearest_opposite is None else nearest_opposite.price,
        "nearest_opposite_tf": None if nearest_opposite is None else nearest_opposite.timeframe,
        "active_same_count": len(same),
        "active_opposite_count": len(opposite),
    }


def replay_liquidity(
    m1: pd.DataFrame, selected: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, int]]:
    pending = sorted(
        (
            pd.Timestamp(child.decision),
            str(child.signal_id),
            int(child.dir),
        )
        for child in selected.itertuples(index=False)
    )
    pending_index = 0

    h1 = CausalSwingState(1)
    h4 = CausalSwingState(4)
    states = [h1, h4]
    market = CausalMarketBuilder()
    consumption_rows: list[dict[str, object]] = []
    object_rows: list[dict[str, object]] = []
    snapshot_rows: list[dict[str, object]] = []
    objects_born = 0
    last_close = np.nan

    for row in m1.itertuples(index=False):
        ts = pd.Timestamp(row.ts)
        for state in states:
            if state.due_before(ts):
                born = state.finalize()
                objects_born += len(born)
                object_rows.extend(
                    {
                        "object_id": obj.object_id,
                        "timeframe": obj.timeframe,
                        "side": obj.side,
                        "price": obj.price,
                        "source_time": obj.source_time,
                        "known_at": obj.known_at,
                    }
                    for obj in born
                )
        market.finalize_due(ts)

        # A small set of broker H4 decisions is stamped 00:00 while the next
        # available raw M1 is 01:00.  No price exists in between.  Snapshot all
        # due decisions immediately before revealing that first available row.
        while pending_index < len(pending) and pending[pending_index][0] <= ts:
            decision, signal_id, direction = pending[pending_index]
            if np.isfinite(last_close):
                snap = topology_snapshot(states, direction, float(last_close))
                snap.update(
                    {
                        "signal_id": signal_id,
                        "decision": decision,
                        "snapshot_observed_at": ts,
                        "snapshot_lag_minutes": (ts - decision).total_seconds() / 60.0,
                    }
                )
                snapshot_rows.append(snap)
            pending_index += 1

        for state in states:
            state.update(ts, float(row.open), float(row.high), float(row.low), float(row.close))
        market.update(ts, float(row.open), float(row.high), float(row.low), float(row.close))
        for state in states:
            for obj in state.raid(float(row.high), float(row.low)):
                consumption_rows.append(
                    {
                        "object_id": obj.object_id,
                        "timeframe": obj.timeframe,
                        "side": obj.side,
                        "price": obj.price,
                        "source_time": obj.source_time,
                        "known_at": obj.known_at,
                        "consumed_at": ts,
                        "consume_h4_start": ts.floor("4h"),
                    }
                )
        last_close = float(row.close)

    audit = {
        "objects_born": int(objects_born),
        "objects_consumed": int(len(consumption_rows)),
        "decision_snapshots": int(len(snapshot_rows)),
        "selected_decisions": int(len(selected)),
        "pending_decisions_after_last_m1": int(len(pending) - pending_index),
    }
    h4_frame, m5_frame = market.frames()
    objects = pd.DataFrame(object_rows)
    consumed_times = (
        pd.DataFrame(consumption_rows)[["object_id", "consumed_at"]]
        if consumption_rows
        else pd.DataFrame(columns=["object_id", "consumed_at"])
    )
    objects = objects.merge(consumed_times, on="object_id", how="left", validate="one_to_one")
    audit["completed_h4_bars"] = int(len(h4_frame))
    audit["completed_m5_bars"] = int(len(m5_frame))
    return (
        pd.DataFrame(consumption_rows),
        objects,
        pd.DataFrame(snapshot_rows),
        h4_frame,
        m5_frame,
        audit,
    )


def density_relative_coordinates(
    closes: np.ndarray,
    raw_low: float,
    raw_high: float,
    raw_close: float,
    boundary: float,
    scale: float,
    direction: int,
) -> dict[str, float | str]:
    empty = {
        "liq_raw_close_beyond_atr": np.nan,
        "liq_density_peak_beyond_atr": np.nan,
        "liq_settlement_beyond_fraction": np.nan,
        "liq_density_beyond_fraction": np.nan,
        "liq_acceptance_state": "NO_SAME_SIDE_ARRIVAL",
    }
    if len(closes) == 0 or not np.isfinite(scale) or scale <= 0.0 or raw_high <= raw_low:
        return empty

    prices = np.linspace(raw_low, raw_high, 49)
    span = raw_high - raw_low
    bandwidth = max(span / 48.0, float(np.std(closes, ddof=0)) * 0.10, 0.02)
    z = (prices[:, None] - closes[None, :]) / bandwidth
    density = np.exp(-0.5 * z * z).mean(axis=1)
    density_sum = float(density.sum())
    peak = float(prices[int(np.argmax(density))])
    raw_beyond = direction * (raw_close - boundary) / scale
    peak_beyond = direction * (peak - boundary) / scale
    settlement_fraction = float(np.mean(direction * (closes - boundary) >= 0.0))
    beyond = direction * (prices - boundary) >= 0.0
    density_fraction = float(density[beyond].sum() / density_sum) if density_sum > 0.0 else np.nan
    if raw_beyond >= 0.0 and peak_beyond >= 0.0:
        acceptance = "ACCEPTED"
    elif raw_beyond < 0.0 and peak_beyond < 0.0:
        acceptance = "RETURNED"
    else:
        acceptance = "SPLIT_UNRESOLVED"
    return {
        "liq_raw_close_beyond_atr": raw_beyond,
        "liq_density_peak_beyond_atr": peak_beyond,
        "liq_settlement_beyond_fraction": settlement_fraction,
        "liq_density_beyond_fraction": density_fraction,
        "liq_acceptance_state": acceptance,
    }


def build_child_ledger(
    selected: pd.DataFrame,
    h4: pd.DataFrame,
    m5: pd.DataFrame,
    consumptions: pd.DataFrame,
    snapshots: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    h4_state = h4.set_index("h4_start")
    closes_by_h4 = {
        key: group.sort_values("m5_start")["close"].to_numpy(dtype=float)
        for key, group in m5.groupby("h4_start", sort=True)
    }
    consumed_by_h4 = {
        key: group.copy()
        for key, group in consumptions.groupby("consume_h4_start", sort=True)
    }
    snapshot_by_signal = snapshots.set_index("signal_id")
    rows: list[dict[str, object]] = []
    fast_direction_mismatches = 0

    for child in selected.itertuples(index=False):
        wave_start = pd.Timestamp(child.decision) - pd.Timedelta(hours=4)
        if (
            wave_start not in h4_state.index
            or wave_start not in closes_by_h4
            or str(child.signal_id) not in snapshot_by_signal.index
        ):
            continue
        state = h4_state.loc[wave_start]
        scale = float(state["causal_scale"])
        if not np.isfinite(scale) or scale <= 0.0:
            continue
        direction = int(child.dir)
        if int(state["fast_dir"]) != direction:
            fast_direction_mismatches += 1
        snap = snapshot_by_signal.loc[str(child.signal_id)]
        arrivals = consumed_by_h4.get(wave_start, pd.DataFrame())
        if arrivals.empty:
            same = arrivals
            opposite = arrivals
        else:
            same = arrivals[arrivals["side"] == direction]
            opposite = arrivals[arrivals["side"] == -direction]
        same_h4 = same[same["timeframe"] == "H4"] if not same.empty else same
        same_h1 = same[same["timeframe"] == "H1"] if not same.empty else same
        primary = same_h4 if not same_h4.empty else same_h1
        if primary.empty:
            boundary = np.nan
            boundary_tf = None
        elif direction == 1:
            terminal = primary.loc[primary["price"].idxmax()]
            boundary = float(terminal["price"])
            boundary_tf = str(terminal["timeframe"])
        else:
            terminal = primary.loc[primary["price"].idxmin()]
            boundary = float(terminal["price"])
            boundary_tf = str(terminal["timeframe"])

        nearest_same = float(snap["nearest_same_price"])
        nearest_opposite = float(snap["nearest_opposite_price"])
        reference = float(snap["reference_price"])
        d_same = (
            direction * (nearest_same - reference) / scale
            if np.isfinite(nearest_same)
            else np.nan
        )
        d_opposite = (
            -direction * (nearest_opposite - reference) / scale
            if np.isfinite(nearest_opposite)
            else np.nan
        )
        log_ratio = (
            float(np.log(d_same / d_opposite))
            if np.isfinite(d_same) and np.isfinite(d_opposite) and d_same > 0.0 and d_opposite > 0.0
            else np.nan
        )
        span = float(state["high"] - state["low"])
        close_location = (
            0.0
            if span <= 0.0
            else 2.0 * (float(state["fast_ha_close"]) - float(state["low"])) / span - 1.0
        )
        row = {
            "signal_id": child.signal_id,
            "decision": child.decision,
            "year": child.year,
            "dir": child.dir,
            "k": child.k,
            "rid": child.rid,
            "r7g_weight": child.r7g_weight,
            "entry": child.entry,
            "stop": child.stop,
            "entry_time": child.entry_time,
            "exit_time": child.exit_time,
            "label_available_at": child.label_available_at,
            "stop_hit": child.stop_hit,
            "R": child.R,
            "pnl": child.pnl,
            "L": child.L,
            "wave_start": wave_start,
            "m5_count": int(len(closes_by_h4[wave_start])),
            "fast_direction_match": int(int(state["fast_dir"]) == direction),
            "outer_ha_body_aligned_atr": direction
            * (float(state["fast_ha_close"]) - float(state["fast_ha_open"]))
            / scale,
            "outer_range_atr": span / scale,
            "outer_close_location_aligned": direction * close_location,
            "raw_h4_open": float(state["open"]),
            "raw_h4_high": float(state["high"]),
            "raw_h4_low": float(state["low"]),
            "raw_h4_close": float(state["close"]),
            "causal_atr180": scale,
            "same_consumed_count": int(len(same)),
            "opposite_consumed_count": int(len(opposite)),
            "same_h4_consumed": int(not same_h4.empty),
            "opposite_h4_consumed": int(
                not opposite.empty and (opposite["timeframe"] == "H4").any()
            ),
            "terminal_same_boundary": boundary,
            "terminal_same_boundary_tf": boundary_tf,
            "nearest_same_price": nearest_same,
            "nearest_opposite_price": nearest_opposite,
            "nearest_same_distance_atr": d_same,
            "nearest_opposite_distance_atr": d_opposite,
            "destination_log_ratio": log_ratio,
            "same_destination_missing": int(not np.isfinite(nearest_same)),
            "opposite_destination_missing": int(not np.isfinite(nearest_opposite)),
            "nearest_same_is_h4": int(str(snap["nearest_same_tf"]) == "H4"),
            "nearest_opposite_is_h4": int(str(snap["nearest_opposite_tf"]) == "H4"),
            "active_same_count": int(snap["active_same_count"]),
            "active_opposite_count": int(snap["active_opposite_count"]),
        }
        row.update(
            density_relative_coordinates(
                closes_by_h4[wave_start],
                float(state["low"]),
                float(state["high"]),
                float(state["close"]),
                boundary,
                scale,
                direction,
            )
            if np.isfinite(boundary)
            else density_relative_coordinates(
                np.array([], dtype=float), 0.0, 0.0, 0.0, 0.0, scale, direction
            )
        )
        rows.append(row)
    audit = {
        "ledger_rows": int(len(rows)),
        "fast_direction_mismatches": int(fast_direction_mismatches),
    }
    return pd.DataFrame(rows), audit


def score_outer_years(
    ledger: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    scored_parts: list[pd.DataFrame] = []
    metric_rows: list[dict[str, object]] = []
    threshold_rows: list[dict[str, object]] = []
    for year in TEST_YEARS:
        boundary = pd.Timestamp(f"{year}-01-01")
        train = ledger[
            (ledger["decision"] < boundary) & (ledger["label_available_at"] < boundary)
        ].copy()
        test = ledger[ledger["year"] == year].copy()
        if train.empty or test.empty or train["stop_hit"].nunique() < 2:
            continue
        scored = test.copy()
        for model_name, features in MODEL_DEFINITIONS.items():
            model = model_pipeline(features)
            model.fit(train[features], train["stop_hit"].astype(int))
            train_score = model.predict_proba(train[features])[:, 1]
            test_score = model.predict_proba(test[features])[:, 1]
            score_column = f"score_{model_name.lower()}"
            scored[score_column] = test_score
            y = test["stop_hit"].astype(int)
            metric_rows.append(
                {
                    "test_year": year,
                    "model": model_name,
                    "train_n": int(len(train)),
                    "test_n": int(len(test)),
                    "test_stops": int(y.sum()),
                    "stop_rate": float(y.mean()),
                    "roc_auc": safe_auc(y, test_score),
                    "average_precision": float(average_precision_score(y, test_score)),
                    "brier": float(brier_score_loss(y, test_score)),
                }
            )
            for quantile in QUANTILES:
                threshold_rows.append(
                    {
                        "test_year": year,
                        "model": model_name,
                        "quantile": quantile,
                        "threshold": float(np.quantile(train_score, quantile)),
                        "score_column": score_column,
                    }
                )
        scored_parts.append(scored)
    return (
        pd.concat(scored_parts, ignore_index=True),
        pd.DataFrame(metric_rows),
        pd.DataFrame(threshold_rows),
    )


def economic_policy_rows(
    ledger: pd.DataFrame, scored: pd.DataFrame, thresholds: pd.DataFrame
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for threshold_row in thresholds.itertuples(index=False):
        year = int(threshold_row.test_year)
        base = ledger[ledger["year"] == year].copy()
        score_map = scored[scored["year"] == year].set_index("signal_id")[
            str(threshold_row.score_column)
        ]
        base["score"] = base["signal_id"].map(score_map)
        reject = base["score"].ge(float(threshold_row.threshold))
        base["policy_R"] = np.where(reject, 0.0, base["R"])
        base["policy_stop"] = base["stop_hit"].astype(bool) & ~reject
        weight = base["r7g_weight"].astype(float)
        positive = base["R"] > 0.0
        tail = positive & (base["L"] >= 6)
        baseline_r = float((base["R"] * weight).sum())
        policy_r = float((base["policy_R"] * weight).sum())
        baseline_positive = float((base.loc[positive, "R"] * weight[positive]).sum())
        kept_positive = float(
            (base.loc[positive, "policy_R"].clip(lower=0.0) * weight[positive]).sum()
        )
        baseline_tail = float((base.loc[tail, "R"] * weight[tail]).sum())
        kept_tail = float(
            (base.loc[tail, "policy_R"].clip(lower=0.0) * weight[tail]).sum()
        )
        ordered = base.sort_values("decision")
        rows.append(
            {
                "test_year": year,
                "model": threshold_row.model,
                "quantile": float(threshold_row.quantile),
                "children": int(len(base)),
                "rejections": int(reject.sum()),
                "baseline_stops": int(base["stop_hit"].sum()),
                "policy_stops": int(base["policy_stop"].sum()),
                "stops_prevented": int((base["stop_hit"].astype(bool) & reject).sum()),
                "baseline_max_stop_streak": max_true_streak(ordered["stop_hit"]),
                "policy_max_stop_streak": max_true_streak(ordered["policy_stop"]),
                "baseline_weighted_R": baseline_r,
                "policy_weighted_R": policy_r,
                "delta_weighted_R": policy_r - baseline_r,
                "positive_R_retention": kept_positive / baseline_positive
                if baseline_positive > 0.0
                else np.nan,
                "L6plus_positive_R_retention": kept_tail / baseline_tail
                if baseline_tail > 0.0
                else np.nan,
            }
        )
    return pd.DataFrame(rows)


def descriptive_rows(ledger: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    cuts: list[tuple[str, list[str]]] = [
        ("ACCEPTANCE_STATE", ["liq_acceptance_state"]),
        ("ACCEPTANCE_BY_TF", ["liq_acceptance_state", "terminal_same_boundary_tf"]),
        ("H4_ARRIVAL", ["same_h4_consumed"]),
        ("H4_ARRIVAL_STATE", ["same_h4_consumed", "liq_acceptance_state"]),
        ("TOPOLOGY_MISSING", ["same_destination_missing", "opposite_destination_missing"]),
    ]
    for cut_name, keys in cuts:
        period_frames = [("POOLED", ledger)]
        period_frames.extend(
            (str(int(year)), group) for year, group in ledger.groupby("year", sort=True)
        )
        period_frames.extend(
            (f"{int(year)}_{'LONG' if int(direction) > 0 else 'SHORT'}", group)
            for (year, direction), group in ledger.groupby(["year", "dir"], sort=True)
        )
        for period, period_frame in period_frames:
            for key_values, group in period_frame.groupby(keys, dropna=False, sort=True):
                if not isinstance(key_values, tuple):
                    key_values = (key_values,)
                weight = group["r7g_weight"].astype(float)
                rows.append(
                    {
                        "cut": cut_name,
                        "period": period,
                        "group": "|".join(
                            f"{key}={value}" for key, value in zip(keys, key_values)
                        ),
                        "n": int(len(group)),
                        "stops": int(group["stop_hit"].sum()),
                        "stop_rate": float(group["stop_hit"].mean()),
                        "weighted_R": float((group["R"] * weight).sum()),
                        "mean_weighted_R_per_child": float((group["R"] * weight).mean()),
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    m1 = load_m1(args.m1)
    selected, selection_audit = load_selected_children(args.universe, args.events)
    consumptions, objects, snapshots, h4, m5, replay_audit = replay_liquidity(m1, selected)
    ledger, ledger_audit = build_child_ledger(selected, h4, m5, consumptions, snapshots)
    scored, metrics, thresholds = score_outer_years(ledger)
    policies = economic_policy_rows(ledger, scored, thresholds)
    descriptive = descriptive_rows(ledger)

    outputs = {
        "child_ledger": args.out_dir / "V11_LIQUIDITY_ARRIVAL_WAVE_LEDGER.csv",
        "liquidity_consumptions": args.out_dir / "V11_LIQUIDITY_CONSUMPTIONS.csv",
        "liquidity_objects": args.out_dir / "V11_LIQUIDITY_OBJECTS.csv",
        "decision_snapshots": args.out_dir / "V11_LIQUIDITY_DECISION_SNAPSHOTS.csv",
        "causal_h4_bars": args.out_dir / "V11_CAUSAL_H4_BARS.csv",
        "model_metrics": args.out_dir / "V11_LIQUIDITY_WAVE_MODEL_COMPARISON.csv",
        "thresholds": args.out_dir / "V11_LIQUIDITY_WAVE_PRIOR_THRESHOLDS.csv",
        "policies": args.out_dir / "V11_LIQUIDITY_WAVE_POLICY_DIAGNOSTIC.csv",
        "descriptive": args.out_dir / "V11_LIQUIDITY_WAVE_DESCRIPTIVE.csv",
    }
    ledger.to_csv(outputs["child_ledger"], index=False, date_format="%Y-%m-%d %H:%M:%S")
    consumptions.to_csv(
        outputs["liquidity_consumptions"], index=False, date_format="%Y-%m-%d %H:%M:%S"
    )
    objects.to_csv(outputs["liquidity_objects"], index=False, date_format="%Y-%m-%d %H:%M:%S")
    snapshots.to_csv(
        outputs["decision_snapshots"], index=False, date_format="%Y-%m-%d %H:%M:%S"
    )
    h4.to_csv(outputs["causal_h4_bars"], index=False, date_format="%Y-%m-%d %H:%M:%S")
    metrics.to_csv(outputs["model_metrics"], index=False)
    thresholds.to_csv(outputs["thresholds"], index=False)
    policies.to_csv(outputs["policies"], index=False)
    descriptive.to_csv(outputs["descriptive"], index=False)

    manifest = {
        "status": "CONSUMED_DATA_LIQUIDITY_RELATIVE_REPRESENTATION_DIAGNOSTIC_ONLY",
        "authority": "NO TRADE OR PRODUCTION AUTHORITY",
        "source_m1": str(args.m1.resolve()),
        "source_m1_sha256": sha256_file(args.m1),
        "source_universe": str(args.universe.resolve()),
        "source_universe_sha256": sha256_file(args.universe),
        "source_events": str(args.events.resolve()),
        "source_events_sha256": sha256_file(args.events),
        "active_start": str(ACTIVE_START),
        "selection_audit": selection_audit,
        "replay_audit": replay_audit,
        "ledger_audit": ledger_audit,
        "test_years": list(TEST_YEARS),
        "fixed_quantiles": list(QUANTILES),
        "liquidity_definition": "causal H1/H4 2-left/2-right swings; strict first penetration",
        "wave_boundary_selection": "terminal consumed H4 same-side boundary; otherwise terminal consumed H1 same-side boundary",
        "models": MODEL_DEFINITIONS,
        "model_family": "RobustScaler(10,90) + LogisticRegression(C=1.0)",
        "training_rule": "decision and label_available_at strictly before test-year boundary",
        "outputs": {name: str(path.resolve()) for name, path in outputs.items()},
        "output_sha256": {name: sha256_file(path) for name, path in outputs.items()},
    }
    manifest_path = args.out_dir / "V11_LIQUIDITY_ARRIVAL_WAVE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(json.dumps(manifest, indent=2))
    print("\nMODEL COMPARISON")
    print(metrics.to_string(index=False))
    print("\nPOLICY DIAGNOSTIC")
    print(policies.to_string(index=False))
    print("\nPOOLED DESCRIPTIVE")
    print(descriptive[descriptive["period"] == "POOLED"].to_string(index=False))


if __name__ == "__main__":
    main()
