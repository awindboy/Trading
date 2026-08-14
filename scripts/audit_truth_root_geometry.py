from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mentor_ai_replay import _closed_ohlc_bucket, parse_utc


def main() -> int:
    config = json.loads(
        (ROOT / "data/mentor_ai_replay_secret.json").read_text(encoding="utf-8-sig")
    )["config"]
    dataset = ROOT / str(config["dataset"])
    rates = np.load(dataset, allow_pickle=True)["rates"]
    source = ROOT / "output" / "mentor_50trade_oos_v2" / "manual_decisions.jsonl"
    for line in source.read_text(encoding="utf-8-sig").splitlines():
        row = json.loads(line)
        trade = re.fullmatch(r"OOS2-(\d+)", str(row.get("trade_id", "")))
        if row.get("status") != "ORDER_FROZEN" or not trade:
            continue
        if not 1 <= int(trade.group(1)) <= 13:
            continue
        match = re.search(
            r"M15\s+(\d{4}-\d\d-\d\d)\s+(\d\d:\d\d)",
            str(row.get("root_ob", "")),
        )
        if match is None:
            continue
        root_time = parse_utc(f"{match.group(1)}T{match.group(2)}:00Z")
        root = _closed_ohlc_bucket(rates, root_time, 900)
        if root is None:
            continue
        deadline = parse_utc(str(row["as_of"]))
        direction = str(row["direction"])
        for radius in (1, 2, 3, 4, 8):
            neighbors = []
            for offset in range(-radius, radius + 1):
                if offset == 0:
                    continue
                origin = root_time + offset * 900
                if origin + 900 > deadline:
                    continue
                candidate = _closed_ohlc_bucket(rates, origin, 900)
                if candidate is not None:
                    neighbors.append(candidate)
            if direction == "SHORT":
                extreme = all(root["high"] >= item["high"] for item in neighbors)
            else:
                extreme = all(root["low"] <= item["low"] for item in neighbors)
            if extreme:
                pivot = f"pivotRadius={radius}"
                break
        else:
            pivot = "notLocalExtreme"
        root_range = root["high"] - root["low"]
        parent_flags = []
        for label, seconds in (("M30", 1800), ("H1", 3600)):
            parent_time = (root_time // seconds) * seconds
            parent = _closed_ohlc_bucket(rates, parent_time, seconds)
            if parent is None or parent_time + seconds > deadline:
                continue
            parent_opposite = (
                direction == "LONG" and parent["close"] < parent["open"]
            ) or (
                direction == "SHORT" and parent["close"] > parent["open"]
            )
            parent_flags.append(f"{label}Opposite={int(parent_opposite)}")
        closed_after = []
        for origin in range(root_time + 900, deadline, 900):
            candidate = _closed_ohlc_bucket(rates, origin, 900)
            if candidate is not None and origin + 900 <= deadline:
                closed_after.append(candidate)
        if direction == "SHORT":
            delivered_close = min(
                [item["close"] for item in closed_after] or [root["close"]]
            )
            broken_depth = 0
            for depth in range(1, 13):
                prior = _closed_ohlc_bucket(rates, root_time - depth * 900, 900)
                if prior is None or delivered_close >= prior["low"]:
                    break
                broken_depth = depth
        else:
            delivered_close = max(
                [item["close"] for item in closed_after] or [root["close"]]
            )
            broken_depth = 0
            for depth in range(1, 13):
                prior = _closed_ohlc_bucket(rates, root_time - depth * 900, 900)
                if prior is None or delivered_close <= prior["high"]:
                    break
                broken_depth = depth
        print(
            f"{row['trade_id']} {direction} {pivot} "
            f"range={root_range:.2f} brokenPriorBars={broken_depth} "
            f"{' '.join(parent_flags)} decision={row['as_of']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
