from __future__ import annotations

import csv
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
from pathlib import Path
from typing import Any

import mt5_batch_runner as runner
from mt5_batch_runner import BatchError, TestCase

EXPECTED_GIT_HEAD = "0e7b1d5b39de1126394e88f85abf87cde167fc84"
SYMBOLS = ("GOLD#", "BTCUSD#", "XAUEUR#", "USDJPY#")

CASE = TestCase(
    "D154P_R2_2024",
    {
        "InpExitManagementMode": 9,
        "InpEpisodeManagementMode": 0,
        "InpV2D151CausalAudit": True,
        "InpV2D154EntrySurvivalAudit": False,
        "InpV2D154BConfirmationAudit": False,
        "InpV2D154CReaccelerationFvgAudit": False,
        "InpV2D154FCausalLineageAudit": False,
        "InpV2D154GHTFRootLineageAudit": False,
        "InpV2D154HHTFNestedReplayAudit": False,
        "InpV2D154JHTFDeliveryGeometryAudit": False,
        "InpV2D154KCrossScaleReactionAudit": True,
        "InpV2D154MExecutionFrictionCounterfactualAudit": True,
    },
    "D154P R2 frozen 2025 hypotheses -> untouched 2024 validation",
)


def kv(s: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in re.finditer(r"(\w+)=([^ ]+)", s or "")}


def num(d: dict[str, str], key: str) -> float | None:
    try:
        x = float(d[key])
        return x if math.isfinite(x) else None
    except Exception:
        return None


def dt_hour(s: str) -> int | None:
    m = re.match(r"\d{4}\.\d{2}\.\d{2} (\d{2}):", s or "")
    return int(m.group(1)) if m else None


def git_head(repo: Path) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False
    )
    if cp.returncode != 0:
        raise BatchError("Could not read Git HEAD.")
    return cp.stdout.strip()


def read_batch(zp: Path) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = {}
    with zipfile.ZipFile(zp) as z:
        for name in z.namelist():
            if not name.endswith(".csv"):
                continue
            for s in SYMBOLS:
                # Generic runner's filename suffix remains __2025.csv even when date
                # constants are overridden to 2024. Manifest/INI are authoritative.
                if f"__{s}__2025.csv" in name:
                    out[s] = list(csv.DictReader(io.StringIO(
                        z.read(name).decode("utf-8-sig", errors="replace")
                    )))
    return out


def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
    plus = sum(x["outcome"] == "PLUS_1R" for x in items)
    sl = sum(x["outcome"] == "SL_FIRST" for x in items)
    cens = sum(x["outcome"] == "RIGHT_CENSORED" for x in items)
    closed = [x for x in items if x["net_r"] is not None]
    wins = [x["net_r"] for x in closed if x["net_r"] > 0]
    losses = [x["net_r"] for x in closed if x["net_r"] <= 0]
    return {
        "fills": len(items),
        "plus1": plus,
        "sl_first": sl,
        "right_censored": cens,
        "survival": plus / (plus + sl) if plus + sl else None,
        "closed": len(closed),
        "realized_wins": len(wins),
        "realized_wr": len(wins) / len(closed) if closed else None,
        "net_r": sum(x["net_r"] for x in closed) if closed else None,
        "expectancy_r": statistics.mean(x["net_r"] for x in closed) if closed else None,
        "avg_winner_r": statistics.mean(wins) if wins else None,
        "avg_loser_r": statistics.mean(losses) if losses else None,
        "profit_factor": (
            sum(wins) / -sum(losses)
            if wins and losses and sum(losses) < 0 else None
        ),
    }


