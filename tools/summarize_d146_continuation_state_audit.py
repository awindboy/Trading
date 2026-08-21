#!/usr/bin/env python3
"""Validate and summarize D-146 continuation-state audit without threshold fitting."""
from __future__ import annotations

import csv
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

KV = re.compile(r"([A-Za-z0-9_]+)=(.*?)(?=\s+[A-Za-z0-9_]+=|$)")
DT_FMT = "%Y.%m.%d %H:%M:%S"


def kv(detail: str) -> dict[str, str]:
    # MT5 datetime values contain a space. Split on the next key= boundary.
    return {k: v.strip() for k, v in KV.findall(detail)}


def b(d: dict[str, str], key: str) -> bool:
    return d.get(key, "false").lower() == "true"


def num(d: dict[str, str], key: str):
    try:
        v = d.get(key)
        if v is None or v == "NA":
            return None
        return float(v)
    except Exception:
        return None


def dt(v: str | None):
    if not v or v == "NA":
        return None
    try:
        return datetime.strptime(v, DT_FMT)
    except ValueError:
        return None


def med(rows: list[dict[str, str]], key: str):
    xs = [num(r, key) for r in rows]
    xs = [x for x in xs if x is not None]
    return None if not xs else statistics.median(xs)


def pct(a: int, n: int) -> float:
    return 0.0 if not n else 100.0 * a / n


