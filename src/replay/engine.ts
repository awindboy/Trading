import type {
  M1Bar,
  ReplayBar,
  ReplayDirection,
  ReplayOrderPlan,
  ReplayOrderState,
  ReplayScenarioScope,
  ReplayTimeframe,
} from "./types";

export const TIMEFRAME_SECONDS: Record<ReplayTimeframe, number> = {
  M1: 60,
  M5: 300,
  M15: 900,
  M30: 1800,
  H1: 3600,
};

export const TIMEFRAMES: ReplayTimeframe[] = ["M1", "M5", "M15", "M30", "H1"];

export const SCENARIO_SCOPE_LABELS: Record<ReplayScenarioScope, string> = {
  EXTERNAL_CONTINUATION: "추세지속",
  INTERNAL_ROTATION: "내부회전",
  EXTERNAL_REVERSAL: "추세반전",
};

export function scenarioScopeLabel(scope?: ReplayScenarioScope) {
  return scope ? SCENARIO_SCOPE_LABELS[scope] : "시나리오";
}

export function frontRunLiquidityTarget(
  direction: ReplayDirection,
  objectivePrice: number,
  spread: number,
  point: number,
) {
  const normalizedPoint = Math.max(Math.abs(point), Number.EPSILON);
  const buffer = Math.max(Math.abs(spread), normalizedPoint);
  const rawTarget = direction === "long"
    ? objectivePrice - buffer
    : objectivePrice + buffer;
  const digits = Math.max(0, Math.ceil(-Math.log10(normalizedPoint)));
  return {
    buffer: Number(buffer.toFixed(digits)),
    target: Number(rawTarget.toFixed(digits)),
  };
}

export function formatUtc(timestamp: number, includeDate = true) {
  const date = new Date(timestamp * 1000);
  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: "UTC",
    month: includeDate ? "2-digit" : undefined,
    day: includeDate ? "2-digit" : undefined,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

export function formatKst(timestamp: number) {
  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(timestamp * 1000));
}

export function dateInputFromTimestamp(timestamp: number) {
  return new Date(timestamp * 1000).toISOString().slice(0, 10);
}

export function timestampFromDateInput(value: string) {
  return Math.floor(new Date(`${value}T00:00:00Z`).getTime() / 1000);
}

export function visibleM1Bars(bars: M1Bar[], cursorTime: number) {
  let low = 0;
  let high = bars.length;
  while (low < high) {
    const middle = (low + high) >> 1;
    if (bars[middle].time + 60 <= cursorTime) low = middle + 1;
    else high = middle;
  }
  return bars.slice(0, low);
}

export function aggregateAsOf(
  bars: M1Bar[],
  timeframe: ReplayTimeframe,
  cursorTime: number,
): ReplayBar[] {
  const visible = visibleM1Bars(bars, cursorTime);
  if (timeframe === "M1") {
    return visible.map((bar) => ({ ...bar, confirmed: true }));
  }

  const seconds = TIMEFRAME_SECONDS[timeframe];
  const aggregated: ReplayBar[] = [];
  let active: ReplayBar | null = null;
  let activeBucket = -1;

  for (const bar of visible) {
    const bucket = Math.floor(bar.time / seconds) * seconds;
    if (!active || bucket !== activeBucket) {
      if (active) aggregated.push(active);
      activeBucket = bucket;
      active = {
        time: bucket,
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close,
        spread: bar.spread,
        confirmed: bucket + seconds <= cursorTime,
      };
    } else {
      active.high = Math.max(active.high, bar.high);
      active.low = Math.min(active.low, bar.low);
      active.close = bar.close;
      active.spread = bar.spread;
      active.confirmed = bucket + seconds <= cursorTime;
    }
  }
  if (active) aggregated.push(active);
  return aggregated;
}

export function timeframeSnapshots(bars: M1Bar[], cursorTime: number) {
  return TIMEFRAMES.reduce(
    (result, timeframe) => {
      const aggregated = aggregateAsOf(bars, timeframe, cursorTime);
      result[timeframe] = aggregated[aggregated.length - 1];
      return result;
    },
    {} as Record<ReplayTimeframe, ReplayBar | undefined>,
  );
}

function orderFill(plan: ReplayOrderPlan, bar: M1Bar) {
  if (plan.orderType === "market") return plan.direction === "long" ? bar.open + bar.spread : bar.open;
  if (plan.direction === "long" && bar.low + bar.spread <= plan.entry) {
    return Math.min(plan.entry, bar.open + bar.spread);
  }
  if (plan.direction === "short" && bar.high >= plan.entry) {
    return Math.max(plan.entry, bar.open);
  }
  return undefined;
}

export function evaluateOrder(plan: ReplayOrderPlan, bars: M1Bar[], cursorTime: number): ReplayOrderState {
  const state: ReplayOrderState = { ...plan, status: "pending" };
  let fillPrice: number | undefined;

  for (const bar of bars) {
    const availableAt = bar.time + 60;
    if (availableAt <= plan.createdAt || availableAt > cursorTime) continue;
    if (plan.cancelledAt !== undefined && availableAt >= plan.cancelledAt) break;

    if (fillPrice === undefined) {
      fillPrice = orderFill(plan, bar);
      if (fillPrice === undefined) continue;
      state.status = "filled";
      state.filledAt = availableAt;
      state.entry = fillPrice;
    }

    const askLow = bar.low + bar.spread;
    const askHigh = bar.high + bar.spread;
    const stopHit = plan.direction === "long" ? bar.low <= plan.stop : askHigh >= plan.stop;
    const targetHit = plan.direction === "long" ? bar.high >= plan.target : askLow <= plan.target;
    if (!stopHit && !targetHit) continue;

    state.closedAt = availableAt;
    state.intrabarAmbiguous = stopHit && targetHit;
    if (stopHit) {
      state.status = "loss";
      state.exitPrice = plan.stop;
      state.resultR = -1;
    } else {
      const risk = Math.abs(fillPrice - plan.stop);
      state.status = "win";
      state.exitPrice = plan.target;
      state.resultR = risk > 0 ? Math.abs(plan.target - fillPrice) / risk : 0;
    }
    return state;
  }
  if (fillPrice === undefined && plan.cancelledAt !== undefined && plan.cancelledAt <= cursorTime) {
    state.status = "cancelled";
    state.closedAt = plan.cancelledAt;
  }
  return state;
}

export function evaluateOrders(plans: ReplayOrderPlan[], bars: M1Bar[], cursorTime: number) {
  return plans.map((plan) => evaluateOrder(plan, bars, cursorTime));
}

export function makeId(prefix: string) {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}
