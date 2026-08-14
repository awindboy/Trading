from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mentor_engine.data import build_timeframes, load_m1_npz
from mentor_engine.structure import analyze_structure


RUN_DIR = ROOT / "output" / "mentor_engine" / "GOLD_2025_Q1_FINAL"
DATASET = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
OUTPUT_DIR = RUN_DIR / "position_box_charts"
UTC = timezone.utc

BG = "#080c12"
GRID = "#263241"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
BULL = "#5eead4"
BEAR = "#f87171"
RISK = "#ef4444"
REWARD = "#10b981"
SWEEP = "#fbbf24"
ZONE = "#38bdf8"
LIQUIDITY = "#c084fc"


def timestamp(value: str) -> int:
    return int(datetime.fromisoformat(value).timestamp())


def utc_text(value: int) -> str:
    return datetime.fromtimestamp(value, tz=UTC).strftime("%Y-%m-%d %H:%M")


def compact_id(value: str) -> str:
    parts = value.split(":")
    if ":liquidity:" in value and len(parts) >= 5:
        return f"{parts[0]} {parts[2]} {parts[3]}"
    if ":zone:" in value and len(parts) >= 4:
        return f"{parts[0]} {parts[2]}"
    if ":structure:" in value and len(parts) >= 3:
        return f"{parts[0]} {parts[2]}"
    return value[:40]


