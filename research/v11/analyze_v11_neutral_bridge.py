"""Study NHA-to-opposite-PHA authorization as a transition episode.

The unit of analysis is one new FAST-HA run, beginning with its k1 NHA relative
to the prior run.  The script compares immediate authorization with neutral
bridges based on time, later HA confirmation, liquidity semantics, completed
NHA Wave settlement, and forming-H4 Wave settlement.

All inputs are consumed development evidence.  The policy names are diagnostic
counterfactuals, not trading rules or production authority.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


EXPECTED_M1_SHA256 = "626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2"
SOURCE_TS = "%Y.%m.%d %H:%M:%S"


class CausalMarketBuilder:
    """Finalize M5/H4 bars only when the first row of a later bucket arrives."""

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
        high: float,
        low: float,
        close: float,
    ) -> dict[str, object]:
        if current is None:
            return {
                "start": start,
                "open": o,
                "high": high,
                "low": low,
                "close": close,
                "rows": 1,
            }
        if pd.Timestamp(current["start"]) != start:
            raise RuntimeError("market bar must be finalized before new bucket")
        current["high"] = max(float(current["high"]), high)
        current["low"] = min(float(current["low"]), low)
        current["close"] = close
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
        high = float(bar["high"])
        low = float(bar["low"])
        close = float(bar["close"])
        if np.isfinite(self.previous_h4_close):
            true_range = max(
                high - low,
                abs(high - self.previous_h4_close),
                abs(low - self.previous_h4_close),
            )
        else:
            true_range = high - low
        causal_scale = self.previous_atr
        self.true_ranges.append(float(true_range))
        if len(self.true_ranges) == 180:
            atr180 = float(np.mean(self.true_ranges))
        elif len(self.true_ranges) > 180:
            atr180 = (self.previous_atr * 179.0 + true_range) / 180.0
        else:
            atr180 = np.nan
        fast_close = (o + high + low + 2.0 * close) / 5.0
        if np.isfinite(self.previous_fast_open):
            fast_open = 0.25 * self.previous_fast_open + 0.75 * self.previous_fast_close
        else:
            fast_open = 0.5 * (o + close)
        self.h4_rows.append(
            {
                "h4_start": pd.Timestamp(bar["start"]),
                "open": o,
                "high": high,
                "low": low,
                "close": close,
                "m1_rows": int(bar["rows"]),
                "atr180": atr180,
                "causal_scale": causal_scale,
                "fast_ha_open": fast_open,
                "fast_ha_close": fast_close,
                "fast_dir": 1 if fast_close >= fast_open else -1,
            }
        )
        self.previous_h4_close = close
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

    def update(
        self, ts: pd.Timestamp, o: float, high: float, low: float, close: float
    ) -> None:
        self.current_m5 = self._update_bar(
            self.current_m5, ts.floor("5min"), o, high, low, close
        )
        self.current_h4 = self._update_bar(
            self.current_h4, ts.floor("4h"), o, high, low, close
        )

    def frames(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        return pd.DataFrame(self.h4_rows), pd.DataFrame(self.m5_rows)


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m1", required=True, type=Path)
    parser.add_argument("--h4", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def add_ha_stream(
    h4: pd.DataFrame, prefix: str, close_weight: float, alpha: float
) -> pd.DataFrame:
    close = (
        h4["open"] + h4["high"] + h4["low"] + close_weight * h4["close"]
    ) / (3.0 + close_weight)
    ha_open = np.empty(len(h4), dtype=float)
    ha_open[0] = 0.5 * (float(h4.iloc[0]["open"]) + float(h4.iloc[0]["close"]))
    close_values = close.to_numpy(dtype=float)
    for i in range(1, len(h4)):
        ha_open[i] = alpha * ha_open[i - 1] + (1.0 - alpha) * close_values[i - 1]
    h4[f"{prefix}_open"] = ha_open
    h4[f"{prefix}_close"] = close_values
    h4[f"{prefix}_dir"] = np.where(close_values >= ha_open, 1, -1)
    return h4


def build_h4_state(path: Path) -> pd.DataFrame:
    h4 = pd.read_csv(path, parse_dates=["h4_start"]).sort_values("h4_start").reset_index(drop=True)
    h4 = add_ha_stream(h4, "fast", 2.0, 0.25)
    h4 = add_ha_stream(h4, "std", 1.0, 0.50)
    h4 = add_ha_stream(h4, "slow", 2.0, 0.75)
    if (
        np.max(np.abs(h4["fast_open"] - h4["fast_ha_open"])) > 1e-9
        or np.max(np.abs(h4["fast_close"] - h4["fast_ha_close"])) > 1e-9
        or not np.array_equal(h4["fast_dir"], h4["fast_dir"].astype(int))
    ):
        raise ValueError("FAST HA reconstruction failed")
    h4["decision"] = h4["h4_start"] + pd.Timedelta(hours=4)
    h4["rid"] = (h4["fast_dir"] != h4["fast_dir"].shift()).cumsum().astype(int)
    h4["k"] = h4.groupby("rid", sort=False).cumcount() + 1
    h4["L"] = h4.groupby("rid", sort=False)["rid"].transform("size")
    h4["run_start_open"] = h4.groupby("rid", sort=False)["open"].transform("first")
    return h4


def causal_m1_feature_replay(
    path: Path, episodes: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Rebuild H4/M5 and freeze all features while raw M1 is revealed once."""
    if sha256_file(path).lower() != EXPECTED_M1_SHA256:
        raise ValueError("raw M1 SHA mismatch")
    records = episodes.to_dict("records")
    events: list[tuple[pd.Timestamp, str, int, pd.Timestamp, int]] = []
    for index, record in enumerate(records):
        decision = pd.Timestamp(record["decision"])
        events.append((decision, "NHA", index, pd.Timestamp(record["wave_start"]), 240))
        for minute in (60, 120, 180):
            events.append(
                (
                    decision + pd.Timedelta(minutes=minute),
                    f"B{minute}",
                    index,
                    decision,
                    15,
                )
            )
    events.sort(key=lambda item: item[0])
    event_index = 0
    market = CausalMarketBuilder()
    completed_by_h4: dict[pd.Timestamp, dict[str, object]] = {}
    previous_completed_start: dict[pd.Timestamp, pd.Timestamp | None] = {}
    forming_meta: dict[pd.Timestamp, dict[str, float]] = {}
    completed_count = 0
    last_completed_start: pd.Timestamp | None = None
    raw_by_h4: dict[pd.Timestamp, dict[str, float]] = {}
    closes_by_h4: dict[pd.Timestamp, list[float]] = {}
    current_m5_start: pd.Timestamp | None = None
    current_m5_h4: pd.Timestamp | None = None
    current_m5_close = np.nan
    m1_rows: list[tuple[datetime, float, float, float, float]] = []
    previous_ts: datetime | None = None

    def capture(
        event_time: pd.Timestamp,
        kind: str,
        record_index: int,
        target_start: pd.Timestamp,
        observed_at: pd.Timestamp,
        max_delay_minutes: int,
    ) -> None:
        record = records[record_index]
        if observed_at - event_time > pd.Timedelta(minutes=max_delay_minutes):
            if kind.startswith("B"):
                record[f"b{kind[1:]}_available"] = 0
            return
        raw = raw_by_h4.get(target_start)
        closes = np.asarray(closes_by_h4.get(target_start, []), dtype=float)
        state = (
            completed_by_h4.get(target_start)
            if kind == "NHA"
            else forming_meta.get(target_start)
        )
        if raw is None or len(closes) == 0 or state is None:
            if kind.startswith("B"):
                record[f"b{kind[1:]}_available"] = 0
            return
        scale = float(state["causal_scale"])
        if not np.isfinite(scale) or scale <= 0.0:
            if kind.startswith("B"):
                record[f"b{kind[1:]}_available"] = 0
            return
        direction = int(record["dir"])
        if kind == "NHA":
            wave = wave_coordinates(
                closes,
                float(raw["low"]),
                float(raw["high"]),
                float(state["fast_ha_open"]),
                float(state["fast_ha_close"]),
                scale,
                direction,
            )
            record.update({f"nha_wave_{key}": value for key, value in wave.items()})
            prior_start = previous_completed_start.get(target_start)
            prior = completed_by_h4.get(prior_start) if prior_start is not None else None
            if prior is not None:
                previous_open = float(prior["open"])
                previous_close = float(prior["close"])
                record["nha_fraction_beyond_prev_open"] = float(
                    np.mean(direction * (closes - previous_open) >= 0.0)
                )
                record["nha_fraction_beyond_prev_close"] = float(
                    np.mean(direction * (closes - previous_close) >= 0.0)
                )
                record["nha_close_beyond_prev_open_atr"] = direction * (
                    float(state["close"]) - previous_open
                ) / scale
                record["nha_density_median_beyond_prev_open_atr"] = direction * (
                    float(wave["density_median"]) - previous_open
                ) / scale
            record["nha_body_atr"] = direction * (
                float(state["fast_ha_close"]) - float(state["fast_ha_open"])
            ) / scale
            record["nha_raw_return_atr"] = direction * (
                float(state["close"]) - float(state["open"])
            ) / scale
            record["nha_range_atr"] = (float(state["high"]) - float(state["low"])) / scale
            record["nha_observed_at"] = observed_at
            return

        minute = int(kind[1:])
        key = f"b{minute}"
        fast_open = float(state["fast_open"])
        fast_close = (
            float(raw["open"])
            + float(raw["high"])
            + float(raw["low"])
            + 2.0 * float(raw["close"])
        ) / 5.0
        wave = wave_coordinates(
            closes,
            float(raw["low"]),
            float(raw["high"]),
            fast_open,
            fast_close,
            scale,
            direction,
        )
        nha_state = completed_by_h4.get(pd.Timestamp(record["wave_start"]))
        if nha_state is None:
            record[f"{key}_available"] = 0
            return
        nha_close = float(nha_state["close"])
        record[f"{key}_available"] = 1
        record[f"{key}_observed_at"] = observed_at
        record[f"{key}_prefix_return_atr"] = direction * (
            float(raw["close"]) - float(raw["open"])
        ) / scale
        record[f"{key}_close_beyond_nha_close_atr"] = direction * (
            float(raw["close"]) - nha_close
        ) / scale
        record[f"{key}_fraction_beyond_nha_close"] = float(
            np.mean(direction * (closes - nha_close) >= 0.0)
        )
        for name, value in wave.items():
            record[f"{key}_wave_{name}"] = value

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        expected = {"<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>"}
        if not expected.issubset(reader.fieldnames or []):
            raise ValueError(f"unexpected M1 schema: {reader.fieldnames}")
        for source in reader:
            ts = datetime.strptime(f"{source['<DATE>']} {source['<TIME>']}", SOURCE_TS)
            if previous_ts is not None and ts <= previous_ts:
                raise ValueError(f"M1 is not strictly chronological at {ts}")
            previous_ts = ts
            o = float(source["<OPEN>"])
            high = float(source["<HIGH>"])
            low = float(source["<LOW>"])
            close = float(source["<CLOSE>"])
            ts_pd = pd.Timestamp(ts)
            h4_start = ts_pd.floor("4h")
            m5_start = ts_pd.floor("5min")

            if current_m5_start is not None and m5_start != current_m5_start:
                closes_by_h4.setdefault(current_m5_h4, []).append(float(current_m5_close))
                current_m5_start = None
                current_m5_h4 = None
            market.finalize_due(ts_pd)
            while completed_count < len(market.h4_rows):
                completed = market.h4_rows[completed_count]
                completed_start = pd.Timestamp(completed["h4_start"])
                previous_completed_start[completed_start] = last_completed_start
                completed_by_h4[completed_start] = completed
                last_completed_start = completed_start
                completed_count += 1
            if h4_start not in forming_meta:
                if np.isfinite(market.previous_fast_open):
                    fast_open = (
                        0.25 * float(market.previous_fast_open)
                        + 0.75 * float(market.previous_fast_close)
                    )
                else:
                    fast_open = 0.5 * (o + close)
                forming_meta[h4_start] = {
                    "fast_open": fast_open,
                    "causal_scale": float(market.previous_atr),
                }
            while event_index < len(events) and events[event_index][0] <= ts_pd:
                event_time, kind, record_index, target_start, max_delay = events[event_index]
                capture(
                    event_time,
                    kind,
                    record_index,
                    target_start,
                    ts_pd,
                    max_delay,
                )
                event_index += 1

            if current_m5_start is None:
                current_m5_start = m5_start
                current_m5_h4 = h4_start
            current_m5_close = close
            raw = raw_by_h4.get(h4_start)
            if raw is None:
                raw_by_h4[h4_start] = {
                    "open": o,
                    "high": high,
                    "low": low,
                    "close": close,
                }
            else:
                raw["high"] = max(float(raw["high"]), high)
                raw["low"] = min(float(raw["low"]), low)
                raw["close"] = close
            market.update(ts_pd, o, high, low, close)
            m1_rows.append((ts, o, high, low, close))

    m1 = pd.DataFrame(m1_rows, columns=["ts", "open", "high", "low", "close"])
    rebuilt_h4, _ = market.frames()
    rebuilt_h4 = add_ha_stream(rebuilt_h4, "fast", 2.0, 0.25)
    rebuilt_h4 = add_ha_stream(rebuilt_h4, "std", 1.0, 0.50)
    rebuilt_h4 = add_ha_stream(rebuilt_h4, "slow", 2.0, 0.75)
    if (
        np.max(np.abs(rebuilt_h4["fast_open"] - rebuilt_h4["fast_ha_open"])) > 1e-9
        or np.max(np.abs(rebuilt_h4["fast_close"] - rebuilt_h4["fast_ha_close"])) > 1e-9
        or not np.array_equal(
            rebuilt_h4["fast_dir"].astype(int),
            np.where(rebuilt_h4["fast_close"] >= rebuilt_h4["fast_open"], 1, -1),
        )
    ):
        raise ValueError("streaming FAST HA reconstruction failed")
    rebuilt_h4["decision"] = rebuilt_h4["h4_start"] + pd.Timedelta(hours=4)
    rebuilt_h4["rid"] = (
        rebuilt_h4["fast_dir"] != rebuilt_h4["fast_dir"].shift()
    ).cumsum().astype(int)
    rebuilt_h4["k"] = rebuilt_h4.groupby("rid", sort=False).cumcount() + 1
    rebuilt_h4["L"] = rebuilt_h4.groupby("rid", sort=False)["rid"].transform("size")
    rebuilt_h4["run_start_open"] = rebuilt_h4.groupby("rid", sort=False)["open"].transform("first")
    result = pd.DataFrame(records)
    completed_index = rebuilt_h4.set_index("h4_start")
    result["std_aligned_at_k1"] = result.apply(
        lambda row: int(
            int(completed_index.loc[pd.Timestamp(row["wave_start"]), "std_dir"])
            == int(row["dir"])
        ),
        axis=1,
    )
    result["slow_aligned_at_k1"] = result.apply(
        lambda row: int(
            int(completed_index.loc[pd.Timestamp(row["wave_start"]), "slow_dir"])
            == int(row["dir"])
        ),
        axis=1,
    )
    for minute in (60, 120, 180):
        key = f"b{minute}"
        for index, episode in result.iterrows():
            if int(episode.get(f"{key}_available", 0) or 0) != 1:
                continue
            outcome = replay_delayed(
                m1,
                pd.Timestamp(episode["decision"]),
                pd.Timestamp(episode["decision"]) + pd.Timedelta(minutes=minute),
                pd.Timestamp(episode["run_end_decision"]),
                int(episode["dir"]),
                float(episode["stop"]),
            )
            for name, value in outcome.items():
                result.at[index, f"{key}_{name}"] = value
    return m1, result, rebuilt_h4


