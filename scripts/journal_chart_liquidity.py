from __future__ import annotations

import math
from typing import Any


def value(bar: Any, key: str) -> float:
    raw = getattr(bar, key, None)
    if raw is None and isinstance(bar, dict):
        raw = bar.get(key)
    try:
        return float(raw)
    except Exception:
        return 0.0


def bar_time(bar: Any) -> Any:
    if isinstance(bar, dict):
        return bar.get("time")
    return getattr(bar, "time", None)


def average_range(bars: list[Any]) -> float:
    if not bars:
        return 0.0
    return sum(max(value(bar, "high") - value(bar, "low"), 0.0) for bar in bars) / len(bars)


def pivot_indexes(bars: list[Any], length: int = 4) -> tuple[list[int], list[int]]:
    highs: list[int] = []
    lows: list[int] = []
    if len(bars) < length * 2 + 1:
        return highs, lows
    for index in range(length, len(bars) - length):
        high = value(bars[index], "high")
        low = value(bars[index], "low")
        left = bars[index - length : index]
        right = bars[index + 1 : index + length + 1]
        if all(high > value(bar, "high") for bar in left + right):
            highs.append(index)
        if all(low < value(bar, "low") for bar in left + right):
            lows.append(index)
    return highs, lows


def _cluster_pivots(bars: list[Any], indexes: list[int], side: str, tolerance: float) -> list[dict[str, Any]]:
    clusters: list[dict[str, Any]] = []
    price_key = "high" if side == "bsl" else "low"
    for index in indexes:
        price = value(bars[index], price_key)
        matched: dict[str, Any] | None = None
        for cluster in clusters:
            if abs(price - float(cluster["level"])) <= tolerance:
                matched = cluster
                break
        if matched is None:
            matched = {"side": side, "indexes": [], "prices": [], "level": price}
            clusters.append(matched)
        matched["indexes"].append(index)
        matched["prices"].append(price)
        if side == "bsl":
            matched["level"] = max(float(matched["level"]), price)
        else:
            matched["level"] = min(float(matched["level"]), price)
    return clusters


def _swing_prominence(bars: list[Any], index: int, side: str, radius: int, atr: float) -> float:
    start = max(0, index - radius)
    end = min(len(bars), index + radius + 1)
    window = bars[start:end]
    if not window or atr <= 0:
        return 0.0
    if side == "bsl":
        level = value(bars[index], "high")
        left_low = min(value(bar, "low") for bar in bars[start : index + 1])
        right_low = min(value(bar, "low") for bar in bars[index:end])
        return max(0.0, min(level - left_low, level - right_low) / atr)
    level = value(bars[index], "low")
    left_high = max(value(bar, "high") for bar in bars[start : index + 1])
    right_high = max(value(bar, "high") for bar in bars[index:end])
    return max(0.0, min(left_high - level, right_high - level) / atr)


def _level_status(bars: list[Any], level: float, side: str, after_index: int, tolerance: float) -> tuple[str, int | None]:
    status = "open"
    event_index: int | None = None
    for index in range(after_index + 1, len(bars)):
        high = value(bars[index], "high")
        low = value(bars[index], "low")
        close = value(bars[index], "close")
        if side == "bsl":
            if close > level + tolerance:
                return "accepted", index
            if high > level + tolerance and close < level:
                status = "swept"
                event_index = index
        else:
            if close < level - tolerance:
                return "accepted", index
            if low < level - tolerance and close > level:
                status = "swept"
                event_index = index
    return status, event_index


