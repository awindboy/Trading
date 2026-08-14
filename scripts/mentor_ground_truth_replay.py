from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "mentor_ground_truth_q1"
PACKETS = OUTPUT / "packets"
STATE_FILE = OUTPUT / "state.json"
LEDGER_FILE = OUTPUT / "ledger.jsonl"
SEAL_FILE = OUTPUT / "seal.json"
CURRENT_PACKET = OUTPUT / "current.png"
CURRENT_DRAFT = OUTPUT / "current_decision.json"
CURRENT_PRIMITIVES = OUTPUT / "current_primitives.json"
PROGRESS_FILE = OUTPUT / "PROGRESS.md"
UTC = timezone.utc

Q1_PERIOD_FROM = int(datetime(2025, 1, 1, tzinfo=UTC).timestamp())
REPLAY_FROM = int(datetime(2025, 1, 2, 8, 0, tzinfo=UTC).timestamp())
Q1_TO = int(datetime(2025, 4, 1, tzinfo=UTC).timestamp())
WARMUP_FROM = int(datetime(2024, 10, 1, tzinfo=UTC).timestamp())
ALLOWED_STEPS = {1, 5, 15, 30, 60, 240}
ALLOWED_STATES = {"NO_SCENARIO", "MAP_ONLY", "WATCH_SOURCE", "TRIGGER_PENDING", "ORDER_PLANNED", "POSITION_ACTIVE", "POSITION_CLOSED"}
ALLOWED_OBSERVATION_MODES = {
    "FIXED_STEP",
    "PRICE_TOUCH_OR_TIMEOUT",
    "FIRST_PRICE_EVENT_OR_TIMEOUT",
    "NEXT_CLOSED_BAR_OR_TIMEOUT",
    "NEXT_STRUCTURE_EVENT_OR_TIMEOUT",
}
FORBIDDEN_KEYS = {"result", "outcome", "pnl", "exit", "future", "algorithm", "candidate"}

from build_mentor_blind_q1_packets import aggregate, asof, load_rates, render_packet

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mentor_engine.models import BarSeries
from mentor_engine.structure import analyze_structure
from mentor_engine.zones import detect_zones


TF_SECONDS = {"H4": 14_400, "H1": 3_600, "M30": 1_800, "M15": 900, "M5": 300, "M1": 60}
STRUCTURE_TIMEFRAMES = tuple(TF_SECONDS)


def iso(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=UTC).isoformat()