def wave_coordinates(
    closes: np.ndarray,
    raw_low: float,
    raw_high: float,
    ha_open: float,
    ha_close: float,
    scale: float,
    direction: int,
) -> dict[str, float]:
    names = [
        "efficiency",
        "settlement",
        "dispersion_atr",
        "favorable_mass",
        "entropy",
        "density_peak",
        "density_median",
    ]
    if len(closes) == 0 or not np.isfinite(scale) or scale <= 0.0 or raw_high <= raw_low:
        return {name: np.nan for name in names}
    path = float(np.abs(np.diff(np.r_[ha_open, closes])).sum())
    efficiency = abs(float(closes[-1]) - ha_open) / path if path > 1e-12 else 0.0
    settlement = float(np.mean(direction * (closes - ha_open) >= 0.0))
    prices = np.linspace(raw_low, raw_high, 49)
    bandwidth = max(
        (raw_high - raw_low) / 48.0,
        float(np.std(closes, ddof=0)) * 0.10,
        0.02,
    )
    z = (prices[:, None] - closes[None, :]) / bandwidth
    density = np.exp(-0.5 * z * z).mean(axis=1)
    density_sum = float(density.sum())
    favorable = direction * (prices - ha_open) >= 0.0
    favorable_mass = float(density[favorable].sum() / density_sum)
    probability = density / density_sum
    positive = probability[probability > 0.0]
    entropy = float(-(positive * np.log(positive)).sum() / np.log(len(prices)))
    cdf = np.cumsum(probability)
    median_idx = int(np.searchsorted(cdf, 0.5, side="left"))
    return {
        "efficiency": efficiency,
        "settlement": settlement,
        "dispersion_atr": float(np.std(closes, ddof=0) / scale),
        "favorable_mass": favorable_mass,
        "entropy": entropy,
        "density_peak": float(prices[int(np.argmax(density))]),
        "density_median": float(prices[min(median_idx, len(prices) - 1)]),
    }


