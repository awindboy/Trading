from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
GREEN = "#16a34a"
RED = "#dc2626"
ROOT_OB = "#f59e0b"
CHILD_OB = "#38bdf8"
UP = "#22c55e"
DOWN = "#ef4444"
BG = "#101418"
GRID = "#29313a"
TEXT = "#e5e7eb"


def parse_utc(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def utc_text(value: int) -> str:
    return datetime.fromtimestamp(value, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def load_rates(path: Path) -> np.ndarray:
    with np.load(path, allow_pickle=False) as payload:
        rates = payload["rates"]
    return np.sort(rates, order="time")


def aggregate(rates: np.ndarray, seconds: int) -> list[dict[str, float | int]]:
    buckets: dict[int, list[Any]] = {}
    for row in rates:
        key = int(row["time"]) // seconds * seconds
        buckets.setdefault(key, []).append(row)
    result: list[dict[str, float | int]] = []
    for key in sorted(buckets):
        rows = buckets[key]
        result.append(
            {
                "time": key,
                "open": float(rows[0]["open"]),
                "high": max(float(item["high"]) for item in rows),
                "low": min(float(item["low"]) for item in rows),
                "close": float(rows[-1]["close"]),
            }
        )
    return result


def select_timeframe(duration_seconds: int) -> tuple[str, int, int, int]:
    if duration_seconds <= 90 * 60:
        return "M1", 60, 35, 10
    if duration_seconds <= 8 * 3600:
        return "M5", 300, 30, 8
    if duration_seconds <= 24 * 3600:
        return "M15", 900, 24, 6
    return "M30", 1800, 20, 5


def scenario_records(run_dir: Path) -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in (run_dir / "decision_ledger.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    planned: dict[str, dict[str, Any]] = {}
    canceled: list[dict[str, Any]] = []
    for row in rows:
        if row["event"] == "SCENARIO_PLANNED":
            scenario = row["details"]["scenario"]
            planned[str(scenario["scenarioHash"])] = scenario
        elif (
            row["event"] == "SCENARIO_CANCELED"
            and row["details"].get("reason") == "OBJECTIVE_REACHED_BEFORE_FILL"
        ):
            canceled.append(row)
    result: list[dict[str, Any]] = []
    for row in canceled:
        scenario_hash = str(row["details"]["scenarioHash"])
        if scenario_hash not in planned:
            raise RuntimeError(f"missing planned scenario: {scenario_hash}")
        result.append(
            {
                "scenario": planned[scenario_hash],
                "canceledAtUtc": row["asOfUtc"],
                "sequence": int(row["sequence"]),
            }
        )
    return result


def candle_width(times: list[float]) -> float:
    if len(times) < 2:
        return 0.00045
    return max(0.00001, (times[1] - times[0]) * 0.68)


def draw_candles(axis: Any, bars: list[dict[str, float | int]]) -> None:
    xs = [mdates.date2num(datetime.fromtimestamp(int(bar["time"]), timezone.utc)) for bar in bars]
    width = candle_width(xs)
    for x, bar in zip(xs, bars):
        colour = UP if float(bar["close"]) >= float(bar["open"]) else DOWN
        axis.vlines(x, float(bar["low"]), float(bar["high"]), color=colour, linewidth=0.75, zorder=4)
        bottom = min(float(bar["open"]), float(bar["close"]))
        height = max(abs(float(bar["close"]) - float(bar["open"])), 0.01)
        axis.add_patch(
            Rectangle(
                (x - width / 2, bottom), width, height,
                facecolor=colour, edgecolor=colour, linewidth=0.35, zorder=5,
            )
        )


def draw_zone(
    axis: Any,
    left: float,
    right: float,
    low: float,
    high: float,
    colour: str,
    label: str,
    y_offset: float,
) -> None:
    axis.add_patch(
        Rectangle(
            (left, min(low, high)), right - left, abs(high - low),
            facecolor=colour, edgecolor=colour, linewidth=0.8,
            alpha=0.12, zorder=1,
        )
    )
    axis.text(
        left + (right - left) * 0.02,
        max(low, high) + y_offset,
        label,
        color=colour,
        fontsize=7,
        va="bottom",
        zorder=8,
    )


def bar_time(bar_id: str) -> int:
    return int(str(bar_id).split(":", 1)[1])


def style_axis(axis: Any) -> None:
    axis.set_facecolor(BG)
    axis.grid(True, color=GRID, linewidth=0.45, alpha=0.65)
    axis.tick_params(colors="#aeb8c2", labelsize=8)
    axis.yaxis.tick_right()
    axis.xaxis.set_major_formatter(
        mdates.DateFormatter("%m-%d\n%H:%M", tz=timezone.utc)
    )
    for spine in axis.spines.values():
        spine.set_color(GRID)


def draw_liquidity(
    axis: Any,
    left: float,
    right: float,
    price: float,
    label: str,
    colour: str = "#f8fafc",
) -> None:
    axis.hlines(
        price, left, right, color=colour, linewidth=1.0,
        linestyle=(0, (3, 3)), alpha=0.9, zorder=7,
    )
    axis.text(
        left + (right - left) * 0.015, price, label,
        color=colour, fontsize=7, va="bottom", zorder=9,
        bbox={"facecolor": BG, "edgecolor": "none", "alpha": 0.72, "pad": 1.5},
    )


def render_one(
    rates: np.ndarray,
    record: dict[str, Any],
    index: int,
    output_dir: Path,
) -> dict[str, Any]:
    scenario = record["scenario"]
    planned = parse_utc(str(scenario["frozenAtUtc"]))
    canceled = parse_utc(str(record["canceledAtUtc"]))
    duration = max(60, canceled - planned)
    tf, tf_seconds, before_bars, after_bars = select_timeframe(duration)
    start = planned - before_bars * tf_seconds
    end = canceled + after_bars * tf_seconds
    selected = rates[(rates["time"] >= start) & (rates["time"] < end + tf_seconds)]
    bars = aggregate(selected, tf_seconds)
    if not bars:
        raise RuntimeError(f"no chart bars for scenario {scenario['scenarioHash']}")

    direction = str(scenario["direction"]).upper()
    root = scenario["root"]
    child = scenario["finalChild"]
    objective = float(scenario["objective"]["price"])
    entry = float(child["proximal"])
    invalidation = float(child["distal"])
    risk = abs(entry - invalidation)
    planned_r = abs(objective - entry) / risk if risk else 0.0

    left = mdates.date2num(datetime.fromtimestamp(planned, timezone.utc))
    right = mdates.date2num(datetime.fromtimestamp(canceled, timezone.utc))
    child_formed = parse_utc(str(child["formedAtUtc"]))
    zone_left = mdates.date2num(
        datetime.fromtimestamp(max(start, child_formed), timezone.utc)
    )
    if right <= left:
        right = left + tf_seconds / 86400

    map_ids = [
        scenario["dealingRange"]["highBarId"],
        scenario["dealingRange"]["lowBarId"],
        scenario["mapProtectedSwing"]["barId"],
        scenario["objective"]["barId"],
        root["obBarId"],
    ]
    map_start = min(bar_time(item) for item in map_ids) - 6 * 3600
    map_end = canceled + 2 * 3600
    map_selected = rates[
        (rates["time"] >= map_start) & (rates["time"] < map_end + 3600)
    ]
    map_bars = aggregate(map_selected, 3600)
    if not map_bars:
        raise RuntimeError(f"no H1 map bars for scenario {scenario['scenarioHash']}")

    fig, (map_axis, axis) = plt.subplots(
        2, 1, figsize=(12.2, 9.2), dpi=150,
        gridspec_kw={"height_ratios": [0.92, 1.28], "hspace": 0.20},
    )
    fig.patch.set_facecolor(BG)
    style_axis(map_axis)
    style_axis(axis)

    map_x0 = mdates.date2num(datetime.fromtimestamp(map_start, timezone.utc))
    map_x1 = mdates.date2num(datetime.fromtimestamp(map_end, timezone.utc))
    draw_candles(map_axis, map_bars)
    dealing = scenario["dealingRange"]
    deal_low = float(dealing["low"])
    deal_high = float(dealing["high"])
    eq = float(dealing["eq"])
    map_axis.add_patch(
        Rectangle(
            (map_x0, deal_low), map_x1 - map_x0, eq - deal_low,
            facecolor=GREEN, edgecolor="none", alpha=0.045, zorder=0,
        )
    )
    map_axis.add_patch(
        Rectangle(
            (map_x0, eq), map_x1 - map_x0, deal_high - eq,
            facecolor=RED, edgecolor="none", alpha=0.045, zorder=0,
        )
    )
    draw_liquidity(map_axis, map_x0, map_x1, eq, f"EQ 50%  {eq:.2f}", "#94a3b8")
    draw_liquidity(
        map_axis, map_x0, map_x1, objective,
        f"OBJECTIVE LIQUIDITY  [{scenario['objective']['tf']}] "
        f"{scenario['objective']['kind']}  {objective:.2f}",
    )
    protected = scenario["mapProtectedSwing"]
    protected_price = (
        float(protected["low"]) if direction == "LONG" else float(protected["high"])
    )
    draw_liquidity(
        map_axis, map_x0, map_x1, protected_price,
        f"MAP PROTECTED SWING  {protected['barId']}  {protected_price:.2f}",
        "#c084fc",
    )
    map_root_left = mdates.date2num(
        datetime.fromtimestamp(parse_utc(str(root["formedAtUtc"])), timezone.utc)
    )
    child_map_left = mdates.date2num(
        datetime.fromtimestamp(parse_utc(str(child["formedAtUtc"])), timezone.utc)
    )
    map_values = [float(item["low"]) for item in map_bars] + [float(item["high"]) for item in map_bars]
    map_values += [deal_low, deal_high, eq, objective, protected_price, float(root["low"]), float(root["high"]), float(child["low"]), float(child["high"])]
    map_span = max(max(map_values) - min(map_values), 1.0)
    draw_zone(
        map_axis, max(map_x0, map_root_left), map_x1,
        float(root["low"]), float(root["high"]), ROOT_OB,
        f"SOURCE POI  [{root['tf']}] ROOT OB  {root['low']:.2f}-{root['high']:.2f}",
        map_span * 0.012,
    )
    draw_zone(
        map_axis, max(map_x0, child_map_left), map_x1,
        float(child["low"]), float(child["high"]), CHILD_OB,
        f"REFINED POI  [{child['tf']}] CHILD OB  {child['low']:.2f}-{child['high']:.2f}",
        map_span * 0.004,
    )
    objective_origin_x = mdates.date2num(
        datetime.fromtimestamp(bar_time(str(scenario["objective"]["barId"])), timezone.utc)
    )
    map_axis.scatter(
        [objective_origin_x], [objective], marker="D", s=30,
        facecolor=BG, edgecolor="#f8fafc", linewidth=1.0, zorder=10,
    )
    map_axis.set_xlim(map_x0, map_x1)
    map_pad = max(map_span * 0.065, 0.5)
    map_axis.set_ylim(min(map_values) - map_pad, max(map_values) + map_pad)
    map_axis.set_title(
        f"MAP H1 | {direction} {scenario['scope']} | range {deal_low:.2f}-{deal_high:.2f} | "
        f"objective source {scenario['objective']['barId']}",
        loc="left", color=TEXT, fontsize=9, pad=9,
    )

    draw_candles(axis, bars)

    if direction == "LONG":
        reward_low, reward_high = entry, objective
        risk_low, risk_high = invalidation, entry
    else:
        reward_low, reward_high = objective, entry
        risk_low, risk_high = entry, invalidation
    axis.add_patch(
        Rectangle(
            (left, min(reward_low, reward_high)), right - left, abs(reward_high - reward_low),
            facecolor=GREEN, edgecolor=GREEN, linewidth=0.9, alpha=0.18, zorder=2,
        )
    )
    axis.add_patch(
        Rectangle(
            (left, min(risk_low, risk_high)), right - left, abs(risk_high - risk_low),
            facecolor=RED, edgecolor=RED, linewidth=0.9, alpha=0.18, zorder=2,
        )
    )

    chart_range = max(float(max(bar["high"] for bar in bars)) - float(min(bar["low"] for bar in bars)), 1.0)
    offset = chart_range * 0.012
    draw_zone(
        axis, left, right, float(root["low"]), float(root["high"]), ROOT_OB,
        f"{root['tf']} ROOT OB", offset,
    )
    draw_liquidity(
        axis,
        mdates.date2num(datetime.fromtimestamp(start, timezone.utc)),
        mdates.date2num(datetime.fromtimestamp(end, timezone.utc)),
        objective,
        f"OBJECTIVE LIQUIDITY  {objective:.2f}",
    )
    draw_zone(
        axis, zone_left, right, float(child["low"]), float(child["high"]), CHILD_OB,
        f"{child['tf']} FINAL CHILD OB", offset * 0.35,
    )

    hit_x = mdates.date2num(datetime.fromtimestamp(canceled, timezone.utc))
    marker = "v" if direction == "LONG" else "^"
    axis.scatter([hit_x], [objective], marker=marker, s=42, color=TEXT, zorder=9)
    axis.text(
        left + (right - left) * 0.5,
        max(reward_low, reward_high) - chart_range * 0.025,
        f"UNFILLED PLAN  {scenario['scope']}  {planned_r:.2f}R",
        ha="center", va="top", fontsize=8, color=TEXT, zorder=9,
        bbox={"facecolor": BG, "edgecolor": "none", "alpha": 0.65, "pad": 2},
    )

    hold_minutes = duration // 60
    title = (
        f"#{index:02d} {direction} {scenario['scope']} | {tf} | "
        f"planned {utc_text(planned)} -> objective {utc_text(canceled)} | "
        f"{hold_minutes // 60}h {hold_minutes % 60}m"
    )
    axis.set_title(title, loc="left", color=TEXT, fontsize=9, pad=9)
    axis.set_xlim(
        mdates.date2num(datetime.fromtimestamp(start, timezone.utc)),
        mdates.date2num(datetime.fromtimestamp(end, timezone.utc)),
    )
    visible_values = [float(bar["low"]) for bar in bars] + [float(bar["high"]) for bar in bars]
    visible_values += [objective, entry, invalidation, float(root["low"]), float(root["high"])]
    low, high = min(visible_values), max(visible_values)
    pad = max((high - low) * 0.07, 0.5)
    axis.set_ylim(low - pad, high + pad)
    fig.subplots_adjust(left=0.045, right=0.955, top=0.965, bottom=0.065)

    filename = f"{index:02d}_{planned}_{direction.lower()}_{tf.lower()}.png"
    path = output_dir / filename
    fig.savefig(path, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    return {
        "index": index,
        "filename": filename,
        "direction": direction,
        "scope": scenario["scope"],
        "timeframe": tf,
        "plannedAtUtc": scenario["frozenAtUtc"],
        "objectiveAtUtc": record["canceledAtUtc"],
        "durationMinutes": hold_minutes,
        "root": f"{root['tf']} {root['low']:.2f}-{root['high']:.2f}",
        "child": f"{child['tf']} {child['low']:.2f}-{child['high']:.2f}",
        "entry": entry,
        "invalidation": invalidation,
        "objective": objective,
        "objectiveSource": scenario["objective"]["barId"],
        "dealingRange": f"{deal_low:.2f}-{deal_high:.2f} (EQ {eq:.2f})",
        "protectedSwing": scenario["mapProtectedSwing"]["barId"],
        "plannedR": planned_r,
    }


def write_html(output_dir: Path, records: list[dict[str, Any]]) -> Path:
    cards = []
    for item in records:
        cards.append(
            f"""
            <article>
              <a href="{html.escape(item['filename'])}"><img src="{html.escape(item['filename'])}" loading="lazy"></a>
              <div class="meta">
                <strong>#{item['index']:02d} {item['scope']} · {item['timeframe']}</strong>
                <span>{item['plannedAtUtc']} → {item['objectiveAtUtc']}</span>
                <span>MAP {item['dealingRange']} · Protected {item['protectedSwing']}</span>
                <span>Root {item['root']} · Child {item['child']}</span>
                <span>Entry {item['entry']:.2f} · Invalidation {item['invalidation']:.2f} · Objective {item['objective']:.2f} ({item['objectiveSource']}) · {item['plannedR']:.2f}R</span>
              </div>
            </article>
            """
        )
    document = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>June 2026 Week 1 Objective-First Scenarios</title>
<style>
body{{margin:0;background:#0b0f13;color:#e5e7eb;font:14px system-ui,sans-serif}}main{{max-width:1500px;margin:auto;padding:22px}}
h1{{font-size:20px;margin:0 0 6px}}p{{color:#9ca3af;margin:0 0 20px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(520px,1fr));gap:16px}}
article{{background:#13191f;border:1px solid #26313b;border-radius:6px;overflow:hidden}}img{{display:block;width:100%;height:auto}}.meta{{display:grid;gap:5px;padding:12px}}span{{color:#aeb8c2}}
@media(max-width:620px){{main{{padding:10px}}.grid{{grid-template-columns:1fr}}}}
</style></head><body><main><h1>6월 첫째 주 목표 선도달 15개 시나리오</h1>
<p>각 이미지는 상단 H1 MAP과 하단 실행 흐름을 짝지었습니다. 초록/빨강 박스는 실제 체결이 아닌 동결된 final child OB proximal 기준의 계획 geometry이며, 삼각형은 objective 도달 지점입니다.</p>
<section class="grid">{''.join(cards)}</section></main></body></html>"""
    path = output_dir / "OBJECTIVE_FIRST_REVIEW.html"
    path.write_text(document, encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    dataset = args.dataset.resolve()
    output_dir = run_dir / "objective_first_charts"
    output_dir.mkdir(parents=True, exist_ok=True)
    records = scenario_records(run_dir)
    if len(records) != 15:
        raise RuntimeError(f"expected 15 objective-first scenarios, got {len(records)}")
    rates = load_rates(dataset)
    rendered = [render_one(rates, item, index, output_dir) for index, item in enumerate(records, 1)]
    (output_dir / "index.json").write_text(
        json.dumps(rendered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    html_path = write_html(output_dir, rendered)
    print(html_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
