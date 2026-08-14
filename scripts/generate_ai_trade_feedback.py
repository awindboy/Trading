from __future__ import annotations

import argparse
import base64
import io
import json
import sqlite3
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge.mt5_bridge import (  # noqa: E402
    JOURNAL_DB_FILE,
    as_dict,
    as_float,
    as_int,
    initialize_mt5,
    mt5,
    parse_since,
    timeframe_value,
)
from scripts.journal_chart_liquidity import (  # noqa: E402
    build_liquidity_profile,
    find_liquidity_sweep_event,
    support_resistance_from_liquidity,
)
from scripts.ai_feedback_provider import ai_feedback_provider_payload, generate_gemini_review

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception as exc:  # pragma: no cover - local dependency check.
    raise SystemExit(f"Pillow is required for feedback chart generation: {exc}")


CANDIDATE_TIMEFRAMES = ("D1", "H4", "H1", "M30", "M15", "M5", "M1")
DEFAULT_SELECTED_TIMEFRAMES = ("M30", "M5", "M1")
AI_FEEDBACK_VERSION = "mtf-evidence-board-v1"
TIMEFRAME_MINUTES = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}

AI_FEEDBACK_PROVIDER_WARNING = "Gemini API key가 없으면 자동 피드백 대신 MT5/screenshot 기반 로컬 평가를 사용합니다."
ROLE_LABELS = {
    "htf": "HTF map",
    "context": "Context",
    "ltf": "LTF trigger",
}

AI_FEEDBACK_PROMPT_TEMPLATE = """너는 트레이딩 피드백용 평가기다.
거래(매도/매수), 시그널 진입 근거, 스텝별 MTF 분석, SL/TP, 손익을 바탕으로만 판단한다.
판단은 다음 JSON 구조로만 응답한다:
{
  "verdict": "...",
  "score": 1~5 정수,
  "feedback": ["..."],
  "improvements": ["..."],
  "nextRules": ["..."]
}
불필요한 감상은 쓰지 말고, 항목별 근거가 있는지 위주로 판단한다.
score는 1~5 정수고, 근거가 모호하면 낮게 준다.
"""


@dataclass
class Bar:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


def load_trade(trade_id: str | None = None) -> dict[str, Any]:
    with sqlite3.connect(JOURNAL_DB_FILE) as connection:
        connection.row_factory = sqlite3.Row
        if trade_id:
            row = connection.execute("SELECT data FROM trades WHERE id=?", (trade_id,)).fetchone()
            if not row:
                raise RuntimeError(f"Trade not found: {trade_id}")
            return json.loads(row["data"])

        rows = connection.execute("SELECT data FROM trades ORDER BY sort_time ASC, updated_at ASC").fetchall()
        for row in rows:
            trade = json.loads(row["data"])
            pnl = trade.get("brokerPnl")
            if trade.get("status") == "closed" and (trade.get("result") == "loss" or as_float(pnl) < 0):
                return trade
    raise RuntimeError("No losing closed trade found.")


def save_trade(trade: dict[str, Any]) -> None:
    trade_id = str(trade.get("id") or "")
    if not trade_id:
        raise RuntimeError("Cannot save feedback without trade id.")
    with sqlite3.connect(JOURNAL_DB_FILE) as connection:
        connection.execute("PRAGMA busy_timeout=30000")
        connection.execute(
            "UPDATE trades SET data=?, updated_at=? WHERE id=?",
            (json.dumps(trade, ensure_ascii=False), datetime.now(timezone.utc).isoformat(timespec="seconds"), trade_id),
        )
        connection.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('updatedAt', ?)",
            (datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),),
        )
        connection.commit()


def parse_trade_time(trade: dict[str, Any], key: str) -> datetime:
    broker_meta = trade.get("brokerMeta") if isinstance(trade.get("brokerMeta"), dict) else {}
    value = broker_meta.get(key) or trade.get("createdAt") or trade.get("updatedAt") or trade.get("date")
    parsed = parse_since(value)
    if parsed is None:
        raise RuntimeError(f"Cannot parse trade {key} time: {value}")
    return parsed


def decode_data_url(value: str) -> Image.Image | None:
    if not value:
        return None
    try:
        payload = value.split(",", 1)[1] if value.startswith("data:") else value
        return Image.open(io.BytesIO(base64.b64decode(payload))).convert("RGB")
    except Exception:
        return None


