from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd


START = pd.Timestamp("2024-01-01 00:00:00")
CANONICAL_CUTOFF = pd.Timestamp("2026-08-28 20:00:00")
COMMENT_RE = re.compile(r"^V13P\|J(?P<journey>\d{6})\|C(?P<child>\d{2})\|(?P<side>[LS])$")
EPS = 1e-9


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_mt5_bars(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep="\t")
    frame["time"] = pd.to_datetime(
        frame["<DATE>"] + " " + frame["<TIME>"], format="%Y.%m.%d %H:%M:%S"
    )
    frame = frame.rename(
        columns={
            "<OPEN>": "open",
            "<HIGH>": "high",
            "<LOW>": "low",
            "<CLOSE>": "close",
            "<TICKVOL>": "tick_volume",
            "<SPREAD>": "spread_points",
        }
    )
    numeric = ["open", "high", "low", "close", "tick_volume", "spread_points"]
    for column in numeric:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="raise")
    frame = frame.sort_values("time").reset_index(drop=True)
    if not frame.time.is_monotonic_increasing or frame.time.duplicated().any():
        raise RuntimeError(f"bar timestamps are not unique and ordered: {path}")
    return frame


def add_standard_ha(frame: pd.DataFrame, prefix: str = "ha") -> pd.DataFrame:
    result = frame.copy()
    previous_open = None
    previous_close = None
    previous_color = 0
    streak = 0
    values: list[dict[str, float | int]] = []
    for row in result.itertuples(index=False):
        ha_close = (row.open + row.high + row.low + row.close) / 4.0
        ha_open = (
            (row.open + row.close) / 2.0
            if previous_open is None
            else (previous_open + previous_close) / 2.0
        )
        ha_high = max(row.high, ha_open, ha_close)
        ha_low = min(row.low, ha_open, ha_close)
        color = 1 if ha_close > ha_open else -1 if ha_close < ha_open else previous_color
        streak = streak + 1 if previous_color and color == previous_color else 1
        upper_wick = ha_high - max(ha_open, ha_close)
        lower_wick = min(ha_open, ha_close) - ha_low
        opposite_wick = lower_wick if color == 1 else upper_wick
        ha_range = ha_high - ha_low
        values.append(
            {
                f"{prefix}_open": ha_open,
                f"{prefix}_close": ha_close,
                f"{prefix}_high": ha_high,
                f"{prefix}_low": ha_low,
                f"{prefix}_color": color,
                f"{prefix}_streak": streak,
                f"{prefix}_delta": ha_close - ha_open,
                f"{prefix}_abs_delta": abs(ha_close - ha_open),
                f"{prefix}_body_ratio": abs(ha_close - ha_open) / ha_range if ha_range else 0.0,
                f"{prefix}_opposite_wick": opposite_wick,
            }
        )
        previous_open, previous_close, previous_color = ha_open, ha_close, color
    return pd.concat([result, pd.DataFrame(values, index=result.index)], axis=1)


def parse_comment(value: object) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    match = COMMENT_RE.match(value.strip())
    if match is None:
        return None
    return (
        int(match.group("journey")),
        int(match.group("child")),
        1 if match.group("side") == "L" else -1,
    )


