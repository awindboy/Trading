from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mentor_ai_replay import flat_delivery_candidate_at, parse_utc


SECRET = ROOT / "data" / "mentor_ai_replay_secret.json"
DECISIONS = ROOT / "output" / "mentor_50trade_oos_v2" / "manual_decisions.jsonl"


def truth_orders() -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for line in DECISIONS.read_text(encoding="utf-8-sig").splitlines():
        row = json.loads(line)
        match = re.fullmatch(r"OOS2-(\d+)", str(row.get("trade_id", "")))
        if row.get("status") != "ORDER_FROZEN" or not match:
            continue
        number = int(match.group(1))
        if not 1 <= number <= 13:
            continue
        root = re.search(
            r"M15\s+(\d{4}-\d\d-\d\d)\s+(\d\d:\d\d)",
            str(row.get("root_ob", "")),
        )
        if root is None:
            raise ValueError(f"missing M15 root in {row['trade_id']}")
        root_time = parse_utc(f"{root.group(1)}T{root.group(2)}:00Z")
        result.append({
            "tradeId": str(row["trade_id"]),
            "decisionAtUtc": str(row["as_of"]),
            "rootBarId": f"M15:{root_time}",
        })
    return result


def main() -> int:
    secret = json.loads(SECRET.read_text(encoding="utf-8-sig"))
    config = dict(secret["config"])
    dataset = Path(str(config["dataset"]))
    if not dataset.is_absolute():
        dataset = ROOT / dataset
    rates = np.load(dataset, allow_pickle=True)["rates"]
    start = parse_utc(str(config["replayStartUtc"]))
    end = parse_utc(str(config["replayEndUtc"]))
    start_index = max(32, int(np.searchsorted(rates["time"], start, side="left")))
    end_index = int(np.searchsorted(rates["time"], end, side="left"))

    by_root: dict[str, list[dict[str, object]]] = defaultdict(list)
    for index in range(start_index, end_index):
        candidate = flat_delivery_candidate_at(rates, index, config)
        if candidate is not None:
            by_root[str(candidate["candidateRootBarId"])].append(candidate)

    truth = truth_orders()
    matched = 0
    print(f"replay={config['replayStartUtc']}..{config['replayEndUtc']}")
    print(f"uniqueWakeRoots={len(by_root)} wakeEvents={sum(map(len, by_root.values()))}")
    for item in truth:
        deadline = parse_utc(item["decisionAtUtc"])
        candidates = [
            row for row in by_root.get(item["rootBarId"], [])
            if parse_utc(str(row["detectedAtUtc"])) <= deadline
        ]
        if candidates:
            matched += 1
            latest = str(candidates[-1]["detectedAtUtc"])
            status = f"MATCH latest={latest}"
        else:
            status = "MISS"
        print(f"{item['tradeId']} {item['rootBarId']} {status}")
    false_roots = sorted(set(by_root) - {item["rootBarId"] for item in truth})
    print(f"truthMatched={matched}/{len(truth)} falseWakeRoots={len(false_roots)}")
    return 0 if matched >= 10 else 1


if __name__ == "__main__":
    raise SystemExit(main())
