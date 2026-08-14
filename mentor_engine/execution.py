from __future__ import annotations

import numpy as np

from .models import BarSeries, Direction, OrderPlan, TradeResult, Zone


def _result(
    plan: OrderPlan,
    result: str,
    entry_time: int | None = None,
    exit_time: int | None = None,
    exit_price: float | None = None,
) -> TradeResult:
    risk = abs(plan.entry - plan.stop_loss)
    if result == "TP" and risk > 0:
        pnl_r = abs(plan.take_profit - plan.entry) / risk
    elif result == "SL":
        pnl_r = -1.0
    else:
        pnl_r = 0.0
    holding = (
        int((exit_time - entry_time) // 60)
        if entry_time is not None and exit_time is not None
        else None
    )
    return TradeResult(
        trade_id=f"trade:{plan.order_id}",
        order_id=plan.order_id,
        scenario_id=plan.scenario_id,
        direction=plan.direction,
        order_time=plan.created_at,
        entry_time=entry_time,
        exit_time=exit_time,
        entry=plan.entry,
        stop_loss=plan.stop_loss,
        take_profit=plan.take_profit,
        exit_price=exit_price,
        result=result,
        pnl_r=pnl_r,
        holding_minutes=holding,
    )


def simulate_order(
    m1: BarSeries,
    plan: OrderPlan,
    entry_zone: Zone,
    point: float,
    trade_to: int | None,
) -> TradeResult:
    # created_at is the close/availability time of the bar that formed the
    # entry zone. An order cannot be filled by that already-completed bar.
    start = int(np.searchsorted(m1.available_time, plan.created_at, side="right"))
    entry_time: int | None = None
    for index in range(max(0, start), len(m1)):
        timestamp = int(m1.available_time[index])
        if trade_to is not None and timestamp >= trade_to:
            break
        spread = float(m1.spread_points[index]) * point
        bid_low = float(m1.low[index])
        bid_high = float(m1.high[index])
        bid_close = float(m1.close[index])
        ask_low = bid_low + spread
        ask_high = bid_high + spread

        if entry_time is None:
            fill = (
                ask_low <= plan.entry
                if plan.direction == Direction.LONG
                else bid_high >= plan.entry
            )
            if fill:
                entry_time = timestamp
            else:
                objective_delivered = (
                    bid_high >= plan.take_profit
                    if plan.direction == Direction.LONG
                    else ask_low <= plan.take_profit
                )
                if objective_delivered:
                    return _result(
                        plan,
                        "CANCELLED_OBJECTIVE_DELIVERED",
                        exit_time=timestamp,
                    )
                if (
                    entry_zone.consumed_at is not None
                    and entry_zone.consumed_at <= timestamp
                ):
                    return _result(
                        plan,
                        "CANCELLED_ZONE_CONSUMED",
                        exit_time=timestamp,
                    )
                if plan.cancel_structure_level is not None:
                    invalid = (
                        bid_close < plan.cancel_structure_level
                        if plan.direction == Direction.LONG
                        else bid_close > plan.cancel_structure_level
                    )
                    if invalid:
                        return _result(
                            plan,
                            "CANCELLED_STRUCTURE_INVALIDATED",
                            exit_time=timestamp,
                        )
                continue

        stop_hit = (
            bid_low <= plan.stop_loss
            if plan.direction == Direction.LONG
            else ask_high >= plan.stop_loss
        )
        target_hit = (
            bid_high >= plan.take_profit
            if plan.direction == Direction.LONG
            else ask_low <= plan.take_profit
        )
        if stop_hit:
            return _result(
                plan,
                "SL",
                entry_time=entry_time,
                exit_time=timestamp,
                exit_price=plan.stop_loss,
            )
        if target_hit:
            return _result(
                plan,
                "TP",
                entry_time=entry_time,
                exit_time=timestamp,
                exit_price=plan.take_profit,
            )
    if entry_time is not None:
        return _result(plan, "OPEN", entry_time=entry_time)
    terminal_time = (
        trade_to
        if trade_to is not None
        else int(m1.available_time[-1]) + int(m1.seconds)
    )
    return _result(plan, "UNFILLED", exit_time=terminal_time)
