#!/usr/bin/env python3
"""Build the V12 Phase-1D broker-clock and economic-event mechanism study.

The market file is revealed only through ``iter_m1_prefix``.  Calendar values
are an immutable MT5 terminal snapshot and never authorize a trade.
"""

from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import defaultdict
import csv
from datetime import datetime, timedelta
import json
from pathlib import Path
from statistics import median
from typing import Iterable, Optional

import numpy as np
import pandas as pd

from build_v12_phase0 import PrefixAudit, iter_m1_prefix, parse_cutoff
from v12_phase0_core import sha256_file


PREFIX = "V12_PHASE1D_"
IMPORTANCE_RANK = {
    "CALENDAR_IMPORTANCE_NONE": 0,
    "CALENDAR_IMPORTANCE_LOW": 1,
    "CALENDAR_IMPORTANCE_MODERATE": 2,
    "CALENDAR_IMPORTANCE_HIGH": 3,
}
WINDOWS = (15, 30, 60, 120, 240)


def read_csv(path: Path, encoding: str = "utf-8-sig") -> list[dict]:
    with path.open("r", encoding=encoding, newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: Optional[list[str]] = None) -> None:
    names = fieldnames or []
    if not names:
        for row in rows:
            for key in row:
                if key not in names:
                    names.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not names:
            return
        writer = csv.DictWriter(handle, fieldnames=names, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_prepare_output(path: Path, replace: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(f"output directory is not empty: {path}")
        for child in path.iterdir():
            if not child.is_file() or not child.name.startswith(PREFIX):
                raise ValueError(f"refusing to replace unexpected path: {child}")
            child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def load_market(path: Path, cutoff: datetime) -> tuple[pd.DataFrame, PrefixAudit]:
    audit = PrefixAudit()
    timestamps: list[datetime] = []
    opens: list[float] = []
    highs: list[float] = []
    lows: list[float] = []
    closes: list[float] = []
    tickvols: list[int] = []
    for row in iter_m1_prefix(path, cutoff, audit=audit):
        timestamps.append(row.timestamp)
        opens.append(row.open)
        highs.append(row.high)
        lows.append(row.low)
        closes.append(row.close)
        tickvols.append(row.tick_volume)
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(timestamps),
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "tick_volume": tickvols,
        }
    )
    frame["m1_range"] = frame["high"] - frame["low"]
    return frame, audit


def load_calendar(path: Path, cutoff: datetime) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(path, encoding="cp949", low_memory=False)
    raw["server_time_dt"] = pd.to_datetime(raw["server_time"], format="%Y.%m.%d %H:%M:%S")
    before = len(raw)
    duplicate_rows = int(raw.duplicated("value_id", keep=False).sum())
    conflict_ids = []
    exact_duplicate_ids = []
    for value_id, values in raw.loc[raw.duplicated("value_id", keep=False)].groupby("value_id"):
        if len(values.drop_duplicates()) > 1:
            conflict_ids.append(value_id)
        else:
            exact_duplicate_ids.append(value_id)
    # A conflicting terminal snapshot row has no defensible timestamp.  It is
    # safer to remove the entire value ID than to select one chunk-boundary copy.
    raw = raw.loc[~raw["value_id"].isin(conflict_ids)].copy()
    raw = raw.sort_values(["server_time_dt", "value_id"]).drop_duplicates("value_id", keep="last")
    post_cutoff = int((raw["server_time_dt"] > cutoff).sum())
    raw = raw.loc[raw["server_time_dt"] <= cutoff].copy()
    raw["importance_rank"] = raw["importance"].map(IMPORTANCE_RANK).fillna(-1).astype(int)
    for column in ("has_actual", "has_forecast", "has_previous", "has_revised_previous"):
        raw[column] = raw[column].fillna(0).astype(int)
    raw["surprise"] = np.where(
        (raw["has_actual"] == 1) & (raw["has_forecast"] == 1),
        raw["actual"] - raw["forecast"],
        np.nan,
    )
    raw["surprise_robust_z"] = np.nan
    usable = raw.loc[raw["surprise"].notna()].sort_values(["event_id", "server_time_dt", "value_id"])
    for _, indices in usable.groupby("event_id", sort=False).groups.items():
        history: list[float] = []
        for index in indices:
            value = float(raw.at[index, "surprise"])
            if len(history) >= 6:
                center = median(history)
                mad = median([abs(item - center) for item in history])
                if mad > 0:
                    raw.at[index, "surprise_robust_z"] = (value - center) / (1.4826 * mad)
            history.append(value)
    diagnostics = {
        "rows_before_dedup": before,
        "duplicate_rows": duplicate_rows,
        "exact_duplicate_value_ids": len(exact_duplicate_ids),
        "duplicate_conflict_groups_excluded": len(conflict_ids),
        "post_cutoff_calendar_rows_excluded": post_cutoff,
        "rows_at_or_before_cutoff": len(raw),
        "first_time": raw["server_time_dt"].min().isoformat(),
        "last_time": raw["server_time_dt"].max().isoformat(),
        "actual_rows": int(raw["has_actual"].sum()),
        "forecast_rows": int(raw["has_forecast"].sum()),
        "normalized_surprise_rows": int(raw["surprise_robust_z"].notna().sum()),
    }
    return raw, diagnostics


