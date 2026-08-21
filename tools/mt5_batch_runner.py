from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from dataclasses import dataclass
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Fixed research environment for the current V2 development window.
# These are intentionally centralized here so research case files only vary
# the strategy input(s) under test.
# ---------------------------------------------------------------------------

FIXED_SYMBOLS = ("GOLD", "BTCUSD")
FIXED_FROM_DATE = "2025.01.01"
FIXED_TO_DATE = "2025.12.31"
FIXED_PERIOD = "M1"
FIXED_MODEL = 4  # MT5: Every tick based on real ticks
FIXED_OPTIMIZATION = 0
FIXED_FORWARD_MODE = 0
FIXED_VISUAL = 0
FIXED_USE_CLOUD = 0
MAX_CASE_SECONDS = 8 * 60 * 60

EA_BASENAME = "MentorDeterministicV2EA"

# Values common to the current research protocol.
# Enum values are intentionally numeric and follow the source enum identities.
FIXED_EA_INPUTS: dict[str, Any] = {
    "InpMagicNumber": 26082202,
    "InpWriteEventCsv": True,
    "InpVerboseLog": False,
    "InpLogBootstrapEvents": False,
    "InpStopLossModel": 2,           # V1_SL_ROOT_OB_DISTAL_20
    "InpRegimeResearchMode": 2,      # V1_REGIME_BASELINE_NO_GATE
    "InpEventLogMode": 0,            # V1_LOG_RESEARCH_COMPACT
    "InpPositionSizingMode": 1,      # V1_SIZE_FIXED_RISK_MONEY
    "InpEpisodeManagementMode": 0,   # V1_EM_OFF unless a case explicitly overrides
    "InpFixedRiskMoneyPerTrade": 100.0,
    "InpEquityRiskPercentPerTrade": 1.0,
    "InpEnableEdgeAudit": False,
    "InpV2D151CausalAudit": True,
}

# Account-level tester settings such as Deposit/Leverage/ExecutionMode are
# deliberately NOT overwritten here. MT5 therefore reuses the terminal's
# existing tester values, while every strategy-comparison run in a batch uses
# the same terminal/session settings. If the project later freezes those
# account settings, add them explicitly in build_tester_ini().


@dataclass(frozen=True)
class TestCase:
    name: str
    overrides: dict[str, Any]
    note: str = ""


@dataclass
class MT5Context:
    terminal_exe: Path
    data_dir: Path
    expert_rel: str
    expert_ex5: Path
    template_set: Path


class BatchError(RuntimeError):
    pass


def _bool_text(v: bool) -> str:
    return "true" if v else "false"


def _value_text(v: Any) -> str:
    if isinstance(v, bool):
        return _bool_text(v)
    if isinstance(v, float):
        return f"{v:.10g}"
    return str(v)