def read_ledger(path: Path):
    starts = []
    one_r: dict[str, list[dict[str, str]]] = defaultdict(list)
    events: dict[str, list[dict[str, str]]] = defaultdict(list)
    deliveries: dict[str, list[dict[str, str]]] = defaultdict(list)
    terminals: dict[str, list[dict[str, str]]] = defaultdict(list)
    censored: dict[str, list[dict[str, str]]] = defaultdict(list)
    runner_outcomes: dict[str, dict[str, str]] = defaultdict(dict)
    stops = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if len(row) < 6:
                continue
            event = row[1]
            d = kv(row[5])
            sid = d.get("scenario_id", row[4] if len(row) > 4 else "")
            if event == "EDGE_AUDIT_START":
                starts.append(d)
            elif event == "EDGE_AUDIT_D146_1R_STATE":
                one_r[sid].append(d)
            elif event == "EDGE_AUDIT_D146_M30_EVENT":
                events[sid].append(d)
            elif event == "EDGE_AUDIT_D146_ORIGINAL_EXTERNAL_DELIVERED":
                deliveries[sid].append(d)
            elif event == "EDGE_AUDIT_D146_TERMINAL":
                terminals[sid].append(d)
            elif event == "EDGE_AUDIT_D146_CENSORED":
                censored[sid].append(d)
            elif event == "EDGE_AUDIT_RUNNER_OUTCOME":
                runner_outcomes[sid][d.get("target", "?")] = d.get("outcome", "?")
            elif event == "EDGE_AUDIT_STOP":
                stops.append(d)
    return starts, one_r, events, deliveries, terminals, censored, runner_outcomes, stops


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: summarize_d146_continuation_state_audit.py LEDGER.csv")
        return 2

    path = Path(sys.argv[1])
    starts, one_r, events, deliveries, terminals, censored, runner_outcomes, stops = read_ledger(path)

    errors: list[str] = []
    warnings: list[str] = []
    armed_ids = sorted(one_r)
    if not armed_ids:
        errors.append("No EDGE_AUDIT_D146_1R_STATE rows found.")

    if starts:
        phase = starts[-1].get("phase")
        build = starts[-1].get("build")
        if build != "1.92R1L8" or phase != "CONTINUATION_STATE_AUDIT_V1_SHADOW":
            errors.append(f"Unexpected audit identity: build={build} phase={phase}")
    else:
        errors.append("No EDGE_AUDIT_START row found.")

    resolved_rows: list[dict[str, str]] = []
    for sid in armed_ids:
        if len(one_r[sid]) != 1:
            errors.append(f"{sid}: D146 1R state rows={len(one_r[sid])}, expected 1")
        nterm = len(terminals.get(sid, []))
        ncens = len(censored.get(sid, []))
        if nterm + ncens != 1:
            errors.append(f"{sid}: terminal+censor rows={nterm + ncens}, expected exactly 1")
        if nterm == 1:
            resolved_rows.append(terminals[sid][0])
        if nterm and ncens:
            errors.append(f"{sid}: both terminal and censored")

        t0 = dt(one_r[sid][0].get("one_r_at")) if one_r[sid] else None
        for e in events.get(sid, []):
            te = dt(e.get("event_available_at"))
            if t0 and te and te < t0:
                errors.append(f"{sid}: M30 event before T0 ({te} < {t0})")
        for drow in deliveries.get(sid, []):
            td = dt(drow.get("delivered_at"))
            if t0 and td and td < t0:
                errors.append(f"{sid}: original external delivery before T0")
        if nterm == 1:
            tr = terminals[sid][0]
            t1 = dt(tr.get("resolved_at"))
            if t0 and t1 and t1 < t0:
                errors.append(f"{sid}: terminal before T0")
            outcome = tr.get("outcome")
            if outcome not in {"+2R_REACHED", "SL_AFTER_1R"}:
                errors.append(f"{sid}: unexpected D146 terminal outcome={outcome}")
            expected = runner_outcomes.get(sid, {}).get("2R")
            if outcome == "+2R_REACHED" and expected not in {None, "REACHED_BEFORE_SL"}:
                errors.append(f"{sid}: D146 +2R conflicts with runner 2R={expected}")
            if outcome == "SL_AFTER_1R" and expected not in {None, "SL_FIRST"}:
                errors.append(f"{sid}: D146 SL conflicts with runner 2R={expected}")
            if b(tr, "original_external_at_or_beyond_at_1r") and b(tr, "original_external_delivered_after_1r"):
                errors.append(f"{sid}: original external cannot be both already reached at T0 and delivered after T0")
            delivery_rows = len(deliveries.get(sid, []))
            if delivery_rows > 1:
                errors.append(f"{sid}: original external delivery rows={delivery_rows}, expected at most 1")
            if b(tr, "original_external_delivered_after_1r") != (delivery_rows == 1):
                errors.append(f"{sid}: terminal original-external delivery flag disagrees with delivery row count={delivery_rows}")

    # Event count consistency against terminal/censor summaries.
    for sid in armed_ids:
        summary_rows = terminals.get(sid, []) or censored.get(sid, [])
        if len(summary_rows) != 1:
            continue
        summary = summary_rows[0]
        erows = events.get(sid, [])
        counted = {
            "m30_same_direction_initial_bos_count": sum(e.get("event_type") == "INITIAL_BOS" and b(e, "same_direction") for e in erows),
            "m30_same_direction_bos_count": sum(e.get("event_type") == "BOS" and b(e, "same_direction") for e in erows),
            "m30_opposite_direction_event_count": sum(b(e, "opposite_direction") for e in erows),
            "m30_protected_break_count": sum(b(e, "protected_break") for e in erows),
            "m30_owner_change_count": sum(b(e, "owner_changed") for e in erows),
            "m30_trend_loss_count": sum(b(e, "trend_lost") for e in erows),
            "m30_outward_external_refresh_count": sum(b(e, "outward_external_refresh") for e in erows),
        }
        for key, actual in counted.items():
            logged = num(summary, key)
            if logged is not None and int(logged) != actual:
                errors.append(f"{sid}: {key} summary={int(logged)} event_rows={actual}")

    print(f"Ledger: {path}")
    print(f"D146 armed +1R continuation runners: {len(armed_ids):,}")
    print(f"D146 resolved terminals:             {sum(len(v) for v in terminals.values()):,}")
    print(f"D146 right-censored:                 {sum(len(v) for v in censored.values()):,}")
    print(f"D146 M30 event rows:                 {sum(len(v) for v in events.values()):,}")
    print(f"Original external delivery rows:     {sum(len(v) for v in deliveries.values()):,}")

    outcome_counts = Counter(r.get("outcome", "?") for r in resolved_rows)
    print("\nResolved outcome:")
    for outcome in ("+2R_REACHED", "SL_AFTER_1R"):
        n = outcome_counts.get(outcome, 0)
        print(f"  {outcome:14s}: {n:4d}/{len(resolved_rows):4d} = {pct(n, len(resolved_rows)):6.2f}%")

    print("\nMechanism frequency by outcome (descriptive; no fitted threshold):")
    for outcome in ("+2R_REACHED", "SL_AFTER_1R"):
        rows = [r for r in resolved_rows if r.get("outcome") == outcome]
        if not rows:
            continue
        refresh = sum((num(r, "m30_outward_external_refresh_count") or 0) > 0 for r in rows)
        pb = sum((num(r, "m30_protected_break_count") or 0) > 0 for r in rows)
        opp = sum((num(r, "m30_opposite_direction_event_count") or 0) > 0 for r in rows)
        loss = sum((num(r, "m30_trend_loss_count") or 0) > 0 for r in rows)
        owner = sum((num(r, "m30_owner_change_count") or 0) > 0 for r in rows)
        delivered = sum(b(r, "original_external_delivered_after_1r") for r in rows)
        replaced = sum(b(r, "original_external_replaced_after_1r") for r in rows)
        print(f"  {outcome}: n={len(rows)}")
        print(f"    outward refresh >0 : {refresh:4d}/{len(rows):4d} = {pct(refresh,len(rows)):6.2f}%")
        print(f"    protected break >0 : {pb:4d}/{len(rows):4d} = {pct(pb,len(rows)):6.2f}%")
        print(f"    opposite event >0  : {opp:4d}/{len(rows):4d} = {pct(opp,len(rows)):6.2f}%")
        print(f"    trend loss >0      : {loss:4d}/{len(rows):4d} = {pct(loss,len(rows)):6.2f}%")
        print(f"    owner change >0    : {owner:4d}/{len(rows):4d} = {pct(owner,len(rows)):6.2f}%")
        print(f"    original ext delivered after 1R: {delivered:4d}/{len(rows):4d} = {pct(delivered,len(rows)):6.2f}%")
        print(f"    original ext replaced after 1R : {replaced:4d}/{len(rows):4d} = {pct(replaced,len(rows)):6.2f}%")
        print(f"    median 1R M30 progress          : {med(rows,'one_r_m30_range_progress')}")
        print(f"    median 1R remaining external R  : {med(rows,'one_r_m30_remaining_to_external_r')}")

    print("\nDirection split:")
    for direction in ("LONG", "SHORT"):
        rows = [r for r in resolved_rows if r.get("direction") == direction]
        wins = sum(r.get("outcome") == "+2R_REACHED" for r in rows)
        print(f"  {direction:5s}: +2R={wins:3d}/{len(rows):3d} = {pct(wins,len(rows)):6.2f}%")
        for outcome in ("+2R_REACHED", "SL_AFTER_1R"):
            sub = [r for r in rows if r.get("outcome") == outcome]
            if sub:
                refresh = sum((num(r, "m30_outward_external_refresh_count") or 0) > 0 for r in sub)
                deterioration = sum(
                    (num(r, "m30_protected_break_count") or 0) > 0
                    or (num(r, "m30_opposite_direction_event_count") or 0) > 0
                    or (num(r, "m30_owner_change_count") or 0) > 0
                    or (num(r, "m30_trend_loss_count") or 0) > 0
                    for r in sub
                )
                print(f"    {outcome:14s}: n={len(sub):3d} refresh={pct(refresh,len(sub)):6.2f}% deterioration={pct(deterioration,len(sub)):6.2f}%")

    # Geometry split using the +1R-time external, not a fitted progress threshold.
    geometry = defaultdict(list)
    for sid in armed_ids:
        if len(one_r[sid]) != 1 or len(terminals.get(sid, [])) != 1:
            continue
        o = one_r[sid][0]
        t = terminals[sid][0]
        ext = num(o, "one_r_m30_external_price")
        target = num(o, "target_2r")
        direction = o.get("direction")
        if not b(o, "one_r_m30_external_available") or ext is None or target is None:
            geometry["M30_EXTERNAL_UNAVAILABLE"].append(t)
        elif direction == "LONG":
            geometry["2R_BEFORE_OR_AT_1R_EXTERNAL" if target <= ext else "2R_BEYOND_1R_EXTERNAL"].append(t)
        elif direction == "SHORT":
            geometry["2R_BEFORE_OR_AT_1R_EXTERNAL" if target >= ext else "2R_BEYOND_1R_EXTERNAL"].append(t)

    print("\nStructural geometry split (no optimized cutoff):")
    for name in ("2R_BEFORE_OR_AT_1R_EXTERNAL", "2R_BEYOND_1R_EXTERNAL", "M30_EXTERNAL_UNAVAILABLE"):
        rows = geometry.get(name, [])
        if not rows:
            continue
        wins = sum(r.get("outcome") == "+2R_REACHED" for r in rows)
        refresh = sum((num(r, "m30_outward_external_refresh_count") or 0) > 0 for r in rows)
        print(f"  {name:31s}: n={len(rows):3d} +2R={pct(wins,len(rows)):6.2f}% refresh={pct(refresh,len(rows)):6.2f}%")
        for outcome in ("+2R_REACHED", "SL_AFTER_1R"):
            sub = [r for r in rows if r.get("outcome") == outcome]
            if not sub:
                continue
            sub_refresh = sum((num(r, "m30_outward_external_refresh_count") or 0) > 0 for r in sub)
            sub_deterioration = sum(
                (num(r, "m30_protected_break_count") or 0) > 0
                or (num(r, "m30_opposite_direction_event_count") or 0) > 0
                or (num(r, "m30_owner_change_count") or 0) > 0
                or (num(r, "m30_trend_loss_count") or 0) > 0
                for r in sub
            )
            print(f"    {outcome:14s}: n={len(sub):3d} refresh={pct(sub_refresh,len(sub)):6.2f}% deterioration={pct(sub_deterioration,len(sub)):6.2f}%")

    if stops:
        s = stops[-1]
        expected_stop = {
            "d146_armed": len(armed_ids),
            "d146_structure_events": sum(len(v) for v in events.values()),
            "d146_original_external_deliveries": sum(len(v) for v in deliveries.values()),
            "d146_terminals": sum(len(v) for v in terminals.values()),
            "d146_censored": sum(len(v) for v in censored.values()),
        }
        for key, actual in expected_stop.items():
            logged = num(s, key)
            if logged is not None and int(logged) != actual:
                errors.append(f"EDGE_AUDIT_STOP {key}={int(logged)} but rows={actual}")
        print("\nStop counters:")
        for k in ("d146_armed", "d146_structure_events", "d146_original_external_deliveries", "d146_terminals", "d146_censored"):
            if k in s:
                print(f"  {k}: {s[k]}")

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print("  -", w)

    if errors:
        print("\nD146 EVENT INTEGRITY: FAIL")
        for e in errors[:50]:
            print("  -", e)
        if len(errors) > 50:
            print(f"  ... and {len(errors)-50} more")
        return 1

    print("\nD146 EVENT INTEGRITY: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