def parse_iso(value: str) -> int:
    return int(datetime.fromisoformat(value).astimezone(UTC).timestamp())


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        raise SystemExit("Replay is not initialized. Run: python scripts\\mentor_ground_truth_replay.py init")
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def write_progress(state: dict[str, Any]) -> None:
    """Write a human-readable replay status without exposing future outcomes."""
    records: list[dict[str, Any]] = []
    if LEDGER_FILE.exists():
        records = [
            json.loads(line)
            for line in LEDGER_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    lines = [
        "# Mentor Q1 Independent Replay",
        "",
        f"- Status: {state['status']}",
        f"- Current decision time (UTC): {state['cursor_utc']}",
        f"- Completed decisions: {state['records']}",
        f"- Orders planned: {state['orders_planned']}",
        f"- Q1 end (UTC): {iso(Q1_TO)}",
        "- Current raw chart: `current.png`",
        "- Current unrecorded decision: `current_decision.json`",
        "",
        "## Recent Decisions",
        "",
        "| # | As-of UTC | State | Advance |",
        "|---:|---|---|---|",
    ]
    for record in records[-12:]:
        advance = record.get("advance_resolution", {})
        next_time = record.get("next_cursor_utc", "")
        lines.append(
            f"| {record['record_no']} | {record['as_of']} | {record['decision_state']} | "
            f"{advance.get('reason', 'UNKNOWN')} -> {next_time} |"
        )
    if not records:
        lines.append("| - | - | No recorded decision yet | - |")
    PROGRESS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def primitive_snapshot(rates: np.ndarray, cutoff: int) -> dict[str, Any]:
    """Expose only closed wave/structure primitives for a manual replay decision."""
    payload: dict[str, Any] = {"as_of": iso(cutoff), "timeframes": {}}
    for timeframe in ("H4", "H1", "M30", "M15", "M5", "M1"):
        bars = asof(aggregate(rates, timeframe), cutoff, len(rates))
        if not len(bars):
            payload["timeframes"][timeframe] = {"bars": 0}
            continue
        series = BarSeries(
            timeframe=timeframe,
            seconds={"H4": 14_400, "H1": 3_600, "M30": 1_800, "M15": 900, "M5": 300, "M1": 60}[timeframe],
            time=bars["time"],
            available_time=bars["available"],
            open=bars["open"],
            high=bars["high"],
            low=bars["low"],
            close=bars["close"],
            spread_points=np.ones(len(bars), dtype=float),
        )
        structure = analyze_structure(series)
        zones = detect_zones(series, structure)
        index = len(series) - 1
        recent_waves = [
            {
                "id": wave.object_id,
                "side": wave.side.value,
                "level": round(float(wave.level), 5),
                "occurred_at": iso(int(wave.occurred_at)),
                "available_at": iso(int(wave.available_at)),
                "rank": wave.rank,
            }
            for wave in structure.waves[-8:]
        ]
        recent_events = [
            {
                "id": event.event_id,
                "type": event.event_type,
                "direction": event.direction.value,
                "broken_level": round(float(event.broken_level), 5),
                "protected_level": None if event.protected_level is None else round(float(event.protected_level), 5),
                "available_at": iso(int(event.available_at)),
            }
            for event in structure.events[-8:]
        ]
        recent_zones = [
            {
                "id": zone.object_id,
                "family_id": zone.family_id,
                "kind": zone.kind.value,
                "direction": zone.direction.value,
                "bottom": round(float(zone.bottom), 5),
                "top": round(float(zone.top), 5),
                "available_at": iso(int(zone.available_at)),
                "linked_structure_event_id": zone.linked_structure_event_id,
            }
            for zone in zones
            if zone.available_at <= cutoff and zone.active_at(cutoff)
        ][-12:]
        payload["timeframes"][timeframe] = {
            "bars": len(series),
            "trend": int(structure.trend[index]),
            "protected_high": None if np.isnan(structure.protected_high[index]) else round(float(structure.protected_high[index]), 5),
            "protected_low": None if np.isnan(structure.protected_low[index]) else round(float(structure.protected_low[index]), 5),
            "range_low": None if np.isnan(structure.range_low[index]) else round(float(structure.range_low[index]), 5),
            "range_high": None if np.isnan(structure.range_high[index]) else round(float(structure.range_high[index]), 5),
            "waves": recent_waves,
            "events": recent_events,
            "zones": recent_zones,
        }
    return payload


def next_structure_event_cursor(cursor: int, timeout_cursor: int, timeframes: list[str]) -> int | None:
    """Advance the replay clock at a live structural event without disclosing its future contents."""
    rates = load_rates(WARMUP_FROM, timeout_cursor)
    next_available: int | None = None
    for timeframe in timeframes:
        bars = aggregate(rates, timeframe)
        if not len(bars):
            continue
        series = BarSeries(
            timeframe=timeframe,
            seconds=TF_SECONDS[timeframe],
            time=bars["time"],
            available_time=bars["available"],
            open=bars["open"],
            high=bars["high"],
            low=bars["low"],
            close=bars["close"],
            spread_points=np.ones(len(bars), dtype=float),
        )
        for event in analyze_structure(series).events:
            available_at = int(event.available_at)
            if cursor < available_at <= timeout_cursor and (
                next_available is None or available_at < next_available
            ):
                next_available = available_at
    return next_available


def command_init(force: bool) -> None:
    if STATE_FILE.exists() and not force:
        raise SystemExit("Replay already exists. Refusing to overwrite it without --force.")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    PACKETS.mkdir(parents=True, exist_ok=True)
    if force:
        for path in (LEDGER_FILE, SEAL_FILE, CURRENT_PACKET, CURRENT_DRAFT):
            if path.exists():
                path.unlink()
    state = {
        "schema": "mentor-ground-truth-replay-v1",
        "status": "ACTIVE",
        "cursor": REPLAY_FROM,
        "cursor_utc": iso(REPLAY_FROM),
        "q1_from": Q1_PERIOD_FROM,
        "first_market_cursor": REPLAY_FROM,
        "q1_to": Q1_TO,
        "records": 0,
        "orders_planned": 0,
        "last_record_hash": None,
    }
    save_state(state)
    write_progress(state)
    print(json.dumps(state, ensure_ascii=False, indent=2))


def render_current(state: dict[str, Any]) -> None:
    if state["status"] != "ACTIVE":
        raise SystemExit("Replay is already sealed.")
    write_progress(state)
    cursor = int(state["cursor"])
    rates = load_rates(WARMUP_FROM, min(cursor, Q1_TO))
    series = {timeframe: aggregate(rates, timeframe) for timeframe in ("H4", "H1", "M30", "M15", "M5", "M1")}
    stamp = datetime.fromtimestamp(cursor, tz=UTC).strftime("%Y-%m-%d_%H%M")
    packet = PACKETS / f"{stamp}.png"
    render_packet(series, cursor, packet)
    CURRENT_PACKET.write_bytes(packet.read_bytes())
    CURRENT_PRIMITIVES.write_text(
        json.dumps(primitive_snapshot(rates, cursor), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    draft = {
        "as_of": iso(cursor),
        "decision_state": "MAP_ONLY",
        "map": {
            "external_structure": "",
            "internal_structure": "",
            "delivery_direction": "UNRESOLVED",
            "map_timeframes": [],
        },
        "scenario": None,
        "no_trade_reason": "",
        "next_observation": {
            "mode": "NEXT_STRUCTURE_EVENT_OR_TIMEOUT",
            "timeframes": ["M1", "M5", "M15", "M30", "H1", "H4"],
            "timeout_minutes": 720,
        },
    }
    CURRENT_DRAFT.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"AS_OF={iso(cursor)}")
    print(f"PACKET={packet}")
    print(f"PRIMITIVES={CURRENT_PRIMITIVES}")
    print(f"DRAFT={CURRENT_DRAFT}")


def forbidden_paths(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            if key.lower() in FORBIDDEN_KEYS:
                found.append(path)
            found.extend(forbidden_paths(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(forbidden_paths(child, f"{prefix}[{index}]"))
    return found


def require_fields(value: dict[str, Any], fields: tuple[str, ...], label: str) -> None:
    missing = [field for field in fields if value.get(field) in (None, "", [])]
    if missing:
        raise SystemExit(f"{label} missing fields: {', '.join(missing)}")


def validate_decision(decision: dict[str, Any], state: dict[str, Any]) -> None:
    expected = iso(int(state["cursor"]))
    if decision.get("as_of") != expected:
        raise SystemExit(f"Decision as_of must equal current cursor: {expected}")
    decision_state = decision.get("decision_state")
    if decision_state not in ALLOWED_STATES:
        raise SystemExit(f"Invalid decision_state: {decision_state}")
    observation = decision.get("next_observation")
    if observation is None:
        step = decision.get("next_step_minutes")
        if step not in ALLOWED_STEPS:
            raise SystemExit(f"next_step_minutes must be one of {sorted(ALLOWED_STEPS)}")
    else:
        if not isinstance(observation, dict):
            raise SystemExit("next_observation must be an object")
        mode = observation.get("mode")
        if mode not in ALLOWED_OBSERVATION_MODES:
            raise SystemExit(f"Invalid next_observation mode: {mode}")
        if mode == "FIXED_STEP":
            step = observation.get("minutes")
            if step not in ALLOWED_STEPS:
                raise SystemExit(f"FIXED_STEP minutes must be one of {sorted(ALLOWED_STEPS)}")
        elif mode == "NEXT_CLOSED_BAR_OR_TIMEOUT":
            require_fields(observation, ("timeout_minutes",), "next_observation")
            timeout = int(observation["timeout_minutes"])
            if timeout < 1 or timeout > 43200:
                raise SystemExit("NEXT_CLOSED_BAR_OR_TIMEOUT timeout_minutes must be between 1 and 43200")
        elif mode == "NEXT_STRUCTURE_EVENT_OR_TIMEOUT":
            require_fields(observation, ("timeframes", "timeout_minutes"), "next_observation")
            timeframes = observation["timeframes"]
            timeout = int(observation["timeout_minutes"])
            if not isinstance(timeframes, list) or not timeframes:
                raise SystemExit("NEXT_STRUCTURE_EVENT_OR_TIMEOUT requires a non-empty timeframes list")
            invalid = [timeframe for timeframe in timeframes if timeframe not in STRUCTURE_TIMEFRAMES]
            if invalid:
                raise SystemExit(f"Unknown structural timeframes: {', '.join(invalid)}")
            if timeout < 1 or timeout > 43200:
                raise SystemExit("NEXT_STRUCTURE_EVENT_OR_TIMEOUT timeout_minutes must be between 1 and 43200")
        elif mode == "PRICE_TOUCH_OR_TIMEOUT":
            require_fields(observation, ("zone_low", "zone_high", "timeout_minutes"), "next_observation")
            zone_low = float(observation["zone_low"])
            zone_high = float(observation["zone_high"])
            timeout = int(observation["timeout_minutes"])
            if zone_low > zone_high:
                raise SystemExit("next_observation zone_low must be <= zone_high")
            if timeout < 1 or timeout > 1440:
                raise SystemExit("next_observation timeout_minutes must be between 1 and 1440")
        else:
            require_fields(observation, ("events", "timeout_minutes"), "next_observation")
            events = observation["events"]
            timeout = int(observation["timeout_minutes"])
            if not isinstance(events, list) or not events:
                raise SystemExit("FIRST_PRICE_EVENT_OR_TIMEOUT requires a non-empty events list")
            for index, event in enumerate(events):
                if not isinstance(event, dict):
                    raise SystemExit(f"next_observation.events[{index}] must be an object")
                require_fields(event, ("label", "zone_low", "zone_high"), f"next_observation.events[{index}]")
                if float(event["zone_low"]) > float(event["zone_high"]):
                    raise SystemExit(f"next_observation.events[{index}] zone_low must be <= zone_high")
                condition = event.get("condition", "touch")
                if condition not in {"touch", "close_above", "close_below"}:
                    raise SystemExit(
                        f"next_observation.events[{index}] condition must be touch, close_above, or close_below"
                    )
            if timeout < 1 or timeout > 43200:
                raise SystemExit("FIRST_PRICE_EVENT_OR_TIMEOUT timeout_minutes must be between 1 and 43200")
    forbidden = forbidden_paths(decision)
    if forbidden:
        raise SystemExit(f"Future/algorithm fields are forbidden before sealing: {', '.join(forbidden)}")
    map_data = decision.get("map")
    if not isinstance(map_data, dict):
        raise SystemExit("map object is required")
    require_fields(map_data, ("external_structure", "internal_structure", "delivery_direction", "map_timeframes"), "map")

    scenario = decision.get("scenario")
    if decision_state == "ORDER_PLANNED":
        if not isinstance(scenario, dict):
            raise SystemExit("ORDER_PLANNED requires scenario")
        require_fields(
            scenario,
            (
                "scenario_id",
                "scope",
                "direction",
                "map_timeframe",
                "source_timeframe",
                "trigger_timeframe",
                "source_liquidity",
                "context_zone",
                "sweep",
                "choch",
                "entry_zone",
                "entry",
                "stop_loss",
                "take_profit",
                "objective",
                "invalidation",
                "seven_sentence_explanation",
            ),
            "scenario",
        )
        explanation = scenario["seven_sentence_explanation"]
        if not isinstance(explanation, list) or len(explanation) != 7 or any(not str(item).strip() for item in explanation):
            raise SystemExit("seven_sentence_explanation must contain exactly seven non-empty sentences")
    elif scenario is None and not str(decision.get("no_trade_reason", "")).strip():
        raise SystemExit("A decision without scenario requires no_trade_reason")


def resolve_next_cursor(decision: dict[str, Any], state: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    cursor = int(state["cursor"])
    observation = decision.get("next_observation")
    if observation is None:
        minutes = int(decision["next_step_minutes"])
        next_cursor = min(cursor + minutes * 60, Q1_TO)
        return next_cursor, {"mode": "FIXED_STEP", "minutes": minutes, "reason": "STEP_ELAPSED"}

    mode = observation["mode"]
    if mode == "FIXED_STEP":
        minutes = int(observation["minutes"])
        next_cursor = min(cursor + minutes * 60, Q1_TO)
        return next_cursor, {"mode": mode, "minutes": minutes, "reason": "STEP_ELAPSED"}

    timeout = int(observation["timeout_minutes"])
    timeout_cursor = min(cursor + timeout * 60, Q1_TO)
    unseen_rates = load_rates(cursor, timeout_cursor)
    if mode == "NEXT_CLOSED_BAR_OR_TIMEOUT":
        if len(unseen_rates):
            next_bar_close = min(int(unseen_rates[0]["time"]) + 60, Q1_TO)
            return next_bar_close, {
                "mode": mode,
                "timeout_minutes": timeout,
                "reason": "NEXT_CLOSED_BAR",
            }
        return timeout_cursor, {
            "mode": mode,
            "timeout_minutes": timeout,
            "reason": "TIMEOUT",
        }
    if mode == "NEXT_STRUCTURE_EVENT_OR_TIMEOUT":
        timeframes = [str(timeframe) for timeframe in observation["timeframes"]]
        next_event = next_structure_event_cursor(cursor, timeout_cursor, timeframes)
        if next_event is not None:
            return next_event, {
                "mode": mode,
                "timeframes": timeframes,
                "timeout_minutes": timeout,
                "reason": "NEXT_STRUCTURE_EVENT",
            }
        return timeout_cursor, {
            "mode": mode,
            "timeframes": timeframes,
            "timeout_minutes": timeout,
            "reason": "TIMEOUT",
        }
    if mode == "FIRST_PRICE_EVENT_OR_TIMEOUT":
        events = observation["events"]
        for bar in unseen_rates:
            labels = []
            for event in events:
                condition = event.get("condition", "touch")
                if condition == "touch":
                    matched = (
                        float(bar["high"]) >= float(event["zone_low"])
                        and float(bar["low"]) <= float(event["zone_high"])
                    )
                elif condition == "close_above":
                    matched = float(bar["close"]) > float(event["zone_high"])
                else:
                    matched = float(bar["close"]) < float(event["zone_low"])
                if matched:
                    labels.append(str(event["label"]))
            if labels:
                event_bar_close = min(int(bar["time"]) + 60, Q1_TO)
                return event_bar_close, {
                    "mode": mode,
                    "events": events,
                    "timeout_minutes": timeout,
                    "reason": "DECLARED_PRICE_EVENT",
                    "triggered_labels": labels,
                }
        return timeout_cursor, {
            "mode": mode,
            "events": events,
            "timeout_minutes": timeout,
            "reason": "TIMEOUT",
        }

    zone_low = float(observation["zone_low"])
    zone_high = float(observation["zone_high"])
    touched = unseen_rates[(unseen_rates["high"] >= zone_low) & (unseen_rates["low"] <= zone_high)]
    if len(touched):
        touch_bar_close = min(int(touched[0]["time"]) + 60, Q1_TO)
        return touch_bar_close, {
            "mode": mode,
            "zone_low": zone_low,
            "zone_high": zone_high,
            "timeout_minutes": timeout,
            "reason": "DECLARED_ZONE_TOUCHED",
        }
    return timeout_cursor, {
        "mode": mode,
        "zone_low": zone_low,
        "zone_high": zone_high,
        "timeout_minutes": timeout,
        "reason": "TIMEOUT",
    }


def command_record(input_path: Path) -> None:
    state = load_state()
    if state["status"] != "ACTIVE":
        raise SystemExit("Replay is already sealed.")
    decision = json.loads(input_path.read_text(encoding="utf-8"))
    validate_decision(decision, state)
    cursor, advance_resolution = resolve_next_cursor(decision, state)
    record_payload = {
        **decision,
        "record_no": int(state["records"]) + 1,
        "previous_record_hash": state.get("last_record_hash"),
        "next_cursor_utc": iso(cursor),
        "advance_resolution": advance_resolution,
    }
    canonical = json.dumps(record_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    record_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    record = {**record_payload, "record_hash": record_hash}
    with LEDGER_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    state.update(
        cursor=cursor,
        cursor_utc=iso(cursor),
        records=int(state["records"]) + 1,
        orders_planned=int(state["orders_planned"]) + (1 if decision["decision_state"] == "ORDER_PLANNED" else 0),
        last_record_hash=record_hash,
    )
    save_state(state)
    write_progress(state)
    print(json.dumps(state, ensure_ascii=False, indent=2))


def command_status() -> None:
    print(json.dumps(load_state(), ensure_ascii=False, indent=2))


def command_seal() -> None:
    state = load_state()
    if int(state["cursor"]) < Q1_TO:
        raise SystemExit(f"Cannot seal before Q1 end. Current cursor: {state['cursor_utc']}")
    ledger_bytes = LEDGER_FILE.read_bytes() if LEDGER_FILE.exists() else b""
    seal = {
        "schema": "mentor-ground-truth-seal-v1",
        "sealed_at": datetime.now(tz=UTC).isoformat(),
        "records": state["records"],
        "orders_planned": state["orders_planned"],
        "ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
        "comparison_authorized": True,
        "economic_replay_authorized": True,
    }
    SEAL_FILE.write_text(json.dumps(seal, ensure_ascii=False, indent=2), encoding="utf-8")
    state["status"] = "SEALED"
    save_state(state)
    print(json.dumps(seal, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--force", action="store_true")
    subparsers.add_parser("show")
    record_parser = subparsers.add_parser("record")
    record_parser.add_argument("--input", type=Path, default=CURRENT_DRAFT)
    subparsers.add_parser("status")
    subparsers.add_parser("seal")
    args = parser.parse_args()

    if args.command == "init":
        command_init(args.force)
    elif args.command == "show":
        render_current(load_state())
    elif args.command == "record":
        command_record(args.input)
    elif args.command == "status":
        command_status()
    elif args.command == "seal":
        command_seal()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
