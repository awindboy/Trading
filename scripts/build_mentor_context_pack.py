from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "mentor_context_pack"
SOURCE = ROOT / "output" / "mentor_50trade_oos_v2"
IMAGES = SOURCE / "internal_charts" / "strict_asof"
ASSET_DIR = PACK / "examples" / "images"

TRADE_CASES = {
    "OOS2-037": ["20251208_0800_map.png", "20251208_1002_micro.png"],
    "OOS2-038": ["20251208_1701_map.png", "20251208_1701_micro.png"],
    "OOS2-041": ["20251212_1841_map.png", "20251212_1841_micro.png"],
    "OOS2-042": ["20251215_1200_map.png", "20251215_1200_micro.png"],
    "OOS2-044": ["20251222_1200_map.png", "20251222_1700_micro.png"],
    "OOS2-048": ["20260617_0600_map.png", "20260617_1652_micro.png"],
    "OOS2-049": ["20260618_0600_map.png", "20260618_0800_micro.png"],
    "OOS2-050": ["20260618_1200_map.png", "20260618_0800_micro.png"],
}

DECISION_CASES = {
    "OOS2-D0105": ["20251204_0503_map.png", "20251204_0739_micro.png"],
    "OOS2-D0112": ["20251209_0810_map.png", "20251209_0810_micro.png"],
    "OOS2-D0118": ["20251210_2102_map.png", "20251210_2102_micro.png"],
    "OOS2-D0129": ["20251217_1200_map.png", "20251217_1520_micro.png"],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def chart_time(name: str) -> datetime:
    match = re.match(r"(\d{8})_(\d{4})_", name)
    if not match:
        raise ValueError(f"Cannot parse chart time: {name}")
    return datetime.strptime("".join(match.groups()), "%Y%m%d%H%M").replace(tzinfo=timezone.utc)


def load_decisions() -> list[dict]:
    rows = []
    with (SOURCE / "manual_decisions.jsonl").open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_trades() -> dict[str, dict]:
    with (SOURCE / "trades.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        return {row["trade_id"]: row for row in csv.DictReader(handle)}


def copy_assets(case_id: str, names: list[str], decision_at: str) -> list[dict]:
    cutoff = parse_time(decision_at)
    assets = []
    for name in names:
        source = IMAGES / name
        if not source.exists():
            raise FileNotFoundError(source)
        observed_at = chart_time(name)
        if observed_at > cutoff:
            raise ValueError(f"Future chart rejected: {case_id} {name} > {decision_at}")
        destination = ASSET_DIR / f"{case_id}__{name}"
        shutil.copy2(source, destination)
        assets.append(
            {
                "path": destination.relative_to(ROOT).as_posix(),
                "chart_as_of": observed_at.isoformat().replace("+00:00", "Z"),
                "sha256": sha256(destination),
            }
        )
    return assets


def main() -> int:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for existing in ASSET_DIR.glob("*.png"):
        existing.unlink()

    decisions = load_decisions()
    decision_by_id = {row["decision_id"]: row for row in decisions}
    order_by_trade = {
        row["trade_id"]: row
        for row in decisions
        if row.get("status") == "ORDER_FROZEN" and row.get("trade_id")
    }
    trades = load_trades()

    cases = []
    for trade_id, image_names in TRADE_CASES.items():
        trade = trades[trade_id]
        order = order_by_trade[trade_id]
        cases.append(
            {
                "case_id": trade_id,
                "case_type": "TRADE",
                "decision_as_of": order["as_of"],
                "order_decision": order,
                "outcome": trade,
                "assets": copy_assets(trade_id, image_names, order["as_of"]),
            }
        )

    for decision_id, image_names in DECISION_CASES.items():
        decision = decision_by_id[decision_id]
        cases.append(
            {
                "case_id": decision_id,
                "case_type": decision["status"],
                "decision_as_of": decision["as_of"],
                "decision": decision,
                "assets": copy_assets(decision_id, image_names, decision["as_of"]),
            }
        )

    case_path = PACK / "examples" / "case_index.jsonl"
    with case_path.open("w", encoding="utf-8", newline="\n") as handle:
        for case in cases:
            handle.write(json.dumps(case, ensure_ascii=False, separators=(",", ":")) + "\n")

    evidence = [
        ROOT / "AGENTS.md",
        ROOT / "output" / "mentor_50trade_scope_locked_v1" / "working_trades.csv",
        ROOT / "output" / "mentor_50trade_scope_locked_v1" / "FINAL_REPORT.md",
        SOURCE / "trades.csv",
        SOURCE / "manual_decisions.jsonl",
        SOURCE / "FINAL_REPORT.md",
        SOURCE / "WORKING_STATE.md",
    ]
    manifest = {
        "pack_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": "AGENTS.md",
        "authority_sha256": sha256(ROOT / "AGENTS.md"),
        "official_evidence": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in evidence
        ],
        "case_count": len(cases),
        "trade_case_count": len(TRADE_CASES),
        "non_trade_case_count": len(DECISION_CASES),
        "case_index": case_path.relative_to(ROOT).as_posix(),
        "case_index_sha256": sha256(case_path),
    }
    (PACK / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"MENTOR_CONTEXT_PACK_BUILT cases={len(cases)} assets={sum(len(c['assets']) for c in cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