def parse_mt5_report(path: Path) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_excel(path, sheet_name=0, header=None, dtype=object)
    deal_rows = raw.loc[raw[4].isin(["in", "out"]), list(range(13))].copy()
    deal_rows.columns = [
        "time",
        "deal",
        "symbol",
        "type",
        "direction",
        "volume",
        "price",
        "order",
        "commission",
        "swap",
        "profit",
        "balance",
        "comment",
    ]
    deal_rows["time"] = pd.to_datetime(deal_rows.time, format="%Y.%m.%d %H:%M:%S")
    for column in ["deal", "volume", "price", "order", "commission", "swap", "profit", "balance"]:
        deal_rows[column] = pd.to_numeric(deal_rows[column], errors="raise")
    deal_rows = deal_rows.sort_values(["time", "deal"]).reset_index(drop=True)

    open_positions: list[dict] = []
    completed: list[dict] = []
    unmatched_entries = 0
    for row in deal_rows.itertuples(index=False):
        if row.direction == "in":
            identity = parse_comment(row.comment)
            if identity is None:
                unmatched_entries += 1
                continue
            journey, child, side = identity
            expected_type = "buy" if side == 1 else "sell"
            if row.type != expected_type:
                raise RuntimeError(f"entry side/comment mismatch at deal {row.deal}")
            open_positions.append(
                {
                    "journey": journey,
                    "child": child,
                    "side": side,
                    "entry_time": row.time,
                    "entry_deal": int(row.deal),
                    "entry_order": int(row.order),
                    "entry_price_actual": float(row.price),
                    "volume": float(row.volume),
                    "entry_comment": row.comment,
                }
            )
            continue

        closing_side = 1 if row.type == "sell" else -1 if row.type == "buy" else 0
        candidates = [
            (index, position)
            for index, position in enumerate(open_positions)
            if position["side"] == closing_side
            and math.isclose(position["volume"], float(row.volume), abs_tol=1e-12)
        ]
        if not candidates:
            raise RuntimeError(f"no open Child matches exit deal {row.deal}")

        def score(candidate: tuple[int, dict]) -> tuple[float, pd.Timestamp, int]:
            index, position = candidate
            expected_profit = position["side"] * (
                float(row.price) - position["entry_price_actual"]
            )
            return abs(expected_profit - float(row.profit)), position["entry_time"], index

        selected_index, position = min(candidates, key=score)
        match_error = score((selected_index, position))[0]
        if match_error > 0.011:
            raise RuntimeError(
                f"exit deal {row.deal} Child match error {match_error:.6f} exceeds cent rounding"
            )
        open_positions.pop(selected_index)
        completed.append(
            {
                **position,
                "exit_time": row.time,
                "exit_deal": int(row.deal),
                "exit_order": int(row.order),
                "exit_price_actual": float(row.price),
                "commission": float(row.commission),
                "swap": float(row.swap),
                "profit_actual": float(row.profit),
                "exit_comment": row.comment if isinstance(row.comment, str) else "",
                "match_error": match_error,
            }
        )

    trades = pd.DataFrame(completed).sort_values(["entry_time", "entry_deal"]).reset_index(drop=True)
    if open_positions:
        raise RuntimeError(f"{len(open_positions)} report positions remain unmatched")
    if trades[["journey", "child"]].duplicated().any():
        duplicates = trades.loc[trades[["journey", "child"]].duplicated(False), ["journey", "child"]]
        raise RuntimeError(f"duplicate Child identities in report: {duplicates.head().to_dict('records')}")
    trades["hold_hours"] = (trades.exit_time - trades.entry_time).dt.total_seconds() / 3600.0
    quality = {
        "report_rows": int(len(raw)),
        "deal_rows": int(len(deal_rows)),
        "entry_deals": int((deal_rows.direction == "in").sum()),
        "exit_deals": int((deal_rows.direction == "out").sum()),
        "completed_children": int(len(trades)),
        "strict_positive_children": int((trades.profit_actual > 0).sum()),
        "strict_negative_children": int((trades.profit_actual < 0).sum()),
        "zero_profit_children": int((trades.profit_actual == 0).sum()),
        "unmatched_entry_comments": int(unmatched_entries),
        "duplicate_child_keys": int(trades[["journey", "child"]].duplicated().sum()),
        "max_profit_match_error": float(trades.match_error.max()),
        "report_first_entry": str(trades.entry_time.min()),
        "report_last_exit": str(trades.exit_time.max()),
    }
    return trades, quality


def load_idealized_ledger(path: Path) -> pd.DataFrame:
    ledger = pd.read_csv(path)
    for column in ["signal", "proof_time"]:
        ledger[column] = pd.to_datetime(ledger[column], errors="coerce")
    return ledger


def path_state(opposed: list[bool]) -> tuple[str, str, int]:
    if not opposed:
        return "missing", "", 0
    path = "".join("1" if value else "0" for value in opposed)
    trailing = 0
    for value in reversed(opposed):
        if not value:
            break
        trailing += 1
    if not any(opposed):
        state = "no_opposition"
    elif not opposed[-1]:
        state = "repaired"
    elif all(opposed):
        state = "persistent_opposition"
    else:
        state = "unrepaired_mixed"
    return state, path, trailing


