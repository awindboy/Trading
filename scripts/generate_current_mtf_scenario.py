from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge.mt5_bridge import as_dict, as_float, as_int, initialize_mt5, mt5, timeframe_value  # noqa: E402
from scripts.journal_chart_liquidity import build_liquidity_profile  # noqa: E402

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception as exc:
    raise SystemExit(f"Pillow is required: {exc}")


TIMEFRAMES = ("H4", "H1", "M15", "M5", "M1")
TF_BARS = {"H4": 180, "H1": 220, "M15": 240, "M5": 260, "M1": 300}
TF_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "H1": 60, "H4": 240}
OUT_DIR = ROOT / "output" / "current_chart_scenario"


@dataclass
class Bar:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def aliases(symbol: str) -> list[str]:
    normalized = symbol.strip().upper()
    result = [normalized]
    if normalized in {"GOLD", "XAUUSD"}:
        result += ["GOLD", "XAUUSD", "GOLD.", "XAUUSD.", "GOLD#"]
    return list(dict.fromkeys(result))


def fetch_bars(symbol: str, timeframe: str, count: int) -> tuple[str, list[Bar]]:
    if mt5 is None:
        raise RuntimeError("MetaTrader5 package is not available.")
    initialize_mt5()
    last_error = ""
    for candidate in aliases(symbol):
        try:
            mt5.symbol_select(candidate, True)
            rates = mt5.copy_rates_from_pos(candidate, timeframe_value(timeframe), 0, count)
        except Exception as exc:
            last_error = str(exc)
            continue
        if rates is None or len(rates) == 0:
            last_error = str(getattr(mt5, "last_error", lambda: "")())
            continue
        bars: list[Bar] = []
        for rate in rates:
            row = as_dict(rate)
            bars.append(
                Bar(
                    time=datetime.fromtimestamp(as_int(row.get("time")), tz=timezone.utc).astimezone(),
                    open=as_float(row.get("open")),
                    high=as_float(row.get("high")),
                    low=as_float(row.get("low")),
                    close=as_float(row.get("close")),
                    volume=as_float(row.get("tick_volume")),
                )
            )
        return candidate, bars
    raise RuntimeError(f"No MT5 bars for {symbol} {timeframe}: {last_error}")


def fetch_tick(symbol: str) -> dict[str, float]:
    if mt5 is None:
        return {}
    for candidate in aliases(symbol):
        mt5.symbol_select(candidate, True)
        tick = mt5.symbol_info_tick(candidate)
        if tick:
            row = as_dict(tick)
            return {"bid": as_float(row.get("bid")), "ask": as_float(row.get("ask"))}
    return {}


def pivots(bars: list[Bar], length: int = 4) -> tuple[list[int], list[int]]:
    highs: list[int] = []
    lows: list[int] = []
    for i in range(length, len(bars) - length):
        window = bars[i - length : i + length + 1]
        if bars[i].high == max(bar.high for bar in window):
            highs.append(i)
        if bars[i].low == min(bar.low for bar in window):
            lows.append(i)
    return highs, lows


def is_mitigated(bars: list[Bar], zone: dict[str, Any], direction: str) -> bool:
    start = as_int(zone["index"]) + 1
    bottom = as_float(zone["bottom"])
    top = as_float(zone["top"])
    for bar in bars[start:]:
        if direction == "bullish" and bar.low <= bottom:
            return True
        if direction == "bearish" and bar.high >= top:
            return True
    return False


def fvg_zones(bars: list[Bar]) -> list[dict[str, Any]]:
    zones: list[dict[str, Any]] = []
    for i in range(2, len(bars)):
        if bars[i].low > bars[i - 2].high:
            zones.append(
                {
                    "type": "bullish",
                    "kind": "FVG",
                    "index": i,
                    "start": i - 2,
                    "top": bars[i].low,
                    "bottom": bars[i - 2].high,
                }
            )
        if bars[i].high < bars[i - 2].low:
            zones.append(
                {
                    "type": "bearish",
                    "kind": "FVG",
                    "index": i,
                    "start": i - 2,
                    "top": bars[i - 2].low,
                    "bottom": bars[i].high,
                }
            )
    for zone in zones:
        zone["mitigated"] = is_mitigated(bars, zone, str(zone["type"]))
        zone["mid"] = (as_float(zone["top"]) + as_float(zone["bottom"])) / 2
        zone["size"] = abs(as_float(zone["top"]) - as_float(zone["bottom"]))
    return zones


