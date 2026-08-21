#!/usr/bin/env python3
"""Validate and summarize D-148 Entry-survival failure taxonomy ledgers.

No threshold fitting. Primary grain is one EXTERNAL_CONTINUATION fill. The primary
failure population is normalized-SL-before-1R. After SL, the shadow taxonomy ends at
original +1R recovery, H1/M30 direction-support loss, or explicit right censor.
"""
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


def kv(s: str) -> dict[str, str]:
    return {k: v.strip() for k, v in KV.findall(s or "")}


def dt(v: str | None):
    if not v or v == "NA":
        return None
    try:
        return datetime.strptime(v, DT_FMT)
    except ValueError:
        return None


def num(d: dict[str, str], key: str):
    try:
        v = d.get(key)
        if v is None or v == "NA":
            return None
        return float(v)
    except Exception:
        return None


def b(d: dict[str, str], key: str) -> bool:
    return d.get(key, "false").lower() == "true"


def pct(n: int, d: int) -> float:
    return 0.0 if not d else 100.0 * n / d


def med(xs):
    xs = [x for x in xs if x is not None]
    return None if not xs else statistics.median(xs)


def fmt(x, digits=3):
    return "NA" if x is None else f"{x:.{digits}f}"


def read(path: Path):
    starts = []
    stops = []
    fill_state = {}
    controls = {}
    sl_failures = {}
    owner_invalid = defaultdict(list)
    map_losses = defaultdict(list)
    root_invalid = defaultdict(list)
    entry_recovered = defaultdict(list)
    terminals = defaultdict(list)
    censored = defaultdict(list)
    pre_sl_censored = defaultdict(list)
    runner_1r_outcome = defaultdict(list)
    runner_fill = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            ev = (row.get("event") or "").strip()
            d = kv(row.get("detail") or "")
            sid = d.get("scenario_id", (row.get("object_id") or "").strip())
            if ev == "EDGE_AUDIT_START":
                starts.append(d)
            elif ev == "EDGE_AUDIT_STOP":
                stops.append(d)
            elif ev == "EDGE_AUDIT_D148_FILL_STATE" and sid:
                fill_state[sid] = d
            elif ev == "EDGE_AUDIT_D148_1R_CONTROL" and sid:
                controls[sid] = d
            elif ev == "EDGE_AUDIT_D148_SL_FAILURE" and sid:
                sl_failures[sid] = d
            elif ev == "EDGE_AUDIT_D148_FROZEN_OWNER_INVALIDATED" and sid:
                owner_invalid[sid].append(d)
            elif ev == "EDGE_AUDIT_D148_MAP_SUPPORT_LOST" and sid:
                map_losses[sid].append(d)
            elif ev == "EDGE_AUDIT_D148_ROOT_INVALIDATED" and sid:
                root_invalid[sid].append(d)
            elif ev == "EDGE_AUDIT_D148_ENTRY_RECOVERED" and sid:
                entry_recovered[sid].append(d)
            elif ev == "EDGE_AUDIT_D148_TERMINAL" and sid:
                terminals[sid].append(d)
            elif ev == "EDGE_AUDIT_D148_CENSORED" and sid:
                censored[sid].append(d)
            elif ev == "EDGE_AUDIT_D148_PRE_SL_CENSORED" and sid:
                pre_sl_censored[sid].append(d)
            elif ev == "EDGE_AUDIT_RUNNER_OUTCOME" and sid and d.get("target") == "1R":
                runner_1r_outcome[sid].append(d)
            elif ev == "EDGE_AUDIT_RUNNER_FILL_SNAPSHOT" and sid:
                runner_fill[sid] = d
    return {
        "starts": starts, "stops": stops, "fill_state": fill_state, "controls": controls,
        "sl_failures": sl_failures, "owner_invalid": owner_invalid, "map_losses": map_losses,
        "root_invalid": root_invalid, "entry_recovered": entry_recovered, "terminals": terminals,
        "censored": censored, "pre_sl_censored": pre_sl_censored,
        "runner_1r_outcome": runner_1r_outcome, "runner_fill": runner_fill,
    }


