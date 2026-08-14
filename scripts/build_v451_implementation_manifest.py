from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mentor_replay_v4_core import PIPELINE_VERSION


FILES = (
    "scripts/mentor_replay_v4_core.py",
    "scripts/mentor_ai_replay_v4.py",
    "scripts/mentor_ai_live_v4.py",
    "scripts/build_ground_truth_v2.py",
    "scripts/audit_ground_truth_v2_codex.py",
    "scripts/build_mentor_api_contracts.py",
    "scripts/test_mentor_ai_replay_v4.py",
    "scripts/test_mentor_ai_replay_v451.py",
    "scripts/test_ground_truth_v2_integration.py",
    "scripts/test_mentor_ai_live_v4.py",
    "mentor_context_pack/api_contracts/v4_manifest.json",
    "config/mentor_ai_replay_v4_49_50_legacy_manifest.json",
)

GROUND_TRUTH_DIR = ROOT / "output/ground_truth_v2_june2026_v451"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", action="append", default=[])
    parser.add_argument(
        "--output",
        default=str(ROOT / "output/implementation/mentor_ai_replay_v451_manifest.json"),
    )
    args = parser.parse_args()
    results: dict[str, str] = {}
    for raw in args.result:
        if "=" not in raw:
            raise SystemExit(f"invalid --result: {raw}")
        name, status = raw.split("=", 1)
        results[name] = status.upper()
    if not results or any(value != "PASS" for value in results.values()):
        raise SystemExit("implementation manifest requires explicit PASS test results")
    if PIPELINE_VERSION != "4.51-ground-truth-v2":
        raise SystemExit(f"unexpected pipeline version: {PIPELINE_VERSION}")
    missing = [name for name in FILES if not (ROOT / name).exists()]
    if missing:
        raise SystemExit("manifest files are missing: " + ",".join(missing))
    ground_truth_manifest_path = GROUND_TRUTH_DIR / "manifest.json"
    accepted_ledger_path = GROUND_TRUTH_DIR / "accepted_ground_truth.jsonl"
    stateful_audit_path = GROUND_TRUTH_DIR / "audits/stateful_plan.jsonl"
    completion_report_path = GROUND_TRUTH_DIR / "COMPLETION_REPORT.md"
    if not ground_truth_manifest_path.exists() or not accepted_ledger_path.exists():
        raise SystemExit("frozen Ground Truth V2 artifacts are missing")
    if not stateful_audit_path.exists() or not completion_report_path.exists():
        raise SystemExit("stateful Ground Truth V2 completion evidence is missing")
    if (GROUND_TRUTH_DIR / "BLOCKED_REPORT.md").exists():
        raise SystemExit("frozen Ground Truth V2 still contains a blocked report")
    ground_truth_manifest = json.loads(
        ground_truth_manifest_path.read_text(encoding="utf-8-sig")
    )
    if (
        ground_truth_manifest.get("status") != "FROZEN_GROUND_TRUTH_V2"
        or ground_truth_manifest.get("groundTruthComplete") is not True
    ):
        raise SystemExit("Ground Truth V2 is not frozen")
    if "STATEFUL_PLAN_SEQUENCE" not in ground_truth_manifest.get(
        "requiredAudits", []
    ):
        raise SystemExit("Ground Truth V2 lacks the stateful PLAN audit gate")
    recorded_stateful_hash = (
        ground_truth_manifest.get("auditLedgerSha256") or {}
    ).get("statefulPlan")
    if recorded_stateful_hash != sha256_file(stateful_audit_path):
        raise SystemExit("stateful PLAN audit hash does not match the frozen manifest")
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "pipelineVersion": PIPELINE_VERSION,
        "status": "CODE_COMPLETE_LOCAL_VERIFICATION_ONLY",
        "generatedAtUtc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "agentsSha256": sha256_file(ROOT / "AGENTS.md"),
        "contractsManifestSha256": sha256_file(
            ROOT / "mentor_context_pack/api_contracts/v4_manifest.json"
        ),
        "files": {
            name: sha256_file(ROOT / name) for name in FILES
        },
        "testResults": results,
        "groundTruth": {
            "path": str(GROUND_TRUTH_DIR.relative_to(ROOT)).replace("\\", "/"),
            "manifestSha256": sha256_file(ground_truth_manifest_path),
            "acceptedLedgerSha256": sha256_file(accepted_ledger_path),
            "statefulPlanAuditSha256": sha256_file(stateful_audit_path),
            "acceptedTradeCount": int(ground_truth_manifest["acceptedTradeCount"]),
            "engineCandidateMissCount": int(
                ground_truth_manifest.get("engineCandidateMissCount", 0)
            ),
        },
        "notExecuted": [
            "REAL_GEMINI_REPRODUCIBILITY",
            "LIVE_SHADOW_PARITY",
            "REAL_MT5_DEMO_FILL",
            "REAL_ACCOUNT_ORDERING",
        ],
        "realAccountOrdering": "HARD_BLOCKED",
    }
    body["manifestSha256"] = hashlib.sha256(
        json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    output.write_text(
        json.dumps(body, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"MENTOR_V451_IMPLEMENTATION_MANIFEST_OK {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