def encode_png_data_url(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def symbol_aliases(symbol: str) -> list[str]:
    normalized = symbol.strip().upper()
    values = [normalized]
    if normalized == "GOLD":
        values.extend(["XAUUSD", "GOLD.", "XAUUSD.", "GOLD#"])
    if normalized == "XAUUSD":
        values.append("GOLD")
    return list(dict.fromkeys(values))


def fetch_bars(symbol: str, timeframe: str, start: datetime, end: datetime) -> tuple[str, list[Bar]]:
    if mt5 is None:
        raise RuntimeError("MetaTrader5 package is not available.")
    initialize_mt5()
    utc_from = (start - timedelta(hours=2)).astimezone(timezone.utc)
    utc_to = (end + timedelta(hours=2)).astimezone(timezone.utc)
    last_error = ""
    for candidate in symbol_aliases(symbol):
        try:
            mt5.symbol_select(candidate, True)
            rates = mt5.copy_rates_range(candidate, timeframe_value(timeframe), utc_from, utc_to)
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
    raise RuntimeError(f"No bars for {symbol} {timeframe}: {last_error}")


def pivots(bars: list[Bar], length: int = 3) -> tuple[list[int], list[int]]:
    highs: list[int] = []
    lows: list[int] = []
    for index in range(length, len(bars) - length):
        window = bars[index - length : index + length + 1]
        if bars[index].high == max(bar.high for bar in window):
            highs.append(index)
        if bars[index].low == min(bar.low for bar in window):
            lows.append(index)
    return highs, lows


def latest_index_before(bars: list[Bar], when: datetime) -> int:
    indexes = [index for index, bar in enumerate(bars) if bar.time <= when]
    return indexes[-1] if indexes else 0


def latest_pivot_before(pivot_indexes: list[int], before_index: int) -> int | None:
    values = [index for index in pivot_indexes if index < before_index]
    return values[-1] if values else None


def find_sweep_event(bars: list[Bar], highs: list[int], lows: list[int], direction: str, start: int, end: int) -> dict[str, Any]:
    for index in range(max(0, start), min(end + 1, len(bars))):
        if direction == "long":
            pivot = latest_pivot_before(lows, index)
            if pivot is not None:
                level = bars[pivot].low
                if bars[index].low < level and bars[index].close > level:
                    return {"found": True, "index": index, "level": level, "label": "SSL sweep"}
        if direction == "short":
            pivot = latest_pivot_before(highs, index)
            if pivot is not None:
                level = bars[pivot].high
                if bars[index].high > level and bars[index].close < level:
                    return {"found": True, "index": index, "level": level, "label": "BSL sweep"}
    return {"found": False, "index": None, "level": None, "label": f"no {'SSL' if direction == 'long' else 'BSL'} sweep"}


def find_choch_event(bars: list[Bar], highs: list[int], lows: list[int], direction: str, start: int, end: int) -> dict[str, Any]:
    for index in range(max(0, start), min(end + 1, len(bars))):
        if direction == "long":
            pivot = latest_pivot_before(highs, index)
            if pivot is not None:
                level = bars[pivot].high
            else:
                window = bars[max(0, start - 8) : index]
                level = max((bar.high for bar in window), default=0.0)
            if level and bars[index].close > level:
                return {"found": True, "index": index, "level": level, "label": "CHoCH"}
        if direction == "short":
            pivot = latest_pivot_before(lows, index)
            if pivot is not None:
                level = bars[pivot].low
            else:
                window = bars[max(0, start - 8) : index]
                level = min((bar.low for bar in window), default=0.0)
            if level and bars[index].close < level:
                return {"found": True, "index": index, "level": level, "label": "CHoCH"}
    return {"found": False, "index": None, "level": None, "label": "no CHoCH"}


def find_fvg_zones(bars: list[Bar], direction: str, start: int, end: int, entry: float) -> list[dict[str, Any]]:
    zones: list[dict[str, Any]] = []
    for index in range(max(2, start), min(end + 1, len(bars))):
        if direction == "long" and bars[index].low > bars[index - 2].high:
            bottom = bars[index - 2].high
            top = bars[index].low
        elif direction == "short" and bars[index].high < bars[index - 2].low:
            bottom = bars[index].high
            top = bars[index - 2].low
        else:
            continue
        midpoint = (top + bottom) / 2
        near_entry = bottom <= entry <= top or abs(entry - midpoint) <= max(abs(top - bottom) * 2.5, max(entry, 1) * 0.0007)
        zones.append(
            {
                "index": index,
                "startIndex": index - 2,
                "top": top,
                "bottom": bottom,
                "nearEntry": near_entry,
                "label": "FVG",
            }
        )
    return zones


def find_bos_event(bars: list[Bar], highs: list[int], lows: list[int], direction: str, start: int, end: int) -> dict[str, Any]:
    for index in range(max(0, start), min(end + 1, len(bars))):
        if direction == "long":
            pivot = latest_pivot_before(highs, index)
            if pivot is not None:
                level = bars[pivot].high
                if bars[index].close > level:
                    return {"found": True, "index": index, "level": level, "label": "BOS"}
        if direction == "short":
            pivot = latest_pivot_before(lows, index)
            if pivot is not None:
                level = bars[pivot].low
                if bars[index].close < level:
                    return {"found": True, "index": index, "level": level, "label": "BOS"}
    return {"found": False, "index": None, "level": None, "label": "no BOS"}


def find_ob_zones(bars: list[Bar], direction: str, start: int, end: int, entry: float) -> list[dict[str, Any]]:
    zones: list[dict[str, Any]] = []
    for index in range(min(end, len(bars) - 1), max(0, start) - 1, -1):
        candle = bars[index]
        bullish = candle.close >= candle.open
        is_ob = (direction == "long" and not bullish) or (direction == "short" and bullish)
        if not is_ob:
            continue
        top = candle.high
        bottom = candle.low
        midpoint = (top + bottom) / 2
        near_entry = bottom <= entry <= top or abs(entry - midpoint) <= max(abs(top - bottom) * 2.5, max(entry, 1) * 0.0007)
        zones.append(
            {
                "index": index,
                "startIndex": index,
                "top": top,
                "bottom": bottom,
                "nearEntry": near_entry,
                "label": "OB",
            }
        )
        if len(zones) >= 2:
            break
    return list(reversed(zones))


def support_resistance_levels(bars: list[Bar], highs: list[int], lows: list[int], entry_index: int) -> list[dict[str, Any]]:
    levels: list[dict[str, Any]] = []
    for pivot in [idx for idx in highs if idx < entry_index][-2:]:
        levels.append({"index": pivot, "level": bars[pivot].high, "label": "R / BSL", "kind": "resistance"})
    for pivot in [idx for idx in lows if idx < entry_index][-2:]:
        levels.append({"index": pivot, "level": bars[pivot].low, "label": "S / SSL", "kind": "support"})
    return levels


def trend_channel_lines(bars: list[Bar], highs: list[int], lows: list[int], entry_index: int) -> dict[str, Any]:
    prior_highs = [idx for idx in highs if idx < entry_index]
    prior_lows = [idx for idx in lows if idx < entry_index]
    result: dict[str, Any] = {}
    if len(prior_lows) >= 2:
        a, b = prior_lows[-2], prior_lows[-1]
        result["trendLine"] = {"a": a, "b": b, "priceA": bars[a].low, "priceB": bars[b].low, "label": "trendline"}
    if len(prior_highs) >= 2:
        a, b = prior_highs[-2], prior_highs[-1]
        result["channelLine"] = {"a": a, "b": b, "priceA": bars[a].high, "priceB": bars[b].high, "label": "channel"}
    return result


def focus_bars(bars: list[Bar], open_time: datetime, close_time: datetime, max_count: int) -> list[Bar]:
    if len(bars) <= max_count:
        return bars
    entry_index = latest_index_before(bars, open_time)
    exit_index = latest_index_before(bars, close_time)
    span = max(exit_index - entry_index + 1, 1)
    before = max(8, int((max_count - span) * 0.72))
    start = max(0, entry_index - before)
    end = min(len(bars), start + max_count)
    if exit_index >= end:
        end = min(len(bars), exit_index + max(8, int(max_count * 0.15)))
        start = max(0, end - max_count)
    return bars[start:end]


def timeframe_minutes(timeframe: str) -> int:
    return TIMEFRAME_MINUTES.get(timeframe, 0)


def trade_holding_minutes(open_time: datetime, close_time: datetime) -> float:
    return max((close_time - open_time).total_seconds() / 60.0, 0.0)


def direction_aligned(direction: str, trend: str) -> bool:
    return (direction == "long" and trend == "bullish") or (direction == "short" and trend == "bearish")


def structure_score(analysis: dict[str, Any], direction: str) -> float:
    if not analysis.get("available"):
        return -100.0
    desired_location = "discount" if direction == "long" else "premium"
    score = 1.0
    if analysis.get("location") == desired_location:
        score += 4.0
    elif analysis.get("location") in {"premium", "discount"}:
        score -= 1.5
    if analysis.get("sweepFound"):
        score += 3.0
    if analysis.get("chochFound"):
        score += 3.0
    if analysis.get("bosFound"):
        score += 2.0
    if analysis.get("freshFvgNearEntry"):
        score += 2.0
    if analysis.get("freshObNearEntry"):
        score += 2.0
    if analysis.get("srLevels"):
        score += 1.0
    if direction_aligned(direction, str(analysis.get("trend") or "")):
        score += 1.0
    elif analysis.get("trend") in {"bullish", "bearish"}:
        score -= 1.0
    score -= min(len(analysis.get("trapReasons") or []), 3) * 0.75
    return score


def holding_preference(role: str, timeframe: str, minutes: float) -> float:
    if role == "htf":
        if minutes >= 480:
            return {"H4": 4, "H1": 3, "M30": 1, "M15": -2}.get(timeframe, -3)
        if minutes >= 120:
            return {"H4": 1, "H1": 4, "M30": 3, "M15": 1}.get(timeframe, -2)
        if minutes >= 30:
            return {"H4": -1, "H1": 2, "M30": 4, "M15": 3}.get(timeframe, -2)
        return {"H4": -2, "H1": 1, "M30": 3, "M15": 4}.get(timeframe, -2)
    if role == "context":
        if minutes >= 480:
            return {"H1": 3, "M30": 2, "M15": 1, "M5": -1}.get(timeframe, -2)
        if minutes >= 120:
            return {"H1": 2, "M30": 3, "M15": 2, "M5": 0}.get(timeframe, -2)
        if minutes >= 30:
            return {"H1": 0, "M30": 2, "M15": 3, "M5": 2}.get(timeframe, -2)
        return {"H1": -1, "M30": 0, "M15": 2, "M5": 3}.get(timeframe, -2)
    if minutes < 5:
        return {"M15": -1, "M5": 3, "M1": 4}.get(timeframe, -2)
    if minutes < 30:
        return {"M15": 1, "M5": 4, "M1": 3}.get(timeframe, -2)
    if minutes < 120:
        return {"M15": 3, "M5": 4, "M1": 2}.get(timeframe, -2)
    return {"M15": 4, "M5": 3, "M1": 1}.get(timeframe, -2)


def role_score(role: str, timeframe: str, analysis: dict[str, Any], direction: str, minutes: float) -> float:
    base = structure_score(analysis, direction)
    if role == "htf":
        score = base + holding_preference(role, timeframe, minutes)
        if analysis.get("freshFvgNearEntry") or analysis.get("freshObNearEntry"):
            score += 2.0
        if analysis.get("location") == ("discount" if direction == "long" else "premium"):
            score += 2.0
        return score
    if role == "context":
        return base + holding_preference(role, timeframe, minutes) + (1.0 if analysis.get("srLevels") else 0.0)
    score = base + holding_preference(role, timeframe, minutes)
    if analysis.get("chochFound"):
        score += 2.0
    if analysis.get("sweepFound"):
        score += 1.5
    if analysis.get("freshFvgNearEntry") or analysis.get("freshObNearEntry"):
        score += 1.5
    return score


def choose_timeframe(
    role: str,
    candidates: list[str],
    analyses: dict[str, dict[str, Any]],
    direction: str,
    minutes: float,
    lower_than: str | None = None,
) -> dict[str, Any]:
    filtered = [timeframe for timeframe in candidates if not lower_than or timeframe_minutes(timeframe) < timeframe_minutes(lower_than)]
    if not filtered:
        filtered = candidates
    ranked = []
    for timeframe in filtered:
        ranked.append((role_score(role, timeframe, analyses.get(timeframe, {}), direction, minutes), timeframe))
    ranked.sort(key=lambda item: (item[0], timeframe_minutes(item[1])), reverse=True)
    score, timeframe = ranked[0]
    analysis = analyses.get(timeframe, {})
    reason_bits: list[str] = []
    if role == "htf":
        reason_bits.append(f"{analysis.get('location', 'unknown')} 위치")
        if analysis.get("freshFvgNearEntry") or analysis.get("freshObNearEntry"):
            reason_bits.append("상위 FVG/OB 근접")
        if analysis.get("srLevels"):
            reason_bits.append("상위 유동성/SR 식별")
    elif role == "context":
        reason_bits.append(f"{analysis.get('trend', 'unknown')} 흐름")
        if analysis.get("sweepFound"):
            reason_bits.append(str(analysis.get("sweepLabel")))
        if analysis.get("srLevels"):
            reason_bits.append("중간 구조 기준선")
    else:
        if analysis.get("sweepFound"):
            reason_bits.append(str(analysis.get("sweepLabel")))
        if analysis.get("chochFound"):
            reason_bits.append("CHoCH 확인")
        if analysis.get("freshFvgNearEntry") or analysis.get("freshObNearEntry"):
            reason_bits.append("진입 zone 근접")
    if not reason_bits:
        reason_bits.append("보유시간과 구조 가시성 기준")
    return {"role": role, "timeframe": timeframe, "score": round(score, 2), "reason": ", ".join(reason_bits)}


def select_timeframes(analyses: dict[str, dict[str, Any]], direction: str, open_time: datetime, close_time: datetime) -> list[dict[str, Any]]:
    minutes = trade_holding_minutes(open_time, close_time)
    htf = choose_timeframe("htf", ["H4", "H1", "M30", "M15"], analyses, direction, minutes)
    context = choose_timeframe("context", ["H1", "M30", "M15", "M5"], analyses, direction, minutes, lower_than=str(htf["timeframe"]))
    ltf = choose_timeframe("ltf", ["M15", "M5", "M1"], analyses, direction, minutes, lower_than=str(context["timeframe"]))
    selected = [htf, context, ltf]
    used: set[str] = set()
    for item in selected:
        timeframe = str(item["timeframe"])
        if timeframe in used:
            alternatives = [tf for tf in CANDIDATE_TIMEFRAMES if tf not in used and tf != "D1" and timeframe_minutes(tf) <= timeframe_minutes(timeframe)]
            if alternatives:
                item["timeframe"] = alternatives[-1]
                item["reason"] = f"{item['reason']}; 중복 방지로 {item['timeframe']} 선택"
        used.add(str(item["timeframe"]))
    return selected


def selected_timeframe_map(selected: list[dict[str, Any]]) -> dict[str, str]:
    return {str(item.get("role")): str(item.get("timeframe")) for item in selected}


def analyze_timeframe(bars: list[Bar], direction: str, entry_time: datetime, entry: float, exit_time: datetime | None = None) -> dict[str, Any]:
    if not bars:
        return {"available": False}
    highs, lows = pivots(bars, 3)
    entry_index = latest_index_before(bars, entry_time)
    exit_index = latest_index_before(bars, exit_time) if exit_time else entry_index
    profile_bars = bars[: max(entry_index + 1, 1)]
    liquidity = build_liquidity_profile(profile_bars, entry, pivot_len=3)
    range_high_meta = liquidity.get("rangeHigh") if isinstance(liquidity.get("rangeHigh"), dict) else {}
    range_low_meta = liquidity.get("rangeLow") if isinstance(liquidity.get("rangeLow"), dict) else {}
    range_high = as_float(range_high_meta.get("level")) or max(bar.high for bar in bars[: max(entry_index, 1)])
    range_low = as_float(range_low_meta.get("level")) or min(bar.low for bar in bars[: max(entry_index, 1)])
    eq = (range_high + range_low) / 2 if range_high > range_low else 0
    location = "discount" if eq and entry <= eq else "premium" if eq else "unknown"

    lookback_start = max(0, entry_index - 20)
    lookahead_end = min(len(bars) - 1, max(entry_index + 3, exit_index + 3))
    sweep = find_liquidity_sweep_event(bars, direction, liquidity, lookback_start, entry_index)
    if not sweep.get("found"):
        sweep = find_sweep_event(bars, highs, lows, direction, lookback_start, entry_index)
    trigger_start = as_int(sweep.get("index"), lookback_start) if sweep.get("found") else lookback_start
    choch = find_choch_event(bars, highs, lows, direction, trigger_start, lookahead_end)
    bos_start = as_int(choch.get("index"), trigger_start) + 1 if choch.get("found") else trigger_start
    bos = find_bos_event(bars, highs, lows, direction, bos_start, lookahead_end)
    fvg_zones = find_fvg_zones(bars, direction, trigger_start, lookahead_end, entry)
    ob_zones = find_ob_zones(bars, direction, trigger_start, min(entry_index + 2, len(bars) - 1), entry)
    fvg_found = any(zone.get("nearEntry") for zone in fvg_zones) or bool(fvg_zones)
    ob_found = any(zone.get("nearEntry") for zone in ob_zones) or bool(ob_zones)

    trend = "bullish" if bars[entry_index].close >= bars[max(0, entry_index - 5)].close else "bearish"
    desired_location = "discount" if direction == "long" else "premium"
    missing: list[str] = []
    if location != desired_location:
        missing.append(f"HTF {desired_location}")
    if not sweep.get("found"):
        missing.append("sweep")
    if not choch.get("found"):
        missing.append("CHoCH")
    if not fvg_found and not ob_found:
        missing.append("fresh FVG/OB")
    trap_reasons: list[str] = []
    if location != desired_location:
        trap_reasons.append(f"{direction} in {location}")
    if choch.get("found") and not sweep.get("found"):
        trap_reasons.append("CHoCH without sweep")
    if trend and ((direction == "long" and trend == "bearish") or (direction == "short" and trend == "bullish")):
        trap_reasons.append(f"counter {trend} micro trend")
    return {
        "available": True,
        "entryIndex": entry_index,
        "exitIndex": exit_index,
        "rangeHigh": range_high,
        "rangeLow": range_low,
        "rangeHighMeta": range_high_meta,
        "rangeLowMeta": range_low_meta,
        "equilibrium": eq,
        "location": location,
        "sweepFound": bool(sweep.get("found")),
        "sweepLabel": sweep.get("label"),
        "sweepIndex": sweep.get("index"),
        "sweepLevel": sweep.get("level"),
        "chochFound": bool(choch.get("found")),
        "chochLabel": choch.get("label"),
        "chochIndex": choch.get("index"),
        "chochLevel": choch.get("level"),
        "bosFound": bool(bos.get("found")),
        "bosLabel": bos.get("label"),
        "bosIndex": bos.get("index"),
        "bosLevel": bos.get("level"),
        "fvgZones": fvg_zones[-3:],
        "obZones": ob_zones[-2:],
        "freshFvgNearEntry": fvg_found,
        "freshObNearEntry": ob_found,
        "srLevels": support_resistance_from_liquidity(liquidity, 3) or support_resistance_levels(bars, highs, lows, entry_index),
        "liquidityQuality": {
            "rangeHigh": range_high_meta,
            "rangeLow": range_low_meta,
            "bsl": (liquidity.get("relevantBsl") or [])[:3],
            "ssl": (liquidity.get("relevantSsl") or [])[:3],
        },
        "trendChannel": trend_channel_lines(bars, highs, lows, entry_index),
        "missingEvidence": missing,
        "trapReasons": trap_reasons,
        "trend": trend,
    }


def price_to_y(price: float, high: float, low: float, top: int, height: int) -> int:
    if high <= low:
        return top + height // 2
    return top + int((high - price) / (high - low) * height)


def bar_to_x(index: int, count: int, left: int, width: int) -> int:
    step = width / max(count, 1)
    return int(left + index * step + step / 2)


def dashed_line(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], fill: tuple[int, int, int], width: int = 1, dash: int = 8) -> None:
    x1, y1, x2, y2 = xy
    if y1 == y2:
        cursor = x1
        while cursor < x2:
            draw.line([cursor, y1, min(cursor + dash, x2), y2], fill=fill, width=width)
            cursor += dash * 2
        return
    draw.line([x1, y1, x2, y2], fill=fill, width=width)