def replay_delayed(
    m1: pd.DataFrame,
    guard_start: pd.Timestamp,
    checkpoint: pd.Timestamp,
    run_end: pd.Timestamp,
    direction: int,
    stop: float,
) -> dict[str, object]:
    ts = m1["ts"].to_numpy(dtype="datetime64[ns]")
    opens = m1["open"].to_numpy(dtype=float)
    highs = m1["high"].to_numpy(dtype=float)
    lows = m1["low"].to_numpy(dtype=float)
    entry_idx = int(np.searchsorted(ts, np.datetime64(checkpoint), side="left"))
    exit_idx = int(np.searchsorted(ts, np.datetime64(run_end), side="left"))
    result: dict[str, object] = {
        "valid": 0,
        "entry_time": pd.NaT,
        "entry": np.nan,
        "exit_time": pd.NaT,
        "exit": np.nan,
        "stop_hit": np.nan,
        "R": np.nan,
        "guard_touched_before_entry": 0,
    }
    if entry_idx >= len(ts) or exit_idx >= len(ts) or entry_idx > exit_idx:
        return result
    entry_time = pd.Timestamp(ts[entry_idx])
    if entry_time - checkpoint > pd.Timedelta(minutes=15):
        return result
    entry = float(opens[entry_idx])
    guard_idx = int(np.searchsorted(ts, np.datetime64(guard_start), side="left"))
    if guard_idx < entry_idx:
        guard_touched = (
            np.any(lows[guard_idx:entry_idx] <= stop)
            if direction > 0
            else np.any(highs[guard_idx:entry_idx] >= stop)
        )
        if guard_touched:
            result["guard_touched_before_entry"] = 1
            return result
    if (direction > 0 and stop >= entry) or (direction < 0 and stop <= entry):
        return result
    touched = (
        lows[entry_idx : exit_idx + 1] <= stop
        if direction > 0
        else highs[entry_idx : exit_idx + 1] >= stop
    )
    locations = np.flatnonzero(touched)
    stop_hit = int(len(locations) > 0)
    actual_idx = entry_idx + int(locations[0]) if stop_hit else exit_idx
    exit_price = stop if stop_hit else float(opens[exit_idx])
    risk = abs(entry - stop)
    result.update(
        valid=1,
        entry_time=entry_time,
        entry=entry,
        exit_time=pd.Timestamp(ts[actual_idx]),
        exit=exit_price,
        stop_hit=stop_hit,
        R=direction * (exit_price - entry) / risk,
    )
    return result