class M1Window:
    def __init__(self, frame: pd.DataFrame):
        self.times = frame.time.to_numpy(dtype="datetime64[ns]")
        self.time_ns = self.times.astype("int64")
        self.high = frame.high.to_numpy(float)
        self.low = frame.low.to_numpy(float)
        self.close = frame.close.to_numpy(float)

    def bounds(self, start: pd.Timestamp, end: pd.Timestamp) -> tuple[int, int]:
        lo = int(np.searchsorted(self.time_ns, np.datetime64(start, "ns").astype("int64"), side="left"))
        hi = int(np.searchsorted(self.time_ns, np.datetime64(end, "ns").astype("int64"), side="left"))
        return lo, hi

    def proof_time(
        self, start: pd.Timestamp, end: pd.Timestamp, side: int, target: float
    ) -> pd.Timestamp | None:
        lo, hi = self.bounds(start.floor("min"), end)
        if lo >= hi:
            return None
        hits = np.flatnonzero(self.high[lo:hi] > target + EPS) if side == 1 else np.flatnonzero(self.low[lo:hi] < target - EPS)
        if not len(hits):
            return None
        return pd.Timestamp(self.times[lo + int(hits[0])])

    def checkpoint_metrics(
        self, start: pd.Timestamp, end: pd.Timestamp, side: int, entry: float
    ) -> dict[str, float]:
        lo, hi = self.bounds(start.floor("min"), end)
        if lo >= hi:
            return {
                "mfe": np.nan,
                "mae": np.nan,
                "directional_progress": np.nan,
                "directional_efficiency": np.nan,
            }
        high = self.high[lo:hi]
        low = self.low[lo:hi]
        closes = self.close[lo:hi]
        if side == 1:
            mfe = float(np.max(high) - entry)
            mae = float(entry - np.min(low))
        else:
            mfe = float(entry - np.min(low))
            mae = float(np.max(high) - entry)
        path = np.r_[entry, closes]
        traveled = float(np.abs(np.diff(path)).sum())
        progress = float(side * (closes[-1] - entry))
        efficiency = progress / traveled if traveled > 0 else 0.0
        return {
            "mfe": mfe,
            "mae": mae,
            "directional_progress": progress,
            "directional_efficiency": efficiency,
        }

    def post_exit_metrics(
        self,
        start: pd.Timestamp,
        end: pd.Timestamp,
        side: int,
        entry: float,
        exit_price: float,
        signal_extreme: float,
    ) -> dict[str, float | bool]:
        # Start on the following minute. Same-minute ordering after the exit is unknowable in OHLC.
        lo, hi = self.bounds(start.floor("min") + pd.Timedelta(minutes=1), end)
        if lo >= hi:
            return {
                "post_exit_additional_favorable": 0.0,
                "post_exit_best_pnl_from_entry": side * (exit_price - entry),
                "post_exit_reaches_entry": False,
                "post_exit_reaches_signal_extreme": False,
            }
        if side == 1:
            best = float(np.max(self.high[lo:hi]))
            additional = best - exit_price
            reaches_entry = best >= entry - EPS
            reaches_signal = best > signal_extreme + EPS
        else:
            best = float(np.min(self.low[lo:hi]))
            additional = exit_price - best
            reaches_entry = best <= entry + EPS
            reaches_signal = best < signal_extreme - EPS
        return {
            "post_exit_additional_favorable": float(additional),
            "post_exit_best_pnl_from_entry": float(side * (best - entry)),
            "post_exit_reaches_entry": bool(reaches_entry),
            "post_exit_reaches_signal_extreme": bool(reaches_signal),
        }


def build_h4_features(h4: pd.DataFrame) -> pd.DataFrame:
    frame = add_standard_ha(h4, "h4ha")
    d = frame.h4ha_open - frame.h4ha_close
    hstoc = []
    width = []
    for index in range(len(frame)):
        if index < 9:
            hstoc.append(np.nan)
            width.append(np.nan)
            continue
        window = d.iloc[index - 9 : index + 1]
        span = float(window.max() - window.min())
        width.append(span)
        hstoc.append(100.0 * (float(d.iloc[index]) - float(window.min())) / span if span else np.nan)
    frame["hastoc10"] = hstoc
    frame["hastoc_width"] = width
    frame["h4_delta_contract"] = frame.h4ha_abs_delta < frame.h4ha_abs_delta.shift(1)
    frame["h4_wick_present"] = frame.h4ha_opposite_wick > EPS
    frame["h4_wick_reappeared"] = (
        (frame.h4ha_opposite_wick.shift(1) <= EPS) & (frame.h4ha_opposite_wick > EPS)
    )
    raw_range = frame.high - frame.low
    frame["h4_raw_close_normalized"] = np.where(
        raw_range > 0,
        frame.h4ha_color * (frame.close - frame.h4ha_close) / raw_range,
        0.0,
    )
    return frame


