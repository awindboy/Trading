from __future__ import annotations

import json
from pathlib import Path
from typing import Any


IMPLEMENTED_FACTS = {
    "TWO_OB_DEFINITIONS",
    "FVG_THREE_CANDLE_WICK_GAP",
    "OB_RETIRES_AFTER_FULL_USE",
    "ACTIVE_TREND_REQUIRED",
    "LIQUIDITY_CONTEXT_REQUIRED",
    "DEALING_RANGE_50_PERCENT",
    "PREMIUM_SHORT",
    "LIQUIDITY_SWEEP",
    "STRUCTURE_CONFIRMATION",
    "FVG_OR_OB_ENTRY",
    "SOURCE_LIQUIDITY_SWEEP",
    "CHOCH_AFTER_SWEEP",
    "REVERSAL_OB_ENTRY",
    "NEXT_LIQUIDITY_TARGET",
    "EXTERNAL_INTERNAL_SEPARATION",
    "INTERNAL_LEVELS_ARE_LIQUIDITY",
    "THREE_OPPOSITE_CANDLES_CONFIRM_WAVE",
    "BODY_BREAK_CONFIRMS_CHOCH",
    "CHOCH_FVG_RETEST",
    "EXTERNAL_SWING_LIQUIDITY",
    "M1_CHOCH",
    "M1_FVG_ENTRY",
    "TRENDLINE_LIQUIDITY_TARGET",
    "SWEEP_BEFORE_TRIGGER",
    "WAIT_FOR_CHOCH",
    "TREND_FIRST",
    "LIQUIDITY_NEAR_ZONE",
    "LOWER_TIMEFRAME_CONFIRMATION",
    "HTF_MAP",
    "M15_LIQUIDITY_AND_OB",
    "M1_SWEEP",
    "LTF_STOP_REDUCTION",
    "WAIT_OUTSIDE_INTERNAL_NOISE",
    "BSL_SWEEP_BEFORE_SHORT",
    "CONTEXT_OB",
    "FVG_INVERSION_IS_SEPARATE_PROTOCOL",
    "FVG_CAN_FILL_BEFORE_OB",
    "FVG_AND_OB_EXECUTIONS_DIFFER",
    "BREAK_EVEN_MANAGEMENT_IS_SEPARATE",
    "ZONE_WITHOUT_TRAP_IS_NOT_READY",
    "REACTION_TRAP_CREATES_CONTEXT",
    "H4_DESTINATION",
    "REACTION_TRAP_SWEEP",
    "M5_FVG_ENTRY",
    "LIQUIDITY_TARGET",
    "EXTERNAL_TREND_NOT_FLIPPED",
    "INTERNAL_OB_ENTRY",
    "NEAR_INTERNAL_LIQUIDITY_TARGET",
    "WAIT_FOR_CORRECT_50_PERCENT_HALF",
    "CHOCH_FVG_AFTER_PD",
    "VALID_STRUCTURE_CAN_LOSE",
    "PREDEFINED_STOP",
    "NO_POST_HOC_REWRITE",
    "OLD_SCENARIO_TERMINATED",
    "NEW_BODY_BREAK",
    "NEW_LIQUIDITY_SOURCE",
    "NEW_OBJECTIVE",
    "M30_HAS_NO_SOURCE_OB",
    "M15_REVEALS_SOURCE_OB",
    "LIQUIDITY_ON_APPROACH_SIDE",
    "ADAPTIVE_SOURCE_TIMEFRAME",
    "UNRESOLVED_LARGER_STRUCTURE",
    "NEARER_SCOPE_COMPATIBLE_TARGET",
    "EXTERNAL_UPTREND",
    "INTERNAL_DOWNTREND",
    "RANGE_OR_TRENDLINE_LIQUIDITY",
    "NEAR_INTERNAL_TARGET",
    "LIQUIDITY_REQUIRES_PARTICIPANT_STOP_REASON",
}


FORBIDDEN_FACTS = {
    "ALL_OB_REUSABLE",
    "FVG_ALONE_AUTHORIZES_ENTRY",
    "OB_ALONE_AUTHORIZES_ENTRY",
    "EVERY_INTERNAL_CHOCH_FLIPS_EXTERNAL_TREND",
    "SWEEP_ALONE_AUTHORIZES_ENTRY",
    "ALL_FVG_SUPPORT_RESISTANCE_TRADES",
    "FVG_INVERSION_IN_BASE_PROTOCOL",
    "DISCRETIONARY_BE_IN_BASE_BACKTEST",
    "NEAREST_FVG_AUTOMATIC_ENTRY",
    "FORCE_EXTERNAL_REVERSAL_TARGET",
    "LATEST_PIVOT_EQUALS_LIQUIDITY",
}


def validate_casebook(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    results = []
    for case in payload.get("cases", []):
        required = set(case.get("requiredFacts") or [])
        forbidden = set(case.get("forbiddenFacts") or [])
        missing = sorted(required - IMPLEMENTED_FACTS)
        violations = sorted(forbidden & IMPLEMENTED_FACTS)
        results.append(
            {
                "id": case["id"],
                "confidence": case.get("confidence"),
                "passed": not missing and not violations,
                "missing": missing,
                "violations": violations,
            }
        )
    explicit = [item for item in results if item["confidence"] == "explicit"]
    passed = sum(1 for item in explicit if item["passed"])
    replay_eligible = [
        case for case in payload.get("cases", []) if case.get("replayFixture")
    ]
    return {
        "schema": "mentor-casebook-validation-v1",
        "totalCases": len(results),
        "explicitCases": len(explicit),
        "explicitPassed": passed,
        "semanticCoverage": passed / len(explicit) if explicit else 0.0,
        "replayEligibleCases": len(replay_eligible),
        "replayParity": None,
        "semanticPassed": passed == len(explicit),
        "protocolPassed": False,
        "passed": False,
        "protocolBlocker": (
            "Casebook entries do not yet contain timestamped OHLC replay fixtures; "
            "semantic fact coverage is not chart-replay parity."
        ),
        "results": results,
    }
