from __future__ import annotations

import csv
import io
import json
import math
import os
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

EXPECTED_GIT_HEAD = "0b317facba97f4edc305d0d4c82fbe5bd10a9739"
FREEZE_PATH = Path(__file__).with_name("..").resolve() / "config" / "d154o_stage_b_freeze.json"

BASE_SETTINGS = {
    "InpExitManagementMode": 9,   # V1_EXIT_SMART_PARTIAL_V3_BANK_2R_LOCK_ONE
    "InpEpisodeManagementMode": 0,  # EM OFF
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
}

CASE = TestCase(
    "D154O_STAGE_B_KM_ON",
    BASE_SETTINGS,
    "Frozen D154O Stage-B 2025 confirmation: V3E mode 9, EM OFF, D151/K/M ON",
)

def kv(detail: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in re.finditer(r"(\w+)=([^ ]+)", detail or "")}

def med(vals):
    vals = [v for v in vals if v is not None and math.isfinite(v)]
    return statistics.median(vals) if vals else None

def as_float(d: dict[str, str], key: str):
    try:
        v = float(d[key])
        return v if math.isfinite(v) else None
    except Exception:
        return None

def git_head(repo: Path) -> str:
    cp = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                        capture_output=True, text=True, check=False)
    if cp.returncode != 0:
        raise BatchError("Could not read Git HEAD: " + (cp.stderr or cp.stdout))
    return cp.stdout.strip()

