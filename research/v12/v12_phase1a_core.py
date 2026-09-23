"""Core mechanics for the frozen V12 Phase-1A no-ML baseline."""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import asdict, dataclass, field
from datetime import datetime
import hashlib
import json
from statistics import mean, median
from typing import Iterable, Optional

from v12_phase0_core import M1Row, iso_broker_label, price_points


CONTRACT_VERSION = "v12-phase1a-model1-v2"
POINT_SIZE = 0.01

LANE_EXECUTION_TF = {
    "W1_TO_H4": "H4",
    "D1_TO_H1": "H1",
}

AUTHORIZED_INTERACTIONS = {
    "HIGH_SWEEP_RETURN": "SHORT",
    "LOW_SWEEP_RETURN": "LONG",
}


@dataclass(frozen=True)
class ExecutionBar:
    timeframe: str
    open_time: datetime
    close_time: datetime
    open: float
    high: float
    low: float
    close: float
    atr14: Optional[float]

    @property
    def body(self) -> float:
        return abs(self.close - self.open)

    @property
    def range(self) -> float:
        return self.high - self.low

    @property
    def body_ratio(self) -> Optional[float]:
        return self.body / self.range if self.range > 0 else None

    @property
    def body_atr(self) -> Optional[float]:
        return self.body / self.atr14 if self.atr14 and self.atr14 > 0 else None


@dataclass(frozen=True)
class TriggerSelection:
    trigger: ExecutionBar
    confirmation: ExecutionBar
    eligible_count: int
    sweep_depth: float
    confirmation_phase: str


def next_completed_parent_bar(
    parent_bars: list[ExecutionBar], c2_open_time: datetime
) -> Optional[ExecutionBar]:
    """Return the next observed completed parent bar, allowing session gaps."""

    opens = [bar.open_time for bar in parent_bars]
    index = bisect_left(opens, c2_open_time)
    if index >= len(parent_bars) or parent_bars[index].open_time != c2_open_time:
        return None
    return parent_bars[index + 1] if index + 1 < len(parent_bars) else None


@dataclass(frozen=True)
class ChildSpec:
    child_id: str
    parent_id: str
    lane: str
    interaction: str
    direction: str
    family: str
    risk_variant: str
    watch_start: datetime
    parent_sweep_time: datetime
    target_guard_start: datetime
    stop_guard_start: datetime
    decision_time: datetime
    expiry_time: datetime
    stop_price: float
    target1_price: float
    target2_price: float
    c1_high: float
    c1_low: float
    c2_high: float
    c2_low: float
    trigger_open_time: Optional[datetime]
    trigger_close_time: Optional[datetime]
    trigger_open: Optional[float]
    trigger_high: Optional[float]
    trigger_low: Optional[float]
    trigger_close: Optional[float]
    trigger_body_atr: Optional[float]
    trigger_body_ratio: Optional[float]
    trigger_sweep_depth: Optional[float]
    trigger_eligible_count: int
    confirmation_time: Optional[datetime]
    confirmation_phase: str

    def decision_record(self) -> dict:
        value = asdict(self)
        for key in (
            "watch_start",
            "parent_sweep_time",
            "target_guard_start",
            "stop_guard_start",
            "decision_time",
            "expiry_time",
            "trigger_open_time",
            "trigger_close_time",
            "confirmation_time",
        ):
            value[key] = iso_broker_label(value[key]) if value[key] else None
        value["contract_version"] = CONTRACT_VERSION
        value["entry_rule"] = "FIRST_M1_OPEN_AT_OR_AFTER_DECISION"
        value["outcome_fields_present"] = False
        return value