def add_h1_activity(h1: pd.DataFrame) -> pd.DataFrame:
    frame = add_standard_ha(h1, "h1ha")
    frame["hour"] = frame.time.dt.hour
    frame["same_hour_median20"] = frame.groupby("hour").tick_volume.transform(
        lambda series: series.shift(1).rolling(20, min_periods=20).median()
    )
    frame["relative_tick_volume20"] = frame.tick_volume / frame.same_hour_median20
    frame["h4_bucket"] = frame.time.dt.floor("4h")
    return frame


def feature_for_trade(
    row,
    h1: pd.DataFrame,
    h4_feature_by_time: pd.DataFrame,
    m1: M1Window,
    journey_end: pd.Timestamp,
) -> dict:
    side = int(row.side)
    signal_time = pd.Timestamp(row.signal)
    proof_h4_start = pd.Timestamp(row.entry_time).floor("4h")
    proof_h4_end = proof_h4_start + pd.Timedelta(hours=4)
    target = float(row.signal_high if side == 1 else row.signal_low)
    observed_until = min(pd.Timestamp(row.exit_time), proof_h4_end)
    proof_time = m1.proof_time(pd.Timestamp(row.entry_time), proof_h4_end, side, target)

    inside_all = h1[(h1.time >= proof_h4_start) & (h1.time < proof_h4_end)].copy()
    inside_observed = inside_all.loc[
        inside_all.time + pd.Timedelta(hours=1) <= observed_until
    ].copy()
    inside_all["ordinal"] = np.arange(1, len(inside_all) + 1)
    inside_observed["ordinal"] = np.arange(1, len(inside_observed) + 1)

    proof_ordinal = np.nan
    if proof_time is not None and len(inside_all):
        proof_hour = proof_time.floor("h")
        matching = inside_all.index[inside_all.time == proof_hour].tolist()
        if matching:
            proof_ordinal = int(inside_all.loc[matching[0], "ordinal"])

    def accepted(frame: pd.DataFrame) -> pd.Series:
        return frame.close > target + EPS if side == 1 else frame.close < target - EPS

    observed_accept = accepted(inside_observed) if len(inside_observed) else pd.Series(dtype=bool)
    full_accept = accepted(inside_all) if len(inside_all) else pd.Series(dtype=bool)
    first_accept_observed = (
        int(inside_observed.loc[observed_accept, "ordinal"].iloc[0]) if observed_accept.any() else np.nan
    )
    first_accept_full = int(inside_all.loc[full_accept, "ordinal"].iloc[0]) if full_accept.any() else np.nan
    aligned_accept_observed = bool(
        (observed_accept & (inside_observed.h1ha_color == side)).any()
    ) if len(inside_observed) else False
    aligned_accept_full = bool((full_accept & (inside_all.h1ha_color == side)).any()) if len(inside_all) else False

    proof_h1_close_inside = False
    if proof_time is not None and len(inside_all):
        proof_bar = inside_all.loc[inside_all.time == proof_time.floor("h")]
        if len(proof_bar):
            proof_h1_close_inside = not bool(accepted(proof_bar).iloc[0])

    opposed_observed = (inside_observed.h1ha_color != side).astype(bool).tolist()
    opposed_full = (inside_all.h1ha_color != side).astype(bool).tolist()
    observed_state, observed_path, observed_trailing = path_state(opposed_observed)
    full_state, full_path, full_trailing = path_state(opposed_full)

    features: dict[str, object] = {
        "proof_h4_start": proof_h4_start,
        "proof_h4_end": proof_h4_end,
        "proof_time_m1": proof_time,
        "proof_h1_ordinal": proof_ordinal,
        "proof_speed": (
            "no_proof"
            if proof_time is None
            else "h1_1"
            if proof_ordinal == 1
            else "h1_2"
            if proof_ordinal == 2
            else "h1_3_4"
        ),
        "h1_bars_observed_before_exit": int(len(inside_observed)),
        "h1_bars_in_proof_h4": int(len(inside_all)),
        "h1_acceptance_by_exit": bool(observed_accept.any()),
        "h1_aligned_acceptance_by_exit": aligned_accept_observed,
        "first_accept_h1_by_exit": first_accept_observed,
        "h1_acceptance_by_h4_end": bool(full_accept.any()),
        "h1_aligned_acceptance_by_h4_end": aligned_accept_full,
        "first_accept_h1_by_h4_end": first_accept_full,
        "proof_h1_close_back_inside": bool(proof_h1_close_inside),
        "h1_path_state_by_exit": observed_state,
        "h1_path_by_exit": observed_path,
        "h1_trailing_opposed_by_exit": observed_trailing,
        "h1_path_state_full_proof_h4": full_state,
        "h1_path_full_proof_h4": full_path,
        "h1_trailing_opposed_full_proof_h4": full_trailing,
        "h1_relative_activity_mean_by_exit": float(inside_observed.relative_tick_volume20.mean()) if len(inside_observed) else np.nan,
        "h1_relative_activity_mean_full_h4": float(inside_all.relative_tick_volume20.mean()) if len(inside_all) else np.nan,
    }

    for checkpoint, ordinal in [("h1_1", 1), ("h1_2", 2)]:
        if len(inside_all) < ordinal:
            metrics = {"mfe": np.nan, "mae": np.nan, "directional_progress": np.nan, "directional_efficiency": np.nan}
            checkpoint_time = pd.NaT
            checkpoint_state = "missing"
        else:
            checkpoint_time = pd.Timestamp(inside_all.iloc[ordinal - 1].time) + pd.Timedelta(hours=1)
            if checkpoint_time > pd.Timestamp(row.exit_time):
                metrics = {"mfe": np.nan, "mae": np.nan, "directional_progress": np.nan, "directional_efficiency": np.nan}
                checkpoint_state = "not_reached_before_exit"
            else:
                metrics = m1.checkpoint_metrics(
                    pd.Timestamp(row.entry_time), checkpoint_time, side, float(row.entry_price_actual)
                )
                prefix = inside_all.iloc[:ordinal]
                checkpoint_state = path_state((prefix.h1ha_color != side).astype(bool).tolist())[0]
        features[f"{checkpoint}_checkpoint_time"] = checkpoint_time
        features[f"{checkpoint}_path_state"] = checkpoint_state
        for name, value in metrics.items():
            features[f"{checkpoint}_{name}"] = value

    signal_feature = h4_feature_by_time.loc[signal_time]
    journey_hastoc = (
        100.0 - float(signal_feature.hastoc10)
        if side == 1 and pd.notna(signal_feature.hastoc10)
        else float(signal_feature.hastoc10)
        if pd.notna(signal_feature.hastoc10)
        else np.nan
    )
    features.update(
        {
            "signal_h4_body_ratio": float(signal_feature.h4ha_body_ratio),
            "signal_h4_abs_delta": float(signal_feature.h4ha_abs_delta),
            "signal_h4_delta_contract": bool(signal_feature.h4_delta_contract),
            "signal_h4_wick_present": bool(signal_feature.h4_wick_present),
            "signal_h4_wick_reappeared": bool(signal_feature.h4_wick_reappeared),
            "signal_h4_raw_close_normalized": float(signal_feature.h4_raw_close_normalized),
            "signal_h4_streak": int(signal_feature.h4ha_streak),
            "signal_journey_hastoc10": journey_hastoc,
        }
    )

    post = m1.post_exit_metrics(
        pd.Timestamp(row.exit_time),
        journey_end,
        side,
        float(row.entry_price_actual),
        float(row.exit_price_actual),
        target,
    )
    features.update(post)
    return features


