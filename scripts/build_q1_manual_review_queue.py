from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "mentor_q1_manual_review"
PACKETS = OUTPUT / "packets"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mentor_engine.models import BarSeries, Side
from mentor_engine.structure import analyze_structure
from mentor_engine.zones import detect_zones
from mentor_ground_truth_replay import (
    Q1_PERIOD_FROM,
    Q1_TO,
    TF_SECONDS,
    WARMUP_FROM,
    aggregate,
    iso,
    load_rates,
    render_packet,
)


def series_for(rates: np.ndarray, timeframe: str) -> BarSeries:
    bars = aggregate(rates, timeframe)
    return BarSeries(
        timeframe=timeframe,
        seconds=TF_SECONDS[timeframe],
        time=bars["time"],
        available_time=bars["available"],
        open=bars["open"],
        high=bars["high"],
        low=bars["low"],
        close=bars["close"],
        spread_points=np.ones(len(bars), dtype=float),
    )


def main() -> int:
    rates = load_rates(WARMUP_FROM, Q1_TO)
    analyses = {}
    chart_series = {}
    for timeframe in ("H4", "H1", "M30", "M15", "M5", "M1"):
        series = series_for(rates, timeframe)
        structure = analyze_structure(series)
        analyses[timeframe] = (series, structure, detect_zones(series, structure))
        chart_series[timeframe] = aggregate(rates, timeframe)

    context_zones = [
        zone
        for timeframe in ("H4", "H1", "M30", "M15")
        for zone in analyses[timeframe][2]
    ]
    candidates: list[dict[str, object]] = []
    for timeframe in ("M5", "M1"):
        series, structure, _ = analyses[timeframe]
        for event in structure.events:
            if not (Q1_PERIOD_FROM <= event.available_at < Q1_TO) or event.event_type != "CHOCH":
                continue
            sweep_side = Side.HIGH if event.direction.value == "short" else Side.LOW
            preceding = [wave for wave in structure.waves if wave.side == sweep_side and wave.confirmed_index < event.index]
            if not preceding:
                continue
            sweep_wave = preceding[-1]
            indexes = range(sweep_wave.confirmed_index + 1, event.index)
            if sweep_side == Side.HIGH:
                swept = any(series.high[index] > sweep_wave.level and series.close[index] < sweep_wave.level for index in indexes)
            else:
                swept = any(series.low[index] < sweep_wave.level and series.close[index] > sweep_wave.level for index in indexes)
            if not swept:
                continue
            price = float(series.close[event.index])
            owners = [
                zone
                for zone in context_zones
                if zone.direction == event.direction
                and zone.available_at <= event.available_at
                and zone.active_at(event.available_at)
                and zone.bottom <= price <= zone.top
            ]
            if not owners:
                continue
            candidates.append(
                {
                    "as_of": iso(int(event.available_at)),
                    "timeframe": timeframe,
                    "direction": event.direction.value,
                    "event_id": event.event_id,
                    "price": round(price, 5),
                    "sweep_wave": {
                        "id": sweep_wave.object_id,
                        "side": sweep_wave.side.value,
                        "level": round(float(sweep_wave.level), 5),
                        "available_at": iso(int(sweep_wave.available_at)),
                    },
                    "context_zones": [
                        {
                            "timeframe": zone.timeframe,
                            "kind": zone.kind.value,
                            "bottom": round(float(zone.bottom), 5),
                            "top": round(float(zone.top), 5),
                        }
                        for zone in owners
                    ],
                }
            )
    candidates.sort(key=lambda item: (item["as_of"], item["timeframe"]))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    PACKETS.mkdir(parents=True, exist_ok=True)
    for index, candidate in enumerate(candidates, start=1):
        timestamp = int(np.datetime64(candidate["as_of"]).astype("datetime64[s]").astype(int))
        name = f"{index:02d}_{candidate['as_of'].replace(':', '').replace('+00:00', 'Z')}.png"
        render_packet(chart_series, timestamp, PACKETS / name)
        candidate["packet"] = str((PACKETS / name).relative_to(ROOT)).replace("\\", "/")
    (OUTPUT / "queue.json").write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"MANUAL_REVIEW_QUEUE_OK candidates={len(candidates)} output={OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
