from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import bisect
import heapq
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PIPELINE_VERSION = "4.51-ground-truth-v2"
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
LIQUIDITY_LIMITS = {"H1": 120, "M30": 160, "M15": 256, "M5": 384}
LIQUIDITY_RECENT_EVIDENCE = {"H1": 8, "M30": 12, "M15": 16, "M5": 24}
LIQUIDITY_SWING_EVIDENCE = {"H1": 14, "M30": 18, "M15": 24, "M5": 32}
LONG_TERM_H1_DAYS = 30
MAX_LONG_TERM_H1_FALLBACK_OBJECTIVES = 2
LONG_HISTORY_START_UTC = 1701388800  # 2023-12-01T00:00:00Z
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


_H1_LIQUIDITY_SWING_CACHE: dict[
    tuple[object, int, int], list[dict[str, Any]]
] = {}
_BAR_ROW_CACHE: dict[tuple[object, str, int], dict[str, Any]] = {}
_M1_TIME_CACHE: dict[tuple[object, int], np.ndarray] = {}
_ROOT_EPISODE_CACHE: dict[
    tuple[object, str], list[tuple[int, int, int, str]]
] = {}
_ROOT_AVAILABILITY_INDEX_CACHE: dict[tuple[object, str], dict[str, Any]] = {}
_PROTECTED_REACTION_CACHE: dict[tuple[object, str, str], dict[str, Any]] = {}
_LIQUIDITY_EVENT_CACHE: dict[
    tuple[object, str], list[dict[str, Any]]
] = {}
_LIQUIDITY_MATURITY_INDEX_CACHE: dict[tuple[object, str], dict[str, Any]] = {}
_LIQUIDITY_RESOLUTION_CACHE: dict[
    tuple[object, str, str, int], tuple[int | None, str | None]
] = {}
_CONFIRMED_LIQUIDITY_ASOF_CACHE: dict[
    tuple[object, int, bool], list[dict[str, Any]]
] = {}
_LIVE_LIQUIDITY_QUERY_CACHE: dict[tuple[Any, ...], list[dict[str, Any]]] = {}