def _score_cluster(
    bars: list[Any],
    cluster: dict[str, Any],
    side: str,
    current_price: float,
    tolerance: float,
    atr: float,
) -> dict[str, Any]:
    indexes = [int(index) for index in cluster["indexes"]]
    prices = [float(price) for price in cluster["prices"]]
    level = float(cluster["level"])
    latest_index = max(indexes)
    first_index = min(indexes)
    lookback = max(len(bars) - 1, 1)
    age = len(bars) - 1 - latest_index
    prominence = max(_swing_prominence(bars, index, side, 12, atr) for index in indexes) if indexes else 0.0
    status, status_index = _level_status(bars, level, side, latest_index, tolerance)

    high_range = max(value(bar, "high") for bar in bars)
    low_range = min(value(bar, "low") for bar in bars)
    total_range = max(high_range - low_range, tolerance)
    in_external_band = level >= low_range + total_range * 0.68 if side == "bsl" else level <= low_range + total_range * 0.32
    ahead_of_price = level > current_price + tolerance if side == "bsl" else level < current_price - tolerance
    equal_touch_bonus = min(max(len(indexes) - 1, 0), 4) * 1.35
    prominence_bonus = min(prominence, 6.0) * 0.75
    recency_bonus = max(0.0, 1.2 * (1.0 - age / lookback))
    external_bonus = 1.8 if in_external_band else 0.0
    status_bonus = {"open": 1.3, "swept": -0.5, "accepted": -2.0}.get(status, 0.0)
    ahead_bonus = 0.7 if ahead_of_price else -0.4
    score = 1.0 + equal_touch_bonus + prominence_bonus + recency_bonus + external_bonus + status_bonus + ahead_bonus

    if score >= 7.0 and in_external_band:
        grade = "external"
    elif score >= 4.8:
        grade = "major"
    else:
        grade = "minor"

    reasons: list[str] = []
    if len(indexes) >= 2:
        reasons.append(f"equal x{len(indexes)}")
    if in_external_band:
        reasons.append("external band")
    if prominence >= 2.0:
        reasons.append("clear swing")
    if status == "open":
        reasons.append("unswept")
    elif status == "swept":
        reasons.append("already swept")
    elif status == "accepted":
        reasons.append("accepted/consumed")
    if ahead_of_price:
        reasons.append("ahead of price")

    return {
        "side": side,
        "label": "BSL" if side == "bsl" else "SSL",
        "level": level,
        "index": latest_index,
        "firstIndex": first_index,
        "touches": len(indexes),
        "touchIndexes": indexes,
        "prices": prices,
        "status": status,
        "statusIndex": status_index,
        "score": round(score, 2),
        "grade": grade,
        "external": in_external_band,
        "aheadOfPrice": ahead_of_price,
        "time": bar_time(bars[latest_index]),
        "reasons": reasons,
    }


def _sort_relevant(levels: list[dict[str, Any]], side: str, current_price: float) -> list[dict[str, Any]]:
    if side == "bsl":
        return sorted(levels, key=lambda item: (not bool(item.get("aheadOfPrice")), -float(item.get("score", 0)), abs(float(item["level"]) - current_price)))
    return sorted(levels, key=lambda item: (not bool(item.get("aheadOfPrice")), -float(item.get("score", 0)), abs(float(item["level"]) - current_price)))