def _decode_bytes(raw: bytes) -> tuple[str, str]:
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16"), "utf-16"
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig"), "utf-8-sig"
    if raw and raw.count(b"\x00") > len(raw) // 5:
        try:
            return raw.decode("utf-16-le"), "utf-16-le"
        except UnicodeDecodeError:
            pass
    for enc in ("utf-8", "cp949", "cp1252"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace"), "utf-8"


def read_text_detect(path: Path) -> tuple[str, str]:
    return _decode_bytes(path.read_bytes())


def write_text_detect(path: Path, text: str, encoding: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding=encoding, newline="")


def patch_set_text(template_text: str, values: dict[str, Any]) -> str:
    """
    Patch only the current value in an MT5 .set line while preserving any
    optimization metadata after ||. Fail closed if a requested input is absent.
    """
    lines = template_text.splitlines()
    found: set[str] = set()
    out: list[str] = []

    for line in lines:
        if "=" not in line or line.lstrip().startswith(";"):
            out.append(line)
            continue
        key, rhs = line.split("=", 1)
        key_stripped = key.strip()
        if key_stripped not in values:
            out.append(line)
            continue

        suffix = ""
        if "||" in rhs:
            _, rest = rhs.split("||", 1)
            suffix = "||" + rest
        out.append(f"{key}={_value_text(values[key_stripped])}{suffix}")
        found.add(key_stripped)

    missing = sorted(set(values) - found)
    if missing:
        raise BatchError(
            "Template .set does not contain required EA input(s): "
            + ", ".join(missing)
            + ". Re-select/compile the current V2 EA in Strategy Tester once so "
              "MT5 refreshes its tester preset, then rerun."
        )
    newline = "\r\n" if "\r\n" in template_text else "\n"
    return newline.join(out) + newline


def _appdata_terminal_root() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise BatchError("%APPDATA% is not available.")
    return Path(appdata) / "MetaQuotes" / "Terminal"


def _common_files_dir() -> Path:
    return _appdata_terminal_root() / "Common" / "Files"


def _candidate_data_dirs() -> list[Path]:
    override = os.environ.get("MT5_DATA_DIR")
    if override:
        p = Path(os.path.expandvars(override)).expanduser()
        if not p.exists():
            raise BatchError(f"MT5_DATA_DIR does not exist: {p}")
        return [p]

    root = _appdata_terminal_root()
    if not root.exists():
        raise BatchError(f"MetaTrader data root not found: {root}")
    return [
        p for p in root.iterdir()
        if p.is_dir() and p.name.lower() != "common"
    ]


def _find_expert_ex5(data_dir: Path) -> list[Path]:
    root = data_dir / "MQL5" / "Experts"
    if not root.exists():
        return []
    return list(root.rglob(EA_BASENAME + ".ex5"))


def _template_matches(path: Path) -> bool:
    try:
        text, _ = read_text_detect(path)
    except OSError:
        return False
    markers = (
        "InpExitManagementMode=",
        "InpEventCsvFile=",
        "InpV2D151CausalAudit=",
        "InpEpisodeManagementMode=",
    )
    return all(m in text for m in markers)


def _find_template_set(data_dir: Path) -> list[Path]:
    tester = data_dir / "MQL5" / "Profiles" / "Tester"
    if not tester.exists():
        return []
    exact = tester / (EA_BASENAME + ".set")
    candidates: list[Path] = []
    if exact.exists() and _template_matches(exact):
        candidates.append(exact)
    for p in tester.glob("*.set"):
        if p == exact:
            continue
        if _template_matches(p):
            candidates.append(p)
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates


def _origin_install_path(data_dir: Path) -> Path | None:
    origin = data_dir / "origin.txt"
    if not origin.exists():
        return None
    try:
        text, _ = read_text_detect(origin)
    except OSError:
        return None

    for raw in text.splitlines():
        s = raw.strip().strip('"')
        if not s:
            continue
        p = Path(os.path.expandvars(s))
        if p.is_file() and p.name.lower() == "terminal64.exe":
            return p
        if p.is_dir() and (p / "terminal64.exe").exists():
            return p / "terminal64.exe"
    # Some origin files contain an install path without clean line boundaries.
    m = re.search(r"([A-Za-z]:\\[^\r\n]+)", text)
    if m:
        p = Path(m.group(1).strip().strip('"'))
        if p.is_dir() and (p / "terminal64.exe").exists():
            return p / "terminal64.exe"
    return None


def _fallback_terminal_search() -> list[Path]:
    override = os.environ.get("MT5_TERMINAL_EXE")
    if override:
        p = Path(os.path.expandvars(override)).expanduser()
        return [p] if p.exists() else []

    roots = []
    for name in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        v = os.environ.get(name)
        if v:
            roots.append(Path(v))

    names = [
        "MetaTrader 5",
        "MetaTrader5",
        "MetaQuotes MetaTrader 5",
        "ICMarkets - MetaTrader 5",
        "IC Markets Global - MetaTrader 5",
    ]
    out = []
    for root in roots:
        for name in names:
            p = root / name / "terminal64.exe"
            if p.exists():
                out.append(p)
    return out


def discover_mt5() -> MT5Context:
    scored = []
    for data_dir in _candidate_data_dirs():
        ex5s = _find_expert_ex5(data_dir)
        sets = _find_template_set(data_dir)
        if not ex5s or not sets:
            continue
        terminal = _origin_install_path(data_dir)
        if terminal is None:
            fallbacks = _fallback_terminal_search()
            terminal = fallbacks[0] if fallbacks else None
        if terminal is None or not terminal.exists():
            continue
        expert = max(ex5s, key=lambda p: p.stat().st_mtime)
        template = sets[0]
        score = max(expert.stat().st_mtime, template.stat().st_mtime)
        scored.append((score, data_dir, terminal, expert, template))

    if not scored:
        raise BatchError(
            "Could not auto-discover an MT5 installation containing both "
            f"{EA_BASENAME}.ex5 and a current tester .set preset.\n"
            "Compile/select the V2 EA once in MT5 Strategy Tester. If multiple "
            "terminals are installed, set environment variables MT5_DATA_DIR "
            "and MT5_TERMINAL_EXE explicitly."
        )

    scored.sort(key=lambda x: x[0], reverse=True)
    _, data_dir, terminal, expert, template = scored[0]
    experts_root = data_dir / "MQL5" / "Experts"
    expert_rel = str(expert.relative_to(experts_root).with_suffix("")).replace("/", "\\")
    return MT5Context(
        terminal_exe=terminal,
        data_dir=data_dir,
        expert_rel=expert_rel,
        expert_ex5=expert,
        template_set=template,
    )


def _terminal_running() -> bool:
    if os.name != "nt":
        return False
    try:
        cp = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq terminal64.exe", "/FO", "CSV", "/NH"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,
            check=False,
        )
        return b"terminal64.exe" in (cp.stdout or b"").lower()
    except OSError:
        return False


