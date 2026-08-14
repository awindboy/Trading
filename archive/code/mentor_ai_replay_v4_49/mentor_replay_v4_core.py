from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PIPELINE_VERSION = "4.49-transactional-plan-resume"
TIMEFRAME_SECONDS = {"H1": 3600, "M30": 1800, "M15": 900, "M5": 300, "M1": 60}
TIMEFRAME_MINUTES = {"H1": 60, "M30": 30, "M15": 15, "M5": 5, "M1": 1}
STATES = {
    "FLAT", "MAPPED", "PLANNED", "REACTION_MONITOR", "TRIGGER_WATCH",
    "PENDING", "FILLED", "CLOSED", "CANCELED",
}
PLAN_LIMITS = {"H1": 60, "M30": 72, "M15": 96, "M5": 120}
MAP_LIMITS = {"H1": 60, "M30": 72, "M15": 96}
MAP_RECENT_EVIDENCE = {"H1": 8, "M30": 12, "M15": 16}
MAP_SWING_EVIDENCE = {"H1": 14, "M30": 14, "M15": 12}
REFINEMENT_LIMITS = {"M30": 72, "M15": 96, "M5": 120}
TRIGGER_LIMITS = {"M15": 48, "M5": 84, "M1": 180}
TRIGGER_RECENT_LIMITS = {"M15": 16, "M5": 48, "M1": 90}
PLAN_SEMANTIC_AUDIT_KEYS = (
    "externalOwnerAndScope",
    "objectiveClassificationAndMaturity",
    "rootDisplacementCausality",
    "fullRefinementCausality",
    "dealingRangePdAndCompetingLiquidity",
)


class V4ContractError(ValueError):
    pass


def parse_utc(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def utc_text(timestamp: int) -> str:
    return datetime.fromtimestamp(int(timestamp), tz=timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_hash(value: Any) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def bar_id(timeframe: str, timestamp: int) -> str:
    return f"{timeframe}:{int(timestamp)}"


def split_bar_id(value: str) -> tuple[str, int]:
    try:
        timeframe, raw_time = value.split(":", 1)
        timestamp = int(raw_time)
    except (AttributeError, ValueError) as exc:
        raise V4ContractError(f"invalid barId: {value!r}") from exc
    if timeframe not in TIMEFRAME_SECONDS:
        raise V4ContractError(f"unsupported timeframe in barId: {value}")
    return timeframe, timestamp


@dataclass(frozen=True)
class MarketData:
    rates: np.ndarray
    frames: dict[str, Any]
    point: float

    @classmethod
    def from_rates(cls, rates: np.ndarray, point: float) -> "MarketData":
        """Build the same MTF view from an append-only closed-M1 live archive."""
        from mentor_engine.data import build_timeframes
        from mentor_engine.models import BarSeries

        if rates.dtype.names is None:
            raise V4ContractError("live M1 rates must be a structured array")
        required = {"time", "open", "high", "low", "close", "spread"}
        missing = sorted(required.difference(rates.dtype.names))
        if missing:
            raise V4ContractError(f"live M1 rates are missing fields: {','.join(missing)}")
        if not len(rates):
            raise V4ContractError("live M1 archive contains no bars")
        times = np.asarray(rates["time"], dtype=np.int64)
        if np.any(times[1:] <= times[:-1]):
            raise V4ContractError("live M1 timestamps must be unique and increasing")
        m1 = BarSeries(
            timeframe="M1",
            seconds=60,
            time=times,
            available_time=times + 60,
            open=np.asarray(rates["open"], dtype=float),
            high=np.asarray(rates["high"], dtype=float),
            low=np.asarray(rates["low"], dtype=float),
            close=np.asarray(rates["close"], dtype=float),
            spread_points=np.asarray(rates["spread"], dtype=float),
        )
        return cls(rates=rates, frames=build_timeframes(m1), point=float(point))

    @classmethod
    def from_npz(
        cls,
        path: Path,
        warmup_start: int,
        replay_end: int,
        point: float,
    ) -> "MarketData":
        from mentor_engine.data import build_timeframes, load_m1_npz

        payload = np.load(path, allow_pickle=True)
        rates = payload["rates"]
        mask = (rates["time"] >= warmup_start) & (rates["time"] < replay_end)
        selected = rates[mask]
        if not selected.size:
            raise V4ContractError("selected dataset range contains no M1 bars")
        m1, _ = load_m1_npz(path, warmup_start, replay_end)
        return cls(rates=selected, frames=build_timeframes(m1), point=float(point))

    def bar(self, selected_id: str, as_of: int | None = None) -> dict[str, Any]:
        timeframe, timestamp = split_bar_id(selected_id)
        series = self.frames[timeframe]
        position = int(np.searchsorted(series.time, timestamp, side="left"))
        if position >= len(series.time) or int(series.time[position]) != timestamp:
            raise V4ContractError(f"barId is not present in the dataset: {selected_id}")
        available = int(series.available_time[position])
        if as_of is not None and available > as_of:
            raise V4ContractError(f"future barId is not available at as-of: {selected_id}")
        return {
            "barId": selected_id,
            "tf": timeframe,
            "time": int(series.time[position]),
            "available": available,
            "open": float(series.open[position]),
            "high": float(series.high[position]),
            "low": float(series.low[position]),
            "close": float(series.close[position]),
            "spreadPoints": float(series.spread_points[position]),
            "index": position,
        }

    def bars(self, timeframe: str, as_of: int, limit: int) -> list[dict[str, Any]]:
        series = self.frames[timeframe]
        closed = np.flatnonzero(series.available_time <= as_of)
        if not len(closed):
            return []
        selected = closed[-max(1, int(limit)) :]
        return [
            {
                "barId": bar_id(timeframe, int(series.time[index])),
                "tf": timeframe,
                "time": int(series.time[index]),
                "available": int(series.available_time[index]),
                "open": float(series.open[index]),
                "high": float(series.high[index]),
                "low": float(series.low[index]),
                "close": float(series.close[index]),
                "spreadPoints": float(series.spread_points[index]),
                "index": int(index),
            }
            for index in selected
        ]

    def compact(self, as_of: int, limits: dict[str, int]) -> dict[str, Any]:
        return {
            "columns": ["barId", "timeUtc", "open", "high", "low", "close", "spreadPoints"],
            "data": {
                timeframe: [
                    [
                        row["barId"],
                        utc_text(row["time"]),
                        round(row["open"], 5),
                        round(row["high"], 5),
                        round(row["low"], 5),
                        round(row["close"], 5),
                        round(row["spreadPoints"], 2),
                    ]
                    for row in self.bars(timeframe, as_of, limit)
                ]
                for timeframe, limit in limits.items()
            },
        }

    def m1_row(self, index: int) -> dict[str, Any]:
        row = self.rates[index]
        timestamp = int(row["time"])
        return {
            "barId": bar_id("M1", timestamp),
            "tf": "M1",
            "time": timestamp,
            "available": timestamp + 60,
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "spreadPoints": float(row["spread"]),
            "index": int(index),
        }

    def m1_index_at_or_after(self, timestamp: int) -> int:
        return int(np.searchsorted(self.rates["time"], timestamp, side="left"))

    def closed_bar_at(self, timeframe: str, available_at: int) -> dict[str, Any] | None:
        series = self.frames[timeframe]
        position = int(np.searchsorted(series.available_time, available_at, side="left"))
        if position >= len(series.available_time) or int(series.available_time[position]) != available_at:
            return None
        return self.bar(bar_id(timeframe, int(series.time[position])), available_at)

    def between(self, timeframe: str, start: int, end: int) -> list[dict[str, Any]]:
        series = self.frames[timeframe]
        indexes = np.flatnonzero((series.time >= start) & (series.available_time <= end))
        return [self.bar(bar_id(timeframe, int(series.time[i])), end) for i in indexes]


def _nullable_enum(values: Iterable[str]) -> dict[str, Any]:
    unique = list(dict.fromkeys(values))
    return {
        "anyOf": [
            {"type": "string", "enum": unique},
            {"type": "null"},
        ]
    }


def _ids(packet: dict[str, Any], timeframes: Iterable[str]) -> list[str]:
    return [row[0] for timeframe in timeframes for row in packet["bars"]["data"].get(timeframe, [])]


def plan_schema(packet: dict[str, Any]) -> dict[str, Any]:
    families = list(packet.get("physicalLineageFamilies", []))
    scenario_scopes = {
        str(option.get("scope", ""))
        for family in families
        for option in family.get("scenarioOptions", [])
        if option.get("scope")
    }
    owner_scope_is_deterministic = (
        isinstance(packet.get("externalMapAuthority"), dict)
        or "INTERNAL_ROTATION" in scenario_scopes
    )
    scenario_option_ids = list(dict.fromkeys(
        str(option["scenarioSelectionId"])
        for family in families
        for option in family.get("scenarioOptions", [])
    )) or ["NO_SCENARIO_OPTION"]

    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schemaVersion", "action", "scenarioSelectionId", "semanticAudit", "reason",
        ],
        "properties": {
            "schemaVersion": {"type": "string", "enum": ["4.11.0"]},
            "action": {"type": "string", "enum": ["PLAN", "NO_PLAN", "DATA_ERROR"]},
            "scenarioSelectionId": _nullable_enum(scenario_option_ids),
            "semanticAudit": {
                "type": "object",
                "additionalProperties": False,
                "required": list(PLAN_SEMANTIC_AUDIT_KEYS),
                "properties": {
                    key: {
                        "type": "string",
                        "enum": (
                            ["PASS"]
                            if key == "externalOwnerAndScope"
                            and owner_scope_is_deterministic
                            else ["PASS", "FAIL", "UNRESOLVED"]
                        ),
                    }
                    for key in PLAN_SEMANTIC_AUDIT_KEYS
                },
            },
            "reason": {"type": "string"},
        },
    }


def map_schema(packet: dict[str, Any]) -> dict[str, Any]:
    htf = _ids(packet, ("H1", "M30", "M15"))
    index = {"type": "integer", "minimum": 0, "maximum": 15}
    nullable_index = {"type": ["integer", "null"], "minimum": 0, "maximum": 15}
    node = {
        "type": ["object", "null"],
        "additionalProperties": False,
        "required": ["obIndex", "displacementIndex", "protectedSwingIndex"],
        "properties": {
            "obIndex": index,
            "displacementIndex": index,
            "protectedSwingIndex": index,
        },
    }
    scope_audit_item = {
        "type": "object",
        "additionalProperties": False,
        "required": ["verdict", "reason"],
        "properties": {
            "verdict": {"type": "string", "enum": ["VALID", "INVALID", "UNRESOLVED"]},
            "reason": {"type": "string"},
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schemaVersion", "action", "selectedBarIds", "direction", "scope", "dealingRange",
            "objective", "mapProtectedSwingIndex", "ownerBreakTargetIndex", "ownerBreakIndex", "root",
            "intermediateLiquidityIndexes", "scopeAudit", "rootFreshness", "reason",
        ],
        "properties": {
            "schemaVersion": {"type": "string", "enum": ["4.4.0"]},
            "action": {"type": "string", "enum": ["MAP", "NO_MAP", "DATA_ERROR"]},
            "selectedBarIds": {
                "type": "array", "maxItems": 16,
                "items": {"type": "string", "enum": htf},
            },
            "direction": _nullable_enum(["LONG", "SHORT"]),
            "scope": _nullable_enum(
                ["EXTERNAL_CONTINUATION", "INTERNAL_ROTATION", "EXTERNAL_REVERSAL"]
            ),
            "dealingRange": {
                "type": ["object", "null"],
                "additionalProperties": False,
                "properties": {"highIndex": index, "lowIndex": index},
                "required": ["highIndex", "lowIndex"],
            },
            "objective": {
                "type": ["object", "null"],
                "additionalProperties": False,
                "required": ["barIndex", "kind"],
                "properties": {
                    "barIndex": index,
                    "kind": _nullable_enum(
                        [
                            "EXTERNAL_SWING", "INTERNAL_SWING", "REACTION_TRAP",
                            "RANGE_EDGE", "TRENDLINE_CLUSTER",
                        ]
                    ),
                },
            },
            "mapProtectedSwingIndex": nullable_index,
            "ownerBreakTargetIndex": nullable_index,
            "ownerBreakIndex": nullable_index,
            "root": node,
            "intermediateLiquidityIndexes": {"type": "array", "items": index},
            "scopeAudit": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "EXTERNAL_CONTINUATION", "INTERNAL_ROTATION", "EXTERNAL_REVERSAL"
                ],
                "properties": {
                    "EXTERNAL_CONTINUATION": scope_audit_item,
                    "INTERNAL_ROTATION": scope_audit_item,
                    "EXTERNAL_REVERSAL": scope_audit_item,
                },
            },
            "rootFreshness": _nullable_enum(["FRESH", "CONSUMED", "INVALIDATED"]),
            "reason": {"type": "string"},
        },
    }


def refinement_schema(packet: dict[str, Any]) -> dict[str, Any]:
    ids = _ids(packet, ("M30", "M15", "M5"))
    index = {"type": "integer", "minimum": 0, "maximum": 15}
    node = {
        "type": "object",
        "additionalProperties": False,
        "required": ["obIndex", "displacementIndex", "protectedSwingIndex"],
        "properties": {
            "obIndex": index,
            "displacementIndex": index,
            "protectedSwingIndex": index,
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["schemaVersion", "action", "selectedBarIds", "refinements", "reason"],
        "properties": {
            "schemaVersion": {"type": "string", "enum": ["4.2.0"]},
            "action": {
                "type": "string", "enum": ["REFINEMENT", "NO_REFINEMENT", "DATA_ERROR"]
            },
            "selectedBarIds": {
                "type": "array", "maxItems": 16,
                "items": {"type": "string", "enum": ids},
            },
            "refinements": {"type": "array", "maxItems": 4, "items": node},
            "reason": {"type": "string"},
        },
    }


def trigger_watch_schema(packet: dict[str, Any]) -> dict[str, Any]:
    allowed_ids = _ids(packet, ("M5", "M1"))
    bar_id_value = {"type": "string", "enum": allowed_ids}
    nullable_bar_id = {"anyOf": [bar_id_value, {"type": "null"}]}
    source_ids = [
        str(item["selectionId"])
        for item in packet.get("sourceUpgradeCandidates", [])
        if item.get("touchBarId") and not item.get("invalidatedAtUtc")
    ]
    source_selection = (
        {"anyOf": [{"type": "string", "enum": source_ids}, {"type": "null"}]}
        if source_ids else {"type": "null"}
    )
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schemaVersion", "action", "matureLiquidityBarId",
            "m5CorrectionSwingBarId", "chochReferenceBarId", "chochBreakBarId",
            "sourceUpgradeSelectionId", "reason",
        ],
        "properties": {
            "schemaVersion": {"type": "string", "enum": ["4.8.0"]},
            "action": {"type": "string", "enum": ["ARM_REACTION", "REJECT_REACTION", "DATA_ERROR"]},
            "matureLiquidityBarId": nullable_bar_id,
            "m5CorrectionSwingBarId": nullable_bar_id,
            "chochReferenceBarId": nullable_bar_id,
            "chochBreakBarId": nullable_bar_id,
            "sourceUpgradeSelectionId": source_selection,
            "reason": {"type": "string"},
        },
    }


