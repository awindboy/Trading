from __future__ import annotations

import csv
import datetime as dt
import io
import json
import math
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import mt5_batch_runner as runner
from mt5_batch_runner import BatchError, TestCase

EXPECTED_GIT_HEAD = "0e7b1d5b39de1126394e88f85abf87cde167fc84"
SYMBOL = "GOLD#"

CASE = TestCase(
    "D155_FULL_AUDIT",
    {
        "InpEventLogMode": 1,            # FULL_AUDIT; logging only
        "InpExitManagementMode": 9,      # same V3E control used in D154O/P
        "InpEpisodeManagementMode": 0,
        "InpV2D151CausalAudit": True,
        "InpV2D154EntrySurvivalAudit": False,
        "InpV2D154BConfirmationAudit": False,
        "InpV2D154CReaccelerationFvgAudit": False,
        "InpV2D154FCausalLineageAudit": False,
        "InpV2D154GHTFRootLineageAudit": False,
        "InpV2D154HHTFNestedReplayAudit": False,
        "InpV2D154JHTFDeliveryGeometryAudit": False,
        "InpV2D154KCrossScaleReactionAudit": False,
        "InpV2D154MExecutionFrictionCounterfactualAudit": False,
    },
    "D155 mentor-fidelity opportunity audit; FULL_AUDIT logging only",
)

BENCHMARKS = {
    2024: {
        "SCENARIO_PLANNED": 700,
        "SCENARIO_ROOT_CONTACT_BOUND": 386,
        "SCENARIO_SWEEP_ACCEPTED": 309,
        "SCENARIO_CHOCH_ACCEPTED": 131,
        "SCENARIO_FVG_SELECTED": 120,
        "EXECUTION_GEOMETRY_READY": 61,
        "D151_FILL_SNAPSHOT": 52,
    },
    2025: {
        "SCENARIO_PLANNED": 804,
        "SCENARIO_ROOT_CONTACT_BOUND": 466,
        "SCENARIO_SWEEP_ACCEPTED": 363,
        "SCENARIO_CHOCH_ACCEPTED": 165,
        "SCENARIO_FVG_SELECTED": 151,
        "EXECUTION_GEOMETRY_READY": 68,
        "D151_FILL_SNAPSHOT": 55,
    },
}


def kv(text: str) -> dict[str, str]:
    return {
        m.group(1): m.group(2)
        for m in re.finditer(r"(\w+)=([^ ]+)", text or "")
    }


def parse_time(text: str) -> dt.datetime | None:
    if not text or text == "NA":
        return None
    try:
        return dt.datetime.strptime(text, "%Y.%m.%d %H:%M:%S")
    except ValueError:
        return None


def row_time(row: dict[str, str]) -> dt.datetime | None:
    # Detector/structure causality follows availability. Scenario lifecycle
    # observed_at is normally identical at runtime.
    return parse_time(row.get("available_at", "")) or parse_time(row.get("observed_at", ""))


def git_head(repo: Path) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    if cp.returncode != 0:
        raise BatchError("Could not read Git HEAD.")
    return cp.stdout.strip()


def load_gold_csv(raw_zip: Path) -> list[dict[str, str]]:
    with zipfile.ZipFile(raw_zip) as z:
        names = [
            n for n in z.namelist()
            if n.endswith(".csv") and f"__{SYMBOL}__2025.csv" in n
        ]
        if len(names) != 1:
            raise BatchError(f"GOLD result CSV discovery failed: {names}")
        return list(csv.DictReader(io.StringIO(
            z.read(names[0]).decode("utf-8-sig", errors="replace")
        )))


def event_sid(row: dict[str, str]) -> str:
    d = kv(row.get("detail", ""))
    sid = d.get("scenario_id", "")
    if sid:
        return sid
    if row.get("event", "").startswith("SCENARIO_"):
        return row.get("object_id", "")
    return ""


def direction_compatible_sweep_side(direction: str) -> str:
    if direction == "LONG":
        return "LOW"
    if direction == "SHORT":
        return "HIGH"
    return "UNKNOWN"


def structure_direction(row: dict[str, str]) -> str:
    return kv(row.get("detail", "")).get("direction", "UNKNOWN")


def wave_latency_minutes(row: dict[str, str]) -> float | None:
    d = kv(row.get("detail", ""))
    occurred = parse_time(d.get("occurred", ""))
    available = parse_time(row.get("available_at", ""))
    if occurred is None or available is None:
        return None
    return (available - occurred).total_seconds() / 60.0