def stable_child_id(parent_id: str, family: str, risk_variant: str) -> str:
    payload = json.dumps(
        {
            "contract_version": CONTRACT_VERSION,
            "parent_id": parent_id,
            "family": family,
            "risk_variant": risk_variant,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "v12c1a-" + hashlib.sha256(payload).hexdigest()[:24]


def select_model1_trigger(
    *,
    direction: str,
    c1_high: float,
    c1_low: float,
    c2_open_time: datetime,
    c2_close_time: datetime,
    c3_close_time: datetime,
    execution_bars: list[ExecutionBar],
) -> tuple[Optional[TriggerSelection], str, int]:
    inside_c2 = [
        bar
        for bar in execution_bars
        if bar.open_time >= c2_open_time and bar.close_time <= c2_close_time
    ]
    if direction == "SHORT":
        body_candidates = [
            bar
            for bar in inside_c2
            if price_points(bar.high) > price_points(c1_high) and bar.close > bar.open
        ]
    elif direction == "LONG":
        body_candidates = [
            bar
            for bar in inside_c2
            if price_points(bar.low) < price_points(c1_low) and bar.close < bar.open
        ]
    else:
        return None, "NON_DIRECTIONAL_PARENT", 0

    if not body_candidates:
        return None, "NO_SWEEP_DIRECTION_BODY_CANDLE", 0
    eligible = [bar for bar in body_candidates if bar.body_atr is not None and bar.body_ratio is not None]
    if not eligible:
        return None, "TRIGGER_ATR_UNAVAILABLE", len(body_candidates)

    def rank(bar: ExecutionBar) -> tuple[float, float, float, datetime]:
        sweep_depth = (bar.high - c1_high) if direction == "SHORT" else (c1_low - bar.low)
        return (bar.body_atr or -1.0, bar.body_ratio or -1.0, sweep_depth, bar.open_time)

    trigger = max(eligible, key=rank)
    later = [
        bar
        for bar in execution_bars
        if bar.open_time > trigger.open_time and bar.close_time <= c3_close_time
    ]
    if direction == "SHORT":
        confirmation = next((bar for bar in later if price_points(bar.close) < price_points(trigger.low)), None)
        sweep_depth = trigger.high - c1_high
    else:
        confirmation = next((bar for bar in later if price_points(bar.close) > price_points(trigger.high)), None)
        sweep_depth = c1_low - trigger.low
    if confirmation is None:
        return None, "NO_CONFIRMATION_BEFORE_C3_CLOSE", len(eligible)
    phase = "PRECONFIRMED_INSIDE_C2" if confirmation.close_time <= c2_close_time else "CONFIRMED_INSIDE_C3"
    return (
        TriggerSelection(
            trigger=trigger,
            confirmation=confirmation,
            eligible_count=len(eligible),
            sweep_depth=sweep_depth,
            confirmation_phase=phase,
        ),
        "MODEL1_SELECTED",
        len(eligible),
    )


def make_child_spec(
    *,
    parent: dict,
    family: str,
    risk_variant: str,
    c3_close_time: datetime,
    trigger: Optional[TriggerSelection] = None,
) -> ChildSpec:
    direction = parent["hypothesis_direction"]
    c2_close = datetime.fromisoformat(parent["c2_close_time"])
    sweep_field = "first_low_breach_time" if direction == "LONG" else "first_high_breach_time"
    if not parent.get(sweep_field):
        raise ValueError(f"directional rejection is missing {sweep_field}")
    parent_sweep_time = datetime.fromisoformat(parent[sweep_field])
    if family == "C3_OPEN_CONTROL":
        decision_time = c2_close
        confirmation_phase = "NOT_REQUIRED_CONTROL"
    elif trigger is not None:
        decision_time = max(c2_close, trigger.confirmation.close_time)
        confirmation_phase = trigger.confirmation_phase
    else:
        raise ValueError("Model1 child requires a trigger selection")

    if risk_variant == "C2_EXTREME":
        stop = (
            float(parent["c2_low"]) - POINT_SIZE
            if direction == "LONG"
            else float(parent["c2_high"]) + POINT_SIZE
        )
        stop_guard_start = c2_close
    elif risk_variant == "TRIGGER_STRUCTURE" and trigger is not None:
        stop = trigger.trigger.low - POINT_SIZE if direction == "LONG" else trigger.trigger.high + POINT_SIZE
        stop_guard_start = trigger.trigger.close_time
    else:
        raise ValueError(f"unsupported risk variant: {risk_variant}")

    target1 = float(parent["c1_midpoint"])
    target2 = float(parent["c1_high"]) if direction == "LONG" else float(parent["c1_low"])
    trigger_bar = trigger.trigger if trigger else None
    confirmation = trigger.confirmation if trigger else None
    child_id = stable_child_id(parent["parent_id"], family, risk_variant)
    return ChildSpec(
        child_id=child_id,
        parent_id=parent["parent_id"],
        lane=parent["lane"],
        interaction=parent["interaction"],
        direction=direction,
        family=family,
        risk_variant=risk_variant,
        watch_start=min(parent_sweep_time, stop_guard_start),
        parent_sweep_time=parent_sweep_time,
        target_guard_start=parent_sweep_time,
        stop_guard_start=stop_guard_start,
        decision_time=decision_time,
        expiry_time=c3_close_time,
        stop_price=round(stop, 2),
        target1_price=round(target1, 2),
        target2_price=round(target2, 2),
        c1_high=float(parent["c1_high"]),
        c1_low=float(parent["c1_low"]),
        c2_high=float(parent["c2_high"]),
        c2_low=float(parent["c2_low"]),
        trigger_open_time=trigger_bar.open_time if trigger_bar else None,
        trigger_close_time=trigger_bar.close_time if trigger_bar else None,
        trigger_open=trigger_bar.open if trigger_bar else None,
        trigger_high=trigger_bar.high if trigger_bar else None,
        trigger_low=trigger_bar.low if trigger_bar else None,
        trigger_close=trigger_bar.close if trigger_bar else None,
        trigger_body_atr=trigger_bar.body_atr if trigger_bar else None,
        trigger_body_ratio=trigger_bar.body_ratio if trigger_bar else None,
        trigger_sweep_depth=trigger.sweep_depth if trigger else None,
        trigger_eligible_count=trigger.eligible_count if trigger else 0,
        confirmation_time=confirmation.close_time if confirmation else None,
        confirmation_phase=confirmation_phase,
    )


def _stop_touched(spec: ChildSpec, row: M1Row) -> bool:
    if spec.direction == "LONG":
        return price_points(row.low) <= price_points(spec.stop_price)
    return price_points(row.high) >= price_points(spec.stop_price)


def _target_touched(spec: ChildSpec, row: M1Row, target: float) -> bool:
    if spec.direction == "LONG":
        return price_points(row.high) >= price_points(target)
    return price_points(row.low) <= price_points(target)


def _open_at_or_beyond_stop(spec: ChildSpec, open_price: float) -> bool:
    if spec.direction == "LONG":
        return price_points(open_price) <= price_points(spec.stop_price)
    return price_points(open_price) >= price_points(spec.stop_price)


def _open_at_or_beyond_target(spec: ChildSpec, open_price: float, target: float) -> bool:
    if spec.direction == "LONG":
        return price_points(open_price) >= price_points(target)
    return price_points(open_price) <= price_points(target)


def _r_value(spec: ChildSpec, entry: float, exit_price: float) -> float:
    risk = (entry - spec.stop_price) if spec.direction == "LONG" else (spec.stop_price - entry)
    if risk <= 0:
        raise ValueError("non-positive risk distance")
    pnl = (exit_price - entry) if spec.direction == "LONG" else (entry - exit_price)
    return pnl / risk


@dataclass
class _SimulationState:
    spec: ChildSpec
    phase: str = "PENDING"
    no_execution_reason: Optional[str] = None
    entry_time: Optional[datetime] = None
    entry_price: Optional[float] = None
    risk_distance: Optional[float] = None
    t1_state: str = "PENDING"
    t1_terminal_time: Optional[datetime] = None
    t1_exit_price: Optional[float] = None
    t1_r: Optional[float] = None
    t2_state: str = "PENDING"
    t2_terminal_time: Optional[datetime] = None
    t2_exit_price: Optional[float] = None
    t2_r: Optional[float] = None
    last_m1_time: Optional[datetime] = None
    last_m1_close: Optional[float] = None
    mfe_r: float = 0.0
    mae_r: float = 0.0
    gap_stop: bool = False

    def no_fill(self, reason: str, timestamp: Optional[datetime] = None) -> None:
        self.phase = "DONE"
        self.no_execution_reason = reason
        self.t1_state = "NO_EXECUTION"
        self.t2_state = "NO_EXECUTION"
        self.t1_terminal_time = timestamp
        self.t2_terminal_time = timestamp

    def attempt_entry(self, row: M1Row) -> bool:
        if _open_at_or_beyond_stop(self.spec, row.open):
            self.no_fill("STOP_INVALIDATED_AT_ENTRY", row.timestamp)
            return False
        if _open_at_or_beyond_target(self.spec, row.open, self.spec.target1_price):
            self.no_fill("TARGET1_CONSUMED_AT_ENTRY", row.timestamp)
            return False
        risk = (
            row.open - self.spec.stop_price
            if self.spec.direction == "LONG"
            else self.spec.stop_price - row.open
        )
        if risk <= 0:
            self.no_fill("NON_POSITIVE_RISK_AT_ENTRY", row.timestamp)
            return False
        self.phase = "ACTIVE"
        self.entry_time = row.timestamp
        self.entry_price = row.open
        self.risk_distance = risk
        self.t1_state = "ACTIVE"
        self.t2_state = "ACTIVE"
        return True

    def observe_pending(self, row: M1Row) -> None:
        stop = row.timestamp >= self.spec.stop_guard_start and _stop_touched(self.spec, row)
        target = row.timestamp >= self.spec.target_guard_start and _target_touched(
            self.spec, row, self.spec.target1_price
        )
        if stop and target:
            self.no_fill("PREENTRY_STOP_AND_TARGET_SAME_M1", row.timestamp)
        elif stop:
            self.no_fill("PREENTRY_STOP_INVALIDATION", row.timestamp)
        elif target:
            reason = (
                "PARENT_SWEEP_AND_TARGET1_SAME_M1_AMBIGUOUS"
                if row.timestamp == self.spec.parent_sweep_time
                else "PREENTRY_TARGET1_CONSUMED"
            )
            self.no_fill(reason, row.timestamp)

    def _terminal(self, target_number: int, state: str, timestamp: datetime, exit_price: Optional[float]) -> None:
        prefix = f"t{target_number}"
        setattr(self, f"{prefix}_state", state)
        setattr(self, f"{prefix}_terminal_time", timestamp)
        setattr(self, f"{prefix}_exit_price", exit_price)
        if exit_price is not None and self.entry_price is not None:
            setattr(self, f"{prefix}_r", _r_value(self.spec, self.entry_price, exit_price))

    def _process_gap(self, row: M1Row, target_number: int, target: float) -> bool:
        state = getattr(self, f"t{target_number}_state")
        if state != "ACTIVE":
            return False
        if _open_at_or_beyond_stop(self.spec, row.open):
            self.gap_stop = True
            self._terminal(target_number, "STOPPED_GAP", row.timestamp, row.open)
            return True
        if _open_at_or_beyond_target(self.spec, row.open, target):
            self._terminal(target_number, f"TARGET{target_number}", row.timestamp, target)
            return True
        return False

    def observe_active(self, row: M1Row, *, entry_row: bool = False) -> None:
        if self.entry_price is None or self.risk_distance is None:
            raise RuntimeError("active state without entry")
        self.last_m1_time = row.timestamp
        self.last_m1_close = row.close

        if not entry_row:
            self._process_gap(row, 1, self.spec.target1_price)
            self._process_gap(row, 2, self.spec.target2_price)

        if self.spec.direction == "LONG":
            favorable = (row.high - self.entry_price) / self.risk_distance
            adverse = (self.entry_price - row.low) / self.risk_distance
        else:
            favorable = (self.entry_price - row.low) / self.risk_distance
            adverse = (row.high - self.entry_price) / self.risk_distance
        self.mfe_r = max(self.mfe_r, favorable)
        self.mae_r = max(self.mae_r, adverse)

        stop = _stop_touched(self.spec, row)
        for number, target in ((1, self.spec.target1_price), (2, self.spec.target2_price)):
            if getattr(self, f"t{number}_state") != "ACTIVE":
                continue
            target_touch = _target_touched(self.spec, row, target)
            if stop and target_touch:
                self._terminal(number, "AMBIGUOUS", row.timestamp, None)
            elif stop:
                self._terminal(number, "STOPPED", row.timestamp, self.spec.stop_price)
            elif target_touch:
                self._terminal(number, f"TARGET{number}", row.timestamp, target)

        if self.t1_state != "ACTIVE" and self.t2_state != "ACTIVE":
            self.phase = "DONE"

    def expire(self) -> None:
        if self.phase == "PENDING":
            self.no_fill("NO_EXECUTABLE_M1_BEFORE_C3_EXPIRY", self.spec.expiry_time)
            return
        if self.phase != "ACTIVE":
            return
        if self.last_m1_close is None or self.entry_price is None:
            self.no_fill("NO_M1_AFTER_ENTRY", self.spec.expiry_time)
            return
        for number in (1, 2):
            if getattr(self, f"t{number}_state") == "ACTIVE":
                self._terminal(number, "EXPIRED", self.spec.expiry_time, self.last_m1_close)
        self.phase = "DONE"

    def outcome_record(self) -> dict:
        return {
            "contract_version": CONTRACT_VERSION,
            "child_id": self.spec.child_id,
            "parent_id": self.spec.parent_id,
            "lane": self.spec.lane,
            "interaction": self.spec.interaction,
            "direction": self.spec.direction,
            "family": self.spec.family,
            "risk_variant": self.spec.risk_variant,
            "watch_start": iso_broker_label(self.spec.watch_start),
            "parent_sweep_time": iso_broker_label(self.spec.parent_sweep_time),
            "target_guard_start": iso_broker_label(self.spec.target_guard_start),
            "stop_guard_start": iso_broker_label(self.spec.stop_guard_start),
            "decision_time": iso_broker_label(self.spec.decision_time),
            "expiry_time": iso_broker_label(self.spec.expiry_time),
            "execution_state": "FILLED" if self.entry_time is not None else "NO_EXECUTION",
            "no_execution_reason": self.no_execution_reason,
            "entry_time": iso_broker_label(self.entry_time) if self.entry_time else None,
            "entry_price": self.entry_price,
            "stop_price": self.spec.stop_price,
            "risk_distance": self.risk_distance,
            "target1_price": self.spec.target1_price,
            "target2_price": self.spec.target2_price,
            "t1_state": self.t1_state,
            "t1_terminal_time": iso_broker_label(self.t1_terminal_time) if self.t1_terminal_time else None,
            "t1_exit_price": self.t1_exit_price,
            "t1_r": self.t1_r,
            "t2_state": self.t2_state,
            "t2_terminal_time": iso_broker_label(self.t2_terminal_time) if self.t2_terminal_time else None,
            "t2_exit_price": self.t2_exit_price,
            "t2_r": self.t2_r,
            "mfe_r": self.mfe_r if self.entry_time else None,
            "mae_r": self.mae_r if self.entry_time else None,
            "gap_stop": self.gap_stop,
            "ordering_precision": "AMBIGUOUS"
            if self.t1_state == "AMBIGUOUS" or self.t2_state == "AMBIGUOUS"
            else "M1",
            "outcome_fields_present": True,
        }


def simulate_children(rows: Iterable[M1Row], specs: list[ChildSpec]) -> list[dict]:
    ordered = sorted(specs, key=lambda spec: (spec.watch_start, spec.child_id))
    next_index = 0
    live: list[_SimulationState] = []
    finished: list[_SimulationState] = []

    for row in rows:
        still_live: list[_SimulationState] = []
        for state in live:
            if row.timestamp >= state.spec.expiry_time:
                state.expire()
                finished.append(state)
            else:
                still_live.append(state)
        live = still_live

        while next_index < len(ordered) and ordered[next_index].watch_start <= row.timestamp:
            spec = ordered[next_index]
            next_index += 1
            if row.timestamp >= spec.expiry_time:
                state = _SimulationState(spec)
                state.no_fill("FIRST_M1_AFTER_C3_EXPIRY", row.timestamp)
                finished.append(state)
            else:
                live.append(_SimulationState(spec))

        still_live = []
        for state in live:
            if state.phase == "PENDING":
                if row.timestamp >= state.spec.decision_time:
                    entered = state.attempt_entry(row)
                    if entered:
                        state.observe_active(row, entry_row=True)
                else:
                    state.observe_pending(row)
            elif state.phase == "ACTIVE":
                state.observe_active(row)

            if state.phase == "DONE":
                finished.append(state)
            else:
                still_live.append(state)
        live = still_live

    for state in live:
        state.expire()
        finished.append(state)
    while next_index < len(ordered):
        state = _SimulationState(ordered[next_index])
        next_index += 1
        state.no_fill("WATCH_WINDOW_NOT_REACHED")
        finished.append(state)

    outcomes = [state.outcome_record() for state in finished]
    outcomes.sort(key=lambda row: row["child_id"])
    return outcomes


def _max_drawdown(rows: list[tuple[str, float]]) -> float:
    by_time: dict[str, float] = {}
    for timestamp, value in rows:
        by_time[timestamp] = by_time.get(timestamp, 0.0) + value
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for timestamp in sorted(by_time):
        equity += by_time[timestamp]
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return drawdown


def _max_stop_streak(rows: list[dict], state_field: str) -> int:
    streak = 0
    maximum = 0
    for row in sorted(rows, key=lambda item: (item.get("entry_time") or "", item["child_id"])):
        state = row[state_field]
        if state in {"STOPPED", "STOPPED_GAP"}:
            streak += 1
            maximum = max(maximum, streak)
        elif state != "AMBIGUOUS":
            streak = 0
    return maximum


def score_outcomes(outcomes: list[dict], target_number: int = 1) -> dict:
    r_field = f"t{target_number}_r"
    state_field = f"t{target_number}_state"
    time_field = f"t{target_number}_terminal_time"
    filled = [row for row in outcomes if row["execution_state"] == "FILLED"]
    ambiguous = [row for row in filled if row[state_field] == "AMBIGUOUS"]
    resolved = [row for row in filled if row[r_field] is not None]
    values = [float(row[r_field]) for row in resolved]
    stops = [row for row in filled if row[state_field] in {"STOPPED", "STOPPED_GAP"}]
    targets = [row for row in filled if row[state_field] == f"TARGET{target_number}"]
    expiries = [row for row in filled if row[state_field] == "EXPIRED"]
    gross_profit = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    net = sum(values)
    return {
        "decisions": len(outcomes),
        "filled_children": len(filled),
        "no_execution": len(outcomes) - len(filled),
        "resolved_children": len(resolved),
        "ambiguous_children": len(ambiguous),
        "stops": len(stops),
        "targets": len(targets),
        "expiries": len(expiries),
        "stop_rate_filled": len(stops) / len(filled) if filled else None,
        "target_rate_filled": len(targets) / len(filled) if filled else None,
        "win_rate_resolved": sum(value > 0 for value in values) / len(values) if values else None,
        "net_r": net,
        "gross_profit_r": gross_profit,
        "gross_loss_r": gross_loss,
        "pf_r": gross_profit / gross_loss if gross_loss > 0 else None,
        "mean_r": mean(values) if values else None,
        "median_r": median(values) if values else None,
        "net_r_per_100_filled": (net / len(filled) * 100.0) if filled else None,
        "stopped_loss_r": -sum(float(row[r_field]) for row in stops if row[r_field] is not None),
        "max_drawdown_r": _max_drawdown(
            [(row[time_field], float(row[r_field])) for row in resolved if row[time_field]]
        ),
        "max_stop_streak": _max_stop_streak(filled, state_field),
        "ge_2r": sum(value >= 2.0 for value in values),
        "ge_5r": sum(value >= 5.0 for value in values),
        "le_minus_1r": sum(value <= -1.0 for value in values),
    }
