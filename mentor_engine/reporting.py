from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import numpy as np

from .engine import MentorScenarioEngine
from .models import Direction, OrderPlan, Scenario, TradeResult, jsonable


def write_artifacts(
    engine: MentorScenarioEngine,
    output_dir: str | Path,
    casebook_validation: dict[str, Any],
    q1_regression: dict[str, Any] | None = None,
    charts: bool = True,
) -> dict[str, Path]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    summary = engine.summary()
    summary["casebook"] = casebook_validation
    summary["q1Regression"] = q1_regression
    economic_checks = summary["acceptance"]
    summary["decision"] = {
        "mentorProtocolApproved": bool(casebook_validation.get("protocolPassed")),
        "automaticEaApproved": bool(
            casebook_validation.get("protocolPassed")
            and (q1_regression is None or q1_regression.get("passed"))
            and economic_checks.get("winRate50")
            and economic_checks.get("profitFactor13")
            and economic_checks.get("netPositive")
            and economic_checks.get("maxDrawdownPercent20")
        ),
        "reason": (
            "EA port requires replayable Casebook parity and every economic gate."
        ),
    }
    summary_path = root / "summary.json"
    summary_path.write_text(
        json.dumps(jsonable(summary), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    ledger_path = root / "ledger.jsonl"
    with ledger_path.open("w", encoding="utf-8", newline="\n") as handle:
        for destination_plan in engine.plans:
            handle.write(
                json.dumps(
                    {"recordType": "destination_plan", **jsonable(destination_plan)},
                    ensure_ascii=False,
                )
                + "\n"
            )
        for rejection in engine.rejections:
            handle.write(
                json.dumps(
                    {"recordType": "engine_rejection", **jsonable(rejection)},
                    ensure_ascii=False,
                )
                + "\n"
            )
        for scenario in engine.scenarios:
            handle.write(
                json.dumps(
                    {"recordType": "scenario", **jsonable(scenario)},
                    ensure_ascii=False,
                )
                + "\n"
            )
        for order in engine.orders:
            handle.write(
                json.dumps(
                    {"recordType": "order", **jsonable(order)},
                    ensure_ascii=False,
                )
                + "\n"
            )
        for trade in engine.trades:
            handle.write(
                json.dumps(
                    {"recordType": "trade", **jsonable(trade)},
                    ensure_ascii=False,
                )
                + "\n"
            )

    scenarios = {item.scenario_id: item for item in engine.scenarios}
    orders = {item.order_id: item for item in engine.orders}
    trades_path = root / "trades.csv"
    with trades_path.open("w", encoding="utf-8-sig", newline="") as handle:
        fieldnames = [
            "trade_id",
            "scenario_id",
            "plan_id",
            "direction",
            "scope",
            "map_timeframe",
            "context_timeframe",
            "trigger_timeframe",
            "source_pool_id",
            "source_zone_ids",
            "parent_zone_ids",
            "refinement_path",
            "map_structure_event_id",
            "planned_at_utc",
            "sweep_event_id",
            "trigger_event_id",
            "entry_zone_id",
            "entry_family_zone_ids",
            "protective_zone_bottom",
            "protective_zone_top",
            "objective_kind",
            "objective_id",
            "order_time_utc",
            "entry_time_utc",
            "exit_time_utc",
            "entry",
            "stop_loss",
            "take_profit",
            "result",
            "pnl_r",
            "holding_minutes",
            "scenario_explanation",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for trade in engine.trades:
            scenario = scenarios[trade.scenario_id]
            plan = orders[trade.order_id]
            writer.writerow(
                {
                    "trade_id": trade.trade_id,
                    "scenario_id": trade.scenario_id,
                    "plan_id": scenario.plan_id,
                    "direction": trade.direction.value,
                    "scope": scenario.scope.value,
                    "map_timeframe": plan.map_timeframe,
                    "context_timeframe": plan.context_timeframe,
                    "trigger_timeframe": plan.trigger_timeframe,
                    "source_pool_id": scenario.source_pool_id,
                    "source_zone_ids": ";".join(scenario.source_zone_ids),
                    "parent_zone_ids": ";".join(scenario.parent_zone_ids),
                    "refinement_path": ";".join(scenario.refinement_path),
                    "map_structure_event_id": scenario.map_structure_event_id,
                    "planned_at_utc": _utc(scenario.planned_at),
                    "sweep_event_id": scenario.sweep_event_id,
                    "trigger_event_id": scenario.trigger_event_id,
                    "entry_zone_id": scenario.entry_zone_id,
                    "entry_family_zone_ids": ";".join(plan.entry_family_zone_ids),
                    "protective_zone_bottom": plan.protective_zone_bottom,
                    "protective_zone_top": plan.protective_zone_top,
                    "objective_kind": scenario.objective_kind,
                    "objective_id": scenario.objective_id,
                    "order_time_utc": _utc(trade.order_time),
                    "entry_time_utc": _utc(trade.entry_time),
                    "exit_time_utc": _utc(trade.exit_time),
                    "entry": trade.entry,
                    "stop_loss": trade.stop_loss,
                    "take_profit": trade.take_profit,
                    "result": trade.result,
                    "pnl_r": trade.pnl_r,
                    "holding_minutes": trade.holding_minutes,
                    "scenario_explanation": " | ".join(trade.explanation),
                }
            )

    validation_path = root / "VALIDATION.md"
    validation_path.write_text(_validation_markdown(summary), encoding="utf-8")

    regression_path = root / "Q1_REGRESSION.json"
    if q1_regression is not None:
        regression_path.write_text(
            json.dumps(q1_regression, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    chart_dir = root / "charts"
    if charts:
        chart_dir.mkdir(exist_ok=True)
        _render_charts(engine, chart_dir)
    return {
        "summary": summary_path,
        "ledger": ledger_path,
        "trades": trades_path,
        "validation": validation_path,
        "q1Regression": regression_path,
        "charts": chart_dir,
    }


def _utc(timestamp: int | None) -> str:
    if timestamp is None:
        return ""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def _render_charts(engine: MentorScenarioEngine, chart_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
    except ImportError:
        return

    scenarios = {item.scenario_id: item for item in engine.scenarios}
    orders = {item.order_id: item for item in engine.orders}
    zones = {
        zone.object_id: zone
        for state in engine.states.values()
        for zone in state.zones
    }
    pools = {
        pool.object_id: pool
        for state in engine.states.values()
        for pool in state.liquidity
    }
    sweeps = {
        sweep.event_id: sweep
        for state in engine.states.values()
        for sweep in state.sweeps
    }
    for sequence, trade in enumerate(engine.trades, start=1):
        if trade.entry_time is None:
            continue
        scenario = scenarios[trade.scenario_id]
        plan = orders[trade.order_id]
        source_pool = pools[scenario.source_pool_id]
        source_sweep = sweeps[scenario.sweep_event_id]
        timeframes = []
        for timeframe in (
            scenario.map_timeframe,
            scenario.context_timeframe,
            plan.trigger_timeframe,
        ):
            if timeframe not in timeframes:
                timeframes.append(timeframe)
        fig, axes = plt.subplots(
            len(timeframes),
            1,
            figsize=(11, 3.6 * len(timeframes)),
            constrained_layout=True,
        )
        axes = np.atleast_1d(axes)
        for axis, timeframe in zip(axes, timeframes):
            series = engine.series[timeframe]
            focus_time = (
                plan.created_at
                if timeframe == plan.trigger_timeframe
                else source_sweep.available_at
            )
            center = int(np.searchsorted(series.available_time, focus_time, side="left"))
            left = max(0, center - 70)
            right = min(len(series), center + 70)
            _candles(axis, series, left, right, Rectangle)
            for zone_id in scenario.source_zone_ids:
                zone = zones[zone_id]
                axis.axhspan(zone.bottom, zone.top, color="#f59e0b", alpha=0.13)
            axis.axhspan(
                plan.entry_zone_bottom,
                plan.entry_zone_top,
                color="#38bdf8",
                alpha=0.16,
            )
            axis.axhspan(
                source_pool.bottom,
                source_pool.top,
                color="#c084fc",
                alpha=0.12,
            )
            axis.axhline(plan.take_profit, color="#34d399", linestyle="--", linewidth=0.9)
            axis.axhline(plan.stop_loss, color="#fb7185", linestyle="--", linewidth=0.9)
            axis.axhline(plan.entry, color="#e2e8f0", linestyle=":", linewidth=0.8)
            axis.set_title(
                f"{timeframe} | {scenario.scope.value} | {trade.result} {trade.pnl_r:.2f}R",
                loc="left",
                fontsize=10,
                color="#e2e8f0",
            )
            markers = [
                (source_sweep.available_at, "Sweep", "#fbbf24"),
                (plan.created_at, "CHoCH zone", "#38bdf8"),
                (trade.entry_time, "Fill", "#f8fafc"),
                (
                    trade.exit_time,
                    trade.result,
                    "#34d399" if trade.result == "TP" else "#fb7185",
                ),
            ]
            for timestamp, label, colour in markers:
                if timestamp is None:
                    continue
                marker = int(
                    np.searchsorted(series.available_time, timestamp, side="left")
                )
                if left <= marker < right:
                    x = marker - left
                    axis.axvline(x, color=colour, linewidth=0.8, alpha=0.75)
                    axis.text(
                        x,
                        0.98,
                        label,
                        color=colour,
                        fontsize=7,
                        ha="center",
                        va="top",
                        transform=axis.get_xaxis_transform(),
                    )
            axis.grid(color="#334155", alpha=0.25, linewidth=0.5)
        fig.patch.set_facecolor("#080c12")
        for axis in axes:
            axis.set_facecolor("#080c12")
            axis.tick_params(colors="#94a3b8", labelsize=7)
            for spine in axis.spines.values():
                spine.set_color("#263241")
        entry_day = _utc(trade.entry_time)[:10] if trade.entry_time else "unfilled"
        path = chart_dir / (
            f"{sequence:03d}_{entry_day}_{trade.direction.value}_{trade.result}.png"
        )
        fig.savefig(path, dpi=150, facecolor=fig.get_facecolor())
        plt.close(fig)


def _candles(axis: Any, series: Any, left: int, right: int, rectangle: Any) -> None:
    width = 0.68
    for x, index in enumerate(range(left, right)):
        bullish = series.close[index] >= series.open[index]
        colour = "#5eead4" if bullish else "#f87171"
        axis.vlines(x, series.low[index], series.high[index], color=colour, linewidth=0.65)
        bottom = min(series.open[index], series.close[index])
        height = max(abs(series.close[index] - series.open[index]), 1e-8)
        axis.add_patch(
            rectangle(
                (x - width / 2, bottom),
                width,
                height,
                facecolor=colour,
                edgecolor=colour,
                linewidth=0.5,
            )
        )
    axis.set_xlim(-1, max(1, right - left))
    count = right - left
    if count > 1:
        positions = np.linspace(0, count - 1, min(6, count), dtype=int)
        labels = [
            datetime.fromtimestamp(
                int(series.available_time[left + position]), tz=timezone.utc
            ).strftime("%m-%d\n%H:%M")
            for position in positions
        ]
        axis.set_xticks(positions, labels)


def _validation_markdown(summary: dict[str, Any]) -> str:
    economics = summary["economics"]
    funnel = summary["funnel"]
    casebook = summary["casebook"]
    decision = summary["decision"]
    q1_regression = summary.get("q1Regression")
    profit_factor = economics["profitFactor"]
    profit_factor_text = "n/a" if profit_factor is None else f"{profit_factor:.3f}"
    return "\n".join(
        [
            "# Mentor Engine Validation",
            "",
            f"- Eligible liquidity sweeps: {funnel['eligibleLiquiditySweeps']}",
            f"- Destination plans: {funnel['destinationPlans']}",
            f"- Activated scenarios: {funnel['activatedScenarios']}",
            f"- Orders / closed trades: {funnel['orders']} / {funnel['closedTrades']}",
            f"- Win rate: {economics['winRate'] * 100:.2f}%",
            f"- Profit factor: {profit_factor_text}",
            f"- Net: {economics['netR']:.3f}R",
            f"- Max drawdown: {economics['maxDrawdownR']:.3f}R",
            f"- Spread included: {economics['spreadIncluded']}",
            f"- Commission/swap included: {economics['commissionIncluded']}/{economics['swapIncluded']}",
            f"- Casebook semantic coverage: {casebook['semanticCoverage'] * 100:.2f}%",
            f"- Replayable Casebook cases: {casebook['replayEligibleCases']}",
            f"- Mentor Protocol approved: {decision['mentorProtocolApproved']}",
            f"- Automatic EA approved: {decision['automaticEaApproved']}",
            f"- Q1 as-of regression: {q1_regression.get('passed') if q1_regression else 'not run'}",
            "",
            "Semantic fact coverage is not video-chart replay parity. Account drawdown, "
            "commission, swap, and tick-exact execution remain unavailable in the Python replay.",
            "",
        ]
    )
