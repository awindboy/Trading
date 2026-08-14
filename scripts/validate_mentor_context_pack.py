from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "mentor_context_pack"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main() -> int:
    errors: list[str] = []
    required = [
        PACK / "README.md",
        PACK / "START_PROMPT.md",
        PACK / "OBSERVATION_PROTOCOL.md",
        PACK / "LIVE_WORKFLOW.md",
        PACK / "state" / "current_state.json",
        PACK / "schemas" / "decision_output.schema.json",
        PACK / "examples" / "case_index.jsonl",
        PACK / "manifest.json",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"missing: {path.relative_to(ROOT)}")

    if errors:
        print("\n".join(errors))
        return 1

    manifest = json.loads((PACK / "manifest.json").read_text(encoding="utf-8"))
    if sha256(ROOT / "AGENTS.md") != manifest["authority_sha256"]:
        errors.append("AGENTS.md hash differs from manifest; rebuild the pack")

    for item in manifest["official_evidence"]:
        path = ROOT / item["path"]
        if not path.exists():
            errors.append(f"missing evidence: {item['path']}")
        elif sha256(path) != item["sha256"]:
            errors.append(f"evidence hash mismatch: {item['path']}")

    case_path = ROOT / manifest["case_index"]
    if sha256(case_path) != manifest["case_index_sha256"]:
        errors.append("case index hash mismatch")

    cases = []
    seen = set()
    with case_path.open("r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"case line {number}: {exc}")
                continue
            case_id = case.get("case_id")
            if case_id in seen:
                errors.append(f"duplicate case: {case_id}")
            seen.add(case_id)
            cutoff = parse_time(case["decision_as_of"])
            for asset in case.get("assets", []):
                path = ROOT / asset["path"]
                if not path.exists():
                    errors.append(f"missing asset: {asset['path']}")
                    continue
                if sha256(path) != asset["sha256"]:
                    errors.append(f"asset hash mismatch: {asset['path']}")
                if parse_time(asset["chart_as_of"]) > cutoff:
                    errors.append(f"future asset: {case_id} {asset['path']}")
            cases.append(case)

    if len(cases) != manifest["case_count"]:
        errors.append(f"case count mismatch: {len(cases)} != {manifest['case_count']}")

    state = json.loads((PACK / "state" / "current_state.json").read_text(encoding="utf-8"))
    if state.get("status") not in {
        "FLAT", "PREPARED", "ARMED", "TRIGGERED", "PENDING", "FILLED", "CLOSED", "CANCELED"
    }:
        errors.append("invalid current state status")

    schema = json.loads((PACK / "schemas" / "decision_output.schema.json").read_text(encoding="utf-8"))
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("unexpected decision schema version")

    if errors:
        print("MENTOR_CONTEXT_PACK_INVALID")
        print("\n".join(errors))
        return 1

    asset_count = sum(len(case.get("assets", [])) for case in cases)
    print(f"MENTOR_CONTEXT_PACK_OK cases={len(cases)} assets={asset_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
