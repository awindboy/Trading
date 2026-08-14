from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "output" / "mentor_blind_q1" / "OPPORTUNITY_INDEX.csv"
OUTPUT = ROOT / "output" / "mentor_blind_q1" / "zoom_queue"
UTC = timezone.utc

from build_mentor_blind_q1_packets import aggregate, load_rates, render_packet


def local_candidates(day: np.ndarray, direction: str) -> list[tuple[float, int, float]]:
    candidates: list[tuple[float, int, float]] = []
    radius = 6
    horizon = 72
    for index in range(radius, max(radius, len(day) - radius)):
        left = max(0, index - radius)
        right = min(len(day), index + radius + 1)
        future = day[index + 1 : min(len(day), index + horizon + 1)]
        if not len(future):
            continue
        if direction == "LONG":
            extreme = float(day["low"][index])
            if extreme > float(np.min(day["low"][left:right])):
                continue
            excursion = float(np.max(future["high"])) - extreme
        else:
            extreme = float(day["high"][index])
            if extreme < float(np.max(day["high"][left:right])):
                continue
            excursion = extreme - float(np.min(future["low"]))
        candidates.append((excursion, index, extreme))
    return sorted(candidates, reverse=True)


def choose_episode(
    day: np.ndarray,
    direction: str,
    previous_time: int | None,
    used_times: list[int],
) -> tuple[float, int, float] | None:
    for excursion, index, extreme in local_candidates(day, direction):
        timestamp = int(day["available"][index])
        if previous_time is not None and timestamp <= previous_time + 90 * 60:
            continue
        if any(abs(timestamp - used) < 3 * 60 * 60 for used in used_times):
            continue
        return excursion, index, extreme
    return None


def main() -> int:
    rows = list(csv.DictReader(INDEX.open(encoding="utf-8", newline="")))
    q1_from = int(datetime(2025, 1, 1, tzinfo=UTC).timestamp())
    q1_to = int(datetime(2025, 4, 2, tzinfo=UTC).timestamp())
    rates = load_rates(q1_from - 120 * 24 * 60 * 60, q1_to)
    series = {timeframe: aggregate(rates, timeframe) for timeframe in ("H4", "H1", "M30", "M15", "M5", "M1")}
    m5 = series["M5"]
    OUTPUT.mkdir(parents=True, exist_ok=True)

    queue: list[dict[str, str]] = []
    event_number = 0
    for row in rows:
        if row["review_state"] != "ZOOM_REQUIRED":
            continue
        day_start = int(datetime.fromisoformat(row["date"]).replace(tzinfo=UTC).timestamp())
        day_end = day_start + 24 * 60 * 60
        mask = (m5["available"] > day_start) & (m5["available"] <= day_end)
        day = m5[mask]
        directions = row["episode_directions"].split("|")
        previous_time: int | None = None
        used_times: list[int] = []
        for direction in directions:
            chosen = choose_episode(day, direction, previous_time, used_times)
            if chosen is None:
                continue
            excursion, index, extreme = chosen
            timestamp = int(day["available"][index])
            used_times.append(timestamp)
            previous_time = timestamp
            event_number += 1
            event_id = f"Q1R{event_number:03d}"
            cutoff = min(timestamp + 90 * 60, q1_to - 1)
            chart = OUTPUT / f"{event_id}_{datetime.fromtimestamp(timestamp, tz=UTC):%Y-%m-%d_%H%M}_{direction.lower()}.png"
            render_packet(series, cutoff, chart)
            queue.append(
                {
                    "event_id": event_id,
                    "date": row["date"],
                    "direction": direction,
                    "map_read": row["map_read"],
                    "locator_extreme_time_utc": datetime.fromtimestamp(timestamp, tz=UTC).isoformat(),
                    "locator_extreme": f"{extreme:.3f}",
                    "locator_forward_excursion": f"{excursion:.3f}",
                    "chart": str(chart.relative_to(ROOT)).replace("\\", "/"),
                    "decision_state": "MANUAL_LINEAGE_REVIEW_REQUIRED",
                    "locator_warning": "RETROSPECTIVE_LOCATION_ONLY_NOT_A_TRADE_SIGNAL",
                }
            )
            print(f"RENDERED={event_number}", flush=True)

    with (OUTPUT / "zoom_queue.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(queue[0]) if queue else [])
        if queue:
            writer.writeheader()
            writer.writerows(queue)
    print(f"ZOOM_QUEUE={len(queue)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