def validate(data):
    errors = []
    starts = data["starts"]
    if len(starts) != 1:
        errors.append(f"expected exactly one EDGE_AUDIT_START, got {len(starts)}")
    else:
        s = starts[0]
        if s.get("build") != "1.94R1L10":
            errors.append(f"unexpected audit build={s.get('build')}")
        if s.get("phase") != "ENTRY_SURVIVAL_FAILURE_TAXONOMY_V1_SHADOW":
            errors.append(f"unexpected phase={s.get('phase')}")
        if s.get("observed_exit_mode") != "ORIGINAL":
            errors.append(f"D148 requires ORIGINAL exit mode, observed {s.get('observed_exit_mode')}")

    fill_state = data["fill_state"]
    controls = data["controls"]
    failures = data["sl_failures"]
    pre_cens = data["pre_sl_censored"]
    if set(controls) & set(failures):
        errors.append("scenario appears in both 1R control and SL-failure population")
    classified_pre = set(controls) | set(failures) | set(pre_cens)
    missing_pre = set(fill_state) - classified_pre
    if missing_pre:
        errors.append(f"eligible fills without +1R/SL/censor classification: {len(missing_pre)}")

    # Existing exact 1R runner label must agree with D148 pre-SL classification.
    for sid in controls:
        outs = data["runner_1r_outcome"].get(sid, [])
        if not any(x.get("outcome") == "REACHED_BEFORE_SL" for x in outs):
            errors.append(f"{sid}: D148 control lacks matching 1R REACHED_BEFORE_SL")
    for sid in failures:
        outs = data["runner_1r_outcome"].get(sid, [])
        if not any(x.get("outcome") == "SL_FIRST" for x in outs):
            errors.append(f"{sid}: D148 SL failure lacks matching 1R SL_FIRST")

    # Each primary SL failure must have exactly one terminal or right censor.
    for sid, sl in failures.items():
        ts = data["terminals"].get(sid, [])
        cs = data["censored"].get(sid, [])
        if len(ts) + len(cs) != 1:
            errors.append(f"{sid}: expected one post-SL terminal/censor, got terminal={len(ts)} censor={len(cs)}")
            continue
        sl_at = dt(sl.get("sl_at"))
        row = ts[0] if ts else cs[0]
        end_at = dt(row.get("resolved_at") or row.get("censored_at"))
        if sl_at and end_at and end_at < sl_at:
            errors.append(f"{sid}: post-SL resolution precedes SL")
        if ts:
            outcome = ts[0].get("outcome", "")
            if outcome == "ORIGINAL_1R_RECOVERED_BEFORE_MAP_SUPPORT_LOSS":
                if not b(ts[0], "one_r_recovered_after_sl"):
                    errors.append(f"{sid}: 1R recovery terminal missing one_r_recovered flag")
                one_at = dt(ts[0].get("one_r_recovered_at"))
                post_loss_at = dt(ts[0].get("post_sl_map_support_loss_at"))
                if post_loss_at is not None:
                    errors.append(f"{sid}: 1R recovery terminal unexpectedly has a post-SL map-support-loss timestamp")
            elif outcome in {"MAP_SUPPORT_NOT_SAME_AT_SL", "MAP_SUPPORT_LOST_AFTER_SL"}:
                if outcome == "MAP_SUPPORT_NOT_SAME_AT_SL" and b(sl, "map_support_same_at_sl"):
                    errors.append(f"{sid}: MAP_SUPPORT_NOT_SAME_AT_SL but SL row says support_same=true")
                if outcome == "MAP_SUPPORT_LOST_AFTER_SL":
                    loss_at = dt(ts[0].get("post_sl_map_support_loss_at"))
                    if loss_at is None:
                        errors.append(f"{sid}: map-loss terminal missing post_sl_map_support_loss_at")
                    elif sl_at and loss_at < sl_at:
                        errors.append(f"{sid}: post-SL map-support-loss timestamp precedes SL")
                    if end_at and loss_at and end_at != loss_at:
                        errors.append(f"{sid}: MAP_SUPPORT_LOST_AFTER_SL resolved_at != post_sl_map_support_loss_at")
            else:
                errors.append(f"{sid}: unexpected terminal outcome={outcome}")

        if len(data["entry_recovered"].get(sid, [])) > 1:
            errors.append(f"{sid}: multiple entry-recovered rows")
        if len(data["owner_invalid"].get(sid, [])) > 1:
            errors.append(f"{sid}: multiple frozen-owner invalidation rows")
        if len(data["root_invalid"].get(sid, [])) > 1:
            errors.append(f"{sid}: multiple Root invalidation rows")
        if len(data["map_losses"].get(sid, [])) > 1:
            errors.append(f"{sid}: multiple first-map-support-loss rows")

    # Stop counters should reconcile to emitted rows when a stop row exists.
    if len(data["stops"]) == 1:
        stop = data["stops"][0]
        expected = {
            "d148_eligible": len(fill_state),
            "d148_one_r_controls": len(controls),
            "d148_sl_failures": len(failures),
            "d148_entry_recoveries": sum(len(v) for v in data["entry_recovered"].values()),
            "d148_one_r_recoveries": sum(1 for rows in data["terminals"].values() for x in rows if x.get("outcome") == "ORIGINAL_1R_RECOVERED_BEFORE_MAP_SUPPORT_LOSS"),
            "d148_map_loss_terminals": sum(1 for rows in data["terminals"].values() for x in rows if x.get("outcome") in {"MAP_SUPPORT_NOT_SAME_AT_SL", "MAP_SUPPORT_LOST_AFTER_SL"}),
            "d148_frozen_owner_invalidations": sum(len(v) for v in data["owner_invalid"].values()),
            "d148_root_invalidations": sum(len(v) for v in data["root_invalid"].values()),
            "d148_censored": sum(len(v) for v in data["censored"].values()),
            "d148_pre_sl_censored": sum(len(v) for v in data["pre_sl_censored"].values()),
        }
        for k, n in expected.items():
            try:
                actual = int(float(stop.get(k, "nan")))
            except Exception:
                errors.append(f"stop counter missing/invalid: {k}")
                continue
            if actual != n:
                errors.append(f"stop counter mismatch {k}: stop={actual} rows={n}")
    elif len(data["stops"]) > 1:
        errors.append(f"expected at most one EDGE_AUDIT_STOP, got {len(data['stops'])}")

    return errors