def terminal_row(events: dict[str, list[dict[str, str]]]) -> dict[str, str] | None:
    candidates = []
    for ev in (
        "SCENARIO_CANCELED",
        "SCENARIO_EXECUTION_NO_TRADE",
        "SCENARIO_FVG_NO_ENTRY",
    ):
        for r in events.get(ev, []):
            t = row_time(r)
            if t is not None:
                candidates.append((t, r))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def rows_between(
    rows: list[dict[str, str]],
    start: dt.datetime,
    end: dt.datetime,
    *,
    timeframe: str | None = None,
    event_names: set[str] | None = None,
) -> list[dict[str, str]]:
    out = []
    for r in rows:
        if timeframe is not None and r.get("timeframe") != timeframe:
            continue
        if event_names is not None and r.get("event") not in event_names:
            continue
        t = row_time(r)
        if t is None or t < start or t > end:
            continue
        out.append(r)
    return out


def quantiles(vals: list[float]) -> dict[str, float | None]:
    if not vals:
        return {k: None for k in ("p10","p25","p50","p75","p90")}
    s = sorted(vals)
    def q(p: float) -> float:
        if len(s) == 1:
            return s[0]
        pos = (len(s)-1)*p
        lo = int(math.floor(pos))
        hi = int(math.ceil(pos))
        if lo == hi:
            return s[lo]
        w = pos-lo
        return s[lo]*(1-w)+s[hi]*w
    return {
        "p10": q(.10), "p25": q(.25), "p50": q(.50),
        "p75": q(.75), "p90": q(.90),
    }