def max_true_streak(values: pd.Series) -> int:
    current = 0
    maximum = 0
    for value in values.astype(bool):
        current = current + 1 if value else 0
        maximum = max(maximum, current)
    return maximum


def adjacent_chain_count(stopped_rids: set[int], length: int) -> int:
    return sum(
        all((rid + offset) in stopped_rids for offset in range(length))
        for rid in stopped_rids
        if (rid - 1) not in stopped_rids
    )


def policy_metrics(
    name: str,
    attempts: pd.DataFrame,
    baseline: pd.DataFrame,
    outcome_r: str = "R",
    outcome_stop: str = "stop_hit",
    entry_time: str = "entry_time",
) -> dict[str, object]:
    attempts = attempts.dropna(subset=[outcome_r, outcome_stop]).copy()
    attempts = attempts.sort_values("decision")
    attempts["policy_R"] = attempts[outcome_r].astype(float)
    attempts["policy_stop"] = attempts[outcome_stop].astype(int)
    attempted_rids = set(attempts["base_rid"].astype(int))
    policy_stop_by_rid = attempts.set_index("base_rid")["policy_stop"].to_dict()
    baseline_stop_by_rid = baseline.set_index("base_rid")["stop_hit"].astype(int).to_dict()
    avoided = sum(
        1
        for rid, stopped in baseline_stop_by_rid.items()
        if stopped and (rid not in attempted_rids or not policy_stop_by_rid.get(rid, 0))
    )
    new_stops = sum(
        1
        for rid, stopped in baseline_stop_by_rid.items()
        if not stopped and policy_stop_by_rid.get(rid, 0)
    )
    baseline_l3 = set(baseline.loc[baseline["L"] >= 3, "base_rid"].astype(int))
    baseline_l6 = set(baseline.loc[baseline["L"] >= 6, "base_rid"].astype(int))
    baseline_positive = baseline.loc[baseline["R"] > 0.0, "R"].sum()
    positive_covered = baseline.loc[
        baseline["base_rid"].astype(int).isin(attempted_rids) & (baseline["R"] > 0.0), "R"
    ].sum()
    stopped_rids = set(attempts.loc[attempts["policy_stop"] == 1, "base_rid"].astype(int))
    delay_hours = (
        pd.to_datetime(attempts[entry_time]) - pd.to_datetime(attempts["episode_decision"])
    ).dt.total_seconds() / 3600.0
    return {
        "policy": name,
        "attempts": len(attempts),
        "admission_rate": float(len(attempts) / len(baseline)),
        "stops": int(attempts["policy_stop"].sum()),
        "stop_rate": float(attempts["policy_stop"].mean()) if len(attempts) else np.nan,
        "wins": int((attempts["policy_R"] > 0.0).sum()),
        "win_rate": float((attempts["policy_R"] > 0.0).mean()) if len(attempts) else np.nan,
        "sum_R": float(attempts["policy_R"].sum()),
        "mean_R": float(attempts["policy_R"].mean()) if len(attempts) else np.nan,
        "median_R": float(attempts["policy_R"].median()) if len(attempts) else np.nan,
        "max_stop_streak_among_attempts": max_true_streak(attempts["policy_stop"]),
        "adjacent_two_stop_chains": adjacent_chain_count(stopped_rids, 2),
        "adjacent_three_stop_chains": adjacent_chain_count(stopped_rids, 3),
        "baseline_stops_avoided": int(avoided),
        "new_stops_vs_baseline": int(new_stops),
        "L3_run_coverage": float(len(attempted_rids & baseline_l3) / len(baseline_l3)),
        "L6_run_coverage": float(len(attempted_rids & baseline_l6) / len(baseline_l6)),
        "baseline_positive_R_coverage": float(positive_covered / baseline_positive),
        "mean_delay_hours": float(delay_hours.mean()) if len(delay_hours) else np.nan,
    }