def draw_label(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fill: tuple[int, int, int],
    text_fill: tuple[int, int, int] = (248, 250, 252),
    size: int = 12,
) -> None:
    if not text:
        return
    label_font = font(size, True)
    x, y = xy
    bbox = draw.textbbox((x, y), text, font=label_font)
    pad_x = 7
    pad_y = 4
    rect = [bbox[0] - pad_x, bbox[1] - pad_y, bbox[2] + pad_x, bbox[3] + pad_y]
    draw.rounded_rectangle(rect, radius=6, fill=fill, outline=tuple(min(255, channel + 28) for channel in fill), width=1)
    draw.text((x, y), text, fill=text_fill, font=label_font)


def draw_position_box(
    draw: ImageDraw.ImageDraw,
    chart_left: int,
    chart_right: int,
    chart_top: int,
    chart_bottom: int,
    x_entry: int,
    x_exit: int,
    y_entry: int,
    y_stop: int,
    y_target: int,
) -> None:
    box_left = max(chart_left, min(x_entry, x_exit))
    box_right = min(chart_right, max(x_entry, x_exit))
    if box_right - box_left < 28:
        center = (box_left + box_right) // 2
        box_left = max(chart_left, center - 21)
        box_right = min(chart_right, center + 21)
        if box_right - box_left < 28:
            box_right = min(chart_right, box_left + 42)
    reward_top = max(chart_top, min(y_entry, y_target))
    reward_bottom = min(chart_bottom, max(y_entry, y_target))
    risk_top = max(chart_top, min(y_entry, y_stop))
    risk_bottom = min(chart_bottom, max(y_entry, y_stop))
    if reward_bottom - reward_top > 1:
        draw.rectangle([box_left, reward_top, box_right, reward_bottom], fill=(16, 185, 129, 42), outline=(52, 211, 153, 150), width=2)
    if risk_bottom - risk_top > 1:
        draw.rectangle([box_left, risk_top, box_right, risk_bottom], fill=(239, 68, 68, 46), outline=(248, 113, 113, 160), width=2)


