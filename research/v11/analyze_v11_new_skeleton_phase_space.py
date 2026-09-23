"""Build V11 journey skeletons from raw M1 without the V10 trade universe.

This is a consumed-data representation diagnostic.  It reconstructs H4 bars
and FAST/STD/SLOW HA streams in one chronological pass, then compares several
independently generated journey state machines.  V10 entries, V10 Hard SLs,
R7G selection, and the V10 event ledger are deliberately not inputs.

The primary candidate is STD_SLOW_MEMORY:

* STD and SLOW agreement establishes or reverses the journey direction.
* disagreement is a neutral bridge that preserves journey memory;
* FAST is not used by the state machine;
* one prototype Child is created only when the journey reverses;
* its fixed Hard SL is the opposite raw-H4 extreme of the causal transition
  bridge ending at the establishing H4 bar.

All results are development evidence only and have no trade authority.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


EXPECTED_M1_SHA256 = "626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2"
SOURCE_TS = "%Y.%m.%d %H:%M:%S"
WARMUP_H4 = 180


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m1", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_default(value: object) -> object:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return pd.Timestamp(value).isoformat()
    raise TypeError(f"not JSON serializable: {type(value)!r}")


def floor_h4(ts: datetime) -> datetime:
    return ts.replace(hour=(ts.hour // 4) * 4, minute=0, second=0, microsecond=0)


@dataclass
class HaStream:
    close_weight: float
    alpha: float
    previous_open: float = math.nan
    previous_close: float = math.nan

    def update(self, o: float, high: float, low: float, close: float) -> tuple[float, float, int]:
        ha_close = (o + high + low + self.close_weight * close) / (3.0 + self.close_weight)
        if math.isfinite(self.previous_open):
            ha_open = self.alpha * self.previous_open + (1.0 - self.alpha) * self.previous_close
        else:
            ha_open = 0.5 * (o + close)
        direction = 1 if ha_close >= ha_open else -1
        self.previous_open = ha_open
        self.previous_close = ha_close
        return ha_open, ha_close, direction


class ChronologicalH4Builder:
    def __init__(self) -> None:
        self.current: dict[str, object] | None = None
        self.rows: list[dict[str, object]] = []
        self.true_ranges: list[float] = []
        self.previous_close = math.nan
        self.fast = HaStream(close_weight=2.0, alpha=0.25)
        self.std = HaStream(close_weight=1.0, alpha=0.50)
        self.slow = HaStream(close_weight=2.0, alpha=0.75)

    def _finalize(self) -> None:
        if self.current is None:
            return
        bar = self.current
        o = float(bar["open"])
        high = float(bar["high"])
        low = float(bar["low"])
        close = float(bar["close"])
        if math.isfinite(self.previous_close):
            true_range = max(high - low, abs(high - self.previous_close), abs(low - self.previous_close))
        else:
            true_range = high - low
        self.true_ranges.append(float(true_range))
        atr180 = float(np.mean(self.true_ranges[-180:])) if len(self.true_ranges) >= 180 else math.nan
        fast_open, fast_close, fast_dir = self.fast.update(o, high, low, close)
        std_open, std_close, std_dir = self.std.update(o, high, low, close)
        slow_open, slow_close, slow_dir = self.slow.update(o, high, low, close)
        self.rows.append({
            "h4_start": pd.Timestamp(bar["start"]),
            "decision": pd.Timestamp(bar["start"]) + pd.Timedelta(hours=4),
            "open": o,
            "high": high,
            "low": low,
            "close": close,
            "m1_rows": int(bar["m1_rows"]),
            "true_range": true_range,
            "atr180": atr180,
            "fast_open": fast_open,
            "fast_close": fast_close,
            "fast_dir": fast_dir,
            "std_open": std_open,
            "std_close": std_close,
            "std_dir": std_dir,
            "slow_open": slow_open,
            "slow_close": slow_close,
            "slow_dir": slow_dir,
        })
        self.previous_close = close
        self.current = None

    def update(self, ts: datetime, o: float, high: float, low: float, close: float) -> None:
        start = floor_h4(ts)
        if self.current is not None and self.current["start"] != start:
            self._finalize()
        if self.current is None:
            self.current = {
                "start": start,
                "open": o,
                "high": high,
                "low": low,
                "close": close,
                "m1_rows": 1,
            }
            return
        self.current["high"] = max(float(self.current["high"]), high)
        self.current["low"] = min(float(self.current["low"]), low)
        self.current["close"] = close
        self.current["m1_rows"] = int(self.current["m1_rows"]) + 1

    def finish(self) -> pd.DataFrame:
        self._finalize()
        return pd.DataFrame(self.rows)


def rebuild_market(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    source_hash = sha256_file(path).lower()
    if source_hash != EXPECTED_M1_SHA256:
        raise ValueError(f"raw M1 SHA mismatch: {source_hash}")

    builder = ChronologicalH4Builder()
    timestamps: list[datetime] = []
    opens: list[float] = []
    highs: list[float] = []
    lows: list[float] = []
    closes: list[float] = []
    previous_ts: datetime | None = None
    duplicate_count = 0
    invalid_ohlc = 0

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        expected = {"<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>"}
        if not expected.issubset(reader.fieldnames or []):
            raise RuntimeError(f"unexpected raw-M1 schema: {reader.fieldnames}")
        for source in reader:
            ts = datetime.strptime(f"{source['<DATE>']} {source['<TIME>']}", SOURCE_TS)
            if previous_ts is not None:
                if ts == previous_ts:
                    duplicate_count += 1
                if ts <= previous_ts:
                    raise RuntimeError(f"raw M1 is not strictly chronological at {ts}")
            previous_ts = ts
            o = float(source["<OPEN>"])
            high = float(source["<HIGH>"])
            low = float(source["<LOW>"])
            close = float(source["<CLOSE>"])
            if low > min(o, close) or high < max(o, close) or high < low:
                invalid_ohlc += 1
            timestamps.append(ts)
            opens.append(o)
            highs.append(high)
            lows.append(low)
            closes.append(close)
            builder.update(ts, o, high, low, close)

    m1 = pd.DataFrame({
        "timestamp": pd.to_datetime(timestamps),
        "open": np.asarray(opens, dtype=float),
        "high": np.asarray(highs, dtype=float),
        "low": np.asarray(lows, dtype=float),
        "close": np.asarray(closes, dtype=float),
    })
    h4 = builder.finish()
    quality = {
        "source_sha256": source_hash,
        "m1_rows": len(m1),
        "m1_first": m1.iloc[0]["timestamp"],
        "m1_last": m1.iloc[-1]["timestamp"],
        "duplicate_timestamps": duplicate_count,
        "invalid_ohlc_rows": invalid_ohlc,
        "h4_rows": len(h4),
        "h4_first": h4.iloc[0]["h4_start"],
        "h4_last": h4.iloc[-1]["h4_start"],
        "h4_m1_rows_min": int(h4["m1_rows"].min()),
        "h4_m1_rows_median": float(h4["m1_rows"].median()),
        "h4_m1_rows_max": int(h4["m1_rows"].max()),
        "h4_partial_under_180": int(h4["m1_rows"].lt(180).sum()),
        "h4_atr_ready": int(h4["atr180"].notna().sum()),
    }
    return m1, h4, quality


def add_state_machines(h4: pd.DataFrame) -> pd.DataFrame:
    frame = h4.copy()
    frame["state_fast_reference"] = frame["fast_dir"].astype(int)
    frame["state_std"] = frame["std_dir"].astype(int)
    frame["state_slow"] = frame["slow_dir"].astype(int)
    agreement = np.where(frame["std_dir"].eq(frame["slow_dir"]), frame["std_dir"], 0).astype(int)
    frame["phase_core"] = agreement
    memory: list[int] = []
    current = 0
    bridge_age = 0
    ages: list[int] = []
    for value in agreement:
        if int(value) != 0:
            current = int(value)
            bridge_age = 0
        else:
            bridge_age += 1
        memory.append(current)
        ages.append(bridge_age if int(value) == 0 else 0)
    frame["state_std_slow_memory"] = np.asarray(memory, dtype=int)
    frame["bridge_age"] = np.asarray(ages, dtype=int)
    frame["std_slow_agree"] = frame["phase_core"].ne(0).astype(int)
    frame["all_three_agree"] = (
        frame["fast_dir"].eq(frame["std_dir"]) & frame["std_dir"].eq(frame["slow_dir"])
    ).astype(int)
    return frame


def first_m1_index(ts: np.ndarray, decision: pd.Timestamp, max_delay_minutes: int = 240) -> int | None:
    index = int(np.searchsorted(ts, np.datetime64(decision), side="left"))
    if index >= len(ts):
        return None
    observed = pd.Timestamp(ts[index])
    # GOLD# has a regular daily market-closure gap.  A journey decision remains
    # causal and executable at the first observed open inside one H4 interval;
    # weekend-size gaps are not backfilled as entries.
    if observed - decision > pd.Timedelta(minutes=max_delay_minutes):
        return None
    return index


def barrier_order(
    direction: int,
    entry: float,
    scale: float,
    highs: np.ndarray,
    lows: np.ndarray,
    multiple: float,
) -> str:
    favorable = entry + direction * multiple * scale
    adverse = entry - direction * multiple * scale
    fav_touch = highs >= favorable if direction > 0 else lows <= favorable
    adv_touch = lows <= adverse if direction > 0 else highs >= adverse
    fav_positions = np.flatnonzero(fav_touch)
    adv_positions = np.flatnonzero(adv_touch)
    fav = int(fav_positions[0]) if len(fav_positions) else None
    adv = int(adv_positions[0]) if len(adv_positions) else None
    if fav is None and adv is None:
        return "NEITHER"
    if fav is None:
        return "ADVERSE_FIRST"
    if adv is None:
        return "FAVORABLE_FIRST"
    if fav == adv:
        return "SAME_M1_AMBIGUOUS"
    return "FAVORABLE_FIRST" if fav < adv else "ADVERSE_FIRST"


def transition_indices(states: np.ndarray) -> list[int]:
    result: list[int] = []
    previous = 0
    for index, value in enumerate(states):
        value = int(value)
        if value == 0:
            continue
        if previous == 0 or value != previous:
            result.append(index)
            previous = value
    return result


def transition_bridge_start(h4: pd.DataFrame, signal_index: int, model: str) -> int:
    if model != "STD_SLOW_MEMORY":
        return signal_index
    new_direction = int(h4.iloc[signal_index]["state_std_slow_memory"])
    previous_direction = -new_direction
    index = signal_index - 1
    while index >= 0 and int(h4.iloc[index]["phase_core"]) == 0:
        index -= 1
    if index >= 0 and int(h4.iloc[index]["phase_core"]) == previous_direction:
        return index + 1
    return signal_index


def build_journeys(m1: pd.DataFrame, h4: pd.DataFrame, model: str, state_column: str) -> pd.DataFrame:
    ts = m1["timestamp"].to_numpy(dtype="datetime64[ns]")
    opens = m1["open"].to_numpy(dtype=float)
    highs = m1["high"].to_numpy(dtype=float)
    lows = m1["low"].to_numpy(dtype=float)
    states = h4[state_column].to_numpy(dtype=int)
    signals = transition_indices(states)
    rows: list[dict[str, object]] = []

    for position, signal_index in enumerate(signals[:-1]):
        if signal_index < WARMUP_H4:
            continue
        next_index = signals[position + 1]
        direction = int(states[signal_index])
        if int(states[next_index]) == direction:
            continue
        decision = pd.Timestamp(h4.iloc[signal_index]["decision"])
        exit_decision = pd.Timestamp(h4.iloc[next_index]["decision"])
        entry_index = first_m1_index(ts, decision)
        exit_index = first_m1_index(ts, exit_decision)
        if entry_index is None or exit_index is None or exit_index <= entry_index:
            continue
        scale = float(h4.iloc[signal_index]["atr180"])
        if not math.isfinite(scale) or scale <= 0:
            continue
        entry = float(opens[entry_index])
        exit_price = float(opens[exit_index])
        segment_high = highs[entry_index : exit_index + 1]
        segment_low = lows[entry_index : exit_index + 1]
        mfe = (float(np.max(segment_high)) - entry) if direction > 0 else (entry - float(np.min(segment_low)))
        mae = (entry - float(np.min(segment_low))) if direction > 0 else (float(np.max(segment_high)) - entry)
        net = direction * (exit_price - entry)
        close_path = h4.iloc[signal_index : next_index + 1]["close"].to_numpy(dtype=float)
        gross_path = float(np.abs(np.diff(close_path)).sum()) if len(close_path) > 1 else 0.0
        bridge_start = transition_bridge_start(h4, signal_index, model)
        bridge = h4.iloc[bridge_start : signal_index + 1]
        stop = float(bridge["low"].min()) if direction > 0 else float(bridge["high"].max())
        risk = direction * (entry - stop)
        stop_valid = int(risk > 0)
        if stop_valid:
            touch = segment_low <= stop if direction > 0 else segment_high >= stop
            locations = np.flatnonzero(touch)
            stop_hit = int(len(locations) > 0)
            stop_offset = int(locations[0]) if stop_hit else -1
            child_exit_index = entry_index + stop_offset if stop_hit else exit_index
            child_exit = stop if stop_hit else exit_price
            child_r = direction * (child_exit - entry) / risk
            child_exit_time = pd.Timestamp(ts[child_exit_index])
        else:
            stop_hit = 0
            child_r = math.nan
            child_exit_time = pd.NaT
        rows.append({
            "model": model,
            "journey_id": f"{model}_{decision:%Y%m%d%H%M}_{'L' if direction > 0 else 'S'}",
            "signal_h4_index": signal_index,
            "bridge_start_h4_index": bridge_start,
            "bridge_bars": signal_index - bridge_start + 1,
            "decision": decision,
            "entry_time": pd.Timestamp(ts[entry_index]),
            "exit_decision": exit_decision,
            "exit_time": pd.Timestamp(ts[exit_index]),
            "direction": direction,
            "year": decision.year,
            "duration_h4": next_index - signal_index,
            "entry": entry,
            "journey_exit": exit_price,
            "atr180": scale,
            "net_atr": net / scale,
            "mfe_atr": mfe / scale,
            "mae_atr": mae / scale,
            "path_efficiency": net / gross_path if gross_path > 0 else math.nan,
            "barrier_05": barrier_order(direction, entry, scale, segment_high, segment_low, 0.5),
            "barrier_10": barrier_order(direction, entry, scale, segment_high, segment_low, 1.0),
            "stop": stop,
            "risk_atr": risk / scale if stop_valid else math.nan,
            "stop_valid": stop_valid,
            "stop_hit": stop_hit if stop_valid else math.nan,
            "child_exit_time": child_exit_time,
            "child_R": child_r,
            "fast_dir_at_signal": int(h4.iloc[signal_index]["fast_dir"]),
            "std_dir_at_signal": int(h4.iloc[signal_index]["std_dir"]),
            "slow_dir_at_signal": int(h4.iloc[signal_index]["slow_dir"]),
        })
    return pd.DataFrame(rows)


def maximum_streak(values: Iterable[bool]) -> int:
    best = current = 0
    for value in values:
        current = current + 1 if bool(value) else 0
        best = max(best, current)
    return best


def summarize(group: pd.DataFrame) -> dict[str, object]:
    valid = group[group["stop_valid"].eq(1)].copy()
    child_r = valid["child_R"].dropna()
    positive_r = child_r[child_r > 0]
    top_decile_cut = positive_r.quantile(0.9) if len(positive_r) else math.nan
    top_decile_r = float(positive_r[positive_r >= top_decile_cut].sum()) if len(positive_r) else math.nan
    total_positive_r = float(positive_r.sum()) if len(positive_r) else math.nan
    return {
        "journeys": len(group),
        "long": int(group["direction"].eq(1).sum()),
        "short": int(group["direction"].eq(-1).sum()),
        "median_duration_h4": float(group["duration_h4"].median()),
        "median_net_atr": float(group["net_atr"].median()),
        "positive_net_rate": float(group["net_atr"].gt(0).mean()),
        "median_mfe_atr": float(group["mfe_atr"].median()),
        "median_mae_atr": float(group["mae_atr"].median()),
        "median_path_efficiency": float(group["path_efficiency"].median()),
        "favorable_first_05": float(group["barrier_05"].eq("FAVORABLE_FIRST").mean()),
        "adverse_first_05": float(group["barrier_05"].eq("ADVERSE_FIRST").mean()),
        "favorable_first_10": float(group["barrier_10"].eq("FAVORABLE_FIRST").mean()),
        "adverse_first_10": float(group["barrier_10"].eq("ADVERSE_FIRST").mean()),
        "valid_children": len(valid),
        "median_risk_atr": float(valid["risk_atr"].median()) if len(valid) else math.nan,
        "stops": int(valid["stop_hit"].sum()) if len(valid) else 0,
        "stop_rate": float(valid["stop_hit"].mean()) if len(valid) else math.nan,
        "wins": int(child_r.gt(0).sum()),
        "win_rate": float(child_r.gt(0).mean()) if len(child_r) else math.nan,
        "total_R": float(child_r.sum()) if len(child_r) else math.nan,
        "median_R": float(child_r.median()) if len(child_r) else math.nan,
        "R_over_3": float(child_r[child_r >= 3.0].sum()) if len(child_r) else math.nan,
        "positive_R_top_decile_share": top_decile_r / total_positive_r if total_positive_r > 0 else math.nan,
        "max_stop_streak": maximum_streak(valid.sort_values("decision")["stop_hit"].eq(1)),
    }


def summary_table(journeys: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for model, group in journeys.groupby("model", sort=False):
        rows.append({"model": model, "segment": "ALL", **summarize(group)})
        for year, year_group in group.groupby("year", sort=True):
            rows.append({"model": model, "segment": str(int(year)), **summarize(year_group)})
        for direction, side_group in group.groupby("direction", sort=True):
            rows.append({"model": model, "segment": "LONG" if direction > 0 else "SHORT", **summarize(side_group)})
    return pd.DataFrame(rows)


def state_census(h4: pd.DataFrame, models: dict[str, str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    eligible = h4.iloc[WARMUP_H4:].copy()
    for model, column in models.items():
        states = eligible[column].to_numpy(dtype=int)
        signals = transition_indices(states)
        rows.append({
            "model": model,
            "eligible_h4": len(eligible),
            "directional_h4": int(np.count_nonzero(states)),
            "neutral_h4": int(np.count_nonzero(states == 0)),
            "transition_signals": max(0, len(signals) - 1),
            "transitions_per_1000_h4": 1000.0 * max(0, len(signals) - 1) / len(eligible),
        })
    return pd.DataFrame(rows)


def file_receipt(path: Path) -> dict[str, object]:
    return {"path": str(path.resolve()), "sha256": sha256_file(path), "bytes": path.stat().st_size}


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    m1, h4, quality = rebuild_market(args.m1)
    h4 = add_state_machines(h4)
    models = {
        "FAST_REFERENCE": "state_fast_reference",
        "STD_RUN": "state_std",
        "SLOW_RUN": "state_slow",
        "STD_SLOW_MEMORY": "state_std_slow_memory",
    }
    ledgers = [build_journeys(m1, h4, model, column) for model, column in models.items()]
    journeys = pd.concat(ledgers, ignore_index=True)
    census = state_census(h4, models)
    summary = summary_table(journeys)

    h4_path = args.out_dir / "V11_NEW_SKELETON_H4_STATE.csv"
    journey_path = args.out_dir / "V11_NEW_SKELETON_JOURNEYS.csv"
    census_path = args.out_dir / "V11_NEW_SKELETON_STATE_CENSUS.csv"
    summary_path = args.out_dir / "V11_NEW_SKELETON_SUMMARY.csv"
    quality_path = args.out_dir / "V11_NEW_SKELETON_DATA_QUALITY.json"
    manifest_path = args.out_dir / "V11_NEW_SKELETON_MANIFEST.json"
    h4.to_csv(h4_path, index=False)
    journeys.to_csv(journey_path, index=False)
    census.to_csv(census_path, index=False)
    summary.to_csv(summary_path, index=False)
    quality_path.write_text(json.dumps(quality, indent=2, default=json_default) + "\n", encoding="utf-8")

    manifest = {
        "status": "CONSUMED_DEVELOPMENT_EVIDENCE_ONLY",
        "source": file_receipt(args.m1),
        "contract": {
            "candidate_source": "chronological raw M1 -> completed H4",
            "v10_trade_ledger_used": False,
            "v10_hard_sl_used": False,
            "fast_role": "reference only; absent from STD_SLOW_MEMORY state machine",
            "primary_candidate": "STD_SLOW_MEMORY",
            "primary_child": "one Child per journey reversal",
            "primary_stop": "opposite raw-H4 extreme of causal transition bridge",
            "costs": "not modeled",
            "authority": "none",
        },
        "outputs": [
            file_receipt(h4_path),
            file_receipt(journey_path),
            file_receipt(census_path),
            file_receipt(summary_path),
            file_receipt(quality_path),
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, default=json_default) + "\n", encoding="utf-8")
    print(summary[summary["segment"].eq("ALL")].to_string(index=False))
    print(f"\nWrote {args.out_dir}")


if __name__ == "__main__":
    main()