def ob_zones(bars: list[Bar]) -> list[dict[str, Any]]:
    zones: list[dict[str, Any]] = []
    atr = average_range(bars[-80:])
    displacement = max(atr * 1.2, 0.01)
    for i in range(3, len(bars) - 3):
        candle = bars[i]
        next_high = max(bar.high for bar in bars[i + 1 : i + 4])
        next_low = min(bar.low for bar in bars[i + 1 : i + 4])
        if candle.close < candle.open and next_high - candle.high >= displacement:
            zones.append({"type": "bullish", "kind": "OB", "index": i, "start": i, "top": candle.high, "bottom": candle.low})
        if candle.close > candle.open and candle.low - next_low >= displacement:
            zones.append({"type": "bearish", "kind": "OB", "index": i, "start": i, "top": candle.high, "bottom": candle.low})
    for zone in zones:
        zone["mitigated"] = is_mitigated(bars, zone, str(zone["type"]))
        zone["mid"] = (as_float(zone["top"]) + as_float(zone["bottom"])) / 2
        zone["size"] = abs(as_float(zone["top"]) - as_float(zone["bottom"]))
    return zones


def average_range(bars: list[Bar]) -> float:
    if not bars:
        return 0.0
    return sum(bar.high - bar.low for bar in bars) / len(bars)


