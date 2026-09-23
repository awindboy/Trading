from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA_PATH = Path(__file__).with_name("v12_crt_event_contract.schema.json")
HEX = set("0123456789abcdef")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def parse_timestamp(value: Any, field: str) -> datetime:
    require(isinstance(value, str), f"{field} must be a string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} is not ISO-8601: {value}") from exc
    require(parsed.tzinfo is None, f"{field} must be an offset-free MT5 broker-clock label")
    return parsed


def validate_hash(value: Any, field: str) -> None:
    require(isinstance(value, str), f"{field} must be a string")
    require(len(value) == 64 and set(value) <= HEX, f"{field} must be lowercase sha256")


def validate_bar(bar: dict[str, Any], field: str) -> None:
    required = {"open_time", "close_time", "open", "high", "low", "close", "complete"}
    require(required <= bar.keys(), f"{field} is missing {sorted(required - bar.keys())}")
    open_time = parse_timestamp(bar["open_time"], f"{field}.open_time")
    close_time = parse_timestamp(bar["close_time"], f"{field}.close_time")
    require(open_time < close_time, f"{field} has a non-positive duration")
    values = [bar[name] for name in ("open", "high", "low", "close")]
    require(all(isinstance(value, (int, float)) for value in values), f"{field} OHLC must be numeric")
    open_price, high, low, close = map(float, values)
    require(high >= max(open_price, close, low), f"{field} high invariant failed")
    require(low <= min(open_price, close, high), f"{field} low invariant failed")
    require(bar["complete"] is True, f"{field} must be completed")


def validate_common(record: dict[str, Any]) -> None:
    require(record.get("schema_version") == "12.0.0-phase0", "unexpected schema_version")
    require(record.get("generation") == "V12", "generation must be V12")
    require(record.get("lane") in {"W1_TO_H4", "D1_TO_H1", "H4_TO_M15_M5_SHADOW"}, "invalid lane")
    validate_hash(record.get("source_dataset_sha256"), "source_dataset_sha256")
    validate_hash(record.get("broker_clock_spec_sha256"), "broker_clock_spec_sha256")
    require(isinstance(record.get("parent_id"), str) and len(record["parent_id"]) >= 12, "invalid parent_id")


def validate_decision(record: dict[str, Any]) -> None:
    validate_common(record)
    require(record.get("record_type") == "decision", "decision record_type mismatch")
    decision_time = parse_timestamp(record.get("decision_time"), "decision_time")
    validate_bar(record["c1"], "c1")
    validate_bar(record["c2"]["bar"], "c2.bar")
    c1 = record["c1"]
    midpoint = (float(c1["high"]) + float(c1["low"])) / 2.0
    require(abs(float(record["c1_midpoint"]) - midpoint) <= 1e-12, "c1 midpoint mismatch")
    require(parse_timestamp(record["c2"]["bar"]["close_time"], "c2.bar.close_time") <= decision_time, "decision precedes C2 close")
    interaction = record["c2"]["interaction"]
    expected_direction = {
        "HIGH_SWEEP_RETURN": "SHORT",
        "LOW_SWEEP_RETURN": "LONG",
        "HIGH_OUTSIDE_ACCEPTANCE": "LONG",
        "LOW_OUTSIDE_ACCEPTANCE": "SHORT",
        "NO_EXTREME_TRADE": "NONE",
        "DUAL_SWEEP_INSIDE": "NONE",
        "DUAL_OR_CONFLICTED": "NONE",
    }[interaction]
    require(record.get("hypothesis_direction") == expected_direction, "C2 branch direction mismatch")
    compliance = record.get("compliance", {})
    require(compliance.get("causal_prefix") is True, "example is not causal")
    require(compliance.get("completed_c2") is True, "example uses incomplete C2")
    require(compliance.get("future_fields_absent") is True, "future-field separation failed")
    forbidden = {"terminal_state", "realized_r", "mfe_r", "mae_r", "first_competing_event"}
    require(not (forbidden & record.keys()), "decision record contains outcome fields")


def validate_outcome(record: dict[str, Any]) -> None:
    validate_common(record)
    require(record.get("record_type") == "outcome", "outcome record_type mismatch")
    require(isinstance(record.get("child_id"), str) and len(record["child_id"]) >= 12, "invalid outcome child_id")
    parse_timestamp(record.get("outcome_asof"), "outcome_asof")
    forbidden = {"c1", "c2", "features", "trigger", "decision_time"}
    require(not (forbidden & record.keys()), "outcome record contains decision payload")


def main() -> int:
    raw = SCHEMA_PATH.read_bytes()
    schema = json.loads(raw)
    require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "wrong JSON Schema draft")
    require(set(schema.get("$defs", {})) >= {"decisionRecord", "outcomeRecord", "bar", "features"}, "missing schema definitions")
    examples = schema.get("examples", [])
    require(len(examples) == 2, "expected one decision and one outcome example")
    for record in examples:
        if record.get("record_type") == "decision":
            validate_decision(record)
        elif record.get("record_type") == "outcome":
            validate_outcome(record)
        else:
            raise ValueError("unknown example record_type")
    digest = hashlib.sha256(raw).hexdigest()
    print("V12_EVENT_SCHEMA_OK")
    print(f"SCHEMA_SHA256={digest}")
    print(f"EXAMPLES={len(examples)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