def build(symbol: str, rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    events = [r.get("event", "") for r in rows]
    if events.count("EA_START") != 1 or events.count("EA_STOP") != 1:
        raise BatchError(f"{symbol}: EA_START/EA_STOP integrity failure")

    start = next(r for r in rows if r.get("event") == "EA_START")
    if start.get("observed_at") != "2024.01.01 00:00:00":
        raise BatchError(
            f"{symbol}: requested 2024 full year but actual EA_START="
            f"{start.get('observed_at')}"
        )

    bad = [
        e for e in (
            "EXECUTION_DIVERGENCE",
            "PENDING_CANCEL_REJECTED",
            "D154K_INTEGRITY_WARNING",
            "D154M_INTEGRITY_WARNING",
        ) if e in events
    ]
    if bad:
        raise BatchError(f"{symbol}: integrity failure {bad}")

    by: dict[str, dict[str, tuple[dict[str, str], dict[str, str]]]] = {}
    for r in rows:
        d = kv(r.get("detail", ""))
        sid = d.get("scenario_id")
        if r.get("event") == "SCENARIO_PLANNED":
            sid = r.get("object_id", "")
        if not sid:
            continue
        by.setdefault(sid, {})
        by[sid].setdefault(r.get("event", ""), (r, d))

    out: list[dict[str, Any]] = []
    for sid, e in by.items():
        if "D151_FILL_SNAPSHOT" not in e:
            continue

        required = (
            "SCENARIO_PLANNED",
            "SCENARIO_FVG_SELECTED",
            "D151_FILL_SNAPSHOT",
            "D154K_CROSS_SCALE_SNAPSHOT",
            "D154M_PAIR_OUTCOME",
        )
        missing = [x for x in required if x not in e]
        if missing:
            raise BatchError(f"{symbol}: {sid} missing {missing}")

        plan_r, plan = e["SCENARIO_PLANNED"]
        fvg_r, fvg = e["SCENARIO_FVG_SELECTED"]
        fill_r, fill = e["D151_FILL_SNAPSHOT"]
        k_r, k = e["D154K_CROSS_SCALE_SNAPSHOT"]
        m_r, m = e["D154M_PAIR_OUTCOME"]

        direction = fill.get("direction")
        root_lo = num(plan, "source_bottom")
        root_hi = num(plan, "source_top")
        entry = num(k, "planned_entry")
        fvg_lo = num(fvg, "bottom")
        fvg_hi = num(fvg, "top")

        if None in (root_lo, root_hi, entry, fvg_lo, fvg_hi):
            raise BatchError(f"{symbol}: missing geometry {sid}")
        W = root_hi - root_lo
        if W <= 0:
            raise BatchError(f"{symbol}: invalid Root width {sid}")

        if direction == "LONG":
            g = (entry - root_hi) / W
        elif direction == "SHORT":
            g = (root_lo - entry) / W
        else:
            raise BatchError(f"{symbol}: invalid direction {direction}")

        interval_gap = max(0.0, max(root_lo, fvg_lo) - min(root_hi, fvg_hi))
        root_near = interval_gap <= W + 1e-12
        escape = (g > 0.0 and g <= 0.5 + 1e-12)

        hour = dt_hour(fill_r.get("observed_at", ""))
        session = hour in (13, 14)

        close = e.get("D151_ACTUAL_CLOSE")
        net_r = num(close[1], "actual_net_r") if close else None

        item = {
            "symbol": symbol,
            "scenario_id": sid,
            "direction": direction,
            "fill_time": fill_r.get("observed_at"),
            "fill_hour": hour,
            "outcome": m.get("actual_outcome"),
            "net_r": net_r,
            "root_width": W,
            "entry_root_escape_w": g,
            "H_ESCAPE": escape,
            "root_fvg_interval_gap_w": interval_gap / W,
            "H_ROOT_NEAR": root_near,
            "H_SESSION": session,
            "reaction_range_over_tr": num(k, "reaction_range_over_tr"),
            "contact_to_sweep_s": num(fill, "contact_to_sweep_s"),
            "structural_tp_r": num(fill, "structural_tp_r"),
            "H_ROOM_3R": (
                num(fill, "structural_tp_r") is not None
                and num(fill, "structural_tp_r") >= 3.0
            ),
        }
        out.append(item)

    n = len(out)
    if not (
        events.count("D151_FILL_SNAPSHOT")
        == events.count("D154K_CROSS_SCALE_SNAPSHOT")
        == events.count("D154M_PAIR_OUTCOME")
        == n
    ):
        raise BatchError(f"{symbol}: D151/K/M population mismatch")

    return out


def pct(x: float | None) -> str:
    return "NA" if x is None else f"{100*x:.1f}%"


def r3(x: float | None) -> str:
    return "NA" if x is None else f"{x:.3f}R"


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("ERROR: run on Windows MT5 machine")

    repo = Path(__file__).resolve().parents[1]
    head = git_head(repo)
    if head != EXPECTED_GIT_HEAD:
        raise SystemExit(
            f"ERROR: expected Git HEAD {EXPECTED_GIT_HEAD}, got {head}"
        )

    runner.FIXED_SYMBOLS = SYMBOLS
    runner.FIXED_FROM_DATE = "2024.01.01"
    runner.FIXED_TO_DATE = "2024.12.31"

    raw = runner.run_fixed_2025_batch(
        "D154P_R2_2024_VALIDATION",
        [CASE],
        symbols=SYMBOLS,
        dry_run=False,
    )
    if raw is None:
        raise SystemExit("ERROR: no batch ZIP")
    raw = Path(raw)

    rows = read_batch(raw)
    if set(rows) != set(SYMBOLS):
        raise SystemExit(f"ERROR: missing symbols {set(SYMBOLS)-set(rows)}")

    all_items: list[dict[str, Any]] = []
    for s in SYMBOLS:
        all_items.extend(build(s, rows[s]))

    report: dict[str, Any] = {
        "phase": "D154P_R2_2024_VALIDATION",
        "git_head": head,
        "period": "2024-01-01..2024-12-31",
        "strategy_changed": False,
        "frozen_hypotheses": {
            "H_ESCAPE": "0 < directional planned-entry Root gap / Root width <= 0.5",
            "H_SESSION": "actual Fill broker/server hour in {13,14}; descriptive execution-time regime",
            "H_ROOT_NEAR": "Root/FVG interval gap <= one Root width; secondary",
            "H_COMPACT": "reaction_range_over_tr continuous only; no cutoff",
            "H_ROOM_3R": "structural_tp_r >= 3.0; payoff axis",
        },
        "overall": summarize(all_items),
        "by_symbol": {},
    }

    for s in SYMBOLS:
        ss = [x for x in all_items if x["symbol"] == s]
        report["by_symbol"][s] = {
            "all": summarize(ss),
            "H_ESCAPE": summarize([x for x in ss if x["H_ESCAPE"]]),
            "NOT_H_ESCAPE": summarize([x for x in ss if not x["H_ESCAPE"]]),
            "H_SESSION": summarize([x for x in ss if x["H_SESSION"]]),
            "NOT_H_SESSION": summarize([x for x in ss if not x["H_SESSION"]]),
        }

    for h in ("H_ESCAPE", "H_SESSION", "H_ROOT_NEAR", "H_ROOM_3R"):
        report[h] = {
            "inside": summarize([x for x in all_items if x[h]]),
            "outside": summarize([x for x in all_items if not x[h]]),
            "by_direction": {
                d: {
                    "inside": summarize([x for x in all_items if x["direction"] == d and x[h]]),
                    "outside": summarize([x for x in all_items if x["direction"] == d and not x[h]]),
                } for d in ("LONG", "SHORT")
            },
        }

    report["H_ESCAPE_OR_SESSION"] = summarize([
        x for x in all_items if x["H_ESCAPE"] or x["H_SESSION"]
    ])
    report["H_ESCAPE_AND_SESSION"] = summarize([
        x for x in all_items if x["H_ESCAPE"] and x["H_SESSION"]
    ])

    # Continuous descriptors: medians by outcome, never optimized into a cutoff.
    for feat in ("reaction_range_over_tr", "contact_to_sweep_s"):
        report[feat] = {}
        for s in ("ALL",) + SYMBOLS:
            ss = all_items if s == "ALL" else [x for x in all_items if x["symbol"] == s]
            plus = [x[feat] for x in ss if x["outcome"] == "PLUS_1R" and x[feat] is not None]
            sl = [x[feat] for x in ss if x["outcome"] == "SL_FIRST" and x[feat] is not None]
            report[feat][s] = {
                "plus1_n": len(plus),
                "sl_n": len(sl),
                "plus1_median": statistics.median(plus) if plus else None,
                "sl_median": statistics.median(sl) if sl else None,
            }

    gold_all = [x for x in all_items if x["symbol"] == "GOLD#"]
    nongold_escape = [
        x for x in all_items
        if x["symbol"] != "GOLD#" and x["H_ESCAPE"]
    ]
    nongold_union = [
        x for x in all_items
        if x["symbol"] != "GOLD#" and (x["H_ESCAPE"] or x["H_SESSION"])
    ]
    report["decision_counterfactuals"] = {
        "GOLD_ALL": summarize(gold_all),
        "NONGOLD_ESCAPE_ONLY": summarize(nongold_escape),
        "GOLD_ALL_PLUS_NONGOLD_ESCAPE": summarize(gold_all + nongold_escape),
        "GOLD_ALL_PLUS_NONGOLD_ESCAPE_OR_SESSION": summarize(gold_all + nongold_union),
    }

    work = Path(tempfile.mkdtemp(prefix="D154P_R2_2024_"))
    try:
        (work / "D154P_R2_2024_VALIDATION.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        fields = [
            "symbol","scenario_id","direction","fill_time","fill_hour",
            "outcome","net_r","root_width","entry_root_escape_w","H_ESCAPE",
            "root_fvg_interval_gap_w","H_ROOT_NEAR","H_SESSION",
            "reaction_range_over_tr","contact_to_sweep_s",
            "structural_tp_r","H_ROOM_3R",
        ]
        with (work / "D154P_R2_2024_SCENARIOS.csv").open(
            "w", encoding="utf-8", newline=""
        ) as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows({k:x.get(k) for k in fields} for x in all_items)

        e = report["H_ESCAPE"]
        s = report["H_SESSION"]
        lines = [
            "# D154P R2 2024 validation",
            "",
            "No 2024 threshold/window fitting was performed.",
            "",
            "## PRIMARY H-ESCAPE",
            f"inside: n={e['inside']['fills']}, survival={pct(e['inside']['survival'])}, WR={pct(e['inside']['realized_wr'])}, exp={r3(e['inside']['expectancy_r'])}, avg winner={r3(e['inside']['avg_winner_r'])}",
            f"outside: n={e['outside']['fills']}, survival={pct(e['outside']['survival'])}, WR={pct(e['outside']['realized_wr'])}, exp={r3(e['outside']['expectancy_r'])}",
            "",
            "## DESCRIPTIVE H-SESSION",
            f"inside: n={s['inside']['fills']}, survival={pct(s['inside']['survival'])}, WR={pct(s['inside']['realized_wr'])}, exp={r3(s['inside']['expectancy_r'])}",
            f"outside: n={s['outside']['fills']}, survival={pct(s['outside']['survival'])}, WR={pct(s['outside']['realized_wr'])}, exp={r3(s['outside']['expectancy_r'])}",
            "",
            "Upload this ZIP without modifying the frozen rules.",
        ]
        (work / "README_RESULTS.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
        shutil.copy2(raw, work / "RAW_MT5_2024_BATCH.zip")

        out = runner.get_desktop_dir() / "D154P_R2_2024_VALIDATION_RESULT.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for p in work.iterdir():
                z.write(p, p.name)

        print("\n".join(lines))
        print()
        print("Result ZIP:", out)
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    try:
        main()
    except BatchError as e:
        raise SystemExit("ERROR: " + str(e))