def make_policy_attempts(
    episodes: pd.DataFrame,
    all_children: pd.DataFrame,
    h4: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    baseline = episodes.copy()
    baseline["base_rid"] = baseline["rid"].astype(int)
    baseline["episode_decision"] = baseline["decision"]
    policies: dict[str, pd.DataFrame] = {"FAST_K1_IMMEDIATE": baseline}
    efficient_masks: dict[int, pd.Series] = {}

    child_lookup = all_children.set_index(["rid", "k"], drop=False)
    for k in (2, 3):
        selected = []
        for episode in baseline.itertuples(index=False):
            key = (int(episode.base_rid), k)
            if key in child_lookup.index:
                row = child_lookup.loc[key]
                if isinstance(row, pd.DataFrame):
                    row = row.iloc[0]
                record = row.to_dict()
                record["base_rid"] = int(episode.base_rid)
                record["episode_decision"] = episode.episode_decision
                record["year"] = int(episode.year)
                selected.append(record)
        policies[f"FAST_K{k}_CONFIRM"] = pd.DataFrame(selected)

    h4_by_rid = {rid: group.sort_values("k") for rid, group in h4.groupby("rid", sort=True)}
    for label, column in (("STD_ALIGN_FIRST", "std_dir"), ("SLOW_ALIGN_FIRST", "slow_dir")):
        selected = []
        for episode in baseline.itertuples(index=False):
            run = h4_by_rid.get(int(episode.base_rid))
            if run is None:
                continue
            aligned = run[run[column].astype(int) == int(episode.dir)]
            if aligned.empty:
                continue
            first_k = int(aligned.iloc[0]["k"])
            key = (int(episode.base_rid), first_k)
            if key not in child_lookup.index:
                continue
            row = child_lookup.loc[key]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            record = row.to_dict()
            record["base_rid"] = int(episode.base_rid)
            record["episode_decision"] = episode.episode_decision
            record["year"] = int(episode.year)
            selected.append(record)
        policies[label] = pd.DataFrame(selected)

    immediate_masks = {
        "PRIOR_H4_ARRIVAL_RESPONSE": baseline["prior_nha_explanation"].astype(str).str.startswith("ARRIVAL_RESPONSE"),
        "PRIOR_NOT_IN_TRANSIT": baseline["prior_nha_explanation"] != "IN_TRANSIT_COUNTERFLOW",
        "NHA_H4_ARRIVAL": baseline["same_h4_consumed"].astype(bool),
        "NHA_H4_ROUTE": baseline["h4_route_open"].astype(bool),
        "NHA_WAVE_SETTLEMENT_MAJORITY": baseline["nha_wave_settlement"] > 0.5,
        "NHA_DEPART_PREV_OPEN": (
            (baseline["nha_fraction_beyond_prev_open"] > 0.5)
            & (baseline["nha_close_beyond_prev_open_atr"] > 0.0)
        ),
    }
    immediate_masks["NHA_LIQUIDITY_AND_WAVE"] = (
        (baseline["same_h4_consumed"].astype(bool) | baseline["h4_route_open"].astype(bool))
        & immediate_masks["NHA_WAVE_SETTLEMENT_MAJORITY"]
        & immediate_masks["NHA_DEPART_PREV_OPEN"]
    )
    for name, mask in immediate_masks.items():
        policies[name] = baseline[mask].copy()

    for minute in (60, 120, 180):
        key = f"b{minute}"
        valid = baseline[f"{key}_valid"] == 1
        delayed = baseline[valid].copy()
        delayed["entry_time"] = delayed[f"{key}_entry_time"]
        delayed["R"] = delayed[f"{key}_R"]
        delayed["stop_hit"] = delayed[f"{key}_stop_hit"]
        policies[f"WAIT_{minute}M_ALL"] = delayed
        component_masks = {
            f"BRIDGE_{minute}M_RETURN_POSITIVE": valid
            & (baseline[f"{key}_prefix_return_atr"] > 0.0),
            f"BRIDGE_{minute}M_WAVE_MAJORITY": valid
            & (baseline[f"{key}_wave_settlement"] > 0.5),
        }
        efficiency_median = baseline[f"{key}_wave_efficiency"].shift(1).rolling(
            180, min_periods=60
        ).median()
        component_masks[f"BRIDGE_{minute}M_RETURN_EFFICIENT"] = (
            component_masks[f"BRIDGE_{minute}M_RETURN_POSITIVE"]
            & (baseline[f"{key}_wave_efficiency"] >= efficiency_median)
        )
        efficient_masks[minute] = component_masks[
            f"BRIDGE_{minute}M_RETURN_EFFICIENT"
        ]
        for component_name, component_mask in component_masks.items():
            component = baseline[component_mask].copy()
            component["entry_time"] = component[f"{key}_entry_time"]
            component["R"] = component[f"{key}_R"]
            component["stop_hit"] = component[f"{key}_stop_hit"]
            policies[component_name] = component
        bridge_mask = component_masks[f"BRIDGE_{minute}M_RETURN_POSITIVE"] & component_masks[
            f"BRIDGE_{minute}M_WAVE_MAJORITY"
        ]
        bridge = baseline[bridge_mask].copy()
        bridge["entry_time"] = bridge[f"{key}_entry_time"]
        bridge["R"] = bridge[f"{key}_R"]
        bridge["stop_hit"] = bridge[f"{key}_stop_hit"]
        policies[f"BRIDGE_{minute}M_SETTLED"] = bridge
        independent_mask = bridge_mask & (
            baseline[f"{key}_fraction_beyond_nha_close"] > 0.5
        )
        independent = baseline[independent_mask].copy()
        independent["entry_time"] = independent[f"{key}_entry_time"]
        independent["R"] = independent[f"{key}_R"]
        independent["stop_hit"] = independent[f"{key}_stop_hit"]
        policies[f"BRIDGE_{minute}M_BEYOND_NHA"] = independent

    remaining = pd.Series(True, index=baseline.index)
    earliest_frames: list[pd.DataFrame] = []
    for minute in (60, 120, 180):
        selected_mask = remaining & efficient_masks[minute]
        selected = baseline[selected_mask].copy()
        key = f"b{minute}"
        selected["entry_time"] = selected[f"{key}_entry_time"]
        selected["R"] = selected[f"{key}_R"]
        selected["stop_hit"] = selected[f"{key}_stop_hit"]
        selected["selected_checkpoint_minutes"] = minute
        earliest_frames.append(selected)
        remaining &= ~selected_mask
    policies["EARLIEST_TESTED_RETURN_EFFICIENT"] = pd.concat(
        earliest_frames, ignore_index=True
    )

    return baseline, policies


def auc_score(label: pd.Series, score: pd.Series) -> float:
    valid = label.notna() & score.notna()
    y = label[valid].astype(int).to_numpy()
    s = score[valid].astype(float)
    positives = int(y.sum())
    negatives = int(len(y) - positives)
    if positives == 0 or negatives == 0:
        return np.nan
    ranks = pd.Series(s).rank(method="average").to_numpy()
    return float((ranks[y == 1].sum() - positives * (positives + 1) / 2) / (positives * negatives))


def feature_audit(episodes: pd.DataFrame) -> pd.DataFrame:
    specs = {
        "STD_ALIGNED_K1": ("std_aligned_at_k1", "stop_hit"),
        "SLOW_ALIGNED_K1": ("slow_aligned_at_k1", "stop_hit"),
        "NHA_H4_ARRIVAL": ("same_h4_consumed", "stop_hit"),
        "NHA_H4_ROUTE": ("h4_route_open", "stop_hit"),
        "NHA_WAVE_EFFICIENCY": ("nha_wave_efficiency", "stop_hit"),
        "NHA_WAVE_SETTLEMENT": ("nha_wave_settlement", "stop_hit"),
        "NHA_WAVE_FAVORABLE_MASS": ("nha_wave_favorable_mass", "stop_hit"),
        "NHA_WAVE_ENTROPY": ("nha_wave_entropy", "stop_hit"),
        "NHA_BEYOND_PREV_OPEN": ("nha_fraction_beyond_prev_open", "stop_hit"),
        "NHA_DEPARTURE_PREV_OPEN": ("nha_close_beyond_prev_open_atr", "stop_hit"),
        "BRIDGE60_SETTLEMENT": ("b60_wave_settlement", "b60_stop_hit"),
        "BRIDGE60_RETURN": ("b60_prefix_return_atr", "b60_stop_hit"),
        "BRIDGE60_EFFICIENCY": ("b60_wave_efficiency", "b60_stop_hit"),
        "BRIDGE60_BEYOND_NHA": ("b60_fraction_beyond_nha_close", "b60_stop_hit"),
        "BRIDGE120_RETURN": ("b120_prefix_return_atr", "b120_stop_hit"),
        "BRIDGE120_EFFICIENCY": ("b120_wave_efficiency", "b120_stop_hit"),
        "BRIDGE180_RETURN": ("b180_prefix_return_atr", "b180_stop_hit"),
        "BRIDGE180_EFFICIENCY": ("b180_wave_efficiency", "b180_stop_hit"),
    }
    rows: list[dict[str, object]] = []
    periods = [("POOLED", episodes)]
    periods.extend((str(int(year)), group) for year, group in episodes.groupby("year", sort=True))
    for period, source in periods:
        for name, (feature, label) in specs.items():
            valid = source[[feature, label]].dropna()
            rows.append(
                {
                    "period": period,
                    "sample": "ALL_VALID",
                    "feature": name,
                    "label": label,
                    "n": len(valid),
                    "positive_labels": int(valid[label].sum()),
                    "auc_high_value_means_stop": auc_score(valid[label], valid[feature]),
                    "feature_mean_stopped": float(valid.loc[valid[label] == 1, feature].mean()),
                    "feature_mean_survived": float(valid.loc[valid[label] == 0, feature].mean()),
                }
            )
        for minute in (60, 120, 180):
            prefix = f"b{minute}"
            conditional = source[source[f"{prefix}_prefix_return_atr"] > 0.0]
            feature = f"{prefix}_wave_efficiency"
            label = f"{prefix}_stop_hit"
            valid = conditional[[feature, label]].dropna()
            rows.append(
                {
                    "period": period,
                    "sample": "RETURN_POSITIVE_ONLY",
                    "feature": f"BRIDGE{minute}_EFFICIENCY",
                    "label": label,
                    "n": len(valid),
                    "positive_labels": int(valid[label].sum()),
                    "auc_high_value_means_stop": auc_score(valid[label], valid[feature]),
                    "feature_mean_stopped": float(
                        valid.loc[valid[label] == 1, feature].mean()
                    ),
                    "feature_mean_survived": float(
                        valid.loc[valid[label] == 0, feature].mean()
                    ),
                }
            )
    return pd.DataFrame(rows)


def sizing_grid(policy_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for name, frame in policy_frames.items():
        if frame.empty or "R" not in frame:
            continue
        ordered = frame.dropna(subset=["R"]).sort_values("decision")
        values = ordered["R"].to_numpy(dtype=float)
        for risk_fraction in (0.0025, 0.005, 0.01, 0.02):
            equity = 1.0
            peak = 1.0
            max_drawdown = 0.0
            for value in values:
                equity *= max(1e-12, 1.0 + risk_fraction * value)
                peak = max(peak, equity)
                max_drawdown = max(max_drawdown, 1.0 - equity / peak)
            rows.append(
                {
                    "policy": name,
                    "risk_fraction": risk_fraction,
                    "attempts": len(values),
                    "ending_equity_multiple": equity,
                    "max_drawdown": max_drawdown,
                }
            )
    return pd.DataFrame(rows)


def stop_timing_summary(episodes: pd.DataFrame) -> pd.DataFrame:
    stopped = episodes[episodes["stop_hit"] == 1].copy()
    stopped["minutes_to_stop"] = (
        pd.to_datetime(stopped["exit_time"]) - pd.to_datetime(stopped["decision"])
    ).dt.total_seconds() / 60.0
    rows: list[dict[str, object]] = []
    cuts = [("POOLED", stopped)]
    cuts.extend((str(int(year)), group) for year, group in stopped.groupby("year", sort=True))
    cuts.extend(
        (("LONG" if int(direction) > 0 else "SHORT"), group)
        for direction, group in stopped.groupby("dir", sort=True)
    )
    for period, group in cuts:
        row: dict[str, object] = {
            "period": period,
            "stops": len(group),
            "median_minutes_to_stop": float(group["minutes_to_stop"].median()),
            "mean_minutes_to_stop": float(group["minutes_to_stop"].mean()),
        }
        for minute in (30, 60, 90, 120, 180, 240):
            row[f"stops_before_{minute}m"] = int((group["minutes_to_stop"] < minute).sum())
            row[f"fraction_before_{minute}m"] = float(
                (group["minutes_to_stop"] < minute).mean()
            )
        rows.append(row)
    return pd.DataFrame(rows)


def rejection_handoff_summary(episodes: pd.DataFrame) -> pd.DataFrame:
    ordered = episodes.sort_values("decision").copy()
    next_lookup = episodes.set_index("rid")
    rows: list[dict[str, object]] = []
    for minute in (60, 120, 180):
        key = f"b{minute}"
        efficiency_median = ordered[f"{key}_wave_efficiency"].shift(1).rolling(
            180, min_periods=60
        ).median()
        groups = {
            "GUARD_FAILED": ordered[f"{key}_guard_touched_before_entry"].fillna(0) == 1,
            "VALID_RETURN_EFFICIENT": (
                (ordered[f"{key}_valid"] == 1)
                & (ordered[f"{key}_prefix_return_atr"] > 0.0)
                & (ordered[f"{key}_wave_efficiency"] >= efficiency_median)
            ),
            "VALID_RETURN_NOT_EFFICIENT": (
                (ordered[f"{key}_valid"] == 1)
                & (ordered[f"{key}_prefix_return_atr"] > 0.0)
                & (ordered[f"{key}_wave_efficiency"] < efficiency_median)
            ),
            "VALID_NONPOSITIVE_RETURN": (
                (ordered[f"{key}_valid"] == 1)
                & (ordered[f"{key}_prefix_return_atr"] <= 0.0)
            ),
        }
        for group_name, mask in groups.items():
            group = ordered[mask]
            following = next_lookup.reindex(group["rid"].astype(int) + 1).dropna(subset=["R"])
            rows.append(
                {
                    "checkpoint_minutes": minute,
                    "bridge_state": group_name,
                    "episodes": len(group),
                    "current_k1_stop_rate": float(group["stop_hit"].mean()) if len(group) else np.nan,
                    "current_run_L2_or_less_rate": float((group["L"] <= 2).mean()) if len(group) else np.nan,
                    "following_old_direction_k1": len(following),
                    "following_k1_stop_rate": float(following["stop_hit"].mean()) if len(following) else np.nan,
                    "following_k1_win_rate": float((following["R"] > 0.0).mean()) if len(following) else np.nan,
                    "following_k1_sum_R": float(following["R"].sum()),
                    "following_L3plus_rate": float((following["L"] >= 3).mean()) if len(following) else np.nan,
                    "following_L6plus_rate": float((following["L"] >= 6).mean()) if len(following) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    ledger = pd.read_csv(
        args.ledger,
        parse_dates=["decision", "entry_time", "exit_time", "run_end_decision", "wave_start"],
    )
    fast = ledger[ledger["base"] == "FAST"].copy()
    prior_explanation = fast[fast["immediate_nha"].astype(bool)].set_index("rid")["nha_explanation"]
    episodes = fast[fast["k"] == 1].copy()
    episodes["prior_nha_explanation"] = episodes["rid"].map(
        lambda rid: prior_explanation.get(int(rid) - 1)
    )
    episodes["base_rid"] = episodes["rid"].astype(int)
    episodes["episode_decision"] = episodes["decision"]
    m1, episodes, h4 = causal_m1_feature_replay(args.m1, episodes)

    h4_keys = h4.set_index("h4_start")[["rid", "k", "fast_dir"]]
    parity = fast.join(h4_keys, on="wave_start", rsuffix="_h4")
    if (
        parity[["rid_h4", "k_h4", "fast_dir"]].isna().any().any()
        or (parity["rid"] != parity["rid_h4"]).any()
        or (parity["k"] != parity["k_h4"]).any()
        or (parity["dir"] != parity["fast_dir"]).any()
    ):
        raise ValueError("FAST ledger/stream-rebuilt H4 run parity failed")

    reference_h4 = build_h4_state(args.h4)
    reference_columns = ["open", "high", "low", "close", "causal_scale", "fast_open", "fast_close"]
    audit = h4.set_index("h4_start")[reference_columns].join(
        reference_h4.set_index("h4_start")[reference_columns],
        how="inner",
        lsuffix="_stream",
        rsuffix="_reference",
    )
    if len(audit) != len(h4):
        raise ValueError("stream-rebuilt H4/reference coverage mismatch")
    h4_parity_max_error = max(
        float(np.nanmax(np.abs(audit[f"{column}_stream"] - audit[f"{column}_reference"])))
        for column in reference_columns
    )
    if h4_parity_max_error > 1e-9:
        raise ValueError(f"stream-rebuilt H4/reference parity failed: {h4_parity_max_error}")

    baseline, policy_frames = make_policy_attempts(episodes, fast, h4)
    metrics = pd.DataFrame(
        [policy_metrics(name, frame, baseline) for name, frame in policy_frames.items()]
    ).sort_values(["stops", "attempts", "policy"]).reset_index(drop=True)
    year_rows: list[dict[str, object]] = []
    for name, frame in policy_frames.items():
        for year, group in frame.groupby("year", sort=True):
            year_baseline = baseline[baseline["year"] == year]
            if year_baseline.empty:
                continue
            row = policy_metrics(name, group, year_baseline)
            row["year"] = int(year)
            year_rows.append(row)
    year_metrics = pd.DataFrame(year_rows)
    side_rows: list[dict[str, object]] = []
    for name, frame in policy_frames.items():
        for direction, group in frame.groupby("dir", sort=True):
            side_baseline = baseline[baseline["dir"] == direction]
            if side_baseline.empty:
                continue
            row = policy_metrics(name, group, side_baseline)
            row["side"] = "LONG" if int(direction) > 0 else "SHORT"
            side_rows.append(row)
    side_metrics = pd.DataFrame(side_rows)
    features = feature_audit(episodes)
    sizing = sizing_grid(policy_frames)
    stop_timing = stop_timing_summary(episodes)
    handoff = rejection_handoff_summary(episodes)

    outputs = {
        "episodes": args.out_dir / "V11_NEUTRAL_BRIDGE_EPISODES.csv",
        "policy_summary": args.out_dir / "V11_NEUTRAL_BRIDGE_POLICY_SUMMARY.csv",
        "policy_by_year": args.out_dir / "V11_NEUTRAL_BRIDGE_POLICY_BY_YEAR.csv",
        "policy_by_side": args.out_dir / "V11_NEUTRAL_BRIDGE_POLICY_BY_SIDE.csv",
        "feature_audit": args.out_dir / "V11_NEUTRAL_BRIDGE_FEATURE_AUDIT.csv",
        "sizing_grid": args.out_dir / "V11_NEUTRAL_BRIDGE_SIZING_GRID.csv",
        "stop_timing": args.out_dir / "V11_NEUTRAL_BRIDGE_STOP_TIMING.csv",
        "rejection_handoff": args.out_dir / "V11_NEUTRAL_BRIDGE_REJECTION_HANDOFF.csv",
    }
    episodes.to_csv(outputs["episodes"], index=False, date_format="%Y-%m-%d %H:%M:%S")
    metrics.to_csv(outputs["policy_summary"], index=False)
    year_metrics.to_csv(outputs["policy_by_year"], index=False)
    side_metrics.to_csv(outputs["policy_by_side"], index=False)
    features.to_csv(outputs["feature_audit"], index=False)
    sizing.to_csv(outputs["sizing_grid"], index=False)
    stop_timing.to_csv(outputs["stop_timing"], index=False)
    handoff.to_csv(outputs["rejection_handoff"], index=False)
    manifest = {
        "status": "CONSUMED_DATA_TRANSITION_EPISODE_DIAGNOSTIC_ONLY",
        "authority": "NO TRADE, SIZING, OR PRODUCTION AUTHORITY",
        "unit": "one valid FAST k1 at the first completed opposite HA after the prior run",
        "baseline_rows": int(len(baseline)),
        "causal_input_contract": "single chronological raw-M1 pass; H4 and M5 rebuilt in-stream; external H4 used only for post-replay parity audit",
        "completed_h4_rows_rebuilt": int(len(h4)),
        "h4_reference_parity_max_error": h4_parity_max_error,
        "source_sha256": {
            "m1": sha256_file(args.m1),
            "h4": sha256_file(args.h4),
            "ledger": sha256_file(args.ledger),
        },
        "fixed_checkpoint_minutes": [60, 120, 180],
        "fixed_majority_boundary": "> 0.5; semantic majority, not optimized",
        "causal_efficiency_normalization": "current forming-Wave efficiency >= median of prior 180 transition episodes; minimum 60; fixed, not optimized",
        "outputs": {key: str(value.resolve()) for key, value in outputs.items()},
        "output_sha256": {key: sha256_file(value) for key, value in outputs.items()},
    }
    manifest_path = args.out_dir / "V11_NEUTRAL_BRIDGE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print("\nPOLICY SUMMARY")
    print(metrics.to_string(index=False))


if __name__ == "__main__":
    main()
