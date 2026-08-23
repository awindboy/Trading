from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from mt5_batch_runner import BatchError, discover_mt5, read_text_detect

EXPECTED_UNIVERSE_ID = "D154O_STAGE_A_UL32_20260824"
SOURCE_REL = Path("mt5/scripts/D154OStageAExporter.mq5")
TARGET_REL = Path("MQL5/Scripts/TradingResearch/D154OStageAExporter.mq5")
STATE_REL = Path("tools/.d154o_stage_a_exporter_compile_state.json")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head(repo: Path) -> str | None:
    try:
        cp = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        if cp.returncode == 0:
            return cp.stdout.strip()
    except OSError:
        pass
    return None


def parse_compile_result(text: str) -> tuple[int | None, int | None]:
    # MetaEditor logs commonly end with "Result: 0 errors, 0 warnings, ..."
    matches = re.findall(r"(\d+)\s+errors?\s*,\s*(\d+)\s+warnings?", text, re.I)
    if not matches:
        return None, None
    e, w = matches[-1]
    return int(e), int(w)


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("ERROR: this installer must run on the Windows MT5 machine.")

    repo = Path(__file__).resolve().parents[1]
    source = repo / SOURCE_REL
    if not source.exists():
        raise SystemExit(f"ERROR: repo exporter source is missing: {source}")

    source_text = source.read_text(encoding="utf-8")
    if EXPECTED_UNIVERSE_ID not in source_text:
        raise SystemExit("ERROR: exporter universe id does not match this D154O package.")

    try:
        ctx = discover_mt5()
    except BatchError as e:
        raise SystemExit(f"ERROR: {e}") from e

    target = ctx.data_dir / TARGET_REL
    target.parent.mkdir(parents=True, exist_ok=True)

    source_hash = sha256(source)
    if target.exists():
        target_hash = sha256(target)
        if target_hash != source_hash:
            raise SystemExit(
                "ERROR: terminal already contains a different D154OStageAExporter.mq5.\n"
                f"Existing: {target}\n"
                "Fail-closed: move/inspect that file manually before rerunning."
            )
    else:
        shutil.copy2(source, target)

    # Re-copy even when identical so timestamp reflects the exact source used for compile.
    shutil.copy2(source, target)

    metaeditor = ctx.terminal_exe.parent / "metaeditor64.exe"
    if not metaeditor.exists():
        alt = ctx.terminal_exe.parent / "metaeditor.exe"
        metaeditor = alt if alt.exists() else metaeditor
    if not metaeditor.exists():
        raise SystemExit(f"ERROR: MetaEditor executable not found beside terminal: {ctx.terminal_exe.parent}")

    ex5 = target.with_suffix(".ex5")
    before_hash = sha256(ex5) if ex5.exists() else None
    log_path = repo / "tools" / "d154o_stage_a_metaeditor_compile.log"
    if log_path.exists():
        log_path.unlink()

    cmd = [str(metaeditor), f"/compile:{target}", f"/log:{log_path}"]
    cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

    if not log_path.exists():
        raise SystemExit(
            "ERROR: MetaEditor returned without a compile log.\n"
            f"command={cmd}\nreturncode={cp.returncode}"
        )

    log_text, _ = read_text_detect(log_path)
    errors, warnings = parse_compile_result(log_text)
    if errors is None:
        raise SystemExit(f"ERROR: could not parse MetaEditor compile result. Inspect: {log_path}")
    if errors != 0:
        raise SystemExit(f"ERROR: MetaEditor compile failed with {errors} error(s). Inspect: {log_path}")
    if not ex5.exists():
        raise SystemExit(f"ERROR: compile reported 0 errors but EX5 is missing: {ex5}")

    after_hash = sha256(ex5)
    state = {
        "universe_id": EXPECTED_UNIVERSE_ID,
        "git_head_at_compile": git_head(repo),
        "repo_source": str(source),
        "repo_source_sha256": source_hash,
        "data_dir": str(ctx.data_dir),
        "terminal_exe": str(ctx.terminal_exe),
        "terminal_source": str(target),
        "terminal_source_sha256": sha256(target),
        "terminal_ex5": str(ex5),
        "terminal_ex5_sha256_before": before_hash,
        "terminal_ex5_sha256_after": after_hash,
        "metaeditor_log": str(log_path),
        "compile_errors": errors,
        "compile_warnings": warnings,
    }
    state_path = repo / STATE_REL
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    print("D154O Stage-A exporter compile PASS")
    print(f"  source:   {source}")
    print(f"  terminal: {target}")
    print(f"  EX5:      {ex5}")
    print(f"  errors:   {errors}")
    print(f"  warnings: {warnings}")
    print(f"  state:    {state_path}")
    print()
    print("Next: open MT5 -> Navigator -> Scripts -> TradingResearch -> D154OStageAExporter")
    print("Drag it onto any chart and wait for 'D154O_STAGE_A EXPORT COMPLETE'.")


if __name__ == "__main__":
    main()
