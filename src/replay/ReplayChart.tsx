import {
  CandlestickSeries,
  ColorType,
  createChart,
  type CandlestickData,
  type IChartApi,
  type ISeriesApi,
  type MouseEventParams,
  type UTCTimestamp,
} from "lightweight-charts";
import {
  type PointerEvent as ReactPointerEvent,
  type MouseEvent as ReactMouseEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type {
  DrawingKind,
  PriceAnchor,
  ReplayBar,
  ReplayDrawing,
  ReplayOrderState,
  ReplayTimeframe,
} from "./types";
import { formatUtc, makeId, scenarioScopeLabel, TIMEFRAME_SECONDS } from "./engine";

type ChartTool = DrawingKind | "cursor";

type ReplayChartProps = {
  symbol: string;
  timeframe: ReplayTimeframe;
  bars: ReplayBar[];
  cursorTime: number;
  drawings: ReplayDrawing[];
  orders: ReplayOrderState[];
  tool: ChartTool;
  color: string;
  label: string;
  onCreateDrawing: (drawing: ReplayDrawing) => void;
};

type PixelAnchor = PriceAnchor & { x: number; y: number };

const BOX_KINDS = new Set<DrawingKind>(["ob", "fvg"]);
const LINE_KINDS = new Set<DrawingKind>(["liquidity", "bos", "choch", "trend"]);
const IMPORTED_DRAWING_PATTERN = /^drawing-(.+)-(root|parent|source|entry|objective|sweep|choch)$/;

function defaultDrawingLabel(kind: DrawingKind) {
  return {
    ob: "OB",
    fvg: "FVG",
    poi: "POI",
    liquidity: "Liquidity",
    bos: "BOS",
    choch: "CHoCH",
    sweep: "Sweep",
    trend: "Structure",
    note: "Note",
  }[kind];
}

export default function ReplayChart({
  symbol,
  timeframe,
  bars,
  cursorTime,
  drawings,
  orders,
  tool,
  color,
  label,
  onCreateDrawing,
}: ReplayChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const barsRef = useRef<ReplayBar[]>(bars);
  const lastTimeframeRef = useRef<ReplayTimeframe>(timeframe);
  const lastDataLengthRef = useRef(0);
  const [revision, setRevision] = useState(0);
  const [draftAnchor, setDraftAnchor] = useState<PriceAnchor | null>(null);
  const [hover, setHover] = useState<ReplayBar | null>(null);

  useEffect(() => {
    barsRef.current = bars;
  }, [bars]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const chart = createChart(container, {
      autoSize: false,
      width: Math.max(1, container.clientWidth),
      height: Math.max(1, container.clientHeight),
      layout: {
        background: { type: ColorType.Solid, color: "#090d12" },
        textColor: "#94a3b8",
        fontFamily: "Inter, Pretendard, system-ui, sans-serif",
      },
      grid: {
        vertLines: { color: "rgba(148,163,184,0.055)" },
        horzLines: { color: "rgba(148,163,184,0.055)" },
      },
      crosshair: {
        vertLine: { color: "rgba(226,232,240,0.36)", labelBackgroundColor: "#253044" },
        horzLine: { color: "rgba(226,232,240,0.28)", labelBackgroundColor: "#253044" },
      },
      rightPriceScale: {
        borderColor: "rgba(148,163,184,0.16)",
        scaleMargins: { top: 0.08, bottom: 0.08 },
      },
      timeScale: {
        borderColor: "rgba(148,163,184,0.16)",
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 7,
        barSpacing: 8,
      },
    });
    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#2dd4bf",
      downColor: "#fb7185",
      borderUpColor: "#2dd4bf",
      borderDownColor: "#fb7185",
      wickUpColor: "#5eead4",
      wickDownColor: "#fda4af",
      priceLineVisible: false,
      lastValueVisible: true,
    });
    const handleRange = () => setRevision((value) => value + 1);
    const handleCrosshair = (param: MouseEventParams) => {
      const data = param.seriesData.get(series) as CandlestickData<UTCTimestamp> | undefined;
      if (!data || typeof data.open !== "number") {
        setHover(null);
        return;
      }
      const source = barsRef.current.find((bar) => bar.time === Number(data.time));
      setHover(source ?? null);
    };
    chart.timeScale().subscribeVisibleLogicalRangeChange(handleRange);
    chart.subscribeCrosshairMove(handleCrosshair);
    const resizeObserver = new ResizeObserver((entries) => {
      const size = entries[0]?.contentRect;
      if (!size || size.width <= 0 || size.height <= 0) return;
      chart.resize(Math.floor(size.width), Math.floor(size.height));
    });
    resizeObserver.observe(container);
    chartRef.current = chart;
    seriesRef.current = series;
    return () => {
      chart.timeScale().unsubscribeVisibleLogicalRangeChange(handleRange);
      chart.unsubscribeCrosshairMove(handleCrosshair);
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    const series = seriesRef.current;
    const chart = chartRef.current;
    if (!series || !chart) return;
    const data: CandlestickData<UTCTimestamp>[] = bars.map((bar) => ({
      time: bar.time as UTCTimestamp,
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
      color: bar.close >= bar.open ? "#2dd4bf" : "#fb7185",
      borderColor: bar.confirmed ? (bar.close >= bar.open ? "#2dd4bf" : "#fb7185") : "#fbbf24",
      wickColor: bar.confirmed ? (bar.close >= bar.open ? "#5eead4" : "#fda4af") : "#fbbf24",
    }));
    const previousLength = lastDataLengthRef.current;
    const visibleRange = chart.timeScale().getVisibleLogicalRange();
    const wasFollowingLatest = (
      previousLength === 0
      || (visibleRange !== null && visibleRange.to >= previousLength - 2)
    );
    series.setData(data);
    const timeframeChanged = lastTimeframeRef.current !== timeframe;
    lastTimeframeRef.current = timeframe;
    lastDataLengthRef.current = data.length;
    if (data.length) {
      const span = timeframe === "M1" ? 150 : timeframe === "M5" ? 130 : 100;
      if (timeframeChanged || previousLength === 0) {
        chart.timeScale().setVisibleLogicalRange({
          from: Math.max(0, data.length - span),
          to: data.length + 6,
        });
      } else if (wasFollowingLatest) {
        chart.timeScale().scrollToRealTime();
      }
    }
    setRevision((value) => value + 1);
  }, [bars, timeframe]);

  useEffect(() => {
    setDraftAnchor(null);
  }, [tool, timeframe]);

  const toPixel = useCallback((anchor: PriceAnchor): PixelAnchor | null => {
    const chart = chartRef.current;
    const series = seriesRef.current;
    if (!chart || !series) return null;
    const seconds = TIMEFRAME_SECONDS[timeframe];
    const chartTime = Math.floor(anchor.time / seconds) * seconds;
    const x = chart.timeScale().timeToCoordinate(chartTime as UTCTimestamp);
    const y = series.priceToCoordinate(anchor.price);
    if (x === null || y === null) return null;
    return { ...anchor, x, y };
  }, [revision, timeframe]);

  const focusedOrderId = useMemo(
    () => orders
      .filter((order) => order.createdAt <= cursorTime)
      .reduce<ReplayOrderState | null>(
        (latest, order) => (!latest || order.createdAt > latest.createdAt ? order : latest),
        null,
      )?.id,
    [cursorTime, orders],
  );

  const visibleDrawings = useMemo(
    () => drawings.filter((drawing) => {
      if (drawing.evidenceStatus !== "validated" && drawing.evidenceStatus !== "manual") {
        return false;
      }
      if (drawing.createdAt > cursorTime) return false;
      const imported = drawing.id.match(IMPORTED_DRAWING_PATTERN);
      if (imported && imported[1] !== focusedOrderId) return false;
      return drawing.timeframe === timeframe || BOX_KINDS.has(drawing.kind);
    }),
    [cursorTime, drawings, focusedOrderId, timeframe],
  );

  const drawingPixels = useMemo(
    () => {
      const lastVisibleBarTime = bars[bars.length - 1]?.time ?? cursorTime;
      return (
      visibleDrawings
        .map((drawing) => ({
          drawing,
          anchors: drawing.anchors
            .map((anchor) => toPixel(
              anchor.time > lastVisibleBarTime
                ? { ...anchor, time: lastVisibleBarTime }
                : anchor,
            ))
            .filter((anchor): anchor is PixelAnchor => Boolean(anchor)),
        }))
        .filter((item) => item.anchors.length)
      );
    },
    [bars, cursorTime, toPixel, visibleDrawings],
  );

  const orderPixels = useMemo(
    () =>
      orders
        .filter(
          (order) => order.id === focusedOrderId
            && order.filledAt
            && order.createdAt <= cursorTime,
        )
        .map((order) => {
          const eventOffset = TIMEFRAME_SECONDS.M1;
          const startTime = Math.max(0, order.filledAt! - eventOffset);
          const endTime = Math.max(
            startTime,
            Math.min((order.closedAt ?? cursorTime) - eventOffset, cursorTime - eventOffset),
          );
          const start = toPixel({ time: startTime, price: order.entry });
          const end = toPixel({ time: endTime, price: order.entry });
          const stop = toPixel({ time: endTime, price: order.stop });
          const target = toPixel({ time: endTime, price: order.target });
          return start && end && stop && target ? { order, start, end, stop, target } : null;
        })
        .filter((item): item is NonNullable<typeof item> => Boolean(item)),
    [cursorTime, focusedOrderId, orders, toPixel],
  );

  const pointerAnchor = (
    event: ReactPointerEvent<SVGElement> | ReactMouseEvent<SVGElement>,
  ): PriceAnchor | null => {
    const chart = chartRef.current;
    const series = seriesRef.current;
    if (!chart || !series || !containerRef.current) return null;
    const rect = containerRef.current.getBoundingClientRect();
    const rawX = Number(event.clientX);
    const rawY = Number(event.clientY);
    const x = Number.isFinite(rawX) && rawX >= rect.left && rawX <= rect.right
      ? rawX - rect.left
      : rect.width / 2;
    const y = Number.isFinite(rawY) && rawY >= rect.top && rawY <= rect.bottom
      ? rawY - rect.top
      : rect.height / 2;
    const resolvedTime = chart.timeScale().coordinateToTime(x);
    const resolvedPrice = series.coordinateToPrice(y);
    let time = typeof resolvedTime === "number" ? Number(resolvedTime) : 0;
    if (!time) {
      const logical = chart.timeScale().coordinateToLogical(x);
      if (logical !== null && bars.length) {
        const index = Math.max(0, Math.min(bars.length - 1, Math.round(logical)));
        time = bars[index].time;
      }
    }
    if (!time && bars.length) time = bars[bars.length - 1].time;
    const price = resolvedPrice === null && bars.length ? bars[bars.length - 1].close : Number(resolvedPrice);
    if (!time || !Number.isFinite(price)) return null;
    return { time, price };
  };

  const handleDraw = (
    event: ReactPointerEvent<SVGElement> | ReactMouseEvent<SVGElement>,
  ) => {
    if (tool === "cursor") return;
    event.preventDefault();
    const anchor = pointerAnchor(event);
    if (!anchor) return;
    const kind = tool as DrawingKind;
    const requiresPair = BOX_KINDS.has(kind) || LINE_KINDS.has(kind);
    if (requiresPair && !draftAnchor) {
      setDraftAnchor(anchor);
      return;
    }
    const anchors = requiresPair ? [draftAnchor!, anchor] : [anchor];
    if (kind !== "trend" && LINE_KINDS.has(kind) && anchors.length === 2) {
      anchors[1] = { ...anchors[1], price: anchors[0].price };
    }
    onCreateDrawing({
      id: makeId("drawing"),
      kind,
      timeframe,
      label: label.trim() || defaultDrawingLabel(kind),
      color,
      createdAt: cursorTime,
      anchors,
      evidenceStatus: "manual",
    });
    setDraftAnchor(null);
  };

  const activeBar = hover ?? bars[bars.length - 1] ?? null;
  const forming = bars.length ? !bars[bars.length - 1].confirmed : false;

  return (
    <div className="replay-chart-stage">
      <div className="replay-chart-legend">
        <strong>{symbol}</strong>
        <span>{timeframe}</span>
        <span className={forming ? "forming" : "confirmed"}>{forming ? "진행 중 HTF" : "확정봉"}</span>
        {activeBar ? (
          <span className="ohlc">
            O {activeBar.open.toFixed(2)} H {activeBar.high.toFixed(2)} L {activeBar.low.toFixed(2)} C{" "}
            {activeBar.close.toFixed(2)}
          </span>
        ) : null}
      </div>
      <div ref={containerRef} className="replay-lw-chart" />
      <svg
        className={`replay-drawing-layer ${tool === "cursor" ? "passive" : "drawing"}`}
        onClick={handleDraw}
      >
        {tool !== "cursor" ? (
          <rect
            className="drawing-hit-target"
            x="0"
            y="0"
            width="100%"
            height="100%"
            fill="transparent"
          />
        ) : null}
        {orderPixels.map(({ order, start, end, stop, target }) => {
          const left = Math.min(start.x, end.x);
          const width = Math.max(5, Math.abs(end.x - start.x));
          const profitTop = Math.min(start.y, target.y);
          const riskTop = Math.min(start.y, stop.y);
          const boxTop = Math.min(start.y, stop.y, target.y);
          const scenarioLabel = order.scenarioScope
            ? scenarioScopeLabel(order.scenarioScope)
            : "";
          return (
            <g key={order.id}>
              <rect
                x={left}
                y={profitTop}
                width={width}
                height={Math.max(1, Math.abs(start.y - target.y))}
                fill="rgba(45,212,191,0.18)"
                stroke="rgba(94,234,212,0.72)"
                strokeWidth="1"
              />
              <rect
                x={left}
                y={riskTop}
                width={width}
                height={Math.max(1, Math.abs(start.y - stop.y))}
                fill="rgba(251,113,133,0.18)"
                stroke="rgba(253,164,175,0.72)"
                strokeWidth="1"
              />
              {scenarioLabel ? (
                <text
                  x={left + 5}
                  y={Math.max(12, boxTop - 20)}
                  fill="#e2e8f0"
                  fontSize="10"
                  fontWeight="600"
                >
                  {scenarioLabel}
                </text>
              ) : null}
            </g>
          );
        })}
        {drawingPixels.map(({ drawing, anchors }) => {
          const first = anchors[0];
          const second = anchors[1];
          if (BOX_KINDS.has(drawing.kind) && second) {
            const rawX = Math.min(first.x, second.x);
            const y = Math.min(first.y, second.y);
            const rawWidth = Math.abs(first.x - second.x);
            const minimumWidth = drawing.timeframe === timeframe ? 8 : 30;
            const width = Math.max(minimumWidth, rawWidth);
            const x = rawWidth < minimumWidth ? rawX - (minimumWidth - rawWidth) / 2 : rawX;
            const height = Math.abs(first.y - second.y);
            const isRootOb = drawing.label === "ROOT OB";
            const isRefinedOb = drawing.label === "REFINED OB";
            const labelY = isRootOb
              ? Math.max(11, y - 5)
              : isRefinedOb
                ? y + Math.max(13, height + 12)
                : y + height / 2;
            return (
              <g key={drawing.id}>
                <rect
                  x={x}
                  y={y}
                  width={width}
                  height={Math.max(2, height)}
                  fill={`${drawing.color}26`}
                  stroke={drawing.color}
                  strokeWidth={isRootOb ? "1.8" : "1.3"}
                  strokeDasharray={isRefinedOb ? "5 3" : undefined}
                />
                <text
                  x={x + width / 2}
                  y={labelY}
                  fill={drawing.color}
                  stroke="#090d12"
                  strokeWidth="2.5"
                  paintOrder="stroke"
                  textAnchor="middle"
                  fontSize="10"
                >
                  [{drawing.timeframe}] {drawing.label}
                </text>
              </g>
            );
          }
          if (LINE_KINDS.has(drawing.kind) && second) {
            return (
              <g key={drawing.id}>
                <line
                  x1={first.x}
                  y1={first.y}
                  x2={second.x}
                  y2={second.y}
                  stroke={drawing.color}
                  strokeWidth={drawing.kind === "trend" ? 1.5 : 1.2}
                  strokeDasharray={drawing.kind === "liquidity" ? "6 5" : "4 3"}
                />
                <text
                  x={(first.x + second.x) / 2}
                  y={(first.y + second.y) / 2 - 7}
                  fill={drawing.color}
                  textAnchor="middle"
                  fontSize="11"
                >
                  [{drawing.timeframe}] {drawing.label}
                </text>
              </g>
            );
          }
          if (drawing.kind === "sweep") {
            return (
              <g key={drawing.id}>
                <path
                  d={`M ${first.x} ${first.y} l -5 -9 l 10 0 z`}
                  fill={drawing.color}
                  stroke="#090d12"
                  strokeWidth="0.6"
                />
                <text x={first.x + 8} y={first.y - 5} fill={drawing.color} fontSize="10">
                  {drawing.label}
                </text>
              </g>
            );
          }
          return (
            <g key={drawing.id}>
              <circle cx={first.x} cy={first.y} r="3" fill={drawing.color} />
              <text x={first.x + 7} y={first.y - 7} fill={drawing.color} fontSize="11">
                [{drawing.timeframe}] {drawing.label}
              </text>
            </g>
          );
        })}
        {draftAnchor ? (() => {
          const pixel = toPixel(draftAnchor);
          return pixel ? <circle cx={pixel.x} cy={pixel.y} r="5" fill={color} stroke="#fff" strokeWidth="1" /> : null;
        })() : null}
      </svg>
      <div className="replay-chart-clock">
        <span>UTC {formatUtc(cursorTime)}</span>
        <strong>{forming ? `${timeframe} 캔들 형성 중` : "확정 데이터"}</strong>
      </div>
    </div>
  );
}