def safe_rate(series: pd.Series) -> float | None:
    return float(series.astype(float).mean()) if len(series) else None


def safe_median(series: pd.Series) -> float | None:
    values = pd.to_numeric(series, errors="coerce").dropna()
    return float(values.median()) if len(values) else None


def summarize_loss_group(group: pd.DataFrame) -> dict:
    return {
        "n": int(len(group)),
        "actual_net": float(group.profit_actual.sum()),
        "post_exit_reaches_entry_rate": safe_rate(group.post_exit_reaches_entry),
        "post_exit_reaches_signal_extreme_rate": safe_rate(group.post_exit_reaches_signal_extreme),
        "standard_h4_exit_positive_rate": safe_rate(group.standard_h4_exit_pnl_actual_entry > 0),
        "standard_h4_exit_better_rate": safe_rate(group.standard_h4_exit_pnl_actual_entry > group.profit_actual),
        "post_exit_best_pnl_median": safe_median(group.post_exit_best_pnl_from_entry),
        "post_exit_additional_favorable_median": safe_median(group.post_exit_additional_favorable),
    }


def summarize_fast_winner_group(group: pd.DataFrame) -> dict:
    return {
        "n": int(len(group)),
        "actual_net": float(group.profit_actual.sum()),
        "standard_h4_exit_better_rate": safe_rate(group.standard_h4_exit_pnl_actual_entry > group.profit_actual),
        "standard_h4_exit_positive_rate": safe_rate(group.standard_h4_exit_pnl_actual_entry > 0),
        "post_exit_reaches_signal_extreme_rate": safe_rate(group.post_exit_reaches_signal_extreme),
        "standard_minus_actual_median": safe_median(group.standard_h4_exit_pnl_actual_entry - group.profit_actual),
        "post_exit_additional_favorable_median": safe_median(group.post_exit_additional_favorable),
    }


