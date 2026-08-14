from __future__ import annotations

import copy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from mentor_engine.data import build_timeframes, load_m1_npz


SCHEMA_DIR = Path(__file__).resolve().parents[1] / "mentor_context_pack" / "schemas"
STAGE_SCHEMAS = {
    "MAP_SCOUT": SCHEMA_DIR / "map_scout.schema.json",
    "MAP_REVIEW": SCHEMA_DIR / "map_review.schema.json",
    "REFINEMENT": SCHEMA_DIR / "refinement.schema.json",
    "TRIGGER": SCHEMA_DIR / "trigger.schema.json",
    "PENDING_REVIEW": SCHEMA_DIR / "pending_review.schema.json",
}


def utc_text(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def bar_id(timeframe: str, open_timestamp: int) -> str:
    return f"{timeframe}:{open_timestamp}"


def compact_bars(
    dataset: Path,
    warmup_start: str,
    as_of: str,
    *,
    limits: dict[str, int] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    cutoff = parse_utc(as_of)
    m1, _ = load_m1_npz(dataset, parse_utc(warmup_start), cutoff + 60)
    frames = build_timeframes(m1)
    requested = limits or {"H1": 72, "M30": 96, "M15": 128}
    result: dict[str, list[dict[str, Any]]] = {}
    for timeframe, limit in requested.items():
        series = frames[timeframe]
        closed = np.flatnonzero(series.available_time <= cutoff)
        selected = closed[-max(1, int(limit)):]
        result[timeframe] = [
            {
                "barId": bar_id(timeframe, int(series.time[index])),
                "time": utc_text(int(series.time[index])),
                "o": float(series.open[index]),
                "h": float(series.high[index]),
                "l": float(series.low[index]),
                "c": float(series.close[index]),
                "spreadPoints": float(series.spread_points[index]),
            }
            for index in selected
        ]
    return result


def bar_lookup(compact: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    return {
        str(item["barId"]): item
        for rows in compact.values()
        for item in rows
    }


def bars_for_prompt(
    compact: dict[str, list[dict[str, Any]]],
    *,
    tail_limits: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Remove repeated JSON keys and ISO timestamps without losing OHLC evidence."""
    data: dict[str, list[list[Any]]] = {}
    for timeframe, rows in compact.items():
        selected = rows[-int((tail_limits or {}).get(timeframe, len(rows))):]
        data[timeframe] = [
            [
                str(row["barId"]),
                round(float(row["o"]), 5), round(float(row["h"]), 5),
                round(float(row["l"]), 5), round(float(row["c"]), 5),
                round(float(row.get("spreadPoints", 0.0)), 2),
            ]
            for row in selected
        ]
    return {
        "columns": ["barId", "open", "high", "low", "close", "spreadPoints"],
        "data": data,
    }


def structural_liquidity_candidates(
    compact: dict[str, list[dict[str, Any]]],
    *,
    maximum: int = 32,
) -> list[dict[str, Any]]:
    """Enumerate confirmed extrema without deciding whether they are true liquidity."""
    candidates: list[dict[str, Any]] = []
    for timeframe in ("H1", "M30", "M15"):
        rows = compact.get(timeframe, [])
        for index in range(1, len(rows) - 1):
            previous, current, following = rows[index - 1:index + 2]
            left = rows[max(0, index - 6):index]
            right = rows[index + 1:min(len(rows), index + 7)]
            bars_since_confirmed = max(0, len(rows) - index - 2)
            if (
                float(current["h"]) > float(previous["h"])
                and float(current["h"]) >= float(following["h"])
            ):
                candidates.append({
                    "barId": current["barId"], "tf": timeframe,
                    "side": "BSL", "price": float(current["h"]),
                    "candidateKind": "PIVOT",
                    "confirmedByBarId": following["barId"],
                    "prominencePrice": (
                        float(current["h"]) - max(
                            min(float(item["l"]) for item in left),
                            min(float(item["l"]) for item in right),
                        ) if left and right else 0.0
                    ),
                    "reactionExcursionPrice": (
                        float(current["h"]) - min(
                            float(item["l"]) for item in rows[index + 1:]
                        )
                    ),
                    "barsSinceConfirmed": bars_since_confirmed,
                })
            if (
                float(current["l"]) < float(previous["l"])
                and float(current["l"]) <= float(following["l"])
            ):
                candidates.append({
                    "barId": current["barId"], "tf": timeframe,
                    "side": "SSL", "price": float(current["l"]),
                    "candidateKind": "PIVOT",
                    "confirmedByBarId": following["barId"],
                    "prominencePrice": (
                        min(
                            max(float(item["h"]) for item in left),
                            max(float(item["h"]) for item in right),
                        ) - float(current["l"]) if left and right else 0.0
                    ),
                    "reactionExcursionPrice": (
                        max(float(item["h"]) for item in rows[index + 1:])
                        - float(current["l"])
                    ),
                    "barsSinceConfirmed": bars_since_confirmed,
                })
            # A mentor-style reaction boundary can be real liquidity even when
            # a wide prior candle prevents a textbook three-bar pivot. Keep the
            # last opposite candle whose next closed body delivers through its
            # distal boundary as a raw REACTION_TRAP candidate. The reviewer,
            # not this enumerator, still decides whether it is mature liquidity.
            bearish = float(current["c"]) < float(current["o"])
            bullish = float(current["c"]) > float(current["o"])
            if bearish and float(following["c"]) > float(current["h"]):
                candidates.append({
                    "barId": current["barId"], "tf": timeframe,
                    "side": "SSL", "price": float(current["l"]),
                    "candidateKind": "REACTION_TRAP",
                    "confirmedByBarId": following["barId"],
                    "prominencePrice": float(following["h"]) - float(current["l"]),
                    "reactionExcursionPrice": max(
                        float(item["h"]) for item in rows[index + 1:]
                    ) - float(current["l"]),
                    "barsSinceConfirmed": bars_since_confirmed,
                })
            if bullish and float(following["c"]) < float(current["l"]):
                candidates.append({
                    "barId": current["barId"], "tf": timeframe,
                    "side": "BSL", "price": float(current["h"]),
                    "candidateKind": "REACTION_TRAP",
                    "confirmedByBarId": following["barId"],
                    "prominencePrice": float(current["h"]) - float(following["l"]),
                    "reactionExcursionPrice": float(current["h"]) - min(
                        float(item["l"]) for item in rows[index + 1:]
                    ),
                    "barsSinceConfirmed": bars_since_confirmed,
                })
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for item in candidates:
        key = (str(item["barId"]), str(item["side"]))
        existing = merged.get(key)
        if existing is None:
            merged[key] = item
            continue
        kinds = set(str(existing.get("candidateKind", "PIVOT")).split("+"))
        kinds.update(str(item.get("candidateKind", "PIVOT")).split("+"))
        existing["candidateKind"] = "+".join(sorted(kinds))
        existing["prominencePrice"] = max(
            float(existing["prominencePrice"]), float(item["prominencePrice"])
        )
        existing["reactionExcursionPrice"] = max(
            float(existing["reactionExcursionPrice"]),
            float(item["reactionExcursionPrice"]),
        )
    candidates = list(merged.values())
    row_indexes = {
        timeframe: {
            str(row["barId"]): index for index, row in enumerate(rows)
        }
        for timeframe, rows in compact.items()
    }
    timeframe_seconds = {"H1": 3600, "M30": 1800, "M15": 900}
    m1_rows = compact.get("M1", [])
    for item in candidates:
        timeframe = str(item["tf"])
        rows = compact.get(timeframe, [])
        confirmed_index = row_indexes.get(timeframe, {}).get(
            str(item["confirmedByBarId"])
        )
        consumed_by = None
        if m1_rows:
            confirmed_open = int(
                str(item["confirmedByBarId"]).split(":", 1)[1]
            )
            known_at = confirmed_open + timeframe_seconds[timeframe]
            later_rows = [
                row for row in m1_rows
                if int(str(row["barId"]).split(":", 1)[1]) >= known_at
            ]
        elif confirmed_index is not None:
            later_rows = rows[confirmed_index + 1:]
        else:
            later_rows = []
        if confirmed_index is not None:
            for row in later_rows:
                if (
                    item["side"] == "BSL"
                    and float(row["h"]) >= float(item["price"])
                ) or (
                    item["side"] == "SSL"
                    and float(row["l"]) <= float(item["price"])
                ):
                    consumed_by = str(row["barId"])
                    break
        item["status"] = "CONSUMED" if consumed_by else "ACTIVE"
        item["consumedByBarId"] = consumed_by

    candidates.sort(
        key=lambda item: int(str(item["barId"]).split(":", 1)[1]), reverse=True
    )
    current_price = next(
        (
            float(rows[-1]["c"])
            for timeframe in ("M1", "M15", "M30", "H1")
            if (rows := compact.get(timeframe))
        ),
        0.0,
    )
    selected: list[dict[str, Any]] = []
    selected_keys: set[tuple[str, str]] = set()

    def add(item: dict[str, Any]) -> None:
        key = (str(item["barId"]), str(item["side"]))
        if key not in selected_keys:
            selected.append(item)
            selected_keys.add(key)

    active = [item for item in candidates if item["status"] == "ACTIVE"]
    # Preserve one nearest live objective for every map TF and side before
    # adding recent context. A recency-only cap can otherwise remove every
    # valid objective on one side of price during a strong one-way excursion.
    for timeframe in ("H1", "M30", "M15"):
        for side in ("BSL", "SSL"):
            group = [
                item for item in active
                if item["tf"] == timeframe and item["side"] == side
            ]
            if group:
                add(min(group, key=lambda item: abs(float(item["price"]) - current_price)))
    for side in ("BSL", "SSL"):
        directional = [
            item for item in active
            if item["side"] == side
            and (
                (side == "BSL" and float(item["price"]) >= current_price)
                or (side == "SSL" and float(item["price"]) <= current_price)
            )
        ]
        for item in sorted(
            directional,
            key=lambda candidate: abs(float(candidate["price"]) - current_price),
        )[:4]:
            add(item)
    for item in candidates:
        add(item)
        if len(selected) >= max(1, int(maximum)):
            break
    return selected[:max(1, int(maximum))]


def structural_liquidity_table(
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    """Encode candidates without repeating JSON keys for every row."""
    return {
        "columns": [
            "barId", "tf", "side", "price", "confirmedByBarId",
            "candidateKind", "prominencePrice", "reactionExcursionPrice",
            "barsSinceConfirmed", "status", "consumedByBarId",
        ],
        "data": [
            [
                item["barId"], item["tf"], item["side"],
                item["price"], item["confirmedByBarId"], item["candidateKind"],
                round(float(item["prominencePrice"]), 8),
                round(float(item["reactionExcursionPrice"]), 8),
                int(item["barsSinceConfirmed"]),
                item["status"], item["consumedByBarId"],
            ]
            for item in candidates
        ],
        "totalCount": len(candidates),
        "omittedCount": 0,
    }


def refinement_candidates(
    compact: dict[str, list[dict[str, Any]]],
    scenario: dict[str, Any],
    *,
    maximum: int = 24,
) -> list[dict[str, Any]]:
    """Enumerate lower-TF opposite candles and their first post-availability touch."""
    root = scenario["rootOb"]
    direction = str(scenario["direction"])
    root_tf = str(root["tf"])
    ladder = ["H1", "M30", "M15", "M5"]
    root_rank = ladder.index(root_tf)
    allowed = set(ladder[root_rank + 1:]) & {"M30", "M15", "M5"}
    seconds = {"M30": 1800, "M15": 900, "M5": 300}
    root_low, root_high = float(root["low"]), float(root["high"])
    root_time = parse_utc(str(root["originTime"]))
    m1_rows = compact.get("M1", [])
    result: list[dict[str, Any]] = []
    for timeframe in ("M30", "M15", "M5"):
        if timeframe not in allowed:
            continue
        timeframe_rows = compact.get(timeframe, [])
        for row_index, row in enumerate(timeframe_rows):
            origin = parse_utc(str(row["time"]))
            if origin < root_time or float(row["l"]) > root_high or float(row["h"]) < root_low:
                continue
            opposite = (
                direction == "LONG" and float(row["c"]) < float(row["o"])
            ) or (
                direction == "SHORT" and float(row["c"]) > float(row["o"])
            )
            if not opposite:
                continue
            delivery = next((
                candidate
                for candidate in timeframe_rows[row_index + 1:row_index + 4]
                if (
                    direction == "LONG"
                    and float(candidate["c"]) > float(row["h"])
                ) or (
                    direction == "SHORT"
                    and float(candidate["c"]) < float(row["l"])
                )
            ), None)
            origin_available = origin + seconds[timeframe]
            m1_delivery = next((
                item for item in m1_rows
                if parse_utc(str(item["time"])) >= origin_available
                and (
                    (direction == "LONG" and float(item["c"]) > float(row["h"]))
                    or (direction == "SHORT" and float(item["c"]) < float(row["l"]))
                )
            ), None)
            if delivery is None and m1_delivery is None:
                continue
            delivery_available = (
                parse_utc(str(delivery["time"])) + seconds[timeframe]
                if delivery is not None
                else parse_utc(str(m1_delivery["time"])) + 60
            )
            touch = next((
                item for item in m1_rows
                if parse_utc(str(item["time"])) >= delivery_available
                and float(item["l"]) <= float(row["h"])
                and float(item["h"]) >= float(row["l"])
            ), None)
            result.append({
                "barId": row["barId"], "tf": timeframe,
                "low": float(row["l"]), "high": float(row["h"]),
                "deliveryBarId": (
                    delivery["barId"] if delivery is not None else m1_delivery["barId"]
                ),
                "firstTouchBarId": touch["barId"] if touch else None,
            })
    # Within one delivery episode the mentor OB is the last opposite candle
    # before displacement, not every earlier opposite fragment of that candle.
    by_delivery: dict[tuple[str, str], dict[str, Any]] = {}
    for item in result:
        key = (str(item["tf"]), str(item["deliveryBarId"]))
        existing = by_delivery.get(key)
        if existing is None or int(str(item["barId"]).split(":", 1)[1]) > int(
            str(existing["barId"]).split(":", 1)[1]
        ):
            by_delivery[key] = item
    result = list(by_delivery.values())
    result.sort(
        key=lambda item: int(str(item["barId"]).split(":", 1)[1]), reverse=True
    )
    return result[:max(1, int(maximum))]


def refinement_candidate_table(
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "columns": ["barId", "tf", "low", "high", "deliveryBarId", "firstTouchBarId"],
        "data": [
            [
                item["barId"], item["tf"], item["low"], item["high"],
                item["deliveryBarId"], item["firstTouchBarId"],
            ]
            for item in candidates
        ],
        "totalCount": len(candidates),
        "omittedCount": 0,
    }


def resolve_bar(compact: dict[str, list[dict[str, Any]]], selected_id: str) -> dict[str, Any]:
    try:
        return bar_lookup(compact)[selected_id]
    except KeyError as exc:
        raise ValueError(f"unknown or unavailable barId: {selected_id}") from exc


def evidence_for_bars(
    compact: dict[str, list[dict[str, Any]]], selected_ids: list[str], point: float
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for selected_id in dict.fromkeys(selected_ids):
        row = resolve_bar(compact, selected_id)
        timeframe = selected_id.split(":", 1)[0]
        seconds = {"H1": 3600, "M30": 1800, "M15": 900, "M5": 300, "M1": 60}[timeframe]
        grouped.setdefault(timeframe, []).append({
            "openTimeUtc": row["time"],
            "availableTimeUtc": utc_text(parse_utc(str(row["time"])) + seconds),
            "open": row["o"], "high": row["h"], "low": row["l"], "close": row["c"],
            "spreadPrice": float(row.get("spreadPoints", 0.0)) * point,
            "barId": selected_id,
        })
    return [
        {"queryId": f"barid-{timeframe.lower()}", "tf": timeframe,
         "requestedAroundTimeUtc": rows[-1]["openTimeUtc"], "purpose": "BAR_ID_RESOLUTION",
         "candles": rows}
        for timeframe, rows in grouped.items()
    ]


def map_scout_prompt(contract: str, packet: dict[str, Any]) -> str:
    payload = {key: value for key, value in packet.items() if key != "images"}
    return (
        contract
        + "\n\n[MAP_SCOUT V2]\n"
        + "This is candidate discovery only. Do not find refinement, sweep, CHoCH, entry, SL, or TP. "
          "Compare all three scopes and select at most three plausible root-OB/objective pairs. "
          "compactBars is columnar: read each row using its columns array. Use only listed barId values. "
          "Never write a price or invent a candle. structuralLiquidityCandidates is columnar: "
          "read rows by columns. objectiveBarId must match an ACTIVE row and side; CONSUMED is context only. "
          "These extrema are only "
          "search candidates; independently reject recent pivots that are not real stop pools. "
          "packet.localTriggerWakeup, when present, is only a timing alarm from broad OHLC activity; "
          "it cannot prove a root OB, direction, objective, or entry. Rebuild the map from H1/M30/M15. "
          "A candidate is allowed to be incomplete; the reviewer decides causality. Return JSON only.\n\n"
        + "[PACKET]\n"
        + __import__("json").dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )


def map_review_prompt(
    contract: str,
    packet: dict[str, Any],
    candidates: list[dict[str, Any]],
    previous_candidate: dict[str, Any] | None,
) -> str:
    # The reviewer receives resolved candidate OHLC plus the chart image. Repeating
    # the entire scout bar table would double MAP input without adding evidence.
    payload = {
        key: value
        for key, value in packet.items()
        if key not in {"images", "compactBars", "structuralLiquidityCandidates"}
    }
    def compact_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
        compact_candidate = {
            key: candidate.get(key)
            for key in (
                "candidateId", "direction", "rootBarId",
                "objectiveBarId", "objectiveSide",
            )
        }
        for source_key in ("resolvedRootOhlc", "resolvedObjectiveOhlc"):
            source = candidate.get(source_key)
            if isinstance(source, dict):
                compact_candidate[source_key] = {
                    key: source.get(key)
                    for key in ("barId", "o", "h", "l", "c")
                }
        structure = candidate.get("objectiveStructure")
        if isinstance(structure, dict):
            compact_candidate["objectiveStructure"] = {
                key: structure.get(key)
                for key in (
                    "tf", "side", "prominencePrice",
                    "reactionExcursionPrice", "barsSinceConfirmed",
                )
            }
        return compact_candidate

    prompt_candidates = [compact_candidate(candidate) for candidate in candidates]
    prompt_previous = (
        compact_candidate(previous_candidate)
        if isinstance(previous_candidate, dict)
        else None
    )
    return (
        contract
        + "\n\n[MAP_REVIEW V2]\n"
        + "Review only root OB and objective causality under AGENTS.md. Refinement and M1 trigger are "
          "not required and must not be discussed as missing MAP evidence. Prices are engine-owned and "
          "already resolved from barId OHLC. APPROVE means the root is being approached/touched and "
          "refinement should begin now. WATCH means the map is causal but price is not yet at the root. "
          "REJECT means the root/objective pair itself is invalid or ambiguous. Compare every supplied "
          "candidate before selecting one; do not reject the batch merely because the first candidate "
          "is invalid. A LOCAL_ROOT suffix is only a timing-detector alternative and has no authority; "
          "approve it only when chart/OHLC causality independently proves it. Independently return the "
          "correct scope and objectiveType; a source candle's timeframe does not make its wick external. "
          "Scout scope labels and prose are intentionally absent to prevent anchoring; classify from the "
          "chart, root/objective OHLC, and the frozen scope definitions only. "
          "objectiveStructure is descriptive evidence, not a score. Compare prominence, completed "
          "reaction excursion, and age to reject a recent minor pivot that is not a mature stop pool. "
          "A fresh opposite M30 displacement inside an intact H1 range is INTERNAL_ROTATION, not "
          "EXTERNAL_CONTINUATION, unless the evidence explicitly proves that direction was already the "
          "H1/M30 external owner. An H1 candle low can still be the first internal objective. "
          "Do not claim that nearer internal liquidity may be bypassed; that statement violates the "
          "INTERNAL_ROTATION contract. "
          "Select one candidateId.\n\n"
        + "[CANDIDATES]\n"
        + __import__("json").dumps(prompt_candidates, ensure_ascii=False, separators=(",", ":"))
        + "\n\n[PREVIOUS WATCHED CANDIDATE]\n"
        + __import__("json").dumps(prompt_previous, ensure_ascii=False, separators=(",", ":"))
        + "\n\n[PACKET]\n"
        + __import__("json").dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )


def stage_prompt(
    contract: str,
    packet: dict[str, Any],
    phase: str,
    previous: dict[str, Any],
) -> str:
    payload = {key: value for key, value in packet.items() if key != "images"}
    tasks = {
        "REFINEMENT": (
            "compactBars is columnar: read each row using its columns array. "
            "Select only causal M30/M15/M5 child OB candles by compactBars barId. "
            "packet.refinementCandidates is columnar and lists lower-TF opposite candles whose "
            "following same-TF body delivery broke their distal boundary, plus the first later touch, so you do not "
            "need to search every bar; it does not prove parent-child causality. "
            "Choose at most one candidate per timeframe and order childBarIds M30 then M15 then M5. "
            "Same-TF rows compete; never place both in one path. If a unique causal lower-TF row explains "
            "the same delivery, make it the final child rather than stopping at a wider parent. "
            "Do not repeat or modify the frozen map. Price overlap alone is insufficient. "
            "M1 rows are restricted to bars at or after the frozen MAP time. If one of those rows "
            "touches the final child after availability, select its exact touchBarId. Otherwise still "
            "select the causal child, return a null touchBarId, and let the engine wait for its future retest."
        ),
        "TRIGGER": (
            "Judge only the post-touch M1 chain. ORDER requires seven M1 barIds: protected swing, "
            "pre-existing mature liquidity, later final sweep, sweep recovery, CHoCH reference, "
            "body-close break, and causal execution OB. The refined child touch must precede the sweep "
            "on a separate M1 candle; mature liquidity must precede and differ from the sweep. The sweep "
            "must pierce that wick, then sweepRecoveryBarId must close back inside on the same or a later "
            "candle before the CHoCH body break. "
            "ORDER means place the pending limit now, before the execution OB's first future retest; "
            "the engine performs the retest/fill simulation. Never WAIT because a valid execution "
            "OB has not yet been retested. WAIT only when the causal chain through execution-OB "
            "formation is incomplete. Do not write any price; the engine derives all geometry "
            "from those candles."
        ),
        "PENDING_REVIEW": (
            "Return KEEP or CANCEL for ordinary reauthorization. If packet.localDeliveryFvgCandidate "
            "identifies a newly closed three-candle FVG, REPLACE_DELIVERY_FVG may atomically cancel "
            "the still-unfilled original OB order and replace it. Select all five M1 barIds; keep the "
            "same owner, scope, root-child lineage and objective. A later or already retested FVG is invalid. "
            "An engineValidatedStructure candidate already proves the gap, directional displacement, "
            "latest confirmed swing body break, and opposite-color causal candle. Copy its five exact "
            "barIds into the replacement fields when owner/source/objective continuity remains valid. "
            "This call itself is the required H1/M15 reauthorization; do not reject merely because the "
            "previous lastReauthorizedAtUtc predates the current close. "
            "When the wake event is LOCAL_DELIVERY_FVG and this particular FVG lacks causal proof, return "
            "KEEP, not CANCEL: rejecting a screening FVG does not invalidate the frozen scenario."
        ),
    }
    return (
        contract + f"\n\n[{phase} V2]\n" + tasks[phase]
        + " Return JSON matching this phase schema only.\n\n[FROZEN STATE]\n"
        + __import__("json").dumps(previous, ensure_ascii=False, separators=(",", ":"))
        + "\n\n[PACKET]\n"
        + __import__("json").dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )


def _next_h1(as_of: str) -> str:
    value = parse_utc(as_of)
    return utc_text(((value // 3600) + 1) * 3600)


def _valid_until(as_of: str) -> str:
    return utc_text(parse_utc(as_of) + 24 * 3600)


def _zone(selected_id: str, row: dict[str, Any], direction: str, reason: str) -> dict[str, Any]:
    timeframe = selected_id.split(":", 1)[0]
    return {
        "tf": timeframe,
        "originTime": row["time"],
        "low": float(row["l"]),
        "high": float(row["h"]),
        "direction": "BULLISH" if direction == "LONG" else "BEARISH",
        "causalReason": reason,
    }


def canonical_map_decision(
    *,
    as_of: str,
    review: dict[str, Any],
    candidates: list[dict[str, Any]],
    compact: dict[str, list[dict[str, Any]]],
    watch_review_minutes: int = 360,
    delivery_wakeup: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    action = str(review.get("action", "REJECT"))
    candidate_id = str(review.get("candidateId", ""))
    candidate = next((item for item in candidates if str(item.get("candidateId")) == candidate_id), None)
    if action in {"APPROVE", "WATCH"} and candidate is None:
        raise ValueError("MAP_REVIEW selected an unknown candidateId")
    if candidate is None or action in {"REJECT", "DATA_ERROR"}:
        return ({
            "schemaVersion": "1.5.0", "asOfUtc": as_of, "phase": "MAP",
            "_v2MapDecision": True,
            "action": "NO_TRADE", "state": "FLAT", "scenario": None,
            "candleQueries": [], "watchEvents": [], "nextReviewAtUtc": _next_h1(as_of),
            "order": None, "rejectionReasons": [str(review.get("reason", "MAP rejected"))],
            "reason": str(review.get("reason", "MAP rejected")),
        }, [])

    direction = str(candidate["direction"])
    expected_side = "BSL" if direction == "LONG" else "SSL"
    if str(candidate["objectiveSide"]) != expected_side:
        raise ValueError("MAP candidate objective side conflicts with direction")
    root_id, objective_id = str(candidate["rootBarId"]), str(candidate["objectiveBarId"])
    root_row, objective_row = resolve_bar(compact, root_id), resolve_bar(compact, objective_id)
    root = _zone(root_id, root_row, direction, str(review.get("rootCausality", "")))
    objective_price = float(objective_row["h"] if expected_side == "BSL" else objective_row["l"])
    reviewed_scope = str(review.get("scope") or candidate["scope"])
    reviewed_objective_type = str(
        review.get("objectiveType") or candidate["objectiveType"]
    )
    if reviewed_scope not in {
        "EXTERNAL_CONTINUATION", "INTERNAL_ROTATION", "EXTERNAL_REVERSAL"
    }:
        raise ValueError("MAP_REVIEW returned an invalid scope")
    if reviewed_objective_type not in {
        "EXTERNAL_LIQUIDITY", "INTERNAL_LIQUIDITY"
    }:
        raise ValueError("MAP_REVIEW returned an invalid objectiveType")
    reviewed_candidate = copy.deepcopy(candidate)
    reviewed_candidate["scope"] = reviewed_scope
    reviewed_candidate["objectiveType"] = reviewed_objective_type
    scenario = {
        "scenarioId": f"MAP2-{candidate_id}-{parse_utc(as_of)}",
        "frozenAtUtc": as_of,
        "direction": direction,
        "scope": reviewed_scope,
        "objective": {
            "type": reviewed_objective_type, "side": expected_side,
            "price": objective_price, "sourceTf": objective_id.split(":", 1)[0],
            "sourceTime": objective_row["time"],
        },
        "rootOb": root,
        "refinementPath": [],
        "rootInvalidation": float(root["low"] if direction == "LONG" else root["high"]),
        "sourceInvalidation": float(root["low"] if direction == "LONG" else root["high"]),
        "mapCandidate": {
            key: copy.deepcopy(value)
            for key, value in reviewed_candidate.items()
            if key not in {"resolvedRootOhlc", "resolvedObjectiveOhlc"}
        },
    }
    valid_until = _valid_until(as_of)
    events = [
        {
            "eventId": "map-root-approach", "kind": "ROOT_APPROACH",
            "comparison": "CROSS_BELOW" if direction == "LONG" else "CROSS_ABOVE",
            "price": float(root["high"] if direction == "LONG" else root["low"]),
            "sourceTf": root["tf"], "sourceTimeUtc": root["originTime"], "validUntilUtc": valid_until,
        },
        {
            "eventId": "map-source-invalidation", "kind": "SOURCE_INVALIDATION",
            "comparison": "CROSS_BELOW" if direction == "LONG" else "CROSS_ABOVE",
            "price": float(scenario["sourceInvalidation"]), "sourceTf": root["tf"],
            "sourceTimeUtc": root["originTime"], "validUntilUtc": valid_until,
        },
        {
            "eventId": "map-objective-reached", "kind": "OBJECTIVE_REACHED",
            "comparison": "CROSS_ABOVE" if direction == "LONG" else "CROSS_BELOW",
            "price": objective_price, "sourceTf": scenario["objective"]["sourceTf"],
            "sourceTimeUtc": scenario["objective"]["sourceTime"], "validUntilUtc": valid_until,
        },
    ]
    # MAP discovery cannot retroactively consume an old root touch. APPROVE is
    # actionable only when the latest closed M1 bar is touching the root now;
    # WATCH always waits for a future engine-observed approach.
    latest_m1 = compact.get("M1", [])[-1] if compact.get("M1") else None
    current_touch = bool(
        latest_m1
        and float(latest_m1["l"]) <= float(root["high"])
        and float(latest_m1["h"]) >= float(root["low"])
    )
    # A flat delivery alarm may wake MAP discovery, but it cannot create a
    # retroactive original OB order. AGENTS.md requires owner/root/child to be
    # frozen before the delivery displacement exists.
    prepared = action == "APPROVE" and current_touch
    decision = {
        "schemaVersion": "1.5.0", "asOfUtc": as_of, "phase": "MAP",
        "_v2MapDecision": True,
        "action": "PREPARE" if prepared else "WATCH_MAP",
        "state": "PREPARED" if prepared else "WATCHING_MAP",
        "scenario": scenario, "candleQueries": [], "watchEvents": events,
        "nextReviewAtUtc": (
            _next_h1(as_of)
            if prepared
            else utc_text(parse_utc(as_of) + max(60, int(watch_review_minutes)) * 60)
        ),
        "reason": (
            str(review.get("reason", ""))
            + " Compared EXTERNAL_CONTINUATION, INTERNAL_ROTATION, and EXTERNAL_REVERSAL."
        ).strip(),
    }
    return decision, [root_id, objective_id]


def canonical_stage_decision(
    *,
    as_of: str,
    phase: str,
    payload: dict[str, Any],
    previous: dict[str, Any],
    compact: dict[str, list[dict[str, Any]]],
    point: float,
    broker_stops: float,
    spread_price: float,
) -> tuple[dict[str, Any], list[str]]:
    scenario = copy.deepcopy(previous.get("scenario"))
    order = copy.deepcopy(previous.get("order"))
    action = str(payload.get("action", "DATA_ERROR"))
    next_review = utc_text(parse_utc(as_of) + (3600 if phase != "PENDING_REVIEW" else 900))
    selected_ids: list[str] = []

    if phase == "REFINEMENT":
        ignored_touch_reason = ""
        if action == "QUERY_CANDLES":
            canonical_action, state = "QUERY_CANDLES", "PREPARED"
        elif action == "CANCEL" or action == "DATA_ERROR":
            canonical_action, state, scenario = "CANCEL", "CANCELED", scenario
        elif action == "SELECT_CHILD":
            selected_ids = [str(item) for item in payload.get("childBarIds", [])]
            if not selected_ids:
                raise ValueError("SELECT_CHILD requires childBarIds")
            allowed_child_ids = {
                str(item["barId"])
                for item in refinement_candidates(compact, scenario)
            }
            invalid_child_ids = [
                item for item in selected_ids if item not in allowed_child_ids
            ]
            if invalid_child_ids:
                raise ValueError(
                    "SELECT_CHILD used a root/non-candidate barId: "
                    + ",".join(invalid_child_ids)
                )
            selected_timeframes = [item.split(":", 1)[0] for item in selected_ids]
            if len(selected_timeframes) != len(set(selected_timeframes)):
                raise ValueError("SELECT_CHILD may contain at most one candidate per timeframe")
            refinement_rank = {"M30": 0, "M15": 1, "M5": 2}
            selected_ranks = [refinement_rank[item] for item in selected_timeframes]
            if selected_ranks != sorted(selected_ranks):
                raise ValueError("SELECT_CHILD path must be ordered from higher TF to lower TF")
            children = [
                _zone(item, resolve_bar(compact, item), str(scenario["direction"]), str(payload.get("reason", "")))
                for item in selected_ids
            ]
            scenario["refinementPath"] = children
            last = children[-1]
            # A proven causal child inherits execution invalidation authority.
            # The wider root remains frozen separately for map ownership.
            scenario.setdefault("rootInvalidation", scenario.get("sourceInvalidation"))
            scenario["sourceInvalidation"] = float(
                last["low"] if scenario["direction"] == "LONG" else last["high"]
            )
            touch_id = str(payload.get("touchBarId") or "")
            touched = False
            if touch_id:
                try:
                    touch = resolve_bar(compact, touch_id)
                except ValueError:
                    touch = None
                    ignored_touch_reason = "unavailable touchBarId"
                child_seconds = {"M30": 1800, "M15": 900, "M5": 300}[str(last["tf"])]
                child_available = parse_utc(str(last["originTime"])) + child_seconds
                frozen_at = scenario.get("frozenAtUtc")
                if not frozen_at:
                    raise ValueError("scenario is missing frozenAtUtc")
                if touch is not None:
                    touch_time = parse_utc(str(touch["time"]))
                    if touch_time < child_available:
                        ignored_touch_reason = "touch predates child OB availability"
                    elif touch_time < parse_utc(str(frozen_at)):
                        ignored_touch_reason = "touch predates frozen MAP scenario"
                    elif not (
                        float(touch["l"]) <= float(last["high"])
                        and float(touch["h"]) >= float(last["low"])
                    ):
                        ignored_touch_reason = "touch does not overlap final child OB"
                    else:
                        touched = True
                        selected_ids.append(touch_id)
                        scenario["refinedTouchBarId"] = touch_id
                        scenario["refinedTouchTimeUtc"] = touch["time"]
            canonical_action, state = ("ARM", "ARMED") if touched else ("WAIT", "PREPARED")
            if not touched:
                child_spread = float(resolve_bar(compact, selected_ids[-1]).get("spreadPoints", 0.0)) * point
                buffer = max(point, broker_stops, spread_price, child_spread)
                direction = str(scenario["direction"])
                entry = float(last["high"] if direction == "LONG" else last["low"])
                distal = float(last["low"] if direction == "LONG" else last["high"])
                stop = distal - buffer if direction == "LONG" else distal + buffer
                order = {
                    "executionModel": "HTF_OB_REACTION_INTENT",
                    "intentOnly": True,
                    "entry": entry,
                    "stopLoss": stop,
                    "takeProfit": float(scenario["objective"]["price"]),
                    "rootOriginTime": scenario["rootOb"]["originTime"],
                    "childOriginTime": last["originTime"],
                    "objectiveSourceTime": scenario["objective"]["sourceTime"],
                    "actualSpread": max(spread_price, child_spread),
                    "brokerStopsLevelPrice": broker_stops,
                    "slBuffer": buffer,
                    "lastReauthorizedAtUtc": as_of,
                }
        else:
            canonical_action, state = "WAIT", "PREPARED"
        queries = list(payload.get("candleQueries") or []) if canonical_action == "QUERY_CANDLES" else []
        events: list[dict[str, Any]] = []
        if isinstance(scenario, dict) and scenario.get("refinementPath"):
            child = scenario["refinementPath"][-1]
            events.append({
                "eventId": "engine-final-child-touch", "kind": "CHILD_TOUCH", "comparison": "TOUCH",
                "price": float(child["high"] if scenario["direction"] == "LONG" else child["low"]),
                "sourceTf": child["tf"], "sourceTimeUtc": child["originTime"], "validUntilUtc": _valid_until(as_of),
            })
        return ({
            "schemaVersion": "1.5.0", "asOfUtc": as_of, "phase": phase,
            "action": canonical_action, "state": state, "scenario": scenario,
            "candleQueries": queries, "watchEvents": events, "nextReviewAtUtc": next_review,
            "order": order,
            "rejectionReasons": (
                [f"IGNORED_HISTORICAL_TOUCH: {ignored_touch_reason}"]
                if action == "SELECT_CHILD" and ignored_touch_reason else []
            ),
            "reason": (
                str(payload.get("reason", ""))
                + (
                    f" Historical touch ignored ({ignored_touch_reason}); waiting for a future child retest."
                    if action == "SELECT_CHILD" and ignored_touch_reason else ""
                )
            ).strip(),
        }, selected_ids)

    if phase == "TRIGGER":
        if action == "QUERY_CANDLES":
            canonical_action, state = "QUERY_CANDLES", "ARMED"
            queries = list(payload.get("candleQueries") or [])
        elif action == "CANCEL" or action == "DATA_ERROR":
            canonical_action, state, queries = "CANCEL", "CANCELED", []
        elif action == "ORDER":
            if payload.get("executionModel") != "HTF_OB_REACTION":
                raise ValueError("TRIGGER may create only the initial HTF_OB_REACTION order")
            fields = [
                "protectedSwingBarId", "matureLiquidityBarId", "sweepBarId",
                "sweepRecoveryBarId", "chochReferenceBarId", "chochBreakBarId",
                "executionBarId",
            ]
            selected_ids = [str(payload.get(field) or "") for field in fields]
            if any(not item.startswith("M1:") for item in selected_ids):
                raise ValueError("TRIGGER ORDER requires seven available M1 barIds")
            protected, mature, sweep, recovery, reference, break_bar = [
                resolve_bar(compact, item) for item in selected_ids[:6]
            ]
            direction = str(scenario["direction"])
            touch_id = str(scenario.get("refinedTouchBarId") or "")
            if not touch_id.startswith("M1:"):
                raise ValueError("TRIGGER ORDER requires frozen refined child touch evidence")
            touch = resolve_bar(compact, touch_id)
            touch_time = parse_utc(str(touch["time"]))
            mature_time = parse_utc(str(mature["time"]))
            sweep_time = parse_utc(str(sweep["time"]))
            recovery_time = parse_utc(str(recovery["time"]))
            reference_time = parse_utc(str(reference["time"]))
            break_time = parse_utc(str(break_bar["time"]))
            if not touch_time < sweep_time:
                raise ValueError("final sweep must occur after refined child touch on a later M1 bar")
            if not mature_time < sweep_time:
                raise ValueError("swept liquidity must be mature before the final sweep")
            if str(payload["matureLiquidityBarId"]) == str(payload["sweepBarId"]):
                raise ValueError("mature liquidity and final sweep cannot be the same M1 candle")
            if str(payload["sweepBarId"]) == str(payload["chochBreakBarId"]):
                raise ValueError("final sweep and CHoCH break cannot be the same M1 candle")
            if str(payload["chochReferenceBarId"]) == str(payload["chochBreakBarId"]):
                raise ValueError("CHoCH reference and break cannot be the same M1 candle")
            if not sweep_time <= recovery_time < break_time:
                raise ValueError("sweep recovery must occur from the sweep candle through before CHoCH")
            if not sweep_time < break_time or not reference_time < break_time:
                raise ValueError("CHoCH break must follow the final sweep and live reference")
            mature_price = float(mature["l"] if direction == "LONG" else mature["h"])
            if direction == "LONG" and not (
                float(sweep["l"]) < mature_price and float(recovery["c"]) > mature_price
            ):
                raise ValueError("LONG final sweep must pierce mature SSL and recover above it before CHoCH")
            if direction == "SHORT" and not (
                float(sweep["h"]) > mature_price and float(recovery["c"]) < mature_price
            ):
                raise ValueError("SHORT final sweep must pierce mature BSL and recover below it before CHoCH")
            reference_price_check = float(reference["h"] if direction == "LONG" else reference["l"])
            if direction == "LONG" and float(break_bar["c"]) <= reference_price_check:
                raise ValueError("LONG CHoCH requires a body close above the live reference")
            if direction == "SHORT" and float(break_bar["c"]) >= reference_price_check:
                raise ValueError("SHORT CHoCH requires a body close below the live reference")
            execution = resolve_bar(compact, selected_ids[6])
            execution_time = parse_utc(str(execution["time"]))
            opposite_execution = (
                direction == "LONG" and float(execution["c"]) < float(execution["o"])
            ) or (
                direction == "SHORT" and float(execution["c"]) > float(execution["o"])
            )
            if not opposite_execution or not sweep_time <= execution_time <= break_time:
                causal_candidates = [
                    row for row in compact.get("M1", [])
                    if sweep_time <= parse_utc(str(row["time"])) <= break_time
                    and (
                        (direction == "LONG" and float(row["c"]) < float(row["o"]))
                        or (direction == "SHORT" and float(row["c"]) > float(row["o"]))
                    )
                ]
                if not causal_candidates:
                    raise ValueError("no opposite-color causal execution OB exists in the sweep-to-CHoCH displacement")
                execution = causal_candidates[-1]
                selected_ids[6] = str(execution["barId"])
                execution_time = parse_utc(str(execution["time"]))
            execution_spread = float(execution.get("spreadPoints", 0.0)) * point
            buffer = max(point, broker_stops, spread_price, execution_spread)
            execution_low, execution_high = float(execution["l"]), float(execution["h"])
            protected_price = float(protected["l"] if direction == "LONG" else protected["h"])
            sweep_price = float(sweep["l"] if direction == "LONG" else sweep["h"])
            reference_price = float(reference["h"] if direction == "LONG" else reference["l"])
            entry = execution_high if direction == "LONG" else execution_low
            child = scenario["refinementPath"][-1]
            scenario_invalidation = float(scenario["sourceInvalidation"])
            stop = (
                min(execution_low, protected_price, sweep_price, float(child["low"]), scenario_invalidation) - buffer
                if direction == "LONG"
                else max(execution_high, protected_price, sweep_price, float(child["high"]), scenario_invalidation) + buffer
            )
            order = {
                "executionModel": payload["executionModel"],
                "entry": entry, "stopLoss": stop, "takeProfit": float(scenario["objective"]["price"]),
                "rootOriginTime": scenario["rootOb"]["originTime"],
                "childOriginTime": scenario["refinementPath"][-1]["originTime"],
                "objectiveSourceTime": scenario["objective"]["sourceTime"],
                "executionOriginTime": execution["time"], "executionLow": execution_low,
                "executionHigh": execution_high,
                "triggerLineage": f"P={protected['time']};S={sweep['time']};R={reference['time']};B={break_bar['time']}",
                "triggerProtectedSwing": protected_price,
                "triggerProtectedSwingSourceTimeUtc": protected["time"],
                "matureLiquidityPrice": mature_price,
                "matureLiquiditySourceTimeUtc": mature["time"],
                "sweepRecoveryTimeUtc": recovery["time"],
                "refinedTouchBarId": touch_id,
                "refinedTouchTimeUtc": touch["time"],
                "sweepExtreme": sweep_price, "sweepExtremeSourceTimeUtc": sweep["time"],
                "chochReferencePrice": reference_price, "chochReferenceSourceTimeUtc": reference["time"],
                "chochBreakTimeUtc": break_bar["time"], "actualSpread": execution_spread,
                "brokerStopsLevelPrice": broker_stops, "slBuffer": buffer,
                "lastReauthorizedAtUtc": as_of,
            }
            canonical_action, state, queries = "ORDER", "PENDING", []
        else:
            canonical_action, state, queries = "WAIT", "ARMED", []
        return ({
            "schemaVersion": "1.5.0", "asOfUtc": as_of, "phase": phase,
            "action": canonical_action, "state": state, "scenario": scenario,
            "candleQueries": queries, "watchEvents": [], "nextReviewAtUtc": next_review,
            "order": order if canonical_action == "ORDER" else None,
            "rejectionReasons": [], "reason": str(payload.get("reason", "")),
        }, selected_ids)

    if phase == "PENDING_REVIEW":
        if action == "REPLACE_DELIVERY_FVG":
            if (
                not isinstance(order, dict)
                or order.get("executionModel") not in {
                    "HTF_OB_REACTION", "HTF_OB_REACTION_INTENT",
                }
            ):
                raise ValueError("delivery FVG replacement requires one unfilled original OB order")
            fields = [
                "fvgLeftBarId", "fvgMiddleBarId", "fvgRightBarId",
                "causalObBarId", "deliveryProtectedSwingBarId",
            ]
            selected_ids = [str(payload.get(field) or "") for field in fields]
            if any(not item.startswith("M1:") for item in selected_ids):
                raise ValueError("DELIVERY_FVG_REPLACEMENT requires five available M1 barIds")
            left, middle, right, causal_ob, protected = [
                resolve_bar(compact, item) for item in selected_ids
            ]
            times = [parse_utc(str(item["time"])) for item in (left, middle, right)]
            if not (times[1] == times[0] + 60 and times[2] == times[1] + 60):
                raise ValueError("delivery FVG bars must be three consecutive M1 candles")
            if times[2] + 60 != parse_utc(as_of):
                raise ValueError("delivery FVG replacement must be decided when the right candle closes")
            direction = str(scenario["direction"])
            if direction == "LONG":
                if not float(left["h"]) < float(right["l"]):
                    raise ValueError("selected candles do not form a bullish FVG")
                if not float(middle["c"]) > float(middle["o"]):
                    raise ValueError("bullish delivery FVG requires bullish displacement")
                if not float(middle["c"]) > float(protected["h"]):
                    raise ValueError("bullish delivery did not body-break its protected swing")
                if not float(causal_ob["c"]) < float(causal_ob["o"]):
                    raise ValueError("bullish delivery causal OB must be bearish")
                zone_low, zone_high = float(left["h"]), float(right["l"])
            else:
                if not float(left["l"]) > float(right["h"]):
                    raise ValueError("selected candles do not form a bearish FVG")
                if not float(middle["c"]) < float(middle["o"]):
                    raise ValueError("bearish delivery FVG requires bearish displacement")
                if not float(middle["c"]) < float(protected["l"]):
                    raise ValueError("bearish delivery did not body-break its protected swing")
                if not float(causal_ob["c"]) > float(causal_ob["o"]):
                    raise ValueError("bearish delivery causal OB must be bullish")
                zone_low, zone_high = float(right["h"]), float(left["l"])
            causal_time = parse_utc(str(causal_ob["time"]))
            protected_time = parse_utc(str(protected["time"]))
            if causal_time > times[1] or protected_time >= times[1]:
                raise ValueError("delivery causal OB/protected swing must predate the displacement close")
            current_spread = max(
                spread_price,
                float(right.get("spreadPoints", 0.0)) * point,
            )
            buffer = max(point, broker_stops, current_spread)
            # This bar is the swing broken by delivery: bullish delivery breaks
            # its high and bearish delivery breaks its low. It is evidence of
            # displacement, not the stop-side invalidation swing.
            protected_price = float(protected["h"] if direction == "LONG" else protected["l"])
            causal_distal = float(causal_ob["l"] if direction == "LONG" else causal_ob["h"])
            original_stop = float(order["stopLoss"])
            stop = (
                min(original_stop, causal_distal - buffer)
                if direction == "LONG"
                else max(original_stop, causal_distal + buffer)
            )
            replacement = copy.deepcopy(order)
            replacement.update({
                "executionModel": "DELIVERY_FVG_REPLACEMENT",
                "entry": zone_high if direction == "LONG" else zone_low,
                "stopLoss": stop,
                "takeProfit": float(scenario["objective"]["price"]),
                "actualSpread": current_spread,
                "brokerStopsLevelPrice": broker_stops,
                "slBuffer": buffer,
                "lastReauthorizedAtUtc": as_of,
                "originalExecutionModel": order["executionModel"],
                "originalEntry": float(order["entry"]),
                "originalOrderCanceledAtUtc": as_of,
                "deliveryFvgLeftTimeUtc": left["time"],
                "deliveryFvgMiddleTimeUtc": middle["time"],
                "deliveryFvgRightTimeUtc": right["time"],
                "deliveryFvgLow": zone_low,
                "deliveryFvgHigh": zone_high,
                "deliveryCausalObTimeUtc": causal_ob["time"],
                "deliveryProtectedSwing": protected_price,
                "deliveryProtectedSwingTimeUtc": protected["time"],
                "deliveryFirstRetestRequired": True,
            })
            # The replacement is a live pending order, not the engine-owned
            # placeholder intent from which it was derived.
            replacement.pop("intentOnly", None)
            return ({
                "schemaVersion": "1.5.0", "asOfUtc": as_of, "phase": phase,
                "action": "ORDER", "state": "PENDING", "scenario": scenario,
                "candleQueries": [], "watchEvents": copy.deepcopy(previous.get("watchEvents") or []),
                "nextReviewAtUtc": next_review, "order": replacement,
                "rejectionReasons": [], "reason": str(payload.get("reason", "")),
            }, selected_ids)
        local_delivery_review = str(previous.get("_wakeEvent", "")) == "LOCAL_DELIVERY_FVG"
        # A broad local FVG wake-up is only a replacement screening event. A
        # rejected screening candidate cannot invalidate the frozen owner,
        # source lineage, or objective. Those are canceled only by their own
        # engine-routed safety events.
        keep = action == "KEEP" or local_delivery_review
        if keep and isinstance(order, dict):
            order["lastReauthorizedAtUtc"] = as_of
        watch_events = copy.deepcopy(previous.get("watchEvents") or [])
        if keep:
            # Safety events must remain live through the next pending review;
            # preserving their old expiry makes a valid KEEP immediately stale.
            for event in watch_events:
                event["validUntilUtc"] = next_review
        return ({
            "schemaVersion": "1.5.0", "asOfUtc": as_of, "phase": phase,
            "action": "ORDER" if keep else "CANCEL", "state": "PENDING" if keep else "CANCELED",
            "scenario": scenario, "candleQueries": [], "watchEvents": watch_events,
            "nextReviewAtUtc": next_review, "order": order if keep else None,
            "rejectionReasons": (
                ["LOCAL_DELIVERY_FVG_REJECTED_SCENARIO_PRESERVED"]
                if local_delivery_review and action != "KEEP" else []
            ),
            "reason": str(payload.get("reason", "")),
        }, [])
    raise ValueError(f"unsupported V2 stage: {phase}")