def recent_sweeps(bars: list[Bar], highs: list[int], lows: list[int]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    lookback_start = max(0, len(bars) - 80)
    for i in range(lookback_start, len(bars)):
        prev_highs = [p for p in highs if p < i]
        prev_lows = [p for p in lows if p < i]
        if prev_highs:
            p = prev_highs[-1]
            level = bars[p].high
            if bars[i].high > level and bars[i].close < level:
                events.append({"type": "BSL sweep", "index": i, "level": level})
        if prev_lows:
            p = prev_lows[-1]
            level = bars[p].low
            if bars[i].low < level and bars[i].close > level:
                events.append({"type": "SSL sweep", "index": i, "level": level})
    return events[-4:]


def structure_breaks(bars: list[Bar], highs: list[int], lows: list[int]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    lookback_start = max(0, len(bars) - 90)
    for i in range(lookback_start, len(bars)):
        prev_highs = [p for p in highs if p < i]
        prev_lows = [p for p in lows if p < i]
        if prev_highs:
            level = bars[prev_highs[-1]].high
            if bars[i].close > level:
                events.append({"type": "BOS", "direction": "bullish", "index": i, "level": level})
        if prev_lows:
            level = bars[prev_lows[-1]].low
            if bars[i].close < level:
                events.append({"type": "BOS", "direction": "bearish", "index": i, "level": level})
    return events[-5:]


def trend_from_pivots(bars: list[Bar], highs: list[int], lows: list[int]) -> str:
    recent_highs = highs[-3:]
    recent_lows = lows[-3:]
    if len(recent_highs) >= 2 and len(recent_lows) >= 2:
        high_up = bars[recent_highs[-1]].high > bars[recent_highs[-2]].high
        low_up = bars[recent_lows[-1]].low > bars[recent_lows[-2]].low
        high_down = bars[recent_highs[-1]].high < bars[recent_highs[-2]].high
        low_down = bars[recent_lows[-1]].low < bars[recent_lows[-2]].low
        if high_up and low_up:
            return "bullish"
        if high_down and low_down:
            return "bearish"
    closes = [bar.close for bar in bars[-30:]]
    if len(closes) >= 2:
        slope = closes[-1] - closes[0]
        threshold = average_range(bars[-30:]) * 1.2
        if slope > threshold:
            return "bullish"
        if slope < -threshold:
            return "bearish"
    return "balanced"


def analyze_tf(timeframe: str, bars: list[Bar], current_price: float) -> dict[str, Any]:
    highs, lows = pivots(bars)
    liquidity = build_liquidity_profile(bars, current_price, pivot_len=4)
    range_high = liquidity.get("rangeHigh") if isinstance(liquidity.get("rangeHigh"), dict) else {}
    range_low = liquidity.get("rangeLow") if isinstance(liquidity.get("rangeLow"), dict) else {}
    high_level = as_float(range_high.get("level")) or max((bars[idx].high for idx in highs[-12:]), default=max(bar.high for bar in bars[-80:]))
    low_level = as_float(range_low.get("level")) or min((bars[idx].low for idx in lows[-12:]), default=min(bar.low for bar in bars[-80:]))
    eq = (high_level + low_level) / 2
    location = "premium" if current_price > eq else "discount"
    zones = fvg_zones(bars) + ob_zones(bars)
    active = [z for z in zones if not z.get("mitigated")]
    near = sorted(active, key=lambda z: abs(as_float(z["mid"]) - current_price))[:8]
    above = sorted([z for z in active if as_float(z["bottom"]) > current_price], key=lambda z: as_float(z["bottom"]))[:4]
    below = sorted([z for z in active if as_float(z["top"]) < current_price], key=lambda z: as_float(z["top"]), reverse=True)[:4]
    return {
        "timeframe": timeframe,
        "bars": len(bars),
        "trend": trend_from_pivots(bars, highs, lows),
        "location": location,
        "rangeHigh": high_level,
        "rangeLow": low_level,
        "eq": eq,
        "rangeHighMeta": range_high,
        "rangeLowMeta": range_low,
        "bsl": (liquidity.get("relevantBsl") or [])[:4],
        "ssl": (liquidity.get("relevantSsl") or [])[:4],
        "liquidity": liquidity,
        "zonesNear": near,
        "zonesAbove": above,
        "zonesBelow": below,
        "sweeps": recent_sweeps(bars, highs, lows),
        "breaks": structure_breaks(bars, highs, lows),
        "lastClose": bars[-1].close,
    }


def price_to_y(price: float, high: float, low: float, top: int, height: int) -> int:
    if math.isclose(high, low):
        return top + height // 2
    return int(top + (high - price) / (high - low) * height)


def index_to_x(index: int, count: int, left: int, width: int) -> int:
    if count <= 1:
        return left + width // 2
    return int(left + index / (count - 1) * width)


def dashed_line(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], fill: tuple[int, int, int, int], width: int = 1, dash: int = 8) -> None:
    x1, y1, x2, y2 = xy
    length = math.hypot(x2 - x1, y2 - y1)
    if length <= 0:
        return
    dx = (x2 - x1) / length
    dy = (y2 - y1) / length
    pos = 0.0
    while pos < length:
        end = min(pos + dash, length)
        draw.line((x1 + dx * pos, y1 + dy * pos, x1 + dx * end, y1 + dy * end), fill=fill, width=width)
        pos += dash * 2


def label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fill: tuple[int, int, int, int], text_fill: tuple[int, int, int, int], size: int = 12) -> None:
    x, y = xy
    fnt = font(size, True)
    bbox = draw.textbbox((x, y), text, font=fnt)
    draw.rounded_rectangle([bbox[0] - 5, bbox[1] - 3, bbox[2] + 5, bbox[3] + 4], radius=4, fill=fill)
    draw.text((x, y), text, font=fnt, fill=text_fill)


