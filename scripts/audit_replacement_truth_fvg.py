from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mentor_ai_replay import parse_utc, utc_text


def parse_zone(text: str) -> tuple[float, float] | None:
    matches = re.findall(r"\[([0-9.]+),([0-9.]+)\]", text.replace(" ", ""))
    if not matches:
        return None
    low, high = map(float, matches[-1])
    return min(low, high), max(low, high)


def main() -> int:
    config = json.loads(
        (ROOT / "data" / "mentor_ai_replay_secret.json").read_text(encoding="utf-8-sig")
    )["config"]
    rates = np.load(ROOT / str(config["dataset"]), allow_pickle=True)["rates"]
    trades = {
        row["trade_id"]: row
        for row in __import__("csv").DictReader(
            (ROOT / "output" / "mentor_oct27_31_high_activity_truth" / "trades.csv")
            .open(encoding="utf-8-sig")
        )
    }
    decisions = ROOT / "output" / "mentor_50trade_oos_v2" / "manual_decisions.jsonl"
    valid = 0
    reviewed = 0
    for line in decisions.read_text(encoding="utf-8-sig").splitlines():
        row = json.loads(line)
        trade = re.fullmatch(r"OOS2-(\d+)", str(row.get("trade_id", "")))
        if row.get("status") != "ORDER_FROZEN" or not trade:
            continue
        if not 1 <= int(trade.group(1)) <= 13:
            continue
        execution_model = str(trades.get(str(row["trade_id"]), {}).get("execution_model", ""))
        if execution_model == "HTF_OB_REACTION":
            continue
        reviewed += 1
        expected = parse_zone(str(row.get("execution_zone", "")))
        decision_time = parse_utc(str(row["as_of"]))
        root_match = re.search(
            r"M15\s+(\d{4}-\d\d-\d\d)\s+(\d\d:\d\d)",
            str(row.get("root_ob", "")),
        )
        if expected is None or root_match is None:
            print(f"{row['trade_id']} INVALID missing zone/root metadata")
            continue
        root_time = parse_utc(f"{root_match.group(1)}T{root_match.group(2)}:00Z")
        start = int(np.searchsorted(rates["time"], root_time, side="left"))
        # Historical manual ledgers used the visible M1 candle label (bar open)
        # in some rows and the information-available time (bar close) in others.
        # Include the candle carrying the recorded label, then report which
        # convention matched instead of declaring the physical FVG absent.
        end = int(np.searchsorted(rates["time"], decision_time, side="right"))
        matches: list[tuple[int, int, float, float]] = []
        direction = str(row["direction"])
        for index in range(max(start + 2, 2), end):
            left, middle, right = rates[index - 2:index + 1]
            if direction == "LONG" and float(left["high"]) < float(right["low"]):
                zone = float(left["high"]), float(right["low"])
            elif direction == "SHORT" and float(left["low"]) > float(right["high"]):
                zone = float(right["high"]), float(left["low"])
            else:
                continue
            if max(abs(zone[0] - expected[0]), abs(zone[1] - expected[1])) <= 0.011:
                matches.append((int(right["time"]), int(right["time"]) + 60, *zone))
        if matches:
            valid += 1
            latest = matches[-1]
            label_time, available_time = latest[0], latest[1]
            if available_time <= decision_time:
                timing = "AVAILABLE_AT_DECISION"
            elif label_time == decision_time:
                timing = "BAR_OPEN_LABEL_DECISION_PLUS_1M"
            else:
                timing = "TIMING_REVIEW_REQUIRED"
            print(
                f"{row['trade_id']} MATCH label={utc_text(label_time)} "
                f"available={utc_text(available_time)} "
                f"zone=[{latest[2]:.2f},{latest[3]:.2f}] "
                f"decision={row['as_of']} timing={timing}"
            )
        else:
            print(
                f"{row['trade_id']} INVALID expected=[{expected[0]:.2f},{expected[1]:.2f}] "
                f"has no matching three-candle wick gap before {row['as_of']}"
            )
    print(f"replacementFvgMatched={valid}/{reviewed}")
    return 0 if valid == reviewed else 1


if __name__ == "__main__":
    raise SystemExit(main())
