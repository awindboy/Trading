import {
  ArrowLeft,
  Box,
  BrainCircuit,
  CalendarRange,
  ChevronLeft,
  ChevronRight,
  CircleDot,
  Crosshair,
  Database,
  Flag,
  FolderOpen,
  Gauge,
  Minus,
  MousePointer2,
  Pause,
  Play,
  Save,
  ScanLine,
  Square,
  StepForward,
  Target,
  Trash2,
  TrendingUp,
  Type,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ReplayChart from "./ReplayChart";
import {
  aggregateAsOf,
  dateInputFromTimestamp,
  evaluateOrders,
  formatKst,
  formatUtc,
  makeId,
  timeframeSnapshots,
  timestampFromDateInput,
  TIMEFRAMES,
  TIMEFRAME_SECONDS,
  visibleM1Bars,
} from "./engine";
import type {
  DrawingKind,
  ReplayDataResponse,
  ReplayDataset,
  ReplayDirection,
  ReplayDrawing,
  ReplayEvent,
  ReplayOrderPlan,
  ReplayScenarioScope,
  ReplaySession,
  ReplaySessionSummary,
  ReplayTimeframe,
  ScenarioSnapshot,
} from "./types";
import "./replay.css";

type ChartTool = DrawingKind | "cursor";

const DRAWING_TOOLS: Array<{
  id: ChartTool;
  label: string;
  icon: typeof MousePointer2;
  color?: string;
}> = [
  { id: "cursor", label: "차트 이동", icon: MousePointer2 },
  { id: "ob", label: "OB 박스", icon: Box, color: "#60a5fa" },
  { id: "fvg", label: "FVG 박스", icon: Square, color: "#f59e0b" },
  { id: "liquidity", label: "유동성", icon: Minus, color: "#22d3ee" },
  { id: "bos", label: "BOS", icon: TrendingUp, color: "#34d399" },
  { id: "choch", label: "CHoCH", icon: ScanLine, color: "#c084fc" },
  { id: "sweep", label: "Sweep", icon: Zap, color: "#fb7185" },
  { id: "trend", label: "구조선", icon: Crosshair, color: "#cbd5e1" },
  { id: "note", label: "메모", icon: Type, color: "#f8fafc" },
];

const SPEEDS = [1, 5, 15, 60, 240];

function apiBase() {
  const host = window.location.hostname && window.location.hostname !== "localhost"
    ? window.location.hostname
    : "127.0.0.1";
  return `http://${host}:8765`;
}

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
  });
  const payload = await response.json();
  if (!payload.ok) throw new Error(payload.error || "Replay API request failed.");
  return payload as T;
}

function newSession(dataset: ReplayDataset, weekStart: number): ReplaySession {
  const now = new Date().toISOString();
  return {
    id: makeId("mentor"),
    name: `${dataset.symbol} ${dateInputFromTimestamp(weekStart)} Mentor Replay`,
    symbol: dataset.symbol,
    dataset: dataset.name,
    weekStart,
    weekEnd: weekStart + 7 * 86400,
    cursorTime: weekStart,
    maxSeenTime: weekStart,
    timeframe: "H1",
    speed: 15,
    createdAt: now,
    updatedAt: now,
    drawings: [],
    scenarios: [],
    orders: [],
    events: [
      {
        id: makeId("event"),
        time: weekStart,
        type: "session",
        title: "주간 블라인드 재생 시작",
        detail: "미래 봉은 maxSeenTime 이후 공개되지 않습니다.",
      },
    ],
  };
}

function numberOrZero(value: string) {
  const parsed = Number(value.replace(/,/g, ""));
  return Number.isFinite(parsed) ? parsed : 0;
}

function directionLabel(direction: ReplayDirection | "neutral") {
  if (direction === "long") return "상승";
  if (direction === "short") return "하락";
  return "중립";
}