def price_in_bar(price: float, bar: Bar, tolerance: float) -> bool:
    if price <= 0:
        return False
    return (bar.low - tolerance) <= price <= (bar.high + tolerance)


def position_box_context(bars: list[Bar], trade: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any] | None:
    if not bars:
        return None
    entry_price = as_float(trade.get("entryPrice"))
    stop_price = as_float(trade.get("stopPrice"))
    target_price = as_float(trade.get("targetPrice"))
    exit_price = as_float(trade.get("exitPrice"))
    if entry_price <= 0 or stop_price <= 0 or target_price <= 0:
        return None
    try:
        open_time = parse_trade_time(trade, "openTime")
        close_time = parse_trade_time(trade, "closeTime")
    except Exception:
        return None

    entry_index = as_int(analysis.get("entryIndex"), latest_index_before(bars, open_time))
    exit_index = as_int(analysis.get("exitIndex"), latest_index_before(bars, close_time))
    if not (0 <= entry_index < len(bars) and 0 <= exit_index < len(bars)):
        return None

    entry_bar = bars[entry_index]
    exit_bar = bars[exit_index]
    entry_tolerance = max(abs(entry_price) * 0.00008, (entry_bar.high - entry_bar.low) * 0.35, 0.02)
    exit_tolerance = max(abs(exit_price) * 0.00008, (exit_bar.high - exit_bar.low) * 0.35, 0.02)
    if not price_in_bar(entry_price, entry_bar, entry_tolerance):
        return None
    if exit_price > 0 and not price_in_bar(exit_price, exit_bar, exit_tolerance):
        return None

    return {
        "openTime": open_time,
        "closeTime": close_time,
        "entryIndex": entry_index,
        "exitIndex": exit_index,
        "entryPrice": entry_price,
        "stopPrice": stop_price,
        "targetPrice": target_price,
    }