def build_clusters(calendar: pd.DataFrame) -> pd.DataFrame:
    timed = calendar.loc[
        (calendar["time_mode"] == "CALENDAR_TIMEMODE_DATETIME")
        & (calendar["event_type"] != "CALENDAR_TYPE_HOLIDAY")
    ].copy()
    rows: list[dict] = []
    for timestamp, group in timed.groupby("server_time_dt", sort=True):
        currencies = sorted(set(group["currency"].dropna().astype(str)))
        sectors = sorted(set(group["sector"].dropna().astype(str)))
        codes = sorted(set(group["event_code"].dropna().astype(str)))
        usd = group.loc[group["currency"] == "USD"]
        surprise_values = group["surprise_robust_z"].dropna().astype(float)
        rows.append(
            {
                "event_time": timestamp,
                "year": timestamp.year,
                "weekday": timestamp.weekday(),
                "hour": timestamp.hour,
                "minute": timestamp.minute,
                "member_count": len(group),
                "max_importance_rank": int(group["importance_rank"].max()),
                "currencies": "|".join(currencies),
                "sectors": "|".join(sectors),
                "event_codes": "|".join(codes),
                "has_usd": bool(len(usd)),
                "any_high": bool((group["importance_rank"] >= 3).any()),
                "any_modhigh": bool((group["importance_rank"] >= 2).any()),
                "usd_high": bool(len(usd) and (usd["importance_rank"] >= 3).any()),
                "usd_modhigh": bool(len(usd) and (usd["importance_rank"] >= 2).any()),
                "max_abs_surprise_z": float(surprise_values.abs().max()) if len(surprise_values) else np.nan,
                "max_signed_surprise_z": (
                    float(surprise_values.loc[surprise_values.abs().idxmax()]) if len(surprise_values) else np.nan
                ),
            }
        )
    return pd.DataFrame(rows)


class MarketWindows:
    def __init__(self, market: pd.DataFrame):
        self.times = market["timestamp"].to_numpy(dtype="datetime64[ns]")
        self.tick = market["tick_volume"].to_numpy(dtype=float)
        self.ranges = market["m1_range"].to_numpy(dtype=float)
        self.tick_cum = np.concatenate(([0.0], np.cumsum(self.tick)))
        self.range_cum = np.concatenate(([0.0], np.cumsum(self.ranges)))

    def window(self, start: datetime, minutes: int) -> Optional[tuple[float, float, int]]:
        left = int(np.searchsorted(self.times, np.datetime64(start), side="left"))
        right = int(np.searchsorted(self.times, np.datetime64(start + timedelta(minutes=minutes)), side="left"))
        count = right - left
        if count < max(1, int(minutes * 0.8)):
            return None
        return (
            float(self.tick_cum[right] - self.tick_cum[left]),
            float(self.range_cum[right] - self.range_cum[left]),
            count,
        )

    def matched_lift(self, start: datetime, minutes: int) -> Optional[dict]:
        actual = self.window(start, minutes)
        if actual is None:
            return None
        controls = [self.window(start - timedelta(days=7 * lag), minutes) for lag in range(1, 9)]
        controls = [value for value in controls if value is not None]
        if len(controls) < 4:
            return None
        tick_base = median([value[0] for value in controls])
        range_base = median([value[1] for value in controls])
        return {
            "tick_volume": actual[0],
            "range_sum": actual[1],
            "market_minutes": actual[2],
            "control_windows": len(controls),
            "tick_volume_lift": actual[0] / tick_base if tick_base > 0 else np.nan,
            "range_lift": actual[1] / range_base if range_base > 0 else np.nan,
        }