def build_liquidity_profile(bars: list[Any], current_price: float, pivot_len: int = 4) -> dict[str, Any]:
    if not bars:
        return {"bsl": [], "ssl": [], "rangeHigh": None, "rangeLow": None, "equilibrium": None}

    highs, lows = pivot_indexes(bars, pivot_len)
    atr = max(average_range(bars[-80:]), average_range(bars), 0.01)
    reference_price = max(abs(current_price), 1.0)
    tolerance = max(atr * 0.22, reference_price * 0.00028)
    bsl_clusters = _cluster_pivots(bars, highs, "bsl", tolerance)
    ssl_clusters = _cluster_pivots(bars, lows, "ssl", tolerance)
    bsl = [_score_cluster(bars, cluster, "bsl", current_price, tolerance, atr) for cluster in bsl_clusters]
    ssl = [_score_cluster(bars, cluster, "ssl", current_price, tolerance, atr) for cluster in ssl_clusters]

    relevant_bsl = [item for item in bsl if item["status"] != "accepted" and item["grade"] != "minor"]
    relevant_ssl = [item for item in ssl if item["status"] != "accepted" and item["grade"] != "minor"]
    if not relevant_bsl:
        relevant_bsl = [item for item in bsl if item["status"] != "accepted"] or bsl
    if not relevant_ssl:
        relevant_ssl = [item for item in ssl if item["status"] != "accepted"] or ssl

    bsl_sorted = _sort_relevant(relevant_bsl, "bsl", current_price)
    ssl_sorted = _sort_relevant(relevant_ssl, "ssl", current_price)
    range_high = next((item for item in bsl_sorted if float(item["level"]) > current_price), bsl_sorted[0] if bsl_sorted else None)
    range_low = next((item for item in ssl_sorted if float(item["level"]) < current_price), ssl_sorted[0] if ssl_sorted else None)

    if range_high and range_low and float(range_high["level"]) <= float(range_low["level"]):
        all_high = max(value(bar, "high") for bar in bars)
        all_low = min(value(bar, "low") for bar in bars)
        range_high = {"side": "bsl", "label": "BSL", "level": all_high, "index": max(range(len(bars)), key=lambda idx: value(bars[idx], "high")), "grade": "fallback", "score": 0, "status": "range"}
        range_low = {"side": "ssl", "label": "SSL", "level": all_low, "index": min(range(len(bars)), key=lambda idx: value(bars[idx], "low")), "grade": "fallback", "score": 0, "status": "range"}

    eq = (float(range_high["level"]) + float(range_low["level"])) / 2.0 if range_high and range_low else None
    return {
        "pivotHighs": highs,
        "pivotLows": lows,
        "tolerance": tolerance,
        "atr": atr,
        "bsl": sorted(bsl, key=lambda item: float(item["score"]), reverse=True),
        "ssl": sorted(ssl, key=lambda item: float(item["score"]), reverse=True),
        "relevantBsl": bsl_sorted,
        "relevantSsl": ssl_sorted,
        "rangeHigh": range_high,
        "rangeLow": range_low,
        "equilibrium": eq,
    }


def support_resistance_from_liquidity(profile: dict[str, Any], limit: int = 4) -> list[dict[str, Any]]:
    levels: list[dict[str, Any]] = []
    for item in (profile.get("relevantBsl") or [])[:limit]:
        levels.append(
            {
                "index": item.get("index"),
                "level": item.get("level"),
                "label": f"{item.get('grade', 'major').upper()} BSL",
                "kind": "resistance",
                "score": item.get("score"),
                "status": item.get("status"),
                "reasons": item.get("reasons", []),
            }
        )
    for item in (profile.get("relevantSsl") or [])[:limit]:
        levels.append(
            {
                "index": item.get("index"),
                "level": item.get("level"),
                "label": f"{item.get('grade', 'major').upper()} SSL",
                "kind": "support",
                "score": item.get("score"),
                "status": item.get("status"),
                "reasons": item.get("reasons", []),
            }
        )
    return sorted(levels, key=lambda item: float(item.get("score") or 0), reverse=True)[: limit * 2]


def find_liquidity_sweep_event(
    bars: list[Any],
    direction: str,
    profile: dict[str, Any],
    start: int,
    end: int,
) -> dict[str, Any]:
    side = "ssl" if direction == "long" else "bsl"
    candidates = profile.get("relevantSsl") if side == "ssl" else profile.get("relevantBsl")
    candidates = [item for item in (candidates or []) if item.get("status") != "accepted"]
    candidates = sorted(candidates, key=lambda item: float(item.get("score") or 0), reverse=True)[:8]
    for index in range(max(0, start), min(end + 1, len(bars))):
        for item in candidates:
            level = float(item.get("level") or 0)
            pivot_index = int(item.get("index") or 0)
            if pivot_index >= index or level <= 0:
                continue
            if side == "ssl" and value(bars[index], "low") < level and value(bars[index], "close") > level:
                return {"found": True, "index": index, "level": level, "label": "SSL sweep", "liquidity": item}
            if side == "bsl" and value(bars[index], "high") > level and value(bars[index], "close") < level:
                return {"found": True, "index": index, "level": level, "label": "BSL sweep", "liquidity": item}
    return {"found": False, "index": None, "level": None, "label": f"no {'SSL' if side == 'ssl' else 'BSL'} sweep"}