def draw_learning_candle_panel(
    draw: ImageDraw.ImageDraw,
    bars: list[Bar],
    box: tuple[int, int, int, int],
    title: str,
    trade: dict[str, Any],
    analysis: dict[str, Any],
) -> None:
    left, top, right, bottom = box
    panel_w = right - left
    draw.rounded_rectangle([left, top, right, bottom], radius=12, fill=(7, 12, 18), outline=(42, 55, 72), width=1)
    draw.text((left + 18, top + 14), title, fill=(226, 232, 240), font=font(21, True))
    if not bars:
        draw.text((left + 18, top + 56), "MT5 bars unavailable", fill=(148, 163, 184), font=font(14))
        return

    chart_left = left + 66
    chart_right = right - 142
    chart_top = top + 68
    chart_bottom = bottom - 54
    chart_w = chart_right - chart_left
    chart_h = chart_bottom - chart_top

    position_context = position_box_context(bars, trade, analysis)
    levels_for_range = [bar.high for bar in bars] + [bar.low for bar in bars]
    if position_context:
        for key in ("entryPrice", "stopPrice", "targetPrice"):
            value = as_float(position_context.get(key))
            if value > 0:
                levels_for_range.append(value)
    for key in ("rangeHigh", "rangeLow", "equilibrium", "sweepLevel", "chochLevel", "bosLevel"):
        value = as_float(analysis.get(key))
        if value > 0:
            levels_for_range.append(value)
    for zone_key in ("fvgZones", "obZones"):
        for zone in analysis.get(zone_key) or []:
            if isinstance(zone, dict):
                levels_for_range.extend([as_float(zone.get("top")), as_float(zone.get("bottom"))])
    high = max(levels_for_range)
    low = min(levels_for_range)
    padding = max((high - low) * 0.08, max(high, 1) * 0.0002)
    high += padding
    low -= padding

    def x_for(index: int) -> int:
        if len(bars) <= 1:
            return chart_left + chart_w // 2
        return int(chart_left + index / (len(bars) - 1) * chart_w)

    def x_for_time(value: datetime) -> int:
        if len(bars) <= 1:
            return chart_left + chart_w // 2
        start_time = bars[0].time
        end_time = bars[-1].time
        total_seconds = max((end_time - start_time).total_seconds(), 1.0)
        offset_seconds = (value - start_time).total_seconds()
        ratio = max(0.0, min(1.0, offset_seconds / total_seconds))
        return int(chart_left + ratio * chart_w)

    def y_for(price: float) -> int:
        return price_to_y(price, high, low, chart_top, chart_h)

    for grid in range(5):
        y = chart_top + grid * chart_h // 4
        draw.line([chart_left, y, chart_right, y], fill=(25, 34, 48), width=1)

    # Liquidity and PD array.
    liquidity_levels = [
        ("BSL", as_float(analysis.get("rangeHigh")), (248, 113, 113)),
        ("SSL", as_float(analysis.get("rangeLow")), (45, 212, 191)),
        ("EQ", as_float(analysis.get("equilibrium")), (148, 163, 184)),
    ]
    for label, price, color in liquidity_levels:
        if price <= 0:
            continue
        y = y_for(price)
        dashed_line(draw, (chart_left, y, chart_right, y), color, width=1, dash=8)
        draw.text((chart_right + 10, y - 8), label, fill=color, font=font(12, True))

    # Support / resistance from recent pivots.
    for level in analysis.get("srLevels") or []:
        if not isinstance(level, dict):
            continue
        price = as_float(level.get("level"))
        index = as_int(level.get("index"))
        label = str(level.get("label") or "S/R")
        kind = str(level.get("kind") or "")
        color = (96, 165, 250) if kind == "resistance" else (52, 211, 153)
        y = y_for(price)
        x = x_for(index)
        dashed_line(draw, (x, y, chart_right, y), color, width=1, dash=5)
        draw.text((x + 4, y - 16), label, fill=color, font=font(10, True))

    # Trendline / channel.
    trend_channel = analysis.get("trendChannel") if isinstance(analysis.get("trendChannel"), dict) else {}
    for key, color, label_y_offset in (
        ("trendLine", (52, 211, 153), 8),
        ("channelLine", (96, 165, 250), -20),
    ):
        line = trend_channel.get(key) if isinstance(trend_channel, dict) else None
        if not isinstance(line, dict):
            continue
        x1 = x_for(as_int(line.get("a")))
        x2 = x_for(as_int(line.get("b")))
        y1 = y_for(as_float(line.get("priceA")))
        y2 = y_for(as_float(line.get("priceB")))
        draw.line([x1, y1, x2, y2], fill=color, width=2)
        draw.text((min(x1, x2) + 6, min(y1, y2) + label_y_offset), str(line.get("label") or key), fill=color, font=font(10, True))

    # Zones around entry model.
    for zone_key, color, label in (
        ("fvgZones", (251, 191, 36), "FVG"),
        ("obZones", (168, 85, 247), "OB"),
    ):
        for zone in analysis.get(zone_key) or []:
            if not isinstance(zone, dict):
                continue
            top_price = as_float(zone.get("top"))
            bottom_price = as_float(zone.get("bottom"))
            if not top_price or not bottom_price:
                continue
            x1 = x_for(max(0, as_int(zone.get("startIndex"))))
            x2 = min(chart_right, x_for(min(len(bars) - 1, as_int(zone.get("index")) + 8)))
            y1 = y_for(top_price)
            y2 = y_for(bottom_price)
            outline = color if zone.get("nearEntry") else (100, 116, 139)
            draw.rectangle([x1, min(y1, y2), x2, max(y1, y2)], outline=outline, width=2)
            draw_label(draw, (x1 + 4, min(y1, y2) + 4), label, (35, 28, 7) if label == "FVG" else (39, 22, 66), outline, 10)

    if position_context:
        x_entry = x_for_time(position_context["openTime"])
        x_exit = x_for_time(position_context["closeTime"])
        draw_position_box(
            draw,
            chart_left,
            chart_right,
            chart_top,
            chart_bottom,
            x_entry,
            x_exit,
            y_for(as_float(position_context.get("entryPrice"))),
            y_for(as_float(position_context.get("stopPrice"))),
            y_for(as_float(position_context.get("targetPrice"))),
        )

    # Candles.
    candle_width = max(2, min(7, int(chart_w / max(len(bars), 1) * 0.42)))
    for index, bar in enumerate(bars):
        x = x_for(index)
        y_high = y_for(bar.high)
        y_low = y_for(bar.low)
        y_open = y_for(bar.open)
        y_close = y_for(bar.close)
        candle_color = (45, 212, 191) if bar.close >= bar.open else (248, 113, 113)
        draw.line([x, y_high, x, y_low], fill=candle_color, width=1)
        draw.rectangle([x - candle_width, min(y_open, y_close), x + candle_width, max(y_open, y_close) + 1], fill=candle_color)

    # Structure breaks and sweep.
    for key, color in (("sweep", (248, 113, 113)), ("choch", (96, 165, 250)), ("bos", (52, 211, 153))):
        level = as_float(analysis.get(f"{key}Level"))
        index = analysis.get(f"{key}Index")
        if not level or not isinstance(index, int):
            continue
        y = y_for(level)
        x = x_for(index)
        dashed_line(draw, (x, y, chart_right, y), color, width=2, dash=7)
        draw_label(draw, (x + 8, y - 14), key.upper() if key != "choch" else "CHoCH", (15, 23, 42), color, 11)

    missing = analysis.get("missingEvidence") or []
    trap = analysis.get("trapReasons") or []
    badge_text = f"{analysis.get('location', 'unknown')} | {analysis.get('trend', 'unknown')}"
    draw_label(draw, (left + panel_w - 300, top + 17), badge_text, (15, 23, 42), (203, 213, 225), 11)
    if missing:
        draw_label(draw, (left + 18, bottom - 38), "Missing: " + ", ".join(str(item) for item in missing[:4]), (69, 26, 3), (253, 186, 116), 11)
    if trap:
        draw_label(draw, (left + 380, bottom - 38), "Trap risk: " + ", ".join(str(item) for item in trap[:3]), (88, 28, 28), (254, 202, 202), 11)