def summarize(data):
    fills = data["fill_state"]
    controls = data["controls"]
    failures = data["sl_failures"]
    terminals = {sid: rows[0] for sid, rows in data["terminals"].items() if rows}
    censored = {sid: rows[0] for sid, rows in data["censored"].items() if rows}

    print(f"eligible_continuation_fills={len(fills)}")
    print(f"+1R_controls={len(controls)} ({pct(len(controls), len(fills)):.2f}%)")
    print(f"SL_before_1R_failures={len(failures)} ({pct(len(failures), len(fills)):.2f}%)")
    print(f"pre_SL_right_censored={len(data['pre_sl_censored'])}")

    outcomes = Counter(x.get("outcome", "UNKNOWN") for x in terminals.values())
    outcomes["RIGHT_CENSORED_AFTER_SL"] += len(censored)
    print("post_SL_taxonomy:")
    for k, n in outcomes.most_common():
        print(f"  {k}={n}/{len(failures)} ({pct(n, len(failures)):.1f}%)")

    if failures:
        pre_mfe = [num(x, "pre_sl_mfe_r") for x in failures.values()]
        pre_mae = [num(x, "pre_sl_mae_r") for x in failures.values()]
        print(f"failure_pre_SL_median_MFE_R={fmt(med(pre_mfe))}")
        print(f"failure_pre_SL_median_MAE_R={fmt(med(pre_mae))}")
        print(f"frozen_owner_alive_at_fill={sum(b(x,'frozen_owner_alive_at_fill') for x in failures.values())}/{len(failures)}")
        print(f"frozen_owner_invalidated_before_SL={sum(b(x,'frozen_owner_invalidated_before_sl') for x in failures.values())}/{len(failures)}")
        print(f"map_support_loss_seen_before_SL={sum(b(x,'map_support_loss_seen_before_sl') for x in failures.values())}/{len(failures)}")
        print(f"map_support_same_at_SL={sum(b(x,'map_support_same_at_sl') for x in failures.values())}/{len(failures)}")
        print(f"root_invalidated_before_SL={sum(b(x,'root_invalidated_before_sl') for x in failures.values())}/{len(failures)}")

    recovered = [x for x in terminals.values() if x.get("outcome") == "ORIGINAL_1R_RECOVERED_BEFORE_MAP_SUPPORT_LOSS"]
    mapfail = [x for x in terminals.values() if x.get("outcome") in {"MAP_SUPPORT_NOT_SAME_AT_SL", "MAP_SUPPORT_LOST_AFTER_SL"}]
    for name, rows in [("RECOVERED_1R", recovered), ("MAP_SUPPORT_FAILURE", mapfail)]:
        if not rows:
            continue
        print(f"{name}: n={len(rows)}")
        print(f"  median_pre_SL_MFE_R={fmt(med([num(x,'pre_sl_mfe_r') for x in rows]))}")
        print(f"  median_post_SL_max_adverse_from_fill_R={fmt(med([num(x,'post_sl_max_adverse_r_from_fill') for x in rows]))}")
        print(f"  median_extra_beyond_SL_R={fmt(med([num(x,'post_sl_extra_beyond_sl_r') for x in rows]))}")
        print(f"  entry_recovered_after_SL={sum(b(x,'entry_recovered_after_sl') for x in rows)}/{len(rows)}")
        print(f"  frozen_owner_invalidated={sum(b(x,'frozen_owner_invalidated') for x in rows)}/{len(rows)}")
        print(f"  root_invalidated={sum(dt(x.get('root_invalidated_at')) is not None for x in rows)}/{len(rows)}")

    # Direction and plan-map splits for the primary failure population.
    print("failure_split_by_direction:")
    for direction in ["LONG", "SHORT"]:
        ids = [sid for sid, x in failures.items() if x.get("direction") == direction]
        if not ids:
            continue
        rec = sum(terminals.get(sid, {}).get("outcome") == "ORIGINAL_1R_RECOVERED_BEFORE_MAP_SUPPORT_LOSS" for sid in ids)
        mf = sum(terminals.get(sid, {}).get("outcome") in {"MAP_SUPPORT_NOT_SAME_AT_SL", "MAP_SUPPORT_LOST_AFTER_SL"} for sid in ids)
        print(f"  {direction}: n={len(ids)} recovered_1R={rec} map_support_failure={mf} censored={sum(sid in censored for sid in ids)}")

    print("failure_split_by_plan_map:")
    for tf in ["H1", "M30"]:
        ids = [sid for sid, x in failures.items() if x.get("active_map_tf_at_plan") == tf]
        if not ids:
            continue
        rec = sum(terminals.get(sid, {}).get("outcome") == "ORIGINAL_1R_RECOVERED_BEFORE_MAP_SUPPORT_LOSS" for sid in ids)
        mf = sum(terminals.get(sid, {}).get("outcome") in {"MAP_SUPPORT_NOT_SAME_AT_SL", "MAP_SUPPORT_LOST_AFTER_SL"} for sid in ids)
        print(f"  {tf}: n={len(ids)} recovered_1R={rec} map_support_failure={mf} censored={sum(sid in censored for sid in ids)}")

    # Descriptive Fill-time variables from existing D145 snapshot, no threshold search.
    def fill_val(sid, key):
        return num(data["runner_fill"].get(sid, {}), key)
    variables = [
        "fill_fvg_width_r",
        "fill_m30_range_progress",
        "fill_m30_range_remaining_to_external_r",
        "fill_m30_wave_progression_ratio",
        "fill_m30_wave_pb_count",
        "prefill_max_favorable_r",
        "prefill_max_adverse_r",
    ]
    print("fill_time_descriptive_medians_no_threshold_fit:")
    for key in variables:
        c = med([fill_val(sid, key) for sid in controls])
        f = med([fill_val(sid, key) for sid in failures])
        if c is None and f is None:
            continue
        print(f"  {key}: +1R_control={fmt(c)} SL_failure={fmt(f)}")

    print("primary_failure_cases:")
    ordered = sorted(failures.items(), key=lambda kvp: (dt(kvp[1].get("sl_at")) or datetime.max, kvp[0]))
    for sid, sl in ordered:
        term = terminals.get(sid)
        censor = censored.get(sid)
        outcome = term.get("outcome") if term else ("RIGHT_CENSORED_AFTER_SL" if censor else "MISSING")
        end = term or censor or {}
        print(
            "  " + sid +
            f" dir={sl.get('direction','NA')} map={sl.get('active_map_tf_at_plan','NA')}" +
            f" preMFE={fmt(num(sl,'pre_sl_mfe_r'))} preMAE={fmt(num(sl,'pre_sl_mae_r'))}" +
            f" ownerPB={sl.get('frozen_owner_invalidated_before_sl','NA')}" +
            f" mapSameSL={sl.get('map_support_same_at_sl','NA')}" +
            f" rootInv={sl.get('root_invalidated_before_sl','NA')}" +
            f" outcome={outcome}" +
            f" postWorst={fmt(num(end,'post_sl_max_adverse_r_from_fill'))}" +
            f" entryRec={end.get('entry_recovered_after_sl','NA')}"
        )


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: summarize_d148_entry_survival_failure_taxonomy.py ledger.csv", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    data = read(path)
    errors = validate(data)
    print("D148 EVENT INTEGRITY:", "PASS" if not errors else "FAIL")
    print(f"file={path}")
    if errors:
        for e in errors[:50]:
            print("ERROR:", e)
        if len(errors) > 50:
            print(f"... {len(errors)-50} more errors")
        return 1
    summarize(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
