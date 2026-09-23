from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = {
    "AGENTS.md",
    "README.md",
    "PROJECT_MANIFEST.json",
    "docs/PROJECT_STRUCTURE.md",
    "docs/README.md",
    "launchers/README.md",
    "scripts/README.md",
    "output/README.md",
    "archive/README.md",
    "bridge/README.md",
    "mt5/README.md",
    "mt5/experts/TradeJournalExporterEA.mq5",
    "mt5/experts/README.md",
    "mt5/indicators/ICTCockpitIndicator.mq5",
    "mt5/indicators/README.md",
    "mt5/legacy/README.md",
    "mentor_context_pack/README.md",
    "tradingview/README.md",
    "docs/ea/v12/AGENTS_V12.md",
    "docs/ea/v12/V12_DOCUMENT_AUTHORITY_MAP_20260923.md",
    "docs/ea/v12/HANDOFF_V12.md",
    "docs/ea/v12/RESEARCH_STATE_V12.md",
    "research/v12/README.md",
    "research/v12/v12_crt_event_contract.schema.json",
}

ALLOWED_ROOT_FILES = {
    ".gitignore",
    "AGENTS.md",
    "GOLD#_M1_202201030100_202608282357.csv",
    "MANIFEST.json",
    "PROJECT_MANIFEST.json",
    "README.md",
    "VALIDATION_WORKING_RESULT.md",
    "index.html",
    "package-lock.json",
    "package.json",
    "requirements-v4-tournament.txt",
    "requirements-v4.txt",
    "tsconfig.json",
    "tsconfig.node.json",
    "tsconfig.node.tsbuildinfo",
    "tsconfig.tsbuildinfo",
    "vite.config.ts",
    "v5_038a_cot_commercial_price_interaction.py",
}

def main() -> int:
    errors: list[str] = []

    for relative in sorted(REQUIRED_PATHS):
        if not (ROOT / relative).exists():
            errors.append(f"missing required path: {relative}")

    root_files = {path.name for path in ROOT.iterdir() if path.is_file()}
    unexpected_root = sorted(root_files - ALLOWED_ROOT_FILES)
    if unexpected_root:
        errors.append("unexpected root files: " + ", ".join(unexpected_root))

    output_dirs = {
        path.name for path in (ROOT / "output").iterdir() if path.is_dir()
    }
    for launcher in sorted((ROOT / "launchers").glob("*.cmd")):
        source = launcher.read_text(encoding="utf-8", errors="replace")
        if 'cd /d "%~dp0.."' not in source:
            errors.append(f"launcher does not enter project root: {launcher.name}")

    try:
        manifest = json.loads((ROOT / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
        if manifest.get("authority", {}).get("manualTradingContract") != "AGENTS.md":
            errors.append("manifest authority does not point to AGENTS.md")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid PROJECT_MANIFEST.json: {exc}")

    if errors:
        print("WORKSPACE_STRUCTURE_FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    archived = sum(1 for path in (ROOT / "archive" / "outputs" / "legacy").iterdir() if path.is_dir())
    print("WORKSPACE_STRUCTURE_OK")
    print(f"ACTIVE_OUTPUT_DIRS={len(output_dirs)}")
    print(f"ARCHIVED_OUTPUT_DIRS={archived}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