def draw_panel(
    draw: ImageDraw.ImageDraw,
    bars: list[Bar],
    analysis: dict[str, Any],
    box: tuple[int, int, int, int],
    title: str,
    current_price: float,
    scenario_zones: list[dict[str, Any]],
    target_levels: list[dict[str, Any]],
) -> None:
    left, top, right, bottom = box
    panel_w = right - left
    panel_h = bottom - top
    draw.rounded_rectangle([left, top, right, bottom], radius=10, fill=(7, 12, 18, 255), outline=(40, 52, 66, 255), width=1)
    draw.text((left + 14, top + 10), title, font=font(18, True), fill=(226, 232, 240, 255))

    chart_top = top + 48
    chart_bottom = bottom - 34
    chart_h = chart_bottom - chart_top
    chart_left = left + 24
    chart_right = right - 84
    chart_w = chart_right - chart_left
    lows = [bar.low for bar in bars]
    highs = [bar.high for bar in bars]
    zone_prices = []
    for zone in scenario_zones:
        zone_prices += [as_float(zone["top"]), as_float(zone["bottom"])]
    for level in target_levels:
        zone_prices.append(as_float(level["level"]))
    high = max(highs + zone_prices + [current_price])
    low = min(lows + zone_prices + [current_price])
    pad = max((high - low) * 0.08, 0.01)
    high += pad
    low -= pad

    for i in range(1, 5):
        y = chart_top + chart_h * i // 5
        draw.line([chart_left, y, chart_right, y], fill=(28, 37, 49, 255), width=1)

    step = chart_w / max(len(bars), 1)
    candle_w = max(2, min(6, int(step * 0.48)))
    for i, bar in enumerate(bars):
        x = index_to_x(i, len(bars), chart_left, chart_w)
        yh = price_to_y(bar.high, high, low, chart_top, chart_h)
        yl = price_to_y(bar.low, high, low, chart_top, chart_h)
        yo = price_to_y(bar.open, high, low, chart_top, chart_h)
        yc = price_to_y(bar.close, high, low, chart_top, chart_h)
        color = (45, 212, 191, 255) if bar.close >= bar.open else (248, 113, 113, 255)
        draw.line([x, yh, x, yl], fill=color, width=1)
        draw.rectangle([x - candle_w, min(yo, yc), x + candle_w, max(yo, yc) + 1], fill=color)

    eq = as_float(analysis.get("eq"))
    if eq:
        y = price_to_y(eq, high, low, chart_top, chart_h)
        dashed_line(draw, (chart_left, y, chart_right, y), (148, 163, 184, 150), width=1)
        draw.text((chart_right + 8, y - 8), "EQ", font=font(11, True), fill=(148, 163, 184, 255))

    for item in analysis.get("bsl", [])[-2:]:
        y = price_to_y(as_float(item["level"]), high, low, chart_top, chart_h)
        level_label = "EXT BSL" if item.get("grade") == "external" else "MAJ BSL" if item.get("grade") == "major" else "BSL"
        dashed_line(draw, (chart_left, y, chart_right, y), (248, 113, 113, 165), width=1)
        draw.text((chart_right + 8, y - 8), level_label, font=font(11, True), fill=(248, 113, 113, 255))
    for item in analysis.get("ssl", [])[-2:]:
        y = price_to_y(as_float(item["level"]), high, low, chart_top, chart_h)
        level_label = "EXT SSL" if item.get("grade") == "external" else "MAJ SSL" if item.get("grade") == "major" else "SSL"
        dashed_line(draw, (chart_left, y, chart_right, y), (52, 211, 153, 165), width=1)
        draw.text((chart_right + 8, y - 8), level_label, font=font(11, True), fill=(52, 211, 153, 255))

    for zone in scenario_zones:
        z_top = as_float(zone["top"])
        z_bottom = as_float(zone["bottom"])
        start = max(0, as_int(zone["start"]))
        end = min(len(bars) - 1, max(as_int(zone["index"]) + 18, len(bars) - 1))
        x1 = index_to_x(start, len(bars), chart_left, chart_w)
        x2 = index_to_x(end, len(bars), chart_left, chart_w)
        y1 = price_to_y(z_top, high, low, chart_top, chart_h)
        y2 = price_to_y(z_bottom, high, low, chart_top, chart_h)
        if zone["kind"] == "FVG":
            outline = (251, 191, 36, 230) if zone["type"] == "bearish" else (34, 211, 238, 230)
            fill = (251, 191, 36, 38) if zone["type"] == "bearish" else (34, 211, 238, 35)
        else:
            outline = (168, 85, 247, 235) if zone["type"] == "bearish" else (52, 211, 153, 235)
            fill = (168, 85, 247, 38) if zone["type"] == "bearish" else (52, 211, 153, 35)
        x_left = min(x1, x2)
        x_right = max(x1, x2)
        draw.rectangle([x_left, min(y1, y2), x_right, max(y1, y2)], fill=fill, outline=outline, width=2)
        label_text = f"{zone['type'][0].upper()} {zone['kind']}"
        label(draw, (x_left + 5, min(y1, y2) + 4), label_text, (15, 23, 42, 220), outline, 10)

    y_cp = price_to_y(current_price, high, low, chart_top, chart_h)
    dashed_line(draw, (chart_left, y_cp, chart_right, y_cp), (96, 165, 250, 210), width=2)
    draw.text((chart_right + 8, y_cp - 8), "Now", font=font(11, True), fill=(96, 165, 250, 255))

    for level in target_levels:
        y = price_to_y(as_float(level["level"]), high, low, chart_top, chart_h)
        color = (248, 113, 113, 230) if str(level["side"]) == "up" else (52, 211, 153, 230)
        draw.line([chart_left, y, chart_right, y], fill=color, width=1)
        draw.text((chart_left + 8, y - 18), str(level["label"]), font=font(11, True), fill=color)

    for event in (analysis.get("sweeps") or [])[-2:]:
        y = price_to_y(as_float(event["level"]), high, low, chart_top, chart_h)
        idx = as_int(event["index"])
        x = index_to_x(idx, len(bars), chart_left, chart_w)
        label(draw, (min(x + 4, chart_right - 70), y + 4), str(event["type"]).replace(" sweep", ""), (69, 26, 3, 220), (253, 186, 116, 255), 10)
    for event in (analysis.get("breaks") or [])[-2:]:
        y = price_to_y(as_float(event["level"]), high, low, chart_top, chart_h)
        idx = as_int(event["index"])
        x = index_to_x(idx, len(bars), chart_left, chart_w)
        label(draw, (min(x + 4, chart_right - 70), y - 18), "BOS", (15, 23, 42, 220), (96, 165, 250, 255), 10)

    meta = f"{analysis.get('location')} | {analysis.get('trend')} | {bars[-1].time.strftime('%m-%d %H:%M')}"
    label(draw, (right - 330, top + 13), meta, (15, 23, 42, 220), (203, 213, 225, 255), 11)