def get_desktop_dir() -> Path:
    if os.name == "nt":
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as k:
                value, _ = winreg.QueryValueEx(k, "Desktop")
            p = Path(os.path.expandvars(value))
            if p.exists():
                return p
        except Exception:
            pass
    for candidate in (Path.home() / "Desktop", Path.home() / "바탕 화면"):
        if candidate.exists():
            return candidate
    return Path.home()


def sanitize_name(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s.strip())
    return s.strip("._") or "case"


def build_tester_ini(
    ctx: MT5Context,
    set_filename: str,
    symbol: str,
) -> str:
    # Deposit, Currency, Leverage and ExecutionMode are intentionally omitted:
    # MT5 reuses the terminal's currently configured tester values.
    return (
        "[Tester]\r\n"
        f"Expert={ctx.expert_rel}\r\n"
        f"ExpertParameters={set_filename}\r\n"
        f"Symbol={symbol}\r\n"
        f"Period={FIXED_PERIOD}\r\n"
        f"Model={FIXED_MODEL}\r\n"
        f"Optimization={FIXED_OPTIMIZATION}\r\n"
        f"FromDate={FIXED_FROM_DATE}\r\n"
        f"ToDate={FIXED_TO_DATE}\r\n"
        f"ForwardMode={FIXED_FORWARD_MODE}\r\n"
        f"Visual={FIXED_VISUAL}\r\n"
        f"UseCloud={FIXED_USE_CLOUD}\r\n"
        "ShutdownTerminal=1\r\n"
    )


def _global_tester_root() -> Path:
    """
    MT5 local Strategy Tester agents are commonly stored outside the terminal
    data directory at:
        %APPDATA%\\MetaQuotes\\Tester\\<tester-hash>\\Agent-*\\MQL5\\Files
    """
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return Path()
    return Path(appdata) / "MetaQuotes" / "Tester"


def _candidate_csv_paths(ctx: MT5Context, csv_name: str) -> list[Path]:
    out: list[Path] = []

    # FILE_COMMON, if a future EA build chooses it.
    common = _common_files_dir() / csv_name
    if common.exists():
        out.append(common)

    # Direct terminal sandbox.
    direct = ctx.data_dir / "MQL5" / "Files" / csv_name
    if direct.exists():
        out.append(direct)

    # Some installations keep tester agents under the terminal data directory.
    terminal_tester = ctx.data_dir / "Tester"
    if terminal_tester.exists():
        for pattern in (
            f"Agent-*/MQL5/Files/{csv_name}",
            f"*/Agent-*/MQL5/Files/{csv_name}",
            f"*/MQL5/Files/{csv_name}",
        ):
            out.extend(terminal_tester.glob(pattern))

    # Standard MT5 local-agent location observed on Windows:
    # %APPDATA%\\MetaQuotes\\Tester\\<hash>\\Agent-127.0.0.1-3000\\MQL5\\Files
    global_tester = _global_tester_root()
    if global_tester.exists():
        for pattern in (
            f"*/Agent-*/MQL5/Files/{csv_name}",
            f"**/MQL5/Files/{csv_name}",
        ):
            out.extend(global_tester.glob(pattern))

    # Deduplicate resolved paths while preserving discovery order.
    unique: list[Path] = []
    seen: set[str] = set()
    for p in out:
        if not p.exists():
            continue
        try:
            key = str(p.resolve()).lower()
        except OSError:
            key = str(p).lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(p)
    return unique


def _remove_old_csvs(ctx: MT5Context, csv_name: str) -> None:
    for p in _candidate_csv_paths(ctx, csv_name):
        try:
            p.unlink()
        except OSError as e:
            raise BatchError(f"Cannot remove stale tester CSV {p}: {e}") from e


def _wait_for_csv(ctx: MT5Context, csv_name: str, started_epoch: float) -> Path:
    deadline = time.time() + 60.0
    while time.time() < deadline:
        paths = [
            p for p in _candidate_csv_paths(ctx, csv_name)
            if p.stat().st_mtime >= started_epoch - 2.0 and p.stat().st_size > 32
        ]
        if paths:
            return max(paths, key=lambda p: p.stat().st_mtime)
        time.sleep(1.0)
    raise BatchError(
        f"Test finished but CSV was not found: {csv_name}. "
        "Checked terminal Files, tester-agent Files and Terminal\\Common\\Files."
    )