def summarize_actual(group: pd.DataFrame) -> dict:
    positive = group.loc[group.profit_actual > 0, "profit_actual"]
    negative = group.loc[group.profit_actual < 0, "profit_actual"]
    wins = int(len(positive))
    losses = int(len(negative))
    flats = int((group.profit_actual == 0).sum())
    gross_win = float(positive.sum())
    gross_loss = float(-negative.sum())
    return {
        "n": int(len(group)),
        "wins": wins,
        "losses": losses,
        "flats": flats,
        "win_rate_nonflat": wins / (wins + losses) if wins + losses else None,
        "profit_factor": gross_win / gross_loss if gross_loss else None,
        "net_usd": float(group.profit_actual.sum()),
        "median_hold_hours": safe_median(group.hold_hours),
    }


def hold_outcome_summary(add_ons: pd.DataFrame) -> dict:
    buckets = pd.Series(index=add_ons.index, dtype="object")
    buckets.loc[add_ons.hold_hours <= 1.0] = "le_1h"
    buckets.loc[(add_ons.hold_hours > 1.0) & (add_ons.hold_hours < 4.0)] = "gt1_lt4h"
    buckets.loc[(add_ons.hold_hours >= 4.0) & (add_ons.hold_hours < 8.0)] = "ge4_lt8h"
    buckets.loc[add_ons.hold_hours >= 8.0] = "ge8h"
    output = {}
    for bucket, group in add_ons.groupby(buckets):
        output[str(bucket)] = summarize_actual(group)
    return output


def grouped_summary(frame: pd.DataFrame, columns: list[str], kind: str, min_count: int = 20) -> dict:
    output: dict[str, dict] = {}
    summarize = summarize_loss_group if kind == "loss" else summarize_fast_winner_group
    for column in columns:
        groups = {}
        for value, group in frame.groupby(column, dropna=False):
            if len(group) < min_count:
                continue
            label = "missing" if pd.isna(value) else str(value)
            groups[label] = summarize(group)
        output[column] = groups
    return output