def choose_scenario(symbol: str, analyses: dict[str, dict[str, Any]], current_price: float) -> dict[str, Any]:
    htf_name = "H1"
    if analyses["H4"]["trend"] != "balanced" or analyses["H4"]["zonesAbove"] or analyses["H4"]["zonesBelow"]:
        htf_name = "H4" if abs(analyses["H4"]["eq"] - current_price) < abs(analyses["H1"]["eq"] - current_price) * 2.2 else "H1"
    ctx_name = "M15"
    ltf_name = "M1"

    htf = analyses[htf_name]
    ctx = analyses[ctx_name]
    ltf = analyses[ltf_name]
    supply = sorted(
        htf["zonesAbove"] + ctx["zonesAbove"],
        key=lambda z: abs(as_float(z["bottom"]) - current_price),
    )[:2]
    demand = sorted(
        htf["zonesBelow"] + ctx["zonesBelow"],
        key=lambda z: abs(as_float(z["top"]) - current_price),
    )[:2]
    up_liq = sorted(htf["bsl"] + ctx["bsl"], key=lambda x: as_float(x["level"]))
    down_liq = sorted(htf["ssl"] + ctx["ssl"], key=lambda x: as_float(x["level"]), reverse=True)
    nearest_up = next((x for x in up_liq if as_float(x["level"]) > current_price), up_liq[-1] if up_liq else None)
    nearest_down = next((x for x in down_liq if as_float(x["level"]) < current_price), down_liq[-1] if down_liq else None)

    primary_side = "bearish" if htf["location"] == "premium" and supply else "bullish" if demand else "range"
    if primary_side == "range":
        primary_side = "bearish" if supply and (not demand or abs(as_float(supply[0]["mid"]) - current_price) < abs(as_float(demand[0]["mid"]) - current_price)) else "bullish"

    primary_zone = supply[0] if primary_side == "bearish" and supply else demand[0] if demand else None
    invalidation = None
    target = None
    if primary_side == "bearish":
        target = nearest_down
        zone_top = as_float(primary_zone["top"]) if primary_zone else current_price
        invalidation = next((x for x in up_liq if as_float(x["level"]) > zone_top), None)
        if invalidation is None and primary_zone:
            invalidation = {"level": zone_top, "label": "zone high"}
        elif invalidation is None:
            invalidation = nearest_up
    elif primary_side == "bullish":
        target = nearest_up
        zone_bottom = as_float(primary_zone["bottom"]) if primary_zone else current_price
        invalidation = next((x for x in down_liq if as_float(x["level"]) < zone_bottom), None)
        if invalidation is None and primary_zone:
            invalidation = {"level": zone_bottom, "label": "zone low"}
        elif invalidation is None:
            invalidation = nearest_down

    return {
        "symbol": symbol,
        "htf": htf_name,
        "context": ctx_name,
        "ltf": ltf_name,
        "primarySide": primary_side,
        "primaryZone": primary_zone,
        "supply": supply,
        "demand": demand,
        "target": target,
        "invalidation": invalidation,
        "ltTrigger": ltf,
    }