def load_records() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    with (RUN_DIR / "trades.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        trades = [row for row in csv.DictReader(handle) if row["result"] in {"SL", "TP"}]
    scenarios: dict[str, dict[str, Any]] = {}
    orders: dict[str, dict[str, Any]] = {}
    with (RUN_DIR / "ledger.jsonl").open("r", encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            if item.get("recordType") == "scenario":
                scenarios[item["scenario_id"]] = item
            elif item.get("recordType") == "order":
                orders[item["scenario_id"]] = item
    return trades, scenarios, orders


def nearest_index(series: Any, value: int) -> int:
    return int(np.clip(np.searchsorted(series.available_time, value, side="left"), 0, len(series) - 1))


def bounded_window(series: Any, start: int, end: int, pre: int, post: int, max_bars: int | None = None) -> tuple[int, int]:
    left = max(0, nearest_index(series, start) - pre)
    right = min(len(series), nearest_index(series, end) + post + 1)
    if max_bars and right - left > max_bars:
        center = (nearest_index(series, start) + nearest_index(series, end)) // 2
        left = max(0, center - max_bars // 2)
        right = min(len(series), left + max_bars)
        left = max(0, right - max_bars)
    return left, right


def draw_candles(axis: Any, series: Any, left: int, right: int) -> None:
    for x, index in enumerate(range(left, right)):
        colour = BULL if series.close[index] >= series.open[index] else BEAR
        axis.vlines(x, series.low[index], series.high[index], color=colour, linewidth=0.65, zorder=3)
        bottom = min(series.open[index], series.close[index])
        height = max(abs(series.close[index] - series.open[index]), 1e-6)
        axis.add_patch(Rectangle((x - 0.34, bottom), 0.68, height, facecolor=colour, edgecolor=colour, linewidth=0.4, zorder=4))
    axis.set_xlim(-1, max(2, right - left))
    count = right - left
    if count > 1:
        ticks = np.unique(np.linspace(0, count - 1, min(6, count), dtype=int))
        labels = [datetime.fromtimestamp(int(series.available_time[left + i]), tz=UTC).strftime("%m-%d\n%H:%M") for i in ticks]
        axis.set_xticks(ticks, labels)


def x_for(series: Any, left: int, right: int, value: int) -> float | None:
    index = int(np.searchsorted(series.available_time, value, side="left"))
    if index < left or index >= right:
        return None
    return float(index - left)


def draw_position_box(axis: Any, series: Any, left: int, right: int, trade: dict[str, Any], guarantee: bool = False) -> None:
    entry_time = timestamp(trade["entry_time_utc"])
    exit_time = timestamp(trade["exit_time_utc"])
    x0 = x_for(series, left, right, entry_time)
    x1 = x_for(series, left, right, exit_time)
    if x0 is None or x1 is None:
        if not guarantee:
            return
        x0, x1 = 0.0, float(right - left - 1)
    x1 = max(x1, x0 + 1.0)
    width = x1 - x0
    entry = float(trade["entry"])
    stop = float(trade["stop_loss"])
    target = float(trade["take_profit"])
    risk_low, risk_high = sorted((entry, stop))
    reward_low, reward_high = sorted((entry, target))
    axis.add_patch(Rectangle((x0, risk_low), width, risk_high - risk_low, facecolor=RISK,
                             edgecolor="#fb7185", linewidth=1.0, alpha=0.20, zorder=1))
    axis.add_patch(Rectangle((x0, reward_low), width, reward_high - reward_low, facecolor=REWARD,
                             edgecolor="#34d399", linewidth=1.0, alpha=0.20, zorder=1))


def reconstruct_zone(zone_id: str, series_by_tf: dict[str, Any]) -> dict[str, Any] | None:
    parts = zone_id.split(":")
    if len(parts) < 6 or parts[1] != "zone":
        return None
    timeframe, kind, direction = parts[0], parts[2], parts[3]
    try:
        origin_time = int(parts[4])
    except ValueError:
        return None
    series = series_by_tf[timeframe]
    origin = int(np.searchsorted(series.time, origin_time, side="left"))
    if origin >= len(series) or int(series.time[origin]) != origin_time:
        return None
    if kind == "FVG":
        confirmed = min(origin + 2, len(series) - 1)
        if direction == "long":
            bottom, top = float(series.high[origin]), float(series.low[confirmed])
        else:
            bottom, top = float(series.high[confirmed]), float(series.low[origin])
    else:
        bottom, top = float(series.low[origin]), float(series.high[origin])
        confirmed = min(origin + 2, len(series) - 1)
        if "structure" in parts:
            position = parts.index("structure")
            if position + 2 < len(parts):
                event_time = int(parts[position + 2])
                event_index = int(np.searchsorted(series.time, event_time, side="left"))
                if event_index < len(series) and int(series.time[event_index]) == event_time:
                    confirmed = event_index
    if top <= bottom:
        return None
    consumed = None
    for index in range(confirmed + 1, len(series)):
        if direction == "long" and float(series.low[index]) <= bottom:
            consumed = int(series.available_time[index])
            break
        if direction == "short" and float(series.high[index]) >= top:
            consumed = int(series.available_time[index])
            break
    return {
        "id": zone_id,
        "timeframe": timeframe,
        "kind": kind,
        "direction": direction,
        "origin": int(series.time[origin]),
        "available": int(series.available_time[confirmed]),
        "consumed": consumed,
        "bottom": bottom,
        "top": top,
    }


def projected_x(series: Any, left: int, right: int, value: int) -> float:
    index = int(np.searchsorted(series.available_time, value, side="left"))
    return float(np.clip(index - left, 0, max(1, right - left - 1)))


def draw_zone(axis: Any, panel_series: Any, left: int, right: int, zone: dict[str, Any], role: str) -> None:
    panel_start = int(panel_series.available_time[left])
    panel_end = int(panel_series.available_time[right - 1])
    zone_end = int(zone["consumed"] or panel_end)
    start_time = max(int(zone["available"]), panel_start)
    end_time = min(zone_end, panel_end)
    if end_time <= start_time:
        return
    x0 = projected_x(panel_series, left, right, start_time)
    x1 = max(projected_x(panel_series, left, right, end_time), x0 + 1.0)
    colours = {
        "FVG": ("#2563eb", "#60a5fa"),
        "FVG_ORIGIN_OB": ("#d97706", "#fbbf24"),
        "LAST_OPPOSITE_OB": ("#7c3aed", "#c4b5fd"),
    }
    fill, edge = colours.get(zone["kind"], ("#475569", "#cbd5e1"))
    axis.add_patch(Rectangle((x0, zone["bottom"]), x1 - x0, zone["top"] - zone["bottom"],
                             facecolor=fill, edgecolor=edge, linewidth=1.1, alpha=0.20, zorder=2))
    label = f"{role} · {zone['timeframe']} {zone['kind'].replace('LAST_OPPOSITE_', '')}"
    axis.text((x0 + x1) / 2, (zone["bottom"] + zone["top"]) / 2, label,
              color="#f8fafc", fontsize=7.0, ha="center", va="center",
              bbox={"facecolor": BG, "edgecolor": edge, "alpha": 0.72, "pad": 1.5}, zorder=8)


def event_start_time(event: Any) -> int:
    try:
        return int(event.broken_swing_id.rsplit(":", 1)[-1])
    except (ValueError, AttributeError):
        return int(event.occurred_at)


def draw_structure_line(axis: Any, panel_series: Any, left: int, right: int, event: Any, emphasized: bool = False) -> None:
    start = event_start_time(event)
    end = int(event.available_at)
    panel_start = int(panel_series.available_time[left])
    panel_end = int(panel_series.available_time[right - 1])
    if end < panel_start or start > panel_end:
        return
    x0 = projected_x(panel_series, left, right, max(start, panel_start))
    x1 = projected_x(panel_series, left, right, min(end, panel_end))
    colour = "#34d399" if event.direction.value == "long" else "#fb7185"
    axis.hlines(event.broken_level, x0, max(x1, x0 + 1), color=colour,
                linewidth=1.25 if emphasized else 0.85, linestyle=(0, (5, 3)), alpha=0.95, zorder=6)
    axis.text((x0 + max(x1, x0 + 1)) / 2, event.broken_level,
              "CHoCH" if event.event_type == "CHOCH" else "BOS",
              color=colour, fontsize=7.2, ha="center",
              va="bottom" if event.direction.value == "long" else "top", zorder=8)


def draw_source_liquidity(axis: Any, panel_series: Any, left: int, right: int, scenario: dict[str, Any]) -> None:
    parts = scenario["source_pool_id"].split(":")
    side = "high" if ":high:" in scenario["source_pool_id"] else "low"
    try:
        wave_position = parts.index("wave")
        start = int(parts[wave_position + 2])
    except (ValueError, IndexError):
        start = int(scenario["created_at"])
    end = int(scenario["created_at"])
    panel_start = int(panel_series.available_time[left])
    panel_end = int(panel_series.available_time[right - 1])
    if end < panel_start or start > panel_end:
        return
    x0 = projected_x(panel_series, left, right, max(start, panel_start))
    x1 = projected_x(panel_series, left, right, min(end, panel_end))
    level = float(scenario["source_price"])
    axis.hlines(level, x0, max(x1, x0 + 1), color=LIQUIDITY, linewidth=1.0,
                linestyle=(0, (4, 3)), zorder=6)
    axis.text((x0 + max(x1, x0 + 1)) / 2, level, "BSL" if side == "high" else "SSL",
              color="#d8b4fe", fontsize=7.2, ha="center",
              va="bottom" if side == "high" else "top", zorder=8)
    sweep_x = x_for(panel_series, left, right, int(scenario["created_at"]))
    if sweep_x is not None:
        axis.text(sweep_x, level, "BS" if side == "high" else "SS", color=SWEEP,
                  fontsize=7.2, ha="center", va="bottom" if side == "high" else "top", zorder=9)


def style_axis(axis: Any, title: str) -> None:
    axis.set_facecolor(BG)
    axis.set_title(title, loc="left", fontsize=10, color=TEXT, fontweight="bold", pad=9)
    axis.grid(color=GRID, alpha=0.32, linewidth=0.55)
    axis.tick_params(colors=MUTED, labelsize=7)
    axis.yaxis.tick_right()
    for spine in axis.spines.values():
        spine.set_color(GRID)


def adaptive_hold_timeframe(minutes: int) -> str:
    if minutes <= 180:
        return "M1"
    if minutes <= 1440:
        return "M5"
    if minutes <= 5760:
        return "M15"
    return "M30"


def render_trade(
    sequence: int,
    trade: dict[str, Any],
    scenario: dict[str, Any],
    order: dict[str, Any],
    series_by_tf: dict[str, Any],
    structure_by_tf: dict[str, Any],
) -> Path:
    sweep_time = int(scenario["created_at"])
    order_time = int(order["created_at"])
    entry_time = timestamp(trade["entry_time_utc"])
    exit_time = timestamp(trade["exit_time_utc"])
    hold_minutes = int(float(trade["holding_minutes"]))
    panels = [
        (trade["map_timeframe"], sweep_time, exit_time, 28, 18, 260, "MAP"),
        (trade["context_timeframe"], sweep_time, order_time, 55, 75, 190, "CONTEXT"),
        (trade["trigger_timeframe"], order_time, order_time, 65, 90, 180, "TRIGGER"),
        (adaptive_hold_timeframe(hold_minutes), entry_time, exit_time, 18, 18, 260, "HOLD"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(15, 9), constrained_layout=True)
    axes = axes.ravel()
    source_zones = [
        zone
        for zone_id in scenario["source_zone_ids"]
        if (zone := reconstruct_zone(zone_id, series_by_tf)) is not None
    ]
    entry_zone = reconstruct_zone(trade["entry_zone_id"], series_by_tf)
    trigger_events = {
        event.event_id: event
        for event in structure_by_tf[trade["trigger_timeframe"]].events
    }
    trigger_event = trigger_events.get(trade["trigger_event_id"])
    for axis, (timeframe, start, end, pre, post, cap, role) in zip(axes, panels):
        series = series_by_tf[timeframe]
        left, right = bounded_window(series, start, end, pre, post, cap)
        draw_candles(axis, series, left, right)
        if role in {"MAP", "CONTEXT"}:
            draw_source_liquidity(axis, series, left, right, scenario)
            for zone in source_zones:
                draw_zone(axis, series, left, right, zone, "SOURCE")
            visible_events = [
                event
                for event in structure_by_tf[timeframe].events
                if int(series.available_time[left]) <= event.available_at <= int(series.available_time[right - 1])
                and event.available_at <= exit_time
            ][-3:]
            for event in visible_events:
                draw_structure_line(axis, series, left, right, event)
        elif role == "TRIGGER":
            if entry_zone is not None:
                draw_zone(axis, series, left, right, entry_zone, "TRIGGER")
            if trigger_event is not None:
                draw_structure_line(axis, series, left, right, trigger_event, emphasized=True)
        if role == "MAP":
            draw_position_box(axis, series, left, right, trade)
        if role == "HOLD":
            draw_position_box(axis, series, left, right, trade, guarantee=True)
            values = [float(trade[k]) for k in ("entry", "stop_loss", "take_profit")]
            candle_low = float(np.min(series.low[left:right]))
            candle_high = float(np.max(series.high[left:right]))
            low, high = min(values + [candle_low]), max(values + [candle_high])
            margin = max((high - low) * 0.08, 0.5)
            axis.set_ylim(low - margin, high + margin)
        style_axis(axis, f"{role} · {timeframe}")
    source_label = compact_id(trade["source_pool_id"])
    zone_label = ", ".join(compact_id(item) for item in trade["source_zone_ids"].split("|") if item)
    planned_r = abs((float(trade["take_profit"]) - float(trade["entry"])) / (float(trade["entry"]) - float(trade["stop_loss"])))
    result_colour = "#34d399" if trade["result"] == "TP" else "#fb7185"
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        f"#{sequence:02d} {utc_text(entry_time)} UTC · {trade['direction'].upper()} · {trade['scope']} · "
        f"{trade['result']} · {hold_minutes // 60}h {hold_minutes % 60}m · planned {planned_r:.2f}R",
        color=result_colour, fontsize=14, fontweight="bold", y=1.02,
    )
    fig.text(0.5, -0.012,
             f"Evidence: {source_label} sweep → {zone_label} → {compact_id(trade['trigger_event_id'])} → {compact_id(trade['entry_zone_id'])}",
             ha="center", va="bottom", color=MUTED, fontsize=9)
    filename = f"{sequence:02d}_{trade['entry_time_utc'][:10]}_{trade['direction']}_{trade['result']}.png"
    path = OUTPUT_DIR / filename
    fig.savefig(path, dpi=160, facecolor=BG, bbox_inches="tight", pad_inches=0.18)
    plt.close(fig)
    return path


def make_contact_sheet(paths: list[Path], start_number: int, output: Path) -> None:
    thumb_w, thumb_h = 760, 460
    margin = 22
    canvas = Image.new("RGB", (thumb_w * 2 + margin * 3, thumb_h * 2 + margin * 3), (8, 12, 18))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    for slot, path in enumerate(paths):
        image = Image.open(path).convert("RGB")
        # Full forensic charts remain available separately; the sheet is a quick index.
        image.thumbnail((thumb_w, thumb_h - 30), Image.Resampling.LANCZOS)
        x = margin + (slot % 2) * (thumb_w + margin)
        y = margin + (slot // 2) * (thumb_h + margin)
        canvas.paste(image, (x + (thumb_w - image.width) // 2, y + 28))
        draw.text((x, y), f"TRADE #{start_number + slot:02d}", fill=(226, 232, 240), font=font)
    canvas.save(output, quality=94)


def write_analysis(trades: list[dict[str, Any]], paths: list[Path]) -> None:
    summary = json.loads((RUN_DIR / "summary.json").read_text(encoding="utf-8"))
    funnel = summary["funnel"]
    total_minutes = sum(int(float(item["holding_minutes"])) for item in trades)
    lines = [
        "# 2025 Q1 Mentor Engine 포지션 박스 전수 분석",
        "",
        "## 왜 3개월 동안 16회뿐이었나",
        "",
        f"- 거래 대상 sweep: {funnel['eligibleLiquiditySweeps']:,}건",
        f"- context 이전 거절: {funnel['contextRejections']:,}건 (81.2%)",
        f"- 유효 context: {funnel['contexts']:,}건 (sweep의 18.8%)",
        f"- 주문 / 체결: {funnel['orders']}건 / {funnel['fills']}건 (sweep의 1.5% / 1.4%)",
        f"- 가장 큰 1차 병목: 유동성과 zone의 유일한 인과관계 없음 {funnel['contextRejectionReasons']['NO_UNIQUE_LIQUIDITY_ZONE_CONTEXT']}건",
        f"- 가장 큰 2차 병목: trigger 전에 source excursion 무효화 {funnel['scenarioRejectionReasons']['SOURCE_EXCURSION_INVALIDATED']}건",
        f"- PD 절반 위치 불일치: {funnel['contextRejectionReasons']['OUTSIDE_MENTOR_PD_HALF']}건",
        f"- 반응 구간 종료 전에 trigger 미완성: {funnel['scenarioRejectionReasons']['SOURCE_REACTION_EPISODE_ENDED']}건",
        "",
        "차트에 FVG/OB가 적어서가 아니다. 현재 계약은 같은 excursion 안에서 유동성 sweep, source zone, CHoCH가 만든 entry zone, 아직 소진되지 않은 objective가 모두 연결돼야 한다. 이 중 하나라도 모호하거나 trigger가 늦으면 거래를 버렸기 때문에 1,135개 sweep이 16개 체결로 줄었다.",
        "",
        "## 왜 승률이 12.5%였나",
        "",
        "- TP 2건, SL 14건이다.",
        "- Q1 GOLD는 2,634.02에서 3,123.74로 18.59% 상승했는데 short가 11건이었고 그중 10건이 손실이었다. 내부 하락 회전을 외부 상승 추세의 실제 반전으로 과대평가한 거래가 많았다.",
        "- 16건 중 15건이 M1 trigger였고 그중 13건이 손실이었다. M1 CHoCH가 source context에 귀속되었다는 사실만 확인했을 뿐, objective까지 delivery가 지속될 우위까지 확인하지 못했다.",
        "- INTERNAL_ROTATION은 9건 중 1승, EXTERNAL_CONTINUATION은 7건 중 1승이다. 한 가지 scope 필터 문제가 아니라 map 방향, source owner, trigger 의미를 연결하는 시나리오 선택 자체가 실패했다.",
        "- 계획 손익비는 0.35R부터 13.87R까지 지나치게 넓었다. 큰 목표는 진입 직후 방향 오류를 보상하지 못했고, 1R 미만 내부 목표는 이 매매법의 고손익비 장점도 살리지 못했다.",
        "- SL 거래의 보유시간 중앙값은 60분이다. 즉 대부분은 긴 시간 뒤 우연히 실패한 것이 아니라, 진입 근처에서 시나리오 방향 또는 LTF trigger 해석이 빠르게 틀렸다는 뜻이다.",
        "",
        f"16건의 총 보유시간은 {total_minutes // 60}시간 {total_minutes % 60}분이다.",
        "",
        "## 거래별 근거와 차트",
        "",
        "각 차트는 좌상단 지도 구조, 우상단 sweep/context, 좌하단 진입 CHoCH, 우하단 전체 보유 구간이다. 빨간 영역은 SL 위험, 초록 영역은 TP 보상이다.",
        "",
        "| # | 진입 UTC | 방향 | 범위 | TF 계보 | 결과 | 보유 | 계획 R | 근거 | 차트 |",
        "|---:|---|---|---|---|---:|---:|---:|---|---|",
    ]
    for number, (trade, path) in enumerate(zip(trades, paths), start=1):
        minutes = int(float(trade["holding_minutes"]))
        risk = abs(float(trade["entry"]) - float(trade["stop_loss"]))
        planned_r = abs(float(trade["take_profit"]) - float(trade["entry"])) / risk
        evidence = f"{compact_id(trade['source_pool_id'])} / {compact_id(trade['entry_zone_id'])}"
        lines.append(
            f"| {number} | {trade['entry_time_utc'][:16].replace('T', ' ')} | {trade['direction']} | {trade['scope']} | "
            f"{trade['map_timeframe']}→{trade['context_timeframe']}→{trade['trigger_timeframe']} | {trade['result']} | "
            f"{minutes // 60}h {minutes % 60}m | {planned_r:.2f}R | {evidence} | [{path.name}](position_box_charts/{path.name}) |"
        )
    (RUN_DIR / "POSITION_BOX_ANALYSIS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUTPUT_DIR.glob("*.png"):
        old.unlink()
    trades, scenarios, orders = load_records()
    # Match the Q1 replay warm-up so structure event IDs remain identical.
    start = int(datetime(2024, 12, 1, tzinfo=UTC).timestamp())
    end = max(timestamp(item["exit_time_utc"]) for item in trades) + 3 * 86400
    m1, _ = load_m1_npz(DATASET, start=start, end=end)
    series_by_tf = build_timeframes(m1)
    structure_by_tf = {
        timeframe: analyze_structure(series)
        for timeframe, series in series_by_tf.items()
    }
    paths = []
    for number, trade in enumerate(trades, start=1):
        scenario = scenarios[trade["scenario_id"]]
        order = orders[trade["scenario_id"]]
        paths.append(render_trade(number, trade, scenario, order, series_by_tf, structure_by_tf))
    for index in range(0, len(paths), 4):
        make_contact_sheet(paths[index:index + 4], index + 1, OUTPUT_DIR / f"overview_{index + 1:02d}_{min(index + 4, len(paths)):02d}.jpg")
    write_analysis(trades, paths)
    print(f"RENDERED={len(paths)}")
    print(f"OUTPUT={OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