def analyze_year(year: int, rows: list[dict[str, str]]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    counts = Counter(r.get("event", "") for r in rows)

    # Non-interference / exact strategy parity.
    expected = BENCHMARKS[year]
    mismatch = {
        ev: {"expected": n, "actual": counts[ev]}
        for ev, n in expected.items()
        if counts[ev] != n
    }
    if mismatch:
        raise BatchError(
            f"{year}: FULL_AUDIT changed or failed to reproduce strategy counts: "
            + json.dumps(mismatch)
        )

    bad = [
        ev for ev in (
            "EXECUTION_DIVERGENCE",
            "PENDING_CANCEL_REJECTED",
            "D154K_INTEGRITY_WARNING",
            "D154M_INTEGRITY_WARNING",
        )
        if counts[ev] > 0
    ]
    if bad:
        raise BatchError(f"{year}: execution/integrity failure events={bad}")

    starts = [r for r in rows if r.get("event") == "EA_START"]
    stops = [r for r in rows if r.get("event") == "EA_STOP"]
    if len(starts) != 1 or len(stops) != 1:
        raise BatchError(f"{year}: EA_START/EA_STOP count failure")

    expected_start = f"{year}.01.01 00:00:00"
    if starts[0].get("observed_at") != expected_start:
        raise BatchError(
            f"{year}: expected full-year EA_START {expected_start}, "
            f"got {starts[0].get('observed_at')}"
        )

    scenarios: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        sid = event_sid(r)
        if sid:
            scenarios[sid][r.get("event", "")].append(r)

    sweep_detector_rows = [
        r for r in rows
        if r.get("event") == "M1_SWEEP_DETECTED" and parse_time(r.get("available_at", "")) is not None
    ]
    structure_rows = [
        r for r in rows
        if r.get("event") in {
            "STRUCTURE_INITIAL_BOS",
            "STRUCTURE_BOS",
            "STRUCTURE_PROTECTED_BREAK",
        }
        and r.get("timeframe") in {"M1", "M5"}
        and parse_time(r.get("available_at", "")) is not None
    ]
    wave_rows = [
        r for r in rows
        if r.get("event") == "WAVE_CONFIRMED"
        and r.get("timeframe") in {"M1", "M5"}
        and parse_time(r.get("available_at", "")) is not None
    ]

    contact_queue: list[dict[str, Any]] = []
    sweep_no_choch_queue: list[dict[str, Any]] = []

    for sid, evs in scenarios.items():
        plan = evs.get("SCENARIO_PLANNED", [])
        direction = "UNKNOWN"
        if plan:
            direction = kv(plan[0].get("detail", "")).get("direction", "UNKNOWN")
        if direction == "UNKNOWN":
            contact = evs.get("SCENARIO_ROOT_CONTACT_BOUND", [])
            if contact:
                direction = kv(contact[0].get("detail", "")).get("direction", "UNKNOWN")

        # A. Contact but no accepted later sweep.
        contacts = evs.get("SCENARIO_ROOT_CONTACT_BOUND", [])
        accepted_sweeps = evs.get("SCENARIO_SWEEP_ACCEPTED", [])
        if contacts and not accepted_sweeps:
            cr = contacts[0]
            cd = kv(cr.get("detail", ""))
            ct = row_time(cr)
            tr = terminal_row(evs)
            tt = row_time(tr) if tr else None
            if ct is not None and tt is not None and tt >= ct:
                contact_bar = parse_time(cd.get("root_contact_bar_open", ""))
                required_side = direction_compatible_sweep_side(direction)
                same_bar = []
                later = []
                for sr in sweep_detector_rows:
                    sd = kv(sr.get("detail", ""))
                    if sd.get("side") != required_side:
                        continue
                    st = row_time(sr)
                    bar_open = parse_time(sd.get("bar_open", ""))
                    if st is None:
                        continue
                    if contact_bar is not None and bar_open == contact_bar:
                        same_bar.append(sr)
                    if st > ct and st <= tt:
                        later.append(sr)

                contact_queue.append({
                    "year": year,
                    "scenario_id": sid,
                    "direction": direction,
                    "contact_at": cr.get("observed_at"),
                    "contact_bar_open": cd.get("root_contact_bar_open"),
                    "terminal_at": tr.get("observed_at") if tr else None,
                    "terminal_event": tr.get("event") if tr else None,
                    "terminal_reason": kv(tr.get("detail", "")).get("reason") if tr else None,
                    "minutes_contact_to_terminal": (tt-ct).total_seconds()/60.0,
                    "required_sweep_side": required_side,
                    "same_contact_bar_compatible_detector_count": len(same_bar),
                    "same_contact_bar_candidate_upper_bound": bool(same_bar),
                    "later_compatible_detector_count_before_terminal": len(later),
                })

        # B. Sweep accepted but current scenario never accepts CHOCH.
        if accepted_sweeps and not evs.get("SCENARIO_CHOCH_ACCEPTED", []):
            sw = accepted_sweeps[0]
            st = row_time(sw)
            tr = terminal_row(evs)
            tt = row_time(tr) if tr else None
            if st is None or tt is None or tt < st:
                continue

            struct = rows_between(
                structure_rows, st, tt,
                event_names={"STRUCTURE_INITIAL_BOS","STRUCTURE_BOS","STRUCTURE_PROTECTED_BREAK"},
            )
            waves = rows_between(wave_rows, st, tt)

            def struct_count(tf: str, event: str, same_dir: bool = True) -> int:
                return sum(
                    1 for r in struct
                    if r.get("timeframe") == tf
                    and r.get("event") == event
                    and (not same_dir or structure_direction(r) == direction)
                )

            same_dir_m1_any = [
                r for r in struct
                if r.get("timeframe") == "M1"
                and structure_direction(r) == direction
            ]
            same_dir_m5_any = [
                r for r in struct
                if r.get("timeframe") == "M5"
                and structure_direction(r) == direction
            ]

            def earliest(rows2):
                vals = [(row_time(r), r) for r in rows2 if row_time(r) is not None]
                if not vals:
                    return None, None
                vals.sort(key=lambda x:x[0])
                t,r = vals[0]
                return t, r

            m1t, m1r = earliest(same_dir_m1_any)
            m5t, m5r = earliest(same_dir_m5_any)

            sweep_no_choch_queue.append({
                "year": year,
                "scenario_id": sid,
                "direction": direction,
                "sweep_at": sw.get("observed_at"),
                "sweep_bar_open": kv(sw.get("detail", "")).get("sweep_bar_open"),
                "terminal_at": tr.get("observed_at") if tr else None,
                "terminal_event": tr.get("event") if tr else None,
                "terminal_reason": kv(tr.get("detail", "")).get("reason") if tr else None,
                "minutes_sweep_to_terminal": (tt-st).total_seconds()/60.0,
                "m1_initial_bos_same_dir": struct_count("M1","STRUCTURE_INITIAL_BOS"),
                "m1_bos_same_dir": struct_count("M1","STRUCTURE_BOS"),
                "m1_protected_break_same_dir": struct_count("M1","STRUCTURE_PROTECTED_BREAK"),
                "m1_any_same_dir_structure": len(same_dir_m1_any),
                "m1_first_same_dir_event": m1r.get("event") if m1r else None,
                "m1_first_same_dir_at": m1r.get("available_at") if m1r else None,
                "m1_first_same_dir_latency_min": (m1t-st).total_seconds()/60.0 if m1t else None,
                "m5_initial_bos_same_dir": struct_count("M5","STRUCTURE_INITIAL_BOS"),
                "m5_bos_same_dir": struct_count("M5","STRUCTURE_BOS"),
                "m5_protected_break_same_dir": struct_count("M5","STRUCTURE_PROTECTED_BREAK"),
                "m5_any_same_dir_structure": len(same_dir_m5_any),
                "m5_first_same_dir_event": m5r.get("event") if m5r else None,
                "m5_first_same_dir_at": m5r.get("available_at") if m5r else None,
                "m5_first_same_dir_latency_min": (m5t-st).total_seconds()/60.0 if m5t else None,
                "m1_wave_confirmed_count": sum(r.get("timeframe")=="M1" for r in waves),
                "m5_wave_confirmed_count": sum(r.get("timeframe")=="M5" for r in waves),
            })

    # Wave detector confirmation-delay description; not a trading result.
    wave_latency = {"M1": [], "M5": []}
    for r in wave_rows:
        x = wave_latency_minutes(r)
        if x is not None and x >= 0:
            wave_latency[r.get("timeframe")].append(x)

    contact_durations = [
        float(x["minutes_contact_to_terminal"]) for x in contact_queue
        if x["minutes_contact_to_terminal"] is not None
    ]
    sweep_durations = [
        float(x["minutes_sweep_to_terminal"]) for x in sweep_no_choch_queue
        if x["minutes_sweep_to_terminal"] is not None
    ]

    summary = {
        "year": year,
        "parity": "PASS",
        "funnel": {ev: counts[ev] for ev in BENCHMARKS[year]},
        "full_audit_detector_counts": {
            "M1_SWEEP_DETECTED": counts["M1_SWEEP_DETECTED"],
            "M1_WAVE_CONFIRMED": sum(
                r.get("event")=="WAVE_CONFIRMED" and r.get("timeframe")=="M1"
                for r in rows
            ),
            "M5_WAVE_CONFIRMED": sum(
                r.get("event")=="WAVE_CONFIRMED" and r.get("timeframe")=="M5"
                for r in rows
            ),
            "M1_STRUCTURE_INITIAL_BOS": sum(
                r.get("event")=="STRUCTURE_INITIAL_BOS" and r.get("timeframe")=="M1"
                for r in rows
            ),
            "M1_STRUCTURE_BOS": sum(
                r.get("event")=="STRUCTURE_BOS" and r.get("timeframe")=="M1"
                for r in rows
            ),
            "M1_STRUCTURE_PROTECTED_BREAK": sum(
                r.get("event")=="STRUCTURE_PROTECTED_BREAK" and r.get("timeframe")=="M1"
                for r in rows
            ),
            "M5_STRUCTURE_INITIAL_BOS": sum(
                r.get("event")=="STRUCTURE_INITIAL_BOS" and r.get("timeframe")=="M5"
                for r in rows
            ),
            "M5_STRUCTURE_BOS": sum(
                r.get("event")=="STRUCTURE_BOS" and r.get("timeframe")=="M5"
                for r in rows
            ),
            "M5_STRUCTURE_PROTECTED_BREAK": sum(
                r.get("event")=="STRUCTURE_PROTECTED_BREAK" and r.get("timeframe")=="M5"
                for r in rows
            ),
        },
        "contact_without_accepted_sweep": {
            "n": len(contact_queue),
            "same_contact_bar_compatible_sweep_detector_n": sum(
                bool(x["same_contact_bar_candidate_upper_bound"])
                for x in contact_queue
            ),
            "any_later_compatible_detector_before_terminal_n": sum(
                int(x["later_compatible_detector_count_before_terminal"]) > 0
                for x in contact_queue
            ),
            "contact_to_terminal_minutes": quantiles(contact_durations),
        },
        "sweep_without_current_choch": {
            "n": len(sweep_no_choch_queue),
            "m1_initial_bos_same_dir_n": sum(
                int(x["m1_initial_bos_same_dir"]) > 0
                for x in sweep_no_choch_queue
            ),
            "m1_bos_same_dir_n": sum(
                int(x["m1_bos_same_dir"]) > 0
                for x in sweep_no_choch_queue
            ),
            "m1_protected_break_same_dir_n": sum(
                int(x["m1_protected_break_same_dir"]) > 0
                for x in sweep_no_choch_queue
            ),
            "m1_any_same_dir_structure_n": sum(
                int(x["m1_any_same_dir_structure"]) > 0
                for x in sweep_no_choch_queue
            ),
            "m5_any_same_dir_structure_n": sum(
                int(x["m5_any_same_dir_structure"]) > 0
                for x in sweep_no_choch_queue
            ),
            "either_m1_or_m5_same_dir_structure_n": sum(
                int(x["m1_any_same_dir_structure"]) > 0
                or int(x["m5_any_same_dir_structure"]) > 0
                for x in sweep_no_choch_queue
            ),
            "sweep_to_terminal_minutes": quantiles(sweep_durations),
        },
        "wave_confirmation_latency_minutes": {
            tf: quantiles(vals) for tf, vals in wave_latency.items()
        },
    }
    return summary, contact_queue, sweep_no_choch_queue


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def run_year(year: int) -> Path:
    runner.FIXED_SYMBOLS = (SYMBOL,)
    runner.FIXED_FROM_DATE = f"{year}.01.01"
    runner.FIXED_TO_DATE = f"{year}.12.31"
    raw = runner.run_fixed_2025_batch(
        f"D155_GOLD_{year}_FULL_AUDIT",
        [CASE],
        symbols=(SYMBOL,),
        dry_run=False,
    )
    if raw is None:
        raise BatchError(f"{year}: generic runner returned no ZIP")
    return Path(raw)


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("ERROR: run this on the Windows MT5 machine.")

    repo = Path(__file__).resolve().parents[1]
    head = git_head(repo)
    if head != EXPECTED_GIT_HEAD:
        raise SystemExit(
            f"ERROR: fail-closed expected Git HEAD {EXPECTED_GIT_HEAD}, got {head}"
        )

    print("D155 mentor-fidelity opportunity audit")
    print("Strategy semantics: unchanged")
    print("Audit mode: FULL_AUDIT logging only")
    print("Years: 2024, 2025 / GOLD#")
    print()

    results = []
    contact_rows = []
    no_choch_rows = []
    raw_zips = {}

    for year in (2024, 2025):
        print(f"[{year}] running FULL_AUDIT...")
        raw = run_year(year)
        raw_zips[year] = raw
        rows = load_gold_csv(raw)
        summary, cq, nq = analyze_year(year, rows)
        results.append(summary)
        contact_rows.extend(cq)
        no_choch_rows.extend(nq)
        print(
            f"[{year}] parity PASS | contact-no-sweep={len(cq)} "
            f"| sweep-no-current-CHOCH={len(nq)}"
        )

    work = Path(tempfile.mkdtemp(prefix="D155_fidelity_"))
    try:
        (work / "D155_OPPORTUNITY_SUMMARY.json").write_text(
            json.dumps(results, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        write_csv(work / "D155_CONTACT_NO_SWEEP_QUEUE.csv", contact_rows)
        write_csv(work / "D155_SWEEP_NO_CURRENT_CHOCH_QUEUE.csv", no_choch_rows)

        for year, raw in raw_zips.items():
            shutil.copy2(raw, work / f"RAW_GOLD_{year}_FULL_AUDIT.zip")

        lines = [
            "# D155 Mentor Fidelity / Opportunity Frequency Audit",
            "",
            "Strategy was not modified. FULL_AUDIT must reproduce the known compact-log counts exactly.",
            "",
        ]
        for s in results:
            c = s["contact_without_accepted_sweep"]
            q = s["sweep_without_current_choch"]
            lines += [
                f"## {s['year']}",
                "",
                f"- contact without accepted sweep: {c['n']}",
                f"- same-contact-bar compatible sweep-detector upper bound: {c['same_contact_bar_compatible_sweep_detector_n']}",
                f"- sweep without current CHOCH: {q['n']}",
                f"- of those, M1 INITIAL_BOS same direction: {q['m1_initial_bos_same_dir_n']}",
                f"- M1 BOS same direction: {q['m1_bos_same_dir_n']}",
                f"- any M1 same-direction structure event: {q['m1_any_same_dir_structure_n']}",
                f"- any M5 same-direction structure event: {q['m5_any_same_dir_structure_n']}",
                f"- either M1 or M5 same-direction structure event: {q['either_m1_or_m5_same_dir_structure_n']}",
                "",
            ]

        lines += [
            "Interpretation must remain source-first.",
            "These counts are opportunity diagnostics, not alternative trigger authorization.",
            "Upload this ZIP for the D155 Stage-A interpretation.",
        ]
        (work / "README_RESULTS.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )

        out = runner.get_desktop_dir() / "D155_MENTOR_FIDELITY_OPPORTUNITY_AUDIT_RESULT.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for p in work.iterdir():
                z.write(p, p.name)

        print()
        print("\n".join(lines))
        print("Result ZIP:", out)
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    try:
        main()
    except BatchError as e:
        raise SystemExit("ERROR: " + str(e))