def numeric_contrast(frame: pd.DataFrame, target: pd.Series, columns: list[str]) -> dict:
    output = {}
    for column in columns:
        valid = frame[column].notna() & target.notna()
        if valid.sum() < 30 or target.loc[valid].nunique() < 2:
            continue
        values = frame.loc[valid, column].astype(float)
        labels = target.loc[valid].astype(bool)
        output[column] = {
            "n": int(valid.sum()),
            "target_true": int(labels.sum()),
            "median_true": float(values.loc[labels].median()),
            "median_false": float(values.loc[~labels].median()),
            "spearman": float(values.rank(method="average").corr(labels.astype(float).rank(method="average"))),
        }
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--h1", type=Path, required=True)
    parser.add_argument("--h4", type=Path, required=True)
    parser.add_argument("--m1", type=Path, required=True)
    parser.add_argument("--ideal-ledger", type=Path, required=True)
    parser.add_argument("--integrated-features", type=Path, required=True)
    parser.add_argument("--raw-swing-features", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output.mkdir(parents=True, exist_ok=True)

    actual, report_quality = parse_mt5_report(arguments.report)
    ideal = load_idealized_ledger(arguments.ideal_ledger)
    canonical_actual = actual.loc[
        (actual.entry_time >= START) & (actual.exit_time <= CANONICAL_CUTOFF)
    ].copy()
    joined = canonical_actual.merge(
        ideal,
        on=["journey", "child", "side"],
        how="left",
        validate="one_to_one",
        suffixes=("_actual", "_ideal"),
        indicator=True,
    )
    join_coverage = int((joined._merge == "both").sum())
    if join_coverage != len(joined):
        missing = joined.loc[joined._merge != "both", ["journey", "child", "side"]]
        raise RuntimeError(f"actual-to-ideal Child join misses: {missing.head().to_dict('records')}")
    joined = joined.drop(columns="_merge")

    h1 = add_h1_activity(load_mt5_bars(arguments.h1))
    h4 = build_h4_features(load_mt5_bars(arguments.h4))
    h4_feature_by_time = h4.set_index("time")
    m1 = M1Window(load_mt5_bars(arguments.m1))

    c1_exit = actual.loc[actual.child == 1, ["journey", "exit_time", "exit_price_actual"]].rename(
        columns={"exit_time": "journey_end_time", "exit_price_actual": "journey_exit_price_actual"}
    )
    joined = joined.merge(c1_exit, on="journey", how="left", validate="many_to_one")
    if joined.journey_end_time.isna().any():
        raise RuntimeError("missing Child #1 Journey end for canonical actual trades")

    records = []
    for row in joined.itertuples(index=False):
        record = row._asdict()
        record.update(
            feature_for_trade(
                row,
                h1,
                h4_feature_by_time,
                m1,
                pd.Timestamp(row.journey_end_time),
            )
        )
        record["standard_h4_exit_pnl_actual_entry"] = int(row.side) * (
            float(row.journey_exit_price_actual) - float(row.entry_price_actual)
        )
        records.append(record)
    ledger = pd.DataFrame(records)

    integrated = pd.read_csv(arguments.integrated_features)
    integrated["signal"] = pd.to_datetime(integrated.signal)
    integrated_keep = [
        "signal",
        "side",
        "journey_bar",
        "fast_opposed",
        "fast_body_ratio",
        "fast_delta_contract",
        "h1_path_state",
        "h1_trailing_opposed",
    ]
    integrated = integrated[integrated_keep].rename(
        columns={
            "h1_path_state": "signal_h4_internal_h1_path_state",
            "h1_trailing_opposed": "signal_h4_internal_h1_trailing_opposed",
        }
    )
    swing = pd.read_csv(arguments.raw_swing_features)
    swing["signal"] = pd.to_datetime(swing.signal)
    swing_keep = [
        "signal",
        "side",
        "progress_state",
        "adverse_state",
        "progress_rejection_or_return",
        "progress_close_distance_ranges",
        "adverse_close_distance_ranges",
    ]
    ledger = ledger.merge(integrated, on=["signal", "side"], how="left", validate="many_to_one")
    ledger = ledger.merge(swing[swing_keep], on=["signal", "side"], how="left", validate="many_to_one")

    ledger["actual_result"] = np.where(
        ledger.profit_actual > 0, "win", np.where(ledger.profit_actual < 0, "loss", "flat")
    )
    ledger["hold_bucket"] = np.select(
        [
            ledger.hold_hours <= 1.0,
            (ledger.hold_hours > 1.0) & (ledger.hold_hours < 4.0),
            (ledger.hold_hours >= 4.0) & (ledger.hold_hours < 8.0),
            ledger.hold_hours >= 8.0,
        ],
        ["le_1h", "gt1_lt4h", "ge4_lt8h", "ge8h"],
        default="unclassified",
    )
    add_ons = ledger.loc[ledger.child >= 2].copy()
    loss_4_8 = add_ons.loc[
        (add_ons.profit_actual < 0) & (add_ons.hold_hours >= 4.0) & (add_ons.hold_hours < 8.0)
    ].copy()
    fast_winners = add_ons.loc[(add_ons.profit_actual > 0) & (add_ons.hold_hours < 4.0)].copy()

    categorical = [
        "proof_speed",
        "h1_acceptance_by_exit",
        "h1_aligned_acceptance_by_exit",
        "proof_h1_close_back_inside",
        "h1_1_path_state",
        "h1_2_path_state",
        "h1_path_state_by_exit",
        "signal_h4_delta_contract",
        "signal_h4_wick_present",
        "signal_h4_wick_reappeared",
        "fast_opposed",
        "progress_state",
        "progress_rejection_or_return",
    ]
    numeric = [
        "h1_1_mfe",
        "h1_1_mae",
        "h1_1_directional_progress",
        "h1_1_directional_efficiency",
        "h1_2_mfe",
        "h1_2_mae",
        "h1_2_directional_progress",
        "h1_2_directional_efficiency",
        "h1_relative_activity_mean_by_exit",
        "signal_h4_body_ratio",
        "signal_h4_abs_delta",
        "signal_h4_raw_close_normalized",
        "signal_journey_hastoc10",
        "journey_bar",
    ]

    report_period = {
        "all_report": {
            "children": int(len(actual)),
            "wins": int((actual.profit_actual > 0).sum()),
            "losses": int((actual.profit_actual < 0).sum()),
            "flats": int((actual.profit_actual == 0).sum()),
            "net_usd": float(actual.profit_actual.sum()),
        },
        "canonical_closed_by_cutoff": {
            "children": int(len(ledger)),
            "wins": int((ledger.profit_actual > 0).sum()),
            "losses": int((ledger.profit_actual < 0).sum()),
            "flats": int((ledger.profit_actual == 0).sum()),
            "net_usd": float(ledger.profit_actual.sum()),
            "journeys": int(ledger.journey.nunique()),
        },
    }
    child_role = {
        "child_1": summarize_actual(ledger.loc[ledger.child == 1]),
        "add_ons": summarize_actual(add_ons),
    }
    hold_outcomes = hold_outcome_summary(add_ons)
    all_report_add_ons = actual.loc[actual.child >= 2].copy()

    summary = {
        "status": "CONSUMED DEVELOPMENT / PHASE-1 MODE RESEARCH / NOT ACTION AUTHORITY",
        "question": "Which first-H4 causal states distinguish 4-8h losing add-ons from recoverable cuts, and fast harvested winners from missed runners?",
        "sources": {
            "report": {"name": arguments.report.name, "sha256": sha256(arguments.report)},
            "m1": {"name": arguments.m1.name, "sha256": sha256(arguments.m1)},
            "h1": {"name": arguments.h1.name, "sha256": sha256(arguments.h1)},
            "h4": {"name": arguments.h4.name, "sha256": sha256(arguments.h4)},
            "ideal_ledger": {"name": arguments.ideal_ledger.name, "sha256": sha256(arguments.ideal_ledger)},
        },
        "data_quality": {
            **report_quality,
            "canonical_actual_children": int(len(canonical_actual)),
            "actual_to_ideal_joined": join_coverage,
            "integrated_feature_coverage": int(ledger.journey_bar.notna().sum()),
            "raw_swing_feature_coverage": int(ledger.progress_state.notna().sum()),
            "h1_1_checkpoint_coverage": int(ledger.h1_1_mfe.notna().sum()),
            "h1_2_checkpoint_coverage": int(ledger.h1_2_mfe.notna().sum()),
        },
        "period": report_period,
        "child_roles": child_role,
        "add_on_hold_outcomes": hold_outcomes,
        "all_report_add_on_hold_outcomes": hold_outcome_summary(all_report_add_ons),
        "population_correction": {
            "all_report_add_ons_under_4h": int((all_report_add_ons.hold_hours < 4.0).sum()),
            "all_report_winning_add_ons_under_4h": int(
                ((all_report_add_ons.hold_hours < 4.0) & (all_report_add_ons.profit_actual > 0)).sum()
            ),
            "canonical_add_ons_under_4h": int((add_ons.hold_hours < 4.0).sum()),
            "canonical_winning_add_ons_under_4h": int(len(fast_winners)),
        },
        "phase1_populations": {
            "loss_4_8h": summarize_loss_group(loss_4_8),
            "fast_winner_under_4h": summarize_fast_winner_group(fast_winners),
        },
        "loss_4_8h_by_causal_state": grouped_summary(loss_4_8, categorical, "loss"),
        "fast_winner_by_causal_state": grouped_summary(fast_winners, categorical, "winner"),
        "loss_4_8h_numeric_contrast": numeric_contrast(
            loss_4_8,
            loss_4_8.standard_h4_exit_pnl_actual_entry > 0,
            numeric,
        ),
        "fast_winner_numeric_contrast": numeric_contrast(
            fast_winners,
            fast_winners.standard_h4_exit_pnl_actual_entry > fast_winners.profit_actual,
            numeric,
        ),
        "year_phase1": {},
        "causal_boundary": {
            "features": "Only signal-H4 information and M1/H1 observations available by the named checkpoint or actual exit.",
            "labels": "Post-exit movement and Standard-H4 counterfactual are future-only research labels and never candidate inputs.",
            "m1_ambiguity": "Proof may share the entry M1. Same-minute tick order is not inferred; post-exit labels begin on the next M1.",
        },
    }
    for year in sorted(ledger.entry_time.dt.year.unique()):
        year_loss = loss_4_8.loc[loss_4_8.entry_time.dt.year == year]
        year_winner = fast_winners.loc[fast_winners.entry_time.dt.year == year]
        summary["year_phase1"][str(int(year))] = {
            "loss_4_8h": summarize_loss_group(year_loss),
            "fast_winner_under_4h": summarize_fast_winner_group(year_winner),
        }

    ledger.to_csv(arguments.output / "trade_mode_ledger.csv", index=False)
    loss_4_8.to_csv(arguments.output / "loss_4_8h_ledger.csv", index=False)
    fast_winners.to_csv(arguments.output / "fast_winner_under_4h_ledger.csv", index=False)
    (arguments.output / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
