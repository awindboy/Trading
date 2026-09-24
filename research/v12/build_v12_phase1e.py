#!/usr/bin/env python3
"""Build the frozen V12 Phase-1E session/weekday/event interaction study."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from build_v12_phase0 import parse_cutoff
from build_v12_phase1d import child_summary, load_market, nha_summary, read_csv, write_csv, write_json
from v12_phase0_core import sha256_file


PREFIX = "V12_PHASE1E_"
BROKER_UTC_OFFSET = timedelta(hours=3)
TOKYO = ZoneInfo("Asia/Tokyo")
LONDON = ZoneInfo("Europe/London")
NEW_YORK = ZoneInfo("America/New_York")
UTC = timezone.utc
WEEKDAY = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")


def safe_prepare_output(path: Path, replace: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(f"output directory is not empty: {path}")
        for child in path.iterdir():
            if not child.is_file() or not child.name.startswith(PREFIX):
                raise ValueError(f"refusing to replace unexpected path: {child}")
            child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def server_to_utc(value: datetime) -> datetime:
    return (value - BROKER_UTC_OFFSET).replace(tzinfo=UTC)


def in_clock(value: datetime, start: time, end: time) -> bool:
    current = value.timetz().replace(tzinfo=None)
    return start <= current < end


def session_context(value: datetime) -> dict:
    utc = server_to_utc(value)
    tokyo = utc.astimezone(TOKYO)
    london = utc.astimezone(LONDON)
    new_york = utc.astimezone(NEW_YORK)
    asia = in_clock(tokyo, time(8, 45), time(15, 45))
    london_core = in_clock(london, time(8), time(16, 30))
    new_york_core = in_clock(new_york, time(8, 30), time(16))
    if asia and not london_core and not new_york_core:
        phase = "ASIA_ONLY"
    elif london_core and not new_york_core:
        phase = "LONDON_PRE_NY"
    elif london_core and new_york_core:
        phase = "LONDON_NY_OVERLAP"
    elif new_york_core and not london_core:
        phase = "NY_AFTER_LONDON"
    else:
        phase = "OFF_CORE"
    lbma_am_minutes = abs((london.hour * 60 + london.minute) - 630)
    lbma_pm_minutes = abs((london.hour * 60 + london.minute) - 900)
    comex_minutes = abs((new_york.hour * 60 + new_york.minute) - 809)
    return {
        "session_phase": phase,
        "broker_weekday": WEEKDAY[value.weekday()],
        "new_york_weekday": WEEKDAY[new_york.weekday()],
        "new_york_local": new_york.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "london_local": london.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "tokyo_local": tokyo.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "near_lbma_am_15m": int(lbma_am_minutes <= 15),
        "near_lbma_pm_15m": int(lbma_pm_minutes <= 15),
        "near_comex_settlement_15m": int(comex_minutes <= 15),
    }


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace(" ", "T"))


def collapse_event_state(value: str) -> str:
    if value in {"AT_RELEASE", "PRE_LE_15", "PRE_15_30"}:
        return "PRE_0_30"
    if value == "PRE_30_60":
        return "PRE_30_60"
    if value in {"POST_LE_15", "POST_15_30", "POST_30_60"}:
        return "POST_0_60"
    return "OTHER"


def event_family(codes: str) -> str:
    value = (codes or "").lower()
    if "baker-hughes" in value:
        return "BAKER_HUGHES"
    if "fomc" in value or "fed-interest-rate" in value:
        return "FOMC"
    if "auction" in value:
        return "AUCTION"
    if "speech" in value or "testimony" in value:
        return "SPEECH"
    if value:
        return "OTHER_MACRO"
    return "NONE"


def validate_calendar_clock(calendar_path: Path, overrides_path: Path | None = None) -> tuple[list[dict], dict]:
    calendar = pd.read_csv(calendar_path, encoding="cp949", low_memory=False)
    override_rows = 0
    if overrides_path is not None:
        spec = json.loads(overrides_path.read_text(encoding="utf-8"))
        for override in spec["overrides"]:
            ids = {int(value) for value in override["value_ids"]}
            mask = calendar["value_id"].astype(int).isin(ids)
            if set(calendar.loc[mask, "value_id"].astype(int)) != ids:
                raise ValueError(f"calendar override IDs missing: {ids}")
            if set(calendar.loc[mask, "server_time"].astype(str)) != {override["original_server_time"]}:
                raise ValueError(f"calendar override original timestamp mismatch: {ids}")
            calendar.loc[mask, "server_time"] = override["corrected_server_time"]
            override_rows += int(mask.sum())
    calendar["server_time_dt"] = pd.to_datetime(calendar["server_time"], format="%Y.%m.%d %H:%M:%S")
    duplicate_ids = int(calendar.duplicated("value_id", keep=False).sum())
    checks = []
    for code, local_hour, local_minute in (
        ("nonfarm-payrolls", 8, 30),
        ("fed-interest-rate-decision", 14, 0),
    ):
        rows = calendar.loc[calendar["event_code"] == code]
        matched = 0
        for timestamp in rows["server_time_dt"]:
            local = datetime(timestamp.year, timestamp.month, timestamp.day, local_hour, local_minute, tzinfo=NEW_YORK)
            expected = (local.astimezone(UTC).replace(tzinfo=None) + BROKER_UTC_OFFSET)
            matched += int(timestamp.to_pydatetime() == expected)
        checks.append({"event_code": code, "rows": len(rows), "matched": matched, "mismatched": len(rows) - matched})
    diagnostics = {
        "rows": len(calendar),
        "unique_value_ids": int(calendar["value_id"].nunique()),
        "duplicate_rows": duplicate_ids,
        "calendar_time_override_rows": override_rows,
        "all_sentinels_pass": all(row["mismatched"] == 0 and row["rows"] > 0 for row in checks),
    }
    if duplicate_ids or not diagnostics["all_sentinels_pass"]:
        raise ValueError(f"calendar clock validation failed: {diagnostics}, checks={checks}")
    return checks, diagnostics


def vector_session_frame(timestamps: pd.Series) -> pd.DataFrame:
    broker = pd.to_datetime(timestamps)
    utc = (broker - pd.Timedelta(hours=3)).dt.tz_localize("UTC")
    tokyo = utc.dt.tz_convert("Asia/Tokyo")
    london = utc.dt.tz_convert("Europe/London")
    new_york = utc.dt.tz_convert("America/New_York")
    tokyo_minute = tokyo.dt.hour * 60 + tokyo.dt.minute
    london_minute = london.dt.hour * 60 + london.dt.minute
    ny_minute = new_york.dt.hour * 60 + new_york.dt.minute
    asia = tokyo_minute.between(525, 944)
    london_core = london_minute.between(480, 989)
    ny_core = ny_minute.between(510, 959)
    phase = np.select(
        [asia & ~london_core & ~ny_core, london_core & ~ny_core, london_core & ny_core, ny_core & ~london_core],
        ["ASIA_ONLY", "LONDON_PRE_NY", "LONDON_NY_OVERLAP", "NY_AFTER_LONDON"],
        default="OFF_CORE",
    )
    return pd.DataFrame(
        {
            "session_phase": phase,
            "broker_date": broker.dt.date,
            "year": broker.dt.year,
            "broker_weekday": broker.dt.dayofweek.map(dict(enumerate(WEEKDAY))),
            "new_york_weekday": new_york.dt.dayofweek.map(dict(enumerate(WEEKDAY))),
        }
    )


def build_activity(market: pd.DataFrame) -> list[dict]:
    context = vector_session_frame(market["timestamp"])
    work = pd.concat([context, market[["tick_volume", "m1_range"]].reset_index(drop=True)], axis=1)
    daily = work.groupby(["broker_date", "year", "new_york_weekday", "session_phase"], as_index=False).agg(
        market_minutes=("tick_volume", "size"), tick_volume=("tick_volume", "sum"), range_sum=("m1_range", "sum")
    )
    totals = daily.groupby("broker_date").agg(day_tick=("tick_volume", "sum"), day_range=("range_sum", "sum"))
    daily = daily.join(totals, on="broker_date")
    daily["daily_tick_share"] = daily["tick_volume"] / daily["day_tick"]
    daily["daily_range_share"] = daily["range_sum"] / daily["day_range"]
    rows = []
    for keys, group in daily.groupby(["year", "new_york_weekday", "session_phase"], sort=True):
        rows.append(
            {
                "year": int(keys[0]),
                "new_york_weekday": keys[1],
                "session_phase": keys[2],
                "observed_days": len(group),
                "market_minutes": int(group["market_minutes"].sum()),
                "tick_volume_per_minute": float(group["tick_volume"].sum() / group["market_minutes"].sum()),
                "range_per_minute": float(group["range_sum"].sum() / group["market_minutes"].sum()),
                "mean_daily_tick_share": float(group["daily_tick_share"].mean()),
                "mean_daily_range_share": float(group["daily_range_share"].mean()),
            }
        )
    return rows


def enrich_children(path: Path) -> list[dict]:
    rows = read_csv(path)
    output = []
    for row in rows:
        item = dict(row)
        for label, field in (("decision", "decision_time"), ("entry", "entry_time"), ("exit", "exit_time")):
            context = session_context(parse_iso(row[field]))
            for key, value in context.items():
                item[f"{label}_{key}"] = value
        item["usd_event_state"] = collapse_event_state(row["usd_modhigh_state"])
        item["next_usd_event_family"] = event_family(row["usd_modhigh_next_event_codes"])
        decision = parse_iso(row["decision_time"])
        item["iso_week"] = f"{decision.isocalendar().year}-W{decision.isocalendar().week:02d}"
        output.append(item)
    return output


def enrich_nha(path: Path) -> list[dict]:
    rows = read_csv(path)
    output = []
    for row in rows:
        item = dict(row)
        context = session_context(parse_iso(row["known_at"]))
        for key, value in context.items():
            item[f"known_{key}"] = value
        item["usd_event_state"] = collapse_event_state(row["usd_modhigh_state"])
        output.append(item)
    return output


def stable_group_seed(group: str, base: int) -> int:
    return base + int(hashlib.sha256(group.encode("utf-8")).hexdigest()[:8], 16)


def bootstrap_child(rows: list[dict], group: str, draws: int = 2000, seed: int = 120124) -> dict:
    if len(rows) < 20:
        return {"bootstrap_weeks": 0, "stop_rate_ci_low": "", "stop_rate_ci_high": "", "net_R_ci_low": "", "net_R_ci_high": ""}
    frame = pd.DataFrame(rows)
    weeks = sorted(frame["iso_week"].unique())
    if len(weeks) < 4:
        return {"bootstrap_weeks": len(weeks), "stop_rate_ci_low": "", "stop_rate_ci_high": "", "net_R_ci_low": "", "net_R_ci_high": ""}
    weekly = frame.groupby("iso_week", sort=True).agg(
        funded=("funded_units", lambda value: value.astype(float).sum()),
        stopped=("stopped_loss_units", lambda value: value.astype(float).sum()),
        net_R=("combined_R_units", lambda value: value.astype(float).sum()),
    ).reindex(weeks)
    rng = np.random.default_rng(stable_group_seed(group, seed))
    sampled = rng.integers(0, len(weeks), size=(draws, len(weeks)))
    funded = weekly["funded"].to_numpy(dtype=float)[sampled].sum(axis=1)
    stopped = weekly["stopped"].to_numpy(dtype=float)[sampled].sum(axis=1)
    net_returns = weekly["net_R"].to_numpy(dtype=float)[sampled].sum(axis=1)
    stop_rates = np.divide(100.0 * stopped, funded, out=np.full(draws, np.nan), where=funded > 0)
    return {
        "bootstrap_weeks": len(weeks),
        "stop_rate_ci_low": float(np.nanpercentile(stop_rates, 2.5)),
        "stop_rate_ci_high": float(np.nanpercentile(stop_rates, 97.5)),
        "net_R_ci_low": float(np.nanpercentile(net_returns, 2.5)),
        "net_R_ci_high": float(np.nanpercentile(net_returns, 97.5)),
    }


def child_scorecards(rows: list[dict]) -> list[dict]:
    dimensions = {
        "ENTRY_SESSION": ["entry_session_phase"],
        "NEW_YORK_WEEKDAY": ["entry_new_york_weekday"],
        "ENTRY_SESSION_X_NEW_YORK_WEEKDAY": ["entry_session_phase", "entry_new_york_weekday"],
        "ENTRY_SESSION_X_JOURNEY_RELATION": ["entry_session_phase", "relation"],
        "ENTRY_SESSION_X_NEW_YORK_WEEKDAY_X_JOURNEY_RELATION": ["entry_session_phase", "entry_new_york_weekday", "relation"],
        "ENTRY_SESSION_X_USD_EVENT_STATE": ["entry_session_phase", "usd_event_state"],
        "ENTRY_SESSION_X_YEAR": ["entry_session_phase", "analysis_year"],
        "NEW_YORK_WEEKDAY_X_YEAR": ["entry_new_york_weekday", "analysis_year"],
        "ENTRY_SESSION_X_NEW_YORK_WEEKDAY_X_YEAR": ["entry_session_phase", "entry_new_york_weekday", "analysis_year"],
        "ENTRY_SESSION_X_SIDE": ["entry_session_phase", "direction"],
        "BROKER_HOUR_X_ENTRY_SESSION": ["broker_hour", "entry_session_phase"],
        "BROKER_HOUR_X_ENTRY_SESSION_X_YEAR": ["broker_hour", "entry_session_phase", "analysis_year"],
        "BROKER_HOUR_X_ENTRY_SESSION_X_NEW_YORK_WEEKDAY": ["broker_hour", "entry_session_phase", "entry_new_york_weekday"],
        "BROKER_HOUR_X_ENTRY_SESSION_X_JOURNEY_RELATION": ["broker_hour", "entry_session_phase", "relation"],
    }
    output = [{"dimension": "ALL", "group": "ALL", **child_summary(rows), **bootstrap_child(rows, "ALL") }]
    for dimension, fields in dimensions.items():
        grouped: dict[tuple, list[dict]] = {}
        for row in rows:
            key = tuple(str(row[field]) for field in fields)
            grouped.setdefault(key, []).append(row)
        for key, values in sorted(grouped.items()):
            group = "|".join(key)
            output.append({"dimension": dimension, "group": group, **child_summary(values), **bootstrap_child(values, f"{dimension}:{group}")})
    return output


def nha_scorecards(rows: list[dict]) -> list[dict]:
    dimensions = {
        "KNOWN_SESSION": ["known_session_phase"],
        "NEW_YORK_WEEKDAY": ["known_new_york_weekday"],
        "KNOWN_SESSION_X_NEW_YORK_WEEKDAY": ["known_session_phase", "known_new_york_weekday"],
        "KNOWN_SESSION_X_EXPLANATION_STATE": ["known_session_phase", "explanation_state"],
        "KNOWN_SESSION_X_NEW_YORK_WEEKDAY_X_EXPLANATION_STATE": ["known_session_phase", "known_new_york_weekday", "explanation_state"],
        "KNOWN_SESSION_X_YEAR": ["known_session_phase", "analysis_year"],
        "NEW_YORK_WEEKDAY_X_YEAR": ["known_new_york_weekday", "analysis_year"],
        "BROKER_HOUR_X_KNOWN_SESSION": ["broker_hour", "known_session_phase"],
    }
    output = [{"dimension": "ALL", "group": "ALL", **nha_summary(rows)}]
    for dimension, fields in dimensions.items():
        grouped: dict[tuple, list[dict]] = {}
        for row in rows:
            key = tuple(str(row[field]) for field in fields)
            grouped.setdefault(key, []).append(row)
        for key, values in sorted(grouped.items()):
            output.append({"dimension": dimension, "group": "|".join(key), **nha_summary(values)})
    return output


def h20_audit(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    base = [row for row in rows if int(row["broker_hour"]) == 20 and row["relation"] == "ALIGNED_ACTIVE_JOURNEY"]
    for row in base:
        row["h20_group"] = "PRE_USD_MODHIGH_30_60" if row["usd_modhigh_state"] == "PRE_30_60" else "OTHER"
    dimensions = {
        "GROUP": ["h20_group"],
        "GROUP_X_SESSION": ["h20_group", "entry_session_phase"],
        "GROUP_X_NY_WEEKDAY": ["h20_group", "entry_new_york_weekday"],
        "GROUP_X_YEAR": ["h20_group", "analysis_year"],
        "GROUP_X_EVENT_FAMILY": ["h20_group", "next_usd_event_family"],
    }
    scorecards = []
    for dimension, fields in dimensions.items():
        grouped: dict[tuple, list[dict]] = {}
        for row in base:
            key = tuple(str(row[field]) for field in fields)
            grouped.setdefault(key, []).append(row)
        for key, values in sorted(grouped.items()):
            group = "|".join(key)
            scorecards.append({
                "dimension": dimension,
                "group": group,
                **child_summary(values),
                **bootstrap_child(values, f"H20:{dimension}:{group}"),
            })
    return base, scorecards


def file_manifest(path: Path) -> dict:
    rows = None
    if path.suffix == ".csv":
        with path.open("rb") as handle:
            rows = max(0, sum(1 for _ in handle) - 1)
    return {"file": path.name, "bytes": path.stat().st_size, "rows": rows, "sha256": sha256_file(path)}


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=repo / "research/v12/v12_phase1e_contract.json")
    parser.add_argument("--m1", type=Path, default=repo / "data/GOLD#/GOLD#_M1_202201030100_202609222358.csv")
    parser.add_argument("--calendar", type=Path, required=True)
    parser.add_argument("--calendar-overrides", type=Path)
    parser.add_argument("--phase1d", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=repo / "output/v12_phase1e_session_weekday_event_20260924")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    cutoff = parse_cutoff(contract["mechanism_cutoff"])
    safe_prepare_output(args.output, args.replace)
    sentinel_rows, calendar_quality = validate_calendar_clock(args.calendar, args.calendar_overrides)
    market, prefix_audit = load_market(args.m1, cutoff)
    activity = build_activity(market)
    children = enrich_children(args.phase1d / "V12_PHASE1D_V10_CHILD_EVENT_CONTEXT.csv")
    nhas = enrich_nha(args.phase1d / "V12_PHASE1D_NHA_EVENT_CONTEXT.csv")
    child_scores = child_scorecards(children)
    nha_scores = nha_scorecards(nhas)
    h20_rows, h20_scores = h20_audit(children)

    outputs = {
        "CLOCK_SENTINEL_VALIDATION.csv": sentinel_rows,
        "SESSION_ACTIVITY.csv": activity,
        "V10_CHILD_SESSION_CONTEXT.csv": children,
        "V10_CHILD_SESSION_SCORECARD.csv": child_scores,
        "NHA_SESSION_CONTEXT.csv": nhas,
        "NHA_SESSION_SCORECARD.csv": nha_scores,
        "H20_INTERACTION_CONTEXT.csv": h20_rows,
        "H20_INTERACTION_SCORECARD.csv": h20_scores,
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
        "market_sha256": sha256_file(args.m1),
        "calendar_sha256": sha256_file(args.calendar),
        "calendar_time_overrides_sha256": sha256_file(args.calendar_overrides) if args.calendar_overrides else None,
        "phase1d_manifest_sha256": sha256_file(args.phase1d / "V12_PHASE1D_MANIFEST.json"),
        "calendar_quality": calendar_quality,
        "market_prefix": prefix_audit.to_dict(),
        "v10_children": len(children),
        "nha_flips": len(nhas),
        "h20_aligned_children": len(h20_rows),
        "post_cutoff_price_rows_parsed": prefix_audit.post_cutoff_price_rows_parsed,
        "trade_authority": False,
        "sizing_authority": False,
    }
    diagnostics_path = args.output / f"{PREFIX}DIAGNOSTICS.json"
    write_json(diagnostics_path, diagnostics)
    paths.append(diagnostics_path)
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