def _m1_times(market: MarketData) -> np.ndarray:
    key = (market.cache_token, len(market.rates))
    cached = _M1_TIME_CACHE.get(key)
    if cached is None:
        cached = np.ascontiguousarray(market.rates["time"], dtype=np.int64)
        _M1_TIME_CACHE[key] = cached
        if len(_M1_TIME_CACHE) > 16:
            del _M1_TIME_CACHE[next(iter(_M1_TIME_CACHE))]
    return cached


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
    cache_token: object = field(default_factory=object, compare=False, repr=False)

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
        cache_key = (self.cache_token, timeframe, timestamp)
        row = _BAR_ROW_CACHE.get(cache_key)
        if row is None:
            position = int(np.searchsorted(series.time, timestamp, side="left"))
            if position >= len(series.time) or int(series.time[position]) != timestamp:
                raise V4ContractError(f"barId is not present in the dataset: {selected_id}")
            row = {
                "barId": selected_id,
                "tf": timeframe,
                "time": int(series.time[position]),
                "available": int(series.available_time[position]),
                "open": float(series.open[position]),
                "high": float(series.high[position]),
                "low": float(series.low[position]),
                "close": float(series.close[position]),
                "spreadPoints": float(series.spread_points[position]),
                "index": position,
            }
            _BAR_ROW_CACHE[cache_key] = row
            if len(_BAR_ROW_CACHE) > 250_000:
                _BAR_ROW_CACHE.clear()
                _BAR_ROW_CACHE[cache_key] = row
        available = int(row["available"])
        if as_of is not None and available > as_of:
            raise V4ContractError(f"future barId is not available at as-of: {selected_id}")
        return row

    def bars(self, timeframe: str, as_of: int, limit: int) -> list[dict[str, Any]]:
        series = self.frames[timeframe]
        right = int(np.searchsorted(series.available_time, as_of, side="right"))
        if right <= 0:
            return []
        left = max(0, right - max(1, int(limit)))
        selected = range(left, right)
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
        return int(np.searchsorted(_m1_times(self), timestamp, side="left"))

    def closed_bar_at(self, timeframe: str, available_at: int) -> dict[str, Any] | None:
        series = self.frames[timeframe]
        position = int(np.searchsorted(series.available_time, available_at, side="left"))
        if position >= len(series.available_time) or int(series.available_time[position]) != available_at:
            return None
        return self.bar(bar_id(timeframe, int(series.time[position])), available_at)

    def between(self, timeframe: str, start: int, end: int) -> list[dict[str, Any]]:
        series = self.frames[timeframe]
        left = int(np.searchsorted(series.time, start, side="left"))
        right = int(np.searchsorted(series.available_time, end, side="right"))
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
            for index in range(left, max(left, right))
        ]


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
    scenario_option_ids = list(dict.fromkeys(
        str(option["scenarioSelectionId"])
        for family in families
        for option in family.get("scenarioOptions", [])
    )) or ["NO_SCENARIO_OPTION"]

    family_ids = [str(item["familyId"]) for item in families] or ["NO_FAMILY"]
    decision = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "familyId", "action", "scenarioSelectionId", "semanticAudit", "reason",
        ],
        "properties": {
            "familyId": {"type": "string", "enum": family_ids},
            "action": {"type": "string", "enum": ["PLAN", "NO_PLAN", "DATA_ERROR"]},
            "scenarioSelectionId": _nullable_enum(scenario_option_ids),
            "semanticAudit": {
                "type": "object",
                "additionalProperties": False,
                "required": list(PLAN_SEMANTIC_AUDIT_KEYS),
                "properties": {
                    key: {
                        "type": "string",
                        "enum": ["PASS", "FAIL", "UNRESOLVED"],
                    }
                    for key in PLAN_SEMANTIC_AUDIT_KEYS
                },
            },
            "reason": {"type": "string"},
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["schemaVersion", "decisions"],
        "properties": {
            "schemaVersion": {"type": "string", "enum": ["5.0.0"]},
            "decisions": {
                "type": "array",
                "minItems": len(families),
                "maxItems": len(families),
                "items": decision,
            },
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


def delivery_review_schema(packet: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(packet["candidate"]["shadowId"])
    execution_model = str(
        packet["candidate"].get("executionModel", "DELIVERY_FVG_REPLACEMENT")
    )
    approve_action = (
        "APPROVE_ADDON"
        if execution_model == "DELIVERY_FVG_ADDON"
        else "APPROVE_REPLACEMENT"
    )
    verdict = {"type": "string", "enum": ["PASS", "FAIL", "UNRESOLVED"]}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schemaVersion", "candidateId", "action", "sourceEpisodeContinuity",
            "ownerObjectiveContinuity", "meaningfulStructureTransfer",
            "causalFvgAndOb", "firstRetestEligibility", "reason",
        ],
        "properties": {
            "schemaVersion": {"type": "string", "enum": ["4.61.0"]},
            "candidateId": {"type": "string", "enum": [candidate_id]},
            "action": {
                "type": "string",
                "enum": [approve_action, "REJECT_CANDIDATE", "DATA_ERROR"],
            },
            "sourceEpisodeContinuity": verdict,
            "ownerObjectiveContinuity": verdict,
            "meaningfulStructureTransfer": verdict,
            "causalFvgAndOb": verdict,
            "firstRetestEligibility": verdict,
            "reason": {"type": "string"},
        },
    }


def mechanical_root_candidates(
    market: MarketData,
    as_of: int,
    *,
    maximum: int | None = None,
    timeframe_limits: dict[str, int] | None = None,
    active_only: bool = False,
    focus_root_bar_ids: set[str] | None = None,
    root_time_ranges: list[tuple[int, int]] | None = None,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for timeframe in (timeframe_limits or MAP_LIMITS):
        series = market.frames[timeframe]
        cache_key = (market.cache_token, timeframe)
        episodes = _ROOT_EPISODE_CACHE.get(cache_key)
        if episodes is None:
            episodes = []
            for root_index in range(len(series.time) - 1):
                root_open = float(series.open[root_index])
                root_close = float(series.close[root_index])
                if root_close == root_open:
                    continue
                for displacement_index in range(root_index + 1, len(series.time)):
                    item_open = float(series.open[displacement_index])
                    item_close = float(series.close[displacement_index])
                    if root_close > root_open:
                        if item_close > item_open:
                            break
                        if item_close < float(series.low[root_index]):
                            episode_end = displacement_index
                            for extension_index in range(displacement_index + 1, len(series.time)):
                                if float(series.close[extension_index]) >= float(series.open[extension_index]):
                                    break
                                episode_end = extension_index
                            episodes.append((root_index, displacement_index, episode_end, "SHORT"))
                            break
                    else:
                        if item_close < item_open:
                            break
                        if item_close > float(series.high[root_index]):
                            episode_end = displacement_index
                            for extension_index in range(displacement_index + 1, len(series.time)):
                                if float(series.close[extension_index]) <= float(series.open[extension_index]):
                                    break
                                episode_end = extension_index
                            episodes.append((root_index, displacement_index, episode_end, "LONG"))
                            break
            _ROOT_EPISODE_CACHE[cache_key] = episodes
        right = int(np.searchsorted(series.available_time, as_of, side="right"))
        visible = [item for item in episodes if item[1] < right]
        if right:
            suffix_high = np.maximum.accumulate(series.high[:right][::-1])[::-1]
            suffix_low = np.minimum.accumulate(series.low[:right][::-1])[::-1]
            suffix_close_high = np.maximum.accumulate(series.close[:right][::-1])[::-1]
            suffix_close_low = np.minimum.accumulate(series.close[:right][::-1])[::-1]
        # Explicit timeframe limits are packet-view limits, never discovery
        # limits. The permanent event ledger remains complete.
        for root_index, displacement_index, episode_end_index, direction in visible:
            root_time = int(series.time[root_index])
            if root_time_ranges is not None and not any(
                int(start) <= root_time < int(end)
                for start, end in root_time_ranges
            ):
                continue
            candidate_root_bar_id = bar_id(
                timeframe, root_time
            )
            if (
                focus_root_bar_ids is not None
                and candidate_root_bar_id not in focus_root_bar_ids
            ):
                continue
            root = market.bar(
                candidate_root_bar_id, as_of
            )
            displacement = market.bar(
                bar_id(timeframe, int(series.time[displacement_index])), as_of
            )
            later_right = right
            later_start = displacement_index + 1
            has_later = later_start < later_right
            if direction == "SHORT":
                later_body_invalidated = bool(
                    has_later and suffix_close_high[later_start] > root["high"]
                )
                later_distal_touched = bool(
                    has_later and suffix_high[later_start] >= root["high"]
                )
                later_proximal_touched = bool(
                    has_later and suffix_high[later_start] >= root["low"]
                )
            else:
                later_body_invalidated = bool(
                    has_later and suffix_close_low[later_start] < root["low"]
                )
                later_distal_touched = bool(
                    has_later and suffix_low[later_start] <= root["low"]
                )
                later_proximal_touched = bool(
                    has_later and suffix_low[later_start] <= root["high"]
                )
            if active_only and (
                later_body_invalidated
                or later_distal_touched
            ):
                continue
            visible_episode_end = min(int(episode_end_index), right - 1)
            episode_bar_ids = [
                bar_id(timeframe, int(series.time[index]))
                for index in range(root_index, visible_episode_end + 1)
            ]
            candidates.append(
                {
                    "direction": direction,
                    "timeframe": timeframe,
                    "rootBarId": root["barId"],
                    "rootTimeUtc": utc_text(root["time"]),
                    "displacementBarId": displacement["barId"],
                    "displacementTimeUtc": utc_text(displacement["time"]),
                    "displacementEpisodeBarIds": episode_bar_ids,
                    "displacementEpisodeStartBarId": episode_bar_ids[0],
                    "displacementEpisodeEndBarId": episode_bar_ids[-1],
                    "displacementEpisodeComplete": episode_end_index < right,
                    "laterClosedBars": max(0, later_right - displacement_index - 1),
                    "laterBodyInvalidated": later_body_invalidated,
                    "laterDistalTouched": later_distal_touched,
                    "laterProximalTouched": later_proximal_touched,
                }
            )
    candidates.sort(
        key=lambda item: split_bar_id(item["displacementBarId"])[1], reverse=True
    )
    if maximum is None:
        return candidates
    return candidates[: max(1, int(maximum))]


def root_bar_ids_available_between(
    market: MarketData,
    after: int,
    as_of: int,
    *,
    timeframes: Iterable[str] = ("H1", "M30", "M15"),
) -> set[str]:
    """Return roots whose displacement first became knowable in the interval.

    The permanent episode cache is built once per dataset. Replaying another
    M5 bar then performs only an indexed timestamp comparison instead of
    rebuilding every cross-timeframe family in the historical archive.
    """
    selected: set[str] = set()
    for timeframe in timeframes:
        series = market.frames[timeframe]
        cache_key = (market.cache_token, timeframe)
        if cache_key not in _ROOT_EPISODE_CACHE:
            mechanical_root_candidates(
                market,
                as_of,
                maximum=None,
                timeframe_limits={timeframe: PLAN_LIMITS.get(timeframe, 1)},
                active_only=False,
            )
        index = _ROOT_AVAILABILITY_INDEX_CACHE.get(cache_key)
        if index is None:
            ordered = sorted(
                (
                    int(series.available_time[displacement_index]),
                    bar_id(timeframe, int(series.time[root_index])),
                )
                for root_index, displacement_index, _, _
                in _ROOT_EPISODE_CACHE[cache_key]
            )
            index = {
                "available": np.asarray(
                    [item[0] for item in ordered], dtype=np.int64
                ),
                "rootBarIds": [item[1] for item in ordered],
            }
            _ROOT_AVAILABILITY_INDEX_CACHE[cache_key] = index
        left = int(np.searchsorted(index["available"], int(after), side="right"))
        right = int(np.searchsorted(index["available"], int(as_of), side="right"))
        selected.update(index["rootBarIds"][left:right])
    return selected


def liquidity_bar_ids_matured_between(
    market: MarketData,
    after: int,
    as_of: int,
    *,
    timeframes: Iterable[str] = ("H1", "M30", "M15"),
) -> set[str]:
    """Return newly mature objective evidence without rebuilding PLAN families."""
    selected: set[str] = set()
    # Populate the permanent event cache once. Subsequent M15 checks use only
    # the maturity timestamp index and never resolve every historical level.
    if any(
        (market.cache_token, timeframe) not in _LIQUIDITY_EVENT_CACHE
        for timeframe in timeframes
    ):
        _confirmed_liquidity_swings(market, as_of, active_only=False)
    for timeframe in timeframes:
        cache_key = (market.cache_token, timeframe)
        index = _LIQUIDITY_MATURITY_INDEX_CACHE.get(cache_key)
        if index is None:
            ordered = sorted(
                (
                    parse_utc(str(item["matureAtUtc"])),
                    str(item["barId"]),
                )
                for item in _LIQUIDITY_EVENT_CACHE.get(cache_key, [])
            )
            index = {
                "mature": np.asarray(
                    [item[0] for item in ordered], dtype=np.int64
                ),
                "barIds": [item[1] for item in ordered],
            }
            _LIQUIDITY_MATURITY_INDEX_CACHE[cache_key] = index
        left = int(np.searchsorted(index["mature"], int(after), side="right"))
        right = int(np.searchsorted(index["mature"], int(as_of), side="right"))
        selected.update(index["barIds"][left:right])
    return selected


def map_opportunity_id(candidate: dict[str, Any]) -> str:
    """Collapse the same physical displacement observed on multiple timeframes."""
    direction = str(candidate["direction"])
    _, timestamp = split_bar_id(str(candidate["displacementBarId"]))
    return f"{direction}:{timestamp}"


def mechanical_root_event_counts(
    market: MarketData, as_of: int, timeframes: Iterable[str]
) -> dict[str, int]:
    """Count the permanent visible ledger without materializing every payload."""
    counts: dict[str, int] = {}
    for timeframe in timeframes:
        # Populate the permanent episode cache through the same discovery code.
        mechanical_root_candidates(
            market,
            as_of,
            maximum=None,
            timeframe_limits={timeframe: PLAN_LIMITS.get(timeframe, 1)},
            active_only=True,
        )
        series = market.frames[timeframe]
        right = int(np.searchsorted(series.available_time, as_of, side="right"))
        counts[timeframe] = sum(
            int(displacement_index) < right
            for _, displacement_index, _, _ in _ROOT_EPISODE_CACHE[
                (market.cache_token, timeframe)
            ]
        )
    return counts


def discovery_event_fingerprint(
    market: MarketData,
    as_of: int,
    external_authority: dict[str, Any] | None = None,
) -> str:
    """Hash only local events capable of creating a new PLAN family.

    This is deliberately cheaper than building the complete semantic packet.
    A family can become newly selectable only when a root displacement, a
    confirmed swing/objective, or the frozen external authority changes.  Zone
    consumption can remove a family but cannot create one, so ordinary M5 price
    movement does not justify rebuilding every cross-timeframe lineage.
    """
    roots = mechanical_root_candidates(market, as_of, maximum=None)
    newest_root_events: dict[tuple[str, str], tuple[str, str, str]] = {}
    for item in roots:
        key = (str(item["timeframe"]), str(item["direction"]))
        event = (
            str(item["direction"]),
            str(item["rootBarId"]),
            str(item["displacementBarId"]),
        )
        previous = newest_root_events.get(key)
        if previous is None or split_bar_id(event[2])[1] > split_bar_id(previous[2])[1]:
            newest_root_events[key] = event
    root_events = sorted(newest_root_events.values())
    newest_swing_events: dict[tuple[str, str], tuple[str, str, str]] = {}
    for timeframe, limit in MAP_LIMITS.items():
        rows = market.bars(timeframe, as_of, limit)
        for index in range(2, len(rows) - 2):
            row = rows[index]
            left = rows[index - 2:index]
            right = rows[index + 1:index + 3]
            if row["high"] > max(item["high"] for item in left) and row["high"] >= max(
                item["high"] for item in right
            ):
                newest_swing_events[(timeframe, "HIGH")] = (
                    timeframe, str(row["barId"]), "HIGH"
                )
            if row["low"] < min(item["low"] for item in left) and row["low"] <= min(
                item["low"] for item in right
            ):
                newest_swing_events[(timeframe, "LOW")] = (
                    timeframe, str(row["barId"]), "LOW"
                )
    swing_events = sorted(newest_swing_events.values())
    authority = resolved_external_authority(market, external_authority, as_of)
    authority_event = None
    if authority:
        authority_event = {
            "direction": authority.get("direction"),
            "status": authority.get("status"),
            "protectedSwingBarId": (authority.get("protectedSwing") or {}).get("barId"),
            "bodyBreakBarId": authority.get("bodyBreakBarId"),
            "objectiveReachedBarId": authority.get("objectiveReachedBarId"),
        }
    return canonical_hash(
        {
            "rootEvents": root_events,
            "swingEvents": swing_events,
            "authorityEvent": authority_event,
        }
    )


def _body_broken_protected_candidates(
    market: MarketData,
    timeframe: str,
    root: dict[str, Any],
    displacement: dict[str, Any],
    direction: str,
    as_of: int,
    maximum: int | None = None,
    confirmed_swings: list[dict[str, Any]] | dict[tuple[str, str], Any] | None = None,
) -> list[str]:
    # Protected structure selection is broader than the liquidity display
    # ledger. A completed one-left/two-right reaction is selectable even when
    # it is not a classic two-sided pivot. Build that permanent event set once
    # per market/timeframe/direction; rescanning all historical bars for every
    # root turns uncapped evidence into O(candidate * history) work.
    series = market.frames[timeframe]
    root_index = int(root["index"])
    reaction_key = (market.cache_token, timeframe, direction)
    reaction_index = _PROTECTED_REACTION_CACHE.get(reaction_key)
    if reaction_index is None:
        indexes = np.arange(1, max(1, len(series.time) - 2), dtype=np.int64)
        if direction == "LONG":
            prices = np.asarray(series.high[indexes], dtype=float)
            reactions = (
                prices > np.asarray(series.high[indexes - 1], dtype=float)
            ) & (
                prices >= np.maximum(
                    np.asarray(series.high[indexes + 1], dtype=float),
                    np.asarray(series.high[indexes + 2], dtype=float),
                )
            )
        else:
            prices = np.asarray(series.low[indexes], dtype=float)
            reactions = (
                prices < np.asarray(series.low[indexes - 1], dtype=float)
            ) & (
                prices <= np.minimum(
                    np.asarray(series.low[indexes + 1], dtype=float),
                    np.asarray(series.low[indexes + 2], dtype=float),
                )
            )
        indexes = indexes[reactions]
        reaction_index = {
            "indexes": indexes,
            "times": np.asarray(series.time[indexes], dtype=np.int64),
            "matureAvailable": np.asarray(
                series.available_time[indexes + 2], dtype=np.int64
            ),
            "prices": np.asarray(
                series.high[indexes] if direction == "LONG" else series.low[indexes],
                dtype=float,
            ),
        }
        first_break_by_index: dict[int, list[int]] = {}
        active: list[tuple[float, int]] = []
        maturity_indexes = indexes + 2
        next_maturity = 0
        for bar_index in range(len(series.time)):
            while (
                next_maturity < len(maturity_indexes)
                and int(maturity_indexes[next_maturity]) <= bar_index
            ):
                price = float(reaction_index["prices"][next_maturity])
                heap_price = price if direction == "LONG" else -price
                heapq.heappush(active, (heap_price, next_maturity))
                next_maturity += 1
            close = float(series.close[bar_index])
            while active:
                level = float(active[0][0])
                crossed = level < close if direction == "LONG" else -level > close
                if not crossed:
                    break
                _, reaction_position = heapq.heappop(active)
                first_break_by_index.setdefault(bar_index, []).append(
                    int(reaction_position)
                )
        reaction_index["firstBreakByIndex"] = first_break_by_index
        _PROTECTED_REACTION_CACHE[reaction_key] = reaction_index

    positions = reaction_index["firstBreakByIndex"].get(
        int(displacement["index"]), []
    )
    ordered = [
        {
            "barId": bar_id(
                timeframe, int(reaction_index["times"][reaction_position])
            ),
            "time": int(reaction_index["times"][reaction_position]),
        }
        for reaction_position in positions
        if int(reaction_index["indexes"][reaction_position]) < root_index
        and int(reaction_index["matureAvailable"][reaction_position])
        <= int(displacement["available"])
    ]
    ordered.sort(key=lambda item: int(item["time"]))
    if maximum is not None:
        ordered = ordered[-int(maximum):]
    return [str(row["barId"]) for row in ordered]


_M1_SUFFIX_CACHE: dict[str, Any] = {}
_M1_RANGE_INDEX_CACHE: dict[str, Any] = {}
_M1_LIFECYCLE_CACHE: dict[tuple[Any, ...], dict[str, bool]] = {}
_OBJECTIVE_CONSUMED_CACHE: dict[tuple[Any, ...], bool] = {}
_NODE_CONSUMED_CACHE: dict[tuple[Any, ...], bool] = {}
_NODE_TOUCHED_CACHE: dict[tuple[Any, ...], bool] = {}


def _m1_suffix_extremes(market: MarketData, as_of: int) -> dict[str, Any]:
    key = (id(market.rates), int(as_of))
    if _M1_SUFFIX_CACHE.get("key") == key:
        return _M1_SUFFIX_CACHE["value"]
    times = _m1_times(market)
    right = int(np.searchsorted(times, int(as_of) - 60, side="right"))
    highs = np.asarray(market.rates["high"][:right], dtype=float)
    lows = np.asarray(market.rates["low"][:right], dtype=float)
    closes = np.asarray(market.rates["close"][:right], dtype=float)
    value = {
        "right": right,
        "highMax": np.maximum.accumulate(highs[::-1])[::-1],
        "lowMin": np.minimum.accumulate(lows[::-1])[::-1],
        "closeMax": np.maximum.accumulate(closes[::-1])[::-1],
        "closeMin": np.minimum.accumulate(closes[::-1])[::-1],
    }
    _M1_SUFFIX_CACHE.clear()
    _M1_SUFFIX_CACHE.update({"key": key, "value": value})
    return value


def _m1_range_extremes(
    market: MarketData, left: int, right: int
) -> dict[str, float]:
    """Return M1 extrema for [left, right) without rebuilding suffix arrays."""
    key = id(market.rates)
    if _M1_RANGE_INDEX_CACHE.get("key") != key:
        block_size = 1024
        arrays = {
            "highMax": np.asarray(market.rates["high"], dtype=float),
            "lowMin": np.asarray(market.rates["low"], dtype=float),
            "closeMax": np.asarray(market.rates["close"], dtype=float),
            "closeMin": np.asarray(market.rates["close"], dtype=float),
        }
        blocks: dict[str, np.ndarray] = {}
        for name, values in arrays.items():
            block_values: list[float] = []
            reducer = np.min if name.endswith("Min") else np.max
            for start in range(0, len(values), block_size):
                block_values.append(float(reducer(values[start:start + block_size])))
            blocks[name] = np.asarray(block_values, dtype=float)
        _M1_RANGE_INDEX_CACHE.clear()
        _M1_RANGE_INDEX_CACHE.update({
            "key": key,
            "blockSize": block_size,
            "arrays": arrays,
            "blocks": blocks,
        })
    index = _M1_RANGE_INDEX_CACHE
    arrays = index["arrays"]
    blocks = index["blocks"]
    block_size = int(index["blockSize"])
    left = max(0, int(left))
    right = min(len(market.rates), int(right))
    if right <= left:
        raise V4ContractError("M1 extrema query range is empty")

    def query(name: str) -> float:
        values = arrays[name]
        reducer = np.min if name.endswith("Min") else np.max
        first_full = (left + block_size - 1) // block_size
        last_full = right // block_size
        parts: list[float] = []
        prefix_end = min(right, first_full * block_size)
        if left < prefix_end:
            parts.append(float(reducer(values[left:prefix_end])))
        if first_full < last_full:
            parts.append(float(reducer(blocks[name][first_full:last_full])))
        suffix_start = max(left, last_full * block_size)
        if suffix_start < right:
            parts.append(float(reducer(values[suffix_start:right])))
        return float(reducer(np.asarray(parts, dtype=float)))

    return {name: query(name) for name in arrays}


def _m1_zone_lifecycle(
    market: MarketData,
    ob: dict[str, Any],
    displacement: dict[str, Any],
    direction: str,
    as_of: int,
) -> dict[str, bool]:
    """Measure freshness on the common M1 clock used by freeze and execution."""
    cache_key = (
        id(market.rates), int(as_of), str(ob["barId"]),
        str(displacement["barId"]), str(direction),
    )
    cached = _M1_LIFECYCLE_CACHE.get(cache_key)
    if cached is not None:
        return dict(cached)
    times = _m1_times(market)
    left = int(np.searchsorted(times, int(displacement["available"]), side="left"))
    right = int(np.searchsorted(times, int(as_of) - 60, side="right"))
    if right <= left:
        result = {
            "bodyInvalidated": False,
            "distalTouched": False,
            "proximalTouched": False,
        }
        _M1_LIFECYCLE_CACHE[cache_key] = result
        return dict(result)
    extrema = _m1_range_extremes(market, left, right)
    if direction == "LONG":
        result = {
            "bodyInvalidated": bool(extrema["closeMin"] < ob["low"]),
            "distalTouched": bool(extrema["lowMin"] <= ob["low"]),
            "proximalTouched": bool(extrema["lowMin"] <= ob["high"]),
        }
    else:
        result = {
            "bodyInvalidated": bool(extrema["closeMax"] > ob["high"]),
            "distalTouched": bool(extrema["highMax"] >= ob["high"]),
            "proximalTouched": bool(extrema["highMax"] >= ob["low"]),
        }
    _M1_LIFECYCLE_CACHE[cache_key] = result
    if len(_M1_LIFECYCLE_CACHE) > 20000:
        _M1_LIFECYCLE_CACHE.clear()
        _M1_LIFECYCLE_CACHE[cache_key] = result
    return dict(result)


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
        times = _m1_times(market)
        left = int(np.searchsorted(times, objective_start, side="left"))
        right = int(np.searchsorted(times, int(as_of) - 60, side="right"))
        if right > left:
            selected = market.rates[left:right]
            mask = (
                selected["high"] >= float(frozen_objective["price"])
                if str(frozen_objective["side"]) == "HIGH"
                else selected["low"] <= float(frozen_objective["price"])
            )
            matches = np.flatnonzero(mask)
            if len(matches):
                objective_reached_bar = market.m1_row(left + int(matches[0]))
    break_available = int(break_bar["available"]) if break_bar else None
    objective_available = (
        int(objective_reached_bar["available"])
        if objective_reached_bar else None
    )
    if break_available is not None and (
        objective_available is None or break_available <= objective_available
    ):
        status = "REMAP_REQUIRED"
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
        "historicalResolution": (
            "RESOLVED_BROKEN" if status == "REMAP_REQUIRED" else None
        ),
        "bodyBreakBarId": break_bar["barId"] if break_bar else None,
        "objectiveReachedBarId": (
            objective_reached_bar["barId"] if objective_reached_bar else None
        ),
        "objectiveReachedAtUtc": (
            utc_text(objective_available) if objective_available is not None else None
        ),
        "resolvedAtUtc": utc_text(resolved_at) if resolved_at is not None else None,
    }


def _is_nearer_same_owner_external_objective(
    direction: str,
    frozen_objective: dict[str, Any],
    candidate: dict[str, Any],
    market_price: float,
) -> bool:
    """Return whether candidate is the next HTF checkpoint before a frozen target."""
    expected_side = "HIGH" if direction == "LONG" else "LOW"
    candidate_tf = str(candidate.get("tf") or split_bar_id(str(candidate["barId"]))[0])
    if (
        candidate_tf not in {"H1", "M30"}
        or (
            candidate.get("kind") is not None
            and str(candidate.get("kind")) != "EXTERNAL_SWING"
        )
        or str(candidate.get("side")) != expected_side
        or str(frozen_objective.get("side")) != expected_side
        or str(candidate.get("barId")) == str(frozen_objective.get("barId"))
    ):
        return False
    frozen_price = float(frozen_objective["price"])
    candidate_price = float(candidate["price"])
    return (
        market_price < candidate_price < frozen_price
        if direction == "LONG"
        else frozen_price < candidate_price < market_price
    )


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
            same_map = (
                str(scenario["dealingRange"]["highBarId"])
                == str(expected_range["highBarId"])
                and str(scenario["dealingRange"]["lowBarId"])
                == str(expected_range["lowBarId"])
                and str(scenario["mapProtectedSwing"]["barId"])
                == str(expected_protected["barId"])
            )
            same_objective = bool(
                isinstance(expected_objective, dict)
                and str(scenario["objective"]["barId"])
                == str(expected_objective["barId"])
            )
            nearer_objective = False
            if not same_objective and isinstance(expected_objective, dict):
                nearer_objective = _is_nearer_same_owner_external_objective(
                    direction,
                    expected_objective,
                    scenario["objective"],
                    float(scenario["root"]["proximal"]),
                )
            if not same_map or (not same_objective and not nearer_objective):
                raise V4ContractError(
                    "same-owner continuation attempted to redefine active external authority"
                )
            if same_objective:
                return previous
            # The authority owns direction and protected structure.  A new
            # scenario may freeze a newly mature nearer external checkpoint
            # without rewriting any already-frozen order or position TP.
            return {
                **previous,
                "establishedAtUtc": str(scenario["frozenAtUtc"]),
                "sourceScenarioHash": str(scenario["scenarioHash"]),
                "sourceScope": scope,
                "objective": dict(scenario["objective"]),
                "status": "ACTIVE",
                "objectiveReachedBarId": None,
                "objectiveReachedAtUtc": None,
                "resolvedAtUtc": None,
            }
        if previous_status == "REMAP_REQUIRED":
            if direction == previous_direction:
                if scope != "EXTERNAL_CONTINUATION":
                    raise V4ContractError(
                        "same-direction owner re-establishment requires external continuation"
                    )
            elif scope != "EXTERNAL_REVERSAL":
                raise V4ContractError(
                    "opposite owner after a body break requires external reversal"
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
    """Promote a physical wick only when the containing HTF swing is mature."""
    source = market.bar(str(objective["barId"]), as_of)
    side = str(objective["side"])
    price = float(objective["price"])
    confirmed = {
        (str(item["barId"]), str(item["side"])): item
        for item in [
            *_confirmed_liquidity_swings(market, as_of, active_only=True),
            *_confirmed_long_history_h1_swings(market, as_of),
        ]
        if item["timeframe"] in {"H1", "M30"}
    }
    for timeframe in ("H1", "M30"):
        seconds = TIMEFRAME_SECONDS[timeframe]
        containing_id = bar_id(timeframe, source["time"] - source["time"] % seconds)
        try:
            containing = market.bar(containing_id, as_of)
        except V4ContractError:
            continue
        wick = float(containing["high"] if side == "HIGH" else containing["low"])
        maturity = confirmed.get((str(containing["barId"]), side))
        if maturity and abs(wick - price) <= market.point / 2.0:
            return {
                "barId": containing["barId"],
                "side": side,
                "price": price,
                "matureAtUtc": maturity["matureAtUtc"],
                "maturityBarId": maturity["maturityBarId"],
            }
    return None


def _causal_dealing_range_pairs(
    market: MarketData,
    as_of: int,
    root: dict[str, Any],
    displacement: dict[str, Any],
    direction: str,
    protected_swing_bar_ids: list[str],
    swing_candidates: list[dict[str, Any]],
    decision_close: float,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Build a causal HTF range from source and body-broken structure.

    The opposite boundary of an active dealing range is the protected swing
    actually body-broken by this displacement.  It is not an arbitrary future
    objective.  Keeping those concepts separate is essential because distant
    H1 liquidity is permitted as fallback TP evidence, but can never redefine
    the current protected range.
    """
    source_side = "LOW" if direction == "LONG" else "HIGH"
    objective_side = "HIGH" if direction == "LONG" else "LOW"
    pairs: list[dict[str, Any]] = []
    context_ids: list[str] = []

    for timeframe in ("H1", "M30"):
        seconds = TIMEFRAME_SECONDS[timeframe]
        episode_start = int(root["time"]) - int(root["time"]) % seconds
        episode_end = int(displacement["time"]) - int(displacement["time"]) % seconds
        source_swings = [
            item for item in swing_candidates
            if item["timeframe"] == timeframe
            and item["side"] == source_side
            and episode_start <= split_bar_id(str(item["barId"]))[1] <= episode_end
            and parse_utc(str(item["matureAtUtc"])) <= as_of
        ]
        if not source_swings:
            continue

        # One delivery episode has one structural source extreme per timeframe.
        # The price extreme is primary; the latest origin is only a deterministic
        # tie breaker for equal-price broker bars.
        source = (
            min(
                source_swings,
                key=lambda item: (
                    float(item["price"]),
                    -split_bar_id(str(item["barId"]))[1],
                ),
            )
            if direction == "LONG"
            else max(
                source_swings,
                key=lambda item: (
                    float(item["price"]),
                    split_bar_id(str(item["barId"]))[1],
                ),
            )
        )
        protected_swings: list[dict[str, Any]] = []
        for protected_id in protected_swing_bar_ids:
            if split_bar_id(str(protected_id))[0] != timeframe:
                continue
            protected = market.bar(str(protected_id), as_of)
            protected_index = int(protected["index"])
            series = market.frames[timeframe]
            maturity_index = protected_index + 2
            if maturity_index >= len(series.time):
                continue
            maturity_available = int(series.available_time[maturity_index])
            if maturity_available > int(displacement["available"]):
                continue
            protected_swings.append({
                "barId": str(protected["barId"]),
                "side": objective_side,
                "price": float(
                    protected["high"] if objective_side == "HIGH" else protected["low"]
                ),
                "matureAtUtc": utc_text(maturity_available),
            })
        for protected in protected_swings:
            low = (
                float(source["price"])
                if direction == "LONG" else float(protected["price"])
            )
            high = (
                float(protected["price"])
                if direction == "LONG" else float(source["price"])
            )
            if low >= high:
                continue
            eq = (low + high) / 2.0
            pairs.append(
                {
                    "timeframe": timeframe,
                    "highBarId": (
                        str(protected["barId"])
                        if direction == "LONG" else str(source["barId"])
                    ),
                    "lowBarId": (
                        str(source["barId"])
                        if direction == "LONG" else str(protected["barId"])
                    ),
                    "bodyBrokenProtectedSwingBarId": str(protected["barId"]),
                    "high": high,
                    "low": low,
                    "eq": round(eq, 5),
                    "decisionCloseLocation": (
                        "DISCOUNT" if decision_close <= eq else "PREMIUM"
                    ),
                    "sourceSwingMatureAtUtc": str(source["matureAtUtc"]),
                    "protectedSwingMatureAtUtc": str(protected["matureAtUtc"]),
                }
            )
            context_ids.extend((str(source["barId"]), str(protected["barId"])))

    pairs.sort(
        key=lambda item: (
            abs(
                float(item["high"] if direction == "LONG" else item["low"])
                - float(decision_close)
            ),
            0 if item["timeframe"] == "H1" else 1,
        )
    )
    return pairs, list(dict.fromkeys(context_ids))


def _physical_lineage_families(
    market: MarketData,
    as_of: int,
    roots: list[dict[str, Any]],
    children: list[dict[str, Any]],
    swing_candidates: list[dict[str, Any]],
    external_authority: dict[str, Any] | None = None,
    focus_objective_bar_ids: set[str] | None = None,
    fixed_objective_members: list[dict[str, Any]] | None = None,
    fixed_dealing_range: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Group only physically possible parent/child events without authorizing causality."""
    families: list[dict[str, Any]] = []
    # All candidate-side price tests use the same completed M1 event clock that
    # scheduled PLAN.  HTF/M15 closes describe structure, never current price.
    decision_close = market.bars("M1", as_of, 1)[-1]["close"]
    timeframe_rank = {"H1": 0, "M30": 1, "M15": 2, "M5": 3}
    authority = resolved_external_authority(market, external_authority, as_of)
    recent_h1 = market.bars("H1", as_of, LIQUIDITY_LIMITS["H1"])
    recent_h1_high = max(
        (float(item["high"]) for item in recent_h1), default=decision_close
    )
    recent_h1_low = min(
        (float(item["low"]) for item in recent_h1), default=decision_close
    )
    raw_swing_index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for swing in swing_candidates:
        raw_swing_index.setdefault(
            (str(swing["timeframe"]), str(swing["side"])), []
        ).append(swing)
    swing_index: dict[tuple[str, str], dict[str, Any]] = {}
    for key, items in raw_swing_index.items():
        ordered = sorted(items, key=lambda item: split_bar_id(str(item["barId"]))[1])
        swing_index[key] = {
            "items": ordered,
            "times": np.asarray(
                [split_bar_id(str(item["barId"]))[1] for item in ordered],
                dtype=np.int64,
            ),
            "mature": np.asarray(
                [parse_utc(str(item["matureAtUtc"])) for item in ordered],
                dtype=np.int64,
            ),
            "prices": np.asarray(
                [float(item["price"]) for item in ordered], dtype=float
            ),
        }
    live_objectives_by_side: dict[str, list[dict[str, Any]]] = {
        "HIGH": [], "LOW": []
    }
    objective_source = swing_candidates
    if fixed_objective_members is not None:
        objective_source = []
        for member in fixed_objective_members:
            row = market.bar(str(member["barId"]), as_of)
            side = str(member.get("side") or (
                "HIGH" if float(member["price"]) >= decision_close else "LOW"
            ))
            objective_source.append({
                **member,
                "barId": str(member["barId"]),
                "timeframe": row["tf"],
                "side": side,
                "price": float(member.get("price") or (
                    row["high"] if side == "HIGH" else row["low"]
                )),
                "matureAtUtc": member.get("matureAtUtc") or utc_text(row["available"]),
            })
    for swing in objective_source:
        if str(swing["timeframe"]) not in {"H1", "M30", "M15"}:
            continue
        if (
            focus_objective_bar_ids is not None
            and str(swing["barId"]) not in focus_objective_bar_ids
        ):
            continue
        objective_probe = {
            "barId": str(swing["barId"]),
            "side": str(swing["side"]),
            "price": float(swing["price"]),
        }
        # Permanent liquidity evidence already carries its as-of lifecycle.
        # Re-querying the full M1 range here duplicated the same work once per
        # family build and dominated month replay time.
        is_live = (
            str(swing.get("state")) == "ACTIVE"
            if swing.get("state") is not None
            else not _objective_consumed(market, objective_probe, as_of)
        )
        if is_live:
            live_objectives_by_side[str(swing["side"])].append(swing)
    # A child can overlap several higher-timeframe roots, but its zone lifecycle
    # is a property of the physical child event itself.  Computing it inside
    # every root/child pair turns an uncapped evidence ledger into an accidental
    # O(roots * children * M1-history) scan.  Resolve each physical child once;
    # no candidate is removed by this cache.
    child_evidence: dict[tuple[str, str, str], dict[str, Any]] = {}
    for child_candidate in children:
        key = (
            str(child_candidate["direction"]),
            str(child_candidate["rootBarId"]),
            str(child_candidate["displacementBarId"]),
        )
        if key in child_evidence:
            continue
        child_root = market.bar(key[1], as_of)
        child_displacement = market.bar(key[2], as_of)
        extensions: list[dict[str, Any]] = []
        child_series = market.frames[child_root["tf"]]
        extension_right = int(np.searchsorted(
            child_series.available_time, as_of, side="right"
        ))
        for extension_index in range(
            int(child_displacement["index"]) + 1, extension_right
        ):
            extension = market.bar(
                bar_id(child_root["tf"], int(child_series.time[extension_index])),
                as_of,
            )
            if key[0] == "LONG":
                if extension["close"] < extension["open"]:
                    break
                if (
                    extension["close"] > extension["open"]
                    and extension["close"] > child_root["high"]
                ):
                    extensions.append(extension)
            else:
                if extension["close"] > extension["open"]:
                    break
                if (
                    extension["close"] < extension["open"]
                    and extension["close"] < child_root["low"]
                ):
                    extensions.append(extension)
        delivery_rows = {
            row["barId"]: row for row in [child_displacement, *extensions]
        }
        delivery_options = [
            {
                "displacementBarId": selected["barId"],
                "displacementAvailable": selected["available"],
                "eligibleProtectedSwingBarIds": _body_broken_protected_candidates(
                    market,
                    child_root["tf"],
                    child_root,
                    selected,
                    key[0],
                    as_of,
                    confirmed_swings=swing_index,
                ),
                "episodeBarIds": [
                    bar_id(child_root["tf"], int(child_series.time[index]))
                    for index in range(
                        int(child_root["index"]), int(selected["index"]) + 1
                    )
                ],
            }
            for selected in delivery_rows.values()
        ]
        child_evidence[key] = {
            "root": child_root,
            "displacement": child_displacement,
            "lifecycle": _m1_zone_lifecycle(
                market, child_root, child_displacement, key[0], as_of
            ),
            "deliveryOptions": delivery_options,
        }
    for root_candidate in roots:
        if (
            root_candidate["laterBodyInvalidated"]
            or root_candidate["laterDistalTouched"]
        ):
            continue
        root = market.bar(str(root_candidate["rootBarId"]), as_of)
        displacement = market.bar(str(root_candidate["displacementBarId"]), as_of)
        episode_displacement = market.bar(
            str(root_candidate["displacementEpisodeEndBarId"]), as_of
        )
        direction = str(root_candidate["direction"])
        compatible_children: list[dict[str, Any]] = []
        for child_candidate in children:
            if child_candidate["direction"] != direction:
                continue
            if (
                child_candidate["laterBodyInvalidated"]
                or child_candidate["laterDistalTouched"]
            ):
                continue
            cached_child = child_evidence[
                (
                    direction,
                    str(child_candidate["rootBarId"]),
                    str(child_candidate["displacementBarId"]),
                )
            ]
            child_root = cached_child["root"]
            child_displacement = cached_child["displacement"]
            child_lifecycle = cached_child["lifecycle"]
            if (
                child_lifecycle["bodyInvalidated"]
                or child_lifecycle["distalTouched"]
            ):
                continue
            if timeframe_rank[child_root["tf"]] <= timeframe_rank[root["tf"]]:
                continue
            inside_parent_candle = root["time"] <= child_root["time"] < root["available"]
            overlaps_parent_event = (
                root["time"] <= child_root["time"] < episode_displacement["available"]
                and child_root["high"] >= root["low"]
                and child_root["low"] <= root["high"]
            )
            if not (inside_parent_candle or overlaps_parent_event):
                continue
            delivery_options = [
                {
                    key: value for key, value in item.items()
                    if key != "displacementAvailable"
                }
                for item in cached_child["deliveryOptions"]
                if int(item["displacementAvailable"])
                <= int(episode_displacement["available"])
            ]
            delivery_options = [
                item for item in delivery_options
                if item["eligibleProtectedSwingBarIds"]
            ]
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
            balanced_children.extend(same_timeframe)
        compatible_children = balanced_children
        root_delivery_options = []
        for displacement_id in root_candidate["displacementEpisodeBarIds"][1:]:
            selected_displacement = market.bar(str(displacement_id), as_of)
            protected_ids = _body_broken_protected_candidates(
                market, root["tf"], root, selected_displacement, direction, as_of,
                confirmed_swings=swing_index,
            )
            if protected_ids:
                root_delivery_options.append({
                    "displacementBarId": selected_displacement["barId"],
                    "eligibleProtectedSwingBarIds": protected_ids,
                })
        root_protected_ids = list(dict.fromkeys(
            protected_id
            for option in root_delivery_options
            for protected_id in option["eligibleProtectedSwingBarIds"]
        ))
        if not compatible_children or not root_protected_ids:
            continue

        objective_candidates: list[dict[str, Any]] = []
        expected_side = "HIGH" if direction == "LONG" else "LOW"
        for swing in live_objectives_by_side[expected_side]:
            if direction == "LONG" and float(swing["price"]) <= decision_close:
                continue
            if direction == "SHORT" and float(swing["price"]) >= decision_close:
                continue
            objective = {
                "barId": swing["barId"], "side": expected_side,
                "price": float(swing["price"]),
                "matureAtUtc": swing.get("matureAtUtc"),
                "maturityBarId": swing.get("maturityBarId"),
                "historyTier": (
                    "LONG_TERM_H1"
                    if (
                        str(swing["timeframe"]) == "H1"
                        and as_of - split_bar_id(str(swing["barId"]))[1]
                        >= LONG_TERM_H1_DAYS * 86400
                    )
                    else "CURRENT_STRUCTURE"
                ),
            }
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
        if fixed_dealing_range is not None:
            range_pairs = [{
                "timeframe": split_bar_id(str(fixed_dealing_range["highBarId"]))[0],
                "highBarId": str(fixed_dealing_range["highBarId"]),
                "lowBarId": str(fixed_dealing_range["lowBarId"]),
                "bodyBrokenProtectedSwingBarId": str(
                    fixed_dealing_range[
                        "highBarId" if direction == "LONG" else "lowBarId"
                    ]
                ),
                "high": float(fixed_dealing_range["high"]),
                "low": float(fixed_dealing_range["low"]),
                "eq": (
                    float(fixed_dealing_range["high"])
                    + float(fixed_dealing_range["low"])
                ) / 2.0,
                "decisionCloseLocation": (
                    "DISCOUNT"
                    if decision_close <= (
                        float(fixed_dealing_range["high"])
                        + float(fixed_dealing_range["low"])
                    ) / 2.0
                    else "PREMIUM"
                ),
            }]
            map_context_ids = [
                str(fixed_dealing_range["highBarId"]),
                str(fixed_dealing_range["lowBarId"]),
            ]
        else:
            range_pairs, map_context_ids = _causal_dealing_range_pairs(
                market,
                as_of,
                root,
                episode_displacement,
                direction,
                root_protected_ids,
                swing_candidates,
                float(decision_close),
            )
        if not range_pairs:
            continue
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
                "rootDisplacementEpisodeBarIds": list(
                    root_candidate.get("displacementEpisodeBarIds", [
                        root["barId"], displacement["barId"]
                    ])
                ),
                "rootLaterBodyInvalidated": root_lifecycle["bodyInvalidated"],
                "rootLaterDistalTouched": root_lifecycle["distalTouched"],
                "rootLaterProximalTouched": root_lifecycle["proximalTouched"],
                "eligibleProtectedSwingBarIds": root_protected_ids,
                "rootDeliveryOptions": root_delivery_options,
                "childCandidates": compatible_children,
                "unconsumedDirectionalLiquidityCandidates": objective_candidates,
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
                            "displacementBarId": delivery["displacementBarId"],
                            "protectedSwingBarId": protected_id,
                        }
                    )[:16],
                    "obBarId": family["rootBarId"],
                    "displacementBarId": delivery["displacementBarId"],
                    "protectedSwingBarId": protected_id,
                }
                for delivery in family["rootDeliveryOptions"]
                for protected_id in delivery["eligibleProtectedSwingBarIds"]
                if _delivery_valid(
                    root, market.bar(delivery["displacementBarId"], as_of),
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
            # Enumerate one physical ancestry chain for every terminal child.
            # The former recursive walk branched from every ancestor to every
            # descendant and could produce a combinatorial number of duplicate
            # paths after the global candidate cap was removed.  Candles on the
            # same timeframe do not overlap in time, so a terminal child has at
            # most one containing parent on the nearest higher timeframe.  All
            # separate terminal children remain separate selectable paths.
            terminal_ids = [
                child_id for child_id in child_ids
                if not any(
                    other_id != child_id and nested(child_id, other_id)
                    for other_id in child_ids
                )
            ]

            def physical_ancestry(terminal_id: str) -> list[str]:
                reversed_path = [terminal_id]
                current_id = terminal_id
                while True:
                    current_minutes = TIMEFRAME_MINUTES[split_bar_id(current_id)[0]]
                    parents = [
                        candidate_id for candidate_id in child_ids
                        if candidate_id not in reversed_path
                        and TIMEFRAME_MINUTES[split_bar_id(candidate_id)[0]] > current_minutes
                        and nested(candidate_id, current_id)
                    ]
                    if not parents:
                        break
                    nearest_minutes = min(
                        TIMEFRAME_MINUTES[split_bar_id(candidate_id)[0]]
                        for candidate_id in parents
                    )
                    nearest = [
                        candidate_id for candidate_id in parents
                        if TIMEFRAME_MINUTES[split_bar_id(candidate_id)[0]] == nearest_minutes
                    ]
                    # Same-timeframe candles cannot both contain the same child;
                    # deterministic sorting is only a defensive tie breaker for
                    # malformed broker timestamps, not a candidate-count cap.
                    current_id = sorted(
                        nearest,
                        key=lambda item: split_bar_id(item)[1],
                        reverse=True,
                    )[0]
                    reversed_path.append(current_id)
                return list(reversed(reversed_path))

            raw_paths = []
            seen_paths: set[tuple[str, ...]] = set()
            for terminal_id in terminal_ids:
                path = physical_ancestry(terminal_id)
                key = tuple(path)
                if key in seen_paths:
                    continue
                seen_paths.add(key)
                raw_paths.append(path)
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
                ]
                external_objectives = _bounded_external_objectives(
                    market, external_objectives, as_of, float(decision_close)
                )
                internal_objectives = [
                    item for item in directional
                    if split_bar_id(str(item["barId"]))[0] == "M15"
                ]
            else:
                authority_low = float(authority["dealingRange"]["low"])
                authority_high = float(authority["dealingRange"]["high"])
                same_owner_direction = family_direction == str(authority["direction"])
                authority_break = (
                    market.bar(str(authority["bodyBreakBarId"]), as_of)
                    if authority.get("bodyBreakBarId") else None
                )
                post_break_delivery = bool(
                    authority_break is not None
                    and int(family_displacement["available"])
                    > int(authority_break["available"])
                )
                protected = authority["protectedSwing"]
                reclaimed_old_boundary = bool(
                    post_break_delivery
                    and (
                        float(family_displacement["close"]) > float(protected["low"])
                        if family_direction == "LONG"
                        else float(family_displacement["close"]) < float(protected["high"])
                    )
                )
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
                    objective_tf = split_bar_id(str(objective["barId"]))[0]
                    if (
                        authority["status"] == "OBJECTIVE_REACHED"
                        and objective_tf == "M15"
                    ):
                        # The fulfilled authority still owns the external map,
                        # but its old range cannot suppress a fresh current-
                        # range internal rotation. The later range-pair pass
                        # binds this M15 pool to the candidate's own dealing
                        # range and selects only the nearest eligible target.
                        internal_objectives.append(objective)
                        continue
                    is_frozen_external = bool(
                        same_owner_direction
                        and isinstance(frozen_objective, dict)
                        and str(objective["barId"]) == str(frozen_objective.get("barId"))
                    )
                    is_newer_external_checkpoint = bool(
                        authority["status"] == "ACTIVE"
                        and same_owner_direction
                        and isinstance(frozen_objective, dict)
                        and _is_nearer_same_owner_external_objective(
                            family_direction,
                            frozen_objective,
                            objective,
                            float(decision_close),
                        )
                        and (
                            not objective.get("matureAtUtc")
                            or parse_utc(str(objective["matureAtUtc"]))
                            > parse_utc(str(authority["establishedAtUtc"]))
                        )
                    )
                    if is_newer_external_checkpoint:
                        external_objectives.append(objective)
                        continue
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
                        # An intact owner remains binding, but completing its
                        # former external objective does not forbid a newly
                        # formed internal rotation inside a fresh causal range.
                        # The option's own dealing-range pair and first M15
                        # objective still have to pass freeze-time validation.
                        if (
                            authority["status"] in {"ACTIVE", "OBJECTIVE_REACHED"}
                            and split_bar_id(str(objective["barId"]))[0]
                            in {"H1", "M30", "M15"}
                        ):
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
                    elif authority["status"] == "REMAP_REQUIRED":
                        if not post_break_delivery:
                            continue
                        if same_owner_direction and reclaimed_old_boundary:
                            external_objectives.append(externalized)
                        elif not same_owner_direction:
                            reversal_objectives.append(externalized)
                external_objectives = _bounded_external_objectives(
                    market, external_objectives, as_of, float(decision_close)
                )
                reversal_objectives = _bounded_external_objectives(
                    market, reversal_objectives, as_of, float(decision_close)
                )

            external_by_id = {
                str(objective["barId"]): objective
                for objective in external_objectives
            }
            reversal_by_id = {
                str(objective["barId"]): objective
                for objective in reversal_objectives
            }
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
                    range_specs: list[tuple[str, dict[str, Any], str]] = []
                    range_low_price = float(range_pair["low"])
                    range_high_price = float(range_pair["high"])
                    if authority and authority["status"] == "ACTIVE":
                        # The authority range is already frozen. A newly mature
                        # nearer checkpoint can sit inside that range while the
                        # original external objective remains the final family
                        # member; it must not be discarded by a fresh-range
                        # boundary test.
                        eligible_external = list(external_by_id.values())
                    else:
                        eligible_external = [
                            objective for objective in external_by_id.values()
                            if (
                                float(objective["price"])
                                >= range_high_price - market.point / 2.0
                                if family_direction == "LONG"
                                else float(objective["price"])
                                <= range_low_price + market.point / 2.0
                            )
                        ]
                    eligible_reversal = [
                        objective for objective in reversal_by_id.values()
                        if (
                            float(objective["price"]) >= range_high_price - market.point / 2.0
                            if family_direction == "LONG"
                            else float(objective["price"]) <= range_low_price + market.point / 2.0
                        )
                    ]
                    range_specs.extend(
                        ("EXTERNAL_CONTINUATION", objective, "EXTERNAL_SWING")
                        for objective in eligible_external
                    )
                    range_specs.extend(
                        ("EXTERNAL_REVERSAL", objective, "EXTERNAL_SWING")
                        for objective in eligible_reversal
                    )
                    eligible_internal = [
                        item for item in internal_objectives
                        if range_low_price <= float(item["price"]) <= range_high_price
                        and (
                            child_proximal < float(item["price"])
                            if family_direction == "LONG"
                            else float(item["price"]) < child_proximal
                        )
                    ]
                    if eligible_internal:
                        nearest_internal = min(
                            eligible_internal,
                            key=lambda item: abs(
                                float(item["price"]) - child_proximal
                            ),
                        )
                        range_specs.append((
                            "INTERNAL_ROTATION", nearest_internal, "INTERNAL_SWING"
                        ))
                    for scope, objective_candidate, objective_kind in range_specs:
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
                                str(item["barId"]) for item in internal_between
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
                                "matureAtUtc": objective_candidate.get("matureAtUtc"),
                                "maturityBarId": objective_candidate.get("maturityBarId"),
                                "destinationContext": objective_candidate.get(
                                    "destinationContext"
                                ),
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
                            "reason": (
                                "engine-enumerated structural option requiring independent semantic approval"
                            ),
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
            family["scenarioOptions"] = _collapse_scenario_objective_families(
                market, as_of, family_id, scenario_options
            )
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