def draw_candle_panel(
    draw: ImageDraw.ImageDraw,
    bars: list[Bar],
    box: tuple[int, int, int, int],
    title: str,
    trade: dict[str, Any],
    analysis: dict[str, Any],
) -> None:
    left, top, right, bottom = box
    width = right - left
    height = bottom - top
    draw.rounded_rectangle([left, top, right, bottom], radius=10, fill=(7, 12, 18), outline=(40, 52, 66), width=1)
    draw.text((left + 12, top + 10), title, fill=(226, 232, 240), font=font(17, True))
    if not bars:
        draw.text((left + 12, top + 44), "MT5 bars unavailable", fill=(148, 163, 184), font=font(14))
        return

    chart_top = top + 40
    chart_bottom = bottom - 28
    chart_height = chart_bottom - chart_top
    high = max(max(bar.high for bar in bars), as_float(trade.get("targetPrice")), as_float(trade.get("stopPrice")))
    low = min(min(bar.low for bar in bars), as_float(trade.get("targetPrice")), as_float(trade.get("stopPrice")))
    padding = max((high - low) * 0.05, 0.01)
    high += padding
    low -= padding
    candle_width = max(3, int(width / max(len(bars), 1) * 0.55))
    step = width / max(len(bars), 1)

    for grid in range(1, 4):
        y = chart_top + grid * chart_height // 4
        draw.line([left + 8, y, right - 8, y], fill=(28, 37, 49), width=1)

    for index, bar in enumerate(bars):
        x = bar_to_x(index, len(bars), left, width)
        y_high = price_to_y(bar.high, high, low, chart_top, chart_height)
        y_low = price_to_y(bar.low, high, low, chart_top, chart_height)
        y_open = price_to_y(bar.open, high, low, chart_top, chart_height)
        y_close = price_to_y(bar.close, high, low, chart_top, chart_height)
        candle_color = (45, 212, 191) if bar.close >= bar.open else (248, 113, 113)
        draw.line([x, y_high, x, y_low], fill=candle_color, width=1)
        draw.rectangle([x - candle_width, min(y_open, y_close), x + candle_width, max(y_open, y_close) + 1], fill=candle_color)

    levels = [
        ("Entry", as_float(trade.get("entryPrice")), (96, 165, 250)),
        ("SL", as_float(trade.get("stopPrice")), (248, 113, 113)),
        ("TP", as_float(trade.get("targetPrice")), (52, 211, 153)),
        ("Exit", as_float(trade.get("exitPrice")), (251, 191, 36)),
    ]
    for label, price, color in levels:
        if price <= 0:
            continue
        y = price_to_y(price, high, low, chart_top, chart_height)
        draw.line([left + 8, y, right - 8, y], fill=color, width=1)
        draw.text((right - 72, y - 9), label, fill=color, font=font(12, True))

    if analysis.get("available"):
        eq = as_float(analysis.get("equilibrium"))
        if eq:
            y = price_to_y(eq, high, low, chart_top, chart_height)
            draw.line([left + 8, y, right - 8, y], fill=(148, 163, 184), width=1)
            draw.text((left + 12, y - 15), "EQ", fill=(148, 163, 184), font=font(11, True))
        sweep_level = analysis.get("sweepLevel")
        sweep_index = analysis.get("sweepIndex")
        if isinstance(sweep_level, (int, float)) and isinstance(sweep_index, int):
            y = price_to_y(as_float(sweep_level), high, low, chart_top, chart_height)
            x = bar_to_x(sweep_index, len(bars), left, width)
            dashed_line(draw, (x, y, right - 8, y), fill=(248, 113, 113), width=2, dash=7)
            draw.text((x + 8, y + 4), "Sweep", fill=(248, 113, 113), font=font(11, True))

        choch_level = analysis.get("chochLevel")
        choch_index = analysis.get("chochIndex")
        if isinstance(choch_level, (int, float)) and isinstance(choch_index, int):
            y = price_to_y(as_float(choch_level), high, low, chart_top, chart_height)
            x = bar_to_x(choch_index, len(bars), left, width)
            dashed_line(draw, (x, y, right - 8, y), fill=(96, 165, 250), width=2, dash=7)
            draw.text((x + 8, y - 17), "CHoCH", fill=(96, 165, 250), font=font(11, True))

        for zone in analysis.get("fvgZones") or []:
            if not isinstance(zone, dict):
                continue
            start_index = as_int(zone.get("startIndex"))
            end_index = as_int(zone.get("index"))
            top_price = as_float(zone.get("top"))
            bottom_price = as_float(zone.get("bottom"))
            if not top_price or not bottom_price:
                continue
            x1 = bar_to_x(start_index, len(bars), left, width)
            x2 = min(right - 8, bar_to_x(end_index + 5, len(bars), left, width))
            y1 = price_to_y(top_price, high, low, chart_top, chart_height)
            y2 = price_to_y(bottom_price, high, low, chart_top, chart_height)
            color = (251, 191, 36) if zone.get("nearEntry") else (148, 163, 184)
            draw.rectangle([x1, min(y1, y2), x2, max(y1, y2)], outline=color, width=2)
            draw.text((x1 + 4, min(y1, y2) + 3), "FVG", fill=color, font=font(10, True))

        text = (
            f"{analysis.get('location')} · {analysis.get('sweepLabel')} · "
            f"{analysis.get('chochLabel')} · FVG {'Y' if analysis.get('freshFvgNearEntry') else 'N'}"
        )
        draw.text((left + 12, bottom - 23), text, fill=(203, 213, 225), font=font(12))


def build_feedback_image(
    trade: dict[str, Any],
    mtf_bars: dict[str, list[Bar]],
    analyses: dict[str, dict[str, Any]],
    selected_timeframes: list[dict[str, Any]],
) -> Image.Image:
    canvas = Image.new("RGB", (1180, 1680), (3, 7, 12))
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.text((48, 30), "Arthur / ICT Study Board", fill=(45, 212, 191), font=font(34, True))
    draw.text(
        (48, 78),
        f"{trade.get('symbol')} {str(trade.get('direction')).upper()} | {trade.get('date')} | PnL {as_float(trade.get('brokerPnl')):.2f}",
        fill=(248, 250, 252),
        font=font(23, True),
    )
    draw_label(draw, (900, 42), "MTF evidence board", (13, 76, 70), (153, 246, 228), 13)

    panel_boxes = {
        "htf": (48, 135, 1132, 545),
        "context": (48, 575, 1132, 985),
        "ltf": (48, 1015, 1132, 1425),
    }
    selected_by_role = {str(item.get("role")): item for item in selected_timeframes}
    for role, box in panel_boxes.items():
        item = selected_by_role.get(role, {})
        timeframe = str(item.get("timeframe") or DEFAULT_SELECTED_TIMEFRAMES[0])
        reason = str(item.get("reason") or "구조 가시성 기준")
        if len(reason) > 72:
            reason = reason[:69] + "..."
        title = f"{ROLE_LABELS.get(role, role.upper())}: {timeframe} | {reason}"
        draw_learning_candle_panel(draw, mtf_bars.get(timeframe, []), box, title, trade, analyses.get(timeframe, {}))

    bottom_top = 1455
    draw.rounded_rectangle([48, bottom_top, 1132, 1635], radius=12, fill=(7, 12, 18), outline=(42, 55, 72), width=1)
    draw.text((70, bottom_top + 18), "Evidence notes", fill=(226, 232, 240), font=font(22, True))
    tf_map = selected_timeframe_map(selected_timeframes)
    htf = analyses.get(tf_map.get("htf", ""), {})
    context = analyses.get(tf_map.get("context", ""), {})
    ltf = analyses.get(tf_map.get("ltf", ""), {})
    selected_text = " / ".join(f"{ROLE_LABELS.get(str(item.get('role')), str(item.get('role')))} {item.get('timeframe')}" for item in selected_timeframes)
    notes = [
        f"Selected frames: {selected_text}.",
        f"HTF: {htf.get('location', 'unknown')} / {htf.get('trend', 'unknown')} / {htf.get('sweepLabel', 'unknown')}.",
        f"Context: {context.get('location', 'unknown')} / {context.get('trend', 'unknown')} / {context.get('sweepLabel', 'unknown')}.",
        f"LTF: {ltf.get('location', 'unknown')} / {ltf.get('trend', 'unknown')} / {ltf.get('chochLabel', 'unknown')}.",
    ]
    y = bottom_top + 58
    for note in notes:
        for wrapped in textwrap.wrap(note, width=116):
            draw.text((70, y), f"- {wrapped}", fill=(203, 213, 225), font=font(16))
            y += 28
    return canvas