def mechanical_root_candidates(
    market: MarketData,
    as_of: int,
    *,
    maximum: int = 24,
    timeframe_limits: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for timeframe, limit in (timeframe_limits or MAP_LIMITS).items():
        rows = market.bars(timeframe, as_of, limit)
        for root_index in range(len(rows) - 1):
            root = rows[root_index]
            direction: str | None = None
            displacement: dict[str, Any] | None = None
            forward = rows[root_index + 1 : root_index + 5]
            if root["close"] > root["open"]:
                for item in forward:
                    if item["close"] > item["open"]:
                        break
                    if item["close"] < root["low"]:
                        direction, displacement = "SHORT", item
                        break
            elif root["close"] < root["open"]:
                for item in forward:
                    if item["close"] < item["open"]:
                        break
                    if item["close"] > root["high"]:
                        direction, displacement = "LONG", item
                        break
            if direction is None or displacement is None:
                continue
            displacement_index = next(
                index for index, item in enumerate(rows)
                if item["barId"] == displacement["barId"]
            )
            later = rows[displacement_index + 1 :]
            if direction == "SHORT":
                later_body_invalidated = any(
                    item["close"] > root["high"] for item in later
                )
                later_distal_touched = any(
                    item["high"] >= root["high"] for item in later
                )
                later_proximal_touched = any(
                    item["high"] >= root["low"] for item in later
                )
            else:
                later_body_invalidated = any(
                    item["close"] < root["low"] for item in later
                )
                later_distal_touched = any(
                    item["low"] <= root["low"] for item in later
                )
                later_proximal_touched = any(
                    item["low"] <= root["high"] for item in later
                )
            candidates.append(
                {
                    "direction": direction,
                    "timeframe": timeframe,
                    "rootBarId": root["barId"],
                    "rootTimeUtc": utc_text(root["time"]),
                    "displacementBarId": displacement["barId"],
                    "displacementTimeUtc": utc_text(displacement["time"]),
                    "laterClosedBars": len(later),
                    "laterBodyInvalidated": later_body_invalidated,
                    "laterDistalTouched": later_distal_touched,
                    "laterProximalTouched": later_proximal_touched,
                }
            )
    candidates.sort(
        key=lambda item: split_bar_id(item["displacementBarId"])[1], reverse=True
    )
    return candidates[: max(1, int(maximum))]


def map_opportunity_id(candidate: dict[str, Any]) -> str:
    """Collapse the same physical displacement observed on multiple timeframes."""
    direction = str(candidate["direction"])
    _, timestamp = split_bar_id(str(candidate["displacementBarId"]))
    return f"{direction}:{timestamp}"


def _body_broken_protected_candidates(
    market: MarketData,
    timeframe: str,
    root: dict[str, Any],
    displacement: dict[str, Any],
    direction: str,
    as_of: int,
    maximum: int = 5,
) -> list[str]:
    rows = market.between(
        timeframe,
        root["time"] - TIMEFRAME_SECONDS[timeframe] * 6,
        min(as_of, displacement["available"]),
    )
    eligible = [row for row in rows if row["time"] < root["time"]]
    if direction == "LONG":
        eligible = [row for row in eligible if displacement["close"] > row["high"]]
    else:
        eligible = [row for row in eligible if displacement["close"] < row["low"]]
    return [row["barId"] for row in eligible[-maximum:]]


def _m1_zone_lifecycle(
    market: MarketData,
    ob: dict[str, Any],
    displacement: dict[str, Any],
    direction: str,
    as_of: int,
) -> dict[str, bool]:
    """Measure freshness on the common M1 clock used by freeze and execution."""
    later = market.between("M1", displacement["available"], as_of)
    if direction == "LONG":
        return {
            "bodyInvalidated": any(row["close"] < ob["low"] for row in later),
            "distalTouched": any(row["low"] <= ob["low"] for row in later),
            "proximalTouched": any(row["low"] <= ob["high"] for row in later),
        }
    return {
        "bodyInvalidated": any(row["close"] > ob["high"] for row in later),
        "distalTouched": any(row["high"] >= ob["high"] for row in later),
        "proximalTouched": any(row["high"] >= ob["low"] for row in later),
    }


def resolved_external_authority(
    market: MarketData,
    authority: dict[str, Any] | None,
    as_of: int,
) -> dict[str, Any] | None:
    """Resolve the previously frozen external owner without reinterpreting it."""
    if not authority:
        return None
    direction = str(authority.get("direction"))
    if direction not in {"LONG", "SHORT"}:
        raise V4ContractError("external authority has no valid direction")
    protected = authority.get("protectedSwing")
    dealing_range = authority.get("dealingRange")
    if not isinstance(protected, dict) or not isinstance(dealing_range, dict):
        raise V4ContractError("external authority is incomplete")
    protected_bar = market.bar(str(protected.get("barId")), as_of)
    if protected_bar["tf"] not in {"H1", "M30"}:
        raise V4ContractError("external authority protected swing must be H1/M30")
    established_at = parse_utc(str(authority["establishedAtUtc"]))
    break_bar: dict[str, Any] | None = None
    for row in market.between(protected_bar["tf"], established_at, as_of):
        broken = (
            float(row["close"]) < float(protected_bar["low"])
            if direction == "LONG"
            else float(row["close"]) > float(protected_bar["high"])
        )
        if broken:
            break_bar = row
            break
    frozen_objective = authority.get("objective")
    objective_reached_bar: dict[str, Any] | None = None
    if isinstance(frozen_objective, dict):
        objective_origin = market.bar(str(frozen_objective["barId"]), as_of)
        objective_start = max(established_at, int(objective_origin["available"]))
        for row in market.between("M1", objective_start, as_of):
            reached = (
                float(row["high"]) >= float(frozen_objective["price"])
                if str(frozen_objective["side"]) == "HIGH"
                else float(row["low"]) <= float(frozen_objective["price"])
            )
            if reached:
                objective_reached_bar = row
                break
    break_available = int(break_bar["available"]) if break_bar else None
    objective_available = (
        int(objective_reached_bar["available"])
        if objective_reached_bar else None
    )
    if break_available is not None and (
        objective_available is None or break_available <= objective_available
    ):
        status = "BROKEN"
        resolved_at = break_available
    elif objective_available is not None:
        status = "OBJECTIVE_REACHED"
        resolved_at = objective_available
    else:
        status = "ACTIVE"
        resolved_at = None
    return {
        **authority,
        "direction": direction,
        "dealingRange": {
            "highBarId": str(dealing_range["highBarId"]),
            "lowBarId": str(dealing_range["lowBarId"]),
            "high": float(dealing_range["high"]),
            "low": float(dealing_range["low"]),
        },
        "protectedSwing": {
            "barId": protected_bar["barId"],
            "tf": protected_bar["tf"],
            "high": float(protected_bar["high"]),
            "low": float(protected_bar["low"]),
        },
        "objective": dict(frozen_objective) if isinstance(frozen_objective, dict) else None,
        "status": status,
        "bodyBreakBarId": break_bar["barId"] if break_bar else None,
        "objectiveReachedBarId": (
            objective_reached_bar["barId"] if objective_reached_bar else None
        ),
        "objectiveReachedAtUtc": (
            utc_text(objective_available) if objective_available is not None else None
        ),
        "resolvedAtUtc": utc_text(resolved_at) if resolved_at is not None else None,
    }


def external_authority_from_scenario(
    scenario: dict[str, Any],
    previous: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Advance owner authority only through an external continuation/reversal PLAN."""
    scope = str(scenario.get("scope"))
    if scope == "INTERNAL_ROTATION":
        return previous
    if scope not in {"EXTERNAL_CONTINUATION", "EXTERNAL_REVERSAL"}:
        raise V4ContractError("cannot derive external authority from unsupported scope")
    direction = str(scenario["direction"])
    if previous:
        previous_status = str(previous.get("status", "ACTIVE"))
        previous_direction = str(previous.get("direction"))
        if previous_status == "ACTIVE":
            if direction != previous_direction:
                raise V4ContractError(
                    "an intact external owner cannot be replaced without its body break"
                )
            if scope != "EXTERNAL_CONTINUATION":
                raise V4ContractError(
                    "an intact same-direction owner only permits external continuation"
                )
            expected_range = previous["dealingRange"]
            expected_protected = previous["protectedSwing"]
            expected_objective = previous.get("objective")
            if (
                str(scenario["dealingRange"]["highBarId"])
                != str(expected_range["highBarId"])
                or str(scenario["dealingRange"]["lowBarId"])
                != str(expected_range["lowBarId"])
                or str(scenario["mapProtectedSwing"]["barId"])
                != str(expected_protected["barId"])
                or not isinstance(expected_objective, dict)
                or str(scenario["objective"]["barId"])
                != str(expected_objective["barId"])
            ):
                raise V4ContractError(
                    "same-owner continuation attempted to redefine active external authority"
                )
            return previous
        if previous_status == "BROKEN":
            if scope != "EXTERNAL_REVERSAL" or direction == previous_direction:
                raise V4ContractError(
                    "broken external authority requires an opposite external reversal"
                )
        elif previous_status == "OBJECTIVE_REACHED":
            if direction != previous_direction or scope != "EXTERNAL_CONTINUATION":
                raise V4ContractError(
                    "fulfilled external authority can advance only in the same direction"
                )
        else:
            raise V4ContractError(f"unsupported external authority status: {previous_status}")
    return {
        "direction": direction,
        "establishedAtUtc": str(scenario["frozenAtUtc"]),
        "sourceScenarioHash": str(scenario["scenarioHash"]),
        "sourceScope": scope,
        "dealingRange": {
            key: scenario["dealingRange"][key]
            for key in ("highBarId", "lowBarId", "high", "low")
        },
        "protectedSwing": dict(scenario["mapProtectedSwing"]),
        "objective": dict(scenario["objective"]),
        "status": "ACTIVE",
        "bodyBreakBarId": None,
        "objectiveReachedBarId": None,
        "objectiveReachedAtUtc": None,
        "resolvedAtUtc": None,
    }


def _containing_external_objective(
    market: MarketData,
    objective: dict[str, Any],
    as_of: int,
) -> dict[str, Any] | None:
    """Use an H1/M30 wick only when it is the exact same physical price event."""
    source = market.bar(str(objective["barId"]), as_of)
    side = str(objective["side"])
    price = float(objective["price"])
    for timeframe in ("H1", "M30"):
        seconds = TIMEFRAME_SECONDS[timeframe]
        containing_id = bar_id(timeframe, source["time"] - source["time"] % seconds)
        try:
            containing = market.bar(containing_id, as_of)
        except V4ContractError:
            continue
        wick = float(containing["high"] if side == "HIGH" else containing["low"])
        if abs(wick - price) <= market.point / 2.0:
            return {"barId": containing["barId"], "side": side, "price": price}
    return None


def _physical_lineage_families(
    market: MarketData,
    as_of: int,
    roots: list[dict[str, Any]],
    children: list[dict[str, Any]],
    swing_candidates: list[dict[str, Any]],
    external_authority: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Group only physically possible parent/child events without authorizing causality."""
    families: list[dict[str, Any]] = []
    decision_close = market.bars("M15", as_of, 1)[-1]["close"]
    timeframe_rank = {"H1": 0, "M30": 1, "M15": 2, "M5": 3}
    authority = resolved_external_authority(market, external_authority, as_of)
    for root_candidate in roots:
        root = market.bar(str(root_candidate["rootBarId"]), as_of)
        displacement = market.bar(str(root_candidate["displacementBarId"]), as_of)
        direction = str(root_candidate["direction"])
        compatible_children: list[dict[str, Any]] = []
        for child_candidate in children:
            if child_candidate["direction"] != direction:
                continue
            if (
                child_candidate["laterBodyInvalidated"]
                or child_candidate["laterDistalTouched"]
                or child_candidate["laterProximalTouched"]
            ):
                continue
            child_root = market.bar(str(child_candidate["rootBarId"]), as_of)
            child_displacement = market.bar(str(child_candidate["displacementBarId"]), as_of)
            child_lifecycle = _m1_zone_lifecycle(
                market, child_root, child_displacement, direction, as_of
            )
            if any(child_lifecycle.values()):
                continue
            if timeframe_rank[child_root["tf"]] <= timeframe_rank[root["tf"]]:
                continue
            inside_parent_candle = root["time"] <= child_root["time"] < root["available"]
            overlaps_parent_event = (
                root["time"] <= child_root["time"] < displacement["available"]
                and child_root["high"] >= root["low"]
                and child_root["low"] <= root["high"]
            )
            if not (inside_parent_candle or overlaps_parent_event):
                continue
            extension_rows = market.between(
                child_root["tf"], child_root["available"],
                min(as_of, displacement["available"]),
            )
            if direction == "LONG":
                extensions = [
                    row for row in extension_rows
                    if row["close"] > row["open"] and row["close"] > child_root["high"]
                ]
            else:
                extensions = [
                    row for row in extension_rows
                    if row["close"] < row["open"] and row["close"] < child_root["low"]
                ]
            delivery_ids = [child_displacement["barId"]]
            delivery_ids.extend(row["barId"] for row in extensions)
            delivery_ids = list(dict.fromkeys(delivery_ids))[:5]
            delivery_options = []
            for selected_id in delivery_ids:
                selected = market.bar(selected_id, as_of)
                delivery_options.append(
                    {
                        "displacementBarId": selected_id,
                        "eligibleProtectedSwingBarIds": _body_broken_protected_candidates(
                            market, child_root["tf"], child_root, selected,
                            direction, as_of, maximum=4,
                        ),
                    }
                )
            delivery_options = [
                item for item in delivery_options
                if item["eligibleProtectedSwingBarIds"]
            ][:3]
            if not delivery_options:
                continue
            compatible_children.append(
                {
                    "rootBarId": child_root["barId"],
                    "deliveryOptions": delivery_options,
                    "insideParentCandle": inside_parent_candle,
                    "overlapsParentEvent": overlaps_parent_event,
                }
            )
        balanced_children: list[dict[str, Any]] = []
        for timeframe in ("M30", "M15", "M5"):
            same_timeframe = [
                item for item in compatible_children
                if split_bar_id(str(item["rootBarId"]))[0] == timeframe
            ]
            same_timeframe.sort(
                key=lambda item: split_bar_id(str(item["rootBarId"]))[1],
                reverse=True,
            )
            balanced_children.extend(same_timeframe[:2])
        compatible_children = balanced_children
        root_protected_ids = _body_broken_protected_candidates(
            market, root["tf"], root, displacement, direction, as_of,
        )
        if not compatible_children or not root_protected_ids:
            continue

        objective_candidates: list[dict[str, Any]] = []
        expected_side = "HIGH" if direction == "LONG" else "LOW"
        for swing in swing_candidates:
            if swing["side"] != expected_side:
                continue
            if direction == "LONG" and float(swing["price"]) <= decision_close:
                continue
            if direction == "SHORT" and float(swing["price"]) >= decision_close:
                continue
            objective = {
                "barId": swing["barId"], "side": expected_side,
                "price": float(swing["price"]),
            }
            if _objective_consumed(market, objective, as_of):
                continue
            objective_candidates.append(objective)
        objective_candidates.sort(
            key=lambda item: (
                abs(float(item["price"]) - decision_close),
                split_bar_id(str(item["barId"]))[1],
            )
        )
        objective_by_price: dict[tuple[str, int], dict[str, Any]] = {}
        for item in objective_candidates:
            key = (str(item["side"]), round(float(item["price"]) / market.point))
            existing = objective_by_price.get(key)
            if existing is None:
                objective_by_price[key] = item
                continue
            item_tf = split_bar_id(str(item["barId"]))[0]
            existing_tf = split_bar_id(str(existing["barId"]))[0]
            if timeframe_rank[item_tf] < timeframe_rank[existing_tf]:
                objective_by_price[key] = item
        objective_candidates = sorted(
            objective_by_price.values(),
            key=lambda item: (
                abs(float(item["price"]) - decision_close),
                timeframe_rank[split_bar_id(str(item["barId"]))[0]],
                split_bar_id(str(item["barId"]))[1],
            ),
        )
        if not objective_candidates:
            continue
        map_context_ids: list[str] = []
        containing_root_by_tf: dict[str, str] = {}
        containing_objective_by_tf: dict[str, list[str]] = {"H1": [], "M30": []}
        for timeframe in ("H1", "M30"):
            seconds = TIMEFRAME_SECONDS[timeframe]
            containing_root = bar_id(timeframe, root["time"] - root["time"] % seconds)
            try:
                market.bar(containing_root, as_of)
            except V4ContractError:
                pass
            else:
                map_context_ids.append(containing_root)
                containing_root_by_tf[timeframe] = containing_root
        for objective in objective_candidates:
            objective_bar = market.bar(str(objective["barId"]), as_of)
            for timeframe in ("H1", "M30"):
                seconds = TIMEFRAME_SECONDS[timeframe]
                containing_objective = bar_id(
                    timeframe, objective_bar["time"] - objective_bar["time"] % seconds
                )
                try:
                    market.bar(containing_objective, as_of)
                except V4ContractError:
                    continue
                map_context_ids.append(containing_objective)
                containing_objective_by_tf[timeframe].append(containing_objective)
        range_pairs: list[dict[str, Any]] = []
        for timeframe in ("H1", "M30"):
            root_context_id = containing_root_by_tf.get(timeframe)
            if not root_context_id:
                continue
            root_context = market.bar(root_context_id, as_of)
            for objective_context_id in dict.fromkeys(containing_objective_by_tf[timeframe]):
                objective_context = market.bar(objective_context_id, as_of)
                low_bar = root_context if direction == "LONG" else objective_context
                high_bar = objective_context if direction == "LONG" else root_context
                if low_bar["low"] >= high_bar["high"]:
                    continue
                eq = (low_bar["low"] + high_bar["high"]) / 2.0
                range_pairs.append(
                    {
                        "timeframe": timeframe,
                        "highBarId": high_bar["barId"],
                        "lowBarId": low_bar["barId"],
                        "high": high_bar["high"],
                        "low": low_bar["low"],
                        "eq": round(eq, 5),
                        "decisionCloseLocation": (
                            "DISCOUNT" if decision_close <= eq else "PREMIUM"
                        ),
                    }
                )
        unique_range_pairs: list[dict[str, Any]] = []
        seen_ranges: set[tuple[int, int]] = set()
        for item in range_pairs:
            key = (
                round(float(item["high"]) / market.point),
                round(float(item["low"]) / market.point),
            )
            if key in seen_ranges:
                continue
            seen_ranges.add(key)
            unique_range_pairs.append(item)
        range_pairs = unique_range_pairs
        root_lifecycle = _m1_zone_lifecycle(
            market, root, displacement, direction, as_of
        )
        families.append(
            {
                "familyId": canonical_hash(
                    {
                        "direction": direction,
                        "root": root["barId"],
                        "displacement": displacement["barId"],
                    }
                )[:12],
                "direction": direction,
                "rootBarId": root["barId"],
                "initialDisplacementBarId": displacement["barId"],
                "rootLaterBodyInvalidated": root_lifecycle["bodyInvalidated"],
                "rootLaterDistalTouched": root_lifecycle["distalTouched"],
                "rootLaterProximalTouched": root_lifecycle["proximalTouched"],
                "eligibleProtectedSwingBarIds": root_protected_ids,
                "childCandidates": compatible_children,
                "unconsumedDirectionalLiquidityCandidates": objective_candidates[:6],
                "mapContextCandidateBarIds": list(dict.fromkeys(map_context_ids)),
                "dealingRangePairCandidates": range_pairs,
                "mapProtectedSwingCandidateBarIds": [
                    item["lowBarId"] if direction == "LONG" else item["highBarId"]
                    for item in range_pairs
                ],
            }
        )
    families.sort(
        key=lambda item: TIMEFRAME_MINUTES[split_bar_id(item["rootBarId"])[0]],
        reverse=True,
    )
    canonical: list[dict[str, Any]] = []
    for family in families:
        root = market.bar(family["rootBarId"], as_of)
        child_ids = {item["rootBarId"] for item in family["childCandidates"]}
        duplicate = False
        for selected in canonical:
            if selected["direction"] != family["direction"]:
                continue
            selected_child_ids = {
                item["rootBarId"] for item in selected["childCandidates"]
            }
            if not child_ids.intersection(selected_child_ids):
                continue
            selected_root = market.bar(selected["rootBarId"], as_of)
            if root["high"] < selected_root["low"] or root["low"] > selected_root["high"]:
                continue
            duplicate = True
            break
        if not duplicate:
            family_direction = str(family["direction"])
            family_displacement = market.bar(
                str(family["initialDisplacementBarId"]), as_of
            )
            family["mapProtectedSwingCandidateBarIds"] = list(
                dict.fromkeys(family["mapProtectedSwingCandidateBarIds"])
            )
            family_id = str(family["familyId"])
            family["rootSelections"] = [
                {
                    "selectionId": "root-" + canonical_hash(
                        {
                            "familyId": family_id,
                            "obBarId": family["rootBarId"],
                            "displacementBarId": family["initialDisplacementBarId"],
                            "protectedSwingBarId": protected_id,
                        }
                    )[:16],
                    "obBarId": family["rootBarId"],
                    "displacementBarId": family["initialDisplacementBarId"],
                    "protectedSwingBarId": protected_id,
                }
                for protected_id in family["eligibleProtectedSwingBarIds"]
                if _delivery_valid(
                    root, family_displacement,
                    market.bar(protected_id, as_of), family_direction
                )
            ]
            for child in family["childCandidates"]:
                child["selectionOptions"] = [
                    {
                        "selectionId": "child-" + canonical_hash(
                            {
                                "familyId": family_id,
                                "obBarId": child["rootBarId"],
                                "displacementBarId": option["displacementBarId"],
                                "protectedSwingBarId": protected_id,
                            }
                        )[:16],
                        "obBarId": child["rootBarId"],
                        "displacementBarId": option["displacementBarId"],
                        "protectedSwingBarId": protected_id,
                    }
                    for option in child["deliveryOptions"]
                    for protected_id in option["eligibleProtectedSwingBarIds"]
                    if _delivery_valid(
                        market.bar(child["rootBarId"], as_of),
                        market.bar(option["displacementBarId"], as_of),
                        market.bar(protected_id, as_of),
                        family_direction,
                    )
                ]
            family["childCandidates"] = [
                child for child in family["childCandidates"]
                if child["selectionOptions"]
            ]
            if not family["rootSelections"] or not family["childCandidates"]:
                continue

            def strongest_selection(options: list[dict[str, Any]]) -> dict[str, Any]:
                earliest_delivery = min(
                    split_bar_id(str(item["displacementBarId"]))[1]
                    for item in options
                )
                earliest = [
                    item for item in options
                    if split_bar_id(str(item["displacementBarId"]))[1] == earliest_delivery
                ]

                def strength(item: dict[str, Any]) -> tuple[float, int]:
                    protected = market.bar(str(item["protectedSwingBarId"]), as_of)
                    level = protected["high"] if family_direction == "LONG" else -protected["low"]
                    return float(level), int(protected["time"])

                return max(earliest, key=strength)

            root_selection = strongest_selection(family["rootSelections"])
            child_selections = {
                str(child["rootBarId"]): strongest_selection(child["selectionOptions"])
                for child in family["childCandidates"]
            }

            def nested(parent_id: str, child_id: str) -> bool:
                parent = market.bar(parent_id, as_of)
                child = market.bar(child_id, as_of)
                return (
                    TIMEFRAME_MINUTES[child["tf"]] < TIMEFRAME_MINUTES[parent["tf"]]
                    and parent["time"] <= child["time"] < parent["available"]
                    and child["high"] >= parent["low"]
                    and child["low"] <= parent["high"]
                )

            child_ids = list(child_selections)
            top_level_ids = [
                child_id for child_id in child_ids
                if not any(
                    other_id != child_id and nested(other_id, child_id)
                    for other_id in child_ids
                )
            ]

            def maximal_paths(current_id: str, used: set[str]) -> list[list[str]]:
                lower = [
                    child_id for child_id in child_ids
                    if child_id not in used and nested(current_id, child_id)
                ]
                if not lower:
                    return [[current_id]]
                closest_tf = max(
                    TIMEFRAME_MINUTES[split_bar_id(child_id)[0]] for child_id in lower
                )
                next_ids = [
                    child_id for child_id in lower
                    if TIMEFRAME_MINUTES[split_bar_id(child_id)[0]] == closest_tf
                ]
                paths: list[list[str]] = []
                for next_id in next_ids:
                    for tail in maximal_paths(next_id, used | {current_id}):
                        paths.append([current_id, *tail])
                return paths

            raw_paths = [
                path
                for top_level_id in top_level_ids
                for path in maximal_paths(top_level_id, set())
            ]
            family["lineagePathOptions"] = [
                {
                    "pathSelectionId": "path-" + canonical_hash(
                        {
                            "familyId": family_id,
                            "rootSelectionId": root_selection["selectionId"],
                            "refinementSelectionIds": [
                                child_selections[child_id]["selectionId"]
                                for child_id in path
                            ],
                        }
                    )[:16],
                    "root": {
                        key: root_selection[key]
                        for key in ("obBarId", "displacementBarId", "protectedSwingBarId")
                    },
                    "refinements": [
                        {
                            key: child_selections[child_id][key]
                            for key in ("obBarId", "displacementBarId", "protectedSwingBarId")
                        }
                        for child_id in path
                    ],
                }
                for path in raw_paths
            ]
            if not family["lineagePathOptions"]:
                continue
            for range_pair in family["dealingRangePairCandidates"]:
                eq = float(range_pair["eq"])
                range_pair["childPoiLocations"] = [
                    {
                        "barId": child["rootBarId"],
                        "location": (
                            "DISCOUNT"
                            if (
                                market.bar(child["rootBarId"], as_of)["high"]
                                if family["direction"] == "LONG"
                                else market.bar(child["rootBarId"], as_of)["low"]
                            ) <= eq
                            else "PREMIUM"
                        ),
                    }
                    for child in family["childCandidates"]
                ]

            directional = list(family["unconsumedDirectionalLiquidityCandidates"])
            external_objectives: list[dict[str, Any]] = []
            internal_objectives: list[dict[str, Any]] = []
            reversal_objectives: list[dict[str, Any]] = []
            if authority is None:
                external_objectives = [
                    item for item in directional
                    if split_bar_id(str(item["barId"]))[0] in {"H1", "M30"}
                ][:1]
                internal_objectives = [
                    item for item in directional
                    if split_bar_id(str(item["barId"]))[0] in {"M15", "M5"}
                ][:1]
            else:
                authority_low = float(authority["dealingRange"]["low"])
                authority_high = float(authority["dealingRange"]["high"])
                same_owner_direction = family_direction == str(authority["direction"])
                frozen_objective = authority.get("objective")
                if (
                    same_owner_direction
                    and isinstance(frozen_objective, dict)
                    and str(frozen_objective.get("side")) == expected_side
                    and not _objective_consumed(market, frozen_objective, as_of)
                ):
                    directional.append(
                        {
                            "barId": str(frozen_objective["barId"]),
                            "side": expected_side,
                            "price": float(frozen_objective["price"]),
                        }
                    )
                    directional = sorted(
                        {
                            (str(item["barId"]), str(item["side"])): item
                            for item in directional
                        }.values(),
                        key=lambda item: abs(float(item["price"]) - decision_close),
                    )
                for raw_objective in directional:
                    objective = dict(raw_objective)
                    price = float(objective["price"])
                    is_frozen_external = bool(
                        same_owner_direction
                        and isinstance(frozen_objective, dict)
                        and str(objective["barId"]) == str(frozen_objective.get("barId"))
                    )
                    inside_authority = (
                        authority_low <= price <= authority_high
                        and not is_frozen_external
                    )
                    beyond_owner_target = (
                        price >= authority_high
                        if family_direction == "LONG"
                        else price <= authority_low
                    )
                    if inside_authority:
                        internal_objectives.append(objective)
                        continue
                    externalized = (
                        objective
                        if is_frozen_external
                        else _containing_external_objective(market, objective, as_of)
                    )
                    if externalized is None or not beyond_owner_target:
                        continue
                    if authority["status"] == "ACTIVE" and same_owner_direction:
                        if is_frozen_external:
                            external_objectives.append(externalized)
                    elif (
                        authority["status"] == "OBJECTIVE_REACHED"
                        and same_owner_direction
                    ):
                        external_objectives.append(externalized)
                    elif authority["status"] == "BROKEN" and not same_owner_direction:
                        reversal_objectives.append(externalized)
                external_objectives = external_objectives[:1]
                internal_objectives = internal_objectives[:1]
                reversal_objectives = reversal_objectives[:1]

            option_specs: list[tuple[str, dict[str, Any], str]] = []
            option_specs.extend(
                ("EXTERNAL_CONTINUATION", objective, "EXTERNAL_SWING")
                for objective in external_objectives
            )
            option_specs.extend(
                ("INTERNAL_ROTATION", objective, "INTERNAL_SWING")
                for objective in internal_objectives
            )
            option_specs.extend(
                ("EXTERNAL_REVERSAL", objective, "EXTERNAL_SWING")
                for objective in reversal_objectives
            )
            scenario_options: list[dict[str, Any]] = []
            seen_semantics: set[str] = set()
            packet_stub = {
                "externalMapAuthority": authority,
                "physicalLineageFamilies": [family],
            }
            if authority and authority["status"] == "ACTIVE":
                frozen_range = authority["dealingRange"]
                option_range_pairs = [
                    {
                        "highBarId": str(frozen_range["highBarId"]),
                        "lowBarId": str(frozen_range["lowBarId"]),
                        "high": float(frozen_range["high"]),
                        "low": float(frozen_range["low"]),
                        "eq": (
                            float(frozen_range["high"])
                            + float(frozen_range["low"])
                        ) / 2.0,
                    }
                ]
            else:
                option_range_pairs = family["dealingRangePairCandidates"]
            for path in family["lineagePathOptions"]:
                final_child = market.bar(
                    str(path["refinements"][-1]["obBarId"]), as_of
                )
                child_proximal = (
                    final_child["high"]
                    if family_direction == "LONG"
                    else final_child["low"]
                )
                for range_pair in option_range_pairs:
                    for scope, objective_candidate, objective_kind in option_specs:
                        objective_price = float(objective_candidate["price"])
                        if scope == "EXTERNAL_CONTINUATION":
                            internal_between = [
                                item for item in internal_objectives
                                if item["barId"] != objective_candidate["barId"]
                                and (
                                    child_proximal < float(item["price"]) < objective_price
                                    if family_direction == "LONG"
                                    else objective_price < float(item["price"]) < child_proximal
                                )
                            ]
                            intermediate_ids = [
                                str(item["barId"]) for item in internal_between[:3]
                            ]
                        else:
                            intermediate_ids = []
                        is_reversal = scope == "EXTERNAL_REVERSAL"
                        candidate_payload = {
                            "schemaVersion": "4.9.0",
                            "action": "PLAN",
                            "direction": family_direction,
                            "scope": scope,
                            "dealingRange": {
                                "highBarId": str(range_pair["highBarId"]),
                                "lowBarId": str(range_pair["lowBarId"]),
                            },
                            "objective": {
                                "barId": str(objective_candidate["barId"]),
                                "side": str(objective_candidate["side"]),
                                "kind": objective_kind,
                            },
                            "mapProtectedSwingBarId": str(
                                authority["protectedSwing"]["barId"]
                                if authority and authority["status"] == "ACTIVE"
                                else range_pair[
                                    "lowBarId" if family_direction == "LONG" else "highBarId"
                                ]
                            ),
                            "ownerBreakTargetBarId": (
                                str(authority["protectedSwing"]["barId"])
                                if is_reversal and authority else None
                            ),
                            "ownerBreakBarId": (
                                str(authority["bodyBreakBarId"])
                                if is_reversal and authority else None
                            ),
                            "lineagePathSelectionId": str(path["pathSelectionId"]),
                            "intermediateLiquidityBarIds": intermediate_ids,
                            "reason": "engine-prevalidated scenario option",
                        }
                        try:
                            frozen = freeze_plan(
                                candidate_payload,
                                market,
                                as_of,
                                None,
                                packet_stub,
                            )
                        except V4ContractError:
                            continue
                        if frozen is None or frozen["semanticHash"] in seen_semantics:
                            continue
                        seen_semantics.add(frozen["semanticHash"])
                        option_body = {
                            key: candidate_payload[key]
                            for key in (
                                "direction", "scope", "dealingRange", "objective",
                                "mapProtectedSwingBarId", "ownerBreakTargetBarId",
                                "ownerBreakBarId", "lineagePathSelectionId",
                                "intermediateLiquidityBarIds",
                            )
                        }
                        scenario_options.append(
                            {
                                "scenarioSelectionId": "scenario-" + canonical_hash(
                                    {"familyId": family_id, **option_body}
                                )[:16],
                                **option_body,
                            }
                        )
            family["scenarioOptions"] = scenario_options[:12]
            family["externalAuthorityAtDecision"] = authority
            if not family["scenarioOptions"]:
                continue
            canonical.append(family)
    if authority and authority["status"] == "OBJECTIVE_REACHED":
        newest_delivery_by_objective: dict[tuple[str, str], int] = {}
        for family in canonical:
            delivery_available = int(
                market.bar(str(family["initialDisplacementBarId"]), as_of)[
                    "available"
                ]
            )
            for option in family["scenarioOptions"]:
                if option["scope"] != "EXTERNAL_CONTINUATION":
                    continue
                key = (
                    str(option["direction"]),
                    str(option["objective"]["barId"]),
                )
                newest_delivery_by_objective[key] = max(
                    newest_delivery_by_objective.get(key, 0),
                    delivery_available,
                )
        retained: list[dict[str, Any]] = []
        for family in canonical:
            delivery_available = int(
                market.bar(str(family["initialDisplacementBarId"]), as_of)[
                    "available"
                ]
            )
            selectable: list[dict[str, Any]] = []
            superseded: list[dict[str, Any]] = []
            for option in family["scenarioOptions"]:
                key = (
                    str(option["direction"]),
                    str(option["objective"]["barId"]),
                )
                is_superseded = (
                    option["scope"] == "EXTERNAL_CONTINUATION"
                    and delivery_available
                    < newest_delivery_by_objective.get(key, delivery_available)
                )
                (superseded if is_superseded else selectable).append(option)
            family["scenarioOptions"] = selectable
            family["supersededScenarioOptions"] = [
                {
                    **option,
                    "supersededReason": (
                        "NEWER_CAUSAL_ROOT_DELIVERY_FOR_SAME_OBJECTIVE"
                    ),
                }
                for option in superseded
            ]
            if selectable:
                retained.append(family)
        canonical = retained
    return canonical


def _nested_bar_ids(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for item in value.values():
            found.extend(_nested_bar_ids(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_nested_bar_ids(item))
    elif isinstance(value, str) and ":" in value:
        try:
            split_bar_id(value)
        except V4ContractError:
            pass
        else:
            found.append(value)
    return list(dict.fromkeys(found))


def _map_evidence(
    market: MarketData,
    as_of: int,
    candidates: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return neutral selectable evidence without authorizing any market meaning."""
    selected: dict[str, dict[str, dict[str, Any]]] = {
        timeframe: {} for timeframe in MAP_LIMITS
    }
    swing_candidates: list[dict[str, Any]] = []

    for timeframe, limit in MAP_LIMITS.items():
        rows = market.bars(timeframe, as_of, limit)
        recent = MAP_RECENT_EVIDENCE[timeframe]
        for row in rows[-recent:]:
            selected[timeframe][row["barId"]] = row
        timeframe_swings: list[tuple[dict[str, Any], str, float]] = []
        for index in range(2, len(rows) - 2):
            row = rows[index]
            left = rows[index - 2:index]
            right = rows[index + 1:index + 3]
            is_high = row["high"] > max(item["high"] for item in left) and row["high"] >= max(
                item["high"] for item in right
            )
            is_low = row["low"] < min(item["low"] for item in left) and row["low"] <= min(
                item["low"] for item in right
            )
            if not is_high and not is_low:
                continue
            if is_high:
                timeframe_swings.append((row, "HIGH", row["high"]))
            if is_low:
                timeframe_swings.append((row, "LOW", row["low"]))
        for row, side, price in timeframe_swings[-MAP_SWING_EVIDENCE[timeframe]:]:
            selected[timeframe][row["barId"]] = row
            swing_candidates.append(
                {
                    "barId": row["barId"], "timeframe": timeframe, "side": side,
                    "price": price,
                }
            )

    for candidate in candidates:
        timeframe = str(candidate["timeframe"])
        root = market.bar(str(candidate["rootBarId"]), as_of)
        displacement = market.bar(str(candidate["displacementBarId"]), as_of)
        selected[timeframe][root["barId"]] = root
        selected[timeframe][displacement["barId"]] = displacement
        rows = market.bars(timeframe, displacement["available"], 8)
        for row in rows[-4:]:
            selected[timeframe][row["barId"]] = row

    columns = ["barId", "timeUtc", "open", "high", "low", "close", "spreadPoints"]
    data: dict[str, list[list[Any]]] = {}
    for timeframe in MAP_LIMITS:
        ordered = sorted(selected[timeframe].values(), key=lambda item: item["time"])
        data[timeframe] = [
            [
                row["barId"], utc_text(row["time"]), round(row["open"], 5),
                round(row["high"], 5), round(row["low"], 5), round(row["close"], 5),
                round(row["spreadPoints"], 2),
            ]
            for row in ordered
        ]
    swing_candidates.sort(key=lambda item: split_bar_id(item["barId"])[1])
    return {"columns": columns, "data": data}, swing_candidates


def build_plan_packet(
    market: MarketData,
    as_of: int,
    symbol: str,
    focus_family_ids: set[str] | None = None,
    external_authority: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one compact semantic packet for map, root, and causal refinement."""
    # A focused request can happen long after a root formed. Scan the full local
    # HTF window so a queued untouched root does not disappear merely because
    # newer mechanical candidates were created while price was away from it.
    scan_maximum = 512 if focus_family_ids is not None else 10
    root_candidates = mechanical_root_candidates(
        market, as_of, maximum=scan_maximum
    )
    evidence, swing_candidates = _map_evidence(market, as_of, root_candidates)
    child_candidates: list[dict[str, Any]] = []
    for timeframe in ("M30", "M15", "M5"):
        child_candidates.extend(
            mechanical_root_candidates(
                market,
                as_of,
                maximum=(PLAN_LIMITS[timeframe] if focus_family_ids is not None else 8),
                timeframe_limits={timeframe: PLAN_LIMITS[timeframe]},
            )
        )
    lineage_families = _physical_lineage_families(
        market,
        as_of,
        root_candidates,
        child_candidates,
        swing_candidates,
        external_authority,
    )
    if focus_family_ids is not None:
        lineage_families = [
            family for family in lineage_families
            if str(family["familyId"]) in focus_family_ids
        ]
    family_bar_ids = _nested_bar_ids(lineage_families)

    selected_m5: dict[str, dict[str, Any]] = {
        row["barId"]: row for row in market.bars("M5", as_of, 20)
    }
    for candidate in [*root_candidates, *child_candidates]:
        root = market.bar(str(candidate["rootBarId"]), as_of)
        displacement = market.bar(str(candidate["displacementBarId"]), as_of)
        start = root["time"] - TIMEFRAME_SECONDS["M15"]
        end = displacement["available"] + TIMEFRAME_SECONDS["M5"]
        for row in market.between("M5", start, min(as_of, end)):
            selected_m5[row["barId"]] = row
    for selected_id in family_bar_ids:
        row = market.bar(selected_id, as_of)
        if row["tf"] not in evidence["data"]:
            continue
        if row["tf"] == "M5":
            selected_m5[row["barId"]] = row
            continue
        existing = {item[0] for item in evidence["data"][row["tf"]]}
        if row["barId"] not in existing:
            evidence["data"][row["tf"]].append(
                [
                    row["barId"], utc_text(row["time"]), round(row["open"], 5),
                    round(row["high"], 5), round(row["low"], 5), round(row["close"], 5),
                    round(row["spreadPoints"], 2),
                ]
            )
            evidence["data"][row["tf"]].sort(key=lambda item: split_bar_id(item[0])[1])

    evidence["data"]["M5"] = [
        [
            row["barId"], utc_text(row["time"]), round(row["open"], 5),
            round(row["high"], 5), round(row["low"], 5), round(row["close"], 5),
            round(row["spreadPoints"], 2),
        ]
        for row in sorted(selected_m5.values(), key=lambda item: item["time"])[-72:]
    ]
    # PLAN never prices an order. Bar IDs already encode time and row order preserves
    # chronology, so repeating UTC text and spread here only wastes vision budget.
    evidence = {
        "columns": ["barId", "open", "high", "low", "close"],
        "data": {
            timeframe: [
                [row[0], row[2], row[3], row[4], row[5]]
                for row in rows
            ]
            for timeframe, rows in evidence["data"].items()
        },
    }
    decision_bar = market.bars("M15", as_of, 1)[-1]
    if focus_family_ids is not None:
        focused_ids = set(family_bar_ids)
        focused_ids.add(decision_bar["barId"])
        evidence["data"] = {
            timeframe: [
                row for row in rows
                if str(row[0]) in focused_ids
            ]
            for timeframe, rows in evidence["data"].items()
        }
        swing_candidates = [
            swing for swing in swing_candidates
            if str(swing["barId"]) in focused_ids
        ]
    authority = resolved_external_authority(market, external_authority, as_of)
    return {
        "pipelineVersion": PIPELINE_VERSION,
        "phase": "PLAN",
        "symbol": symbol,
        "asOfUtc": utc_text(as_of),
        "allowedTimeframes": ["H1", "M30", "M15", "M5"],
        "m1Excluded": True,
        "decisionReference": {
            "barId": decision_bar["barId"],
            "timeUtc": utc_text(decision_bar["time"]),
            "close": decision_bar["close"],
        },
        "focusedRootApproach": focus_family_ids is not None,
        "focusedFamilyIds": sorted(focus_family_ids or []),
        "externalMapAuthority": authority,
        "externalMapAuthorityBoundary": (
            "A frozen external owner survives trade close, cancellation, and internal rotation. Opposite "
            "EXTERNAL_CONTINUATION is impossible while status is ACTIVE. ACTIVE also freezes the dealing "
            "range, protected swing, and objective. OBJECTIVE_REACHED permits only a new same-direction "
            "continuation map. Only BROKEN with the recorded H1/M30 body break permits EXTERNAL_REVERSAL. "
            "H1/M30 liquidity inside the frozen dealing range remains internal; timeframe alone cannot "
            "promote it to an external objective."
            if authority else
            "No external owner has yet been frozen in this run; infer it from the supplied closed HTF chart."
        ),
        "taskBoundary": (
            "Freeze one complete scenario: map, objective, causal root OB, and every causal child OB down "
            "to the last unambiguous causal child on M30, M15, or M5. Do not force a lower timeframe when "
            "it creates competing or unrelated children. M1 is unavailable and must not be inferred. Root "
            "and child candidate lists are neutral navigation evidence, never automatic authorization."
        ),
        "physicalLineageFamilies": lineage_families,
        "physicalLineageBoundary": (
            "A family means only that a lower-timeframe opposite candle formed inside the parent candle "
            "or overlapped its physical delivery window. Eligible delivery/protected/objective IDs are "
            "mechanical navigation choices, not proof of meaningful structure, owner, objective quality, "
            "freshness, or causal refinement. Duplicate representations of one physical event preserve the "
            "highest valid parent timeframe so lower candles can be judged as refinements. An opposite M15 "
            "family inside an intact H1/M30 range is not a new opposing owner unless the frozen H1/M30 "
            "protected swing is body-broken. Independently approve or reject every semantic role."
        ),
        "swingCandidates": swing_candidates,
        "evidenceSelectionBoundary": (
            "Bars are recent closed context plus neutral swings, root deliveries, and M5 candles around "
            "their physical formation windows. The selection does not decide owner, scope, objective, "
            "OB causality, refinement, freshness, direction, or entry permission."
        ),
        "bars": evidence,
        "futureHidden": True,
    }


def build_map_packet(market: MarketData, as_of: int, symbol: str) -> dict[str, Any]:
    decision_bar = market.bars("M15", as_of, 1)[-1]
    root_candidates = mechanical_root_candidates(market, as_of, maximum=12)
    evidence, swing_candidates = _map_evidence(market, as_of, root_candidates)
    return {
        "pipelineVersion": PIPELINE_VERSION,
        "phase": "MAP",
        "symbol": symbol,
        "asOfUtc": utc_text(as_of),
        "allowedTimeframes": ["H1", "M30", "M15"],
        "m1Excluded": True,
        "decisionReference": {
            "barId": decision_bar["barId"],
            "timeUtc": utc_text(decision_bar["time"]),
            "close": decision_bar["close"],
        },
        "taskBoundary": (
            "Select only map, objective, and root. Do not select or reject for child refinement. "
            "Use decisionReference.close for the current PD-half check: continuation LONG requires "
            "close below the selected dealing-range EQ and continuation SHORT requires close above EQ. "
            "Evaluate INTERNAL_ROTATION separately: it may temporarily trade opposite the intact external "
            "owner toward the first mature internal liquidity, and must not be rejected merely because "
            "the external H1/M30 trend points the other way."
        ),
        "mechanicalRootCandidates": root_candidates,
        "mechanicalCandidateBoundary": (
            "These are neutral opposite-candle plus next-body-delivery candidates, not authorized OBs. "
            "Use them to avoid visual/time-index mistakes, then independently verify meaningful protected "
            "swing, objective-before-displacement causality, same price event, and freshness. The displacement "
            "candle itself does not count as a later mitigation; laterClosedBars starts after it."
        ),
        "swingCandidates": swing_candidates,
        "evidenceSelectionBoundary": (
            "Selectable bars are the union of recent closed bars, neutral two-left/two-right swing "
            "candidates, root/displacement candidates, and their nearby closed bars. Candidate extraction "
            "does not classify owner, liquidity quality, OB causality, freshness, scope, or trade direction."
        ),
        "bars": evidence,
        "futureHidden": True,
    }


def build_refinement_packet(
    market: MarketData, as_of: int, symbol: str, mapped: dict[str, Any]
) -> dict[str, Any]:
    return {
        "pipelineVersion": PIPELINE_VERSION,
        "phase": "REFINEMENT",
        "symbol": symbol,
        "asOfUtc": utc_text(as_of),
        "rootApproachAtUtc": mapped["rootApproachAtUtc"],
        "frozenMap": {
            key: mapped[key]
            for key in (
                "mapHash", "direction", "scope", "dealingRange", "objective",
                "mapProtectedSwing", "root", "intermediateLiquidityBarIds",
            )
        },
        "allowedTimeframes": ["M30", "M15", "M5"],
        "m1Excluded": True,
        "taskBoundary": "Select only causal child OB lineage for the frozen root and price event.",
        "bars": market.compact(as_of, REFINEMENT_LIMITS),
        "futureHidden": True,
    }


def build_trigger_packet(
    market: MarketData,
    as_of: int,
    symbol: str,
    scenario: dict[str, Any],
    sweep_events: list[dict[str, Any]] | None = None,
    liquidity_candidates: list[dict[str, Any]] | None = None,
    choch_candidates: list[dict[str, Any]] | None = None,
    correction_candidates: list[dict[str, Any]] | None = None,
    choch_break_candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    candidate_groups = {
        "liquidityCandidates": list(liquidity_candidates or []),
        "sweepCandidates": list(sweep_events or []),
        "chochReferenceCandidates": list(choch_candidates or []),
        "m5CorrectionSwingCandidates": list(correction_candidates or []),
        "chochBreakCandidates": list(choch_break_candidates or []),
    }
    source_upgrades = [
        item for item in scenario.get("sourceUpgradeCandidates", [])
        if item.get("touchBarId") and not item.get("invalidatedAtUtc")
    ]
    bars = market.compact(as_of, TRIGGER_RECENT_LIMITS)
    required_ids = set(_nested_bar_ids(candidate_groups))
    required_ids.update(_nested_bar_ids(source_upgrades))
    required_ids.update(
        item
        for item in _nested_bar_ids(
            {
                "finalChild": scenario.get("finalChild"),
                "childTouchBarId": scenario.get("childTouchBarId"),
            }
        )
        if split_bar_id(item)[0] in TRIGGER_RECENT_LIMITS
    )
    for selected_id in sorted(required_ids, key=lambda item: split_bar_id(item)[1]):
        timeframe, _ = split_bar_id(selected_id)
        if timeframe not in TRIGGER_RECENT_LIMITS:
            continue
        if any(row[0] == selected_id for row in bars["data"][timeframe]):
            continue
        row = market.bar(selected_id, as_of)
        bars["data"][timeframe].append(
            [
                row["barId"], utc_text(row["time"]), round(row["open"], 5),
                round(row["high"], 5), round(row["low"], 5),
                round(row["close"], 5), round(row["spreadPoints"], 2),
            ]
        )
    for timeframe in bars["data"]:
        bars["data"][timeframe].sort(key=lambda item: split_bar_id(item[0])[1])
    return {
        "pipelineVersion": PIPELINE_VERSION,
        "phase": "TRIGGER_WATCH",
        "symbol": symbol,
        "asOfUtc": utc_text(as_of),
        "childTouchAtUtc": scenario["childTouchAtUtc"],
        "frozenScenario": {
            key: scenario[key]
            for key in (
                "scenarioHash", "direction", "scope", "dealingRange", "objective",
                "mapProtectedSwing", "root", "refinements", "finalChild",
            )
        },
        "sourceUpgradeCandidates": source_upgrades,
        **candidate_groups,
        "taskBoundary": (
            "Select one mature liquidity that has a matching completed sweepCandidates event, the "
            "governing M5 correction swing, and one completed meaningful M1 body-CHoCH pair from "
            "chochBreakCandidates. Also select a touched sourceUpgradeCandidate only when its later "
            "same-direction root/child lineage explains the same frozen owner and objective more "
            "precisely than the original source; otherwise return null. The engine derives the "
            "execution OB and order from frozen bars. Do not invent a price or create an order."
        ),
        "bars": bars,
        "futureHidden": True,
    }


def _directional_ob(bar: dict[str, Any], direction: str) -> bool:
    return bar["close"] < bar["open"] if direction == "LONG" else bar["close"] > bar["open"]


def _delivery_valid(
    ob: dict[str, Any], displacement: dict[str, Any], protected: dict[str, Any], direction: str
) -> bool:
    if displacement["tf"] != ob["tf"] or protected["tf"] != ob["tf"]:
        return False
    if displacement["time"] <= ob["time"] or protected["time"] >= displacement["time"]:
        return False
    if direction == "LONG":
        return displacement["close"] > displacement["open"] and displacement["close"] > protected["high"]
    return displacement["close"] < displacement["open"] and displacement["close"] < protected["low"]


def _freeze_node(
    raw: dict[str, Any], market: MarketData, as_of: int, direction: str, allowed_tfs: set[str]
) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise V4ContractError("OB lineage node is missing")
    selected = [raw.get(key) for key in ("obBarId", "displacementBarId", "protectedSwingBarId")]
    if not all(isinstance(item, str) and item for item in selected):
        raise V4ContractError("OB lineage node has a missing barId")
    ob, displacement, protected = (market.bar(item, as_of) for item in selected)
    if ob["tf"] not in allowed_tfs:
        raise V4ContractError(f"OB timeframe is not allowed at this stage: {ob['tf']}")
    if not _directional_ob(ob, direction):
        raise V4ContractError(f"selected OB is not an opposite-color candle: {ob['barId']}")
    if not _delivery_valid(ob, displacement, protected, direction):
        raise V4ContractError(f"selected OB does not own the declared body-break delivery: {ob['barId']}")
    proximal = ob["high"] if direction == "LONG" else ob["low"]
    distal = ob["low"] if direction == "LONG" else ob["high"]
    return {
        "tf": ob["tf"],
        "obBarId": ob["barId"],
        "displacementBarId": displacement["barId"],
        "protectedSwingBarId": protected["barId"],
        "low": ob["low"],
        "high": ob["high"],
        "proximal": proximal,
        "distal": distal,
        "formedAtUtc": utc_text(ob["available"]),
        "deliveryAvailableAtUtc": utc_text(displacement["available"]),
    }


def discover_source_upgrade_candidates(
    market: MarketData,
    scenario: dict[str, Any],
    as_of: int,
    symbol: str,
) -> list[dict[str, Any]]:
    """Collect neutral, later same-owner source lineages without another API call."""
    if scenario.get("childTouchAtUtc") is None:
        return []
    packet = build_plan_packet(
        market,
        as_of,
        symbol,
        external_authority=external_authority_from_scenario(scenario, None),
    )
    direction = str(scenario["direction"])
    frozen_at = parse_utc(str(scenario["frozenAtUtc"]))
    old_root = scenario["root"]
    old_child = scenario["finalChild"]
    candidates: list[dict[str, Any]] = []
    for family in packet.get("physicalLineageFamilies", []):
        if str(family.get("direction")) != direction:
            continue
        for path in family.get("lineagePathOptions", []):
            root = _freeze_node(
                path["root"], market, as_of, direction, {"H1", "M30", "M15"}
            )
            refinements = [
                _freeze_node(
                    item, market, as_of, direction, {"M30", "M15", "M5"}
                )
                for item in path.get("refinements", [])
            ]
            if not refinements or parse_utc(root["formedAtUtc"]) <= frozen_at:
                continue
            final_child = refinements[-1]
            if root["high"] < old_root["low"] or root["low"] > old_root["high"]:
                continue
            tighter_distal = (
                final_child["distal"] > old_child["distal"]
                if direction == "LONG"
                else final_child["distal"] < old_child["distal"]
            )
            if not tighter_distal:
                continue
            selection_id = "source-upgrade-" + canonical_hash(
                {
                    "scenarioHash": scenario["scenarioHash"],
                    "root": root["obBarId"],
                    "refinements": [item["obBarId"] for item in refinements],
                }
            )[:16]
            candidates.append(
                {
                    "selectionId": selection_id,
                    "discoveredAtUtc": utc_text(as_of),
                    "root": root,
                    "refinements": refinements,
                    "finalChild": final_child,
                    "touchAtUtc": None,
                    "touchBarId": None,
                    "invalidatedAtUtc": None,
                }
            )
    unique = {item["selectionId"]: item for item in candidates}
    return list(unique.values())


def advance_source_upgrade_candidates(
    scenario: dict[str, Any], row: dict[str, Any]
) -> list[dict[str, Any]]:
    touched: list[dict[str, Any]] = []
    direction = str(scenario["direction"])
    for candidate in scenario.get("sourceUpgradeCandidates", []):
        if candidate.get("touchBarId") or candidate.get("invalidatedAtUtc"):
            continue
        child = candidate["finalChild"]
        if row["available"] <= parse_utc(str(child["deliveryAvailableAtUtc"])):
            continue
        if zone_distal_crossed(row, child, direction, body=True):
            candidate["invalidatedAtUtc"] = utc_text(row["available"])
            continue
        if zone_touched(row, child):
            candidate["touchAtUtc"] = utc_text(row["available"])
            candidate["touchBarId"] = row["barId"]
            touched.append(candidate)
    return touched


def apply_source_upgrade(
    scenario: dict[str, Any], watch: dict[str, Any]
) -> None:
    upgrade = watch.get("sourceUpgrade")
    if not upgrade:
        return
    scenario.setdefault(
        "originalSource",
        {
            "root": scenario["root"],
            "refinements": scenario["refinements"],
            "finalChild": scenario["finalChild"],
            "childTouchAtUtc": scenario["childTouchAtUtc"],
            "childTouchBarId": scenario["childTouchBarId"],
        },
    )
    scenario["root"] = upgrade["root"]
    scenario["refinements"] = upgrade["refinements"]
    scenario["finalChild"] = upgrade["finalChild"]
    scenario["childTouchAtUtc"] = upgrade["touchAtUtc"]
    scenario["childTouchBarId"] = upgrade["touchBarId"]
    scenario["executionSourceUpgradeSelectionId"] = upgrade["selectionId"]


def _selection_pool(
    payload: dict[str, Any], market: MarketData, as_of: int, maximum: int
) -> list[str]:
    raw = payload.get("selectedBarIds")
    if not isinstance(raw, list) or len(raw) > maximum:
        raise V4ContractError(f"selectedBarIds must be an array with at most {maximum} items")
    pool = [str(item) for item in raw]
    if len(pool) != len(set(pool)):
        raise V4ContractError("selectedBarIds contains duplicates")
    for selected_id in pool:
        market.bar(selected_id, as_of)
    return pool


def _pool_id(pool: list[str], index: Any, role: str) -> str:
    if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(pool):
        raise V4ContractError(f"{role} index does not reference selectedBarIds")
    return pool[index]


def _node_ids(raw: dict[str, Any] | None, pool: list[str], role: str) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise V4ContractError(f"{role} OB lineage node is missing")
    return {
        "obBarId": _pool_id(pool, raw.get("obIndex"), f"{role}.ob"),
        "displacementBarId": _pool_id(pool, raw.get("displacementIndex"), f"{role}.displacement"),
        "protectedSwingBarId": _pool_id(pool, raw.get("protectedSwingIndex"), f"{role}.protectedSwing"),
    }


def _objective_consumed(market: MarketData, objective: dict[str, Any], as_of: int) -> bool:
    origin = market.bar(objective["barId"], as_of)
    rows = market.between("M1", origin["available"], as_of)
    if objective["side"] == "HIGH":
        return any(row["high"] >= objective["price"] for row in rows)
    return any(row["low"] <= objective["price"] for row in rows)


def _node_consumed(market: MarketData, node: dict[str, Any], as_of: int, direction: str) -> bool:
    displacement = market.bar(node["displacementBarId"], as_of)
    rows = market.between("M1", displacement["available"], as_of)
    if direction == "LONG":
        return any(row["low"] <= node["distal"] for row in rows)
    return any(row["high"] >= node["distal"] for row in rows)


def _node_touched_after_delivery(
    market: MarketData, node: dict[str, Any], as_of: int, direction: str
) -> bool:
    displacement = market.bar(node["displacementBarId"], as_of)
    rows = market.between("M1", displacement["available"], as_of)
    if direction == "LONG":
        return any(row["low"] <= node["proximal"] for row in rows)
    return any(row["high"] >= node["proximal"] for row in rows)


def freeze_map(
    payload: dict[str, Any],
    market: MarketData,
    as_of: int,
) -> dict[str, Any] | None:
    if payload.get("schemaVersion") != "4.4.0":
        raise V4ContractError("MAP schemaVersion must be 4.4.0")
    scope_audit = payload.get("scopeAudit")
    expected_scopes = {
        "EXTERNAL_CONTINUATION", "INTERNAL_ROTATION", "EXTERNAL_REVERSAL"
    }
    if not isinstance(scope_audit, dict) or set(scope_audit) != expected_scopes:
        raise V4ContractError("MAP requires an audit of all three scenario scopes")
    for audit_scope, audit in scope_audit.items():
        if not isinstance(audit, dict) or audit.get("verdict") not in {
            "VALID", "INVALID", "UNRESOLVED"
        }:
            raise V4ContractError(f"MAP scope audit is invalid for {audit_scope}")
    action = payload.get("action")
    if action in {"NO_MAP", "DATA_ERROR"}:
        if payload.get("selectedBarIds") != []:
            raise V4ContractError(f"{action} must not contain MAP evidence")
        if payload.get("intermediateLiquidityIndexes") != []:
            raise V4ContractError(f"{action} must not contain MAP arrays")
        if payload.get("rootFreshness") is not None:
            raise V4ContractError(f"{action} must not declare root freshness")
        if any(item.get("verdict") == "VALID" for item in scope_audit.values()):
            raise V4ContractError(f"{action} conflicts with a VALID scope audit")
        return None
    if action != "MAP":
        raise V4ContractError(f"unsupported MAP action: {action}")

    pool = _selection_pool(payload, market, as_of, 16)
    direction = payload.get("direction")
    scope = payload.get("scope")
    if direction not in {"LONG", "SHORT"}:
        raise V4ContractError("MAP requires LONG or SHORT direction")
    if scope not in {"EXTERNAL_CONTINUATION", "INTERNAL_ROTATION", "EXTERNAL_REVERSAL"}:
        raise V4ContractError("MAP requires a supported scenario scope")
    if scope_audit[scope].get("verdict") != "VALID":
        raise V4ContractError("chosen MAP scope was not marked VALID in scopeAudit")
    if payload.get("rootFreshness") != "FRESH":
        raise V4ContractError("MAP requires the selected root to be declared FRESH")

    range_raw = payload.get("dealingRange") or {}
    range_high = market.bar(_pool_id(pool, range_raw.get("highIndex"), "dealingRange.high"), as_of)
    range_low = market.bar(_pool_id(pool, range_raw.get("lowIndex"), "dealingRange.low"), as_of)
    if range_high["tf"] not in {"H1", "M30"} or range_low["tf"] not in {"H1", "M30"}:
        raise V4ContractError("dealing range must use H1/M30 bars")
    if range_low["low"] >= range_high["high"]:
        raise V4ContractError("dealing range low is not below its high")
    latest = market.bars("M1", as_of, 1)[-1]
    eq = (range_low["low"] + range_high["high"]) / 2.0

    objective_raw = payload.get("objective") or {}
    objective_bar = market.bar(_pool_id(pool, objective_raw.get("barIndex"), "objective"), as_of)
    expected_side = "HIGH" if direction == "LONG" else "LOW"
    if objective_raw.get("kind") not in {
        "EXTERNAL_SWING", "INTERNAL_SWING", "REACTION_TRAP", "RANGE_EDGE",
        "TRENDLINE_CLUSTER",
    }:
        raise V4ContractError("MAP requires a supported objective liquidity kind")
    if scope == "INTERNAL_ROTATION" and objective_raw.get("kind") == "EXTERNAL_SWING":
        raise V4ContractError("internal rotation requires an internal objective kind")
    if scope != "INTERNAL_ROTATION" and objective_raw.get("kind") == "INTERNAL_SWING":
        raise V4ContractError("external scenario cannot use an internal swing objective")
    objective_price = objective_bar["high"] if expected_side == "HIGH" else objective_bar["low"]
    if direction == "LONG" and objective_price <= latest["close"]:
        raise V4ContractError("long objective is not above current price")
    if direction == "SHORT" and objective_price >= latest["close"]:
        raise V4ContractError("short objective is not below current price")
    objective = {
        "barId": objective_bar["barId"], "tf": objective_bar["tf"], "side": expected_side,
        "kind": objective_raw.get("kind"), "price": objective_price,
    }
    if (
        scope in {"EXTERNAL_CONTINUATION", "EXTERNAL_REVERSAL"}
        and objective["kind"] == "EXTERNAL_SWING"
        and objective["tf"] not in {"H1", "M30"}
    ):
        raise V4ContractError(
            "external swing objective must originate from H1 or M30 structure"
        )
    if _objective_consumed(market, objective, as_of):
        raise V4ContractError("objective was already consumed before MAP")

    map_protected = market.bar(
        _pool_id(pool, payload.get("mapProtectedSwingIndex"), "mapProtectedSwing"), as_of
    )
    if map_protected["tf"] not in {"H1", "M30"}:
        raise V4ContractError("map protected swing must be H1/M30")
    owner_break_target_index = payload.get("ownerBreakTargetIndex")
    owner_break_target_id = (
        _pool_id(pool, owner_break_target_index, "ownerBreakTarget")
        if owner_break_target_index is not None else None
    )
    owner_break_index = payload.get("ownerBreakIndex")
    owner_break_id = (
        _pool_id(pool, owner_break_index, "ownerBreak") if owner_break_index is not None else None
    )
    if scope == "EXTERNAL_REVERSAL":
        if not owner_break_target_id or not owner_break_id:
            raise V4ContractError("external reversal requires an old-owner target and its body-break bar")
        owner_break_target = market.bar(str(owner_break_target_id), as_of)
        owner_break = market.bar(str(owner_break_id), as_of)
        if owner_break_target["tf"] not in {"H1", "M30"} or owner_break["tf"] not in {"H1", "M30"}:
            raise V4ContractError("external reversal owner target and break must be H1/M30")
        if owner_break_target["tf"] != owner_break["tf"]:
            raise V4ContractError("external reversal owner target and break must use the same timeframe")
        expected_boundary = range_high["barId"] if direction == "LONG" else range_low["barId"]
        if owner_break_target["barId"] != expected_boundary:
            raise V4ContractError(
                "external reversal must body-break the selected external dealing-range boundary"
            )
        if direction == "LONG" and owner_break["close"] <= owner_break_target["high"]:
            raise V4ContractError("external long reversal did not body-break the protected high")
        if direction == "SHORT" and owner_break["close"] >= owner_break_target["low"]:
            raise V4ContractError("external short reversal did not body-break the protected low")
    elif owner_break_target_id or owner_break_id:
        raise V4ContractError("owner-break fields are only valid for EXTERNAL_REVERSAL")

    root = _freeze_node(
        _node_ids(payload.get("root"), pool, "root"),
        market, as_of, direction, {"H1", "M30", "M15"},
    )
    if scope == "INTERNAL_ROTATION":
        if not range_low["low"] < objective_price < range_high["high"]:
            raise V4ContractError("internal rotation objective must remain inside the active dealing range")
        if objective_raw.get("kind") == "EXTERNAL_SWING":
            raise V4ContractError("internal rotation objective cannot be classified as EXTERNAL_SWING")
    if _node_consumed(market, root, as_of, direction):
        raise V4ContractError(f"root OB was fully consumed before MAP: {root['obBarId']}")

    intermediate_indexes = payload.get("intermediateLiquidityIndexes", [])
    if not isinstance(intermediate_indexes, list) or len(intermediate_indexes) != len(set(intermediate_indexes)):
        raise V4ContractError("intermediateLiquidityIndexes must be a unique array")
    intermediate = [
        market.bar(_pool_id(pool, item, f"intermediateLiquidity[{index}]"), as_of)["barId"]
        for index, item in enumerate(intermediate_indexes)
    ]
    if objective["barId"] in intermediate:
        raise V4ContractError(
            "the final objective cannot also be intermediate liquidity"
        )
    semantic = {
        "direction": direction, "scope": scope,
        "rangeHighBarId": range_high["barId"], "rangeLowBarId": range_low["barId"],
        "objective": objective, "mapProtectedSwingBarId": map_protected["barId"],
        "ownerBreakTargetBarId": owner_break_target_id, "ownerBreakBarId": owner_break_id,
        "root": {key: root[key] for key in ("obBarId", "displacementBarId", "protectedSwingBarId")},
        "intermediateLiquidityBarIds": intermediate,
    }
    map_hash = canonical_hash(semantic)
    return {
        "mapHash": map_hash,
        "mapFrozenAtUtc": utc_text(as_of),
        "lastReauthorizedAtUtc": utc_text(as_of),
        "direction": direction,
        "scope": scope,
        "dealingRange": {
            "highBarId": range_high["barId"], "lowBarId": range_low["barId"],
            "high": range_high["high"], "low": range_low["low"], "eq": eq,
        },
        "objective": objective,
        "mapProtectedSwing": {
            "barId": map_protected["barId"], "tf": map_protected["tf"],
            "high": map_protected["high"], "low": map_protected["low"],
        },
        "ownerBreakTargetBarId": owner_break_target_id,
        "ownerBreakBarId": owner_break_id,
        "root": root,
        "refinements": [],
        "finalChild": None,
        "intermediateLiquidityBarIds": intermediate,
        "rootApproachAtUtc": None,
        "rootApproachBarId": None,
        "childTouchAtUtc": None,
        "childTouchBarId": None,
        "reason": str(payload.get("reason", "")),
    }


def freeze_refinement(
    payload: dict[str, Any],
    market: MarketData,
    as_of: int,
    mapped: dict[str, Any],
    accepted_hashes: set[str] | None = None,
) -> dict[str, Any] | None:
    if payload.get("schemaVersion") != "4.2.0":
        raise V4ContractError("REFINEMENT schemaVersion must be 4.2.0")
    action = payload.get("action")
    if action in {"NO_REFINEMENT", "DATA_ERROR"}:
        if payload.get("selectedBarIds") != [] or payload.get("refinements") != []:
            raise V4ContractError(f"{action} must not contain refinement evidence")
        return None
    if action != "REFINEMENT":
        raise V4ContractError(f"unsupported REFINEMENT action: {action}")
    pool = _selection_pool(payload, market, as_of, 16)
    raw = payload.get("refinements")
    if not isinstance(raw, list) or not raw:
        raise V4ContractError("REFINEMENT requires at least one causal child OB")
    direction = mapped["direction"]
    refinements = [
        _freeze_node(
            _node_ids(item, pool, f"refinement[{index}]"),
            market, as_of, direction, {"M30", "M15", "M5"},
        )
        for index, item in enumerate(raw)
    ]
    previous = mapped["root"]
    for child in refinements:
        if TIMEFRAME_MINUTES[child["tf"]] > TIMEFRAME_MINUTES[previous["tf"]]:
            raise V4ContractError("refinement timeframe cannot be higher than its parent")
        if child["high"] < previous["low"] or child["low"] > previous["high"]:
            raise V4ContractError("child OB does not overlap its causal parent price event")
        if _node_consumed(market, child, as_of, direction):
            raise V4ContractError(f"child OB was fully consumed before REFINEMENT: {child['obBarId']}")
        previous = child
    semantic = {
        "mapHash": mapped["mapHash"],
        "refinements": [
            {key: node[key] for key in ("obBarId", "displacementBarId", "protectedSwingBarId")}
            for node in refinements
        ],
    }
    semantic_hash = canonical_hash(semantic)
    scenario_hash = canonical_hash(
        {"semanticHash": semantic_hash, "refinementFrozenAtUtc": utc_text(as_of)}
    )
    if accepted_hashes is not None and scenario_hash in accepted_hashes:
        raise V4ContractError("duplicate scenario hash")
    return {
        **mapped,
        "scenarioHash": scenario_hash,
        "semanticHash": semantic_hash,
        "frozenAtUtc": mapped["mapFrozenAtUtc"],
        "refinementFrozenAtUtc": utc_text(as_of),
        "lastReauthorizedAtUtc": utc_text(as_of),
        "refinements": refinements,
        "finalChild": refinements[-1],
        "parentApproachPrepared": True,
        "parentApproachAtUtc": mapped["rootApproachAtUtc"],
        "childTouchAtUtc": None,
        "childTouchBarId": None,
        "refinementReason": str(payload.get("reason", "")),
    }


def _atomic_lineage_selections(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Resolve schema-safe lineage IDs to one prevalidated physical tuple."""
    output: dict[str, dict[str, Any]] = {}
    for family in packet.get("physicalLineageFamilies", []):
        family_id = str(family["familyId"])
        for option in family.get("rootSelections", []):
            selection_id = str(option["selectionId"])
            output[selection_id] = {
                "familyId": family_id,
                "role": "ROOT",
                "node": {
                    key: str(option[key])
                    for key in ("obBarId", "displacementBarId", "protectedSwingBarId")
                },
            }
        for child in family.get("childCandidates", []):
            for option in child.get("selectionOptions", []):
                selection_id = str(option["selectionId"])
                output[selection_id] = {
                    "familyId": family_id,
                    "role": "REFINEMENT",
                    "node": {
                        key: str(option[key])
                        for key in ("obBarId", "displacementBarId", "protectedSwingBarId")
                    },
                }
    return output


def _atomic_lineage_paths(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for family in packet.get("physicalLineageFamilies", []):
        family_id = str(family["familyId"])
        for option in family.get("lineagePathOptions", []):
            path_id = str(option["pathSelectionId"])
            output[path_id] = {
                "familyId": family_id,
                "root": {
                    key: str(option["root"][key])
                    for key in ("obBarId", "displacementBarId", "protectedSwingBarId")
                },
                "refinements": [
                    {
                        key: str(node[key])
                        for key in ("obBarId", "displacementBarId", "protectedSwingBarId")
                    }
                    for node in option["refinements"]
                ],
            }
    return output


def _atomic_scenario_options(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    keys = (
        "direction", "scope", "dealingRange", "objective",
        "mapProtectedSwingBarId", "ownerBreakTargetBarId", "ownerBreakBarId",
        "lineagePathSelectionId", "intermediateLiquidityBarIds",
    )
    for family in packet.get("physicalLineageFamilies", []):
        for option in family.get("scenarioOptions", []):
            selection_id = str(option["scenarioSelectionId"])
            output[selection_id] = {key: option[key] for key in keys}
    return output


def _validate_plan_against_external_authority(
    packet: dict[str, Any] | None,
    *,
    direction: str,
    scope: str,
    range_high_id: str,
    range_low_id: str,
    map_protected_id: str,
    objective: dict[str, Any],
    owner_break_target_id: str | None,
    owner_break_id: str | None,
) -> None:
    """Make frozen external-map ownership an engine invariant, not model judgment."""
    authority = packet.get("externalMapAuthority") if packet else None
    if not authority:
        return
    status = str(authority.get("status", "ACTIVE"))
    owner_direction = str(authority["direction"])
    if status == "ACTIVE":
        frozen_range = authority["dealingRange"]
        if (
            str(range_high_id) != str(frozen_range["highBarId"])
            or str(range_low_id) != str(frozen_range["lowBarId"])
            or str(map_protected_id)
            != str(authority["protectedSwing"]["barId"])
        ):
            raise V4ContractError(
                "PLAN cannot redefine an active external dealing range or protected swing"
            )
        if scope == "EXTERNAL_CONTINUATION":
            frozen_objective = authority.get("objective")
            if direction != owner_direction:
                raise V4ContractError(
                    "opposite external continuation cannot replace an active owner"
                )
            if (
                not isinstance(frozen_objective, dict)
                or str(objective["barId"]) != str(frozen_objective["barId"])
            ):
                raise V4ContractError(
                    "same-owner continuation must preserve the active external objective"
                )
        elif scope == "EXTERNAL_REVERSAL":
            raise V4ContractError(
                "external reversal requires a body-broken external authority"
            )
        else:
            low = float(frozen_range["low"])
            high = float(frozen_range["high"])
            if not low <= float(objective["price"]) <= high:
                raise V4ContractError(
                    "internal rotation objective must remain inside the active external range"
                )
        return
    if status == "OBJECTIVE_REACHED":
        if scope == "EXTERNAL_CONTINUATION" and direction != owner_direction:
            raise V4ContractError(
                "fulfilled authority may advance only in its existing direction"
            )
        if scope == "EXTERNAL_REVERSAL":
            raise V4ContractError(
                "objective completion alone cannot authorize an external reversal"
            )
        return
    if status == "BROKEN":
        if scope == "EXTERNAL_CONTINUATION":
            raise V4ContractError(
                "body-broken authority cannot authorize external continuation"
            )
        if scope == "EXTERNAL_REVERSAL":
            if direction == owner_direction:
                raise V4ContractError(
                    "external reversal must oppose the body-broken owner"
                )
            if (
                str(owner_break_target_id)
                != str(authority["protectedSwing"]["barId"])
                or str(owner_break_id) != str(authority["bodyBreakBarId"])
            ):
                raise V4ContractError(
                    "external reversal must use the frozen owner break evidence"
                )
        return
    raise V4ContractError(f"unsupported external authority status: {status}")


def freeze_plan(
    payload: dict[str, Any],
    market: MarketData,
    as_of: int,
    accepted_hashes: set[str] | None = None,
    packet: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    schema_version = payload.get("schemaVersion")
    if schema_version not in {
        "4.0.0", "4.7.0", "4.8.0", "4.9.0", "4.10.0", "4.11.0"
    }:
        raise V4ContractError(
            "PLAN schemaVersion must be 4.0.0, 4.7.0, 4.8.0, 4.9.0, 4.10.0, or 4.11.0"
        )
    atomic_scenario = schema_version in {"4.10.0", "4.11.0"}
    if atomic_scenario:
        action = payload.get("action")
        if action in {"NO_PLAN", "DATA_ERROR"}:
            if payload.get("scenarioSelectionId") is not None:
                raise V4ContractError(f"{action} must not contain a scenario selection")
            return None
        if action != "PLAN":
            raise V4ContractError(f"unsupported PLAN action: {action}")
        if schema_version == "4.11.0":
            audit = payload.get("semanticAudit")
            if not isinstance(audit, dict) or set(audit) != set(PLAN_SEMANTIC_AUDIT_KEYS):
                raise V4ContractError("PLAN semantic audit is incomplete")
            failed = [
                key for key in PLAN_SEMANTIC_AUDIT_KEYS
                if audit.get(key) != "PASS"
            ]
            if failed:
                raise V4ContractError(
                    "PLAN cannot approve a scenario with unresolved semantic audit: "
                    + ",".join(failed)
                )
        if packet is None:
            raise V4ContractError("PLAN 4.10 requires the originating evidence packet")
        selected = _atomic_scenario_options(packet).get(
            str(payload.get("scenarioSelectionId"))
        )
        if selected is None:
            raise V4ContractError(
                "PLAN scenarioSelectionId is not a supplied prevalidated scenario"
            )
        resolved = {
            "schemaVersion": "4.9.0",
            "action": "PLAN",
            **selected,
            "reason": str(payload.get("reason", "")),
        }
        return freeze_plan(resolved, market, as_of, accepted_hashes, packet)
    direct_ids = schema_version in {"4.7.0", "4.8.0", "4.9.0"}
    atomic_lineage = schema_version == "4.8.0"
    atomic_path = schema_version == "4.9.0"
    action = payload.get("action")
    if action in {"NO_PLAN", "DATA_ERROR"}:
        if not direct_ids and payload.get("selectedBarIds") != []:
            raise V4ContractError(f"{action} must not contain PLAN evidence")
        intermediate_key = "intermediateLiquidityBarIds" if direct_ids else "intermediateLiquidityIndexes"
        refinement_key = "refinementSelectionIds" if atomic_lineage else "refinements"
        if not atomic_path and payload.get(refinement_key) != []:
            raise V4ContractError(f"{action} must not contain PLAN arrays")
        if payload.get(intermediate_key) != []:
            raise V4ContractError(f"{action} must not contain PLAN arrays")
        if atomic_lineage and payload.get("rootSelectionId") is not None:
            raise V4ContractError(f"{action} must not contain a root selection")
        if atomic_path and payload.get("lineagePathSelectionId") is not None:
            raise V4ContractError(f"{action} must not contain a lineage path")
        return None
    if action != "PLAN":
        raise V4ContractError(f"unsupported PLAN action: {action}")
    pool = [] if direct_ids else _selection_pool(payload, market, as_of, 24)
    direction = payload.get("direction")
    scope = payload.get("scope")
    if direction not in {"LONG", "SHORT"}:
        raise V4ContractError("PLAN requires LONG or SHORT direction")
    if scope not in {"EXTERNAL_CONTINUATION", "INTERNAL_ROTATION", "EXTERNAL_REVERSAL"}:
        raise V4ContractError("PLAN requires a supported scenario scope")

    range_raw = payload.get("dealingRange") or {}
    range_high_id = (
        range_raw.get("highBarId") if direct_ids
        else _pool_id(pool, range_raw.get("highIndex"), "dealingRange.high")
    )
    range_low_id = (
        range_raw.get("lowBarId") if direct_ids
        else _pool_id(pool, range_raw.get("lowIndex"), "dealingRange.low")
    )
    range_high = market.bar(str(range_high_id), as_of)
    range_low = market.bar(str(range_low_id), as_of)
    if range_high["tf"] not in {"H1", "M30"} or range_low["tf"] not in {"H1", "M30"}:
        raise V4ContractError("dealing range must use H1/M30 bars")
    if range_low["low"] >= range_high["high"]:
        raise V4ContractError("dealing range low is not below its high")
    latest = market.bars("M1", as_of, 1)[-1]
    eq = (range_low["low"] + range_high["high"]) / 2.0

    objective_raw = payload.get("objective") or {}
    objective_bar_id = (
        objective_raw.get("barId") if direct_ids
        else _pool_id(pool, objective_raw.get("barIndex"), "objective")
    )
    objective_bar = market.bar(str(objective_bar_id), as_of)
    expected_side = "HIGH" if direction == "LONG" else "LOW"
    if objective_raw.get("side") != expected_side:
        raise V4ContractError("objective side conflicts with direction")
    if objective_raw.get("kind") not in {
        "EXTERNAL_SWING", "INTERNAL_SWING", "REACTION_TRAP", "RANGE_EDGE",
        "TRENDLINE_CLUSTER",
    }:
        raise V4ContractError("PLAN requires a supported objective liquidity kind")
    if scope == "INTERNAL_ROTATION" and objective_raw.get("kind") == "EXTERNAL_SWING":
        raise V4ContractError("internal rotation requires an internal objective kind")
    if scope != "INTERNAL_ROTATION" and objective_raw.get("kind") == "INTERNAL_SWING":
        raise V4ContractError("external scenario cannot use an internal swing objective")
    objective_price = objective_bar["high"] if expected_side == "HIGH" else objective_bar["low"]
    if direction == "LONG" and objective_price <= latest["close"]:
        raise V4ContractError("long objective is not above current price")
    if direction == "SHORT" and objective_price >= latest["close"]:
        raise V4ContractError("short objective is not below current price")
    objective = {
        "barId": objective_bar["barId"],
        "tf": objective_bar["tf"],
        "side": expected_side,
        "kind": objective_raw.get("kind"),
        "price": objective_price,
    }
    if (
        scope in {"EXTERNAL_CONTINUATION", "EXTERNAL_REVERSAL"}
        and objective["kind"] == "EXTERNAL_SWING"
        and objective["tf"] not in {"H1", "M30"}
    ):
        raise V4ContractError(
            "external swing objective must originate from H1 or M30 structure"
        )
    if _objective_consumed(market, objective, as_of):
        raise V4ContractError("objective was already consumed before PLAN")

    map_protected_id = (
        payload.get("mapProtectedSwingBarId") if direct_ids
        else _pool_id(pool, payload.get("mapProtectedSwingIndex"), "mapProtectedSwing")
    )
    map_protected = market.bar(str(map_protected_id), as_of)
    if map_protected["tf"] not in {"H1", "M30"}:
        raise V4ContractError("map protected swing must be H1/M30")
    owner_break_target_value = payload.get(
        "ownerBreakTargetBarId" if direct_ids else "ownerBreakTargetIndex"
    )
    owner_break_target_id = (
        str(owner_break_target_value) if direct_ids and owner_break_target_value is not None
        else _pool_id(pool, owner_break_target_value, "ownerBreakTarget")
        if owner_break_target_value is not None else None
    )
    owner_break_value = payload.get("ownerBreakBarId" if direct_ids else "ownerBreakIndex")
    owner_break_id = (
        str(owner_break_value) if direct_ids and owner_break_value is not None
        else _pool_id(pool, owner_break_value, "ownerBreak")
        if owner_break_value is not None else None
    )
    if scope == "EXTERNAL_REVERSAL":
        if not owner_break_target_id or not owner_break_id:
            raise V4ContractError("external reversal requires an old-owner target and its body-break bar")
        owner_break_target = market.bar(str(owner_break_target_id), as_of)
        owner_break = market.bar(str(owner_break_id), as_of)
        if owner_break_target["tf"] not in {"H1", "M30"} or owner_break["tf"] not in {"H1", "M30"}:
            raise V4ContractError("external reversal owner target and break must be H1/M30")
        if owner_break_target["tf"] != owner_break["tf"]:
            raise V4ContractError("external reversal owner target and break must use the same timeframe")
        if direction == "LONG" and owner_break["close"] <= owner_break_target["high"]:
            raise V4ContractError("external long reversal did not body-break the protected high")
        if direction == "SHORT" and owner_break["close"] >= owner_break_target["low"]:
            raise V4ContractError("external short reversal did not body-break the protected low")
    elif owner_break_target_id or owner_break_id:
        raise V4ContractError("owner-break fields are only valid for EXTERNAL_REVERSAL")

    _validate_plan_against_external_authority(
        packet,
        direction=direction,
        scope=scope,
        range_high_id=range_high["barId"],
        range_low_id=range_low["barId"],
        map_protected_id=map_protected["barId"],
        objective=objective,
        owner_break_target_id=owner_break_target_id,
        owner_break_id=owner_break_id,
    )

    if atomic_path:
        if packet is None:
            raise V4ContractError("PLAN 4.9 requires the originating evidence packet")
        paths = _atomic_lineage_paths(packet)
        selected_path = paths.get(str(payload.get("lineagePathSelectionId")))
        if selected_path is None:
            raise V4ContractError("PLAN lineagePathSelectionId is not a supplied maximal path")
        root_raw = selected_path["root"]
        refinement_raw = selected_path["refinements"]
        if not refinement_raw:
            raise V4ContractError("PLAN lineage path has no causal child")
    elif atomic_lineage:
        if packet is None:
            raise V4ContractError("PLAN 4.8 requires the originating evidence packet")
        selections = _atomic_lineage_selections(packet)
        root_selection_id = payload.get("rootSelectionId")
        root_selection = selections.get(str(root_selection_id))
        if root_selection is None or root_selection["role"] != "ROOT":
            raise V4ContractError("PLAN rootSelectionId is not a supplied root tuple")
        refinement_selection_ids = payload.get("refinementSelectionIds")
        if not isinstance(refinement_selection_ids, list) or not refinement_selection_ids:
            raise V4ContractError("PLAN requires at least one causal child selection")
        if len(refinement_selection_ids) != len(set(refinement_selection_ids)):
            raise V4ContractError("PLAN refinement selections contain duplicates")
        refinement_selections = [selections.get(str(item)) for item in refinement_selection_ids]
        if any(item is None or item["role"] != "REFINEMENT" for item in refinement_selections):
            raise V4ContractError("PLAN refinementSelectionIds contain an unknown child tuple")
        family_id = root_selection["familyId"]
        if any(item["familyId"] != family_id for item in refinement_selections if item):
            raise V4ContractError("PLAN root and refinements belong to different physical families")
        root_raw = root_selection["node"]
        refinement_raw = [item["node"] for item in refinement_selections if item]
    else:
        root_raw = payload.get("root") if direct_ids else _node_ids(payload.get("root"), pool, "root")
        refinement_raw = payload.get("refinements")
        if not isinstance(refinement_raw, list) or not refinement_raw:
            raise V4ContractError("PLAN requires at least one causal child OB")
    root = _freeze_node(
        root_raw, market, as_of, direction, {"H1", "M30", "M15"},
    )
    refinements = [
        _freeze_node(
            item if direct_ids else _node_ids(item, pool, f"refinement[{index}]"),
            market, as_of, direction, {"M30", "M15", "M5"},
        )
        for index, item in enumerate(refinement_raw)
    ]
    previous = root
    for child in refinements:
        if TIMEFRAME_MINUTES[child["tf"]] > TIMEFRAME_MINUTES[previous["tf"]]:
            raise V4ContractError("refinement timeframe cannot be higher than its parent")
        overlaps = child["high"] >= previous["low"] and child["low"] <= previous["high"]
        if not overlaps:
            raise V4ContractError("child OB does not overlap its causal parent price event")
        previous = child
    for node in [root, *refinements]:
        if _node_consumed(market, node, as_of, direction):
            raise V4ContractError(f"source OB was fully consumed before PLAN: {node['obBarId']}")
    final_child = refinements[-1]
    if _node_touched_after_delivery(market, final_child, as_of, direction):
        raise V4ContractError(
            f"final child OB was already touched before PLAN: {final_child['obBarId']}"
        )
    if scope == "EXTERNAL_CONTINUATION":
        if direction == "LONG" and final_child["proximal"] > eq:
            raise V4ContractError("continuation long child POI is not in discount")
        if direction == "SHORT" and final_child["proximal"] < eq:
            raise V4ContractError("continuation short child POI is not in premium")

    intermediate_values = payload.get(
        "intermediateLiquidityBarIds" if direct_ids else "intermediateLiquidityIndexes", []
    )
    if not isinstance(intermediate_values, list):
        raise V4ContractError("intermediate liquidity must be an array")
    if len(intermediate_values) != len(set(intermediate_values)):
        raise V4ContractError("intermediate liquidity contains duplicates")
    intermediate_ids = (
        [str(item) for item in intermediate_values]
        if direct_ids else [
            _pool_id(pool, item, f"intermediateLiquidity[{index}]")
            for index, item in enumerate(intermediate_values)
        ]
    )
    intermediate = [market.bar(item, as_of)["barId"] for item in intermediate_ids]
    if objective["barId"] in intermediate:
        raise V4ContractError(
            "the final objective cannot also be intermediate liquidity"
        )
    semantic = {
        "direction": direction,
        "scope": scope,
        "rangeHighBarId": range_high["barId"],
        "rangeLowBarId": range_low["barId"],
        "objective": objective,
        "mapProtectedSwingBarId": map_protected["barId"],
        "ownerBreakTargetBarId": owner_break_target_id,
        "ownerBreakBarId": owner_break_id,
        "root": {key: root[key] for key in ("obBarId", "displacementBarId", "protectedSwingBarId")},
        "refinements": [
            {key: node[key] for key in ("obBarId", "displacementBarId", "protectedSwingBarId")}
            for node in refinements
        ],
        "intermediateLiquidityBarIds": intermediate,
    }
    semantic_hash = canonical_hash(semantic)
    scenario_hash = canonical_hash({"semanticHash": semantic_hash, "frozenAtUtc": utc_text(as_of)})
    if accepted_hashes is not None and scenario_hash in accepted_hashes:
        raise V4ContractError("duplicate scenario hash")
    return {
        "scenarioHash": scenario_hash,
        "semanticHash": semantic_hash,
        "frozenAtUtc": utc_text(as_of),
        "lastReauthorizedAtUtc": utc_text(as_of),
        "direction": direction,
        "scope": scope,
        "dealingRange": {
            "highBarId": range_high["barId"], "lowBarId": range_low["barId"],
            "high": range_high["high"], "low": range_low["low"], "eq": eq,
        },
        "objective": objective,
        "mapProtectedSwing": {
            "barId": map_protected["barId"], "tf": map_protected["tf"],
            "high": map_protected["high"], "low": map_protected["low"],
        },
        "ownerBreakTargetBarId": owner_break_target_id,
        "ownerBreakBarId": owner_break_id,
        "root": root,
        "refinements": refinements,
        "finalChild": final_child,
        "intermediateLiquidityBarIds": intermediate,
        "parentApproachPrepared": False,
        "parentApproachAtUtc": None,
        "childTouchAtUtc": None,
        "childTouchBarId": None,
        "reason": str(payload.get("reason", "")),
    }


def freeze_trigger_watch(
    payload: dict[str, Any],
    market: MarketData,
    as_of: int,
    scenario: dict[str, Any],
    sweep_events: list[dict[str, Any]] | None = None,
    liquidity_candidates: list[dict[str, Any]] | None = None,
    choch_candidates: list[dict[str, Any]] | None = None,
    correction_candidates: list[dict[str, Any]] | None = None,
    choch_break_candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    schema_version = payload.get("schemaVersion")
    if schema_version not in {"4.0.0", "4.2.0", "4.6.0", "4.7.0", "4.8.0"}:
        raise V4ContractError("TRIGGER_WATCH schemaVersion is unsupported")
    direct_ids = schema_version in {"4.7.0", "4.8.0"}
    action = payload.get("action")
    if action in {"REJECT_REACTION", "DATA_ERROR"}:
        if not direct_ids and payload.get("selectedBarIds") != []:
            raise V4ContractError(f"{action} must not contain trigger evidence")
        return None
    if action != "ARM_REACTION":
        raise V4ContractError(f"unsupported TRIGGER_WATCH action: {action}")
    pool = [] if direct_ids else _selection_pool(payload, market, as_of, 7)
    ids = (
        {
            "matureLiquidityBarId": str(payload.get("matureLiquidityBarId")),
            "m5CorrectionSwingBarId": str(payload.get("m5CorrectionSwingBarId")),
            "chochReferenceBarId": str(payload.get("chochReferenceBarId")),
        }
        if direct_ids else {
            "matureLiquidityBarId": _pool_id(
                pool, payload.get("matureLiquidityIndex"), "matureLiquidity"
            ),
            "m5CorrectionSwingBarId": _pool_id(
                pool, payload.get("m5CorrectionSwingIndex"), "m5CorrectionSwing"
            ),
            "chochReferenceBarId": _pool_id(
                pool, payload.get("chochReferenceIndex"), "chochReference"
            ),
        }
    )
    choch_break_value = payload.get(
        "chochBreakBarId" if direct_ids else "chochBreakIndex"
    )
    choch_break_id = (
        str(choch_break_value) if direct_ids and choch_break_value is not None
        else _pool_id(pool, choch_break_value, "chochBreak")
        if choch_break_value is not None else None
    )
    liquidity = market.bar(ids["matureLiquidityBarId"], as_of)
    correction = market.bar(ids["m5CorrectionSwingBarId"], as_of)
    choch = market.bar(ids["chochReferenceBarId"], as_of)
    if liquidity["tf"] != "M1" or choch["tf"] != "M1":
        raise V4ContractError("liquidity and CHoCH reference must be M1")
    if correction["tf"] != "M5":
        raise V4ContractError("correction governing swing must be M5")
    if correction_candidates is not None and correction["barId"] not in {
        str(item.get("barId")) for item in correction_candidates
    }:
        raise V4ContractError("selected M5 correction swing is not a closed candidate")
    frozen_liquidity = None
    if liquidity_candidates is not None:
        frozen_liquidity = next(
            (
                item for item in liquidity_candidates
                if str(item.get("liquidityBarId")) == liquidity["barId"]
            ),
            None,
        )
        if frozen_liquidity is None:
            raise V4ContractError("selected mature liquidity is not a locally qualified candidate")
    if choch_candidates is not None and choch["barId"] not in {
        str(item.get("barId")) for item in choch_candidates
    }:
        raise V4ContractError("selected CHoCH reference is not a closed local pivot candidate")
    source_upgrade = None
    if schema_version == "4.8.0":
        selected_upgrade = payload.get("sourceUpgradeSelectionId")
        if selected_upgrade is not None:
            source_upgrade = next(
                (
                    item for item in scenario.get("sourceUpgradeCandidates", [])
                    if item.get("selectionId") == selected_upgrade
                    and item.get("touchBarId")
                    and not item.get("invalidatedAtUtc")
                ),
                None,
            )
            if source_upgrade is None:
                raise V4ContractError("selected source upgrade is not an active touched candidate")
    touch_time = parse_utc(
        source_upgrade["touchAtUtc"] if source_upgrade else scenario["childTouchAtUtc"]
    )
    direction = scenario["direction"]
    choch_break = market.bar(choch_break_id, as_of) if choch_break_id else None
    if schema_version in {"4.6.0", "4.7.0", "4.8.0"} and choch_break is None:
        raise V4ContractError("TRIGGER_WATCH requires a completed CHoCH break")
    if choch_break is not None:
        if choch_break["tf"] != "M1":
            raise V4ContractError("CHoCH break must be M1")
        if choch_break_candidates is not None and not any(
            str(item.get("referenceBarId")) == choch["barId"]
            and str(item.get("breakBarId")) == choch_break["barId"]
            and str(item.get("m5CorrectionSwingBarId")) == correction["barId"]
            for item in choch_break_candidates
        ):
            raise V4ContractError("selected CHoCH/M5 break chain is not a completed local candidate")
    sweep_excursion = None
    sweep_recovery = None
    if sweep_events is not None:
        matching = [
            event for event in sweep_events
            if event.get("liquidityBarId") == liquidity["barId"]
        ]
        if len(matching) > 1:
            raise V4ContractError("selected mature liquidity has duplicate local sweep events")
        if not matching:
            raise V4ContractError("selected mature liquidity has no completed local sweep event")
        event = matching[0]
        sweep_excursion = market.bar(str(event.get("excursionBarId")), as_of)
        sweep_recovery = market.bar(str(event.get("recoveryBarId")), as_of)
        if sweep_excursion["tf"] != "M1" or sweep_recovery["tf"] != "M1":
            raise V4ContractError("local sweep evidence must use M1 bars")
        if not (
            touch_time < sweep_excursion["available"]
            and liquidity["available"] <= sweep_excursion["time"]
            and sweep_excursion["time"] <= sweep_recovery["time"]
            and sweep_recovery["available"] <= as_of
            and touch_time < choch["available"] <= as_of
        ):
            raise V4ContractError("local sweep/reference evidence violates the child-touch time order")
        if frozen_liquidity is not None:
            qualified_at = parse_utc(str(frozen_liquidity["qualifiedAtUtc"]))
            if qualified_at > sweep_excursion["time"]:
                raise V4ContractError("selected liquidity was not mature before the sweep excursion")
        elapsed = market.between("M1", liquidity["available"], sweep_excursion["time"])
        if len(elapsed) < 2:
            raise V4ContractError("selected liquidity has no completed reaction before its sweep")
        if direction == "LONG" and max(row["high"] for row in elapsed) <= liquidity["high"]:
            raise V4ContractError("sell-side liquidity lacks a completed upward reaction")
        if direction == "SHORT" and min(row["low"] for row in elapsed) >= liquidity["low"]:
            raise V4ContractError("buy-side liquidity lacks a completed downward reaction")
        if direction == "LONG":
            valid_sweep = (
                sweep_excursion["low"] < liquidity["low"]
                and sweep_recovery["close"] > liquidity["low"]
            )
        else:
            valid_sweep = (
                sweep_excursion["high"] > liquidity["high"]
                and sweep_recovery["close"] < liquidity["high"]
            )
        if not valid_sweep:
            raise V4ContractError("local sweep evidence does not pierce and recover the selected liquidity")
    if choch_break is not None:
        if sweep_recovery is None or not (
            sweep_recovery["time"] < choch_break["time"]
            and choch["available"] <= choch_break["time"]
        ):
            raise V4ContractError("CHoCH break is not later than sweep recovery and reference formation")
        valid_break = (
            choch_break["close"] > choch["high"]
            and choch_break["close"] > correction["high"]
            and choch_break["close"] > choch_break["open"]
            if direction == "LONG"
            else choch_break["close"] < choch["low"]
            and choch_break["close"] < correction["low"]
            and choch_break["close"] < choch_break["open"]
        )
        if not valid_break:
            raise V4ContractError("selected CHoCH bar did not body-break both M1 and M5 correction references")
        if correction_candidates is not None and sweep_excursion is not None:
            post_touch_confirmed: list[dict[str, Any]] = []
            for candidate in correction_candidates:
                candidate_bar = market.bar(str(candidate.get("barId")), as_of)
                confirmed_id = candidate.get("confirmedByBarId")
                if confirmed_id is None:
                    continue
                confirmed_bar = market.bar(str(confirmed_id), as_of)
                if (
                    candidate_bar["time"] >= touch_time
                    and confirmed_bar["available"] <= choch_break["time"]
                ):
                    post_touch_confirmed.append(candidate_bar)
            if post_touch_confirmed:
                latest_governing = max(
                    post_touch_confirmed, key=lambda item: int(item["time"])
                )
                latest_broken = (
                    choch_break["close"] > latest_governing["high"]
                    if direction == "LONG"
                    else choch_break["close"] < latest_governing["low"]
                )
                if not latest_broken:
                    raise V4ContractError(
                        "CHoCH break did not transfer the latest confirmed pre-break M5 correction swing"
                    )
    execution_ob = (
        find_execution_ob(market, sweep_excursion["time"], choch_break["available"], direction)
        if sweep_excursion is not None and choch_break is not None else None
    )
    if choch_break is not None and execution_ob is None:
        raise V4ContractError("completed CHoCH has no causal opposite-color execution OB")
    return {
        "frozenAtUtc": utc_text(as_of),
        "matureLiquidity": liquidity,
        "m5CorrectionSwing": correction,
        "chochReference": choch,
        "triggerProtectedSwing": sweep_excursion,
        "sweepExcursion": sweep_excursion,
        "sweep": sweep_excursion,
        "sweepRecovery": sweep_recovery,
        "chochBreak": choch_break,
        "executionOb": execution_ob,
        "sourceUpgrade": source_upgrade,
        "reason": str(payload.get("reason", "")),
    }


def _reaction_liquidity_candidates(
    market: MarketData,
    scenario: dict[str, Any],
    as_of: int,
    lookback_bars: int = 180,
) -> list[dict[str, Any]]:
    """Enumerate neutral M1 liquidity that matured before ``as_of``."""
    rows = market.bars("M1", as_of, max(12, int(lookback_bars)))
    direction = scenario["direction"]
    lineage = [scenario["root"], *scenario["refinements"]]
    context_low = min(float(node["low"]) for node in lineage)
    context_high = max(float(node["high"]) for node in lineage)
    candidates: list[dict[str, Any]] = []
    for index in range(2, len(rows) - 2):
        row = rows[index]
        left = rows[index - 2:index]
        right = rows[index + 1:index + 3]
        if direction == "SHORT":
            pivot = row["high"] > max(item["high"] for item in left) and row["high"] >= max(
                item["high"] for item in right
            )
            level = row["high"]
            inside_context = context_low - market.point <= level <= context_high + market.point
            later = rows[index + 1:]
            unswept = not any(item["high"] > level for item in later)
            reacted = any(item["low"] < row["low"] for item in later)
            side = "BSL"
        else:
            pivot = row["low"] < min(item["low"] for item in left) and row["low"] <= min(
                item["low"] for item in right
            )
            level = row["low"]
            inside_context = context_low - market.point <= level <= context_high + market.point
            later = rows[index + 1:]
            unswept = not any(item["low"] < level for item in later)
            reacted = any(item["high"] > row["high"] for item in later)
            side = "SSL"
        if pivot and inside_context and unswept and reacted:
            candidates.append(
                {
                    "liquidityBarId": row["barId"],
                    "timeUtc": utc_text(row["time"]),
                    "availableAtUtc": utc_text(row["available"]),
                    "qualifiedAtUtc": utc_text(as_of),
                    "side": side,
                    "level": level,
                }
            )
    return candidates[-12:]


def build_reaction_monitor(
    market: MarketData,
    scenario: dict[str, Any],
    as_of: int,
    lookback_bars: int = 180,
) -> dict[str, Any]:
    """Start local waiting; candidates may also mature after the child touch."""
    candidates = _reaction_liquidity_candidates(
        market, scenario, as_of, lookback_bars
    )
    return {
        "armedAtUtc": utc_text(as_of),
        "childTouchBarId": scenario["childTouchBarId"],
        "candidates": candidates,
        "excursions": {},
        "completedLiquidityBarIds": [],
        "sweepEvents": [],
    }


def refresh_reaction_monitor(
    market: MarketData,
    scenario: dict[str, Any],
    monitor: dict[str, Any],
    as_of: int,
    lookback_bars: int = 180,
) -> dict[str, Any]:
    """Add newly matured candidates without reconsidering completed physical events."""
    existing = {
        str(item["liquidityBarId"]): item
        for item in monitor.get("candidates", [])
    }
    completed = set(str(item) for item in monitor.get("completedLiquidityBarIds", []))
    for candidate in _reaction_liquidity_candidates(
        market, scenario, as_of, lookback_bars
    ):
        liquidity_id = str(candidate["liquidityBarId"])
        if liquidity_id not in completed and liquidity_id not in existing:
            existing[liquidity_id] = candidate
    ordered = sorted(
        existing.values(),
        key=lambda item: split_bar_id(str(item["liquidityBarId"]))[1],
    )[-12:]
    return {**monitor, "candidates": ordered}


def advance_reaction_monitor(
    monitor: dict[str, Any],
    row: dict[str, Any],
    direction: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Advance only price-event detection; semantic candidate selection remains an AI decision."""
    if row["available"] <= parse_utc(monitor["armedAtUtc"]):
        return monitor, []
    excursions = dict(monitor.get("excursions", {}))
    completed = set(monitor.get("completedLiquidityBarIds", []))
    stored_events = list(monitor.get("sweepEvents", []))
    events: list[dict[str, Any]] = []
    for candidate in monitor.get("candidates", []):
        liquidity_id = str(candidate["liquidityBarId"])
        level = float(candidate["level"])
        pierced = row["low"] < level if direction == "LONG" else row["high"] > level
        if liquidity_id in completed:
            previous_event = next(
                (
                    item for item in stored_events
                    if str(item["liquidityBarId"]) == liquidity_id
                ),
                None,
            )
            previous_recovery_time = (
                split_bar_id(str(previous_event["recoveryBarId"]))[1]
                if previous_event else None
            )
            same_excursion_continuation = (
                pierced
                and previous_recovery_time is not None
                and row["time"] == previous_recovery_time + TIMEFRAME_SECONDS["M1"]
            )
            if not same_excursion_continuation:
                continue
            completed.discard(liquidity_id)
            stored_events = [
                item for item in stored_events
                if str(item["liquidityBarId"]) != liquidity_id
            ]
            # A recovery followed immediately by another pierce is still one
            # physical sweep excursion. Preserve its deepest/highest extreme
            # instead of resetting the SL anchor to the newer, shallower bar.
            if liquidity_id not in excursions:
                raise V4ContractError(
                    "completed sweep continuation lost its physical excursion"
                )
        excursion = excursions.get(liquidity_id)
        if excursion is None and pierced:
            excursion = row
        elif excursion is not None:
            extends = row["low"] < excursion["low"] if direction == "LONG" else row["high"] > excursion["high"]
            if extends:
                excursion = row
        if excursion is not None:
            excursions[liquidity_id] = excursion
            recovered = row["close"] > level if direction == "LONG" else row["close"] < level
            if recovered:
                events.append(
                    {
                        "liquidityBarId": liquidity_id,
                        "side": candidate["side"],
                        "level": level,
                        "excursionBarId": excursion["barId"],
                        "recoveryBarId": row["barId"],
                        "detectedAtUtc": utc_text(row["available"]),
                    }
                )
                completed.add(liquidity_id)
    known_event_ids = {
        (str(item["liquidityBarId"]), str(item["excursionBarId"]), str(item["recoveryBarId"]))
        for item in stored_events
    }
    stored_events.extend(
        item for item in events
        if (
            str(item["liquidityBarId"]),
            str(item["excursionBarId"]),
            str(item["recoveryBarId"]),
        ) not in known_event_ids
    )
    return {
        **monitor,
        "excursions": excursions,
        "completedLiquidityBarIds": sorted(completed),
        "sweepEvents": stored_events,
    }, events


def outermost_completed_sweep_events(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collapse nested pools pierced by one physical excursion to its outer edge."""
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for event in events:
        side = str(event["side"])
        key = (
            str(event["excursionBarId"]),
            str(event["recoveryBarId"]),
            side,
        )
        current = grouped.get(key)
        if current is None:
            grouped[key] = event
            continue
        current_level = float(current["level"])
        candidate_level = float(event["level"])
        is_outer = (
            candidate_level < current_level
            if side == "SSL"
            else candidate_level > current_level
        )
        if is_outer:
            grouped[key] = event
    return sorted(
        grouped.values(),
        key=lambda item: (
            split_bar_id(str(item["recoveryBarId"]))[1],
            split_bar_id(str(item["liquidityBarId"]))[1],
        ),
    )


def mechanical_choch_reference_candidates(
    market: MarketData,
    scenario: dict[str, Any],
    as_of: int,
) -> list[dict[str, Any]]:
    """Return broad, closed M1 pivot candidates; the model still chooses meaning."""
    touch_time = parse_utc(scenario["childTouchAtUtc"])
    rows = market.between("M1", touch_time, as_of)
    direction = scenario["direction"]
    output: list[dict[str, Any]] = []
    for index in range(1, len(rows) - 1):
        previous, row, following = rows[index - 1], rows[index], rows[index + 1]
        if direction == "SHORT":
            pivot = row["low"] < previous["low"] and row["low"] <= following["low"]
            reacted = following["high"] > row["high"]
            side = "LIVE_LOW"
            level = row["low"]
        else:
            pivot = row["high"] > previous["high"] and row["high"] >= following["high"]
            reacted = following["low"] < row["low"]
            side = "LIVE_HIGH"
            level = row["high"]
        if pivot and reacted:
            output.append(
                {
                    "barId": row["barId"],
                    "timeUtc": utc_text(row["time"]),
                    "side": side,
                    "level": level,
                    "confirmedByBarId": following["barId"],
                }
            )
    return output[-12:]


def mechanical_m5_correction_swing_candidates(
    market: MarketData,
    scenario: dict[str, Any],
    as_of: int,
) -> list[dict[str, Any]]:
    """Return broad confirmed M5 correction pivots; semantic ownership remains with the model."""
    rows = market.bars("M5", as_of, TRIGGER_LIMITS["M5"])
    frozen_at = parse_utc(str(scenario.get("frozenAtUtc") or scenario["childTouchAtUtc"]))
    rows = [row for row in rows if row["available"] >= frozen_at]
    direction = scenario["direction"]
    output: list[dict[str, Any]] = []
    for index in range(1, len(rows) - 1):
        previous, row, following = rows[index - 1], rows[index], rows[index + 1]
        if direction == "LONG":
            pivot = row["high"] > previous["high"] and row["high"] >= following["high"]
            reacted = following["low"] < row["low"]
            side, level = "CORRECTION_HIGH", row["high"]
        else:
            pivot = row["low"] < previous["low"] and row["low"] <= following["low"]
            reacted = following["high"] > row["high"]
            side, level = "CORRECTION_LOW", row["low"]
        if pivot and reacted:
            output.append(
                {
                    "barId": row["barId"],
                    "timeUtc": utc_text(row["time"]),
                    "side": side,
                    "level": level,
                    "confirmedByBarId": following["barId"],
                }
            )
    return output[-12:]


def mechanical_choch_break_candidates(
    market: MarketData,
    scenario: dict[str, Any],
    as_of: int,
    sweep_events: list[dict[str, Any]],
    choch_candidates: list[dict[str, Any]],
    correction_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Wake semantics only after one body close transfers both M1 and M5 correction structure."""
    direction = scenario["direction"]
    output: list[dict[str, Any]] = []
    for sweep in sweep_events:
        recovery = market.bar(str(sweep["recoveryBarId"]), as_of)
        for reference_meta in choch_candidates:
            reference = market.bar(str(reference_meta["barId"]), as_of)
            for correction_meta in correction_candidates:
                correction = market.bar(str(correction_meta["barId"]), as_of)
                start = max(recovery["available"], reference["available"], correction["available"])
                for row in market.between("M1", start, as_of):
                    if row["time"] <= recovery["time"]:
                        continue
                    broke = (
                        row["close"] > reference["high"]
                        and row["close"] > correction["high"]
                        and row["close"] > row["open"]
                        if direction == "LONG"
                        else row["close"] < reference["low"]
                        and row["close"] < correction["low"]
                        and row["close"] < row["open"]
                    )
                    if broke:
                        output.append(
                            {
                                "liquidityBarId": str(sweep["liquidityBarId"]),
                                "sweepExcursionBarId": str(sweep["excursionBarId"]),
                                "sweepRecoveryBarId": str(sweep["recoveryBarId"]),
                                "referenceBarId": reference["barId"],
                                "m5CorrectionSwingBarId": correction["barId"],
                                "breakBarId": row["barId"],
                                "detectedAtUtc": utc_text(row["available"]),
                            }
                        )
                        break
    unique: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for item in output:
        key = (
            item["liquidityBarId"], item["referenceBarId"],
            item["m5CorrectionSwingBarId"], item["breakBarId"],
        )
        unique[key] = item
    return list(unique.values())[-24:]


def zone_touched(row: dict[str, Any], zone: dict[str, Any]) -> bool:
    return row["high"] >= zone["low"] and row["low"] <= zone["high"]


def zone_distal_crossed(row: dict[str, Any], zone: dict[str, Any], direction: str, body: bool) -> bool:
    value = row["close"] if body else (row["low"] if direction == "LONG" else row["high"])
    return value <= zone["distal"] if direction == "LONG" else value >= zone["distal"]


def local_scenario_cancel_reason(
    market: MarketData,
    scenario: dict[str, Any],
    row: dict[str, Any],
    trigger_watch: dict[str, Any] | None = None,
) -> str | None:
    direction = scenario["direction"]
    objective = scenario["objective"]["price"]
    if direction == "LONG" and row["high"] >= objective:
        return "OBJECTIVE_REACHED_BEFORE_FILL"
    if direction == "SHORT" and row["low"] <= objective:
        return "OBJECTIVE_REACHED_BEFORE_FILL"

    for node in [scenario["root"], *scenario["refinements"]]:
        closed = market.closed_bar_at(node["tf"], row["available"])
        if closed and zone_distal_crossed(closed, node, direction, body=True):
            return f"SOURCE_BODY_INVALIDATED:{node['obBarId']}"

    # An INTERNAL_ROTATION trades inside the external owner's range. The external
    # protected swing is context, not a direction-mirrored stop for that rotation.
    if scenario["scope"] != "INTERNAL_ROTATION":
        map_swing = scenario["mapProtectedSwing"]
        closed = market.closed_bar_at(map_swing["tf"], row["available"])
        if closed:
            if direction == "LONG" and closed["close"] < map_swing["low"]:
                return "OPPOSING_OWNER_CONFIRMED"
            if direction == "SHORT" and closed["close"] > map_swing["high"]:
                return "OPPOSING_OWNER_CONFIRMED"

    if trigger_watch and trigger_watch.get("triggerProtectedSwing"):
        protected = trigger_watch["triggerProtectedSwing"]
        if direction == "LONG" and row["close"] < protected["low"]:
            return "TRIGGER_PROTECTED_SWING_BROKEN"
        if direction == "SHORT" and row["close"] > protected["high"]:
            return "TRIGGER_PROTECTED_SWING_BROKEN"
    return None


def should_reauthorize(row: dict[str, Any]) -> bool:
    return row["available"] % TIMEFRAME_SECONDS["M15"] == 0


def parent_zone(scenario: dict[str, Any]) -> dict[str, Any]:
    refinements = scenario["refinements"]
    return refinements[-2] if len(refinements) > 1 else scenario["root"]


def find_execution_ob(
    market: MarketData,
    start_time: int,
    end_time: int,
    direction: str,
) -> dict[str, Any] | None:
    rows = market.between("M1", start_time, end_time)
    for row in reversed(rows[:-1] if rows else []):
        if _directional_ob(row, direction):
            return row
    return None


def advance_trigger_watch(
    market: MarketData,
    scenario: dict[str, Any],
    watch: dict[str, Any],
    row: dict[str, Any],
    broker_stops_level: float,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    direction = scenario["direction"]
    touch_time = parse_utc(scenario["childTouchAtUtc"])
    if row["available"] <= touch_time:
        return watch, None
    liquidity = watch["matureLiquidity"]
    if watch["sweep"] is None:
        excursion = watch.get("sweepExcursion")
        pierced = (
            row["low"] < liquidity["low"] if direction == "LONG"
            else row["high"] > liquidity["high"]
        )
        if excursion is None and pierced:
            excursion = row
            watch = {**watch, "sweepExcursion": row, "triggerProtectedSwing": row}
        elif excursion is not None:
            extends = (
                row["low"] < excursion["low"] if direction == "LONG"
                else row["high"] > excursion["high"]
            )
            if extends:
                excursion = row
                watch = {**watch, "sweepExcursion": row, "triggerProtectedSwing": row}
        recovered = (
            row["close"] > liquidity["low"] if direction == "LONG"
            else row["close"] < liquidity["high"]
        )
        if excursion is not None and recovered:
            watch = {
                **watch,
                "sweep": excursion,
                "sweepRecovery": row,
                "triggerProtectedSwing": excursion,
            }
        return watch, None

    recovery = watch.get("sweepRecovery") or watch["sweep"]
    if row["time"] <= recovery["time"]:
        return watch, None
    reference = watch["chochReference"]
    correction = watch["m5CorrectionSwing"]
    broke = (
        row["close"] > reference["high"]
        and row["close"] > correction["high"]
        and row["close"] > row["open"]
        if direction == "LONG"
        else row["close"] < reference["low"]
        and row["close"] < correction["low"]
        and row["close"] < row["open"]
    )
    if not broke:
        return watch, None
    execution = find_execution_ob(market, watch["sweep"]["time"], row["available"], direction)
    if execution is None:
        raise V4ContractError("meaningful CHoCH has no causal opposite-color execution OB")
    watch = {**watch, "chochBreak": row, "executionOb": execution}
    order = build_order(market, scenario, watch, execution, row, broker_stops_level)
    return watch, order


def build_order(
    market: MarketData,
    scenario: dict[str, Any],
    watch: dict[str, Any],
    execution: dict[str, Any],
    decision_bar: dict[str, Any],
    broker_stops_level: float,
) -> dict[str, Any]:
    direction = scenario["direction"]
    entry = execution["high"] if direction == "LONG" else execution["low"]
    sweep = watch["sweep"]
    protected = watch["triggerProtectedSwing"]
    child = scenario["finalChild"]
    spread = decision_bar["spreadPoints"] * market.point
    buffer = max(market.point, spread, float(broker_stops_level))
    if direction == "LONG":
        structural = min(execution["low"], child["distal"], protected["low"], sweep["low"])
        stop = structural - buffer
        marketable = entry >= decision_bar["close"] + spread
    else:
        structural = max(execution["high"], child["distal"], protected["high"], sweep["high"])
        stop = structural + buffer
        marketable = entry <= decision_bar["close"]
    target = scenario["objective"]["price"]
    if direction == "LONG" and not stop < entry < target:
        raise V4ContractError("long order geometry is invalid")
    if direction == "SHORT" and not target < entry < stop:
        raise V4ContractError("short order geometry is invalid")
    if marketable:
        raise V4ContractError("execution OB first retest already passed at order creation")
    order_id = canonical_hash(
        {
            "scenarioHash": scenario["scenarioHash"],
            "execution": execution["barId"],
            "entry": entry,
            "stop": stop,
            "target": target,
        }
    )[:20]
    return {
        "orderId": order_id,
        "scenarioHash": scenario["scenarioHash"],
        "model": "HTF_OB_REACTION",
        "direction": direction,
        "createdAtUtc": utc_text(decision_bar["available"]),
        "lastReauthorizedAtUtc": scenario["lastReauthorizedAtUtc"],
        "entry": entry,
        "stop": stop,
        "target": target,
        "executionObBarId": execution["barId"],
        "executionZone": {"low": execution["low"], "high": execution["high"]},
        "structuralInvalidation": structural,
        "spreadAtCreation": spread,
        "buffer": buffer,
        "replacementUsed": False,
        "originalOrderId": None,
    }


def delivery_replacement(
    market: MarketData,
    scenario: dict[str, Any],
    watch: dict[str, Any],
    order: dict[str, Any],
    row: dict[str, Any],
    broker_stops_level: float,
) -> dict[str, Any] | None:
    if order.get("replacementUsed"):
        return None
    index = row["index"]
    if index < 2:
        return None
    first = market.m1_row(index - 2)
    direction = scenario["direction"]
    bullish_gap = row["low"] > first["high"]
    bearish_gap = row["high"] < first["low"]
    if (direction == "LONG" and not bullish_gap) or (direction == "SHORT" and not bearish_gap):
        return None
    reference = watch["chochReference"]
    delivered = row["close"] > reference["high"] if direction == "LONG" else row["close"] < reference["low"]
    if not delivered:
        return None
    entry = row["low"] if direction == "LONG" else row["high"]
    spread = row["spreadPoints"] * market.point
    buffer = max(market.point, spread, float(broker_stops_level))
    execution = watch["executionOb"]
    protected = watch["triggerProtectedSwing"]
    child = scenario["finalChild"]
    if direction == "LONG":
        structural = min(execution["low"], protected["low"], child["distal"])
        stop = structural - buffer
    else:
        structural = max(execution["high"], protected["high"], child["distal"])
        stop = structural + buffer
    target = scenario["objective"]["price"]
    if direction == "LONG" and not stop < entry < target:
        return None
    if direction == "SHORT" and not target < entry < stop:
        return None
    return {
        **order,
        "orderId": canonical_hash({"original": order["orderId"], "fvg": row["barId"]})[:20],
        "model": "DELIVERY_FVG_REPLACEMENT",
        "createdAtUtc": utc_text(row["available"]),
        "entry": entry,
        "stop": stop,
        "executionZone": {
            "low": first["high"] if direction == "LONG" else row["high"],
            "high": row["low"] if direction == "LONG" else first["low"],
        },
        "structuralInvalidation": structural,
        "spreadAtCreation": spread,
        "buffer": buffer,
        "replacementUsed": True,
        "originalOrderId": order["orderId"],
        "deliveryFvgBarId": row["barId"],
    }


def advance_pending(
    market: MarketData,
    order: dict[str, Any],
    row: dict[str, Any],
) -> tuple[str, dict[str, Any] | None]:
    direction = order["direction"]
    spread = row["spreadPoints"] * market.point
    target_reached = row["high"] >= order["target"] if direction == "LONG" else row["low"] <= order["target"]
    if target_reached:
        return "CANCELED_OBJECTIVE_FIRST", None
    entry_hit = row["low"] + spread <= order["entry"] if direction == "LONG" else row["high"] >= order["entry"]
    if not entry_hit:
        return "WAIT", None
    stop_crossed = row["low"] <= order["stop"] if direction == "LONG" else row["high"] + spread >= order["stop"]
    if stop_crossed:
        return "CANCELED_THROUGH_DELIVERY", None
    if order.get("model") != "DELIVERY_FVG_REPLACEMENT":
        zone = order["executionZone"]
        poi_consumed = row["low"] <= zone["low"] if direction == "LONG" else row["high"] >= zone["high"]
        if poi_consumed:
            return "CANCELED_EXECUTION_POI_CONSUMED", None
    position = {
        "orderId": order["orderId"],
        "scenarioHash": order["scenarioHash"],
        "direction": direction,
        "model": order["model"],
        "entryAtUtc": utc_text(row["available"]),
        "entry": order["entry"],
        "stop": order["stop"],
        "target": order["target"],
        "risk": abs(order["entry"] - order["stop"]),
        "entryBarId": row["barId"],
    }
    return "FILLED", position


def advance_position(
    market: MarketData,
    position: dict[str, Any],
    row: dict[str, Any],
) -> dict[str, Any] | None:
    direction = position["direction"]
    spread = row["spreadPoints"] * market.point
    if direction == "LONG":
        hit_stop = row["low"] <= position["stop"]
        hit_target = row["high"] >= position["target"]
    else:
        hit_stop = row["high"] + spread >= position["stop"]
        hit_target = row["low"] + spread <= position["target"]
    if not hit_stop and not hit_target:
        return None
    outcome = "SL" if hit_stop else "TP"
    exit_price = position["stop"] if hit_stop else position["target"]
    sign = 1.0 if direction == "LONG" else -1.0
    result_r = sign * (exit_price - position["entry"]) / position["risk"]
    return {
        **position,
        "exitAtUtc": utc_text(row["available"]),
        "exitBarId": row["barId"],
        "exit": exit_price,
        "outcome": outcome,
        "resultR": -1.0 if hit_stop else result_r,
        "intrabarAmbiguous": bool(hit_stop and hit_target),
    }


def new_runtime(start_index: int) -> dict[str, Any]:
    return {
        "pipelineVersion": PIPELINE_VERSION,
        "state": "FLAT",
        "cursor": int(start_index),
        "lastPlanH1Available": None,
        "lastPlanRequestAtUtc": None,
        "lastPlanRequestH1Bucket": None,
        "lastFlatPlanFingerprint": None,
        "evaluatedFlatPlanFingerprints": [],
        "evaluatedPlanOpportunityKeys": [],
        "flatPlanCandidates": [],
        "lastPlanCandidateRefreshM15": None,
        "flatSinceAtUtc": None,
        "seenMapOpportunityIds": [],
        "seenPlanOpportunityIds": [],
        "externalMapAuthority": None,
        "scenario": None,
        "parkedScenarios": [],
        "reactionMonitor": None,
        "triggerWatch": None,
        "order": None,
        "position": None,
        "acceptedScenarioHashes": [],
        "apiCallsByMap": {},
        "apiCallsByScenario": {},
        "closedTrades": 0,
        "canceledScenarios": 0,
    }


def reset_terminal(runtime: dict[str, Any], terminal: str) -> dict[str, Any]:
    if terminal not in {"CLOSED", "CANCELED"}:
        raise V4ContractError("terminal reset requires CLOSED or CANCELED")
    return {
        **runtime,
        "state": "FLAT",
        "scenario": None,
        "reactionMonitor": None,
        "triggerWatch": None,
        "order": None,
        "position": None,
        "flatSinceAtUtc": runtime.get("terminalAtUtc"),
        "closedTrades": runtime["closedTrades"] + (1 if terminal == "CLOSED" else 0),
        "canceledScenarios": runtime["canceledScenarios"] + (1 if terminal == "CANCELED" else 0),
    }


def assert_runtime_invariants(runtime: dict[str, Any]) -> None:
    state = runtime.get("state")
    if state not in STATES:
        raise AssertionError(f"invalid V4 state: {state}")
    scenario = runtime.get("scenario")
    monitor = runtime.get("reactionMonitor")
    watch = runtime.get("triggerWatch")
    order = runtime.get("order")
    position = runtime.get("position")
    authority = runtime.get("externalMapAuthority")
    if authority is not None:
        if authority.get("direction") not in {"LONG", "SHORT"}:
            raise AssertionError("external map authority has an invalid direction")
        if authority.get("status", "ACTIVE") not in {
            "ACTIVE", "OBJECTIVE_REACHED", "BROKEN"
        }:
            raise AssertionError("external map authority has an invalid status")
        if not authority.get("dealingRange") or not authority.get("protectedSwing"):
            raise AssertionError("external map authority is incomplete")
    if state == "FLAT" and any(item is not None for item in (scenario, monitor, watch, order, position)):
        raise AssertionError("FLAT cannot retain an active scenario, monitor, watch, order, or position")
    if state in {"MAPPED", "PLANNED", "REACTION_MONITOR", "TRIGGER_WATCH", "PENDING", "FILLED"} and scenario is None:
        raise AssertionError(f"{state} requires an active scenario")
    if state == "MAPPED" and scenario is not None and scenario.get("finalChild") is not None:
        raise AssertionError("MAPPED cannot contain a frozen final child")
    if state in {"PLANNED", "REACTION_MONITOR", "TRIGGER_WATCH", "PENDING", "FILLED"} and scenario is not None:
        if scenario.get("finalChild") is None:
            raise AssertionError(f"{state} requires a frozen final child")
    if state == "REACTION_MONITOR" and monitor is None:
        raise AssertionError("REACTION_MONITOR requires local reaction evidence state")
    if state in {"TRIGGER_WATCH", "PENDING", "FILLED"} and watch is None:
        raise AssertionError(f"{state} requires frozen trigger semantics")
    if state == "PENDING" and (order is None or position is not None):
        raise AssertionError("PENDING requires exactly one order")
    if state == "FILLED" and (position is None or order is None):
        raise AssertionError("FILLED requires one frozen order and one position")
    hashes = runtime.get("acceptedScenarioHashes", [])
    if len(hashes) != len(set(hashes)):
        raise AssertionError("duplicate scenario hash was accepted")
    parked = runtime.get("parkedScenarios", [])
    if not isinstance(parked, list):
        raise AssertionError("parkedScenarios must be a list")
    if any(
        not isinstance(item, dict)
        or not isinstance(item.get("scenario"), dict)
        or not item["scenario"].get("scenarioHash")
        or not item.get("parkedAtUtc")
        for item in parked
    ):
        raise AssertionError("parked scenario record is incomplete")
    parked_hashes = [
        str(item.get("scenario", {}).get("scenarioHash")) for item in parked
    ]
    if len(parked_hashes) != len(set(parked_hashes)):
        raise AssertionError("duplicate parked scenario hash")
    if any(item.get("state") != "PLANNED" for item in parked):
        raise AssertionError("only pre-order scenarios may be parked")
    if scenario is not None and str(scenario.get("scenarioHash")) in set(parked_hashes):
        raise AssertionError("active scenario cannot also be parked")
    for scenario_hash, count in runtime.get("apiCallsByScenario", {}).items():
        if int(count) > 2:
            raise AssertionError(f"scenario {scenario_hash} exceeded two API calls")
    for map_hash, count in runtime.get("apiCallsByMap", {}).items():
        if int(count) > 1:
            raise AssertionError(f"map {map_hash} exceeded one API call")
