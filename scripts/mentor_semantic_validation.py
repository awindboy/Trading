"""Fail-closed OHLC validation for manually declared Mentor replay evidence.

Narrative fields are never treated as proof. Every required trading element
must have a price/time witness that can be checked against already-confirmed
bars at the decision timestamp.
"""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any, Iterable


UTC = timezone.utc
TF_SECONDS = {
    "H4": 4 * 60 * 60,
    "H1": 60 * 60,
    "M30": 30 * 60,
    "M15": 15 * 60,
    "M5": 5 * 60,
    "M1": 60,
}
TF_DESCENDING = ("H4", "H1", "M30", "M15", "M5", "M1")


def parse_time(value: Any) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return int(parsed.astimezone(UTC).timestamp())


def iso(timestamp: int | None) -> str | None:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(int(timestamp), tz=UTC).isoformat()


def _value(bar: Any, key: str) -> Any:
    if isinstance(bar, dict):
        return bar[key]
    return bar[key].item() if hasattr(bar[key], "item") else bar[key]


def _rows(values: Iterable[Any]) -> list[Any]:
    return list(values)


def _available_at(bar: Any, timeframe: str) -> int:
    if isinstance(bar, dict) and "available" in bar:
        return int(bar["available"])
    names = getattr(getattr(bar, "dtype", None), "names", None) or ()
    if "available" in names:
        return int(_value(bar, "available"))
    return int(_value(bar, "time")) + TF_SECONDS[timeframe]


def _confirmed(series: dict[str, Any], timeframe: str, cutoff: int) -> list[Any]:
    return [
        bar
        for bar in _rows(series.get(timeframe, []))
        if _available_at(bar, timeframe) <= cutoff
    ]


def _bar_at(
    series: dict[str, Any],
    timeframe: str,
    open_time: int,
    cutoff: int,
) -> Any | None:
    for bar in _confirmed(series, timeframe, cutoff):
        if int(_value(bar, "time")) == open_time:
            return bar
    return None


def _price_matches(left: float, right: float, point: float) -> bool:
    return abs(float(left) - float(right)) <= max(abs(point) * 1.1, 1e-9)


def _zone_kind(zone: dict[str, Any]) -> str:
    value = f"{zone.get('type', '')} {zone.get('label', '')}".upper()
    if "FVG" in value:
        return "FVG"
    if re.search(r"\bOB\b", value) or "OB_" in value:
        return "OB"
    return "UNKNOWN"


def _origin_time(zone: dict[str, Any]) -> int | None:
    if zone.get("formedAt") not in (None, ""):
        return parse_time(zone["formedAt"])
    matched = re.search(
        r"(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})",
        str(zone.get("originCandles") or ""),
    )
    if not matched:
        return None
    return parse_time(f"{matched.group(1)}T{matched.group(2)}:00+00:00")


def _check(
    element: str,
    code: str,
    valid: bool,
    reason: str,
    *,
    evidence: dict[str, Any] | None = None,
    required: bool = True,
) -> dict[str, Any]:
    return {
        "element": element,
        "code": code,
        "valid": bool(valid),
        "required": bool(required),
        "reason": reason,
        **({"evidence": evidence} if evidence else {}),
    }


def _element_valid(checks: list[dict[str, Any]], element: str) -> bool:
    selected = [item for item in checks if item["element"] == element and item["required"]]
    return bool(selected) and all(item["valid"] for item in selected)