def load_freeze(repo: Path) -> dict[str, Any]:
    path = repo / "config" / "d154o_stage_b_freeze.json"
    if not path.exists():
        raise BatchError(f"Freeze manifest missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    syms = data.get("all_stage_b_symbols", [])
    expected = [
        "GOLD#","XAUJPY#","XAUCNH#","BTCUSD#","XAUEUR#","GAUCNH#","GAUUSD#","USDJPY#",
        "GBPUSD#","SILVER#","EURUSD#","ETHUSD#"
    ]
    if syms != expected:
        raise BatchError(f"Frozen Stage-B symbol list mismatch: {syms}")
    if data.get("selection_time_status") != "FROZEN_BEFORE_NEW_2025_OUTCOMES":
        raise BatchError("Freeze manifest is not marked outcome-blind/frozen.")
    return data

def rows_from_zip(zp: Path) -> dict[str, list[dict[str, str]]]:
    out = {}
    with zipfile.ZipFile(zp) as z:
        for name in z.namelist():
            if name.endswith(".csv"):
                out[name] = list(csv.DictReader(io.StringIO(
                    z.read(name).decode("utf-8-sig", errors="replace")
                )))
    return out

def analyze_symbol(rows: list[dict[str, str]], symbol: str, cohort: str) -> dict[str, Any]:
    events = [r.get("event", "") for r in rows]
    if events.count("EA_START") != 1 or events.count("EA_STOP") != 1:
        raise BatchError(f"{symbol}: EA_START/EA_STOP integrity failure")
    bad = [
        "EXECUTION_DIVERGENCE", "PENDING_CANCEL_REJECTED",
        "D154K_INTEGRITY_WARNING", "D154M_INTEGRITY_WARNING"
    ]
    present = [x for x in bad if x in events]
    if present:
        raise BatchError(f"{symbol}: integrity failure events={present}")

    fills: dict[str, dict[str, str]] = {}
    ksnaps: dict[str, dict[str, str]] = {}
    pairs: dict[str, dict[str, str]] = {}
    closes: dict[str, dict[str, str]] = {}
    partial_sids: set[str] = set()

    for r in rows:
        ev = r.get("event", "")
        d = kv(r.get("detail", ""))
        sid = d.get("scenario_id", r.get("object_id", ""))
        if not sid:
            continue
        if ev == "D151_FILL_SNAPSHOT":
            fills[sid] = d
        elif ev == "D154K_CROSS_SCALE_SNAPSHOT":
            ksnaps[sid] = d
        elif ev == "D154M_PAIR_OUTCOME":
            pairs[sid] = d
        elif ev == "POSITION_CLOSED":
            closes[sid] = d
        elif ev in ("D149_SP_PARTIAL_ACCEPTED", "D149_SP_V2_CLOSE_ACCEPTED"):
            partial_sids.add(sid)

    if not fills:
        return {
            "symbol": symbol, "cohort": cohort, "fills": 0,
            "status": "INSUFFICIENT_STRATEGY_SAMPLE",
            "integrity": "PASS_NO_FILLS",
        }

    if len(ksnaps) != len(fills) or len(pairs) != len(fills):
        raise BatchError(
            f"{symbol}: D151/K/M completeness mismatch fills={len(fills)} "
            f"K={len(ksnaps)} M={len(pairs)}"
        )

    impossible = sum(
        p.get("pair_class") == "ACTUAL_PLUS_1R_TO_SHADOW_SL"
        for p in pairs.values()
    )
    if impossible:
        raise BatchError(f"{symbol}: impossible D154M pair count={impossible}")

    def outcome_counts(items):
        plus = sum(x.get("actual_outcome") == "PLUS_1R" for x in items)
        sl = sum(x.get("actual_outcome") == "SL_FIRST" for x in items)
        cens = sum(x.get("actual_outcome") == "RIGHT_CENSORED" for x in items)
        return plus, sl, cens

    pair_items = list(pairs.values())
    plus, sl, cens = outcome_counts(pair_items)
    resolved = plus + sl
    actual_survival = plus / resolved if resolved else None

    shadow_plus = sum(x.get("shadow_outcome") == "PLUS_1R" for x in pair_items)
    shadow_sl = sum(x.get("shadow_outcome") == "SL_FIRST" for x in pair_items)
    shadow_cens = sum(x.get("shadow_outcome") == "RIGHT_CENSORED" for x in pair_items)
    shadow_resolved = shadow_plus + shadow_sl
    shadow_survival = shadow_plus / shadow_resolved if shadow_resolved else None
    flips = sum(x.get("pair_class") == "ACTUAL_SL_TO_SHADOW_PLUS_1R" for x in pair_items)

    dirs = {}
    for sid, d in fills.items():
        dirs[sid] = d.get("direction", "UNKNOWN")

    dir_stats = {}
    for direction in ("LONG", "SHORT"):
        sids = [sid for sid, dr in dirs.items() if dr == direction and sid in pairs]
        vals = [pairs[sid] for sid in sids]
        p, l, c = outcome_counts(vals)
        rr = p + l
        dir_stats[direction] = {
            "fills": len(sids), "plus1": p, "sl_first": l, "censored": c,
            "survival": (p / rr if rr else None),
        }

    def nums(key):
        return [as_float(d, key) for d in ksnaps.values()]

    # Exact trade-level V3E aggregate net R cannot be reconstructed from POSITION_CLOSED
    # alone when a +1R partial close happened. Do not manufacture precision.
    exact_trade_r = []
    if not partial_sids:
        for sid, d in closes.items():
            risk = as_float(d, "actual_fill_risk_money")
            net = as_float(d, "realized_net_money")
            if risk and risk > 0 and net is not None:
                exact_trade_r.append(net / risk)
        perf_status = "EXACT_FROM_POSITION_CLOSED_NO_PARTIALS"
    else:
        perf_status = "REQUIRES_COMPLETE_DEAL_LEDGER_DUE_TO_V3E_PARTIALS"

    winners = [r for r in exact_trade_r if r > 0]
    losses = [r for r in exact_trade_r if r <= 0]

    n = len(fills)
    # Descriptive sample flag only; not a promotion threshold.
    sample_status = "INSUFFICIENT_STRATEGY_SAMPLE" if n < 20 else "ANALYZABLE_SAMPLE"

    return {
        "symbol": symbol,
        "cohort": cohort,
        "status": sample_status,
        "integrity": "PASS",
        "fills": n,
        "plus1": plus,
        "sl_first": sl,
        "right_censored": cens,
        "entry_survival": actual_survival,
        "long_fills": dir_stats["LONG"]["fills"],
        "long_survival": dir_stats["LONG"]["survival"],
        "short_fills": dir_stats["SHORT"]["fills"],
        "short_survival": dir_stats["SHORT"]["survival"],
        "median_spread_over_reaction_tr": med(nums("spread_over_reaction_tr")),
        "median_spread_over_risk": med(nums("spread_over_risk")),
        "median_spread_over_selected_fvg": med(nums("spread_over_fvg")),
        "median_risk_over_reaction_tr": med(nums("risk_over_reaction_tr")),
        "median_fvg_over_reaction_tr": med(nums("fvg_over_reaction_tr")),
        "shadow_plus1": shadow_plus,
        "shadow_sl_first": shadow_sl,
        "shadow_right_censored": shadow_cens,
        "shadow_survival": shadow_survival,
        "sl_to_shadow_plus1": flips,
        "sl_to_shadow_plus1_rate_of_actual_sl": (flips / sl if sl else None),
        "position_closed_count": len(closes),
        "v3e_partial_scenario_count": len(partial_sids),
        "v3e_exact_performance_status": perf_status,
        "v3e_exact_trade_count": len(exact_trade_r),
        "v3e_realized_wr": (len(winners) / len(exact_trade_r) if exact_trade_r else None),
        "v3e_average_winner_r": (statistics.mean(winners) if winners else None),
        "v3e_expectancy_r": (statistics.mean(exact_trade_r) if exact_trade_r else None),
    }

def write_csv(path: Path, rows: list[dict[str, Any]]):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

def main():
    repo = Path(__file__).resolve().parents[1]
    head = git_head(repo)
    if head != EXPECTED_GIT_HEAD:
        raise BatchError(
            f"Fail-closed: expected Git HEAD {EXPECTED_GIT_HEAD}, got {head}. "
            "Pull/reconcile GitHub and regenerate the Stage-B package rather than running on an unknown base."
        )

    freeze = load_freeze(repo)
    symbols = tuple(freeze["all_stage_b_symbols"])
    cohorts = {freeze["reference"]: "REFERENCE"}
    cohorts.update({s: "GOLD_LIKE" for s in freeze["gold_like_candidates"]})
    cohorts.update({s: "NEGATIVE_CONTROL" for s in freeze["negative_controls"]})

    # Existing generic runner is proven infrastructure; expand its fixed symbol whitelist
    # only inside this Stage-B process.
    runner.FIXED_SYMBOLS = symbols
    runner.FIXED_FROM_DATE = "2025.01.01"
    runner.FIXED_TO_DATE = "2025.12.31"

    raw_zip = runner.run_fixed_2025_batch(
        "D154O_STAGE_B_2025",
        [CASE],
        symbols=symbols,
        dry_run=False,
    )
    if raw_zip is None:
        raise BatchError("Stage-B runner returned no result ZIP.")
    raw_zip = Path(raw_zip)

    files = rows_from_zip(raw_zip)
    summaries = []
    for symbol in symbols:
        matches = [
            rows for name, rows in files.items()
            if "__D154O_STAGE_B_KM_ON__" + symbol + "__2025.csv" in name
        ]
        if len(matches) != 1:
            raise BatchError(f"{symbol}: result CSV discovery failed count={len(matches)}")
        s = analyze_symbol(matches[0], symbol, cohorts[symbol])
        summaries.append(s)
        surv = s.get("entry_survival")
        surv_txt = "NA" if surv is None else f"{100*surv:.1f}%"
        print(
            f"{symbol:10s} {cohorts[symbol]:16s} fills={s.get('fills',0):4d} "
            f"survival={surv_txt:>7s} status={s.get('status')}"
        )

    work = Path(tempfile.mkdtemp(prefix="D154O_STAGE_B_summary_"))
    try:
        write_csv(work / "D154O_STAGE_B_2025_SUMMARY.csv", summaries)
        (work / "D154O_STAGE_B_2025_SUMMARY.json").write_text(
            json.dumps(summaries, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (work / "D154O_STAGE_B_FREEZE.json").write_text(
            json.dumps(freeze, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        readme = """D154O Stage B 2025 result package

Primary evidence:
- Fill -> +1R actual executable-side survival
- LONG/SHORT survival
- exact D154K execution geometry
- D154M entry-side quote counterfactual and flip incidence

The symbol cohorts were frozen from Stage-A outcome-blind raw metrics before
new 2025 outcomes were generated. Do not add/drop symbols after this run.

V3E strategy-level caveat:
Mode 9 can realize a partial close at +1R. POSITION_CLOSED alone does not contain
the full partial-deal P/L ledger. Therefore this summarizer reports exact V3E
WR/average-winner/expectancy only when no partial close occurred. Otherwise it
marks REQUIRES_COMPLETE_DEAL_LEDGER_DUE_TO_V3E_PARTIALS rather than fabricating
a cost-adjusted aggregate result. This does not affect the primary D154O
Entry-survival/D154K/D154M test.

Upload this final ZIP to ChatGPT for interpretation.
"""
        (work / "README.txt").write_text(readme, encoding="utf-8")
        shutil.copy2(raw_zip, work / "RAW_MT5_BATCH.zip")

        out = runner.get_desktop_dir() / "D154O_STAGE_B_2025_RESULT.zip"
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for p in work.iterdir():
                z.write(p, p.name)
        print("\nD154O Stage B complete.")
        print("Result ZIP:", out)
    finally:
        shutil.rmtree(work, ignore_errors=True)

if __name__ == "__main__":
    try:
        main()
    except BatchError as e:
        raise SystemExit("ERROR: " + str(e))