function ReplaySetup({
  datasets,
  sessions,
  loading,
  onCreate,
  onLoad,
}: {
  datasets: ReplayDataset[];
  sessions: ReplaySessionSummary[];
  loading: boolean;
  onCreate: (dataset: ReplayDataset, weekStart: number) => void;
  onLoad: (session: ReplaySessionSummary) => void;
}) {
  const [datasetName, setDatasetName] = useState("");
  const [week, setWeek] = useState("2025-01-06");
  const weekInputRef = useRef<HTMLInputElement>(null);
  const selected = datasets.find((dataset) => dataset.name === datasetName) ?? datasets[0];

  useEffect(() => {
    if (!datasetName && datasets[0]) setDatasetName(datasets[0].name);
  }, [datasetName, datasets]);

  return (
    <main className="replay-setup">
      <header>
        <div className="replay-brand-mark"><ScanLine size={21} /></div>
        <div>
          <span>MENTOR MARKET REPLAY</span>
          <h1>블라인드 시나리오 작업대</h1>
        </div>
        <a href="/"><ArrowLeft size={16} /> 매매일지</a>
      </header>
      <section className="replay-setup-body">
        <div className="setup-primary">
          <span className="section-kicker">NEW REPLAY</span>
          <h2>한 주의 M1 데이터를 실제 차트처럼 재생합니다.</h2>
          <p>H1부터 M1까지 진행 중 캔들이 함께 갱신되며, 당시 그린 구조와 주문 판단이 재생 시각에 맞춰 복원됩니다.</p>
          <label>
            원본 데이터
            <select value={selected?.name || ""} onChange={(event) => setDatasetName(event.target.value)}>
              {datasets.map((dataset) => (
                <option key={dataset.name} value={dataset.name}>
                  {dataset.symbol} · {dateInputFromTimestamp(dataset.firstTime)} ~ {dateInputFromTimestamp(dataset.lastTime)}
                </option>
              ))}
            </select>
          </label>
          <label>
            재생 시작일 (UTC)
            <input
              ref={weekInputRef}
              type="date"
              value={week}
              onChange={(event) => setWeek(event.target.value)}
            />
          </label>
          <button
            type="button"
            className="primary-action"
            disabled={!selected || loading}
            onClick={() => selected && onCreate(
              selected,
              timestampFromDateInput(weekInputRef.current?.value || week),
            )}
          >
            <Play size={17} /> {loading ? "데이터 준비 중" : "새 재생 시작"}
          </button>
        </div>
        <div className="setup-sessions">
          <div className="section-heading">
            <div>
              <span className="section-kicker">SAVED SESSIONS</span>
              <h2>저장된 판단 원장</h2>
            </div>
            <Database size={18} />
          </div>
          <div className="session-list">
            {sessions.map((session) => (
              <button type="button" key={session.id} onClick={() => onLoad(session)}>
                <div>
                  <strong>{session.name}</strong>
                  <span>{formatUtc(session.weekStart)} UTC · {session.symbol}</span>
                </div>
                <div className="session-counts">
                  <span>{session.drawingCount} 구조</span>
                  <span>{session.orderCount} 주문</span>
                </div>
                <ChevronRight size={17} />
              </button>
            ))}
            {!sessions.length ? <div className="empty-sessions">저장된 재생 세션이 없습니다.</div> : null}
          </div>
        </div>
      </section>
    </main>
  );
}