def validate_raw_fvg(
    series: dict[str, Any],
    timeframe: str,
    zone: dict[str, Any],
    direction: str,
    cutoff: int,
    point: float,
    *,
    element: str,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    checks: list[dict[str, Any]] = []
    origin = _origin_time(zone)
    checks.append(
        _check(
            element,
            "FVG_ORIGIN_DECLARED",
            origin is not None,
            "FVG third-candle open time is explicitly declared."
            if origin is not None
            else "FVG formedAt is missing; narrative text cannot identify a raw gap.",
        )
    )
    if origin is None:
        return checks, None
    bars = _confirmed(series, timeframe, cutoff)
    index = next(
        (position for position, bar in enumerate(bars) if int(_value(bar, "time")) == origin),
        None,
    )
    if index is None or index < 2:
        checks.append(
            _check(
                element,
                "FVG_THREE_BARS_AVAILABLE",
                False,
                "The declared third candle and its two predecessors are not confirmed by the decision time.",
            )
        )
        return checks, None
    first, middle, third = bars[index - 2], bars[index - 1], bars[index]
    consecutive = (
        int(_value(middle, "time")) - int(_value(first, "time")) == TF_SECONDS[timeframe]
        and int(_value(third, "time")) - int(_value(middle, "time")) == TF_SECONDS[timeframe]
    )
    checks.append(
        _check(
            element,
            "FVG_CONSECUTIVE_BARS",
            consecutive,
            "The FVG uses three consecutive confirmed candles."
            if consecutive
            else "The declared FVG spans missing or non-consecutive candles.",
        )
    )
    if direction == "long":
        actual_low = float(_value(first, "high"))
        actual_high = float(_value(third, "low"))
    else:
        actual_low = float(_value(third, "high"))
        actual_high = float(_value(first, "low"))
    gap_exists = actual_high > actual_low
    geometry = (
        gap_exists
        and _price_matches(actual_low, float(zone["low"]), point)
        and _price_matches(actual_high, float(zone["high"]), point)
    )
    checks.append(
        _check(
            element,
            "FVG_WICK_GAP_GEOMETRY",
            geometry,
            (
                f"Raw three-candle wick gap matches {actual_low:.2f}-{actual_high:.2f}."
                if geometry
                else (
                    f"Declared {float(zone['low']):.2f}-{float(zone['high']):.2f} is not the "
                    f"raw three-candle gap {actual_low:.2f}-{actual_high:.2f}."
                )
            ),
            evidence={
                "firstAt": iso(int(_value(first, "time"))),
                "middleAt": iso(int(_value(middle, "time"))),
                "thirdAt": iso(int(_value(third, "time"))),
                "actualLow": actual_low,
                "actualHigh": actual_high,
            },
        )
    )
    return checks, {
        "originTime": origin,
        "firstTime": int(_value(first, "time")),
        "middleTime": int(_value(middle, "time")),
        "thirdTime": int(_value(third, "time")),
        "actualLow": actual_low,
        "actualHigh": actual_high,
    }


def validate_raw_ob(
    series: dict[str, Any],
    timeframe: str,
    zone: dict[str, Any],
    direction: str,
    cutoff: int,
    point: float,
    *,
    element: str,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    checks: list[dict[str, Any]] = []
    origin = _origin_time(zone)
    checks.append(
        _check(
            element,
            "OB_ORIGIN_DECLARED",
            origin is not None,
            "OB origin candle time is explicitly declared."
            if origin is not None
            else "OB formedAt is missing; a narrative description is not proof.",
        )
    )
    if origin is None:
        return checks, None
    bar = _bar_at(series, timeframe, origin, cutoff)
    checks.append(
        _check(
            element,
            "OB_ORIGIN_CONFIRMED",
            bar is not None,
            "The declared OB origin is a confirmed raw candle."
            if bar is not None
            else "The declared OB origin candle is unavailable at the decision time.",
        )
    )
    if bar is None:
        return checks, None
    actual_low = float(_value(bar, "low"))
    actual_high = float(_value(bar, "high"))
    geometry = (
        _price_matches(actual_low, float(zone["low"]), point)
        and _price_matches(actual_high, float(zone["high"]), point)
    )
    checks.append(
        _check(
            element,
            "OB_CANDLE_GEOMETRY",
            geometry,
            (
                f"Declared OB range matches the raw candle {actual_low:.2f}-{actual_high:.2f}."
                if geometry
                else (
                    f"Declared {float(zone['low']):.2f}-{float(zone['high']):.2f} does not match "
                    f"the origin candle {actual_low:.2f}-{actual_high:.2f}."
                )
            ),
            evidence={"originAt": iso(origin), "actualLow": actual_low, "actualHigh": actual_high},
        )
    )
    opposite = (
        float(_value(bar, "close")) < float(_value(bar, "open"))
        if direction == "long"
        else float(_value(bar, "close")) > float(_value(bar, "open"))
    )
    checks.append(
        _check(
            element,
            "OB_OPPOSITE_CANDLE",
            opposite,
            "The origin candle is opposite to the intended delivery direction."
            if opposite
            else "The origin candle is not opposite to the intended delivery direction.",
        )
    )
    return checks, {
        "originTime": origin,
        "actualLow": actual_low,
        "actualHigh": actual_high,
    }


def validate_causal_ob(
    series: dict[str, Any],
    timeframe: str,
    zone: dict[str, Any],
    direction: str,
    cutoff: int,
    point: float,
    *,
    element: str,
    touch_at: int | None,
    upper_bound: int,
    require_touch: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    checks, raw = validate_raw_ob(
        series,
        timeframe,
        zone,
        direction,
        cutoff,
        point,
        element=element,
    )
    if raw is None:
        return checks, None
    origin = int(raw["originTime"])
    confirmed = _confirmed(series, timeframe, min(cutoff, upper_bound))
    departure_bar = next(
        (
            bar
            for bar in confirmed
            if int(_value(bar, "time")) > origin
            and (
                float(_value(bar, "close")) > float(zone["high"])
                if direction == "long"
                else float(_value(bar, "close")) < float(zone["low"])
            )
        ),
        None,
    )
    checks.append(
        _check(
            element,
            "OB_CONFIRMED_DEPARTURE",
            departure_bar is not None,
            (
                f"Price closed outside the OB at {iso(int(_value(departure_bar, 'time')))}."
                if departure_bar is not None
                else "Price never closed outside the declared OB before its alleged reaction/sweep."
            ),
            evidence=(
                {
                    "departureAt": iso(int(_value(departure_bar, "time"))),
                    "departureClose": float(_value(departure_bar, "close")),
                }
                if departure_bar is not None
                else None
            ),
        )
    )

    required_witness = ("breakLevel", "breakLevelFormedAt", "breakAt")
    witness_present = all(zone.get(key) not in (None, "") for key in required_witness)
    checks.append(
        _check(
            element,
            "OB_STRUCTURED_BREAK_WITNESS",
            witness_present,
            "The protected level and body-break candle are numeric, time-stamped evidence."
            if witness_present
            else (
                "Structured breakLevel, breakLevelFormedAt, and breakAt are required; "
                "displacementAndStructureRole text is not evidence."
            ),
        )
    )
    if witness_present:
        level = float(zone["breakLevel"])
        level_time = parse_time(zone["breakLevelFormedAt"])
        break_at = parse_time(zone["breakAt"])
        level_bar = _bar_at(series, timeframe, level_time, cutoff)
        break_bar = _bar_at(series, timeframe, break_at, cutoff)
        side_price = (
            float(_value(level_bar, "high"))
            if level_bar is not None and direction == "long"
            else float(_value(level_bar, "low"))
            if level_bar is not None
            else None
        )
        level_valid = (
            level_bar is not None
            and side_price is not None
            and _price_matches(side_price, level, point)
            and level_time <= origin
        )
        checks.append(
            _check(
                element,
                "OB_PROTECTED_LEVEL_PREEXISTS",
                level_valid,
                "The broken protected level existed before the OB origin."
                if level_valid
                else "The declared protected level is absent, on the wrong side, or formed after the OB.",
                evidence={"level": level, "levelFormedAt": iso(level_time)},
            )
        )
        break_valid = (
            break_bar is not None
            and break_at > origin
            and (
                float(_value(break_bar, "close")) > max(level, float(zone["high"]))
                if direction == "long"
                else float(_value(break_bar, "close")) < min(level, float(zone["low"]))
            )
        )
        checks.append(
            _check(
                element,
                "OB_BODY_BREAKS_STRUCTURE_AND_RANGE",
                break_valid,
                "The declared break candle body closed beyond both the protected level and OB range."
                if break_valid
                else "No confirmed body close broke both the pre-existing structure and the OB range.",
                evidence={
                    "breakAt": iso(break_at),
                    "breakClose": float(_value(break_bar, "close")) if break_bar is not None else None,
                    "level": level,
                },
            )
        )

    touch_present = touch_at is not None
    if require_touch:
        checks.append(
            _check(
                element,
                "OB_RETEST_TIME_DECLARED",
                touch_present,
                "The first post-departure OB touch is explicitly time-stamped."
                if touch_present
                else "sourceTouchAt is required; an OB cannot self-certify a later retest.",
            )
        )
    if touch_at is not None:
        touch_bar = _bar_at(series, "M1", touch_at, cutoff)
        overlaps = (
            touch_bar is not None
            and float(_value(touch_bar, "high")) >= float(zone["low"])
            and float(_value(touch_bar, "low")) <= float(zone["high"])
        )
        after_departure = (
            departure_bar is not None
            and touch_at >= _available_at(departure_bar, timeframe)
            and touch_at <= upper_bound
        )
        checks.append(
            _check(
                element,
                "OB_DEPARTURE_THEN_RETEST",
                overlaps and after_departure,
                "Price left the OB, then later returned to it before the trigger."
                if overlaps and after_departure
                else "The declared touch is absent, precedes confirmed departure, or occurs after the trigger.",
                evidence={"touchAt": iso(touch_at)},
            )
        )
    return checks, raw


def _find_level_witness(
    series: dict[str, Any],
    *,
    timeframe: str,
    formed_at: int,
    price: float,
    side: str,
    cutoff: int,
    point: float,
) -> tuple[Any | None, bool]:
    bar = _bar_at(series, timeframe, formed_at, cutoff)
    if bar is None:
        return None, False
    actual = float(_value(bar, "high" if side == "high" else "low"))
    return bar, _price_matches(actual, price, point)


def _is_local_pivot(
    series: dict[str, Any],
    timeframe: str,
    formed_at: int,
    side: str,
    cutoff: int,
) -> bool:
    bars = _confirmed(series, timeframe, cutoff)
    index = next(
        (position for position, bar in enumerate(bars) if int(_value(bar, "time")) == formed_at),
        None,
    )
    depth = 2
    if index is None or index < depth or index >= len(bars) - depth:
        return False
    value = float(_value(bars[index], "high" if side == "high" else "low"))
    neighbors = [
        float(_value(bars[position], "high" if side == "high" else "low"))
        for position in range(index - depth, index + depth + 1)
        if position != index
    ]
    return all(value >= neighbor for neighbor in neighbors) if side == "high" else all(
        value <= neighbor for neighbor in neighbors
    )


def validate_liquidity(
    series: dict[str, Any],
    liquidity: dict[str, Any],
    direction: str,
    cutoff: int,
    point: float,
    *,
    element: str,
    objective: bool,
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    required = ("kind", "price", "formedAt", "timeframe")
    complete = all(liquidity.get(key) not in (None, "") for key in required)
    checks.append(
        _check(
            element,
            "LIQUIDITY_WITNESS_DECLARED",
            complete,
            "Liquidity kind, price, timeframe, and formation time are explicit."
            if complete
            else "Liquidity requires structured kind, price, timeframe, and formedAt fields.",
        )
    )
    if not complete:
        return checks
    timeframe = str(liquidity["timeframe"])
    if timeframe not in TF_SECONDS:
        checks.append(
            _check(element, "LIQUIDITY_TIMEFRAME_SUPPORTED", False, f"Unsupported liquidity timeframe: {timeframe}")
        )
        return checks
    price = float(liquidity["price"])
    formed_at = parse_time(liquidity["formedAt"])
    side = (
        "high"
        if (objective and direction == "long") or (not objective and direction == "short")
        else "low"
    )
    bar, level_matches = _find_level_witness(
        series,
        timeframe=timeframe,
        formed_at=formed_at,
        price=price,
        side=side,
        cutoff=cutoff,
        point=point,
    )
    checks.append(
        _check(
            element,
            "LIQUIDITY_PRICE_EXISTS",
            level_matches,
            "The declared liquidity price matches the raw wick on the correct side."
            if level_matches
            else "The declared liquidity price does not match a confirmed raw wick on the required side.",
            evidence={"formedAt": iso(formed_at), "price": price, "side": side, "timeframe": timeframe},
        )
    )
    kind = str(liquidity["kind"]).upper()
    supported = {
        "EXTERNAL_SWING",
        "SWING_HIGH",
        "SWING_LOW",
        "EQH",
        "EQL",
        "RANGE_EDGE",
    }
    checks.append(
        _check(
            element,
            "LIQUIDITY_KIND_SUPPORTED",
            kind in supported,
            f"{kind} has an implemented raw-price witness."
            if kind in supported
            else (
                f"{kind} has no complete deterministic witness yet; it cannot authorize a trade."
            ),
        )
    )
    if kind not in supported:
        return checks
    if kind in {"EQH", "EQL", "RANGE_EDGE"}:
        witnesses = liquidity.get("witnesses") or []
        witness_times = [
            parse_time(item.get("formedAt"))
            for item in witnesses
            if isinstance(item, dict) and item.get("formedAt") not in (None, "")
        ]
        matches = [
            _find_level_witness(
                series,
                timeframe=timeframe,
                formed_at=witness_at,
                price=price,
                side=side,
                cutoff=cutoff,
                point=point,
            )[1]
            for witness_at in witness_times
        ]
        touches = sum(1 for matched in matches if matched)
        classified = len(set(witness_times)) >= 2 and touches == len(witness_times)
        reason = (
            f"{kind} has {touches} explicit independent wick witnesses."
            if classified
            else (
                f"{kind} requires at least two explicit, distinct, matching wick witnesses; "
                f"validated {touches}."
            )
        )
    else:
        classified = bar is not None and _is_local_pivot(series, timeframe, formed_at, side, cutoff)
        reason = (
            f"{kind} is a confirmed local swing witness."
            if classified
            else f"{kind} is not a confirmed local swing at the declared time."
        )
    checks.append(_check(element, "LIQUIDITY_CLASSIFICATION", classified, reason))
    return checks


def validate_sweep(
    series: dict[str, Any],
    trigger_liquidity: dict[str, Any],
    sweep: dict[str, Any],
    direction: str,
    decision_at: int,
    point: float,
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    sweep_at_value = sweep.get("at")
    complete = sweep_at_value not in (None, "") and trigger_liquidity.get("price") not in (None, "")
    checks.append(
        _check(
            "sweep",
            "SWEEP_WITNESS_DECLARED",
            complete,
            "Sweep time, trigger-liquidity price, and extreme are explicit."
            if complete
            else "Sweep validation requires a structured trigger liquidity and sweep timestamp.",
        )
    )
    if not complete:
        return checks
    sweep_at = parse_time(sweep_at_value)
    bar = _bar_at(series, "M1", sweep_at, decision_at)
    price = float(trigger_liquidity["price"])
    extreme = float(sweep["extreme"])
    if direction == "long":
        penetrated = bar is not None and float(_value(bar, "low")) < price - point / 2
        reclaimed = bar is not None and float(_value(bar, "close")) > price
        extreme_matches = bar is not None and _price_matches(float(_value(bar, "low")), extreme, point)
    else:
        penetrated = bar is not None and float(_value(bar, "high")) > price + point / 2
        reclaimed = bar is not None and float(_value(bar, "close")) < price
        extreme_matches = bar is not None and _price_matches(float(_value(bar, "high")), extreme, point)
    checks.extend(
        [
            _check(
                "sweep",
                "SWEEP_BAR_CONFIRMED",
                bar is not None,
                "The sweep candle is confirmed before the decision."
                if bar is not None
                else "The declared sweep candle is unavailable or still forming at the decision.",
            ),
            _check(
                "sweep",
                "SWEEP_PENETRATES_AND_RECLAIMS",
                penetrated and reclaimed,
                "The wick penetrated the pre-existing liquidity and the same candle closed back inside."
                if penetrated and reclaimed
                else "The candle did not both penetrate the declared liquidity and close back inside.",
                evidence={"sweepAt": iso(sweep_at), "liquidityPrice": price, "extreme": extreme},
            ),
            _check(
                "sweep",
                "SWEEP_EXTREME_MATCHES",
                extreme_matches,
                "The declared sweep extreme matches the raw wick."
                if extreme_matches
                else "The declared sweep extreme does not match the raw sweep candle.",
            ),
        ]
    )
    return checks


def validate_choch(
    series: dict[str, Any],
    choch: dict[str, Any],
    direction: str,
    trigger_timeframe: str,
    sweep_at: int | None,
    decision_at: int,
    point: float,
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    complete = all(choch.get(key) not in (None, "") for key in ("at", "level", "referenceFormedAt"))
    checks.append(
        _check(
            "choch",
            "CHOCH_WITNESS_DECLARED",
            complete,
            "CHoCH level, reference formation time, and break candle are explicit."
            if complete
            else "CHoCH requires referenceFormedAt; a level and narrative alone cannot prove structure.",
        )
    )
    if not complete:
        return checks
    break_at = parse_time(choch["at"])
    reference_at = parse_time(choch["referenceFormedAt"])
    level = float(choch["level"])
    break_bar = _bar_at(series, trigger_timeframe, break_at, decision_at)
    reference_bar = _bar_at(series, trigger_timeframe, reference_at, decision_at)
    side_price = (
        float(_value(reference_bar, "high"))
        if reference_bar is not None and direction == "long"
        else float(_value(reference_bar, "low"))
        if reference_bar is not None
        else None
    )
    reference_valid = (
        reference_bar is not None
        and side_price is not None
        and _price_matches(side_price, level, point)
        and reference_at < break_at
    )
    checks.append(
        _check(
            "choch",
            "CHOCH_REFERENCE_PREEXISTS",
            reference_valid,
            "The broken live reference existed before the CHoCH candle."
            if reference_valid
            else "The declared CHoCH level is not a prior raw high/low on the trigger timeframe.",
        )
    )
    body_break = (
        break_bar is not None
        and (
            float(_value(break_bar, "close")) > level
            if direction == "long"
            else float(_value(break_bar, "close")) < level
        )
    )
    prior_break = any(
        (
            float(_value(bar, "close")) > level
            if direction == "long"
            else float(_value(bar, "close")) < level
        )
        for bar in _confirmed(series, trigger_timeframe, decision_at)
        if reference_at < int(_value(bar, "time")) < break_at
    )
    separate = sweep_at is not None and break_at > sweep_at
    known = break_at + TF_SECONDS[trigger_timeframe] <= decision_at
    checks.extend(
        [
            _check(
                "choch",
                "CHOCH_BODY_CLOSE_BREAK",
                body_break and not prior_break,
                "This is the first body close through the declared live reference."
                if body_break and not prior_break
                else "The declared candle did not break the reference, or an earlier candle had already broken it.",
            ),
            _check(
                "choch",
                "CHOCH_AFTER_SWEEP_SEPARATE_BAR",
                separate,
                "CHoCH occurred on a later candle than the sweep."
                if separate
                else "Sweep and CHoCH are missing or not separate candles.",
            ),
            _check(
                "choch",
                "CHOCH_CONFIRMED_BEFORE_DECISION",
                known,
                "The CHoCH candle was closed before the decision."
                if known
                else "The decision used a still-forming CHoCH candle.",
            ),
        ]
    )
    return checks


def validate_entry_zone(
    series: dict[str, Any],
    zone: dict[str, Any],
    direction: str,
    decision_at: int,
    point: float,
    *,
    sweep_at: int | None,
    choch_at: int | None,
    source_zone: dict[str, Any],
) -> list[dict[str, Any]]:
    timeframe = str(zone.get("timeframe") or "M1")
    kind = _zone_kind(zone)
    if kind == "FVG":
        checks, raw = validate_raw_fvg(
            series,
            timeframe,
            zone,
            direction,
            decision_at,
            point,
            element="entry",
        )
    elif kind == "OB":
        checks, raw = validate_raw_ob(
            series,
            timeframe,
            zone,
            direction,
            decision_at,
            point,
            element="entry",
        )
    else:
        return [_check("entry", "ENTRY_ZONE_TYPE", False, "Entry zone is neither a raw OB nor a raw FVG.")]
    owned_by = str(zone.get("ownedBy") or "")
    if owned_by == "REFINED_SOURCE_OB":
        ownership = (
            timeframe == str(source_zone.get("timeframe"))
            and kind == _zone_kind(source_zone)
            and _price_matches(float(zone["low"]), float(source_zone["low"]), point)
            and _price_matches(float(zone["high"]), float(source_zone["high"]), point)
        )
    elif owned_by == "RECORDED_CHOCH" and raw is not None and choch_at is not None:
        if kind == "FVG":
            ownership = choch_at in {int(raw["middleTime"]), int(raw["thirdTime"])}
        else:
            origin = int(raw["originTime"])
            bars = _confirmed(series, timeframe, decision_at)
            between = [
                bar for bar in bars
                if origin < int(_value(bar, "time")) < choch_at
            ]
            opposite_after_origin = any(
                (
                    float(_value(bar, "close")) < float(_value(bar, "open"))
                    if direction == "long"
                    else float(_value(bar, "close")) > float(_value(bar, "open"))
                )
                for bar in between
            )
            ownership = (
                sweep_at is not None
                and sweep_at <= origin < choch_at
                and not opposite_after_origin
            )
    else:
        ownership = False
    checks.append(
        _check(
            "entry",
            "ENTRY_CAUSAL_OWNERSHIP",
            ownership,
            "The entry zone is either the final refined source or is physically owned by the recorded CHoCH."
            if ownership
            else "The raw zone exists but is not owned by the declared source/CHoCH chain.",
        )
    )
    return checks


def validate_objective_unconsumed(
    series: dict[str, Any],
    objective: dict[str, Any],
    direction: str,
    decision_at: int,
    point: float,
) -> list[dict[str, Any]]:
    checks = validate_liquidity(
        series,
        objective,
        direction,
        decision_at,
        point,
        element="objective",
        objective=True,
    )
    if not all(objective.get(key) not in (None, "") for key in ("formedAt", "price", "timeframe")):
        return checks
    formed_at = parse_time(objective["formedAt"])
    timeframe = str(objective["timeframe"])
    available = formed_at + TF_SECONDS.get(timeframe, 0)
    price = float(objective["price"])
    consumed = False
    for bar in _confirmed(series, "M1", decision_at):
        if int(_value(bar, "time")) < available:
            continue
        if direction == "long" and float(_value(bar, "high")) >= price - point / 2:
            consumed = True
            break
        if direction == "short" and float(_value(bar, "low")) <= price + point / 2:
            consumed = True
            break
    checks.append(
        _check(
            "objective",
            "OBJECTIVE_UNCONSUMED_AT_DECISION",
            not consumed,
            "The objective remained unconsumed at the decision."
            if not consumed
            else "Price had already traded through the declared objective before the decision.",
        )
    )
    return checks


def validate_order_semantics(
    order: dict[str, Any],
    series: dict[str, Any],
    point: float,
) -> dict[str, Any]:
    """Validate every declared element without trusting narrative descriptions."""

    checks: list[dict[str, Any]] = []
    decision_at = parse_time(order["decisionAt"])
    direction = str(order["direction"])
    lineage = order.get("causalLineage") or {}
    parent = lineage.get("parentZone") or {}
    source = lineage.get("sourceZone") or order.get("sourceZone") or {}
    source_liquidity = lineage.get("sourceLiquidity") or {}
    entry = lineage.get("entryZone") or order.get("entryZone") or {}
    trigger_liquidity = lineage.get("triggerLiquidity") or {}
    objective = lineage.get("objectiveLiquidity") or {}
    sweep_at = parse_time(lineage["sweepAt"]) if lineage.get("sweepAt") else None
    choch_at = parse_time(lineage["chochAt"]) if lineage.get("chochAt") else None
    source_touch_at = parse_time(lineage["sourceTouchAt"]) if lineage.get("sourceTouchAt") else None

    checks.append(
        _check(
            "contract",
            "CAUSAL_LINEAGE_PRESENT",
            bool(lineage),
            "Structured causal lineage is present."
            if lineage
            else "Order has no structured causal lineage and is not performance eligible.",
        )
    )
    if not lineage:
        return _result(order, checks)

    chronological = (
        source_touch_at is not None
        and sweep_at is not None
        and choch_at is not None
        and source_touch_at <= sweep_at < choch_at
        and choch_at + TF_SECONDS.get(str(order.get("triggerTimeframe") or "M1"), 60) <= decision_at
    )
    checks.append(
        _check(
            "contract",
            "CAUSAL_TIME_ORDER",
            chronological,
            "Source touch <= trigger sweep < separate CHoCH close <= decision."
            if chronological
            else "The causal chain time order is incomplete or uses an unclosed trigger candle.",
        )
    )

    source_upper_bound = sweep_at or decision_at
    if parent and _zone_kind(parent) == "OB":
        parent_tf = str(parent.get("timeframe") or order.get("sourceTimeframe") or "M15")
        parent_checks, _ = validate_causal_ob(
            series,
            parent_tf,
            parent,
            direction,
            decision_at,
            point,
            element="parent",
            touch_at=source_touch_at,
            upper_bound=source_upper_bound,
        )
        checks.extend(parent_checks)
    else:
        checks.append(_check("parent", "PARENT_ZONE_PRESENT", False, "A structured parent OB is required."))

    source_tf = str(source.get("timeframe") or order.get("sourceTimeframe") or "M15")
    if _zone_kind(source) == "OB":
        source_checks, _ = validate_causal_ob(
            series,
            source_tf,
            source,
            direction,
            decision_at,
            point,
            element="source",
            touch_at=source_touch_at,
            upper_bound=source_upper_bound,
        )
        checks.extend(source_checks)
    else:
        checks.append(
            _check(
                "source",
                "SOURCE_MUST_BE_OB",
                False,
                "The first-position Mentor protocol requires a causal source OB; a standalone FVG is information only.",
            )
        )

    refinement = lineage.get("refinementPath") or []
    previous = parent
    for index, child in enumerate([*refinement, source], start=1):
        if not previous or child is previous:
            previous = child
            continue
        same_direction_nested = (
            float(previous["low"]) - point <= float(child["low"])
            and float(child["high"]) <= float(previous["high"]) + point
        )
        checks.append(
            _check(
                "refinement",
                f"REFINEMENT_{index}_NESTED",
                same_direction_nested,
                "Child OB is contained in its causal parent."
                if same_direction_nested
                else "A lower-timeframe zone is not price-contained in its declared parent.",
            )
        )
        if child is not source:
            child_tf = str(child.get("timeframe") or "")
            if _zone_kind(child) != "OB":
                checks.append(
                    _check(
                        "refinement",
                        f"REFINEMENT_{index}_MUST_BE_OB",
                        False,
                        "A first-entry causal refinement must be an OB; FVG remains informational.",
                    )
                )
            else:
                child_checks, _ = validate_causal_ob(
                    series,
                    child_tf,
                    child,
                    direction,
                    decision_at,
                    point,
                    element=f"refinement{index}",
                    touch_at=source_touch_at,
                    upper_bound=source_upper_bound,
                )
                checks.extend(child_checks)
        previous = child

    if source_liquidity:
        checks.extend(
            validate_liquidity(
                series,
                source_liquidity,
                direction,
                decision_at,
                point,
                element="sourceLiquidity",
                objective=False,
            )
        )
    else:
        checks.append(
            _check(
                "sourceLiquidity",
                "SOURCE_LIQUIDITY_PRESENT",
                False,
                "The liquidity context that led price into the source OB must be structured evidence.",
            )
        )

    if trigger_liquidity:
        checks.extend(
            validate_liquidity(
                series,
                trigger_liquidity,
                direction,
                decision_at,
                point,
                element="triggerLiquidity",
                objective=False,
            )
        )
    else:
        checks.append(
            _check(
                "triggerLiquidity",
                "TRIGGER_LIQUIDITY_PRESENT",
                False,
                "The post-POI liquidity swept by the trigger must be separate structured evidence.",
            )
        )
    sweep = {**(order.get("sweep") or {}), "at": lineage.get("sweepAt")}
    checks.extend(validate_sweep(series, trigger_liquidity, sweep, direction, decision_at, point))

    choch = {
        **(order.get("choch") or {}),
        "at": lineage.get("chochAt"),
        "referenceFormedAt": lineage.get("chochReferenceFormedAt"),
    }
    checks.extend(
        validate_choch(
            series,
            choch,
            direction,
            str(order.get("triggerTimeframe") or "M1"),
            sweep_at,
            decision_at,
            point,
        )
    )
    checks.extend(
        validate_entry_zone(
            series,
            entry,
            direction,
            decision_at,
            point,
            sweep_at=sweep_at,
            choch_at=choch_at,
            source_zone=source,
        )
    )
    proximal = float(entry.get("high", 0)) if direction == "long" else float(entry.get("low", 0))
    entry_matches = _price_matches(float(order["entry"]), proximal, point)
    checks.append(
        _check(
            "entry",
            "ENTRY_AT_PROXIMAL_BOUNDARY",
            entry_matches,
            "Entry equals the directional proximal boundary."
            if entry_matches
            else f"Entry {float(order['entry']):.2f} does not equal proximal {proximal:.2f}.",
        )
    )

    if objective:
        checks.extend(validate_objective_unconsumed(series, objective, direction, decision_at, point))
    else:
        checks.append(
            _check("objective", "OBJECTIVE_PRESENT", False, "A structured objective-liquidity witness is required.")
        )
    objective_price = float(objective.get("price", float("nan")))
    exact_target = objective_price == objective_price and _price_matches(
        float(order["takeProfit"]), objective_price, point
    )
    direction_valid = (
        objective_price > float(order["entry"])
        if direction == "long" and objective_price == objective_price
        else objective_price < float(order["entry"])
        if objective_price == objective_price
        else False
    )
    checks.extend(
        [
            _check(
                "objective",
                "TP_EQUALS_OBJECTIVE",
                exact_target,
                "TP is exactly the frozen objective liquidity."
                if exact_target
                else "TP differs from the frozen objective; no RR fallback or offset is allowed.",
            ),
            _check(
                "objective",
                "OBJECTIVE_IN_TRADE_DIRECTION",
                direction_valid,
                "Objective lies beyond entry in the scenario direction."
                if direction_valid
                else "Objective is not beyond entry in the scenario direction.",
            ),
        ]
    )

    source_low = float(source.get("low", order["sourceInvalidation"]))
    source_high = float(source.get("high", order["sourceInvalidation"]))
    sweep_extreme = float((order.get("sweep") or {}).get("extreme", order["sourceInvalidation"]))
    if direction == "long":
        stop_valid = float(order["stopLoss"]) < min(source_low, float(order["sourceInvalidation"]), sweep_extreme)
    else:
        stop_valid = float(order["stopLoss"]) > max(source_high, float(order["sourceInvalidation"]), sweep_extreme)
    checks.append(
        _check(
            "risk",
            "SL_OUTSIDE_SOURCE_AND_SWEEP",
            stop_valid,
            "SL is outside the source distal, scenario invalidation, and sweep extreme."
            if stop_valid
            else "SL is inside at least one structural invalidation boundary.",
        )
    )
    return _result(order, checks)


def _result(order: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    failures = [item for item in checks if item["required"] and not item["valid"]]
    elements = sorted({item["element"] for item in checks})
    return {
        "schema": "mentor-semantic-audit-v1",
        "orderId": str(order.get("orderId") or order.get("id") or "UNKNOWN"),
        "valid": not failures,
        "performanceEligible": not failures,
        "elements": {element: _element_valid(checks, element) for element in elements},
        "failureCodes": [item["code"] for item in failures],
        "failureReasons": [item["reason"] for item in failures],
        "checks": checks,
    }


def summarize_semantic_audits(audits: list[dict[str, Any]]) -> dict[str, Any]:
    failure_counts: dict[str, int] = {}
    element_counts: dict[str, dict[str, int]] = {}
    for audit in audits:
        for code in audit["failureCodes"]:
            failure_counts[code] = failure_counts.get(code, 0) + 1
        for element, valid in audit["elements"].items():
            counts = element_counts.setdefault(element, {"valid": 0, "invalid": 0})
            counts["valid" if valid else "invalid"] += 1
    return {
        "schema": "mentor-semantic-audit-summary-v1",
        "orders": len(audits),
        "validOrders": sum(1 for item in audits if item["valid"]),
        "invalidOrders": sum(1 for item in audits if not item["valid"]),
        "elementCounts": element_counts,
        "failureCounts": dict(sorted(failure_counts.items())),
        "results": audits,
    }