def _collapse_scenario_objective_families(
    market: MarketData,
    as_of: int,
    family_id: str,
    options: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Freeze one ordered destination family per owner/scope/lineage route."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for option in options:
        route_keys = [
            "direction", "scope", "ownerBreakTargetBarId", "ownerBreakBarId",
            "lineagePathSelectionId",
        ]
        if option.get("scope") == "INTERNAL_ROTATION":
            route_keys.extend(("dealingRange", "mapProtectedSwingBarId"))
        route = {key: option.get(key) for key in route_keys}
        grouped.setdefault(canonical_hash(route), []).append(option)

    collapsed: list[dict[str, Any]] = []
    for route_hash, variants in grouped.items():
        first = variants[0]
        direction = str(first["direction"])
        members_by_level: dict[tuple[str, int], dict[str, Any]] = {}
        for variant in variants:
            objective = dict(variant["objective"])
            price = float(objective.get("price") or 0.0)
            if price == 0.0:
                # The exact wick is intentionally resolved from the supplied ID.
                objective_bar = market.bar(str(objective["barId"]), as_of)
                price = float(
                    objective_bar["high"] if direction == "LONG" else objective_bar["low"]
                )
                objective["price"] = price
            key = (str(objective["side"]), round(price / market.point))
            previous = members_by_level.get(key)
            if previous is None:
                members_by_level[key] = objective
                continue
            previous_tf = split_bar_id(str(previous["barId"]))[0]
            current_tf = split_bar_id(str(objective["barId"]))[0]
            if current_tf == "H1" and previous_tf != "H1":
                members_by_level[key] = objective
        members = sorted(
            members_by_level.values(),
            key=lambda item: (
                float(item["price"]) if direction == "LONG" else -float(item["price"]),
                split_bar_id(str(item["barId"]))[1],
            ),
        )
        if not members:
            continue
        objective_family_id = "objective-family-" + canonical_hash(
            {
                "familyId": family_id,
                "route": route_hash,
                "members": [str(item["barId"]) for item in members],
            }
        )[:16]
        body = {
            key: first[key]
            for key in (
                "direction", "scope", "dealingRange", "mapProtectedSwingBarId",
                "ownerBreakTargetBarId", "ownerBreakBarId", "lineagePathSelectionId",
            )
        }
        body["objectiveFamily"] = {
            "objectiveFamilyId": objective_family_id,
            "orderedMembers": members,
        }
        # Compatibility field for legacy readers. Order creation never trusts
        # this provisional member; it runs select_objective_from_family().
        body["objective"] = members[0]
        provisional_bar_id = str(members[0]["barId"])
        provisional_variant = next(
            variant
            for variant in variants
            if str(variant["objective"]["barId"]) == provisional_bar_id
        )
        # This compatibility field must describe the compatibility objective
        # only. The execution path recomputes intermediate delivery after it
        # selects the first still-live member with planned R >= 1.
        body["intermediateLiquidityBarIds"] = list(dict.fromkeys(
            provisional_variant.get("intermediateLiquidityBarIds", [])
        ))
        collapsed.append({
            "scenarioSelectionId": "scenario-" + canonical_hash(
                {"familyId": family_id, **body}
            )[:16],
            **body,
        })
    return collapsed


def _confirmed_liquidity_swings(
    market: MarketData,
    as_of: int,
    *,
    active_only: bool = False,
) -> list[dict[str, Any]]:
    """Return the permanent, as-of-safe liquidity event ledger.

    A level is recognized after two completed reaction candles.  Only one
    left-hand comparison is required, so protected structure is not restricted
    to a mechanical two-left/two-right pivot.  Classification and lifecycle
    timestamps remain separate from the origin candle to prevent look-ahead.
    """
    asof_key = (market.cache_token, int(as_of), bool(active_only))
    cached_asof = _CONFIRMED_LIQUIDITY_ASOF_CACHE.get(asof_key)
    if cached_asof is not None:
        return cached_asof
    candidates: list[dict[str, Any]] = []
    for timeframe in LIQUIDITY_LIMITS:
        series = market.frames[timeframe]
        cache_key = (market.cache_token, timeframe)
        timeframe_candidates = _LIQUIDITY_EVENT_CACHE.get(cache_key)
        if timeframe_candidates is None:
            timeframe_candidates = []
            prior_by_side: dict[str, list[tuple[float, int, dict[str, Any]]]] = {
                "HIGH": [], "LOW": []
            }
            latest_opposite: dict[str, int | None] = {"HIGH": None, "LOW": None}
            root_episodes = {
                (str(item["rootBarId"]), str(item["direction"])): item
                for item in mechanical_root_candidates(
                    market, int(series.available_time[-1]), maximum=None,
                    timeframe_limits={timeframe: LIQUIDITY_LIMITS[timeframe]},
                )
            }
            for index in range(2, len(series.time) - 2):
                left = slice(index - 2, index)
                right = slice(index + 1, index + 3)
                is_high = (
                    float(series.high[index]) > float(np.max(series.high[left]))
                    and float(series.high[index]) >= float(np.max(series.high[right]))
                )
                is_low = (
                    float(series.low[index]) < float(np.min(series.low[left]))
                    and float(series.low[index]) <= float(np.min(series.low[right]))
                )
                for side, matched in (("HIGH", is_high), ("LOW", is_low)):
                    if not matched:
                        continue
                    price = float(
                        series.high[index] if side == "HIGH" else series.low[index]
                    )
                    wick_near_body = float(
                        max(series.open[index], series.close[index])
                        if side == "HIGH"
                        else min(series.open[index], series.close[index])
                    )
                    ordered_prior = prior_by_side[side]
                    insertion = bisect.bisect_left(
                        ordered_prior, (price, int(series.time[index]), {})
                    )
                    nearby = ordered_prior[
                        max(0, insertion - 8):min(len(ordered_prior), insertion + 8)
                    ]
                    previous_overlaps = [
                        prior_item for _, _, prior_item in nearby
                        if (
                            min(price, wick_near_body)
                            <= max(float(prior_item["price"]), float(prior_item["wickNearBody"]))
                            and max(price, wick_near_body)
                            >= min(float(prior_item["price"]), float(prior_item["wickNearBody"]))
                        )
                    ]
                    previous_overlap = previous_overlaps[-1] if previous_overlaps else None
                    opposite_side = "LOW" if side == "HIGH" else "HIGH"
                    alternating_reaction = bool(
                        previous_overlap is not None
                        and latest_opposite[opposite_side] is not None
                        and split_bar_id(str(previous_overlap["barId"]))[1]
                        < int(latest_opposite[opposite_side])
                        < int(series.time[index])
                    )
                    direction = "SHORT" if side == "HIGH" else "LONG"
                    root_episode = root_episodes.get(
                        (bar_id(timeframe, int(series.time[index])), direction)
                    )
                    kind_maturities = {
                        "RAW_SWING": utc_text(int(series.available_time[index + 2]))
                    }
                    if previous_overlaps:
                        kind_maturities["REPEATED_DEFENSE"] = utc_text(
                            int(series.available_time[index + 2])
                        )
                    if alternating_reaction:
                        kind_maturities["RANGE_EDGE"] = utc_text(
                            int(series.available_time[index + 2])
                        )
                    if root_episode is not None:
                        displacement_available = market.bar(
                            str(root_episode["displacementBarId"]),
                            int(series.available_time[-1]),
                        )["available"]
                        kind_maturities["REACTION_TRAP"] = utc_text(
                            max(
                                int(series.available_time[index + 2]),
                                int(displacement_available),
                            )
                        )
                    item = {
                        "barId": bar_id(timeframe, int(series.time[index])),
                        "timeframe": timeframe,
                        "side": side,
                        "price": price,
                        "wickNearBody": wick_near_body,
                        "matureAtUtc": utc_text(int(series.available_time[index + 2])),
                        "maturityBarId": bar_id(
                            timeframe, int(series.time[index + 2])
                        ),
                        "kindMaturities": kind_maturities,
                        "overlapBarIds": [
                            str(item["barId"]) for item in previous_overlaps[-8:]
                        ],
                        "reactionEpisodeId": (
                            canonical_hash(root_episode)[:20]
                            if root_episode is not None else None
                        ),
                    }
                    timeframe_candidates.append(item)
                    latest_opposite[side] = int(series.time[index])
                    bisect.insort(
                        prior_by_side[side],
                        (price, int(series.time[index]), item),
                    )
            _LIQUIDITY_EVENT_CACHE[cache_key] = timeframe_candidates
        for cached in timeframe_candidates:
            mature_at = cached.get("_matureEpoch")
            if mature_at is None:
                mature_at = parse_utc(str(cached["matureAtUtc"]))
                cached["_matureEpoch"] = mature_at
            if int(mature_at) > int(as_of):
                continue
            origin_available = cached.get("_originAvailable")
            if origin_available is None:
                origin_available = market.bar(
                    str(cached["barId"]), as_of
                )["available"]
                cached["_originAvailable"] = origin_available
            resolution_key = (
                market.cache_token, str(cached["barId"]), str(cached["side"]),
                round(float(cached["price"]) / market.point),
            )
            resolution = _LIQUIDITY_RESOLUTION_CACHE.get(resolution_key)
            if resolution is None:
                times = _m1_times(market)
                left = int(np.searchsorted(times, int(mature_at), side="left"))
                price = float(cached["price"])
                resolution = (None, None)
                for block_left in range(left, len(market.rates), 4096):
                    block_right = min(len(market.rates), block_left + 4096)
                    if cached["side"] == "HIGH":
                        touched = np.asarray(
                            market.rates["high"][block_left:block_right], dtype=float
                        ) >= price
                        invalid = np.asarray(
                            market.rates["close"][block_left:block_right], dtype=float
                        ) > price
                    else:
                        touched = np.asarray(
                            market.rates["low"][block_left:block_right], dtype=float
                        ) <= price
                        invalid = np.asarray(
                            market.rates["close"][block_left:block_right], dtype=float
                        ) < price
                    indexes = np.flatnonzero(touched | invalid)
                    if not len(indexes):
                        continue
                    offset = int(indexes[0])
                    resolved_index = block_left + offset
                    resolution = (
                        int(market.rates[resolved_index]["time"]) + 60,
                        "INVALIDATED" if bool(invalid[offset]) else "CONSUMED",
                    )
                    break
                _LIQUIDITY_RESOLUTION_CACHE[resolution_key] = resolution
            resolved_at, resolved_state = resolution
            if active_only and resolved_at is not None and resolved_at <= int(as_of):
                continue
            if resolved_at is not None and resolved_at > int(as_of):
                resolved_at, resolved_state = None, None
            item = {
                key: value for key, value in cached.items()
                if not str(key).startswith("_")
            }
            item["liquidityKinds"] = [
                kind for kind, known_at in item.get("kindMaturities", {}).items()
                if parse_utc(str(known_at)) <= int(as_of)
            ]
            resolved_by = (
                bar_id("M1", int(resolved_at) - 60) if resolved_at is not None else None
            )
            item.update({
                "formedAtUtc": utc_text(int(origin_available)),
                "state": resolved_state or "ACTIVE",
                "consumedAtUtc": utc_text(resolved_at)
                if resolved_state == "CONSUMED" else None,
                "consumedByBarId": resolved_by
                if resolved_state == "CONSUMED" else None,
                "invalidatedAtUtc": utc_text(resolved_at)
                if resolved_state == "INVALIDATED" else None,
                "invalidatedByBarId": resolved_by
                if resolved_state == "INVALIDATED" else None,
            })
            candidates.append(item)
    candidates.sort(
        key=lambda item: (
            parse_utc(str(item["matureAtUtc"])),
            split_bar_id(str(item["barId"]))[1],
        )
    )
    _CONFIRMED_LIQUIDITY_ASOF_CACHE[asof_key] = candidates
    if len(_CONFIRMED_LIQUIDITY_ASOF_CACHE) > 64:
        del _CONFIRMED_LIQUIDITY_ASOF_CACHE[
            next(iter(_CONFIRMED_LIQUIDITY_ASOF_CACHE))
        ]
    return candidates


def _confirmed_long_history_h1_swings(
    market: MarketData,
    as_of: int,
) -> list[dict[str, Any]]:
    """Return all mature H1 swings for destination fallback only."""
    series = market.frames["H1"]
    right = int(np.searchsorted(series.available_time, as_of, side="right"))
    if right <= 0:
        return []
    cache_key = (
        market.cache_token,
        right,
        int(series.available_time[right - 1]),
    )
    cached = _H1_LIQUIDITY_SWING_CACHE.get(cache_key)
    if cached is not None:
        return cached
    candidates: list[dict[str, Any]] = []
    for index in range(2, right - 2):
        origin_high = float(series.high[index])
        origin_low = float(series.low[index])
        is_high = (
            origin_high > float(np.max(series.high[index - 2:index]))
            and origin_high >= float(np.max(series.high[index + 1:index + 3]))
        )
        is_low = (
            origin_low < float(np.min(series.low[index - 2:index]))
            and origin_low <= float(np.min(series.low[index + 1:index + 3]))
        )
        origin_bar_id = bar_id("H1", int(series.time[index]))
        maturity_at = int(series.available_time[index + 2])
        maturity_bar_id = bar_id("H1", int(series.time[index + 2]))
        if is_high:
            candidates.append({
                "barId": origin_bar_id, "timeframe": "H1", "side": "HIGH",
                "price": origin_high,
                "matureAtUtc": utc_text(maturity_at),
                "maturityBarId": maturity_bar_id,
            })
        if is_low:
            candidates.append({
                "barId": origin_bar_id, "timeframe": "H1", "side": "LOW",
                "price": origin_low,
                "matureAtUtc": utc_text(maturity_at),
                "maturityBarId": maturity_bar_id,
            })
    _H1_LIQUIDITY_SWING_CACHE[cache_key] = candidates
    if len(_H1_LIQUIDITY_SWING_CACHE) > 256:
        del _H1_LIQUIDITY_SWING_CACHE[next(iter(_H1_LIQUIDITY_SWING_CACHE))]
    return candidates


def _external_objective_context(
    market: MarketData,
    objective: dict[str, Any],
    as_of: int,
    decision_close: float,
) -> dict[str, Any]:
    origin = market.bar(str(objective["barId"]), as_of)
    age_days = max(0.0, (int(as_of) - int(origin["time"])) / 86400.0)
    recent_h1 = market.bars("H1", as_of, LIQUIDITY_LIMITS["H1"])
    recent_high = max((float(row["high"]) for row in recent_h1), default=decision_close)
    recent_low = min((float(row["low"]) for row in recent_h1), default=decision_close)
    side = str(objective["side"])
    price = float(objective["price"])
    return {
        "originTimeUtc": utc_text(int(origin["time"])),
        "ageDays": round(age_days, 2),
        "historyTier": (
            "LONG_TERM_H1"
            if origin["tf"] == "H1" and age_days >= LONG_TERM_H1_DAYS
            else "CURRENT_STRUCTURE"
        ),
        "distanceFromDecision": round(abs(price - float(decision_close)), 5),
        "beyondRecentH1Range": (
            price > recent_high if side == "HIGH" else price < recent_low
        ),
        "recentH1Range": {
            "high": round(recent_high, 5),
            "low": round(recent_low, 5),
        },
    }


def _bounded_external_objectives(
    market: MarketData,
    candidates: list[dict[str, Any]],
    as_of: int,
    decision_close: float,
) -> list[dict[str, Any]]:
    """Return current objectives plus at most two long-term H1 fallbacks.

    Current H1/M30 structure is never truncated here. Distant history is not
    a competing primary target: only the two nearest unconsumed H1 levels are
    retained for deterministic fallback when every current objective is below
    1R after executable entry and stop geometry is known. Old M30 levels are
    not eligible as long-history fallback.
    """
    eligible = [
        dict(item)
        for item in candidates
        if split_bar_id(str(item["barId"]))[0] in {"H1", "M30"}
    ]
    eligible.sort(
        key=lambda item: (
            abs(float(item["price"]) - float(decision_close)),
            0 if split_bar_id(str(item["barId"]))[0] == "H1" else 1,
            split_bar_id(str(item["barId"]))[1],
        )
    )
    enriched: list[dict[str, Any]] = []
    for item in eligible:
        item["destinationContext"] = _external_objective_context(
            market, item, as_of, decision_close
        )
        enriched.append(item)

    deduplicated: dict[tuple[str, int], dict[str, Any]] = {}
    for item in enriched:
        key = (str(item["side"]), round(float(item["price"]) / market.point))
        previous = deduplicated.get(key)
        if previous is None:
            deduplicated[key] = item
            continue
        previous_tf = split_bar_id(str(previous["barId"]))[0]
        item_tf = split_bar_id(str(item["barId"]))[0]
        if item_tf == "H1" and previous_tf != "H1":
            deduplicated[key] = item
    current = sorted(
        (
            item for item in deduplicated.values()
            if float(item["destinationContext"]["ageDays"])
            < LONG_TERM_H1_DAYS
        ),
        key=lambda item: (
            abs(float(item["price"]) - float(decision_close)),
            0 if split_bar_id(str(item["barId"]))[0] == "H1" else 1,
            split_bar_id(str(item["barId"]))[1],
        ),
    )
    historical_h1 = sorted(
        (
            item for item in deduplicated.values()
            if split_bar_id(str(item["barId"]))[0] == "H1"
            and float(item["destinationContext"]["ageDays"])
            >= LONG_TERM_H1_DAYS
        ),
        key=lambda item: (
            abs(float(item["price"]) - float(decision_close)),
            split_bar_id(str(item["barId"]))[1],
        ),
    )
    return current + historical_h1[:MAX_LONG_TERM_H1_FALLBACK_OBJECTIVES]


def _live_directional_liquidity(
    market: MarketData,
    as_of: int,
    direction: str,
    *,
    range_low: float | None = None,
    range_high: float | None = None,
    from_price: float | None = None,
    to_price: float | None = None,
) -> list[dict[str, Any]]:
    """Return mature, unconsumed liquidity in directional price order."""
    cache_key = (
        market.cache_token, int(as_of), str(direction), range_low, range_high,
        from_price, to_price,
    )
    cached = _LIVE_LIQUIDITY_QUERY_CACHE.get(cache_key)
    if cached is not None:
        return cached
    side = "HIGH" if direction == "LONG" else "LOW"
    filtered: list[dict[str, Any]] = []
    for swing in _confirmed_liquidity_swings(market, as_of, active_only=True):
        if swing["side"] != side:
            continue
        price = float(swing["price"])
        if range_low is not None and price < float(range_low):
            continue
        if range_high is not None and price > float(range_high):
            continue
        if from_price is not None:
            if direction == "LONG" and price <= float(from_price):
                continue
            if direction == "SHORT" and price >= float(from_price):
                continue
        if to_price is not None:
            if direction == "LONG" and price >= float(to_price):
                continue
            if direction == "SHORT" and price <= float(to_price):
                continue
        filtered.append(dict(swing))

    # All candidates share one as-of boundary. Build one suffix-extreme array
    # instead of rescanning the entire M1 history once per liquidity swing.
    output: list[dict[str, Any]] = []
    if filtered:
        times = _m1_times(market)
        right = int(np.searchsorted(times, int(as_of) - 60, side="right"))
        origins = [market.bar(str(item["barId"]), as_of) for item in filtered]
        lefts = [
            int(np.searchsorted(times, int(origin["available"]), side="left"))
            for origin in origins
        ]
        base = min(lefts)
        if side == "HIGH":
            extremes = np.maximum.accumulate(
                np.asarray(market.rates["high"][base:right], dtype=float)[::-1]
            )[::-1]
        else:
            extremes = np.minimum.accumulate(
                np.asarray(market.rates["low"][base:right], dtype=float)[::-1]
            )[::-1]
        for swing, left in zip(filtered, lefts):
            if left >= right:
                output.append(swing)
                continue
            consumed = (
                float(extremes[left - base]) >= float(swing["price"])
                if side == "HIGH" else
                float(extremes[left - base]) <= float(swing["price"])
            )
            if not consumed:
                output.append(swing)

    timeframe_rank = {"H1": 0, "M30": 1, "M15": 2, "M5": 3}
    by_price: dict[int, dict[str, Any]] = {}
    for item in output:
        key = round(float(item["price"]) / market.point)
        existing = by_price.get(key)
        if existing is None:
            by_price[key] = item
            continue
        item_rank = timeframe_rank[split_bar_id(str(item["barId"]))[0]]
        existing_rank = timeframe_rank[split_bar_id(str(existing["barId"]))[0]]
        if item_rank < existing_rank:
            by_price[key] = item
    anchor = float(from_price) if from_price is not None else market.bars("M1", as_of, 1)[-1]["close"]
    result = sorted(
        by_price.values(),
        key=lambda item: (
            abs(float(item["price"]) - anchor),
            parse_utc(str(item["matureAtUtc"])),
        ),
    )
    _LIVE_LIQUIDITY_QUERY_CACHE[cache_key] = result
    if len(_LIVE_LIQUIDITY_QUERY_CACHE) > 4096:
        _LIVE_LIQUIDITY_QUERY_CACHE.clear()
        _LIVE_LIQUIDITY_QUERY_CACHE[cache_key] = result
    return result


def _map_evidence(
    market: MarketData,
    as_of: int,
    candidates: list[dict[str, Any]],
    include_full_liquidity_ledger: bool = True,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return neutral selectable evidence without authorizing any market meaning."""
    selected: dict[str, dict[str, dict[str, Any]]] = {
        timeframe: {} for timeframe in LIQUIDITY_LIMITS
    }
    # The complete ledger is required for protected swings that are consumed
    # by the very displacement being evaluated. Objective selection below
    # independently admits only still-live levels.
    swing_candidates = (
        _confirmed_liquidity_swings(market, as_of)
        if include_full_liquidity_ledger else []
    )

    for timeframe, limit in LIQUIDITY_LIMITS.items():
        rows = market.bars(timeframe, as_of, limit)
        recent = LIQUIDITY_RECENT_EVIDENCE[timeframe]
        for row in rows[-recent:]:
            selected[timeframe][row["barId"]] = row
        timeframe_swings = [
            item for item in swing_candidates if item["timeframe"] == timeframe
        ]
        for swing in timeframe_swings[-LIQUIDITY_SWING_EVIDENCE[timeframe]:]:
            row = market.bar(str(swing["barId"]), as_of)
            selected[timeframe][row["barId"]] = row

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
    for timeframe in LIQUIDITY_LIMITS:
        ordered = sorted(selected[timeframe].values(), key=lambda item: item["time"])
        data[timeframe] = [
            [
                row["barId"], utc_text(row["time"]), round(row["open"], 5),
                round(row["high"], 5), round(row["low"], 5), round(row["close"], 5),
                round(row["spreadPoints"], 2),
            ]
            for row in ordered
        ]
    return {"columns": columns, "data": data}, swing_candidates


def build_plan_packet(
    market: MarketData,
    as_of: int,
    symbol: str,
    focus_family_ids: set[str] | None = None,
    external_authority: dict[str, Any] | None = None,
    approach_event: dict[str, Any] | None = None,
    approach_events: list[dict[str, Any]] | None = None,
    candidate_context: list[dict[str, Any]] | None = None,
    focus_root_bar_ids: set[str] | None = None,
    focus_objective_bar_ids: set[str] | None = None,
    fixed_objective_members: list[dict[str, Any]] | None = None,
    fixed_dealing_range: dict[str, Any] | None = None,
    minimal_lineage_audit: bool = False,
    decision_bar_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Build one compact semantic packet for map, root, and causal refinement."""
    # A focused request can happen long after a root formed. Scan the full local
    # HTF window so a queued untouched root does not disappear merely because
    # newer mechanical candidates were created while price was away from it.
    active_root_candidates = mechanical_root_candidates(
        market,
        as_of,
        maximum=None,
        active_only=True,
        focus_root_bar_ids=focus_root_bar_ids,
    )
    if focus_root_bar_ids is not None:
        active_root_candidates = [
            item for item in active_root_candidates
            if str(item["rootBarId"]) in focus_root_bar_ids
        ]
    evidence, swing_candidates = _map_evidence(
        market, as_of, active_root_candidates,
        include_full_liquidity_ledger=not minimal_lineage_audit,
    )
    child_candidates: list[dict[str, Any]] = []
    if focus_root_bar_ids is None:
        for timeframe in ("M30", "M15", "M5"):
            child_candidates.extend(
                mechanical_root_candidates(
                    market,
                    as_of,
                    maximum=None,
                    timeframe_limits={timeframe: PLAN_LIMITS[timeframe]},
                    active_only=True,
                )
            )
    if focus_root_bar_ids is not None:
        parent_windows: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
        for candidate in active_root_candidates:
            parent_root = market.bar(str(candidate["rootBarId"]), as_of)
            parent_episode_end = market.bar(
                str(candidate["displacementEpisodeEndBarId"]), as_of
            )
            parent_windows.append(
                (str(candidate["direction"]), parent_root, parent_episode_end)
            )
        child_time_ranges = [
            (int(parent_root["time"]), int(parent_episode_end["available"]))
            for _, parent_root, parent_episode_end in parent_windows
        ]
        child_candidates = []
        for timeframe in ("M30", "M15", "M5"):
            child_candidates.extend(
                mechanical_root_candidates(
                    market,
                    as_of,
                    maximum=None,
                    timeframe_limits={timeframe: PLAN_LIMITS[timeframe]},
                    active_only=True,
                    root_time_ranges=child_time_ranges,
                )
            )
        compatible_child_candidates: list[dict[str, Any]] = []
        for child_candidate in child_candidates:
            child_root = market.bar(str(child_candidate["rootBarId"]), as_of)
            for direction, parent_root, parent_episode_end in parent_windows:
                if str(child_candidate["direction"]) != direction:
                    continue
                inside_parent_candle = (
                    parent_root["time"]
                    <= child_root["time"]
                    < parent_root["available"]
                )
                overlaps_parent_event = (
                    parent_root["time"]
                    <= child_root["time"]
                    < parent_episode_end["available"]
                    and child_root["high"] >= parent_root["low"]
                    and child_root["low"] <= parent_root["high"]
                )
                if inside_parent_candle or overlaps_parent_event:
                    compatible_child_candidates.append(child_candidate)
                    break
        child_candidates = compatible_child_candidates
    active_child_candidates = child_candidates
    lineage_families = _physical_lineage_families(
        market,
        as_of,
        active_root_candidates,
        active_child_candidates,
        swing_candidates,
        external_authority,
        focus_objective_bar_ids,
        fixed_objective_members,
        fixed_dealing_range,
    )
    if focus_root_bar_ids is not None:
        lineage_families = [
            family for family in lineage_families
            if str(family["rootBarId"]) in focus_root_bar_ids
        ]
    if focus_family_ids is not None:
        lineage_families = [
            family for family in lineage_families
            if str(family["familyId"]) in focus_family_ids
        ]
    if decision_bar_ids is not None:
        decision_ids = set(decision_bar_ids)
        decision_families: list[dict[str, Any]] = []
        for family in lineage_families:
            filtered = [
                option for option in family.get("scenarioOptions", [])
                if _nested_bar_ids(option) <= decision_ids
            ]
            if not filtered:
                continue
            family = dict(family)
            family["scenarioOptions"] = filtered
            decision_families.append(family)
        lineage_families = decision_families
    family_bar_ids = _nested_bar_ids(lineage_families)

    selected_m5: dict[str, dict[str, Any]] = {
        row["barId"]: row for row in market.bars("M5", as_of, 20)
    }
    for candidate in [*active_root_candidates, *active_child_candidates]:
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
    decision_bar = market.bars("M5", as_of, 1)[-1]
    execution_bar = market.bars("M1", as_of, 1)[-1]
    packet_swing_candidates = [
        swing for swing in swing_candidates if swing["state"] == "ACTIVE"
    ]
    if focus_family_ids is not None or focus_root_bar_ids is not None:
        focused_ids = set(family_bar_ids)
        focused_ids.add(decision_bar["barId"])
        # The semantic choice remains HTF/M5-only, but current map and delivery
        # context must survive focus filtering. The old focused packet retained
        # almost only formation candles, so the model could not tell whether
        # price was now approaching the POI or had already delivered away.
        for timeframe, count in (("H1", 36), ("M30", 48), ("M15", 48), ("M5", 48)):
            focused_ids.update(
                row["barId"] for row in market.bars(timeframe, as_of, count)
            )
        evidence["data"] = {
            timeframe: [
                row for row in rows
                if str(row[0]) in focused_ids
            ]
            for timeframe, rows in evidence["data"].items()
        }
        packet_swing_candidates = [
            swing for swing in packet_swing_candidates
            if str(swing["barId"]) in focused_ids
        ]
    authority = resolved_external_authority(market, external_authority, as_of)
    root_counts = mechanical_root_event_counts(
        market, as_of, ("H1", "M30", "M15")
    )
    child_counts = mechanical_root_event_counts(
        market, as_of, ("M30", "M15", "M5")
    )
    active_root_counts = {
        timeframe: sum(
            1 for item in active_root_candidates if item["timeframe"] == timeframe
        )
        for timeframe in ("H1", "M30", "M15")
    }
    active_child_counts = {
        timeframe: sum(
            1 for item in active_child_candidates if item["timeframe"] == timeframe
        )
        for timeframe in ("M30", "M15", "M5")
    }
    if lineage_families:
        no_family_reason = None
    elif not active_root_candidates:
        no_family_reason = "NO_MECHANICAL_ROOT"
    elif not active_child_candidates:
        no_family_reason = "NO_CHILD_CANDIDATE"
    elif authority and authority.get("status") == "REMAP_REQUIRED":
        no_family_reason = "REMAP_HAS_NO_CONFIRMED_POST_BREAK_FAMILY"
    else:
        no_family_reason = "NO_CAUSAL_LINEAGE_OR_OBJECTIVE"
    return {
        "pipelineVersion": PIPELINE_VERSION,
        "phase": "PLAN",
        "symbol": symbol,
        "asOfUtc": utc_text(as_of),
        "allowedTimeframes": ["H1", "M30", "M15", "M5"],
        "m1ExcludedFromSemanticStructure": True,
        "decisionReference": {
            "barId": decision_bar["barId"],
            "timeUtc": utc_text(decision_bar["time"]),
            "availableUtc": utc_text(decision_bar["available"]),
            "close": decision_bar["close"],
        },
        "executionReference": {
            "role": "ENGINE_CLOCK_ONLY_NOT_TRIGGER_EVIDENCE",
            "barId": execution_bar["barId"],
            "timeUtc": utc_text(execution_bar["time"]),
            "availableUtc": utc_text(execution_bar["available"]),
            "open": execution_bar["open"],
            "high": execution_bar["high"],
            "low": execution_bar["low"],
            "close": execution_bar["close"],
        },
        "approachEvent": approach_event,
        "approachEvents": approach_events or ([approach_event] if approach_event else []),
        "candidateLifecycleContext": candidate_context or [],
        "focusReason": (
            "ROOT_APPROACH" if approach_event is not None
            else "FAMILY_FORMATION" if focus_family_ids is not None
            else "GLOBAL_REVIEW"
        ),
        "focusedRootApproach": approach_event is not None,
        "focusedFamilyFormation": (
            focus_family_ids is not None and approach_event is None
        ),
        "focusedFamilyIds": sorted(focus_family_ids or []),
        "externalMapAuthority": authority,
        "discoveryDiagnostics": {
            "rootCandidatesByTf": root_counts,
            "activeRootCandidatesByTf": active_root_counts,
            "childCandidatesByTf": child_counts,
            "activeChildCandidatesByTf": active_child_counts,
            "physicalFamilies": len(lineage_families),
            "noFamilyReason": no_family_reason,
            "globalCandidateCapApplied": False,
            "longTermH1FallbackLimit": MAX_LONG_TERM_H1_FALLBACK_OBJECTIVES,
        },
        "externalMapAuthorityBoundary": (
            "A frozen external owner survives trade close, cancellation, and internal rotation. Opposite "
            "EXTERNAL_CONTINUATION is impossible while status is ACTIVE. ACTIVE also freezes the dealing "
            "range, protected swing, and objective. OBJECTIVE_REACHED permits a fresh INTERNAL_ROTATION "
            "inside its own newly frozen causal range or a new same-direction continuation map. "
            "REMAP_REQUIRED archives the broken owner and exposes only a post-break "
            "same-direction reclaim continuation or an opposite EXTERNAL_REVERSAL with the exact recorded "
            "H1/M30 body-break evidence. "
            "H1/M30 liquidity inside the frozen dealing range remains internal; timeframe alone cannot "
            "promote it to an external objective."
            if authority else
            "No external owner has yet been frozen in this run; infer it from the supplied closed HTF chart."
        ),
        "taskBoundary": (
            "Freeze one complete scenario: map, objective, causal root OB, and every causal child OB down "
            "to the last unambiguous causal child on M30, M15, or M5. Do not force a lower timeframe when "
            "it creates competing or unrelated children. M1 trigger structure is unavailable and must not be "
            "inferred. executionReference and optional approachEvent are engine-clock facts. A FAMILY_FORMATION "
            "request occurs when the complete causal family first becomes actionable after displacement, before any "
            "required retest; it must not be rejected merely because price has departed from its source. A "
            "ROOT_APPROACH request verifies that the POI was known before that approach. Root "
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
        "swingCandidates": packet_swing_candidates,
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
    direction = str(scenario["direction"])
    frozen_at = parse_utc(str(scenario["frozenAtUtc"]))
    old_root = scenario["root"]
    focus_roots: set[str] = set()
    for candidate in mechanical_root_candidates(
        market, as_of, maximum=None, active_only=True
    ):
        if str(candidate["direction"]) != direction:
            continue
        root = market.bar(str(candidate["rootBarId"]), as_of)
        if int(root["available"]) <= frozen_at:
            continue
        if (
            float(root["high"]) >= float(old_root["low"])
            and float(root["low"]) <= float(old_root["high"])
        ):
            focus_roots.add(str(candidate["rootBarId"]))
    if not focus_roots:
        return []
    packet = build_plan_packet(
        market,
        as_of,
        symbol,
        external_authority=external_authority_from_scenario(scenario, None),
        focus_root_bar_ids=focus_roots,
    )
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
    cache_key = (
        id(market.rates), int(as_of), str(objective["barId"]),
        str(objective["side"]), float(objective["price"]),
    )
    cached = _OBJECTIVE_CONSUMED_CACHE.get(cache_key)
    if cached is not None:
        return bool(cached)
    origin = market.bar(objective["barId"], as_of)
    times = _m1_times(market)
    left = int(np.searchsorted(times, int(origin["available"]), side="left"))
    right = int(np.searchsorted(times, int(as_of) - 60, side="right"))
    if left >= right:
        _OBJECTIVE_CONSUMED_CACHE[cache_key] = False
        return False
    extrema = _m1_range_extremes(market, left, right)
    if objective["side"] == "HIGH":
        result = bool(extrema["highMax"] >= objective["price"])
    else:
        result = bool(extrema["lowMin"] <= objective["price"])
    _OBJECTIVE_CONSUMED_CACHE[cache_key] = result
    if len(_OBJECTIVE_CONSUMED_CACHE) > 20000:
        _OBJECTIVE_CONSUMED_CACHE.clear()
        _OBJECTIVE_CONSUMED_CACHE[cache_key] = result
    return result


def _node_consumed(market: MarketData, node: dict[str, Any], as_of: int, direction: str) -> bool:
    key = (
        market.cache_token, int(as_of), str(node["obBarId"]),
        str(node["displacementBarId"]), str(direction),
    )
    cached = _NODE_CONSUMED_CACHE.get(key)
    if cached is not None:
        return cached
    displacement = market.bar(node["displacementBarId"], as_of)
    times = _m1_times(market)
    left = int(np.searchsorted(times, int(displacement["available"]), side="left"))
    right = int(np.searchsorted(times, int(as_of) - 60, side="right"))
    rows = market.rates[left:right]
    result = (
        bool(np.any(rows["low"] <= node["distal"]))
        if direction == "LONG"
        else bool(np.any(rows["high"] >= node["distal"]))
    )
    _NODE_CONSUMED_CACHE[key] = result
    return result


def _node_touched_after_delivery(
    market: MarketData, node: dict[str, Any], as_of: int, direction: str
) -> bool:
    key = (
        market.cache_token, int(as_of), str(node["obBarId"]),
        str(node["displacementBarId"]), str(direction),
    )
    cached = _NODE_TOUCHED_CACHE.get(key)
    if cached is not None:
        return cached
    displacement = market.bar(node["displacementBarId"], as_of)
    times = _m1_times(market)
    left = int(np.searchsorted(times, int(displacement["available"]), side="left"))
    right = int(np.searchsorted(times, int(as_of) - 60, side="right"))
    rows = market.rates[left:right]
    result = (
        bool(np.any(rows["low"] <= node["proximal"]))
        if direction == "LONG"
        else bool(np.any(rows["high"] >= node["proximal"]))
    )
    _NODE_TOUCHED_CACHE[key] = result
    return result


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


def _single_objective_family(
    objective: dict[str, Any], scope: str,
) -> dict[str, Any]:
    """Build the canonical one-member family used by every compatibility path."""
    member = dict(objective)
    return {
        "objectiveFamilyId": "objective-family-" + canonical_hash(
            {"scope": str(scope), "members": [str(member["barId"])]}
        )[:16],
        "orderedMembers": [member],
    }


def _canonical_objective_member(
    market: MarketData,
    raw_member: dict[str, Any],
    *,
    as_of: int,
    direction: str,
    scope: str,
    decision_close: float,
) -> dict[str, Any]:
    member_id = str(raw_member["barId"])
    member_bar = market.bar(member_id, as_of)
    side = "HIGH" if direction == "LONG" else "LOW"
    member = {
        "barId": member_id,
        "tf": member_bar["tf"],
        "side": side,
        "kind": str(raw_member.get("kind") or "EXTERNAL_SWING"),
        "price": float(member_bar["high"] if side == "HIGH" else member_bar["low"]),
    }
    if scope in {"EXTERNAL_CONTINUATION", "EXTERNAL_REVERSAL"}:
        member["destinationContext"] = _external_objective_context(
            market, member, as_of, decision_close
        )
    return member


def _atomic_scenario_options(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    keys = (
        "direction", "scope", "dealingRange", "objective", "objectiveFamily",
        "mapProtectedSwingBarId", "ownerBreakTargetBarId", "ownerBreakBarId",
        "lineagePathSelectionId", "intermediateLiquidityBarIds",
    )
    for family in packet.get("physicalLineageFamilies", []):
        for option in family.get("scenarioOptions", []):
            selection_id = str(option["scenarioSelectionId"])
            frozen = {
                key: option[key]
                for key in keys
                if key in option
            }
            if "objectiveFamily" not in frozen:
                objective = dict(option["objective"])
                frozen["objectiveFamily"] = _single_objective_family(
                    objective, str(option["scope"])
                )
            output[selection_id] = frozen
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
    market_price: float,
    owner_break_target_id: str | None,
    owner_break_id: str | None,
) -> None:
    """Make frozen external-map ownership an engine invariant, not model judgment."""
    authority = packet.get("externalMapAuthority") if packet else None
    if not authority:
        return
    supersession = packet.get("activeScenarioSupersession") if packet else None
    if supersession:
        if direction != str(supersession.get("direction")):
            raise V4ContractError("source supersession changed the frozen direction")
        if scope != str(supersession.get("scope")):
            raise V4ContractError("source supersession changed the frozen scenario scope")
        tolerance = float(supersession.get("objectiveTolerancePrice", 0.0))
        objective_price = float(objective["price"])
        old_objective = float(supersession["objectivePrice"])
        market_price = float(supersession.get("marketPrice", old_objective))
        same_objective = abs(objective_price - old_objective) <= tolerance + 1e-9
        newer_external = (
            bool(supersession.get("permitNewerExternalObjective"))
            and scope == "EXTERNAL_CONTINUATION"
            and str(objective.get("kind")) == "EXTERNAL_SWING"
            and str(objective.get("barId", "")).startswith(("H1:", "M30:"))
            and (
                old_objective < objective_price < market_price
                if direction == "SHORT"
                else market_price < objective_price < old_objective
            )
        )
        if not same_objective and not newer_external:
            raise V4ContractError("source supersession changed the physical objective pool")
        if str(authority.get("direction")) != direction:
            raise V4ContractError("source supersession conflicts with the active external owner")
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
            same_objective = bool(
                isinstance(frozen_objective, dict)
                and str(objective["barId"]) == str(frozen_objective["barId"])
            )
            nearer_objective = bool(
                isinstance(frozen_objective, dict)
                and _is_nearer_same_owner_external_objective(
                    direction, frozen_objective, objective, market_price
                )
            )
            if not same_objective and not nearer_objective:
                raise V4ContractError(
                    "same-owner continuation must preserve the active objective or use a nearer H1/M30 external checkpoint"
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
        if scope == "INTERNAL_ROTATION":
            # Candidate construction already binds this objective to the
            # option's fresh dealing range and nearest internal pool. The old
            # fulfilled authority cannot supply a price range for this new
            # internal rotation, so it only constrains external ownership.
            return
        if scope != "EXTERNAL_CONTINUATION":
            raise V4ContractError(
                "fulfilled authority permits a new internal rotation or same-direction external continuation"
            )
        if direction != owner_direction:
            raise V4ContractError(
                "fulfilled authority may advance only in its existing direction"
            )
        return
    if status == "REMAP_REQUIRED":
        # Candidate construction already limits this state to post-break
        # deliveries.  Freeze enforces direction/scope and exact old-owner
        # evidence so a model cannot convert an unresolved map into an internal
        # rotation or a same-direction pseudo reversal.
        if scope == "INTERNAL_ROTATION":
            raise V4ContractError(
                "internal rotation is unavailable while external authority requires remap"
            )
        if scope == "EXTERNAL_CONTINUATION":
            if direction != owner_direction:
                raise V4ContractError(
                    "same-direction owner re-establishment conflicts with the old owner"
                )
            if owner_break_target_id or owner_break_id:
                raise V4ContractError(
                    "same-direction owner re-establishment must not claim reversal evidence"
                )
            return
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
                "PLAN scenarioSelectionId is not a supplied engine-enumerated scenario"
            )
        if packet.get("focusedRootApproach"):
            event = packet.get("approachEvent")
            if not isinstance(event, dict) or not event.get("eligible"):
                raise V4ContractError(
                    "focused PLAN requires one eligible directional M1 approach event"
                )
            if str(event.get("familyId")) not in set(
                packet.get("focusedFamilyIds") or []
            ):
                raise V4ContractError("PLAN approach event does not match focused family")
            known_at = parse_utc(str(event.get("knownAtUtc")))
            event_at = parse_utc(str(event.get("eventAtUtc")))
            if known_at >= event_at or event_at != int(as_of):
                raise V4ContractError(
                    "PLAN POI was not known before the directional approach event"
                )
            if str(event.get("direction")) != str(selected.get("direction")):
                raise V4ContractError("PLAN direction conflicts with the approach event")
            if event.get("approachSide") not in {"FROM_ABOVE", "FROM_BELOW"}:
                raise V4ContractError("PLAN approach side is missing")
            expected_side = (
                "FROM_ABOVE" if selected.get("direction") == "LONG" else "FROM_BELOW"
            )
            if event.get("approachSide") != expected_side:
                raise V4ContractError("PLAN POI was approached from the wrong side")
        elif packet.get("focusedFamilyFormation"):
            family_ids = set(packet.get("focusedFamilyIds") or [])
            selection_id = str(payload.get("scenarioSelectionId"))
            selected_family_id = next(
                (
                    str(family["familyId"])
                    for family in packet.get("physicalLineageFamilies", [])
                    if any(
                        str(option.get("scenarioSelectionId")) == selection_id
                        for option in family.get("scenarioOptions", [])
                    )
                ),
                "",
            )
            if not selected_family_id or selected_family_id not in family_ids:
                raise V4ContractError(
                    "formation PLAN selected a family outside the formation event"
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
    if scope in {"EXTERNAL_CONTINUATION", "EXTERNAL_REVERSAL"}:
        objective["destinationContext"] = _external_objective_context(
            market, objective, as_of, float(latest["close"])
        )
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
        market_price=float(latest["close"]),
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
    if scope == "INTERNAL_ROTATION" and not (
        float(range_low["low"]) <= float(objective["price"])
        <= float(range_high["high"])
    ):
        raise V4ContractError(
            "internal rotation objective must remain inside its selected dealing range"
        )
    # INTERNAL_ROTATION objective ordering is engine-enumerated before this
    # freeze and is revalidated against the live family at order creation.
    # Re-scanning the full permanent liquidity ledger for every atomic option
    # here would be duplicate work, not an independent safety boundary.

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
    raw_family = payload.get("objectiveFamily")
    if raw_family is None:
        objective_family = _single_objective_family(objective, scope)
    else:
        if not isinstance(raw_family, dict):
            raise V4ContractError("objectiveFamily must be an object")
        raw_members = raw_family.get("orderedMembers")
        if not isinstance(raw_members, list) or not raw_members:
            raise V4ContractError("objectiveFamily requires orderedMembers")
        objective_members: list[dict[str, Any]] = []
        seen_objective_ids: set[str] = set()
        for raw_member in raw_members:
            if not isinstance(raw_member, dict) or not raw_member.get("barId"):
                raise V4ContractError("objectiveFamily member is malformed")
            member_id = str(raw_member["barId"])
            if member_id in seen_objective_ids:
                raise V4ContractError("objectiveFamily contains duplicate bar IDs")
            seen_objective_ids.add(member_id)
            objective_members.append(_canonical_objective_member(
                market,
                raw_member,
                as_of=as_of,
                direction=direction,
                scope=scope,
                decision_close=float(latest["close"]),
            ))
        ordered_prices = [float(item["price"]) for item in objective_members]
        expected = sorted(ordered_prices, reverse=direction == "SHORT")
        if ordered_prices != expected:
            raise V4ContractError("objectiveFamily price order is not directional")
        objective_family_id = str(raw_family.get("objectiveFamilyId") or "")
        if not objective_family_id:
            raise V4ContractError("objectiveFamilyId is missing")
        objective_family = {
            "objectiveFamilyId": objective_family_id,
            "orderedMembers": objective_members,
        }
    semantic = {
        "direction": direction,
        "scope": scope,
        "rangeHighBarId": range_high["barId"],
        "rangeLowBarId": range_low["barId"],
        "objective": objective,
        "objectiveFamily": objective_family,
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
        "objectiveFamily": objective_family,
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


def freeze_plan_batch(
    payload: dict[str, Any],
    market: MarketData,
    as_of: int,
    packet: dict[str, Any],
    accepted_hashes: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Validate an exhaustive per-family PLAN page and freeze all approvals."""
    if payload.get("schemaVersion") != "5.0.0":
        scenario = freeze_plan(payload, market, as_of, accepted_hashes, packet)
        return [] if scenario is None else [scenario]
    decisions = payload.get("decisions")
    if not isinstance(decisions, list):
        raise V4ContractError("PLAN 5.0 decisions must be an array")
    packet_families = {
        str(family["familyId"]): family
        for family in packet.get("physicalLineageFamilies", [])
    }
    response_ids = [str(item.get("familyId")) for item in decisions if isinstance(item, dict)]
    if len(response_ids) != len(set(response_ids)):
        raise V4ContractError("PLAN page contains duplicate family decisions")
    if set(response_ids) != set(packet_families):
        missing = sorted(set(packet_families) - set(response_ids))
        extra = sorted(set(response_ids) - set(packet_families))
        raise V4ContractError(
            f"PLAN family-set mismatch missing={missing} extra={extra}"
        )
    frozen: list[dict[str, Any]] = []
    accepted = set(accepted_hashes or set())
    for decision in decisions:
        family_id = str(decision["familyId"])
        selected_id = decision.get("scenarioSelectionId")
        allowed_ids = {
            str(option["scenarioSelectionId"])
            for option in packet_families[family_id].get("scenarioOptions", [])
        }
        if decision.get("action") == "PLAN":
            if str(selected_id) not in allowed_ids:
                raise V4ContractError(
                    f"PLAN selected scenario outside family {family_id}"
                )
        elif decision.get("action") in {"NO_PLAN", "DATA_ERROR"}:
            # A non-trading action has no authority to select a scenario. Some
            # structured-output providers still populate an optional enum field;
            # discard that inert residue instead of sealing an otherwise valid
            # chronological replay. The original response remains in the ledger.
            selected_id = None
        single = {
            "schemaVersion": "4.11.0",
            "action": decision.get("action"),
            "scenarioSelectionId": selected_id,
            "semanticAudit": decision.get("semanticAudit"),
            "reason": decision.get("reason", ""),
        }
        scenario = freeze_plan(single, market, as_of, accepted, packet)
        if scenario is None:
            continue
        scenario["physicalFamilyId"] = family_id
        scenario["planDecisionId"] = canonical_hash(decision)[:20]
        accepted.add(str(scenario["scenarioHash"]))
        frozen.append(scenario)
    return frozen


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
    if correction_candidates is not None and int(correction["time"]) < touch_time:
        raise V4ContractError(
            "M5 correction swing predates the active child-touch reaction episode"
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
        "chochCandidates": [],
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
    choch_existing = {
        str(item["barId"]): item for item in monitor.get("chochCandidates", [])
    }
    recent = market.bars("M1", as_of, 3)
    touch_time = parse_utc(str(scenario["childTouchAtUtc"]))
    if len(recent) == 3:
        previous, candidate, following = recent
        if candidate["time"] >= touch_time:
            if scenario["direction"] == "SHORT":
                pivot = (
                    candidate["low"] < previous["low"]
                    and candidate["low"] <= following["low"]
                    and following["high"] > candidate["high"]
                )
                side, level = "LIVE_LOW", candidate["low"]
            else:
                pivot = (
                    candidate["high"] > previous["high"]
                    and candidate["high"] >= following["high"]
                    and following["low"] < candidate["low"]
                )
                side, level = "LIVE_HIGH", candidate["high"]
            if pivot:
                choch_existing[str(candidate["barId"])] = {
                    "barId": candidate["barId"],
                    "timeUtc": utc_text(candidate["time"]),
                    "side": side,
                    "level": level,
                    "confirmedByBarId": following["barId"],
                }
    choch_ordered = sorted(
        choch_existing.values(), key=lambda item: split_bar_id(str(item["barId"]))[1]
    )[-12:]
    return {
        **monitor,
        "candidates": ordered,
        "chochCandidates": choch_ordered,
    }


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


def reaction_source_episode_end_reason(
    market: MarketData,
    scenario: dict[str, Any],
    monitor: dict[str, Any],
    row: dict[str, Any],
) -> str | None:
    """End a missed child reaction after objective-direction M5 delivery.

    This is event-based, not a timeout. It applies only before any mature sweep
    has completed. A completed M5 correction swing from the touch episode must
    then be body-broken toward the frozen objective. At that point the original
    touch cannot later borrow a trigger from a different reaction episode.
    """
    if monitor.get("sweepEvents") or row["available"] % TIMEFRAME_SECONDS["M5"]:
        return None
    armed_at = parse_utc(str(monitor["armedAtUtc"]))
    candidates = mechanical_m5_correction_swing_candidates(
        market, scenario, int(row["available"])
    )
    eligible: list[dict[str, Any]] = []
    for candidate in candidates:
        swing_time = split_bar_id(str(candidate["barId"]))[1]
        confirmed = market.bar(
            str(candidate["confirmedByBarId"]), int(row["available"])
        )
        if (
            swing_time >= armed_at - TIMEFRAME_SECONDS["M5"]
            and int(confirmed["available"]) > armed_at
        ):
            eligible.append(candidate)
    if not eligible:
        return None
    closed = market.closed_bar_at("M5", int(row["available"]))
    if closed is None:
        return None
    for candidate in eligible:
        broken = (
            float(closed["close"]) > float(candidate["level"])
            if scenario["direction"] == "LONG"
            else float(closed["close"]) < float(candidate["level"])
        )
        if broken:
            return (
                "SOURCE_EPISODE_ENDED_WITHOUT_TRIGGER:"
                + str(candidate["barId"])
            )
    return None


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
    # Trigger correction structure belongs to the active child-touch reaction,
    # not to the older PLAN formation window.
    frozen_at = parse_utc(str(scenario.get("childTouchAtUtc") or scenario["frozenAtUtc"]))
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
    current = market.closed_bar_at("M1", as_of)
    if current is None:
        return []
    previous_rows = market.bars("M1", int(current["time"]), 1)
    previous = previous_rows[-1] if previous_rows else None
    if previous is None:
        return []
    for sweep in sweep_events:
        recovery = market.bar(str(sweep["recoveryBarId"]), as_of)
        for reference_meta in choch_candidates:
            reference = market.bar(str(reference_meta["barId"]), as_of)
            for correction_meta in correction_candidates:
                correction = market.bar(str(correction_meta["barId"]), as_of)
                start = max(recovery["available"], reference["available"], correction["available"])
                if current["available"] < start or current["time"] <= recovery["time"]:
                    continue
                broke = (
                    current["close"] > reference["high"]
                    and current["close"] > correction["high"]
                    and current["close"] > current["open"]
                    and (
                        previous["close"] <= reference["high"]
                        or previous["close"] <= correction["high"]
                    )
                    if direction == "LONG"
                    else current["close"] < reference["low"]
                    and current["close"] < correction["low"]
                    and current["close"] < current["open"]
                    and (
                        previous["close"] >= reference["low"]
                        or previous["close"] >= correction["low"]
                    )
                )
                if broke:
                    output.append(
                        {
                            "liquidityBarId": str(sweep["liquidityBarId"]),
                            "sweepExcursionBarId": str(sweep["excursionBarId"]),
                            "sweepRecoveryBarId": str(sweep["recoveryBarId"]),
                            "referenceBarId": reference["barId"],
                            "m5CorrectionSwingBarId": correction["barId"],
                            "breakBarId": current["barId"],
                            "detectedAtUtc": utc_text(current["available"]),
                        }
                    )
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
    objective_members = list(
        (scenario.get("objectiveFamily") or {}).get("orderedMembers")
        or [scenario["objective"]]
    )
    live_members = [
        item for item in objective_members
        if not _objective_consumed(market, item, int(row["available"]))
    ]
    if scenario["scope"] == "INTERNAL_ROTATION":
        # The nearest internal member owns the scope. Once consumed, the plan
        # cannot roll outward to another internal or external destination.
        if not live_members or str(live_members[0]["barId"]) != str(objective_members[0]["barId"]):
            return "INTERNAL_OBJECTIVE_REACHED_BEFORE_FILL"
    elif not live_members:
        return "OBJECTIVE_FAMILY_EXHAUSTED_BEFORE_FILL"

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


def select_objective_from_family(
    market: MarketData,
    scenario: dict[str, Any],
    entry: float,
    stop: float,
    as_of: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Choose TP deterministically after executable risk geometry exists."""
    risk = abs(float(entry) - float(stop))
    if risk <= market.point / 2.0:
        raise V4ContractError("OBJECTIVE_FAMILY_ZERO_RISK")
    raw_family = scenario.get("objectiveFamily") or {
        "orderedMembers": [scenario["objective"]]
    }
    members = [dict(item) for item in raw_family.get("orderedMembers", [])]
    if not members:
        raise V4ContractError("OBJECTIVE_FAMILY_EMPTY")
    direction = str(scenario["direction"])
    if scenario["scope"] == "INTERNAL_ROTATION":
        first = dict(members[0])
        first_bar = market.bar(str(first["barId"]), as_of)
        first["side"] = "HIGH" if direction == "LONG" else "LOW"
        first["price"] = float(
            first_bar["high"] if direction == "LONG" else first_bar["low"]
        )
        first["timeframe"] = first_bar["tf"]
        if _objective_consumed(market, first, as_of):
            raise V4ContractError("INTERNAL_OBJECTIVE_PRECONSUMED_CANCEL")
        directional = (
            float(first["price"]) > float(entry)
            if direction == "LONG" else float(first["price"]) < float(entry)
        )
        if not directional:
            raise V4ContractError("INTERNAL_OBJECTIVE_NOT_DIRECTIONAL")
        first["plannedR"] = abs(float(first["price"]) - float(entry)) / risk
        if float(first["plannedR"]) < 1.0:
            raise V4ContractError("INTERNAL_OBJECTIVE_BELOW_ONE_R")
        return first, []
    live: list[dict[str, Any]] = []
    for member in members:
        member_bar = market.bar(str(member["barId"]), as_of)
        side = "HIGH" if direction == "LONG" else "LOW"
        member["side"] = side
        member["price"] = float(member_bar["high"] if side == "HIGH" else member_bar["low"])
        member["timeframe"] = member_bar["tf"]
        if _objective_consumed(market, member, as_of):
            continue
        directional = (
            float(member["price"]) > float(entry)
            if direction == "LONG"
            else float(member["price"]) < float(entry)
        )
        if not directional:
            continue
        member["plannedR"] = abs(float(member["price"]) - float(entry)) / risk
        context = member.get("destinationContext") or {}
        member["historyTier"] = str(
            member.get("historyTier")
            or context.get("historyTier")
            or "CURRENT_STRUCTURE"
        )
        live.append(member)
    if not live:
        raise V4ContractError("OBJECTIVE_FAMILY_EXHAUSTED")

    current = [item for item in live if item["historyTier"] != "LONG_TERM_H1"]
    historical = [item for item in live if item["historyTier"] == "LONG_TERM_H1"]
    eligible_current = [item for item in current if float(item["plannedR"]) >= 1.0]
    pool = eligible_current or [
        item for item in historical if float(item["plannedR"]) >= 1.0
    ]
    if not pool:
        raise V4ContractError("OBJECTIVE_FAMILY_NO_MEMBER_AT_LEAST_ONE_R")
    selected = pool[0]
    selected_index = next(
        index for index, item in enumerate(live)
        if str(item["barId"]) == str(selected["barId"])
    )
    return selected, live[:selected_index]


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
    selected_objective, intermediate_delivery = select_objective_from_family(
        market, scenario, float(entry), float(stop), int(decision_bar["available"])
    )
    target = float(selected_objective["price"])
    if scenario["scope"] == "INTERNAL_ROTATION":
        first_internal = _live_directional_liquidity(
            market,
            int(decision_bar["available"]),
            direction,
            range_low=float(scenario["dealingRange"]["low"]),
            range_high=float(scenario["dealingRange"]["high"]),
            from_price=float(entry),
        )
        if not first_internal:
            raise V4ContractError(
                "INTERNAL_OBJECTIVE_NOT_LIVE_AT_ORDER"
            )
        if abs(float(first_internal[0]["price"]) - float(target)) > market.point / 2.0:
            raise V4ContractError(
                "INTERNAL_OBJECTIVE_NO_LONGER_FIRST_AT_ORDER"
            )
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
        "selectedObjective": selected_objective,
        "objectiveFamilyId": (scenario.get("objectiveFamily") or {}).get(
            "objectiveFamilyId"
        ),
        "intermediateDelivery": intermediate_delivery,
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


def _latest_completed_m1_swing(
    market: MarketData,
    end_index: int,
    side: str,
    *,
    minimum_time: int,
) -> dict[str, Any] | None:
    """Return a two-sided swing that was knowable before the delivery bar."""
    start = max(2, end_index - 90)
    candidates: list[dict[str, Any]] = []
    for index in range(start, max(start, end_index - 2)):
        row = market.m1_row(index)
        if int(row["time"]) < int(minimum_time):
            continue
        left = [market.m1_row(index - 2), market.m1_row(index - 1)]
        right = [market.m1_row(index + 1), market.m1_row(index + 2)]
        if side == "HIGH":
            qualified = row["high"] > max(item["high"] for item in left) and row[
                "high"
            ] >= max(item["high"] for item in right)
        else:
            qualified = row["low"] < min(item["low"] for item in left) and row[
                "low"
            ] <= min(item["low"] for item in right)
        if qualified:
            candidates.append(row)
    return candidates[-1] if candidates else None


def _delivery_confirmation(
    market: MarketData,
    scenario: dict[str, Any],
    row: dict[str, Any],
    m1_transfer: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Return structure transfer or an explicit frozen-root reconfirmation.

    A two-sided M1 pivot is sufficient for precise execution geometry, but it
    is not sufficient evidence that price has resumed the frozen HTF delivery.
    AGENTS permits replacement after either meaningful structure transfer or a
    clear reconfirmation of the existing delivery.  The latter is a post-freeze
    rejection from the already-frozen root proximal, not a newly invented M1
    source.
    """
    candidates = mechanical_m5_correction_swing_candidates(
        market, scenario, int(row["available"])
    )
    if scenario["direction"] == "LONG":
        transferred = [
            item for item in candidates
            if float(row["close"]) > float(item["level"])
        ]
    else:
        transferred = [
            item for item in candidates
            if float(row["close"]) < float(item["level"])
        ]
    if transferred:
        return {
            "mode": "M5_STRUCTURE_TRANSFER",
            "barId": transferred[-1]["barId"],
            "level": float(transferred[-1]["level"]),
        }

    root = scenario.get("root") or {}
    proximal = root.get("proximal")
    if proximal is None:
        return None
    frozen_at = parse_utc(str(scenario["frozenAtUtc"]))
    rejection_cache = scenario.setdefault(
        "_deliveryRootProximalRejectionCache",
        {"searchedThroughUtc": utc_text(frozen_at), "match": None},
    )
    cached_match = rejection_cache.get("match")
    if isinstance(cached_match, dict):
        return dict(cached_match)
    search_start = max(
        frozen_at,
        parse_utc(str(rejection_cache.get("searchedThroughUtc") or utc_text(frozen_at))),
    )
    for candidate in market.between(
        "M1", search_start, int(row["available"])
    ):
        if int(candidate["available"]) >= int(row["available"]):
            break
        rejected = (
            float(candidate["low"]) <= float(proximal)
            and float(candidate["close"]) > float(proximal)
            if scenario["direction"] == "LONG"
            else float(candidate["high"]) >= float(proximal)
            and float(candidate["close"]) < float(proximal)
        )
        if rejected:
            match = {
                "mode": "FROZEN_ROOT_PROXIMAL_REJECTION",
                "barId": candidate["barId"],
                "level": float(proximal),
            }
            rejection_cache["match"] = match
            rejection_cache["searchedThroughUtc"] = utc_text(
                int(row["available"])
            )
            return match
    rejection_cache["searchedThroughUtc"] = utc_text(int(row["available"]))

    # AGENTS section 7 explicitly permits an M5 *or M1* destination-direction
    # displacement that body-breaks a protected swing.  A newly frozen plan can
    # produce a valid M1 transfer before enough bars exist to complete an M5
    # correction pivot.  Prefer stronger M5/root evidence above; this fallback
    # still requires a two-sided completed M1 swing, body break, causal opposite
    # candle, and fresh FVG in the caller.
    if m1_transfer is not None:
        level = (
            float(m1_transfer["high"])
            if scenario["direction"] == "LONG"
            else float(m1_transfer["low"])
        )
        body_broken = (
            float(row["close"]) > level
            if scenario["direction"] == "LONG"
            else float(row["close"]) < level
        )
        if body_broken:
            return {
                "mode": "M1_STRUCTURE_TRANSFER",
                "barId": m1_transfer["barId"],
                "level": level,
            }
    return None


def delivery_structural_invalidation(
    direction: str,
    causal_ob: dict[str, Any],
    protected_swing: dict[str, Any],
    final_child: dict[str, Any],
) -> float:
    """Return the AGENTS-defined outer structural boundary for Delivery FVG SL."""
    if direction == "LONG":
        return min(
            float(causal_ob["low"]),
            float(protected_swing["low"]),
            float(final_child["distal"]),
        )
    if direction == "SHORT":
        return max(
            float(causal_ob["high"]),
            float(protected_swing["high"]),
            float(final_child["distal"]),
        )
    raise V4ContractError(f"unsupported delivery direction: {direction}")


def detect_pre_touch_delivery_candidate(
    market: MarketData,
    scenario: dict[str, Any],
    row: dict[str, Any],
    broker_stops_level: float,
) -> dict[str, Any] | None:
    """Detect an AGENTS-compliant pre-touch Delivery FVG replacement."""
    if scenario.get("childTouchAtUtc") is not None or int(row["index"]) < 3:
        return None
    frozen_at = parse_utc(str(scenario["frozenAtUtc"]))
    if int(row["available"]) <= frozen_at:
        return None
    direction = str(scenario["direction"])
    first = market.m1_row(int(row["index"]) - 2)
    bullish_fvg = row["low"] > first["high"]
    bearish_fvg = row["high"] < first["low"]
    if direction == "LONG":
        if not bullish_fvg or row["close"] <= row["open"]:
            return None
    elif not bearish_fvg or row["close"] >= row["open"]:
        return None

    transfer_side = "HIGH" if direction == "LONG" else "LOW"
    stop_side = "LOW" if direction == "LONG" else "HIGH"
    transfer = _latest_completed_m1_swing(
        market, int(row["index"]), transfer_side, minimum_time=frozen_at
    )
    protected = _latest_completed_m1_swing(
        market, int(row["index"]), stop_side, minimum_time=frozen_at
    )
    if transfer is None or protected is None:
        return None
    transferred = (
        row["close"] > transfer["high"]
        if direction == "LONG"
        else row["close"] < transfer["low"]
    )
    if not transferred:
        return None
    delivery_confirmation = _delivery_confirmation(
        market, scenario, row, m1_transfer=transfer
    )
    if delivery_confirmation is None:
        return None
    causal_ob = find_execution_ob(
        market, max(frozen_at, int(transfer["time"])), int(row["available"]), direction
    )
    if causal_ob is None:
        return None

    spread = float(row["spreadPoints"]) * market.point
    buffer = max(market.point, spread, float(broker_stops_level))
    child = scenario["finalChild"]
    if direction == "LONG":
        fvg_low, fvg_high = float(first["high"]), float(row["low"])
        entry = fvg_high
        structural = delivery_structural_invalidation(
            direction, causal_ob, protected, child
        )
        stop = structural - buffer
    else:
        fvg_low, fvg_high = float(row["high"]), float(first["low"])
        entry = fvg_low
        structural = delivery_structural_invalidation(
            direction, causal_ob, protected, child
        )
        stop = structural + buffer
    try:
        selected_objective, family_intermediate = select_objective_from_family(
            market, scenario, entry, stop, int(row["available"])
        )
    except V4ContractError:
        return None
    target = float(selected_objective["price"])
    if direction == "LONG" and not stop < entry < target:
        return None
    if direction == "SHORT" and not target < entry < stop:
        return None
    live_between = _live_directional_liquidity(
        market,
        int(row["available"]),
        direction,
        range_low=float(scenario["dealingRange"]["low"]),
        range_high=float(scenario["dealingRange"]["high"]),
        from_price=float(entry),
        to_price=float(target),
    )
    # Internal rotation cannot skip any nearer mature pool.  External
    # continuation keeps ordinary lower-TF pools as delivery waypoints, except
    # when the candidate claims a fresh M5 structure transfer: that transfer
    # is incomplete until the still-live M15/M5 pool governing the correction
    # has actually been delivered through.  A frozen-root rejection is a
    # separate reconfirmation path and does not promote every lower-TF pivot to
    # a competing objective.
    if scenario["scope"] == "INTERNAL_ROTATION":
        blocking_liquidity = live_between
    elif delivery_confirmation["mode"] == "M5_STRUCTURE_TRANSFER":
        blocking_liquidity = live_between
    else:
        blocking_liquidity = [
            item for item in live_between
            if str(item.get("timeframe")) in {"H1", "M30"}
        ]
    shadow_id = canonical_hash(
        {
            "scenarioHash": scenario["scenarioHash"],
            "fvgBarId": row["barId"],
            "causalObBarId": causal_ob["barId"],
            "transferSwingBarId": transfer["barId"],
        }
    )[:20]
    candidate = {
        "shadowId": shadow_id,
        "executionModel": "DELIVERY_FVG_REPLACEMENT",
        "scenarioHash": scenario["scenarioHash"],
        "status": "WAIT_FIRST_RETEST",
        "direction": direction,
        "formedAtUtc": utc_text(row["available"]),
        "formedBarId": row["barId"],
        "fvg": {"low": fvg_low, "high": fvg_high},
            "causalObBarId": causal_ob["barId"],
            "transferSwingBarId": transfer["barId"],
            "deliveryConfirmation": delivery_confirmation,
            "m5TransferSwingBarId": (
                delivery_confirmation["barId"]
                if delivery_confirmation["mode"] == "M5_STRUCTURE_TRANSFER"
                else None
            ),
            "protectedSwingBarId": protected["barId"],
        "originalChildObBarId": child["obBarId"],
        "entry": entry,
        "stop": stop,
        "target": target,
        "selectedObjective": selected_objective,
        "objectiveFamilyId": (scenario.get("objectiveFamily") or {}).get(
            "objectiveFamilyId"
        ),
        "risk": abs(entry - stop),
        "spreadAtFormation": spread,
        "buffer": buffer,
        "stopBasis": {
            "model": "DELIVERY_CAUSAL_STRUCTURE",
            "fvgDistal": fvg_low if direction == "LONG" else fvg_high,
            "causalObBoundary": (
                float(causal_ob["low"])
                if direction == "LONG" else float(causal_ob["high"])
            ),
            "protectedSwingBoundary": (
                float(protected["low"])
                if direction == "LONG" else float(protected["high"])
            ),
            "structuralInvalidation": structural,
            "originalChildDistal": float(child["distal"]),
        },
        "intermediateDelivery": family_intermediate,
    }
    if blocking_liquidity:
        candidate["status"] = "BLOCKED_CLOSER_LIQUIDITY"
        candidate["blockedLiquidity"] = blocking_liquidity
    return candidate


def detect_delivery_addon_candidate(
    market: MarketData,
    scenario: dict[str, Any],
    position: dict[str, Any],
    row: dict[str, Any],
    broker_stops_level: float,
) -> dict[str, Any] | None:
    """Detect one distinct Delivery FVG chain after a position is in profit.

    An addon never creates a new map.  It reuses the filled position's frozen
    owner, objective family, and HTF-to-LTF lineage, while requiring a new
    post-fill structure transfer and fresh FVG.  The candidate still has to
    pass the same semantic delivery review and first-retest lifecycle as a
    replacement order.
    """
    entry_at = parse_utc(str(position["entryAtUtc"]))
    if int(row["available"]) <= entry_at:
        return None
    direction = str(position["direction"])
    favorable = (
        float(row["close"]) > float(position["entry"])
        if direction == "LONG"
        else float(row["close"]) < float(position["entry"])
    )
    if not favorable:
        return None

    addon_scenario = {
        **scenario,
        "frozenAtUtc": utc_text(entry_at),
        "childTouchAtUtc": None,
        "childTouchBarId": None,
    }
    candidate = detect_pre_touch_delivery_candidate(
        market,
        addon_scenario,
        row,
        broker_stops_level,
    )
    if candidate is None:
        return None
    existing_execution = str(
        position.get("deliveryFvgBarId")
        or position.get("executionObBarId")
        or ""
    )
    if existing_execution and str(candidate["formedBarId"]) == existing_execution:
        return None
    addon_id = canonical_hash(
        {
            "sourcePosition": position["orderId"],
            "fvgBarId": candidate["formedBarId"],
            "causalObBarId": candidate["causalObBarId"],
        }
    )[:20]
    return {
        **candidate,
        "shadowId": addon_id,
        "executionModel": "DELIVERY_FVG_ADDON",
        "sourcePositionOrderId": position["orderId"],
        "sourcePositionEntryAtUtc": position["entryAtUtc"],
    }


def _delivery_lineage_key(scenario: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    return (
        str(scenario["root"]["obBarId"]),
        tuple(str(item["obBarId"]) for item in scenario["refinements"]),
    )


def _delivery_lineage_fully_contained(scenario: dict[str, Any]) -> bool:
    """Apply the frozen June benchmark's price-and-parent-time containment rule."""
    parent = scenario["root"]
    for child in scenario["refinements"]:
        parent_tf, parent_time = split_bar_id(str(parent["obBarId"]))
        _, child_time = split_bar_id(str(child["obBarId"]))
        time_contained = (
            parent_time <= child_time < parent_time + TIMEFRAME_SECONDS[parent_tf]
        )
        price_contained = (
            float(parent["low"]) <= float(child["low"])
            and float(child["high"]) <= float(parent["high"])
        )
        if not time_contained or not price_contained:
            return False
        parent = child
    return True


def resolve_delivery_lineage_variants(
    active_scenario: dict[str, Any],
    active_candidate: dict[str, Any],
    reproduced: list[dict[str, Any]],
    formed_bar_id: str,
) -> dict[str, Any]:
    """Resolve pre-outcome lineage and objective ambiguity for one physical FVG."""
    all_path_groups: dict[tuple[str, tuple[str, ...]], list[dict[str, Any]]] = {}
    for item in reproduced:
        all_path_groups.setdefault(
            _delivery_lineage_key(item["scenario"]), []
        ).append(item)

    # AGENTS permits a child inside the parent OB *or* immediately adjacent to
    # the same parent swing event. A unique path has already passed PLAN's
    # semantic causal audit, so strict candle containment must not erase it.
    # Containment is used only to resolve genuinely competing physical paths.
    if len(all_path_groups) == 1:
        path_groups = all_path_groups
    else:
        path_groups: dict[tuple[str, tuple[str, ...]], list[dict[str, Any]]] = {}
        for item in reproduced:
            if item["fullyContained"]:
                path_groups.setdefault(
                    _delivery_lineage_key(item["scenario"]), []
                ).append(item)

    public_lineages = [
        {key: value for key, value in item.items() if key != "scenario"}
        for item in reproduced
    ]
    if not path_groups:
        return {
            "approved": False,
            "reason": "NO_FULLY_CONTAINED_CAUSAL_LINEAGE",
            "formedBarId": formed_bar_id,
            "lineages": public_lineages,
        }
    if len(path_groups) > 1:
        return {
            "approved": False,
            "reason": "MULTIPLE_FULLY_CONTAINED_CAUSAL_LINEAGES",
            "formedBarId": formed_bar_id,
            "pathCount": len(path_groups),
            "lineages": public_lineages,
        }

    variants = next(iter(path_groups.values()))
    direction = str(active_scenario["direction"])
    entry = float(active_candidate["entry"])
    external = [item for item in variants if item["scope"] == "EXTERNAL_CONTINUATION"]
    if external:
        directional = [
            item for item in external
            if (
                float(item["objectivePrice"]) > entry
                if direction == "LONG"
                else float(item["objectivePrice"]) < entry
            )
        ]
        if not directional:
            return {
                "approved": False,
                "reason": "NO_DIRECTIONAL_EXTERNAL_OBJECTIVE",
                "formedBarId": formed_bar_id,
                "lineages": public_lineages,
            }
        selected = min(
            directional,
            key=lambda item: abs(float(item["objectivePrice"]) - entry),
        )
    else:
        internal = [item for item in variants if item["scope"] == "INTERNAL_ROTATION"]
        if len(internal) != 1:
            return {
                "approved": False,
                "reason": "NON_UNIQUE_INTERNAL_OBJECTIVE",
                "formedBarId": formed_bar_id,
                "lineages": public_lineages,
            }
        selected = internal[0]

    active_path = _delivery_lineage_key(active_scenario)
    selected_path = _delivery_lineage_key(selected["scenario"])
    if active_path != selected_path:
        reason = "ACTIVE_LINEAGE_DIFFERS_FROM_CAUSAL_RESOLUTION"
    elif str(active_scenario["scope"]) != str(selected["scope"]):
        reason = "ACTIVE_SCOPE_DIFFERS_FROM_CAUSAL_RESOLUTION"
    elif str(active_scenario["objective"]["barId"]) != str(selected["objectiveBarId"]):
        reason = "ACTIVE_OBJECTIVE_DIFFERS_FROM_CAUSAL_RESOLUTION"
    else:
        reason = "UNIQUE_CAUSAL_LINEAGE_AND_OBJECTIVE"
    return {
        "approved": reason == "UNIQUE_CAUSAL_LINEAGE_AND_OBJECTIVE",
        "reason": reason,
        "formedBarId": formed_bar_id,
        "pathCount": 1,
        "selected": {
            key: value for key, value in selected.items() if key != "scenario"
        },
        "lineages": public_lineages,
    }


def audit_pre_touch_delivery_lineages(
    market: MarketData,
    active_scenario: dict[str, Any],
    row: dict[str, Any],
    broker_stops_level: float,
    symbol: str,
    external_authority: dict[str, Any] | None,
) -> dict[str, Any]:
    """Resolve competing causal paths before a Delivery FVG can reach the model.

    The audit uses only evidence available when the FVG closes. It mirrors the
    June benchmark salvage contract: one physical FVG cannot be authorized when
    more than one fully-contained root/refinement path explains it.
    """
    as_of = int(row["available"])
    active_candidate = detect_pre_touch_delivery_candidate(
        market, active_scenario, row, broker_stops_level
    )
    if active_candidate is None:
        return {
            "approved": False,
            "reason": "ACTIVE_SCENARIO_DOES_NOT_REPRODUCE_DELIVERY_FVG",
            "formedBarId": row["barId"],
            "lineages": [],
        }

    active_root = active_scenario["root"]
    focus_roots: set[str] = set()
    for candidate_root in mechanical_root_candidates(
        market, as_of, maximum=None, active_only=True
    ):
        if str(candidate_root["direction"]) != str(active_scenario["direction"]):
            continue
        root_bar = market.bar(str(candidate_root["rootBarId"]), as_of)
        if (
            float(root_bar["high"]) >= float(active_root["low"])
            and float(root_bar["low"]) <= float(active_root["high"])
        ):
            focus_roots.add(str(candidate_root["rootBarId"]))
    focus_roots.add(str(active_root["obBarId"]))
    packet = build_plan_packet(
        market,
        as_of,
        symbol,
        external_authority=external_authority,
        focus_root_bar_ids=focus_roots,
        focus_objective_bar_ids={
            str(item["barId"])
            for item in (
                (active_scenario.get("objectiveFamily") or {}).get(
                    "orderedMembers", []
                )
                or [active_scenario["objective"]]
            )
        },
        fixed_objective_members=list(
            (active_scenario.get("objectiveFamily") or {}).get(
                "orderedMembers", []
            ) or [active_scenario["objective"]]
        ),
        fixed_dealing_range=dict(active_scenario["dealingRange"]),
        minimal_lineage_audit=True,
    )
    reproduced: list[dict[str, Any]] = []
    seen_semantic: set[tuple[Any, ...]] = set()
    for selection_id in _atomic_scenario_options(packet):
        try:
            scenario = freeze_plan(
                {
                    "schemaVersion": "4.10.0",
                    "action": "PLAN",
                    "scenarioSelectionId": selection_id,
                    "reason": "delivery-lineage-audit",
                },
                market,
                as_of,
                packet=packet,
            )
        except V4ContractError:
            continue
        if scenario is None or str(scenario["direction"]) != str(active_scenario["direction"]):
            continue

        known_at = max(
            parse_utc(str(node["deliveryAvailableAtUtc"]))
            for node in [scenario["root"], *scenario["refinements"]]
        )
        if known_at >= as_of:
            continue
        scenario["frozenAtUtc"] = utc_text(known_at)
        scenario["lastReauthorizedAtUtc"] = utc_text(known_at)
        alternative = detect_pre_touch_delivery_candidate(
            market, scenario, row, broker_stops_level
        )
        if alternative is None or str(alternative["formedBarId"]) != str(row["barId"]):
            continue
        if (
            abs(float(alternative["fvg"]["low"]) - float(active_candidate["fvg"]["low"]))
            > market.point / 2.0
            or abs(float(alternative["fvg"]["high"]) - float(active_candidate["fvg"]["high"]))
            > market.point / 2.0
        ):
            continue
        semantic_key = (
            *_delivery_lineage_key(scenario),
            str(scenario["scope"]),
            str(scenario["objective"]["barId"]),
        )
        if semantic_key in seen_semantic:
            continue
        seen_semantic.add(semantic_key)
        reproduced.append(
            {
                "selectionId": selection_id,
                "rootObBarId": scenario["root"]["obBarId"],
                "refinementObBarIds": [
                    item["obBarId"] for item in scenario["refinements"]
                ],
                "scope": scenario["scope"],
                "objectiveBarId": scenario["objective"]["barId"],
                "objectivePrice": scenario["objective"]["price"],
                "fullyContained": _delivery_lineage_fully_contained(scenario),
                "scenario": scenario,
            }
        )

    # The already-frozen scenario remains admissible evidence even if the
    # current packet deduplicated its older representation.
    active_key = (
        *_delivery_lineage_key(active_scenario),
        str(active_scenario["scope"]),
        str(active_scenario["objective"]["barId"]),
    )
    if active_key not in seen_semantic:
        reproduced.append(
            {
                "selectionId": "ACTIVE_FROZEN_SCENARIO",
                "rootObBarId": active_scenario["root"]["obBarId"],
                "refinementObBarIds": [
                    item["obBarId"] for item in active_scenario["refinements"]
                ],
                "scope": active_scenario["scope"],
                "objectiveBarId": active_scenario["objective"]["barId"],
                "objectivePrice": active_scenario["objective"]["price"],
                "fullyContained": _delivery_lineage_fully_contained(active_scenario),
                "scenario": active_scenario,
            }
        )

    return resolve_delivery_lineage_variants(
        active_scenario,
        active_candidate,
        reproduced,
        str(row["barId"]),
    )


def delivery_candidate_order(
    market: MarketData,
    scenario: dict[str, Any],
    candidate: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Convert frozen replacement evidence into one first-retest limit order."""
    formed_at = parse_utc(str(candidate["formedAtUtc"]))
    causal = market.bar(str(candidate["causalObBarId"]), formed_at)
    protected = market.bar(str(candidate["protectedSwingBarId"]), formed_at)
    execution_model = str(
        candidate.get("executionModel", "DELIVERY_FVG_REPLACEMENT")
    )
    original_order_id = canonical_hash({
        "scenarioHash": scenario["scenarioHash"],
        "originalChildObBarId": candidate["originalChildObBarId"],
        "model": (
            "FILLED_SOURCE_POSITION"
            if execution_model == "DELIVERY_FVG_ADDON"
            else "PLANNED_CHILD_OB"
        ),
    })[:20]
    order_id = canonical_hash({
        "original": original_order_id,
        "fvg": candidate["formedBarId"],
        "entry": candidate["entry"],
        "stop": candidate["stop"],
        "target": candidate["target"],
        "selectedObjective": candidate.get("selectedObjective"),
        "objectiveFamilyId": candidate.get("objectiveFamilyId"),
        "intermediateDelivery": candidate.get("intermediateDelivery", []),
    })[:20]
    order = {
        "orderId": order_id,
        "scenarioHash": scenario["scenarioHash"],
        "model": execution_model,
        "direction": candidate["direction"],
        "createdAtUtc": candidate["formedAtUtc"],
        "lastReauthorizedAtUtc": scenario["lastReauthorizedAtUtc"],
        "entry": candidate["entry"],
        "stop": candidate["stop"],
        "target": candidate["target"],
        "executionObBarId": candidate["causalObBarId"],
        "executionZone": dict(candidate["fvg"]),
        "deliveryFvg": dict(candidate["fvg"]),
        "deliveryCausalOb": {
            "barId": causal["barId"], "low": causal["low"], "high": causal["high"],
        },
        "deliveryProtectedSwing": {
            "barId": protected["barId"], "low": protected["low"],
            "high": protected["high"],
        },
        "structuralInvalidation": (
            float(candidate["stop"]) + float(candidate["buffer"])
            if candidate["direction"] == "LONG"
            else float(candidate["stop"]) - float(candidate["buffer"])
        ),
        "spreadAtCreation": candidate["spreadAtFormation"],
        "buffer": candidate["buffer"],
        "replacementUsed": True,
        "originalOrderId": original_order_id,
        "deliveryFvgBarId": candidate["formedBarId"],
        "transferSwingBarId": candidate["transferSwingBarId"],
        "sourcePositionOrderId": candidate.get("sourcePositionOrderId"),
    }
    watch = {
        "model": execution_model,
        "triggerProtectedSwing": protected,
        "deliveryFvgBarId": candidate["formedBarId"],
        "causalObBarId": candidate["causalObBarId"],
        "transferSwingBarId": candidate["transferSwingBarId"],
    }
    return order, watch


def advance_shadow_delivery_candidate(
    market: MarketData,
    candidate: dict[str, Any],
    row: dict[str, Any],
) -> tuple[dict[str, Any], str | None]:
    """Advance a shadow replacement through first retest and frozen SL/TP."""
    if candidate["status"] in {
        "TP", "SL", "OBJECTIVE_FIRST", "INVALIDATED", "THROUGH_DELIVERY"
    }:
        return candidate, None
    formed_at = parse_utc(str(candidate["formedAtUtc"]))
    if int(row["available"]) <= formed_at:
        return candidate, None
    direction = str(candidate["direction"])
    spread = float(row["spreadPoints"]) * market.point
    if candidate["status"] == "WAIT_FIRST_RETEST":
        objective_hit = (
            row["high"] >= candidate["target"]
            if direction == "LONG"
            else row["low"] <= candidate["target"]
        )
        if objective_hit:
            return {
                **candidate,
                "status": "OBJECTIVE_FIRST",
                "closedAtUtc": utc_text(row["available"]),
            }, "OBJECTIVE_FIRST"
        entry_hit = (
            row["low"] + spread <= candidate["entry"]
            if direction == "LONG"
            else row["high"] >= candidate["entry"]
        )
        if not entry_hit:
            return candidate, None
        stop_hit = (
            row["low"] <= candidate["stop"]
            if direction == "LONG"
            else row["high"] + spread >= candidate["stop"]
        )
        if stop_hit:
            return {
                **candidate,
                "status": "THROUGH_DELIVERY",
                "closedAtUtc": utc_text(row["available"]),
            }, "THROUGH_DELIVERY"
        return {
            **candidate,
            "status": "FILLED",
            "filledAtUtc": utc_text(row["available"]),
            "fillBarId": row["barId"],
        }, "FILLED"

    stop_hit = (
        row["low"] <= candidate["stop"]
        if direction == "LONG"
        else row["high"] + spread >= candidate["stop"]
    )
    target_hit = (
        row["high"] >= candidate["target"]
        if direction == "LONG"
        else row["low"] + spread <= candidate["target"]
    )
    if not stop_hit and not target_hit:
        return candidate, None
    outcome = "SL" if stop_hit else "TP"
    result_r = -1.0 if stop_hit else abs(
        float(candidate["target"]) - float(candidate["entry"])
    ) / float(candidate["risk"])
    return {
        **candidate,
        "status": outcome,
        "closedAtUtc": utc_text(row["available"]),
        "closeBarId": row["barId"],
        "resultR": result_r,
        "intrabarAmbiguous": bool(stop_hit and target_hit),
    }, outcome


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
    semantic_ready = order.get("semanticReadyAtUtc")
    broker_ready = order.get("brokerAuthorizedAtUtc")
    row_start = int(row.get("time", int(row["available"]) - 60))
    if semantic_ready:
        semantic_ready_at = parse_utc(str(semantic_ready))
        if row_start < semantic_ready_at <= int(row["available"]):
            return "CANCELED_LATENCY_INTRABAR_AMBIGUOUS", None
        if int(row["available"]) <= semantic_ready_at:
            return "CANCELED_MISSED_API_LATENCY", None
    if broker_ready:
        broker_ready_at = parse_utc(str(broker_ready))
        if row_start < broker_ready_at <= int(row["available"]):
            return "CANCELED_LATENCY_INTRABAR_AMBIGUOUS", None
        if int(row["available"]) <= broker_ready_at:
            return "CANCELED_MISSED_ORDER_LATENCY", None
    if (
        order.get("model") in {"DELIVERY_FVG_REPLACEMENT", "DELIVERY_FVG_ADDON"}
        and spread > float(order.get("buffer", 0.0)) + market.point / 2.0
    ):
        return "CANCELED_SPREAD_EXPANSION", None
    stop_crossed = row["low"] <= order["stop"] if direction == "LONG" else row["high"] + spread >= order["stop"]
    if stop_crossed:
        return "CANCELED_THROUGH_DELIVERY", None
    if order.get("model") not in {"DELIVERY_FVG_REPLACEMENT", "DELIVERY_FVG_ADDON"}:
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
        "executionObBarId": order.get("executionObBarId"),
        "deliveryFvgBarId": order.get("deliveryFvgBarId"),
        "sourcePositionOrderId": order.get("sourcePositionOrderId"),
        "selectedObjective": order.get("selectedObjective"),
        "objectiveFamilyId": order.get("objectiveFamilyId"),
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
        "lastPlanM5Available": None,
        "lastLocalDiscoveryFingerprint": None,
        "lastPlanRequestAtUtc": None,
        "lastPlanRequestH1Bucket": None,
        "lastFlatPlanFingerprint": None,
        "evaluatedFlatPlanFingerprints": [],
        "evaluatedPlanOpportunityKeys": [],
        "flatPlanCandidates": [],
        # Roots can become knowable before a suitable objective matures. Keep
        # them independently from complete families so a later liquidity event
        # can finish the PLAN without reconstructing the source retrospectively.
        "pendingPlanRootBarIds": [],
        "newPlanFamilyIdsAtLastRefresh": [],
        "newPlanEventsAtLastRefresh": [],
        "deferredPlanEvents": [],
        "forcedRemapFamilyIds": [],
        "completedDeliveryFamilyIds": [],
        "evaluatedPlanSupersessionKeys": [],
        "lastPlanCandidateRefreshM5": None,
        "lastCandidateLedgerBarAvailable": None,
        "flatSinceAtUtc": None,
        "seenMapOpportunityIds": [],
        "seenPlanOpportunityIds": [],
        "externalMapAuthority": None,
        "ownerEpoch": 0,
        "ownerEpochHistory": [],
        "externalAuthorityHistory": [],
        "scenario": None,
        "parkedScenarios": [],
        "reactionMonitor": None,
        "triggerWatch": None,
        "order": None,
        "position": None,
        # A filled trade no longer monopolizes semantic scenario discovery.
        # Each book item owns its frozen scenario/order/position until the
        # original SL or TP resolves it.  The top-level state remains the one
        # and only pre-fill analysis lane.
        "openPositions": [],
        "orders": [],
        "positions": [],
        "executionChains": [],
        "inFlightRequests": {},
        "scenarioSlots": [],
        "retiredSourceFamilyKeys": [],
        "shadowDeliveryCandidates": [],
        "deliveryReviewHistory": [],
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
    open_positions = runtime.get("openPositions", [])
    if not isinstance(open_positions, list):
        raise AssertionError("openPositions must be a list")
    position_ids: list[str] = []
    family_keys: list[str] = []
    execution_keys: list[str] = []
    for item in open_positions:
        if not isinstance(item, dict):
            raise AssertionError("open position book item must be an object")
        if not all(isinstance(item.get(key), dict) for key in ("scenario", "order", "position")):
            raise AssertionError("open position book item is incomplete")
        position_ids.append(str(item.get("bookId") or ""))
        family_keys.append(str(item.get("sourceFamilyKey") or ""))
        execution_keys.append(str(item.get("executionSignalKey") or ""))
    if any(not item for item in position_ids) or len(position_ids) != len(set(position_ids)):
        raise AssertionError("duplicate position in openPositions")
    if any(not key for key in family_keys):
        raise AssertionError("openPositions require source family keys")
    if any(not key for key in execution_keys) or len(execution_keys) != len(set(execution_keys)):
        raise AssertionError("openPositions must have unique physical execution signals")
    slots = runtime.get("scenarioSlots", [])
    if not isinstance(slots, list):
        raise AssertionError("scenarioSlots must be a list")
    slot_ids = [str(item.get("slotId") or "") for item in slots]
    if any(not item for item in slot_ids) or len(slot_ids) != len(set(slot_ids)):
        raise AssertionError("scenarioSlots must have unique slot IDs")
    for item in slots:
        lane = {
            **runtime,
            "scenarioSlots": [],
            "state": item.get("state"),
            "scenario": item.get("scenario"),
            "reactionMonitor": item.get("reactionMonitor"),
            "triggerWatch": item.get("triggerWatch"),
            "order": item.get("order"),
            "position": item.get("position"),
            "shadowDeliveryCandidates": item.get("shadowDeliveryCandidates", []),
        }
        assert_runtime_invariants(lane)
    if authority is not None:
        if authority.get("direction") not in {"LONG", "SHORT"}:
            raise AssertionError("external map authority has an invalid direction")
        if authority.get("status", "ACTIVE") not in {
            "ACTIVE", "OBJECTIVE_REACHED", "REMAP_REQUIRED"
        }:
            raise AssertionError("external map authority has an invalid status")
        if not authority.get("dealingRange") or not authority.get("protectedSwing"):
            raise AssertionError("external map authority is incomplete")
    if not isinstance(runtime.get("externalAuthorityHistory", []), list):
        raise AssertionError("externalAuthorityHistory must be a list")
    if int(runtime.get("ownerEpoch", 0)) < 0:
        raise AssertionError("ownerEpoch cannot be negative")
    if not isinstance(runtime.get("ownerEpochHistory", []), list):
        raise AssertionError("ownerEpochHistory must be a list")
    for field_name in ("orders", "positions", "executionChains"):
        if not isinstance(runtime.get(field_name, []), list):
            raise AssertionError(f"{field_name} must be a list")
    if not isinstance(runtime.get("inFlightRequests", {}), dict):
        raise AssertionError("inFlightRequests must be an object")
    if not isinstance(runtime.get("shadowDeliveryCandidates", []), list):
        raise AssertionError("shadowDeliveryCandidates must be a list")
    if not isinstance(runtime.get("deliveryReviewHistory", []), list):
        raise AssertionError("deliveryReviewHistory must be a list")
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
        if int(count) < 0:
            raise AssertionError(f"scenario {scenario_hash} has a negative API call count")
    for map_hash, count in runtime.get("apiCallsByMap", {}).items():
        if int(count) > 1:
            raise AssertionError(f"map {map_hash} exceeded one API call")