def build_notes(symbol: str, generated_at: datetime, current_price: float, tick: dict[str, float], analyses: dict[str, dict[str, Any]], scenario: dict[str, Any]) -> str:
    zone = scenario.get("primaryZone")
    target = scenario.get("target")
    invalidation = scenario.get("invalidation")
    side = scenario["primarySide"]
    if zone:
        zone_text = f"{zone['kind']} {zone['type']} {as_float(zone['bottom']):.2f}-{as_float(zone['top']):.2f}"
    else:
        zone_text = "명확한 미해소 zone 없음"
    target_text = f"{as_float(target['level']):.2f} {target.get('label', 'liquidity')}" if target else "유효한 다음 유동성 없음"
    invalidation_text = f"{as_float(invalidation['level']):.2f}" if invalidation else "구조 재평가"

    lines = [
        f"# {symbol} Current MTF Scenario",
        "",
        f"- generated_at: {generated_at.isoformat(timespec='seconds')}",
        f"- current_price: {current_price:.2f} (bid {tick.get('bid', 0):.2f}, ask {tick.get('ask', 0):.2f})",
        f"- selected: HTF {scenario['htf']} / Context {scenario['context']} / LTF {scenario['ltf']}",
        "",
        "## Scenario",
        f"- Primary read: {side}",
        f"- Wait zone: {zone_text}",
        f"- Liquidity target: {target_text}",
        f"- Invalidation / 재평가 기준: {invalidation_text}",
        "",
        "## Timeframe Context",
    ]
    for tf in ("H4", "H1", "M15", "M5", "M1"):
        a = analyses[tf]
        lines.append(
            f"- {tf}: {a['location']} / {a['trend']} / range {as_float(a['rangeLow']):.2f}-{as_float(a['rangeHigh']):.2f} / EQ {as_float(a['eq']):.2f}"
        )
    return "\n".join(lines) + "\n"