def clock_profile(market: pd.DataFrame) -> tuple[list[dict], dict]:
    work = market[["timestamp", "tick_volume", "m1_range"]].copy()
    work["date"] = work["timestamp"].dt.date
    work["year"] = work["timestamp"].dt.year
    work["weekday"] = work["timestamp"].dt.weekday
    work["hour"] = work["timestamp"].dt.hour
    work["minute_of_day"] = work["timestamp"].dt.hour * 60 + work["timestamp"].dt.minute
    daily_hour = work.groupby(["date", "year", "weekday", "hour"], as_index=False).agg(
        tick_volume=("tick_volume", "sum"), range_sum=("m1_range", "sum"), market_minutes=("timestamp", "size")
    )
    totals = daily_hour.groupby("date").agg(day_tick=("tick_volume", "sum"), day_range=("range_sum", "sum"))
    daily_hour = daily_hour.join(totals, on="date")
    daily_hour["tick_share"] = daily_hour["tick_volume"] / daily_hour["day_tick"]
    daily_hour["range_share"] = daily_hour["range_sum"] / daily_hour["day_range"]
    rows: list[dict] = []
    for (year, hour), group in daily_hour.groupby(["year", "hour"]):
        rows.append(
            {
                "dimension": "YEAR_HOUR",
                "year": int(year),
                "weekday": "ALL",
                "hour": int(hour),
                "observed_days": int(len(group)),
                "mean_daily_tick_share": float(group["tick_share"].mean()),
                "median_daily_tick_share": float(group["tick_share"].median()),
                "mean_daily_range_share": float(group["range_share"].mean()),
                "median_daily_range_share": float(group["range_share"].median()),
            }
        )
    for (weekday, hour), group in daily_hour.groupby(["weekday", "hour"]):
        rows.append(
            {
                "dimension": "WEEKDAY_HOUR",
                "year": "ALL",
                "weekday": int(weekday),
                "hour": int(hour),
                "observed_days": int(len(group)),
                "mean_daily_tick_share": float(group["tick_share"].mean()),
                "median_daily_tick_share": float(group["tick_share"].median()),
                "mean_daily_range_share": float(group["range_share"].mean()),
                "median_daily_range_share": float(group["range_share"].median()),
            }
        )
    minute = work.groupby(["year", "minute_of_day"], as_index=False).agg(
        observed_minutes=("timestamp", "size"),
        mean_tick_volume=("tick_volume", "mean"),
        median_tick_volume=("tick_volume", "median"),
        mean_range=("m1_range", "mean"),
        median_range=("m1_range", "median"),
    )
    for item in minute.to_dict("records"):
        rows.append(
            {
                "dimension": "YEAR_MINUTE",
                "year": int(item["year"]),
                "weekday": "ALL",
                "hour": int(item["minute_of_day"] // 60),
                "minute_of_day": int(item["minute_of_day"]),
                **{key: value for key, value in item.items() if key not in {"year", "minute_of_day"}},
            }
        )
    year_hour = pd.DataFrame([row for row in rows if row["dimension"] == "YEAR_HOUR"])
    stability = []
    for year, group in year_hour.groupby("year"):
        ordered = group.sort_values("mean_daily_tick_share", ascending=False).reset_index(drop=True)
        target = ordered.loc[ordered["hour"] == 16].iloc[0]
        stability.append(
            {
                "year": int(year),
                "hour16_rank": int(ordered.index[ordered["hour"] == 16][0] + 1),
                "hour16_mean_daily_tick_share": float(target["mean_daily_tick_share"]),
                "hour16_vs_hour_median": float(target["mean_daily_tick_share"] / group["mean_daily_tick_share"].median()),
                "top_hour": int(ordered.iloc[0]["hour"]),
            }
        )
    summary = {"hour16_by_year": stability}
    return rows, summary


def event_response(clusters: pd.DataFrame, windows: MarketWindows) -> tuple[list[dict], list[dict], dict]:
    details: list[dict] = []
    for row in clusters.to_dict("records"):
        output = dict(row)
        output["event_time"] = row["event_time"].isoformat()
        for minutes in WINDOWS:
            lift = windows.matched_lift(row["event_time"], minutes)
            for metric in ("tick_volume", "range_sum", "market_minutes", "control_windows", "tick_volume_lift", "range_lift"):
                output[f"post_{minutes}_{metric}"] = lift[metric] if lift else np.nan
        details.append(output)
    detail_frame = pd.DataFrame(details)
    scorecards: list[dict] = []
    scopes = {
        "ALL_TIMED": pd.Series(True, index=detail_frame.index),
        "ANY_HIGH": detail_frame["any_high"].astype(bool),
        "ANY_MODHIGH": detail_frame["any_modhigh"].astype(bool),
        "USD_HIGH": detail_frame["usd_high"].astype(bool),
        "USD_MODHIGH": detail_frame["usd_modhigh"].astype(bool),
    }
    for scope, mask in scopes.items():
        scoped = detail_frame.loc[mask]
        for year_label, values in [("ALL", scoped), *[(str(year), group) for year, group in scoped.groupby("year")]]:
            for minutes in WINDOWS:
                valid = values.dropna(subset=[f"post_{minutes}_tick_volume_lift", f"post_{minutes}_range_lift"])
                scorecards.append(
                    {
                        "scope": scope,
                        "year": year_label,
                        "window_minutes": minutes,
                        "clusters": len(values),
                        "valid_clusters": len(valid),
                        "median_tick_volume_lift": float(valid[f"post_{minutes}_tick_volume_lift"].median()) if len(valid) else np.nan,
                        "pct_tick_volume_lift_gt_1": float((valid[f"post_{minutes}_tick_volume_lift"] > 1).mean()) if len(valid) else np.nan,
                        "median_range_lift": float(valid[f"post_{minutes}_range_lift"].median()) if len(valid) else np.nan,
                        "pct_range_lift_gt_1": float((valid[f"post_{minutes}_range_lift"] > 1).mean()) if len(valid) else np.nan,
                    }
                )
    alignment_rows = []
    usd_high = clusters.loc[clusters["usd_high"]]
    for offset in (-1, 0, 1, 2, 3, 4):
        for year_label, group in [("ALL", usd_high), *[(str(year), values) for year, values in usd_high.groupby("year")]]:
            lifts = []
            ranges = []
            for event_time in group["event_time"]:
                result = windows.matched_lift(event_time.to_pydatetime() + timedelta(hours=offset), 15)
                if result:
                    lifts.append(result["tick_volume_lift"])
                    ranges.append(result["range_lift"])
            alignment_rows.append(
                {
                    "offset_hours": offset,
                    "year": year_label,
                    "valid_clusters": len(lifts),
                    "median_tick_volume_lift": float(np.median(lifts)) if lifts else np.nan,
                    "median_range_lift": float(np.median(ranges)) if ranges else np.nan,
                }
            )
    all_alignment = pd.DataFrame(alignment_rows)
    overall = all_alignment.loc[all_alignment["year"] == "ALL"].sort_values("median_range_lift", ascending=False)
    alignment_summary = {
        "best_offset_by_overall_median_range_lift": int(overall.iloc[0]["offset_hours"]),
        "best_offset_median_range_lift": float(overall.iloc[0]["median_range_lift"]),
        "offset_zero_rank": int(overall.reset_index(drop=True).index[overall["offset_hours"].to_numpy() == 0][0] + 1),
    }
    return details, scorecards + [{"scope": "CLOCK_ALIGNMENT", **row} for row in alignment_rows], alignment_summary


def scope_times(clusters: pd.DataFrame) -> dict[str, list[datetime]]:
    return {
        "ANY_HIGH": [value.to_pydatetime() for value in clusters.loc[clusters["any_high"], "event_time"]],
        "ANY_MODHIGH": [value.to_pydatetime() for value in clusters.loc[clusters["any_modhigh"], "event_time"]],
        "USD_HIGH": [value.to_pydatetime() for value in clusters.loc[clusters["usd_high"], "event_time"]],
        "USD_MODHIGH": [value.to_pydatetime() for value in clusters.loc[clusters["usd_modhigh"], "event_time"]],
    }


def proximity_state(timestamp: datetime, times: list[datetime], max_minutes: int = 240) -> tuple[str, Optional[float], Optional[float]]:
    position = bisect_left(times, timestamp)
    previous = times[position - 1] if position else None
    following = times[position] if position < len(times) else None
    since = (timestamp - previous).total_seconds() / 60 if previous else None
    until = (following - timestamp).total_seconds() / 60 if following else None
    candidates = []
    if since is not None and since <= max_minutes:
        candidates.append((since, "POST", since))
    if until is not None and until <= max_minutes:
        candidates.append((until, "PRE", until))
    if not candidates:
        return "FAR_GT_240", since, until
    distance, relation, _ = min(candidates, key=lambda item: (item[0], 0 if item[1] == "POST" else 1))
    if distance == 0:
        return "AT_RELEASE", since, until
    upper = next(value for value in WINDOWS if distance <= value)
    lower = 0 if upper == 15 else WINDOWS[WINDOWS.index(upper) - 1]
    return f"{relation}_{lower}_{upper}", since, until


def enrich_proximity(
    rows: list[dict],
    time_field: str,
    scopes: dict[str, list[datetime]],
    cluster_meta: dict[datetime, dict],
) -> list[dict]:
    output = []
    for row in rows:
        item = dict(row)
        timestamp = datetime.fromisoformat(row[time_field].replace(" ", "T"))
        item["analysis_year"] = timestamp.year
        item["broker_weekday"] = timestamp.weekday()
        item["broker_hour"] = timestamp.hour
        for scope, times in scopes.items():
            state, since, until = proximity_state(timestamp, times)
            key = scope.lower()
            item[f"{key}_state"] = state
            item[f"{key}_minutes_since"] = since
            item[f"{key}_minutes_until"] = until
            position = bisect_left(times, timestamp)
            previous = times[position - 1] if position else None
            following = times[position] if position < len(times) else None
            previous_meta = cluster_meta.get(previous, {})
            following_meta = cluster_meta.get(following, {})
            item[f"{key}_previous_time"] = previous.isoformat() if previous else ""
            item[f"{key}_previous_event_codes"] = previous_meta.get("event_codes", "")
            item[f"{key}_previous_sectors"] = previous_meta.get("sectors", "")
            item[f"{key}_previous_max_abs_surprise_z"] = previous_meta.get("max_abs_surprise_z", "")
            item[f"{key}_next_time"] = following.isoformat() if following else ""
            item[f"{key}_next_event_codes"] = following_meta.get("event_codes", "")
            item[f"{key}_next_sectors"] = following_meta.get("sectors", "")
        output.append(item)
    return output


def child_summary(values: Iterable[dict]) -> dict:
    rows = list(values)
    funded = sum(float(row["funded_units"]) for row in rows)
    stopped = sum(float(row["stopped_loss_units"]) for row in rows)
    returns = [float(row["combined_R_units"]) for row in rows]
    gross_profit = sum(max(value, 0.0) for value in returns)
    gross_loss = -sum(min(value, 0.0) for value in returns)
    chain = best = 0
    for row in sorted(rows, key=lambda value: value["decision_time"]):
        chain = chain + 1 if int(float(row["stop_hit"])) else 0
        best = max(best, chain)
    return {
        "children": len(rows),
        "funded_units": funded,
        "stopped_children": sum(int(float(row["stop_hit"])) for row in rows),
        "stopped_units": stopped,
        "stopped_units_per_100_funded": 100.0 * stopped / funded if funded else np.nan,
        "net_R": sum(returns),
        "profit_factor_R": gross_profit / gross_loss if gross_loss else np.nan,
        "right_tail_ge_5R_units": sum(float(row["right_tail_ge_5R_units"]) for row in rows),
        "max_stop_chain": best,
    }


def build_child_outputs(
    phase1b: Path, scopes: dict[str, list[datetime]], cluster_meta: dict[datetime, dict]
) -> tuple[list[dict], list[dict]]:
    decisions = read_csv(phase1b / "V12_PHASE1B_V10_CHILD_DECISION_CONTEXT.csv")
    outcomes = {row["signal_id"]: row for row in read_csv(phase1b / "V12_PHASE1B_V10_CHILD_OUTCOME_LINK.csv")}
    joined = []
    for row in decisions:
        item = dict(row)
        item.update(outcomes[row["signal_id"]])
        joined.append(item)
    joined = enrich_proximity(joined, "decision_time", scopes, cluster_meta)
    scorecards: list[dict] = []

    def add(dimension: str, group: str, values: list[dict]) -> None:
        scorecards.append({"dimension": dimension, "group": str(group), **child_summary(values)})

    add("ALL", "ALL", joined)
    for field in ("analysis_year", "direction", "broker_weekday", "broker_hour", "event", "relation"):
        groups: dict[str, list[dict]] = defaultdict(list)
        for row in joined:
            groups[str(row.get(field, ""))].append(row)
        for group, values in sorted(groups.items()):
            add(field.upper(), group, values)
    for scope in scopes:
        field = f"{scope.lower()}_state"
        groups = defaultdict(list)
        for row in joined:
            groups[row[field]].append(row)
        for group, values in sorted(groups.items()):
            add(f"{scope}_STATE", group, values)
        for window in WINDOWS:
            pre = [row for row in joined if row[f"{scope.lower()}_minutes_until"] is not None and 0 <= float(row[f"{scope.lower()}_minutes_until"]) <= window]
            post = [row for row in joined if row[f"{scope.lower()}_minutes_since"] is not None and 0 <= float(row[f"{scope.lower()}_minutes_since"]) <= window]
            add(f"{scope}_WINDOW", f"PRE_LE_{window}", pre)
            add(f"{scope}_WINDOW", f"POST_LE_{window}", post)
    return joined, scorecards


def nha_summary(values: Iterable[dict]) -> dict:
    rows = list(values)
    linked = [row for row in rows if row.get("linked_v10_k1_signal_id")]
    repairs = [row for row in rows if row.get("repair_status")]
    repair_outcomes = [row for row in repairs if row.get("repair_R") not in (None, "")]
    return {
        "flips": len(rows),
        "mean_new_run_h4_bars": float(np.mean([float(row["new_fast_run_h4_bars"]) for row in rows])) if rows else np.nan,
        "linked_k1_children": len(linked),
        "linked_k1_stops": sum(int(float(row["linked_v10_k1_stop_hit"])) for row in linked if row.get("linked_v10_k1_stop_hit") not in (None, "")),
        "linked_k1_stop_rate": float(np.mean([int(float(row["linked_v10_k1_stop_hit"])) for row in linked if row.get("linked_v10_k1_stop_hit") not in (None, "")])) if linked else np.nan,
        "repair_candidates": len(repairs),
        "repair_stops": sum(int(float(row["repair_stop_hit"])) for row in repair_outcomes),
        "repair_net_R": sum(float(row["repair_R"]) for row in repair_outcomes),
    }


def build_nha_outputs(
    phase1b: Path,
    phase1c: Path,
    scopes: dict[str, list[datetime]],
    cluster_meta: dict[datetime, dict],
) -> tuple[list[dict], list[dict]]:
    decisions = read_csv(phase1b / "V12_PHASE1B_NHA_DECISION_CONTEXT.csv")
    outcomes = {row["flip_id"]: row for row in read_csv(phase1b / "V12_PHASE1B_NHA_OUTCOME_LINK.csv")}
    repair_decisions = {row["bridge_id"]: row for row in read_csv(phase1c / "V12_PHASE1C_REPAIR_DECISIONS.csv")}
    repair_outcomes = {row["bridge_id"]: row for row in read_csv(phase1c / "V12_PHASE1C_REPAIR_OUTCOMES.csv")}
    joined = []
    for row in decisions:
        item = dict(row)
        item.update(outcomes[row["flip_id"]])
        repair = repair_decisions.get(row["flip_id"])
        if repair:
            item["repair_status"] = repair["repair_status"]
            outcome = repair_outcomes.get(row["flip_id"])
            item["repair_R"] = outcome["R"] if outcome else ""
            item["repair_stop_hit"] = outcome["stop_hit"] if outcome else ""
        joined.append(item)
    joined = enrich_proximity(joined, "known_at", scopes, cluster_meta)
    scorecards: list[dict] = []

    def add(dimension: str, group: str, values: list[dict]) -> None:
        scorecards.append({"dimension": dimension, "group": str(group), **nha_summary(values)})

    add("ALL", "ALL", joined)
    for field in ("analysis_year", "explanation_state", "broker_weekday", "broker_hour"):
        groups: dict[str, list[dict]] = defaultdict(list)
        for row in joined:
            groups[str(row.get(field, ""))].append(row)
        for group, values in sorted(groups.items()):
            add(field.upper(), group, values)
    for scope in scopes:
        field = f"{scope.lower()}_state"
        groups = defaultdict(list)
        for row in joined:
            groups[row[field]].append(row)
        for group, values in sorted(groups.items()):
            add(f"{scope}_STATE", group, values)
    return joined, scorecards


def mechanism_scorecards(child_rows: list[dict], nha_rows: list[dict]) -> tuple[list[dict], list[dict]]:
    child = pd.DataFrame(child_rows)
    interactions: list[dict] = []
    base = (child["broker_hour"] == 20) & (child["relation"] == "ALIGNED_ACTIVE_JOURNEY")
    candidate = base & (child["usd_modhigh_state"] == "PRE_30_60")
    for year_label, year_mask in [
        ("ALL", pd.Series(True, index=child.index)),
        *[(str(year), child["analysis_year"] == year) for year in sorted(child["analysis_year"].unique())],
    ]:
        for group, mask in (
            ("H20_ALIGNED_PRE_USD_MODHIGH_30_60", candidate),
            ("H20_ALIGNED_OTHER", base & ~candidate),
            ("ALL_PRE_USD_MODHIGH_30_60", child["usd_modhigh_state"] == "PRE_30_60"),
        ):
            interactions.append({"year": year_label, "group": group, **child_summary(child.loc[year_mask & mask].to_dict("records"))})

    surprise_rows: list[dict] = []
    child_z = pd.to_numeric(child["usd_modhigh_previous_max_abs_surprise_z"], errors="coerce")
    child_since = pd.to_numeric(child["usd_modhigh_minutes_since"], errors="coerce")
    child_post = child.loc[child_since.le(240) & child_z.notna()].copy()
    child_post["surprise_bin"] = pd.cut(
        child_z.loc[child_post.index], [-np.inf, 1, 2, np.inf], labels=["ABS_Z_LE_1", "ABS_Z_1_2", "ABS_Z_GT_2"]
    )
    for group, values in child_post.groupby("surprise_bin", observed=True):
        surprise_rows.append({"unit": "V10_CHILD", "group": str(group), **child_summary(values.to_dict("records"))})

    nha = pd.DataFrame(nha_rows)
    nha_z = pd.to_numeric(nha["usd_modhigh_previous_max_abs_surprise_z"], errors="coerce")
    nha_since = pd.to_numeric(nha["usd_modhigh_minutes_since"], errors="coerce")
    nha_post = nha.loc[nha_since.le(240) & nha_z.notna()].copy()
    nha_post["surprise_bin"] = pd.cut(
        nha_z.loc[nha_post.index], [-np.inf, 1, 2, np.inf], labels=["ABS_Z_LE_1", "ABS_Z_1_2", "ABS_Z_GT_2"]
    )
    for group, values in nha_post.groupby("surprise_bin", observed=True):
        stops = pd.to_numeric(values["linked_v10_k1_stop_hit"], errors="coerce")
        linked = stops.notna()
        surprise_rows.append(
            {
                "unit": "NHA_FLIP",
                "group": str(group),
                "flips": len(values),
                "linked_k1_children": int(linked.sum()),
                "linked_k1_stops": float(stops.sum()),
                "linked_k1_stop_rate": float(stops.loc[linked].mean()) if linked.any() else np.nan,
                "mean_new_run_h4_bars": float(pd.to_numeric(values["new_fast_run_h4_bars"]).mean()),
            }
        )
    return interactions, surprise_rows


def render_summary(
    path: Path,
    clock_rows: list[dict],
    event_scorecard: list[dict],
    child_scorecard: list[dict],
) -> None:
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (1800, 620), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    def panel(index: int, title: str, xlabel: str, ylabel: str) -> tuple[int, int, int, int]:
        left = 45 + index * 590
        top, right, bottom = 70, 565 + index * 590, 555
        draw.rectangle((left, top, right, bottom), outline="#777777", width=1)
        draw.text((left + 8, top + 8), title, fill="black", font=font)
        draw.text((left + 180, bottom + 28), xlabel, fill="black", font=font)
        draw.text((left + 8, bottom + 8), ylabel, fill="#444444", font=font)
        return left + 55, top + 45, right - 20, bottom - 35

    def xy(box: tuple[int, int, int, int], x: float, y: float, xmin: float, xmax: float, ymin: float, ymax: float) -> tuple[int, int]:
        left, top, right, bottom = box
        px = left + (x - xmin) / (xmax - xmin) * (right - left)
        py = bottom - (y - ymin) / (ymax - ymin) * (bottom - top)
        return int(px), int(py)

    draw.text((710, 20), "V12 Phase-1D temporal and event-state audit", fill="black", font=font)
    clock = pd.DataFrame([row for row in clock_rows if row["dimension"] == "YEAR_HOUR"])
    box = panel(0, "Broker-clock activity", "Broker hour", "Daily tick share (%)")
    ymax = 100 * clock["mean_daily_tick_share"].max() * 1.1
    for color, (year, values) in zip(colors, clock.groupby("year")):
        values = values.sort_values("hour")
        points = [xy(box, float(row.hour), 100 * float(row.mean_daily_tick_share), 0, 23, 0, ymax) for row in values.itertuples()]
        draw.line(points, fill=color, width=2)
        draw.text((box[0] + 75 * (int(year) - 2022), box[1] + 5), str(year), fill=color, font=font)
    x16, _ = xy(box, 16, 0, 0, 23, 0, ymax)
    draw.line((x16, box[1], x16, box[3]), fill="#d62728", width=1)

    event = pd.DataFrame(event_scorecard)
    event = event.loc[(event["year"].astype(str) == "ALL") & event["scope"].isin(["ANY_HIGH", "USD_HIGH", "USD_MODHIGH"])]
    box = panel(1, "Post-event range lift", "Window minutes", "Matched-week ratio")
    ymin, ymax = 0.98, max(1.16, float(event["median_range_lift"].max()) * 1.02)
    for color, (scope, values) in zip(colors, event.groupby("scope")):
        values = values.sort_values("window_minutes")
        points = [xy(box, float(row.window_minutes), float(row.median_range_lift), 15, 240, ymin, ymax) for row in values.itertuples()]
        draw.line(points, fill=color, width=3)
        for point in points:
            draw.ellipse((point[0] - 3, point[1] - 3, point[0] + 3, point[1] + 3), fill=color)
    for offset, (scope, _) in enumerate(event.groupby("scope")):
        draw.text((box[0] + offset * 145, box[1] + 5), scope, fill=colors[offset], font=font)
    _, y1 = xy(box, 15, 1, 15, 240, ymin, ymax)
    draw.line((box[0], y1, box[2], y1), fill="#333333", width=1)

    child = pd.DataFrame(child_scorecard)
    child = child.loc[child["dimension"] == "USD_MODHIGH_STATE"].copy()
    box = panel(2, "V10 exposure by event state", "Stopped units / 100 funded", "Net R")
    xmax = max(25.0, float(child["stopped_units_per_100_funded"].max()) * 1.08)
    ymin = min(-45.0, float(child["net_R"].min()) * 1.15)
    ymax = max(90.0, float(child["net_R"].max()) * 1.08)
    for _, row in child.iterrows():
        point = xy(box, float(row["stopped_units_per_100_funded"]), float(row["net_R"]), 0, xmax, ymin, ymax)
        radius = max(3, min(12, int(3 + float(row["children"]) / 100)))
        draw.ellipse((point[0] - radius, point[1] - radius, point[0] + radius, point[1] + radius), fill="#1f77b4")
        if row["group"] in {"PRE_30_60", "FAR_GT_240", "AT_RELEASE", "POST_15_30"}:
            draw.text((point[0] + 5, point[1] - 12), row["group"], fill="black", font=font)
    xbase, _ = xy(box, 12.522546, 0, 0, xmax, ymin, ymax)
    _, yzero = xy(box, 0, 0, 0, xmax, ymin, ymax)
    draw.line((xbase, box[1], xbase, box[3]), fill="#777777", width=1)
    draw.line((box[0], yzero, box[2], yzero), fill="#333333", width=1)
    image.save(path)


def file_manifest(path: Path) -> dict:
    rows = None
    if path.suffix.lower() == ".csv":
        with path.open("rb") as handle:
            rows = max(0, sum(1 for _ in handle) - 1)
    return {"file": path.name, "bytes": path.stat().st_size, "rows": rows, "sha256": sha256_file(path)}


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=repo_root / "research" / "v12" / "v12_phase1d_contract.json")
    parser.add_argument("--m1", type=Path, default=repo_root / "data" / "GOLD#" / "GOLD#_M1_202201030100_202609222358.csv")
    parser.add_argument("--calendar", type=Path, required=True)
    parser.add_argument("--phase1b", type=Path, default=repo_root / "output" / "v12_phase1b_h4m5_journey_overlay_20260923")
    parser.add_argument("--phase1c", type=Path, default=repo_root / "output" / "v12_phase1c_crt_protected_carry_repair_20260924")
    parser.add_argument("--output", type=Path, default=repo_root / "output" / "v12_phase1d_temporal_event_state_20260924")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    cutoff = parse_cutoff(contract["mechanism_cutoff"])
    safe_prepare_output(args.output, args.replace)

    market, prefix_audit = load_market(args.m1, cutoff)
    calendar, calendar_quality = load_calendar(args.calendar, cutoff)
    clusters = build_clusters(calendar)
    windows = MarketWindows(market)
    clock_rows, clock_summary = clock_profile(market)
    event_details, event_scorecard, alignment_summary = event_response(clusters, windows)
    scopes = scope_times(clusters)
    cluster_meta = {
        row["event_time"].to_pydatetime(): row.to_dict()
        for _, row in clusters.iterrows()
    }
    child_context, child_scorecard = build_child_outputs(args.phase1b, scopes, cluster_meta)
    nha_context, nha_scorecard = build_nha_outputs(args.phase1b, args.phase1c, scopes, cluster_meta)
    interactions, surprise_scorecard = mechanism_scorecards(child_context, nha_context)

    outputs = {
        "CLOCK_PROFILE.csv": clock_rows,
        "EVENT_CLUSTER_RESPONSE.csv": event_details,
        "EVENT_SCORECARD.csv": event_scorecard,
        "V10_CHILD_EVENT_CONTEXT.csv": child_context,
        "V10_CHILD_SCORECARD.csv": child_scorecard,
        "NHA_EVENT_CONTEXT.csv": nha_context,
        "NHA_SCORECARD.csv": nha_scorecard,
        "INTERACTION_SCORECARD.csv": interactions,
        "REALIZED_SURPRISE_SCORECARD.csv": surprise_scorecard,
    }
    paths = []
    for name, rows in outputs.items():
        path = args.output / f"{PREFIX}{name}"
        write_csv(path, rows)
        paths.append(path)

    diagnostics = {
        "contract_version": contract["contract_version"],
        "contract_sha256": sha256_file(args.contract),
        "causal_cutoff": cutoff.isoformat(),
        "market": {
            "source": str(args.m1),
            "sha256": sha256_file(args.m1),
            **prefix_audit.to_dict(),
            "first_timestamp": market["timestamp"].min().isoformat(),
            "last_timestamp": market["timestamp"].max().isoformat(),
        },
        "calendar": {
            "source": str(args.calendar),
            "sha256": sha256_file(args.calendar),
            **calendar_quality,
        },
        "event_clusters": len(clusters),
        "event_scope_counts": {name: len(values) for name, values in scopes.items()},
        "clock_summary": clock_summary,
        "clock_alignment": alignment_summary,
        "v10_children": len(child_context),
        "nha_flips": len(nha_context),
        "post_cutoff_price_rows_parsed": prefix_audit.post_cutoff_price_rows_parsed,
        "trade_authority": False,
        "sizing_authority": False,
    }
    diagnostics_path = args.output / f"{PREFIX}DIAGNOSTICS.json"
    write_json(diagnostics_path, diagnostics)
    paths.append(diagnostics_path)

    summary_path = args.output / f"{PREFIX}SUMMARY.png"
    render_summary(summary_path, clock_rows, event_scorecard, child_scorecard)
    paths.append(summary_path)

    manifest = {
        "contract_version": contract["contract_version"],
        "contract_sha256": sha256_file(args.contract),
        "frozen_at": contract["frozen_at"],
        "files": [file_manifest(path) for path in paths],
    }
    write_json(args.output / f"{PREFIX}MANIFEST.json", manifest)
    print(json.dumps(diagnostics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