def _ledger_basic_integrity(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    status = {
        "ea_start": b"EA_START" in raw,
        "ea_stop": b"EA_STOP" in raw,
        "execution_divergence": b"EXECUTION_DIVERGENCE" in raw,
        "cancel_rejected": b"PENDING_CANCEL_REJECTED" in raw,
        "size_bytes": len(raw),
    }
    status["infrastructure_complete"] = bool(status["ea_start"] and status["ea_stop"])
    status["profitability_evidence_clean"] = bool(
        status["infrastructure_complete"]
        and not status["execution_divergence"]
        and not status["cancel_rejected"]
    )
    return status


def _write_log(log_path: Path, message: str) -> None:
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}"
    print(line, flush=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_fixed_2025_batch(
    batch_id: str,
    cases: Iterable[TestCase],
    symbols: Iterable[str] = FIXED_SYMBOLS,
    dry_run: bool = False,
) -> Path | None:
    if os.name != "nt":
        raise BatchError("MT5 batch execution is supported only on Windows.")

    cases = list(cases)
    symbols = tuple(symbols)
    if not cases:
        raise BatchError("No test cases supplied.")
    if set(symbols) - set(FIXED_SYMBOLS):
        raise BatchError(
            f"This fixed runner currently allows only: {', '.join(FIXED_SYMBOLS)}"
        )

    ctx = discover_mt5()

    temp_root = Path(tempfile.mkdtemp(prefix=f"Trading_{sanitize_name(batch_id)}_"))
    results_dir = temp_root / "results"
    repro_dir = results_dir / "repro"
    results_dir.mkdir(parents=True)
    repro_dir.mkdir(parents=True)
    log_path = results_dir / "run_log.txt"

    _write_log(log_path, f"batch_id={batch_id}")
    _write_log(log_path, f"terminal={ctx.terminal_exe}")
    _write_log(log_path, f"data_dir={ctx.data_dir}")
    _write_log(log_path, f"expert={ctx.expert_rel}")
    _write_log(log_path, f"expert_ex5_sha256={_sha256(ctx.expert_ex5)}")
    _write_log(log_path, f"template_set={ctx.template_set}")
    _write_log(
        log_path,
        f"fixed_test={FIXED_SYMBOLS} {FIXED_FROM_DATE}..{FIXED_TO_DATE} "
        f"period={FIXED_PERIOD} model={FIXED_MODEL}",
    )

    template_text, template_encoding = read_text_detect(ctx.template_set)
    all_runs = [(symbol, case) for symbol in symbols for case in cases]

    manifest: dict[str, Any] = {
        "batch_id": batch_id,
        "created_at_local": dt.datetime.now().isoformat(timespec="seconds"),
        "fixed": {
            "symbols": list(symbols),
            "from_date": FIXED_FROM_DATE,
            "to_date": FIXED_TO_DATE,
            "period": FIXED_PERIOD,
            "model": FIXED_MODEL,
            "model_name": "Every tick based on real ticks",
            "optimization": FIXED_OPTIMIZATION,
            "forward_mode": FIXED_FORWARD_MODE,
            "visual": FIXED_VISUAL,
            "use_cloud": FIXED_USE_CLOUD,
            "fixed_ea_inputs": FIXED_EA_INPUTS,
            "account_tester_fields": "Deposit/Leverage/Currency/ExecutionMode inherited from current terminal tester settings",
        },
        "mt5": {
            "terminal_exe": str(ctx.terminal_exe),
            "data_dir": str(ctx.data_dir),
            "expert_rel": ctx.expert_rel,
            "expert_ex5": str(ctx.expert_ex5),
            "expert_ex5_sha256": _sha256(ctx.expert_ex5),
            "template_set": str(ctx.template_set),
        },
        "runs": [],
    }

    if dry_run:
        for idx, (symbol, case) in enumerate(all_runs, 1):
            csv_name = f"{sanitize_name(batch_id)}__{sanitize_name(case.name)}__{symbol}__2025.csv"
            _write_log(
                log_path,
                f"DRY [{idx}/{len(all_runs)}] {symbol} {case.name} -> {csv_name} overrides={case.overrides}",
            )
        print(f"\nDry-run OK. Discovery log: {log_path}")
        return None

    if _terminal_running():
        raise BatchError(
            "terminal64.exe is already running. Close MT5 before starting the batch "
            "so each /config test owns the terminal lifecycle deterministically."
        )

    tester_preset_dir = ctx.data_dir / "MQL5" / "Profiles" / "Tester"
    tester_preset_dir.mkdir(parents=True, exist_ok=True)
    generated_sets: list[Path] = []

    try:
        for idx, (symbol, case) in enumerate(all_runs, 1):
            safe_case = sanitize_name(case.name)
            csv_name = f"{sanitize_name(batch_id)}__{safe_case}__{symbol}__2025.csv"
            set_filename = f"_BATCH_{sanitize_name(batch_id)}__{safe_case}__{symbol}.set"
            set_path = tester_preset_dir / set_filename
            ini_path = temp_root / f"{safe_case}__{symbol}.ini"

            values = dict(FIXED_EA_INPUTS)
            values.update(case.overrides)
            values["InpEventCsvFile"] = csv_name

            patched = patch_set_text(template_text, values)
            write_text_detect(set_path, patched, template_encoding)
            generated_sets.append(set_path)

            # Save exact reproducibility copies in the result archive.
            repro_set = repro_dir / set_filename
            shutil.copy2(set_path, repro_set)

            ini_text = build_tester_ini(ctx, set_filename, symbol)
            ini_path.write_text(ini_text, encoding="utf-8", newline="")
            shutil.copy2(ini_path, repro_dir / ini_path.name)

            _remove_old_csvs(ctx, csv_name)

            _write_log(
                log_path,
                f"RUN [{idx}/{len(all_runs)}] symbol={symbol} case={case.name} csv={csv_name}",
            )
            _write_log(log_path, f"overrides={json.dumps(case.overrides, ensure_ascii=False)}")

            started = time.time()
            cmd = [str(ctx.terminal_exe), f"/config:{ini_path}"]
            try:
                cp = subprocess.run(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                    timeout=MAX_CASE_SECONDS,
                    check=False,
                )
            except subprocess.TimeoutExpired as e:
                raise BatchError(
                    f"MT5 timed out after {MAX_CASE_SECONDS}s: {symbol} {case.name}"
                ) from e

            elapsed = time.time() - started
            source_csv = _wait_for_csv(ctx, csv_name, started)
            final_csv = results_dir / csv_name
            shutil.copy2(source_csv, final_csv)
            integrity = _ledger_basic_integrity(final_csv)

            if not integrity["infrastructure_complete"]:
                raise BatchError(
                    f"Ledger is incomplete (EA_START/EA_STOP missing): {final_csv}"
                )

            manifest["runs"].append(
                {
                    "index": idx,
                    "symbol": symbol,
                    "case": case.name,
                    "note": case.note,
                    "overrides": case.overrides,
                    "csv": csv_name,
                    "csv_sha256": _sha256(final_csv),
                    "source_csv": str(source_csv),
                    "set_file": set_filename,
                    "ini_file": ini_path.name,
                    "terminal_returncode": cp.returncode,
                    "elapsed_seconds": round(elapsed, 3),
                    "integrity": integrity,
                }
            )
            _write_log(
                log_path,
                f"DONE [{idx}/{len(all_runs)}] elapsed={elapsed/60:.1f}m "
                f"clean_evidence={integrity['profitability_evidence_clean']} source={source_csv}",
            )

        manifest_path = results_dir / "batch_manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        desktop = get_desktop_dir()
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = desktop / f"Trading_{sanitize_name(batch_id)}_{timestamp}.zip"

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for p in sorted(results_dir.rglob("*")):
                if p.is_file():
                    z.write(p, p.relative_to(results_dir))

        _write_log(log_path, f"ZIP={zip_path}")
        print("\n============================================================")
        print("BATCH COMPLETE")
        print(f"ZIP: {zip_path}")
        print("Send this ZIP to ChatGPT for analysis.")
        print("============================================================")
        return zip_path

    finally:
        for p in generated_sets:
            try:
                p.unlink()
            except OSError:
                pass
        # Keep temp results only until a ZIP is successfully produced. If an
        # exception occurs, leave them in %TEMP% so diagnostics are not lost.


def cli_main(batch_id: str, cases: Iterable[TestCase]) -> None:
    parser = argparse.ArgumentParser(
        description="Fixed GOLD/BTCUSD 2025 MT5 real-tick batch runner"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="discover MT5 and print the matrix without launching tests",
    )
    args = parser.parse_args()
    try:
        run_fixed_2025_batch(batch_id, cases, dry_run=args.dry_run)
    except BatchError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(
        "This is the stable batch engine. Run a research case file such as "
        "python tools\\run_d152_gold_btc_2025.py"
    )