def build_fallback_image(trade: dict[str, Any]) -> Image.Image:
    source = decode_data_url(str(trade.get("screenshot") or ""))
    if source is None:
        source = Image.new("RGB", (1400, 800), (3, 7, 12))
    if source.width > 1500:
        ratio = 1500 / source.width
        source = source.resize((1500, int(source.height * ratio)), Image.Resampling.LANCZOS)
    source = source.convert("RGBA")
    overlay = Image.new("RGBA", source.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle([34, 34, min(760, source.width - 34), 280], radius=16, fill=(7, 13, 18, 220), outline=(45, 212, 191), width=2)
    draw.text((56, 56), "AI Feedback - screenshot fallback", fill=(45, 212, 191), font=font(24, True))
    draw.text((56, 94), f"{trade.get('symbol')} {str(trade.get('direction')).upper()} · SL exit", fill=(248, 250, 252), font=font(28, True))
    lines = [
        "MT5 bars were unavailable, so this feedback used the saved chart image.",
        "Core issue: HTF map, liquidity sweep, LTF CHoCH and fresh FVG/OB were not documented.",
        "Treat this as a process failure until the full MTF sequence is proven.",
    ]
    y = 136
    for line in lines:
        for wrapped in textwrap.wrap(line, width=70):
            draw.text((56, y), wrapped, fill=(203, 213, 225), font=font(18))
            y += 28
    return Image.alpha_composite(source, overlay).convert("RGB")


def status_from_bool(value: bool | None) -> str:
    if value is True:
        return "pass"
    if value is False:
        return "fail"
    return "unknown"


def journal_note_lines(trade: dict[str, Any]) -> list[str]:
    fields = [
        ("진입 메모", "thesis"),
        ("잘한 점", "good"),
        ("아쉬운 점", "bad"),
        ("실수", "mistake"),
        ("교훈", "lesson"),
        ("감정", "emotion"),
    ]
    notes: list[str] = []
    for label, key in fields:
        value = trade.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            notes.append(f"{label}: {text}")
    tags = trade.get("tags")
    if isinstance(tags, list) and tags:
        clean_tags = [str(tag).strip() for tag in tags if str(tag).strip()]
        if clean_tags:
            notes.append("태그: " + ", ".join(clean_tags))
    return notes


def timeframe_summary(analyses: dict[str, dict[str, Any]], selected_timeframes: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    items = selected_timeframes or [{"role": "", "timeframe": timeframe, "reason": ""} for timeframe in DEFAULT_SELECTED_TIMEFRAMES]
    for item in items:
        timeframe = str(item.get("timeframe") or "")
        analysis = analyses.get(timeframe, {})
        summaries.append(
            {
                "role": item.get("role") or "",
                "timeframe": timeframe,
                "reason": item.get("reason") or "",
                "score": item.get("score"),
                "available": bool(analysis.get("available")),
                "location": analysis.get("location") or "unknown",
                "trend": analysis.get("trend") or "unknown",
                "sweep": analysis.get("sweepLabel") or "unknown",
                "choch": analysis.get("chochLabel") or "unknown",
                "fvg": bool(analysis.get("freshFvgNearEntry")),
            }
        )
    return summaries


def yn(value: Any) -> str:
    return "있음" if bool(value) else "없음"


def fmt_price(value: Any) -> str:
    price = as_float(value)
    return f"{price:.2f}" if price > 0 else "-"


def _coerce_text_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        text = str(value).strip() if value else ""
        return [text] if text else []
    output: list[str] = []
    for item in value:
        text = str(item).strip() if item is not None else ""
        if text:
            output.append(text)
    return output


def _coerce_score(raw: Any, fallback: int = 2) -> int:
    try:
        value = int(float(raw))
    except (TypeError, ValueError):
        return fallback
    if value < 0:
        return 0
    if value > 5:
        return 5
    return value


def analysis_fact_line(role: str, timeframe: str, analysis: dict[str, Any]) -> str:
    if not analysis.get("available"):
        return f"{role} {timeframe}: MT5 bars 없음"
    fvg_near = yn(analysis.get("freshFvgNearEntry"))
    ob_near = yn(analysis.get("freshObNearEntry"))
    sr_count = len(analysis.get("srLevels") or [])
    missing = ", ".join(str(item) for item in analysis.get("missingEvidence") or []) or "없음"
    trap = ", ".join(str(item) for item in analysis.get("trapReasons") or []) or "없음"
    return (
        f"{role} {timeframe}: 위치 {analysis.get('location', 'unknown')}, 흐름 {analysis.get('trend', 'unknown')}, "
        f"sweep {analysis.get('sweepLabel', 'unknown')}, CHoCH {analysis.get('chochLabel', 'unknown')}, "
        f"BOS {analysis.get('bosLabel', 'unknown')}, 진입부근 FVG {fvg_near}, OB {ob_near}, S/R {sr_count}개, "
        f"누락 {missing}, trap {trap}"
    )


def outcome_fact_line(trade: dict[str, Any], reward_risk: float) -> str:
    pnl = as_float(trade.get("brokerPnl"))
    direction = str(trade.get("direction") or "").lower()
    result = "수익" if pnl > 0 else "손실" if pnl < 0 else "본전"
    exit_price = as_float(trade.get("exitPrice"))
    stop = as_float(trade.get("stopPrice"))
    target = as_float(trade.get("targetPrice"))
    exit_context = "청산가 확인"
    if stop and exit_price:
        stopped = exit_price <= stop if direction == "long" else exit_price >= stop
        if stopped:
            exit_context = "SL 또는 SL 주변에서 종료"
    if target and exit_price:
        targeted = exit_price >= target if direction == "long" else exit_price <= target
        if targeted:
            exit_context = "TP 또는 TP 주변에서 종료"
    return (
        f"결과 {result}, PnL {pnl:.2f}, entry {fmt_price(trade.get('entryPrice'))}, "
        f"SL {fmt_price(stop)}, TP {fmt_price(target)}, exit {fmt_price(exit_price)}, "
        f"계획 손익비 {reward_risk:.2f}:1, 종료 맥락 {exit_context}"
    )


def build_feedback(
    trade: dict[str, Any],
    analyses: dict[str, dict[str, Any]],
    image: Image.Image,
    used_bars: bool,
    selected_timeframes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    direction = str(trade.get("direction") or "").lower()
    selected_timeframes = selected_timeframes or [
        {"role": "htf", "timeframe": "M30", "reason": "기본 HTF"},
        {"role": "context", "timeframe": "M5", "reason": "기본 context"},
        {"role": "ltf", "timeframe": "M1", "reason": "기본 LTF"},
    ]
    tf_map = selected_timeframe_map(selected_timeframes)
    htf_tf = tf_map.get("htf", "M30")
    context_tf = tf_map.get("context", "M5")
    ltf_tf = tf_map.get("ltf", "M1")
    htf_analysis = analyses.get(htf_tf, {})
    context_analysis = analyses.get(context_tf, {})
    ltf_analysis = analyses.get(ltf_tf, {})
    desired_location = "discount" if direction == "long" else "premium"
    htf_location_ok = htf_analysis.get("available") and htf_analysis.get("location") == desired_location
    ltf_sweep_ok = bool(ltf_analysis.get("sweepFound") or context_analysis.get("sweepFound"))
    ltf_choch_ok = bool(ltf_analysis.get("chochFound") or context_analysis.get("chochFound"))
    ltf_bos_ok = bool(ltf_analysis.get("bosFound") or context_analysis.get("bosFound"))
    fvg_ok = bool(ltf_analysis.get("freshFvgNearEntry") or context_analysis.get("freshFvgNearEntry"))
    ob_ok = bool(ltf_analysis.get("freshObNearEntry") or context_analysis.get("freshObNearEntry"))
    entry_zone_ok = bool(fvg_ok or ob_ok)
    trap_reasons = [*htf_analysis.get("trapReasons", []), *context_analysis.get("trapReasons", []), *ltf_analysis.get("trapReasons", [])]
    has_sl_tp = as_float(trade.get("stopPrice")) > 0 and as_float(trade.get("targetPrice")) > 0
    reward_risk = 0.0
    entry = as_float(trade.get("entryPrice"))
    stop = as_float(trade.get("stopPrice"))
    target = as_float(trade.get("targetPrice"))
    if entry and stop and target:
        reward_risk = abs(target - entry) / max(abs(entry - stop), 1e-9)
    journal_notes = journal_note_lines(trade)
    journal_summary = " / ".join(journal_notes[:3]) if journal_notes else "일지 메모가 비어 있어 진입 당시 사고 과정을 확인할 수 없다."
    selected_by_role = {str(item.get("role")): item for item in selected_timeframes}
    htf_label = f"{htf_tf} ({selected_by_role.get('htf', {}).get('reason', '선택 이유 없음')})"
    context_label = f"{context_tf} ({selected_by_role.get('context', {}).get('reason', '선택 이유 없음')})"
    ltf_label = f"{ltf_tf} ({selected_by_role.get('ltf', {}).get('reason', '선택 이유 없음')})"
    outcome_line = outcome_fact_line(trade, reward_risk)
    fact_lines = [
        outcome_line,
        analysis_fact_line("HTF", htf_tf, htf_analysis),
        analysis_fact_line("Context", context_tf, context_analysis),
        analysis_fact_line("LTF", ltf_tf, ltf_analysis),
    ]

    checklist = [
        {
            "label": "HTF map",
            "status": status_from_bool(bool(htf_location_ok) if used_bars else None),
            "detail": f"{htf_tf} 기준 진입 위치는 {htf_analysis.get('location', 'unknown')}로 판정됐다. {direction} 기준 선호 위치는 {desired_location}이다.",
        },
        {
            "label": "Liquidity sweep",
            "status": status_from_bool(ltf_sweep_ok if used_bars else None),
            "detail": f"{context_tf}/{ltf_tf} sweep 판정: {context_analysis.get('sweepLabel', 'unknown')} / {ltf_analysis.get('sweepLabel', 'unknown')}.",
        },
        {
            "label": "LTF CHoCH",
            "status": status_from_bool(ltf_choch_ok if used_bars else None),
            "detail": f"{context_tf}/{ltf_tf} CHoCH 판정: {context_analysis.get('chochLabel', 'unknown')} / {ltf_analysis.get('chochLabel', 'unknown')}.",
        },
        {
            "label": "FVG / OB entry",
            "status": status_from_bool(entry_zone_ok if used_bars else None),
            "detail": f"진입 주변 zone: FVG {context_tf}={bool(context_analysis.get('freshFvgNearEntry'))}, {ltf_tf}={bool(ltf_analysis.get('freshFvgNearEntry'))}; OB {context_tf}={bool(context_analysis.get('freshObNearEntry'))}, {ltf_tf}={bool(ltf_analysis.get('freshObNearEntry'))}.",
        },
        {
            "label": "BOS continuation",
            "status": status_from_bool(ltf_bos_ok if used_bars else None),
            "detail": f"{context_tf}/{ltf_tf} BOS 판정: {context_analysis.get('bosLabel', 'unknown')} / {ltf_analysis.get('bosLabel', 'unknown')}. CHoCH 이후 continuation 확인용이다.",
        },
        {
            "label": "Trap risk",
            "status": status_from_bool(not trap_reasons if used_bars else None),
            "detail": ", ".join(dict.fromkeys(str(item) for item in trap_reasons)) if trap_reasons else "뚜렷한 자동 탐지 trap risk는 없다.",
        },
        {
            "label": "SL / TP",
            "status": status_from_bool(has_sl_tp),
            "detail": f"SL {stop:.2f}, TP {target:.2f}, 계획 손익비 약 {reward_risk:.2f}:1.",
        },
    ]

    verdict = (
        "이 항목은 자동 피드백이 아니라 Codex 심층 리뷰를 위한 MTF 근거 보드다. "
        f"선택 프레임은 HTF {htf_label}, Context {context_label}, LTF {ltf_label}이다."
    )
    if not used_bars:
        verdict = (
            "MT5 bars를 불러오지 못해 저장된 차트 이미지와 매매일지 기록만 근거 자료로 남겼다. "
            "이 상태에서는 Codex 심층 리뷰 전에 차트 데이터 보강이 필요하다."
        )

    return {
        "id": f"ai-feedback:{trade.get('id')}",
        "generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "mentor": "자동 MTF 근거 추출",
        "version": AI_FEEDBACK_VERSION,
        "usedBars": used_bars,
        "analysisSource": "mt5-bars" if used_bars else "screenshot-fallback",
        "timeframes": timeframe_summary(analyses, selected_timeframes),
        "selectedTimeframes": selected_timeframes,
        "journalNotes": journal_notes,
        "title": "MTF 차트 근거 보드",
        "verdict": verdict,
        "score": 2,
        "chartImage": encode_png_data_url(image),
        "chartImageName": f"{trade.get('symbol')}_{trade.get('brokerMeta', {}).get('positionId') or trade.get('id')}_ai_mtf_feedback.png",
        "summary": " / ".join(fact_lines),
        "checklist": checklist,
        "feedback": [],
        "improvements": [],
        "nextRules": [],
        "chartNotes": [
            f"일지 메모 반영: {journal_summary}",
            *fact_lines,
            "이 보드는 최종 피드백이 아니라, Codex가 거래별 시나리오를 직접 해석할 때 쓰는 근거 자료다.",
        ],
    }


def generate_feedback(trade_id: str | None = None) -> dict[str, Any]:
    trade = load_trade(trade_id)
    open_time = parse_trade_time(trade, "openTime")
    close_time = parse_trade_time(trade, "closeTime")
    symbol = str(trade.get("symbol") or "").upper()
    mtf_bars: dict[str, list[Bar]] = {}
    analyses: dict[str, dict[str, Any]] = {}
    selected_timeframes: list[dict[str, Any]] = []
    used_bars = False
    try:
        focus_counts = {"D1": 24, "H4": 42, "H1": 60, "M30": 64, "M15": 72, "M5": 86, "M1": 110}
        for timeframe in CANDIDATE_TIMEFRAMES:
            _, bars = fetch_bars(symbol, timeframe, open_time - timedelta(days=3), close_time + timedelta(days=1))
            mtf_bars[timeframe] = focus_bars(bars, open_time, close_time, focus_counts.get(timeframe, 90))
            analyses[timeframe] = analyze_timeframe(
                mtf_bars[timeframe],
                str(trade.get("direction") or ""),
                open_time,
                as_float(trade.get("entryPrice")),
                close_time,
            )
        selected_timeframes = select_timeframes(analyses, str(trade.get("direction") or ""), open_time, close_time)
        used_bars = any(mtf_bars.values())
        image = build_feedback_image(trade, mtf_bars, analyses, selected_timeframes)
    except Exception as exc:
        analyses = {"fallback": {"error": str(exc)}}
        image = build_fallback_image(trade)

    feedback = build_feedback(trade, analyses, image, used_bars, selected_timeframes)
    if analyses.get("fallback", {}).get("error"):
        feedback["chartNotes"] = [
            *(feedback.get("chartNotes") or []),
            f"MT5 bars fallback reason: {analyses['fallback']['error']}",
        ]
    trade["aiFeedback"] = feedback
    save_trade(trade)
    return {
        "ok": True,
        "tradeId": trade.get("id"),
        "usedBars": used_bars,
        "feedback": feedback,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Arthur/ICT AI feedback for a journal trade.")
    parser.add_argument("--trade-id", default="", help="Specific trade id. Defaults to earliest losing closed trade.")
    args = parser.parse_args()
    result = generate_feedback(args.trade_id or None)
    printable = {**result, "feedback": {**result["feedback"], "chartImage": f"<{len(result['feedback'].get('chartImage', ''))} chars>"}}
    print(json.dumps(printable, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
