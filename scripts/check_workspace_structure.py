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
}

ALLOWED_ROOT_FILES = {
    ".gitignore",
    "AGENTS.md",
    "PROJECT_MANIFEST.json",
    "README.md",
    "index.html",
    "package-lock.json",
    "package.json",
    "tsconfig.json",
    "tsconfig.node.json",
    "tsconfig.node.tsbuildinfo",
    "tsconfig.tsbuildinfo",
    "vite.config.ts",
}

ALLOWED_OUTPUT_DIRS = {
    "ai_feedback",
    "build-check",
    "clean_trade_screenshots",
    "current_chart_scenario",
    "datasets",
    "_verification",
    "ground_truth_v2_june2026",
    "ground_truth_v2_june2026_v451",
    "ground_truth_v2_june2026_v451_r3",
    "implementation",
    "mentor_ai_live_v4",
    "mentor_ai_replay_v4_benchmarks",
    "mentor_ai_replay_v4_cache",
    "mentor_ai_replay_v4_fixed_packets",
    "mentor_ai_replay_v4_runs",
    "mentor_ai_replay_v4_validation",
    "mentor_aug18_22_truth_v1",
    "mentor_aug21_truth_v3",
    "mentor_engine",
    "mentor_june2026_causal_benchmark",
    "mentor_manual_vs_gemini_2026-06-08",
    "mentor_manual_vs_gemini_2026-06-09",
    "mentor_oct28_31_protocol_truth_v2",
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
    unexpected_output = sorted(output_dirs - ALLOWED_OUTPUT_DIRS)
    if unexpected_output:
        errors.append(
            "unclassified active output directories: " + ", ".join(unexpected_output)
        )

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