export default function ReplayApp() {
  const [datasets, setDatasets] = useState<ReplayDataset[]>([]);
  const [savedSessions, setSavedSessions] = useState<ReplaySessionSummary[]>([]);
  const [data, setData] = useState<ReplayDataResponse | null>(null);
  const [session, setSession] = useState<ReplaySession | null>(null);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState("");
  const [saveState, setSaveState] = useState("저장 대기");
  const [tool, setTool] = useState<ChartTool>("cursor");
  const [drawingColor, setDrawingColor] = useState("#60a5fa");
  const [drawingLabel, setDrawingLabel] = useState("");
  const [activePanel, setActivePanel] = useState<"scenario" | "order" | "ledger">("scenario");
  const sessionRef = useRef<ReplaySession | null>(null);
  const dirtyRef = useRef(false);
  const skipDirtyRef = useRef(false);
  const sessionRevisionRef = useRef(0);
  const saveQueueRef = useRef<Promise<void>>(Promise.resolve());

  const [scenarioDraft, setScenarioDraft] = useState({
    title: "",
    scope: "EXTERNAL_CONTINUATION" as ReplayScenarioScope,
    direction: "neutral" as ReplayDirection | "neutral",
    mapTimeframe: "H1" as ReplayTimeframe,
    sourceTimeframe: "M15" as ReplayTimeframe,
    objective: "",
    invalidation: "",
    waitingFor: "",
    thesis: "",
  });
  const [orderDraft, setOrderDraft] = useState({
    direction: "long" as ReplayDirection,
    executionModel: "refined-ob-retest" as NonNullable<ReplayOrderPlan["executionModel"]>,
    orderType: "limit" as "market" | "limit",
    entry: "",
    triggerInvalidation: "",
    scenarioInvalidation: "",
    stop: "",
    objectivePrice: "",
    target: "",
    rationale: "",
  });

  useEffect(() => {
    Promise.all([
      api<{ ok: boolean; datasets: ReplayDataset[] }>("/replay/datasets"),
      api<{ ok: boolean; sessions: ReplaySessionSummary[] }>("/replay/sessions"),
    ])
      .then(([datasetPayload, sessionPayload]) => {
        setDatasets(datasetPayload.datasets);
        setSavedSessions(sessionPayload.sessions);
      })
      .catch((error) => setNotice(error instanceof Error ? error.message : "재생 서버 연결 실패"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    sessionRef.current = session;
    if (!session) return;
    sessionRevisionRef.current += 1;
    if (skipDirtyRef.current) {
      skipDirtyRef.current = false;
      return;
    }
    dirtyRef.current = true;
  }, [session]);

  const saveSession = useCallback((silent = false) => {
    const saveLatest = async () => {
      const current = sessionRef.current;
      if (!current || !dirtyRef.current) return;
      const revision = sessionRevisionRef.current;
      if (!silent) setSaveState("저장 중");
      try {
        await api<{ ok: boolean; session: ReplaySession }>("/replay/sessions", {
          method: "POST",
          body: JSON.stringify(current),
        });
        dirtyRef.current = sessionRevisionRef.current !== revision;
        setSaveState(`저장됨 · ${new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })}`);
      } catch (error) {
        dirtyRef.current = true;
        setSaveState("저장 실패");
        setNotice(error instanceof Error ? error.message : "세션 저장 실패");
      }
    };
    const queued = saveQueueRef.current.then(saveLatest, saveLatest);
    saveQueueRef.current = queued.then(() => undefined, () => undefined);
    return queued;
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => void saveSession(true), 5000);
    return () => window.clearInterval(timer);
  }, [saveSession]);

  const loadWeekData = useCallback(async (dataset: ReplayDataset, weekStart: number, days = 7) => {
    setLoading(true);
    setNotice("");
    try {
      const payload = await api<ReplayDataResponse>(
        `/replay/data?dataset=${encodeURIComponent(dataset.name)}&start=${weekStart}&days=${days}&warmupDays=14`,
      );
      setData(payload);
      return payload;
    } finally {
      setLoading(false);
    }
  }, []);

  const createReplay = async (dataset: ReplayDataset, weekStart: number) => {
    try {
      await loadWeekData(dataset, weekStart);
      const created = newSession(dataset, weekStart);
      setSession(created);
      sessionRef.current = created;
      dirtyRef.current = true;
      setPlaying(false);
      setSaveState("새 세션");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "주간 데이터를 불러오지 못했습니다.");
    }
  };

  const loadReplay = async (summary: ReplaySessionSummary) => {
    setLoading(true);
    setNotice("");
    try {
      const payload = await api<{ ok: boolean; session: ReplaySession }>(
        `/replay/sessions/${encodeURIComponent(summary.id)}`,
      );
      const dataset = datasets.find((item) => item.name === payload.session.dataset);
      if (!dataset) throw new Error("세션의 원본 데이터셋을 찾지 못했습니다.");
      const replayDays = Math.max(
        7,
        Math.ceil((payload.session.weekEnd - payload.session.weekStart) / 86400),
      );
      await loadWeekData(dataset, payload.session.weekStart, replayDays);
      skipDirtyRef.current = true;
      setSession(payload.session);
      sessionRef.current = payload.session;
      dirtyRef.current = false;
      setPlaying(false);
      setSaveState("저장본 열림");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "세션을 열지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const replayBars = useMemo(
    () => data?.bars.filter((bar) => bar.time >= data.replayStart && bar.time < data.replayEnd) ?? [],
    [data],
  );
  const replayTimes = useMemo(() => replayBars.map((bar) => bar.time + 60), [replayBars]);

  const advance = useCallback((steps: number) => {
    setSession((current) => {
      if (!current || !replayTimes.length) return current;
      let index = replayTimes.findIndex((time) => time > current.cursorTime);
      if (index < 0) index = replayTimes.length;
      const targetIndex = Math.min(replayTimes.length - 1, Math.max(0, index + steps - 1));
      const cursorTime = replayTimes[targetIndex];
      if (!cursorTime) return current;
      if (cursorTime >= current.weekEnd) setPlaying(false);
      return {
        ...current,
        cursorTime: Math.min(cursorTime, current.weekEnd),
        maxSeenTime: Math.max(current.maxSeenTime, Math.min(cursorTime, current.weekEnd)),
      };
    });
  }, [replayTimes]);

  const rewind = useCallback((steps: number) => {
    setPlaying(false);
    setSession((current) => {
      if (!current || !replayTimes.length) return current;
      let index = replayTimes.findIndex((time) => time >= current.cursorTime);
      if (index < 0) index = replayTimes.length - 1;
      const target = replayTimes[Math.max(0, index - steps)];
      return { ...current, cursorTime: Math.max(current.weekStart, target || current.weekStart) };
    });
  }, [replayTimes]);

  useEffect(() => {
    if (!playing || !session) return;
    const interval = session.speed === 1 ? 1000 : 200;
    const step = session.speed === 1 ? 1 : Math.max(1, Math.round(session.speed / 5));
    const timer = window.setInterval(() => advance(step), interval);
    return () => window.clearInterval(timer);
  }, [advance, playing, session?.speed]);

  const visibleSourceBars = useMemo(
    () => (data && session ? visibleM1Bars(data.bars, session.cursorTime) : []),
    [data, session?.cursorTime],
  );
  const chartBars = useMemo(() => {
    if (!session) return [];
    const seconds = TIMEFRAME_SECONDS[session.timeframe];
    const m1Window = session.timeframe === "M1" ? 1800 : Math.max(2400, Math.ceil((seconds / 60) * 700));
    const source = visibleSourceBars.slice(-m1Window);
    const aggregated = aggregateAsOf(source, session.timeframe, session.cursorTime);
    return aggregated.slice(-(session.timeframe === "M1" ? 1000 : 700));
  }, [session?.cursorTime, session?.timeframe, visibleSourceBars]);
  const snapshots = useMemo(
    () => (session ? timeframeSnapshots(visibleSourceBars.slice(-4000), session.cursorTime) : null),
    [session?.cursorTime, visibleSourceBars],
  );
  const evaluatedOrders = useMemo(
    () => (session && data ? evaluateOrders(session.orders, data.bars, session.cursorTime) : []),
    [data, session?.cursorTime, session?.orders],
  );
  const visibleOrderStates = useMemo(
    () => evaluatedOrders.filter((order) => !session || order.createdAt <= session.cursorTime),
    [evaluatedOrders, session?.cursorTime],
  );
  const visibleScenarios = useMemo(
    () => session?.scenarios.filter((scenario) => scenario.createdAt <= session.cursorTime) ?? [],
    [session?.cursorTime, session?.scenarios],
  );
  const knownOrderStates = useMemo(
    () => (session && data ? evaluateOrders(session.orders, data.bars, session.maxSeenTime) : []),
    [data, session?.maxSeenTime, session?.orders],
  );
  const latestPrice = visibleSourceBars[visibleSourceBars.length - 1]?.close ?? 0;
  const point = data?.dataset.point ?? 0.01;
  const priceDigits = Math.max(0, Math.ceil(-Math.log10(point)));

  const updateOrderObjective = (value: string) => {
    setOrderDraft((current) => {
      const objectivePrice = numberOrZero(value);
      if (!objectivePrice) return { ...current, objectivePrice: value, target: "" };
      return { ...current, objectivePrice: value, target: objectivePrice.toFixed(priceDigits) };
    });
  };

  const updateOrderDirection = (direction: ReplayDirection) => {
    setOrderDraft((current) => {
      const objectivePrice = numberOrZero(current.objectivePrice);
      if (!objectivePrice) return { ...current, direction };
      return { ...current, direction, target: objectivePrice.toFixed(priceDigits) };
    });
  };

  useEffect(() => {
    if (!latestPrice) return;
    setOrderDraft((current) => {
      if (current.entry) return current;
      return { ...current, entry: latestPrice.toFixed(2) };
    });
  }, [latestPrice]);

  const appendEvent = (current: ReplaySession, event: Omit<ReplayEvent, "id">) => ({
    ...current,
    events: [...current.events, { ...event, id: makeId("event") }],
  });

  const createDrawing = (drawing: ReplayDrawing) => {
    setSession((current) => {
      if (!current) return current;
      const next = { ...current, drawings: [...current.drawings, drawing] };
      return appendEvent(next, {
        time: drawing.createdAt,
        type: "drawing",
        title: `[${drawing.timeframe}] ${drawing.label}`,
        detail: "차트 구조 표시",
      });
    });
    setTool("cursor");
  };

  const saveScenario = () => {
    if (!session || !scenarioDraft.title.trim() || !scenarioDraft.thesis.trim()) {
      setNotice("시나리오 제목과 핵심 논리를 입력하세요.");
      return;
    }
    const snapshot: ScenarioSnapshot = {
      id: makeId("scenario"),
      createdAt: session.cursorTime,
      ...scenarioDraft,
    };
    setSession((current) => {
      if (!current) return current;
      const next = { ...current, scenarios: [...current.scenarios, snapshot] };
      return appendEvent(next, {
        time: snapshot.createdAt,
        type: "scenario",
        title: snapshot.title,
        detail: `${directionLabel(snapshot.direction)} · ${snapshot.mapTimeframe}→${snapshot.sourceTimeframe}`,
      });
    });
    setScenarioDraft((current) => ({ ...current, title: "", thesis: "", waitingFor: "" }));
    setNotice("현재 시점의 시나리오를 동결했습니다.");
  };

  const placeOrder = () => {
    if (!session) return;
    const scenario = session.scenarios[session.scenarios.length - 1];
    if (!scenario?.scope) {
      setNotice("범위를 지정한 시나리오를 먼저 저장하세요.");
      return;
    }
    const entry = orderDraft.orderType === "market"
      ? latestPrice
      : numberOrZero(orderDraft.entry);
    const triggerInvalidation = numberOrZero(orderDraft.triggerInvalidation);
    const scenarioInvalidation = numberOrZero(orderDraft.scenarioInvalidation);
    const stop = numberOrZero(orderDraft.stop);
    const objectivePrice = numberOrZero(orderDraft.objectivePrice);
    const target = numberOrZero(orderDraft.target);
    const validLong = orderDraft.direction === "long" && stop < entry && target > entry;
    const validShort = orderDraft.direction === "short" && stop > entry && target < entry;
    if (!entry || !triggerInvalidation || !scenarioInvalidation || !stop || !objectivePrice || !target || (!validLong && !validShort)) {
      setNotice("Entry, 무효화, SL, 목적 유동성, TP를 모두 입력하세요.");
      return;
    }
    const targetMatchesObjective = Math.abs(target - objectivePrice) <= point * 1.1;
    if (!targetMatchesObjective) {
      setNotice("TP는 동결한 목적 유동성 가격과 정확히 같아야 합니다.");
      return;
    }
    const validLongInvalidation = orderDraft.direction === "long"
      && stop < scenarioInvalidation
      && scenarioInvalidation <= triggerInvalidation
      && triggerInvalidation < entry;
    const validShortInvalidation = orderDraft.direction === "short"
      && entry < triggerInvalidation
      && triggerInvalidation <= scenarioInvalidation
      && scenarioInvalidation < stop;
    if (!validLongInvalidation && !validShortInvalidation) {
      setNotice("SL은 시나리오 무효화 바깥이어야 하며, 트리거 무효화만으로 줄일 수 없습니다.");
      return;
    }
    const plan: ReplayOrderPlan = {
      id: makeId("order"),
      createdAt: session.cursorTime,
      direction: orderDraft.direction,
      executionModel: orderDraft.executionModel,
      orderType: orderDraft.orderType,
      entry,
      triggerInvalidation,
      scenarioInvalidation,
      stop,
      objectivePrice,
      targetBuffer: 0,
      target,
      semanticEvidenceValid: false,
      performanceEligible: false,
      semanticAudit: {
        elements: { contract: false },
        failureCodes: ["MANUAL_UI_EVIDENCE_NOT_ATTACHED"],
        failureReasons: ["웹에서 만든 수동 주문에는 OHLC 구조 증거 원장이 첨부되지 않았습니다."],
      },
      evidenceIssue: "구조 증거 원장이 없는 수동 주문이므로 성과 통계에서 제외됩니다.",
      rationale: orderDraft.rationale.trim(),
      scenarioId: scenario.id,
      scenarioScope: scenario.scope,
    };
    setSession((current) => {
      if (!current) return current;
      const next = { ...current, orders: [...current.orders, plan] };
      return appendEvent(next, {
        time: plan.createdAt,
        type: "order",
        title: `${plan.direction.toUpperCase()} ${plan.executionModel} 주문 동결`,
        detail: `${plan.orderType === "market" ? "다음 M1 시가" : plan.entry.toFixed(2)} · 목적 ${objectivePrice.toFixed(priceDigits)} · TP ${target.toFixed(priceDigits)}`,
      });
    });
    setOrderDraft((current) => ({
      ...current,
      entry: "",
      triggerInvalidation: "",
      scenarioInvalidation: "",
      stop: "",
      objectivePrice: "",
      target: "",
      rationale: "",
    }));
    setNotice("주문 판단이 기록되었습니다. 같은 봉에서는 체결되지 않습니다.");
  };

  const cancelPendingOrder = (orderId: string) => {
    if (!session) return;
    setSession((current) => {
      if (!current) return current;
      const order = current.orders.find((item) => item.id === orderId);
      if (!order || order.cancelledAt !== undefined) return current;
      const next = {
        ...current,
        orders: current.orders.map((item) => item.id === orderId
          ? {
              ...item,
              cancelledAt: current.cursorTime,
              cancelReason: "목적 유동성 선도달 또는 구조 무효화",
            }
          : item),
      };
      return appendEvent(next, {
        time: current.cursorTime,
        type: "order",
        title: `${order.direction.toUpperCase()} ${order.orderType.toUpperCase()} 주문 취소`,
        detail: "목적 유동성 선도달 또는 구조 무효화",
      });
    });
    setNotice("보류 주문을 현재 시점에서 취소했습니다.");
  };

  const seekTo = (timestamp: number) => {
    setPlaying(false);
    setSession((current) => current
      ? { ...current, cursorTime: Math.min(Math.max(timestamp, current.weekStart), current.maxSeenTime) }
      : current);
  };

  const returnToSetup = async () => {
    setPlaying(false);
    await saveSession(true);
    try {
      const payload = await api<{ ok: boolean; sessions: ReplaySessionSummary[] }>("/replay/sessions");
      setSavedSessions(payload.sessions);
    } catch {
      // The setup screen can still open with the already loaded summaries.
    }
    sessionRef.current = null;
    dirtyRef.current = false;
    setSession(null);
    setData(null);
  };

  const timelineEvents = useMemo(() => {
    if (!session) return [];
    const derived: ReplayEvent[] = [];
    knownOrderStates.forEach((order) => {
      if (order.filledAt && order.filledAt <= session.maxSeenTime) {
        derived.push({
          id: `${order.id}-fill`,
          time: order.filledAt,
          type: "fill",
          title: `${order.direction.toUpperCase()} 체결`,
          detail: order.entry.toFixed(2),
        });
      }
      if (order.closedAt && order.closedAt <= session.maxSeenTime) {
        const eligible = order.performanceEligible === true;
        derived.push({
          id: `${order.id}-close`,
          time: order.closedAt,
          type: order.status === "win" ? "win" : "loss",
          title: !eligible
            ? "종료 · 성과 검증 제외"
            : order.status === "win"
              ? `TP · +${order.resultR?.toFixed(2)}R`
              : "SL · -1R",
          detail: order.intrabarAmbiguous ? "동일 M1 봉 내 양방향 도달 · 보수적으로 SL 우선" : undefined,
        });
      }
    });
    return [...session.events, ...derived]
      .filter((event) => event.time <= session.cursorTime)
      .sort((a, b) => a.time - b.time);
  }, [knownOrderStates, session]);

  if (!session || !data) {
    return (
      <>
        <ReplaySetup
          datasets={datasets}
          sessions={savedSessions}
          loading={loading}
          onCreate={createReplay}
          onLoad={loadReplay}
        />
        {notice ? <div className="replay-toast">{notice}</div> : null}
      </>
    );
  }

  const progress = ((session.cursorTime - session.weekStart) / (session.weekEnd - session.weekStart)) * 100;
  const blindComplete = session.cursorTime >= session.weekEnd;
  const replayDays = Math.max(1, Math.ceil((session.weekEnd - session.weekStart) / 86400));

  return (
    <main className="replay-workspace">
      <header className="replay-topbar">
        <div className="replay-brand">
          <div className="replay-brand-mark"><ScanLine size={19} /></div>
          <div>
            <span>MENTOR REPLAY</span>
            <input
              value={session.name}
              onChange={(event) => setSession((current) => current ? { ...current, name: event.target.value } : current)}
            />
          </div>
        </div>
        <div className="replay-mode">
          <span className={blindComplete ? "review" : "blind"}>{blindComplete ? "REVIEW MODE" : "BLIND RUN"}</span>
          <strong>{session.symbol}</strong>
          <small>{dateInputFromTimestamp(session.weekStart)} · {replayDays}D</small>
        </div>
        <div className="topbar-actions">
          <span>{saveState}</span>
          <button type="button" title="저장" onClick={() => void saveSession()}><Save size={17} /></button>
          <button
            type="button"
            title="세션 목록"
            onClick={() => void returnToSetup()}
          >
            <FolderOpen size={17} />
          </button>
          <a href="/" title="매매일지"><ArrowLeft size={17} /></a>
        </div>
      </header>

      <section className="replay-body">
        <aside className="replay-left-rail">
          <div className="rail-section">
            <span className="rail-title">TIMEFRAME</span>
            <div className="tf-list">
              {[...TIMEFRAMES].reverse().map((timeframe) => {
                const snapshot = snapshots?.[timeframe];
                return (
                  <button
                    type="button"
                    key={timeframe}
                    className={session.timeframe === timeframe ? "active" : ""}
                    onClick={() => setSession((current) => current ? { ...current, timeframe } : current)}
                  >
                    <strong>{timeframe}</strong>
                    <span>{snapshot?.close.toFixed(2) || "-"}</span>
                    <small className={snapshot?.confirmed ? "closed" : "forming"}>
                      {snapshot?.confirmed ? "확정" : "형성 중"}
                    </small>
                  </button>
                );
              })}
            </div>
          </div>
          <div className="rail-section">
            <span className="rail-title">DRAW</span>
            <div className="drawing-tools">
              {DRAWING_TOOLS.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    type="button"
                    key={item.id}
                    title={item.label}
                    className={tool === item.id ? "active" : ""}
                    onClick={() => {
                      setTool(item.id);
                      if (item.color) setDrawingColor(item.color);
                      if (item.id !== "cursor") setDrawingLabel(item.label.replace(" 박스", ""));
                    }}
                  >
                    <Icon size={17} />
                  </button>
                );
              })}
            </div>
            <label className="drawing-input">
              <input type="color" value={drawingColor} onChange={(event) => setDrawingColor(event.target.value)} />
              <input
                value={drawingLabel}
                onChange={(event) => setDrawingLabel(event.target.value)}
                placeholder="표시 텍스트"
              />
            </label>
            <button
              type="button"
              className="undo-drawing"
              disabled={!session.drawings.length}
              onClick={() => setSession((current) => current
                ? { ...current, drawings: current.drawings.slice(0, -1) }
                : current)}
            >
              <Trash2 size={14} /> 마지막 도형 삭제
            </button>
          </div>
          <div className="rail-section compact">
            <span className="rail-title">AS-OF</span>
            <strong className="rail-clock">{formatUtc(session.cursorTime)}</strong>
            <span>KST {formatKst(session.cursorTime)}</span>
            <small>공개 M1 {visibleSourceBars.filter((bar) => bar.time >= session.weekStart).length.toLocaleString()}개</small>
          </div>
        </aside>

        <section className="replay-center">
          <ReplayChart
            symbol={session.symbol}
            timeframe={session.timeframe}
            bars={chartBars}
            cursorTime={session.cursorTime}
            drawings={session.drawings}
            orders={visibleOrderStates}
            tool={tool}
            color={drawingColor}
            label={drawingLabel}
            onCreateDrawing={createDrawing}
          />
          <div className="replay-controls">
            <button type="button" title="5봉 뒤로" onClick={() => rewind(5)}><ChevronLeft size={18} /></button>
            <button type="button" title="1봉 뒤로" onClick={() => rewind(1)}><ArrowLeft size={16} /></button>
            <button
              type="button"
              className="play-button"
              title={playing ? "일시정지" : "재생"}
              onClick={() => setPlaying((value) => !value)}
            >
              {playing ? <Pause size={20} /> : <Play size={20} />}
            </button>
            <button type="button" title="1분 진행" onClick={() => advance(1)}><StepForward size={18} /></button>
            <button type="button" title="5분 진행" onClick={() => advance(5)}><ChevronRight size={18} /></button>
            <div className="speed-control">
              <Gauge size={16} />
              <select
                value={session.speed}
                onChange={(event) => setSession((current) => current
                  ? { ...current, speed: Number(event.target.value) }
                  : current)}
              >
                {SPEEDS.map((speed) => <option key={speed} value={speed}>{speed}분/초</option>)}
              </select>
            </div>
            <div className="progress-readout">
              <strong>{Math.max(0, Math.min(100, progress)).toFixed(1)}%</strong>
              <span>{formatUtc(session.maxSeenTime)}까지 공개</span>
            </div>
          </div>
          <div className="replay-scrubber">
            <input
              type="range"
              min={session.weekStart}
              max={Math.max(session.weekStart, session.maxSeenTime)}
              step={60}
              value={Math.min(session.cursorTime, session.maxSeenTime)}
              onChange={(event) => seekTo(Number(event.target.value))}
            />
            <div>
              <span>{formatUtc(session.weekStart)}</span>
              <span>미래 데이터 차단선 · {formatUtc(session.maxSeenTime)}</span>
            </div>
          </div>
        </section>

        <aside className="replay-right-panel">
          <nav>
            <button className={activePanel === "scenario" ? "active" : ""} onClick={() => setActivePanel("scenario")}>
              <BrainCircuit size={15} /> 시나리오
            </button>
            <button className={activePanel === "order" ? "active" : ""} onClick={() => setActivePanel("order")}>
              <Target size={15} /> 주문
            </button>
            <button className={activePanel === "ledger" ? "active" : ""} onClick={() => setActivePanel("ledger")}>
              <Flag size={15} /> 원장
            </button>
          </nav>

          {activePanel === "scenario" ? (
            <div className="panel-content scenario-form">
              <div className="panel-heading">
                <div><span>DECISION SNAPSHOT</span><h2>현재 판단 동결</h2></div>
                <CircleDot size={17} />
              </div>
              <label>시나리오 이름<input value={scenarioDraft.title} onChange={(event) => setScenarioDraft({ ...scenarioDraft, title: event.target.value })} placeholder="예: H1 상승 OB 재진입" /></label>
              <div className="triple-fields">
                <label>범위<select value={scenarioDraft.scope} onChange={(event) => setScenarioDraft({ ...scenarioDraft, scope: event.target.value as ReplayScenarioScope })}><option value="EXTERNAL_CONTINUATION">추세지속</option><option value="INTERNAL_ROTATION">내부회전</option><option value="EXTERNAL_REVERSAL">추세반전</option></select></label>
                <label>방향<select value={scenarioDraft.direction} onChange={(event) => setScenarioDraft({ ...scenarioDraft, direction: event.target.value as ReplayDirection | "neutral" })}><option value="neutral">중립</option><option value="long">상승</option><option value="short">하락</option></select></label>
                <label>Map<select value={scenarioDraft.mapTimeframe} onChange={(event) => setScenarioDraft({ ...scenarioDraft, mapTimeframe: event.target.value as ReplayTimeframe })}>{[...TIMEFRAMES].reverse().map((tf) => <option key={tf}>{tf}</option>)}</select></label>
                <label>Source<select value={scenarioDraft.sourceTimeframe} onChange={(event) => setScenarioDraft({ ...scenarioDraft, sourceTimeframe: event.target.value as ReplayTimeframe })}>{[...TIMEFRAMES].reverse().map((tf) => <option key={tf}>{tf}</option>)}</select></label>
              </div>
              <label>목적 유동성<input value={scenarioDraft.objective} onChange={(event) => setScenarioDraft({ ...scenarioDraft, objective: event.target.value })} placeholder="어디까지 전달될 것으로 보는가" /></label>
              <label>무효화 조건<input value={scenarioDraft.invalidation} onChange={(event) => setScenarioDraft({ ...scenarioDraft, invalidation: event.target.value })} placeholder="어떤 구조가 깨지면 틀린가" /></label>
              <label>현재 기다리는 것<input value={scenarioDraft.waitingFor} onChange={(event) => setScenarioDraft({ ...scenarioDraft, waitingFor: event.target.value })} placeholder="OB 접촉, sweep, M1 CHoCH..." /></label>
              <label>시나리오 논리<textarea value={scenarioDraft.thesis} onChange={(event) => setScenarioDraft({ ...scenarioDraft, thesis: event.target.value })} placeholder="현재 보이는 구조만으로 판단을 기록합니다." /></label>
              <button type="button" className="panel-primary" onClick={saveScenario}><Save size={15} /> 이 시점의 판단 저장</button>
              <div className="snapshot-list">
                {[...visibleScenarios].reverse().slice(0, 5).map((scenario) => (
                  <button type="button" key={scenario.id} onClick={() => seekTo(scenario.createdAt)}>
                    <span>{formatUtc(scenario.createdAt, false)} · {scenario.mapTimeframe}</span>
                    <strong>{scenario.title}</strong>
                    <small>{directionLabel(scenario.direction)} · {scenario.waitingFor || "대기 조건 없음"}</small>
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {activePanel === "order" ? (
            <div className="panel-content order-form">
              <div className="panel-heading">
                <div><span>FIXED PLAN</span><h2>주문 판단 기록</h2></div>
                <Target size={17} />
              </div>
              <div className="segmented">
                <button className={orderDraft.direction === "long" ? "active long" : ""} onClick={() => updateOrderDirection("long")}>LONG</button>
                <button className={orderDraft.direction === "short" ? "active short" : ""} onClick={() => updateOrderDirection("short")}>SHORT</button>
              </div>
              <label>실행 모델
                <select
                  value={orderDraft.executionModel}
                  onChange={(event) => setOrderDraft({
                    ...orderDraft,
                    executionModel: event.target.value as NonNullable<ReplayOrderPlan["executionModel"]>,
                  })}
                >
                  <option value="refined-ob-retest">Refined OB retest</option>
                  <option value="delivery-fvg-replacement">Delivery FVG 대체진입</option>
                  <option value="delivery-fvg-addon">Delivery FVG 추가진입</option>
                </select>
              </label>
              <label>주문 방식<select value={orderDraft.orderType} onChange={(event) => setOrderDraft({ ...orderDraft, orderType: event.target.value as "market" | "limit" })}><option value="limit">Limit · 지정가</option><option value="market">Market · 다음 M1 시가</option></select></label>
              <div className="price-grid">
                <label>ENTRY<input inputMode="decimal" value={orderDraft.entry} onChange={(event) => setOrderDraft({ ...orderDraft, entry: event.target.value })} /></label>
                <label>트리거 무효<input inputMode="decimal" value={orderDraft.triggerInvalidation} onChange={(event) => setOrderDraft({ ...orderDraft, triggerInvalidation: event.target.value })} /></label>
                <label>시나리오 무효<input inputMode="decimal" value={orderDraft.scenarioInvalidation} onChange={(event) => setOrderDraft({ ...orderDraft, scenarioInvalidation: event.target.value })} /></label>
              </div>
              <div className="price-grid">
                <label>SL<input inputMode="decimal" value={orderDraft.stop} onChange={(event) => setOrderDraft({ ...orderDraft, stop: event.target.value })} /></label>
                <label>목적 유동성<input inputMode="decimal" value={orderDraft.objectivePrice} onChange={(event) => updateOrderObjective(event.target.value)} /></label>
                <label>TP<input inputMode="decimal" value={orderDraft.target} onChange={(event) => setOrderDraft({ ...orderDraft, target: event.target.value })} /></label>
              </div>
              <label>진입 근거<textarea value={orderDraft.rationale} onChange={(event) => setOrderDraft({ ...orderDraft, rationale: event.target.value })} placeholder="owner/objective → source → M1 trigger 또는 delivery FVG 첫 retest" /></label>
              <div className="order-contract">
                <span>결정 봉 체결 금지</span><span>동일 봉 충돌은 SL 우선</span><span>TP = 목적 유동성</span><span>구조 증거 없으면 성과 제외</span>
              </div>
              <button type="button" className="panel-primary" onClick={placeOrder}><Target size={15} /> 주문 계획 동결</button>
              <div className="order-list">
                {[...visibleOrderStates].reverse().map((order) => (
                  <button
                    type="button"
                    key={order.id}
                    title={order.status === "pending" ? "보류 주문 취소" : "주문 시점으로 이동"}
                    onClick={() => order.status === "pending"
                      ? cancelPendingOrder(order.id)
                      : seekTo(order.createdAt)}
                  >
                    <span className={`order-side ${order.direction}`}>{order.direction.toUpperCase()}</span>
                    <div>
                      <strong>{order.entry.toFixed(2)}</strong>
                      <small>{formatUtc(order.createdAt, false)} · {order.executionModel || order.orderType}</small>
                      {order.semanticEvidenceValid !== true
                      || order.performanceEligible !== true
                      || order.sourceEvidenceValid === false
                      || order.entryEvidenceValid === false
                      || order.stopEvidenceValid === false ? (
                        <small className="evidence-invalid">
                          검증 제외 · {order.evidenceIssue || "구조 근거 무효"}
                        </small>
                      ) : null}
                    </div>
                    <span className={`order-status ${order.status}`}>
                      {order.performanceEligible !== true ? "검증 제외" : order.status}
                      {order.performanceEligible === true && order.resultR
                        ? ` ${order.resultR > 0 ? "+" : ""}${order.resultR.toFixed(2)}R`
                        : ""}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {activePanel === "ledger" ? (
            <div className="panel-content ledger-panel">
              <div className="panel-heading">
                <div><span>AS-OF LEDGER</span><h2>판단 타임라인</h2></div>
                <CalendarRange size={17} />
              </div>
              <div className="ledger-list">
                {[...timelineEvents].reverse().map((event) => (
                  <button
                    type="button"
                    key={event.id}
                    className={event.time === session.cursorTime ? "current" : ""}
                    onClick={() => seekTo(event.time)}
                  >
                    <time>{formatUtc(event.time)}</time>
                    <span className={`event-dot ${event.type}`} />
                    <div><strong>{event.title}</strong>{event.detail ? <small>{event.detail}</small> : null}</div>
                  </button>
                ))}
              </div>
            </div>
          ) : null}
        </aside>
      </section>
      {notice ? <button type="button" className="replay-toast" onClick={() => setNotice("")}>{notice}</button> : null}
    </main>
  );
}