def render_board(symbol: str, bars_by_tf: dict[str, list[Bar]], analyses: dict[str, dict[str, Any]], current_price: float, scenario: dict[str, Any], generated_at: datetime) -> Image.Image:
    canvas = Image.new("RGB", (1320, 1420), (3, 7, 12))
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.text((48, 28), f"{symbol} MTF Scenario Board", font=font(34, True), fill=(45, 212, 191, 255))
    draw.text(
        (48, 76),
        f"Generated {generated_at.strftime('%Y-%m-%d %H:%M:%S')} | Current {current_price:.2f} | Scenario, not a trade signal",
        font=font(17),
        fill=(203, 213, 225, 255),
    )

    htf = scenario["htf"]
    context = scenario["context"]
    ltf = scenario["ltf"]
    primary_zone = scenario.get("primaryZone")
    supply = scenario.get("supply") or []
    demand = scenario.get("demand") or []
    htf_zones = []
    if primary_zone and primary_zone in analyses[htf]["zonesAbove"] + analyses[htf]["zonesBelow"]:
        htf_zones.append(primary_zone)
    htf_zones += [z for z in (supply + demand) if z not in htf_zones][:3]

    target_levels: list[dict[str, Any]] = []
    if scenario.get("target"):
        target = dict(scenario["target"])
        target["side"] = "up" if as_float(target["level"]) > current_price else "down"
        target["label"] = "Target liquidity"
        target_levels.append(target)
    if scenario.get("invalidation"):
        invalid = dict(scenario["invalidation"])
        invalid["side"] = "up" if as_float(invalid["level"]) > current_price else "down"
        invalid["label"] = "Invalidation"
        target_levels.append(invalid)

    draw_panel(
        draw,
        bars_by_tf[htf],
        analyses[htf],
        (44, 120, 1276, 500),
        f"HTF Map: {htf} | FVG/OB, external liquidity, premium-discount",
        current_price,
        htf_zones,
        target_levels,
    )
    ctx_zones = (analyses[context]["zonesAbove"] + analyses[context]["zonesBelow"])[:4]
    draw_panel(
        draw,
        bars_by_tf[context],
        analyses[context],
        (44, 530, 1276, 910),
        f"Context: {context} | wait zone, sweep/BOS confirmation area",
        current_price,
        ctx_zones,
        target_levels,
    )
    ltf_zones = (analyses[ltf]["zonesAbove"] + analyses[ltf]["zonesBelow"])[:5]
    draw_panel(
        draw,
        bars_by_tf[ltf],
        analyses[ltf],
        (44, 940, 1276, 1250),
        f"LTF Trigger: {ltf} | wait for sweep + CHoCH/BOS + fresh micro FVG/OB",
        current_price,
        ltf_zones,
        [],
    )

    side = scenario["primarySide"]
    zone = scenario.get("primaryZone")
    if zone:
        zone_text = f"{zone['type']} {zone['kind']} {as_float(zone['bottom']):.2f}-{as_float(zone['top']):.2f}"
    else:
        zone_text = "no clean fresh zone"
    target = scenario.get("target")
    target_text = f"{as_float(target['level']):.2f}" if target else "none"
    invalid = scenario.get("invalidation")
    invalid_text = f"{as_float(invalid['level']):.2f}" if invalid else "re-map"
    draw.rounded_rectangle([44, 1280, 1276, 1384], radius=12, fill=(7, 12, 18, 255), outline=(40, 52, 66, 255), width=1)
    draw.text((66, 1300), "Scenario Plan", font=font(21, True), fill=(226, 232, 240, 255))
    bullets = [
        f"Primary: {side}. Do not chase current candle; wait for price to interact with {zone_text}.",
        f"Confirmation: on {scenario['ltf']}, prefer liquidity sweep -> CHoCH/BOS -> fresh FVG/OB retest.",
        f"Expected path: if confirmation holds, next liquidity magnet is {target_text}. Re-map if price accepts beyond {invalid_text}.",
    ]
    y = 1330
    for item in bullets:
        draw.text((66, y), "- " + item, font=font(14), fill=(203, 213, 225, 255))
        y += 23
    return canvas


def main() -> int:
    symbol = sys.argv[1] if len(sys.argv) > 1 else "GOLD"
    generated_at = datetime.now().astimezone()
    bars_by_tf: dict[str, list[Bar]] = {}
    actual_symbol = symbol
    for tf in TIMEFRAMES:
        actual_symbol, bars = fetch_bars(symbol, tf, TF_BARS[tf])
        bars_by_tf[tf] = bars
    tick = fetch_tick(actual_symbol)
    current_price = (as_float(tick.get("bid")) + as_float(tick.get("ask"))) / 2 if tick.get("bid") and tick.get("ask") else bars_by_tf["M1"][-1].close
    analyses = {tf: analyze_tf(tf, bars_by_tf[tf], current_price) for tf in TIMEFRAMES}
    scenario = choose_scenario(actual_symbol, analyses, current_price)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    image = render_board(actual_symbol, bars_by_tf, analyses, current_price, scenario, generated_at)
    image_path = OUT_DIR / f"current_{actual_symbol}_mtf_scenario.png"
    note_path = OUT_DIR / f"current_{actual_symbol}_mtf_scenario.md"
    json_path = OUT_DIR / f"current_{actual_symbol}_mtf_scenario.json"
    image.save(image_path)
    note_path.write_text(build_notes(actual_symbol, generated_at, current_price, tick, analyses, scenario), encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {"symbol": actual_symbol, "generatedAt": generated_at.isoformat(), "currentPrice": current_price, "scenario": scenario, "analyses": analyses},
            ensure_ascii=False,
            default=str,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"image": str(image_path), "notes": str(note_path), "json": str(json_path), "symbol": actual_symbol}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
