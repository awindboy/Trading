import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  CandlestickSeries,
  ColorType,
  createChart,
  LineStyle,
  type CandlestickData,
  type IChartApi,
  type IPriceLine,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Brain,
  CalendarDays,
  Calculator,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Circle,
  ClipboardList,
  Cloud,
  DatabaseZap,
  Download,
  FileJson,
  FileSpreadsheet,
  Gauge,
  ImagePlus,
  Minus,
  Plus,
  Save,
  Search,
  Send,
  ShieldCheck,
  Square,
  Target,
  Type,
  Trash2,
  Undo2,
  Upload,
  Wallet,
  X,
} from "lucide-react";
import {
  ChangeEvent,
  ClipboardEvent,
  DragEvent,
  FormEvent,
  PointerEvent,
  ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

type Direction = "long" | "short";
type TradeStatus = "open" | "closed";
type TradeResult = "open" | "win" | "loss" | "breakeven";
type TradeSource = "manual" | "mt5";
type WorkspaceTab = "journal" | "analytics" | "calendar" | "reviews" | "aiFeedback" | "chart" | "order";
type ReviewType = "daily" | "weekly" | "monthly";
type AnalyticsPeriod = "today" | "week" | "month" | "all";
type AnnotationTool = "hline" | "vline" | "segment" | "rectangle" | "circle" | "text";

type AiFeedbackStatus = "pass" | "fail" | "unknown";

type AiFeedback = {
  id: string;
  generatedAt: string;
  mentor: string;
  version?: string;
  usedBars?: boolean;
  analysisSource?: "mt5-bars" | "screenshot-fallback";
  timeframes?: {
    role?: string;
    timeframe: string;
    reason?: string;
    score?: number;
    available: boolean;
    location: string;
    trend: string;
    sweep: string;
    choch: string;
    fvg: boolean;
  }[];
  title: string;
  verdict: string;
  score: number;
  summary: string;
  checklist: {
    label: string;
    status: AiFeedbackStatus;
    detail: string;
  }[];
  feedback: string[];
  improvements: string[];
  nextRules: string[];
  mentorReview?: {
    title: string;
    generatedAt?: string;
    source?: string;
    paragraphs: string[];
  };
  journalNotes?: string[];
  chartNotes?: string[];
  chartImage?: string;
  chartImageName?: string;
};

type ChartAnnotation = {
  id: string;
  type: AnnotationTool;
  color: string;
  strokeWidth: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  text?: string;
};

type Trade = {
  id: string;
  createdAt: string;
  updatedAt: string;
  date: string;
  market: string;
  symbol: string;
  currency: string;
  direction: Direction;
  setup: string;
  timeframe: string;
  status: TradeStatus;
  result: TradeResult;
  accountValue: number;
  riskPercent: number;
  entryPrice: number;
  stopPrice: number;
  targetPrice: number;
  exitPrice: number;
  quantity: number;
  fees: number;
  brokerPnl?: number;
  brokerGrossPnl?: number;
  brokerCommission?: number;
  brokerSwap?: number;
  brokerFee?: number;
  source?: TradeSource;
  externalId?: string;
  brokerMeta?: {
    accountLogin?: number;
    server?: string;
    ticket?: number;
    positionId?: number;
    order?: number;
    magic?: number;
    comment?: string;
    openTime?: string;
    closeTime?: string;
  };
  confidence: number;
  discipline: number;
  emotion: string;
  grade: string;
  tags: string[];
  thesis: string;
  riskPlan: string;
  good: string;
  bad: string;
  lesson: string;
  screenshot?: string;
  screenshotName?: string;
  screenshotAnnotations?: ChartAnnotation[];
  aiFeedback?: AiFeedback;
};

type TradeDraft = Omit<Trade, "id" | "createdAt" | "updatedAt" | "tags" | "result"> & {
  tags: string;
  result: TradeResult;
};

type Review = {
  id: string;
  type: ReviewType;
  periodKey: string;
  title: string;
  startDate: string;
  endDate: string;
  completed: boolean;
  createdAt: string;
  updatedAt: string;
  marketSummary: string;
  good: string;
  bad: string;
  lesson: string;
  nextPlan: string;
  score: number;
};

type ReviewDraft = Omit<Review, "id" | "createdAt" | "updatedAt" | "completed"> & {
  completed: boolean;
};

type DerivedTrade = {
  allocated: number;
  plannedRisk: number;
  riskBudget: number;
  actualRiskPercent: number;
  rewardRisk: number;
  pnlPercent: number;
  suggestedQuantity: number;
  pnl: number;
  rMultiple: number;
  computedResult: TradeResult;
};

type Mt5Account = {
  login?: number;
  server?: string;
  name?: string;
  currency?: string;
  balance?: number;
  equity?: number;
  margin?: number;
  marginFree?: number;
  leverage?: number;
};

type Mt5Position = {
  ticket: number;
  symbol: string;
  direction: Direction;
  volume: number;
  priceOpen: number;
  priceCurrent: number;
  stopLoss: number;
  takeProfit: number;
  profit: number;
  swap: number;
  comment: string;
  time: string;
};

type Mt5ImportedTrade = {
  externalId: string;
  date: string;
  symbol: string;
  direction: Direction;
  status?: TradeStatus;
  entryPrice: number;
  stopPrice: number;
  targetPrice: number;
  exitPrice: number;
  quantity: number;
  brokerPnl: number;
  brokerGrossPnl?: number;
  brokerCommission?: number;
  brokerSwap?: number;
  brokerFee?: number;
  fees: number;
  currency?: string;
  accountValue?: number;
  comment?: string;
  openTime?: string;
  closeTime?: string;
  positionId?: number;
  ticket?: number;
  order?: number;
  magic?: number;
  screenshot?: string;
  screenshotName?: string;
  source?: "mt5" | "mt5-ea";
};

type Mt5Snapshot = {
  ok: boolean;
  generatedAt?: string;
  account?: Mt5Account;
  positions: Mt5Position[];
  trades: Mt5ImportedTrade[];
  ea?: {
    eventFile?: string;
    eventFileExists?: boolean;
    eventFileModifiedAt?: string;
    secondsSinceEventFileModified?: number;
    csvFile?: string;
    csvFileExists?: boolean;
    csvFileModifiedAt?: string;
    eventSource?: "jsonl" | "csv";
    jsonEventCount?: number;
    csvEventCount?: number;
    eventCount?: number;
    tradeEventCount?: number;
    statusEventCount?: number;
    parseErrorCount?: number;
    tradeCount?: number;
    lastEvent?: string;
    lastEventTime?: string;
    lastStatus?: string;
    lastStatusTime?: string;
    lastStatusChartSymbol?: string;
    lastStatusPositionsTotal?: number;
    lastStatusEaVersion?: string;
    lastStatusFeatures?: string;
    secondsSinceLastEvent?: number;
    secondsSinceLastStatus?: number;
    attachmentState?: "missing" | "connected" | "stale" | "stopped" | "unknown";
    attachmentMessage?: string;
  };
  error?: string;
};

type JournalResponse = {
  ok: boolean;
  trades: Trade[];
  reviews?: Review[];
  updatedAt?: string;
  storage?: string;
  error?: string;
};

type JournalWriteResponse = {
  ok: boolean;
  trade?: Trade;
  review?: Review;
  updatedAt?: string;
  storage?: string;
  error?: string;
};

type AiFeedbackResponse = {
  ok: boolean;
  tradeId?: string;
  usedBars?: boolean;
  feedback?: AiFeedback;
  trade?: Trade;
  error?: string;
};

type AiFeedbackPreflight = {
  ok: boolean;
  tradeId?: string;
  symbol?: string;
  generatedAt?: string;
  mt5PackageAvailable?: boolean;
  mt5TerminalRunning?: boolean;
  canUseBars?: boolean;
  message?: string;
  timeframes?: {
    timeframe: string;
    available: boolean;
    bars: number;
    symbol?: string;
    error?: string;
  }[];
  error?: string;
};

type AiFeedbackBatchResponse = {
  ok: boolean;
  jobId?: string;
  total?: number;
  alreadyRunning?: boolean;
  error?: string;
};

type AiFeedbackBatchJob = {
  ok: boolean;
  jobId?: string;
  status?: "queued" | "running" | "completed" | "failed";
  total?: number;
  completed?: number;
  failed?: number;
  usedBars?: number;
  currentTradeId?: string;
  currentSymbol?: string;
  errors?: { tradeId?: string; symbol?: string; error?: string }[];
  error?: string;
};

type PendingJournalChange = {
  id: string;
  kind: "trade" | "review";
  key: string;
  payload: Trade | Review;
  createdAt: string;
  attempts: number;
};

type OrderSide = "buy" | "sell";

type OrderDraft = {
  symbol: string;
  side: OrderSide;
  riskPercent: number;
  stopLoss: number;
  takeProfit: number;
  deviation: number;
  fillPolicy: "IOC" | "FOK" | "RETURN";
  comment: string;
};

type OrderPreview = {
  ok: boolean;
  error?: string;
  account?: Mt5Account;
  symbol?: string;
  side?: OrderSide;
  entryPrice?: number;
  bid?: number;
  ask?: number;
  spread?: number;
  stopLoss?: number;
  takeProfit?: number;
  riskPercent?: number;
  riskAmount?: number;
  riskPerLot?: number;
  rawVolume?: number;
  volume?: number;
  volumeMin?: number;
  volumeMax?: number;
  volumeStep?: number;
  estimatedLoss?: number;
  estimatedProfit?: number;
  rewardRisk?: number;
  currency?: string;
  orderCheck?: Record<string, unknown>;
  warnings?: string[];
};

type OrderSendResult = {
  ok: boolean;
  error?: string;
  result?: Record<string, unknown>;
  preview?: OrderPreview;
};

type ChartTimeframe = "M1" | "M5" | "M15" | "H1" | "H4" | "D1";

type ChartBar = {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  spread: number;
  realVolume: number;
};

type Mt5Tick = {
  time?: string;
  timeRaw?: number;
  bid: number;
  ask: number;
  last?: number;
  volume?: number;
  flags?: number;
};

type Mt5SymbolInfo = {
  name?: string;
  description?: string;
  digits?: number;
  point?: number;
  tradeTickSize?: number;
  tradeTickValue?: number;
  volumeMin?: number;
  volumeMax?: number;
  volumeStep?: number;
  spread?: number;
};

type ChartResponse = {
  ok: boolean;
  error?: string;
  generatedAt?: string;
  symbol?: string;
  timeframe?: ChartTimeframe;
  bars: ChartBar[];
  tick?: Mt5Tick;
  symbolInfo?: Mt5SymbolInfo;
};

type LiveResponse = {
  ok: boolean;
  error?: string;
  generatedAt?: string;
  account?: Mt5Account;
  positions: Mt5Position[];
  tick?: Mt5Tick;
  symbolInfo?: Mt5SymbolInfo;
};

const STORAGE_KEY = "trading-journal:v3";
const REVIEWS_STORAGE_KEY = "trading-journal-reviews:v1";
const PENDING_JOURNAL_CHANGES_KEY = "trading-journal-pending:v1";
const ANNOTATION_COLOR_PRESETS_KEY = "trading-journal-annotation-colors:v1";
const MT5_SERVER_TIME_ZONE = "Etc/GMT-3";
const MT5_REPORT_FILE_TYPES = ".html,.htm,.xls,.csv,.tsv,text/html,text/csv,application/vnd.ms-excel";
const brokenEmotionValues = new Set(["???", "李⑤텇??", "차분??"]);
const autoThesisValues = new Set(["MT5 청산 거래 자동 가져오기", "MT5 현재 포지션 자동 불러오기"]);
const bridgeHost =
  typeof window !== "undefined" && window.location.hostname && window.location.hostname !== "localhost"
    ? window.location.hostname
    : "127.0.0.1";
const envBridgeUrl = (import.meta as unknown as { env?: Record<string, string | undefined> }).env?.VITE_MT5_BRIDGE_URL;
const MT5_BRIDGE_URL = envBridgeUrl ?? `http://${bridgeHost}:8765`;
const chartTimeframes: ChartTimeframe[] = ["M1", "M5", "M15", "H1", "H4", "D1"];

const marketOptions = ["XM MT5", "FOREX", "METALS", "ENERGY", "INDEX CFD", "STOCK CFD", "CRYPTO", "KRX", "NASDAQ", "NYSE"];
const setupOptions = ["기타", "돌파", "눌림목", "추세 추종", "반전", "갭", "뉴스", "실적"];
const timeframeOptions = ["1m", "5m", "15m", "1H", "4H", "1D", "1W"];
const emotionOptions = ["차분함", "확신", "조급함", "공포", "탐욕", "피로", "복수매매"];
const gradeOptions = ["A", "B", "C", "D"];
const annotationTools: { tool: AnnotationTool; label: string; icon: ReactNode }[] = [
  { tool: "hline", label: "수평선", icon: <Minus size={16} /> },
  { tool: "vline", label: "수직선", icon: <Minus className="rotate-icon" size={16} /> },
  { tool: "segment", label: "선분", icon: <Minus size={16} /> },
  { tool: "rectangle", label: "사각형", icon: <Square size={16} /> },
  { tool: "circle", label: "원", icon: <Circle size={16} /> },
  { tool: "text", label: "텍스트", icon: <Type size={16} /> },
];

const resultLabel: Record<TradeResult, string> = {
  open: "보유",
  win: "수익",
  loss: "손실",
  breakeven: "본전",
};

const directionLabel: Record<Direction, string> = {
  long: "Long",
  short: "Short",
};

const reviewTypeLabel: Record<ReviewType, string> = {
  daily: "일일",
  weekly: "주간",
  monthly: "월간",
};

const analyticsPeriodLabel: Record<AnalyticsPeriod, string> = {
  today: "금일",
  week: "일주일",
  month: "한달",
  all: "전체",
};

const aiFeedbackStatusLabel: Record<AiFeedbackStatus, string> = {
  pass: "충족",
  fail: "누락",
  unknown: "불명확",
};

const aiFeedbackRoleLabel: Record<string, string> = {
  htf: "HTF",
  context: "Context",
  ltf: "LTF",
};

const aiFeedbackJobStatusLabel: Record<string, string> = {
  queued: "대기 중",
  running: "분석 중",
  completed: "완료",
  failed: "실패",
};

const todayInput = () => {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 10);
};

function localDateInput(date: Date) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 10);
}

function parseDateInput(value: string) {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year || 1970, (month || 1) - 1, day || 1);
}

function addDays(date: Date, days: number) {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

function startOfWeek(date: Date) {
  const next = new Date(date);
  const day = next.getDay();
  next.setDate(next.getDate() - day);
  return next;
}

function endOfWeek(date: Date) {
  return addDays(startOfWeek(date), 6);
}

function monthKey(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

function reviewPeriodKey(type: ReviewType, startDate: string, endDate: string) {
  return `${type}:${startDate}:${endDate}`;
}

const createDraft = (): TradeDraft => ({
  date: todayInput(),
  market: "XM MT5",
  symbol: "",
  currency: "USD",
  direction: "long",
  setup: "기타",
  timeframe: "MT5",
  status: "open",
  result: "open",
  accountValue: 10_000,
  riskPercent: 1,
  entryPrice: 0,
  stopPrice: 0,
  targetPrice: 0,
  exitPrice: 0,
  quantity: 0,
  fees: 0,
  confidence: 3,
  discipline: 3,
  emotion: "차분함",
  grade: "B",
  tags: "",
  thesis: "",
  riskPlan: "",
  good: "",
  bad: "",
  lesson: "",
});

const createOrderDraft = (): OrderDraft => ({
  symbol: "XAUUSD",
  side: "buy",
  riskPercent: 1,
  stopLoss: 0,
  takeProfit: 0,
  deviation: 20,
  fillPolicy: "IOC",
  comment: "Trade Ledger",
});

const number = new Intl.NumberFormat("ko-KR", {
  maximumFractionDigits: 2,
});

function formatMoney(value: number, currencyCode = "USD") {
  const code = currencyCode || "USD";
  if (code.toUpperCase() === "USD") {
    const sign = value < 0 ? "-" : "";
    return `${sign}$${number.format(Math.abs(value || 0))}`;
  }
  const zeroDecimal = ["JPY", "KRW"].includes(code.toUpperCase());

  try {
    return new Intl.NumberFormat("ko-KR", {
      style: "currency",
      currency: code,
      maximumFractionDigits: zeroDecimal ? 0 : 2,
    }).format(value || 0);
  } catch {
    return `${number.format(value || 0)} ${code}`;
  }
}

function formatCompactMoney(value: number, currencyCode = "USD") {
  if ((currencyCode || "USD").toUpperCase() === "USD") {
    const sign = value < 0 ? "-" : "";
    return `${sign}$${number.format(Math.abs(value || 0))}`;
  }
  return formatMoney(value, currencyCode);
}

function formatPercent(value: number) {
  if (!Number.isFinite(value)) return "0.00%";
  const absolute = Math.abs(value);
  if (absolute > 0 && absolute < 0.01) {
    return `${value < 0 ? "-" : ""}<0.01%`;
  }
  return `${value.toFixed(absolute >= 100 ? 1 : 2)}%`;
}

function formatPnlComponents(trade: Pick<Trade, "currency" | "brokerGrossPnl" | "brokerSwap" | "brokerCommission" | "brokerFee">) {
  const components = [
    typeof trade.brokerGrossPnl === "number" ? `가격 ${formatMoney(trade.brokerGrossPnl, trade.currency)}` : "",
    trade.brokerSwap ? `스왑 ${formatMoney(trade.brokerSwap, trade.currency)}` : "",
    trade.brokerCommission ? `커미션 ${formatMoney(trade.brokerCommission, trade.currency)}` : "",
    trade.brokerFee ? `수수료 ${formatMoney(trade.brokerFee, trade.currency)}` : "",
  ].filter(Boolean);

  return components.length > 1 ? components.join(" · ") : "";
}

function uid() {
  return globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function toNumber(value: string) {
  const parsed = Number(value.replace(/,/g, ""));
  return Number.isFinite(parsed) ? parsed : 0;
}

function normalizeSymbol(value: string) {
  return value.trim().toUpperCase();
}

function pricePrecision(symbolInfo?: Mt5SymbolInfo, fallbackPrice = 0) {
  if (typeof symbolInfo?.digits === "number" && symbolInfo.digits >= 0) {
    return Math.min(symbolInfo.digits, 8);
  }
  return fallbackPrice >= 100 ? 2 : 5;
}

function roundPrice(value: number, symbolInfo?: Mt5SymbolInfo) {
  if (!Number.isFinite(value)) return 0;
  return Number(value.toFixed(pricePrecision(symbolInfo, value)));
}

function normalizeTags(value: string | string[]) {
  if (Array.isArray(value)) {
    return value.map((tag) => tag.trim()).filter(Boolean);
  }

  return value
    .split(/[,#]/)
    .map((tag) => tag.trim())
    .filter(Boolean);
}

function compactDateTime(value?: string) {
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value.replace("T", " ").slice(0, 16);
  return parsed.toLocaleString("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function tradeTimeLabel(trade: Pick<Trade, "date" | "brokerMeta"> & Partial<Pick<Trade, "createdAt">>) {
  const open = compactDateTime(trade.brokerMeta?.openTime || trade.createdAt);
  const close = compactDateTime(trade.brokerMeta?.closeTime);
  if (open && close && open !== close) return `${open} -> ${close}`;
  return close || open || trade.date;
}

function rawDateTimeLabel(value?: string) {
  if (!value) return "";
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})/);
  if (match) return `${match[2]}.${match[3]} ${match[4]}:${match[5]}`;
  return compactDateTime(value);
}

function zonedDateTimeLabel(value?: string, timeZone = "Asia/Seoul") {
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return rawDateTimeLabel(value);
  try {
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone,
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    })
      .formatToParts(parsed)
      .reduce<Record<string, string>>((acc, part) => {
        acc[part.type] = part.value;
        return acc;
      }, {});
    return `${parts.month}.${parts.day} ${parts.hour}:${parts.minute}`;
  } catch {
    return rawDateTimeLabel(value);
  }
}

function timeRangeLabel(open?: string, close?: string, formatter = rawDateTimeLabel) {
  const openLabel = formatter(open);
  const closeLabel = formatter(close);
  if (openLabel && closeLabel && openLabel !== closeLabel) return `${openLabel} -> ${closeLabel}`;
  return closeLabel || openLabel || "";
}

function holdingTimeLabel(trade: Pick<Trade, "brokerMeta"> & Partial<Pick<Trade, "createdAt" | "updatedAt">>) {
  const open = trade.brokerMeta?.openTime || trade.createdAt;
  const close = trade.brokerMeta?.closeTime || trade.updatedAt;
  const openMs = open ? new Date(open).getTime() : 0;
  const closeMs = close ? new Date(close).getTime() : 0;
  if (!Number.isFinite(openMs) || !Number.isFinite(closeMs) || closeMs <= openMs) return "";
  const totalMinutes = Math.max(1, Math.round((closeMs - openMs) / 60_000));
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  if (hours && minutes) return `${hours}h ${minutes}m`;
  if (hours) return `${hours}h`;
  return `${minutes}m`;
}

function tradeSyncTime(trade: Trade) {
  const candidates = [trade.brokerMeta?.closeTime, trade.brokerMeta?.openTime, trade.createdAt, trade.updatedAt, trade.date]
    .filter(Boolean)
    .map((value) => new Date(String(value)).getTime())
    .filter((value) => Number.isFinite(value));
  return candidates.length ? Math.max(...candidates) : 0;
}

function tradeOrderTime(trade: Pick<Trade, "date" | "createdAt" | "brokerMeta">) {
  const candidates = [trade.brokerMeta?.closeTime, trade.brokerMeta?.openTime, trade.date, trade.createdAt]
    .filter(Boolean)
    .map((value) => new Date(String(value)).getTime())
    .filter((value) => Number.isFinite(value));
  return candidates.length ? Math.max(...candidates) : 0;
}

function compareTradesByTradeTimeDesc(a: Trade, b: Trade) {
  const diff = tradeOrderTime(b) - tradeOrderTime(a);
  if (diff !== 0) return diff;
  return b.createdAt.localeCompare(a.createdAt);
}

function latestTradeSyncIso(trades: Trade[]) {
  const latest = trades.reduce((max, trade) => Math.max(max, tradeSyncTime(trade)), 0);
  return latest > 0 ? new Date(latest - 60_000).toISOString() : "";
}

function clampUnit(value: unknown) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 0;
  return Math.max(0, Math.min(1, numeric));
}

function normalizeAnnotations(value: unknown): ChartAnnotation[] {
  if (!Array.isArray(value)) return [];
  const validTools = new Set<AnnotationTool>(["hline", "vline", "segment", "rectangle", "circle", "text"]);

  return value
    .map((item) => item as Partial<ChartAnnotation>)
    .filter((item) => item && validTools.has(item.type as AnnotationTool))
    .map((item) => ({
      id: item.id || uid(),
      type: item.type as AnnotationTool,
      color: typeof item.color === "string" && item.color ? item.color : "#f59e0b",
      strokeWidth: Math.max(1, Math.min(12, Number(item.strokeWidth) || 2)),
      x1: clampUnit(item.x1),
      y1: clampUnit(item.y1),
      x2: clampUnit(item.x2),
      y2: clampUnit(item.y2),
      text: typeof item.text === "string" ? item.text : "",
    }));
}

function normalizeTextList(value: unknown) {
  if (!Array.isArray(value)) return [];
  return value.map((item) => String(item ?? "").trim()).filter(Boolean);
}

function normalizeAiFeedback(value: unknown): AiFeedback | undefined {
  if (!value || typeof value !== "object") return undefined;
  const item = value as Partial<AiFeedback>;
  const checklist = Array.isArray(item.checklist)
    ? item.checklist
        .map((entry) => entry as Partial<AiFeedback["checklist"][number]>)
        .filter((entry) => entry && entry.label)
        .map((entry) => {
          const status: AiFeedbackStatus = entry.status === "pass" || entry.status === "fail" ? entry.status : "unknown";
          return {
            label: String(entry.label ?? ""),
            status,
            detail: String(entry.detail ?? ""),
          };
        })
    : [];
  const mentorReviewSource = item.mentorReview && typeof item.mentorReview === "object"
    ? item.mentorReview as Record<string, unknown>
    : null;
  const mentorReview = mentorReviewSource
    ? {
        title: String(mentorReviewSource.title || "Codex 멘토 피드백"),
        generatedAt: mentorReviewSource.generatedAt ? String(mentorReviewSource.generatedAt) : undefined,
        source: mentorReviewSource.source ? String(mentorReviewSource.source) : undefined,
        paragraphs: normalizeTextList(mentorReviewSource.paragraphs),
      }
    : undefined;

  return {
    id: String(item.id || uid()),
    generatedAt: String(item.generatedAt || new Date().toISOString()),
    mentor: String(item.mentor || "Arthur / ICT 기준"),
    version: item.version ? String(item.version) : undefined,
    usedBars: Boolean(item.usedBars),
    analysisSource: item.analysisSource === "mt5-bars" ? "mt5-bars" : "screenshot-fallback",
    timeframes: Array.isArray(item.timeframes)
      ? item.timeframes.map((timeframe) => {
          const row = timeframe as Record<string, unknown>;
          return {
            role: String(row.role || ""),
            timeframe: String(row.timeframe || ""),
            reason: String(row.reason || ""),
            score: typeof row.score === "number" ? row.score : undefined,
            available: Boolean(row.available),
            location: String(row.location || "unknown"),
            trend: String(row.trend || "unknown"),
            sweep: String(row.sweep || "unknown"),
            choch: String(row.choch || "unknown"),
            fvg: Boolean(row.fvg),
          };
        })
      : [],
    title: String(item.title || "MTF 차트 근거 보드"),
    verdict: String(item.verdict || ""),
    score: Math.max(1, Math.min(5, Number(item.score) || 3)),
    summary: String(item.summary || ""),
    checklist,
    feedback: normalizeTextList(item.feedback),
    improvements: normalizeTextList(item.improvements),
    nextRules: normalizeTextList(item.nextRules),
    mentorReview,
    journalNotes: normalizeTextList(item.journalNotes),
    chartNotes: normalizeTextList(item.chartNotes),
    chartImage: typeof item.chartImage === "string" ? item.chartImage : undefined,
    chartImageName: typeof item.chartImageName === "string" ? item.chartImageName : undefined,
  };
}

function computeTrade(trade: Pick<Trade, "accountValue" | "riskPercent" | "entryPrice" | "stopPrice" | "targetPrice" | "exitPrice" | "quantity" | "fees" | "direction" | "status" | "brokerPnl">): DerivedTrade {
  const unitRisk = trade.entryPrice > 0 && trade.stopPrice > 0 ? Math.abs(trade.entryPrice - trade.stopPrice) : 0;
  const unitReward = trade.entryPrice > 0 && trade.targetPrice > 0 ? Math.abs(trade.targetPrice - trade.entryPrice) : 0;
  const accountBasis = Math.abs(trade.accountValue || 0);
  const riskBudget = accountBasis * (trade.riskPercent / 100);
  const suggestedQuantity = unitRisk > 0 ? Math.max(Math.floor(riskBudget / unitRisk), 0) : 0;
  const allocated = trade.entryPrice * trade.quantity;
  const rewardRisk = unitRisk > 0 ? unitReward / unitRisk : 0;

  const rawPnl =
    trade.status === "closed" && trade.exitPrice > 0 && trade.quantity > 0
      ? trade.direction === "long"
        ? (trade.exitPrice - trade.entryPrice) * trade.quantity
        : (trade.entryPrice - trade.exitPrice) * trade.quantity
      : 0;
  const hasBrokerPnl = typeof trade.brokerPnl === "number" && Number.isFinite(trade.brokerPnl);
  const pnl = hasBrokerPnl ? trade.brokerPnl || 0 : rawPnl - (trade.status === "closed" ? trade.fees : 0);
  const exitMove = trade.entryPrice > 0 && trade.exitPrice > 0 ? Math.abs(trade.exitPrice - trade.entryPrice) : 0;
  const inferredValuePerPoint = hasBrokerPnl && exitMove > 0 ? Math.abs(pnl) / exitMove : 0;
  const fallbackRisk = unitRisk * trade.quantity;
  const plannedRisk = inferredValuePerPoint > 0 ? unitRisk * inferredValuePerPoint : fallbackRisk;
  const actualRiskPercent = accountBasis > 0 ? (plannedRisk / accountBasis) * 100 : 0;
  const pnlPercent = accountBasis > 0 ? (pnl / accountBasis) * 100 : 0;
  const rMultiple = trade.status === "closed" && plannedRisk > 0 ? pnl / plannedRisk : 0;
  const computedResult: TradeResult =
    trade.status === "open" ? "open" : pnl > 0 ? "win" : pnl < 0 ? "loss" : "breakeven";

  return {
    allocated,
    plannedRisk,
    riskBudget,
    actualRiskPercent,
    rewardRisk,
    pnlPercent,
    suggestedQuantity,
    pnl,
    rMultiple,
    computedResult,
  };
}

function tradeCloseDate(trade: Pick<Trade, "date" | "brokerMeta">) {
  return (trade.brokerMeta?.closeTime || trade.date).slice(0, 10);
}

function tradeCloseDateTime(trade: Pick<Trade, "date" | "brokerMeta" | "updatedAt">) {
  return trade.brokerMeta?.closeTime || trade.updatedAt || `${trade.date}T23:59:59`;
}

function tradesInRange(trades: Trade[], startDate: string, endDate: string) {
  return trades.filter((trade) => {
    if (trade.status !== "closed") return false;
    const date = tradeCloseDate(trade);
    return date >= startDate && date <= endDate;
  });
}

function summarizeTrades(trades: Trade[]) {
  const closed = trades.filter((trade) => trade.status === "closed");
  const pnl = closed.reduce((sum, trade) => sum + computeTrade(trade).pnl, 0);
  const wins = closed.filter((trade) => computeTrade(trade).computedResult === "win").length;
  const losses = closed.filter((trade) => computeTrade(trade).computedResult === "loss").length;
  const rewardRisks = closed.map((trade) => computeTrade(trade).rewardRisk).filter((value) => value > 0);
  const avgRewardRisk = rewardRisks.length ? rewardRisks.reduce((sum, value) => sum + value, 0) / rewardRisks.length : 0;
  const winRate = closed.length ? (wins / closed.length) * 100 : 0;
  return { trades: closed.length, pnl, wins, losses, winRate, avgRewardRisk };
}

function buildAnalyticsEquityCurve(trades: Trade[], startDate: string, endDate: string, period: AnalyticsPeriod) {
  const bucketPnl = new Map<string, number>();
  trades.forEach((trade) => {
    const closeTime = tradeCloseDateTime(trade);
    const closeDate = tradeCloseDate(trade);
    const parsed = new Date(closeTime);
    const hour = Number.isNaN(parsed.getTime()) ? "00" : String(parsed.getHours()).padStart(2, "0");
    const key = period === "today" ? `${closeDate}T${hour}` : closeDate;
    bucketPnl.set(key, (bucketPnl.get(key) ?? 0) + computeTrade(trade).pnl);
  });

  const points: { key: string; label: string; bucketPnl: number; pnl: number }[] = [];
  let cumulative = 0;

  if (period === "today") {
    for (let hour = 0; hour < 24; hour += 1) {
      const key = `${startDate}T${String(hour).padStart(2, "0")}`;
      cumulative += bucketPnl.get(key) ?? 0;
      points.push({
        key,
        label: `${String(hour).padStart(2, "0")}:00`,
        bucketPnl: Math.round((bucketPnl.get(key) ?? 0) * 100) / 100,
        pnl: Math.round(cumulative * 100) / 100,
      });
    }
    return points;
  }

  for (let cursor = parseDateInput(startDate); localDateInput(cursor) <= endDate; cursor = addDays(cursor, 1)) {
    const key = localDateInput(cursor);
    cumulative += bucketPnl.get(key) ?? 0;
    points.push({
      key,
      label: key.slice(5),
      bucketPnl: Math.round((bucketPnl.get(key) ?? 0) * 100) / 100,
      pnl: Math.round(cumulative * 100) / 100,
    });
  }

  return points;
}

function reviewSummaryText(type: ReviewType, startDate: string, endDate: string, trades: Trade[], currency: string) {
  const summary = summarizeTrades(trades);
  const title = type === "daily" ? startDate : `${startDate} ~ ${endDate}`;
  return `${reviewTypeLabel[type]} ${title}
거래 ${summary.trades}건 · 승 ${summary.wins} / 패 ${summary.losses} · 승률 ${summary.winRate.toFixed(1)}%
손익 ${formatMoney(summary.pnl, currency)} · 평균 손익비 ${summary.avgRewardRisk.toFixed(2)}:1`;
}

function createReviewDraft(type: ReviewType, startDate: string, endDate: string, trades: Trade[], currency: string): ReviewDraft {
  const summaryTitle = type === "daily" ? startDate : `${startDate} ~ ${endDate}`;
  return {
    type,
    periodKey: reviewPeriodKey(type, startDate, endDate),
    title: `${reviewTypeLabel[type]} 결산 · ${summaryTitle}`,
    startDate,
    endDate,
    completed: false,
    marketSummary: reviewSummaryText(type, startDate, endDate, trades, currency),
    good: "",
    bad: "",
    lesson: "",
    nextPlan: "",
    score: 3,
  };
}

function normalizeReview(value: Partial<Review>): Review {
  const now = new Date().toISOString();
  const type = value.type === "weekly" || value.type === "monthly" ? value.type : "daily";
  const startDate = value.startDate || todayInput();
  const endDate = value.endDate || startDate;
  return {
    id: value.id || uid(),
    type,
    periodKey: value.periodKey || reviewPeriodKey(type, startDate, endDate),
    title: value.title || `${reviewTypeLabel[type]} 결산`,
    startDate,
    endDate,
    completed: Boolean(value.completed),
    createdAt: value.createdAt || now,
    updatedAt: value.updatedAt || now,
    marketSummary: value.marketSummary || "",
    good: value.good || "",
    bad: value.bad || "",
    lesson: value.lesson || "",
    nextPlan: value.nextPlan || "",
    score: Math.max(1, Math.min(5, Number(value.score) || 3)),
  };
}

function reviewHasContent(review: Review) {
  return [review.good, review.bad, review.lesson, review.nextPlan].some((value) => value.trim().length > 0);
}

function mergeReviews(localReviews: Review[], serverReviews: Review[]) {
  const merged = new Map<string, Review>();
  const put = (review: Review) => {
    const key = review.periodKey || review.id;
    const current = merged.get(key);
    if (!current) {
      merged.set(key, review);
      return;
    }
    const currentHasContent = reviewHasContent(current);
    const nextHasContent = reviewHasContent(review);
    const currentTime = Date.parse(current.updatedAt || current.createdAt || "");
    const nextTime = Date.parse(review.updatedAt || review.createdAt || "");
    if (currentHasContent && !nextHasContent) return;
    if (!currentHasContent && nextHasContent) {
      merged.set(key, review);
      return;
    }
    if ((Number.isFinite(nextTime) ? nextTime : 0) >= (Number.isFinite(currentTime) ? currentTime : 0)) {
      merged.set(key, review);
    }
  };

  localReviews.forEach(put);
  serverReviews.forEach(put);
  return Array.from(merged.values()).sort((a, b) => {
    if (a.startDate !== b.startDate) return b.startDate.localeCompare(a.startDate);
    return a.type.localeCompare(b.type);
  });
}

function loadReviews() {
  if (typeof localStorage === "undefined") return [];
  try {
    const raw = localStorage.getItem(REVIEWS_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.map((item) => normalizeReview(item));
  } catch {
    return [];
  }
}

function loadAnnotationColorPresets() {
  const fallback = ["#f59e0b", "#ffffff", "#ef4444", "#22c55e", "#60a5fa"];
  if (typeof localStorage === "undefined") return fallback;
  try {
    const parsed = JSON.parse(localStorage.getItem(ANNOTATION_COLOR_PRESETS_KEY) || "[]");
    if (!Array.isArray(parsed)) return fallback;
    const valid = parsed
      .map((value) => String(value || "").trim())
      .filter((value) => /^#[0-9a-f]{6}$/i.test(value))
      .slice(0, 5);
    return [...valid, ...fallback].slice(0, 5);
  } catch {
    return fallback;
  }
}

function loadTrades(): Trade[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return normalizeStoredTrades(parsed);
  } catch {
    return [];
  }
}

function tradeForLocalCache(trade: Trade): Trade {
  return {
    ...trade,
    screenshot: undefined,
    screenshotName: trade.screenshotName,
    screenshotAnnotations: trade.screenshotAnnotations ?? [],
    aiFeedback: trade.aiFeedback
      ? {
          ...trade.aiFeedback,
          chartImage: undefined,
          chartImageName: trade.aiFeedback.chartImageName,
        }
      : undefined,
  };
}

function reviewForLocalCache(review: Review): Review {
  return { ...review };
}

function safeLocalStorageSet(key: string, value: unknown) {
  if (typeof localStorage === "undefined") return true;
  const serialized = JSON.stringify(value);
  try {
    localStorage.setItem(key, serialized);
    return true;
  } catch {
    try {
      localStorage.removeItem(key);
      localStorage.setItem(key, serialized);
      return true;
    } catch {
      return false;
    }
  }
}

function loadPendingJournalChanges(): PendingJournalChange[] {
  if (typeof localStorage === "undefined") return [];
  try {
    const parsed = JSON.parse(localStorage.getItem(PENDING_JOURNAL_CHANGES_KEY) || "[]");
    if (!Array.isArray(parsed)) return [];
    return parsed
      .map((item) => item as Partial<PendingJournalChange>)
      .filter((item): item is PendingJournalChange => item.kind === "trade" || item.kind === "review")
      .filter((item) => Boolean(item.key && item.payload));
  } catch {
    return [];
  }
}

function storePendingJournalChanges(changes: PendingJournalChange[]) {
  if (typeof localStorage === "undefined") return;
  safeLocalStorageSet(PENDING_JOURNAL_CHANGES_KEY, changes);
}

function queuePendingJournalChange(kind: "trade" | "review", key: string, payload: Trade | Review) {
  if (!key) return;
  const now = new Date().toISOString();
  const existing = loadPendingJournalChanges().filter((change) => !(change.kind === kind && change.key === key));
  const queuePayload = kind === "trade" ? tradeForLocalCache(payload as Trade) : reviewForLocalCache(payload as Review);
  storePendingJournalChanges([
    ...existing,
    {
      id: `${kind}:${key}:${Date.now()}`,
      kind,
      key,
      payload: queuePayload,
      createdAt: now,
      attempts: 0,
    },
  ]);
}

function normalizeStoredTrades(value: unknown): Trade[] {
  const rawTrades = Array.isArray(value) ? value : typeof value === "object" && value !== null ? (value as { trades?: unknown }).trades : [];
  if (!Array.isArray(rawTrades)) return [];
  return rawTrades.map((trade) => {
    const item = trade as Partial<Trade>;
    return {
      ...item,
      id: item.id ?? uid(),
      createdAt: item.createdAt ?? new Date().toISOString(),
      updatedAt: item.updatedAt ?? new Date().toISOString(),
      currency: item.currency ?? "USD",
      tags: normalizeTags(item.tags ?? []),
      exitPrice: Number(item.exitPrice ?? 0),
      fees: Number(item.fees ?? 0),
      brokerGrossPnl: item.brokerGrossPnl === undefined ? undefined : Number(item.brokerGrossPnl),
      brokerCommission: item.brokerCommission === undefined ? undefined : Number(item.brokerCommission),
      brokerSwap: item.brokerSwap === undefined ? undefined : Number(item.brokerSwap),
      brokerFee: item.brokerFee === undefined ? undefined : Number(item.brokerFee),
      screenshotAnnotations: normalizeAnnotations(item.screenshotAnnotations),
      aiFeedback: normalizeAiFeedback(item.aiFeedback),
    } as Trade;
  });
}

function downloadBlob(contents: string, filename: string, type: string) {
  const blob = new Blob([contents], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function escapeCsv(value: unknown) {
  const text = String(value ?? "");
  return `"${text.replace(/"/g, '""')}"`;
}

function toCsv(trades: Trade[]) {
  const columns = [
    "date",
    "market",
    "symbol",
    "direction",
    "setup",
    "timeframe",
    "status",
    "result",
    "source",
    "externalId",
    "currency",
    "entryPrice",
    "stopPrice",
    "targetPrice",
    "exitPrice",
    "quantity",
    "plannedRisk",
    "pnl",
    "rMultiple",
    "emotion",
    "discipline",
    "grade",
    "tags",
    "thesis",
    "good",
    "bad",
    "lesson",
  ];

  const rows = trades.map((trade) => {
    const derived = computeTrade(trade);
    const values: Record<string, unknown> = {
      ...trade,
      plannedRisk: Math.round(derived.plannedRisk),
      pnl: Math.round(derived.pnl),
      rMultiple: derived.rMultiple.toFixed(2),
      tags: trade.tags.join(", "),
      source: trade.source ?? "manual",
    };
    return columns.map((column) => escapeCsv(values[column])).join(",");
  });

  return `\ufeff${columns.join(",")}\n${rows.join("\n")}`;
}

function buildTradeFromDraft(draft: TradeDraft, existing?: Trade): Trade {
  const now = new Date().toISOString();
  const quantity = draft.quantity || computeTrade({ ...draft, quantity: draft.quantity }).suggestedQuantity;
  const computed = computeTrade({ ...draft, quantity });

  return {
    ...draft,
    id: existing?.id ?? uid(),
    createdAt: existing?.createdAt ?? now,
    updatedAt: now,
    symbol: draft.symbol.trim().toUpperCase(),
    setup: draft.setup.trim() || "기타",
    currency: draft.currency.trim().toUpperCase() || "USD",
    tags: normalizeTags(draft.tags),
    quantity,
    result: computed.computedResult,
  };
}

function draftFromTrade(trade: Trade): TradeDraft {
  return {
    ...trade,
    tags: trade.tags.join(", "),
  };
}

function resultFromPnl(status: TradeStatus, pnl: number): TradeResult {
  if (status === "open") return "open";
  if (pnl > 0) return "win";
  if (pnl < 0) return "loss";
  return "breakeven";
}

function normalizeImportedTrade(imported: Mt5ImportedTrade, account?: Mt5Account): Trade {
  const now = new Date().toISOString();
  const currency = (imported.currency ?? account?.currency ?? "USD").toUpperCase();
  const pnl = Number(imported.brokerPnl ?? 0);
  const status = imported.status ?? "closed";
  const trade: Trade = {
    id: imported.externalId || uid(),
    externalId: imported.externalId,
    source: "mt5",
    createdAt: imported.openTime ?? imported.closeTime ?? now,
    updatedAt: now,
    date: imported.date || todayInput(),
    market: "XM MT5",
    symbol: imported.symbol.toUpperCase(),
    currency,
    direction: imported.direction,
    setup: "기타",
    timeframe: "MT5",
    status,
    result: resultFromPnl(status, pnl),
    accountValue: Number(imported.accountValue ?? account?.balance ?? account?.equity ?? 0),
    riskPercent: 0,
    entryPrice: Number(imported.entryPrice ?? 0),
    stopPrice: Number(imported.stopPrice ?? 0),
    targetPrice: Number(imported.targetPrice ?? 0),
    exitPrice: Number(imported.exitPrice ?? 0),
    quantity: Number(imported.quantity ?? 0),
    fees: Number(imported.fees ?? 0),
    brokerPnl: pnl,
    brokerGrossPnl: imported.brokerGrossPnl === undefined ? pnl : Number(imported.brokerGrossPnl),
    brokerCommission: Number(imported.brokerCommission ?? 0),
    brokerSwap: Number(imported.brokerSwap ?? 0),
    brokerFee: Number(imported.brokerFee ?? 0),
    confidence: 3,
    discipline: 3,
    emotion: "차분함",
    grade: "B",
    tags: ["MT5", "XM", imported.symbol.toUpperCase()],
    thesis: "",
    riskPlan: "",
    good: "",
    bad: "",
    lesson: "",
    screenshot: imported.screenshot || undefined,
    screenshotName: imported.screenshotName || undefined,
    screenshotAnnotations: [],
    brokerMeta: {
      accountLogin: account?.login,
      server: account?.server,
      ticket: imported.ticket,
      positionId: imported.positionId,
      order: imported.order,
      magic: imported.magic,
      comment: imported.comment,
      openTime: imported.openTime,
      closeTime: imported.closeTime,
    },
  };

  return trade;
}

function parseReportNumber(value: string | undefined) {
  const cleaned = String(value ?? "")
    .replace(/\u00a0/g, " ")
    .replace(/,/g, "")
    .replace(/[()]/g, "")
    .replace(/[+]/g, "")
    .trim();
  const match = cleaned.match(/-?\d+(?:\.\d+)?/);
  return match ? Number(match[0]) : 0;
}

function normalizeReportHeader(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function parseMt5ReportDate(value: string | undefined) {
  const text = String(value ?? "").trim();
  const match = text.match(/(\d{4})[.\/-](\d{1,2})[.\/-](\d{1,2})\s+(\d{1,2}):(\d{2})(?::(\d{2}))?/);
  if (!match) return "";
  const [, year, month, day, hour, minute, second = "00"] = match;
  const utcMs = Date.UTC(Number(year), Number(month) - 1, Number(day), Number(hour) - 3, Number(minute), Number(second));
  return new Date(utcMs).toISOString();
}

function parseDelimitedLine(line: string, delimiter: string) {
  const cells: string[] = [];
  let current = "";
  let quoted = false;

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    if (char === '"') {
      if (quoted && line[index + 1] === '"') {
        current += '"';
        index += 1;
      } else {
        quoted = !quoted;
      }
    } else if (char === delimiter && !quoted) {
      cells.push(current.trim());
      current = "";
    } else {
      current += char;
    }
  }

  cells.push(current.trim());
  return cells;
}

function tableRowsFromMt5Report(text: string) {
  if (/<\s*(html|table|tr|td|th)\b/i.test(text)) {
    const document = new DOMParser().parseFromString(text, "text/html");
    return [...document.querySelectorAll("table")].map((table) =>
      [...table.querySelectorAll("tr")]
        .map((row) => [...row.querySelectorAll("th,td")].map((cell) => cell.textContent?.replace(/\s+/g, " ").trim() ?? ""))
        .filter((row) => row.some(Boolean)),
    );
  }

  const delimiter = text.includes("\t") ? "\t" : ",";
  return [text.split(/\r?\n/).map((line) => parseDelimitedLine(line, delimiter)).filter((row) => row.some(Boolean))];
}

function parseMt5Report(text: string, fileName: string, account?: Mt5Account): Mt5ImportedTrade[] {
  if (/\.xlsx$/i.test(fileName) || text.startsWith("PK\u0003\u0004")) {
    throw new Error("xlsx reports are not supported yet. Export MT5 report as HTML/XLS or CSV.");
  }

  const imported: Mt5ImportedTrade[] = [];
  const findHeader = (headers: string[], candidates: string[]) =>
    headers.findIndex((header) => candidates.some((candidate) => header === candidate || header.includes(candidate)));

  tableRowsFromMt5Report(text).forEach((rows) => {
    rows.forEach((rawHeader, headerIndex) => {
      const headers = rawHeader.map(normalizeReportHeader);
      const symbolIndex = findHeader(headers, ["symbol"]);
      const typeIndex = findHeader(headers, ["type"]);
      const profitIndex = findHeader(headers, ["profit"]);
      const positionIndex = findHeader(headers, ["position", "ticket"]);
      if (symbolIndex < 0 || typeIndex < 0 || profitIndex < 0) return;

      const volumeIndex = findHeader(headers, ["volume", "vol"]);
      const stopIndex = findHeader(headers, ["sl", "stoploss"]);
      const targetIndex = findHeader(headers, ["tp", "takeprofit"]);
      const commissionIndex = findHeader(headers, ["commission"]);
      const swapIndex = findHeader(headers, ["swap"]);
      const commentIndex = findHeader(headers, ["comment"]);
      const timeIndexes = headers
        .map((header, index) => ({ header, index }))
        .filter(({ header }) => header === "time" || header.endsWith("time"))
        .map(({ index }) => index);
      const openTimeIndex = findHeader(headers, ["opentime"]);
      const closeTimeIndex = findHeader(headers, ["closetime"]);
      const priceIndexes = headers
        .map((header, index) => ({ header, index }))
        .filter(({ header }) => header === "price" || header.endsWith("price"))
        .map(({ index }) => index);

      rows.slice(headerIndex + 1).forEach((row) => {
        const symbol = String(row[symbolIndex] ?? "").trim().toUpperCase();
        const type = String(row[typeIndex] ?? "").trim().toLowerCase();
        const direction: Direction | null = type.includes("buy") ? "long" : type.includes("sell") ? "short" : null;
        if (!symbol || !direction) return;

        const entryPrice = parseReportNumber(row[priceIndexes[0]]);
        const exitPrice = parseReportNumber(row[priceIndexes[priceIndexes.length - 1]]);
        const quantity = parseReportNumber(row[volumeIndex]);
        const brokerGrossPnl = parseReportNumber(row[profitIndex]);
        const brokerCommission = parseReportNumber(row[commissionIndex]);
        const brokerSwap = parseReportNumber(row[swapIndex]);
        const brokerPnl = brokerGrossPnl + brokerCommission + brokerSwap;
        if (!entryPrice || !exitPrice || !quantity) return;

        const positionId = parseReportNumber(row[positionIndex]);
        const openTime = parseMt5ReportDate(row[openTimeIndex >= 0 ? openTimeIndex : timeIndexes[0]]);
        const closeTime = parseMt5ReportDate(row[closeTimeIndex >= 0 ? closeTimeIndex : timeIndexes[timeIndexes.length - 1]]);
        const accountPart = account?.login ? `mt5:${account.login}` : "mt5-report";
        const fallbackId = `${symbol}:${openTime || "open"}:${closeTime || "close"}:${entryPrice}:${exitPrice}`;

        imported.push({
          externalId: positionId ? `${accountPart}:${Math.trunc(positionId)}` : `mt5-report:${fallbackId}`,
          date: (closeTime || openTime || todayInput()).slice(0, 10),
          symbol,
          direction,
          entryPrice,
          stopPrice: parseReportNumber(row[stopIndex]),
          targetPrice: parseReportNumber(row[targetIndex]),
          exitPrice,
          quantity,
          brokerPnl,
          brokerGrossPnl,
          brokerCommission,
          brokerSwap,
          brokerFee: 0,
          fees: Math.abs(brokerCommission) + Math.abs(brokerSwap),
          currency: account?.currency ?? "USD",
          accountValue: account?.balance ?? account?.equity ?? 0,
          comment: String(row[commentIndex] ?? ""),
          openTime,
          closeTime,
          positionId: positionId ? Math.trunc(positionId) : undefined,
        });
      });
    });
  });

  return imported;
}
function mergeTags(left: string[], right: string[]) {
  return [...new Set([...left, ...right].map((tag) => tag.trim()).filter(Boolean))];
}

function isAutoThesis(value: string) {
  const text = String(value ?? "").trim();
  return !text || autoThesisValues.has(text) || text.startsWith("MT5 comment:");
}

function mergeImportedTrades(current: Trade[], imported: Trade[]) {
  const byExternalId = new Map(current.filter((trade) => trade.externalId).map((trade) => [trade.externalId, trade]));
  const byPositionId = new Map(
    current
      .filter((trade) => trade.brokerMeta?.positionId)
      .map((trade) => [trade.brokerMeta?.positionId, trade] as const),
  );
  const nextById = new Map(current.map((trade) => [trade.id, trade]));

  imported.forEach((incoming) => {
    const existing = (incoming.externalId ? byExternalId.get(incoming.externalId) : undefined) ?? byPositionId.get(incoming.brokerMeta?.positionId);
    const merged: Trade = existing
      ? {
          ...incoming,
          id: existing.id,
          externalId: existing.externalId || incoming.externalId,
          createdAt: existing.createdAt,
          updatedAt: incoming.updatedAt,
          stopPrice: incoming.stopPrice || existing.stopPrice,
          targetPrice: incoming.targetPrice || existing.targetPrice,
          brokerGrossPnl: incoming.brokerGrossPnl ?? existing.brokerGrossPnl,
          brokerCommission: incoming.brokerCommission ?? existing.brokerCommission,
          brokerSwap: incoming.brokerSwap ?? existing.brokerSwap,
          brokerFee: incoming.brokerFee ?? existing.brokerFee,
          confidence: existing.confidence,
          discipline: existing.discipline,
          emotion: brokenEmotionValues.has(existing.emotion) ? incoming.emotion : existing.emotion,
          grade: existing.grade,
          thesis: isAutoThesis(existing.thesis) ? incoming.thesis : existing.thesis,
          riskPlan: existing.riskPlan || incoming.riskPlan,
          good: existing.good || incoming.good,
          bad: existing.bad || incoming.bad,
          lesson: existing.lesson || incoming.lesson,
          screenshot: incoming.screenshot || existing.screenshot,
          screenshotName: incoming.screenshotName || existing.screenshotName,
          screenshotAnnotations: existing.screenshotAnnotations ?? incoming.screenshotAnnotations ?? [],
          tags: mergeTags(incoming.tags, existing.tags),
        }
      : incoming;

    nextById.set(merged.id, merged);
  });

  return [...nextById.values()].sort(compareTradesByTradeTimeDesc);
}

function draftFromMt5Position(position: Mt5Position, account?: Mt5Account): TradeDraft {
  const base = createDraft();

  return {
    ...base,
    date: position.time.slice(0, 10) || todayInput(),
    market: "XM MT5",
    symbol: position.symbol,
    currency: (account?.currency ?? "USD").toUpperCase(),
    direction: position.direction,
    setup: "기타",
    timeframe: "MT5",
    status: "open",
    result: "open",
    accountValue: Number(account?.balance ?? account?.equity ?? base.accountValue),
    riskPercent: 0,
    entryPrice: position.priceOpen,
    stopPrice: position.stopLoss,
    targetPrice: position.takeProfit,
    exitPrice: position.priceCurrent,
    quantity: position.volume,
    brokerPnl: position.profit + position.swap,
    brokerGrossPnl: position.profit,
    brokerCommission: 0,
    brokerSwap: position.swap,
    brokerFee: 0,
    fees: 0,
    source: "mt5",
    externalId: account?.login ? `mt5:${account.login}:${position.ticket}` : `mt5-live:${position.ticket}`,
    brokerMeta: {
      accountLogin: account?.login,
      server: account?.server,
      ticket: position.ticket,
      positionId: position.ticket,
      comment: position.comment,
      openTime: position.time,
    },
    tags: `MT5, XM, ${position.symbol}`,
    thesis: "",
  };
}

type ChartImageEditorProps = {
  image?: string;
  imageName?: string;
  annotations?: ChartAnnotation[];
  onImageUpload: (event: ChangeEvent<HTMLInputElement>) => void;
  onDrop: (event: DragEvent<HTMLElement>) => void;
  onRemoveImage: () => void;
  onAnnotationsChange: (annotations: ChartAnnotation[]) => void;
};

function ChartImageEditor({
  image,
  imageName,
  annotations = [],
  onImageUpload,
  onDrop,
  onRemoveImage,
  onAnnotationsChange,
}: ChartImageEditorProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [tool, setTool] = useState<AnnotationTool>("hline");
  const [color, setColor] = useState("#f59e0b");
  const [colorPresets, setColorPresets] = useState<string[]>(loadAnnotationColorPresets);
  const [colorPickerOpen, setColorPickerOpen] = useState(false);
  const [strokeWidth, setStrokeWidth] = useState(3);
  const [text, setText] = useState("메모");
  const [draftAnnotation, setDraftAnnotation] = useState<ChartAnnotation | null>(null);
  const [tapStartAnnotation, setTapStartAnnotation] = useState<ChartAnnotation | null>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (!containerRef.current) return;
    const resize = () => {
      const rect = containerRef.current?.getBoundingClientRect();
      if (!rect) return;
      setSize({ width: rect.width, height: rect.height });
    };
    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [image]);

  useEffect(() => {
    safeLocalStorageSet(ANNOTATION_COLOR_PRESETS_KEY, colorPresets);
  }, [colorPresets]);

  useEffect(() => {
    setDraftAnnotation(null);
    setTapStartAnnotation(null);
  }, [tool]);

  const pointFromEvent = (event: PointerEvent<SVGSVGElement>) => {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect || rect.width <= 0 || rect.height <= 0) return { x: 0, y: 0 };
    return {
      x: Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width)),
      y: Math.max(0, Math.min(1, (event.clientY - rect.top) / rect.height)),
    };
  };

  const addAnnotation = (annotation: ChartAnnotation) => {
    onAnnotationsChange([...annotations, annotation]);
  };

  const usesTwoTapShape = (event: PointerEvent<SVGSVGElement>) => {
    return event.pointerType === "touch" && (tool === "rectangle" || tool === "circle");
  };

  const makeAnnotation = (point: { x: number; y: number }): ChartAnnotation => {
    if (tool === "hline") {
      return { id: uid(), type: tool, color, strokeWidth, x1: 0, y1: point.y, x2: 1, y2: point.y };
    }
    if (tool === "vline") {
      return { id: uid(), type: tool, color, strokeWidth, x1: point.x, y1: 0, x2: point.x, y2: 1 };
    }
    return { id: uid(), type: tool, color, strokeWidth, x1: point.x, y1: point.y, x2: point.x, y2: point.y, text };
  };

  const handlePointerDown = (event: PointerEvent<SVGSVGElement>) => {
    if (!image) return;
    const point = pointFromEvent(event);
    if (usesTwoTapShape(event)) {
      event.preventDefault();
      if (tapStartAnnotation) {
        const finished = { ...tapStartAnnotation, x2: point.x, y2: point.y };
        setDraftAnnotation(null);
        setTapStartAnnotation(null);
        const moved = Math.abs(finished.x2 - finished.x1) + Math.abs(finished.y2 - finished.y1);
        if (moved > 0.01) addAnnotation(finished);
        return;
      }
      const next = makeAnnotation(point);
      setTapStartAnnotation(next);
      setDraftAnnotation(next);
      return;
    }
    event.currentTarget.setPointerCapture(event.pointerId);
    const next = makeAnnotation(point);
    if (tool === "hline" || tool === "vline") {
      addAnnotation(next);
      return;
    }
    if (tool === "text") {
      addAnnotation({ ...next, text: text.trim() || "메모" });
      return;
    }
    setDraftAnnotation(next);
  };

  const handlePointerMove = (event: PointerEvent<SVGSVGElement>) => {
    if (usesTwoTapShape(event) && tapStartAnnotation) {
      const point = pointFromEvent(event);
      setDraftAnnotation({ ...tapStartAnnotation, x2: point.x, y2: point.y });
      return;
    }
    if (!draftAnnotation) return;
    const point = pointFromEvent(event);
    setDraftAnnotation({ ...draftAnnotation, x2: point.x, y2: point.y });
  };

  const handlePointerUp = (event: PointerEvent<SVGSVGElement>) => {
    if (usesTwoTapShape(event) && tapStartAnnotation) return;
    if (!draftAnnotation) return;
    const point = pointFromEvent(event);
    const finished = { ...draftAnnotation, x2: point.x, y2: point.y };
    setDraftAnnotation(null);
    const moved = Math.abs(finished.x2 - finished.x1) + Math.abs(finished.y2 - finished.y1);
    if (moved > 0.01) addAnnotation(finished);
  };

  const undo = () => onAnnotationsChange(annotations.slice(0, -1));
  const clear = () => onAnnotationsChange([]);
  const saveColorPreset = (index: number) => {
    setColorPresets((current) => current.map((preset, presetIndex) => (presetIndex === index ? color : preset)));
  };
  const rendered = draftAnnotation ? [...annotations, draftAnnotation] : annotations;

  const renderAnnotation = (annotation: ChartAnnotation) => {
    const width = size.width || 100;
    const height = size.height || 100;
    const x1 = annotation.x1 * width;
    const y1 = annotation.y1 * height;
    const x2 = annotation.x2 * width;
    const y2 = annotation.y2 * height;
    const common = {
      stroke: annotation.color,
      strokeWidth: annotation.strokeWidth,
      vectorEffect: "non-scaling-stroke" as const,
      strokeLinecap: "round" as const,
      strokeLinejoin: "round" as const,
      fill: "none",
    };

    if (annotation.type === "hline" || annotation.type === "vline" || annotation.type === "segment") {
      return <line key={annotation.id} x1={x1} y1={y1} x2={x2} y2={y2} {...common} />;
    }
    if (annotation.type === "rectangle") {
      return (
        <rect
          key={annotation.id}
          x={Math.min(x1, x2)}
          y={Math.min(y1, y2)}
          width={Math.abs(x2 - x1)}
          height={Math.abs(y2 - y1)}
          {...common}
        />
      );
    }
    if (annotation.type === "circle") {
      return <circle key={annotation.id} cx={x1} cy={y1} r={Math.hypot(x2 - x1, y2 - y1)} {...common} />;
    }
    return (
      <text
        key={annotation.id}
        x={x1}
        y={y1}
        textAnchor="middle"
        dominantBaseline="central"
        stroke="#071015"
        strokeWidth={Math.max(2, annotation.strokeWidth)}
        paintOrder="stroke"
        fill={annotation.color}
        fontSize={Math.max(13, annotation.strokeWidth * 5)}
        fontWeight={800}
      >
        {annotation.text || "메모"}
      </text>
    );
  };

  if (!image) {
    return (
      <label className="dropzone" onDragOver={(event) => event.preventDefault()} onDrop={onDrop}>
        <input className="sr-only" type="file" accept="image/*" onChange={onImageUpload} />
        <div className="dropzone-empty">
          <ImagePlus size={24} />
          <span>차트 이미지</span>
        </div>
      </label>
    );
  }

  return (
    <div className="annotation-editor" onDragOver={(event) => event.preventDefault()} onDrop={onDrop}>
      <div className="annotation-toolbar">
        <div className="annotation-tools" role="group" aria-label="차트 이미지 주석 도구">
          {annotationTools.map((item) => (
            <button
              key={item.tool}
              type="button"
              className={tool === item.tool ? "active" : ""}
              onClick={() => setTool(item.tool)}
              title={item.label}
              aria-label={item.label}
            >
              {item.icon}
            </button>
          ))}
        </div>
        <div className="color-preset-group" aria-label="색상 프리셋">
          {colorPresets.map((preset, index) => (
            <button
              key={`${preset}-${index}`}
              type="button"
              className={preset.toLowerCase() === color.toLowerCase() ? "active" : ""}
              style={{ backgroundColor: preset }}
              onClick={() => setColor(preset)}
              title={`색상 프리셋 ${index + 1}`}
              aria-label={`색상 프리셋 ${index + 1}`}
            />
          ))}
        </div>
        <div className="color-picker-wrap">
          <button
            type="button"
            className="color-control"
            style={{ backgroundColor: color }}
            onClick={() => setColorPickerOpen((current) => !current)}
            title="색상 변경"
            aria-label="색상 변경"
          />
          {colorPickerOpen ? (
            <div className="color-popover">
              <input
                type="color"
                value={color}
                onInput={(event) => setColor(event.currentTarget.value)}
                onChange={(event) => setColor(event.target.value)}
                aria-label="현재 색상"
              />
              <div className="preset-save-row">
                {[0, 1, 2, 3, 4].map((index) => (
                  <button type="button" key={index} onClick={() => saveColorPreset(index)} title={`${index + 1}번 프리셋에 저장`}>
                    {index + 1}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
        </div>
        <label className="thickness-control" title="두께">
          <input
            type="range"
            min="1"
            max="12"
            value={strokeWidth}
            onChange={(event) => setStrokeWidth(toNumber(event.target.value))}
          />
          <span>{strokeWidth}</span>
        </label>
        <input className="annotation-text-input" value={text} onChange={(event) => setText(event.target.value)} placeholder="텍스트" />
        <button type="button" className="icon-button" onClick={undo} disabled={!annotations.length} aria-label="마지막 주석 취소">
          <Undo2 size={16} />
        </button>
        <button type="button" className="icon-button" onClick={clear} disabled={!annotations.length} aria-label="주석 전체 삭제">
          <Trash2 size={16} />
        </button>
        <label className="annotation-upload">
          <Upload size={16} />
          교체
          <input className="sr-only" type="file" accept="image/*" onChange={onImageUpload} />
        </label>
      </div>

      <div className="annotation-canvas" ref={containerRef}>
        <img src={image} alt="차트 스크린샷" />
        <svg
          ref={svgRef}
          viewBox={`0 0 ${size.width || 100} ${size.height || 100}`}
          className="annotation-layer"
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={() => {
            setDraftAnnotation(null);
            setTapStartAnnotation(null);
          }}
        >
          {rendered.map(renderAnnotation)}
        </svg>
        <button type="button" className="remove-image" onClick={onRemoveImage} aria-label="이미지 제거">
          <X size={16} />
        </button>
      </div>

      <div className="annotation-footer">
        <span>{imageName || "차트 이미지"}</span>
        <b>{annotations.length}개 주석</b>
      </div>
    </div>
  );
}

function MetricCard({
  icon,
  label,
  value,
  detail,
  tone = "neutral",
}: {
  icon: ReactNode;
  label: string;
  value: string;
  detail: string;
  tone?: "neutral" | "good" | "bad" | "warn";
}) {
  return (
    <section className={`metric-card ${tone}`}>
      <div className="metric-icon">{icon}</div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
    </section>
  );
}

function TradingChart({
  symbol,
  timeframe,
  bars,
  latestTick,
  positions,
  symbolInfo,
  stopLoss,
  takeProfit,
  loading,
  error,
  onSymbolChange,
  onTimeframeChange,
  onStopLossChange,
  onTakeProfitChange,
}: {
  symbol: string;
  timeframe: ChartTimeframe;
  bars: ChartBar[];
  latestTick?: Mt5Tick;
  positions: Mt5Position[];
  symbolInfo?: Mt5SymbolInfo;
  stopLoss: number;
  takeProfit: number;
  loading: boolean;
  error: string;
  onSymbolChange: (symbol: string) => void;
  onTimeframeChange: (timeframe: ChartTimeframe) => void;
  onStopLossChange: (price: number) => void;
  onTakeProfitChange: (price: number) => void;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const priceLinesRef = useRef<Record<string, IPriceLine | null>>({});
  const draggingRef = useRef<"sl" | "tp" | null>(null);
  const [dragging, setDragging] = useState<"sl" | "tp" | null>(null);
  const [hoverLine, setHoverLine] = useState<"sl" | "tp" | null>(null);
  const activePosition = positions.find((position) => normalizeSymbol(position.symbol) === normalizeSymbol(symbol));
  const latestPrice = latestTick?.ask || latestTick?.bid || (bars.length ? bars[bars.length - 1].close : 0);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "#111720" },
        textColor: "#aeb9c8",
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.045)" },
        horzLines: { color: "rgba(255,255,255,0.045)" },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: "rgba(255,255,255,0.1)",
      },
      timeScale: {
        borderColor: "rgba(255,255,255,0.1)",
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#fb7185",
      borderUpColor: "#22c55e",
      borderDownColor: "#fb7185",
      wickUpColor: "#22c55e",
      wickDownColor: "#fb7185",
      priceLineVisible: false,
    });

    chartRef.current = chart;
    seriesRef.current = series;

    return () => {
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
      priceLinesRef.current = {};
    };
  }, []);

  useEffect(() => {
    const series = seriesRef.current;
    if (!series) return;

    const candles: CandlestickData<UTCTimestamp>[] = bars.map((bar) => ({
      time: bar.time as UTCTimestamp,
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
    }));

    series.setData(candles);
    if (candles.length) {
      chartRef.current?.timeScale().fitContent();
    }
  }, [bars]);

  useEffect(() => {
    const series = seriesRef.current;
    if (!series) return;

    Object.values(priceLinesRef.current).forEach((line) => {
      if (line) series.removePriceLine(line);
    });

    const nextLines: Record<string, IPriceLine | null> = {};
    const addLine = (
      key: string,
      price: number,
      color: string,
      title: string,
      style: LineStyle = LineStyle.Solid,
      width: 1 | 2 | 3 | 4 = 1,
    ) => {
      if (!Number.isFinite(price) || price <= 0) {
        nextLines[key] = null;
        return;
      }
      nextLines[key] = series.createPriceLine({
        price,
        color,
        lineWidth: width,
        lineStyle: style,
        axisLabelVisible: true,
        title,
      });
    };

    addLine("bid", latestTick?.bid ?? 0, "#60a5fa", "Bid", LineStyle.Dotted);
    addLine("ask", latestTick?.ask ?? 0, "#f59e0b", "Ask", LineStyle.Dotted);
    addLine("entry", activePosition?.priceOpen ?? 0, "#edf2f7", "Entry", LineStyle.Dashed);
    addLine("sl", stopLoss, "#fb7185", "SL drag", LineStyle.Solid, 2);
    addLine("tp", takeProfit, "#22c55e", "TP drag", LineStyle.Solid, 2);

    priceLinesRef.current = nextLines;
  }, [activePosition?.priceOpen, latestTick?.ask, latestTick?.bid, stopLoss, takeProfit]);

  const targetFromY = (y: number) => {
    const series = seriesRef.current;
    if (!series) return null;
    const checks: Array<["sl" | "tp", number]> = [
      ["sl", stopLoss],
      ["tp", takeProfit],
    ];

    for (const [target, price] of checks) {
      if (!Number.isFinite(price) || price <= 0) continue;
      const coordinate = series.priceToCoordinate(price);
      if (coordinate !== null && Math.abs(coordinate - y) <= 12) return target;
    }
    return null;
  };

  const updateDraggedPrice = (event: PointerEvent<HTMLDivElement>) => {
    const target = draggingRef.current;
    const series = seriesRef.current;
    if (!target || !series || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const price = Number(series.coordinateToPrice(event.clientY - rect.top));
    if (!Number.isFinite(price) || price <= 0) return;
    const rounded = roundPrice(price, symbolInfo);
    if (target === "sl") onStopLossChange(rounded);
    if (target === "tp") onTakeProfitChange(rounded);
  };

  const handlePointerDown = (event: PointerEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const target = targetFromY(event.clientY - rect.top);
    if (!target) return;
    event.preventDefault();
    draggingRef.current = target;
    setDragging(target);
    event.currentTarget.setPointerCapture(event.pointerId);
    updateDraggedPrice(event);
  };

  const handlePointerMove = (event: PointerEvent<HTMLDivElement>) => {
    if (draggingRef.current) {
      event.preventDefault();
      updateDraggedPrice(event);
      return;
    }
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    setHoverLine(targetFromY(event.clientY - rect.top));
  };

  const endDrag = (event: PointerEvent<HTMLDivElement>) => {
    if (draggingRef.current) {
      updateDraggedPrice(event);
      draggingRef.current = null;
      setDragging(null);
    }
  };

  return (
    <section className="chart-shell">
      <div className="chart-toolbar">
        <div>
          <span className="eyebrow">MT5 Live Chart</span>
          <h2>{symbol || "Symbol"}</h2>
        </div>
        <div className="chart-controls">
          <label>
            Symbol
            <input value={symbol} onChange={(event) => onSymbolChange(event.target.value)} autoComplete="off" />
          </label>
          <div className="timeframe-tabs" role="group" aria-label="Chart timeframe">
            {chartTimeframes.map((item) => (
              <button
                type="button"
                key={item}
                className={timeframe === item ? "active" : ""}
                onClick={() => onTimeframeChange(item)}
              >
                {item}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div
        className={`chart-container ${dragging || hoverLine ? "line-hover" : ""}`}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
        onPointerLeave={() => {
          if (!draggingRef.current) setHoverLine(null);
        }}
      >
        <div ref={containerRef} className="lw-chart" />
        {!bars.length || error ? (
          <div className="chart-empty">
            <strong>{error ? "MT5 chart unavailable" : "Waiting for bars"}</strong>
            <span>{error || "MT5 브리지에서 캔들 데이터를 기다리는 중입니다."}</span>
          </div>
        ) : null}
        {loading ? <div className="chart-loading">Updating</div> : null}
      </div>

      <div className="chart-status-strip">
        <div>
          <span>Bid</span>
          <strong>{latestTick?.bid ? number.format(latestTick.bid) : "-"}</strong>
        </div>
        <div>
          <span>Ask</span>
          <strong>{latestTick?.ask ? number.format(latestTick.ask) : "-"}</strong>
        </div>
        <div>
          <span>Last</span>
          <strong>{latestPrice ? number.format(latestPrice) : "-"}</strong>
        </div>
        <div>
          <span>Position</span>
          <strong>{activePosition ? `${activePosition.direction} ${number.format(activePosition.volume)} lot` : "-"}</strong>
        </div>
      </div>
    </section>
  );
}

function App() {
  const [trades, setTrades] = useState<Trade[]>(loadTrades);
  const [reviews, setReviews] = useState<Review[]>(loadReviews);
  const [draft, setDraft] = useState<TradeDraft>(createDraft);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [activeReviewDraft, setActiveReviewDraft] = useState<ReviewDraft | null>(null);
  const [expandedReviewId, setExpandedReviewId] = useState<string | null>(null);
  const [expandedFeedbackId, setExpandedFeedbackId] = useState<string | null>(null);
  const [aiFeedbackLoading, setAiFeedbackLoading] = useState(false);
  const [aiFeedbackPreflight, setAiFeedbackPreflight] = useState<AiFeedbackPreflight | null>(null);
  const [aiFeedbackPreflightLoading, setAiFeedbackPreflightLoading] = useState(false);
  const [aiFeedbackBatchLoading, setAiFeedbackBatchLoading] = useState(false);
  const [aiFeedbackBatchJob, setAiFeedbackBatchJob] = useState<AiFeedbackBatchJob | null>(null);
  const [analyticsPeriod, setAnalyticsPeriod] = useState<AnalyticsPeriod>("month");
  const [calendarMonth, setCalendarMonth] = useState(() => monthKey(new Date()));
  const [query, setQuery] = useState("");
  const [resultFilter, setResultFilter] = useState<"all" | TradeResult>("all");
  const [directionFilter, setDirectionFilter] = useState<"all" | Direction>("all");
  const [dateFilter, setDateFilter] = useState<string | null>(null);
  const [dateFilterOpen, setDateFilterOpen] = useState(false);
  const [dateFilterMonth, setDateFilterMonth] = useState(() => monthKey(new Date()));
  const [activeWorkspaceTab, setActiveWorkspaceTab] = useState<WorkspaceTab>("journal");
  const [notice, setNotice] = useState("");
  const [journalSync, setJournalSync] = useState("공용 저장소 연결 확인 중");
  const [journalServerReady, setJournalServerReady] = useState(false);
  const [mt5Days, setMt5Days] = useState(14);
  const [mt5Snapshot, setMt5Snapshot] = useState<Mt5Snapshot | null>(null);
  const [mt5Loading, setMt5Loading] = useState(false);
  const [mt5Notice, setMt5Notice] = useState("MT5 브리지를 실행하면 계좌와 거래를 자동으로 읽습니다.");
  const [eaNotice, setEaNotice] = useState("EA 이벤트 대기 중");
  const [orderDraft, setOrderDraft] = useState<OrderDraft>(createOrderDraft);
  const [orderPreview, setOrderPreview] = useState<OrderPreview | null>(null);
  const [orderLoading, setOrderLoading] = useState(false);
  const [orderArmed, setOrderArmed] = useState(false);
  const [activeSymbol, setActiveSymbol] = useState(() => normalizeSymbol(createOrderDraft().symbol));
  const [activeTimeframe, setActiveTimeframe] = useState<ChartTimeframe>("M5");
  const [chartBars, setChartBars] = useState<ChartBar[]>([]);
  const [latestTick, setLatestTick] = useState<Mt5Tick | undefined>();
  const [chartSymbolInfo, setChartSymbolInfo] = useState<Mt5SymbolInfo | undefined>();
  const [chartLoading, setChartLoading] = useState(false);
  const [chartError, setChartError] = useState("");
  const [liveError, setLiveError] = useState("");
  const [orderNotice, setOrderNotice] = useState("SL 기준 손실이 계좌의 지정 비율을 넘지 않도록 lot을 계산합니다.");
  const importRef = useRef<HTMLInputElement | null>(null);
  const reportImportRef = useRef<HTMLInputElement | null>(null);
  const journalHydratedRef = useRef(false);
  const tradesRef = useRef(trades);
  const reviewsRef = useRef(reviews);

  const refreshAiFeedbackPreflight = useCallback(async () => {
    setAiFeedbackPreflightLoading(true);
    try {
      const response = await fetch(`${MT5_BRIDGE_URL}/ai-feedback/preflight`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = (await response.json()) as AiFeedbackPreflight;
      setAiFeedbackPreflight(payload.ok ? payload : { ok: false, error: payload.error || "복기 자료 상태 확인 실패" });
      return payload;
    } catch (error) {
      const message = error instanceof Error ? error.message : "복기 자료 상태 확인 실패";
      const payload = { ok: false, error: message };
      setAiFeedbackPreflight(payload);
      return payload;
    } finally {
      setAiFeedbackPreflightLoading(false);
    }
  }, []);

  useEffect(() => {
    tradesRef.current = trades;
  }, [trades]);

  useEffect(() => {
    reviewsRef.current = reviews;
  }, [reviews]);

  useEffect(() => {
    if (activeWorkspaceTab === "aiFeedback") {
      void refreshAiFeedbackPreflight();
    }
  }, [activeWorkspaceTab, refreshAiFeedbackPreflight]);

  const saveJournalToServer = useCallback(async (nextTrades: Trade[], nextReviews: Review[], label = "공용 저장소 저장됨") => {
    const response = await fetch(`${MT5_BRIDGE_URL}/journal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trades: nextTrades, reviews: nextReviews }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = (await response.json()) as JournalResponse;
    if (!payload.ok) throw new Error(payload.error || "공용 저장소 저장 실패");
    setJournalServerReady(true);
    setJournalSync(`${label} ${new Date().toLocaleTimeString()}`);
    return payload;
  }, []);

  const saveJournalRecordToServer = useCallback(
    async (kind: "trade" | "review", key: string, payload: Trade | Review, label = "공용 저장소 저장됨") => {
      const path = kind === "trade" ? "trades" : "reviews";
      const response = await fetch(`${MT5_BRIDGE_URL}/${path}/${encodeURIComponent(key)}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const result = (await response.json()) as JournalWriteResponse;
      if (!result.ok) throw new Error(result.error || "공용 저장소 저장 실패");
      setJournalServerReady(true);
      setJournalSync(`${label} ${new Date().toLocaleTimeString()}`);
      return result;
    },
    [],
  );

  const deleteJournalRecordFromServer = useCallback(async (kind: "trade" | "review", key: string, label = "공용 저장소 삭제됨") => {
    const path = kind === "trade" ? "trades" : "reviews";
    const response = await fetch(`${MT5_BRIDGE_URL}/${path}/${encodeURIComponent(key)}`, { method: "DELETE" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const result = (await response.json()) as JournalWriteResponse;
    if (!result.ok) throw new Error(result.error || "공용 저장소 삭제 실패");
    setJournalServerReady(true);
    setJournalSync(`${label} ${new Date().toLocaleTimeString()}`);
    return result;
  }, []);

  const handleJournalRecordSaveFailure = useCallback((kind: "trade" | "review", key: string, payload: Trade | Review, error: unknown) => {
    queuePendingJournalChange(kind, key, payload);
    setJournalServerReady(false);
    const prefix = kind === "trade" ? "매매일지" : "결산";
    setJournalSync(error instanceof Error ? `${prefix} 공용 저장 대기: ${error.message}` : `${prefix} 공용 저장 대기`);
  }, []);

  const flushPendingJournalChanges = useCallback(async () => {
    const pending = loadPendingJournalChanges();
    if (!pending.length) return 0;

    const remaining: PendingJournalChange[] = [];
    for (const change of pending) {
      try {
        await saveJournalRecordToServer(change.kind, change.key, change.payload, "미전송 저장 전송됨");
      } catch {
        remaining.push({ ...change, attempts: change.attempts + 1 });
      }
    }

    storePendingJournalChanges(remaining);
    if (remaining.length) {
      setJournalServerReady(false);
      setJournalSync(`미전송 저장 ${remaining.length}건 대기 중`);
    } else {
      setJournalServerReady(true);
      setJournalSync(`미전송 저장 ${pending.length}건 전송 완료 ${new Date().toLocaleTimeString()}`);
    }
    return pending.length - remaining.length;
  }, [saveJournalRecordToServer]);

  const pullJournalFromServer = useCallback(async (mode: "initial" | "refresh" = "refresh") => {
    const response = await fetch(`${MT5_BRIDGE_URL}/journal`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = (await response.json()) as JournalResponse;
    if (!payload.ok) throw new Error(payload.error || "공용 저장소를 읽지 못했습니다.");

    const serverTrades = normalizeStoredTrades(payload.trades);
    const serverReviews = Array.isArray(payload.reviews) ? payload.reviews.map((review) => normalizeReview(review)) : [];
    const mergedTrades = serverTrades.length ? mergeImportedTrades(tradesRef.current, serverTrades) : tradesRef.current;
    const mergedReviews = mergeReviews(reviewsRef.current, serverReviews);

    if (serverTrades.length > 0) {
      setTrades(mergedTrades);
    }
    setReviews((current) => mergeReviews(current, mergedReviews));
    setJournalServerReady(true);
    journalHydratedRef.current = true;
    setJournalSync(
      mode === "initial"
        ? `공용 저장소 연결됨: ${serverTrades.length || tradesRef.current.length}개 기록 · 결산 ${mergedReviews.length}개`
        : `공용 저장소 새로고침 ${new Date().toLocaleTimeString()}`,
    );

    if (mergedReviews.length !== serverReviews.length) {
      await saveJournalToServer(mergedTrades, mergedReviews, "공용 저장소 결산 병합됨");
    }

    return { serverTrades, mergedTrades, mergedReviews };
  }, [saveJournalToServer]);

  useEffect(() => {
    safeLocalStorageSet(REVIEWS_STORAGE_KEY, reviews.map(reviewForLocalCache));
  }, [reviews]);

  useEffect(() => {
    const cachedTrades = trades.map(tradeForLocalCache);
    const saved = safeLocalStorageSet(STORAGE_KEY, cachedTrades);
    if (!saved) {
      safeLocalStorageSet(STORAGE_KEY, cachedTrades.slice(0, 20));
    }
  }, [trades]);

  useEffect(() => {
    let cancelled = false;

    const hydrateJournal = async () => {
      try {
        if (cancelled) return;
        const { serverTrades, mergedReviews } = await pullJournalFromServer("initial");
        if (!serverTrades.length && (tradesRef.current.length > 0 || reviewsRef.current.length > 0)) {
          await saveJournalToServer(tradesRef.current, mergedReviews.length ? mergedReviews : reviewsRef.current, "브라우저 기록을 공용 저장소로 올림");
        }
      } catch (error) {
        if (!cancelled) {
          journalHydratedRef.current = true;
          setJournalServerReady(false);
          setJournalSync(error instanceof Error ? `로컬 저장 모드: ${error.message}` : "로컬 저장 모드");
        }
      }
    };

    void hydrateJournal();

    return () => {
      cancelled = true;
    };
  }, [pullJournalFromServer, saveJournalToServer]);

  useEffect(() => {
    if (!journalServerReady) return;
    const interval = window.setInterval(() => {
      pullJournalFromServer("refresh").catch((error) => {
        setJournalServerReady(false);
        setJournalSync(error instanceof Error ? `공용 저장소 새로고침 실패: ${error.message}` : "공용 저장소 새로고침 실패");
      });
    }, 15_000);
    return () => window.clearInterval(interval);
  }, [journalServerReady, pullJournalFromServer]);

  useEffect(() => {
    const interval = window.setInterval(() => {
      if (!loadPendingJournalChanges().length) return;
      flushPendingJournalChanges().catch((error) => {
        setJournalServerReady(false);
        setJournalSync(error instanceof Error ? `미전송 저장 재시도 실패: ${error.message}` : "미전송 저장 재시도 실패");
      });
    }, 10_000);
    void flushPendingJournalChanges().catch(() => undefined);
    return () => window.clearInterval(interval);
  }, [flushPendingJournalChanges]);

  const draftDerived = useMemo(() => computeTrade(draft), [draft]);
  const displayCurrency = mt5Snapshot?.account?.currency ?? draft.currency ?? trades[0]?.currency ?? "USD";
  const isMt5Draft = draft.source === "mt5" || Boolean(draft.externalId || draft.brokerMeta?.positionId || draft.brokerMeta?.ticket);

  const sortedTrades = useMemo(
    () => [...trades].sort(compareTradesByTradeTimeDesc),
    [trades],
  );

  const tradeDateSet = useMemo(() => new Set(trades.map((trade) => trade.date).filter(Boolean)), [trades]);

  const dateFilterCalendar = useMemo(() => {
    const [year, month] = dateFilterMonth.split("-").map(Number);
    const first = new Date(year || new Date().getFullYear(), (month || 1) - 1, 1);
    const start = startOfWeek(first);
    return Array.from({ length: 42 }, (_, index) => {
      const date = addDays(start, index);
      const dateKey = localDateInput(date);
      return {
        date: dateKey,
        label: date.getDate(),
        inMonth: date.getMonth() === first.getMonth(),
        hasTrades: tradeDateSet.has(dateKey),
      };
    });
  }, [dateFilterMonth, tradeDateSet]);

  const shiftDateFilterMonth = (offset: number) => {
    const [year, month] = dateFilterMonth.split("-").map(Number);
    const next = new Date(year || new Date().getFullYear(), (month || 1) - 1 + offset, 1);
    setDateFilterMonth(monthKey(next));
  };

  const filteredTrades = useMemo(() => {
    const lowered = query.trim().toLowerCase();

    return sortedTrades.filter((trade) => {
      const matchesQuery = !lowered || trade.symbol.toLowerCase().includes(lowered);
      const matchesResult = resultFilter === "all" || trade.result === resultFilter;
      const matchesDirection = directionFilter === "all" || trade.direction === directionFilter;
      const matchesDate = !dateFilter || trade.date === dateFilter;
      return matchesQuery && matchesResult && matchesDirection && matchesDate;
    });
  }, [dateFilter, directionFilter, query, resultFilter, sortedTrades]);

  const aiFeedbackTrades = useMemo(
    () => sortedTrades.filter((trade) => Boolean(trade.aiFeedback)),
    [sortedTrades],
  );

  const summary = useMemo(() => {
    const closed = trades.filter((trade) => trade.status === "closed");
    const pnl = closed.reduce((sum, trade) => sum + computeTrade(trade).pnl, 0);
    const wins = closed.filter((trade) => trade.result === "win").length;
    const winRate = closed.length ? (wins / closed.length) * 100 : 0;
    const rewardRiskTrades = closed.map((trade) => computeTrade(trade).rewardRisk).filter((value) => value > 0);
    const avgRewardRisk = rewardRiskTrades.length ? rewardRiskTrades.reduce((sum, value) => sum + value, 0) / rewardRiskTrades.length : 0;
    const avgDiscipline = trades.length ? trades.reduce((sum, trade) => sum + trade.discipline, 0) / trades.length : 0;

    return { closed: closed.length, pnl, wins, winRate, avgRewardRisk, avgDiscipline };
  }, [trades]);

  const analyticsRange = useMemo(() => {
    const today = parseDateInput(todayInput());
    if (analyticsPeriod === "today") {
      const date = localDateInput(today);
      return { startDate: date, endDate: date };
    }
    if (analyticsPeriod === "week") {
      return { startDate: localDateInput(addDays(today, -6)), endDate: localDateInput(today) };
    }
    if (analyticsPeriod === "month") {
      return { startDate: localDateInput(addDays(today, -29)), endDate: localDateInput(today) };
    }
    const dates = trades.filter((trade) => trade.status === "closed").map(tradeCloseDate).sort();
    return { startDate: dates[0] || localDateInput(today), endDate: dates[dates.length - 1] || localDateInput(today) };
  }, [analyticsPeriod, trades]);

  const analyticsTrades = useMemo(
    () => tradesInRange(trades, analyticsRange.startDate, analyticsRange.endDate),
    [analyticsRange.endDate, analyticsRange.startDate, trades],
  );

  const analyticsSummary = useMemo(() => summarizeTrades(analyticsTrades), [analyticsTrades]);
  const todayDate = todayInput();

  const analyticsEquityCurve = useMemo(() => {
    return buildAnalyticsEquityCurve(analyticsTrades, analyticsRange.startDate, analyticsRange.endDate, analyticsPeriod);
  }, [analyticsPeriod, analyticsRange.endDate, analyticsRange.startDate, analyticsTrades]);

  const analyticsMetricChart = useMemo(
    () => [
      { label: "승률", value: Math.round(analyticsSummary.winRate * 10) / 10 },
      { label: "평균 손익비", value: Math.round(analyticsSummary.avgRewardRisk * 100) / 100 },
      { label: "거래 수", value: analyticsSummary.trades },
    ],
    [analyticsSummary],
  );

  const reviewByPeriod = useMemo(() => {
    const map = new Map<string, Review>();
    reviews.forEach((review) => map.set(review.periodKey, review));
    return map;
  }, [reviews]);

  const calendarData = useMemo(() => {
    const [year, month] = calendarMonth.split("-").map(Number);
    const first = new Date(year, (month || 1) - 1, 1);
    const last = new Date(year, month || 1, 0);
    const gridStart = startOfWeek(first);
    const gridEnd = endOfWeek(last);
    const days = [];
    for (let cursor = new Date(gridStart); cursor <= gridEnd; cursor = addDays(cursor, 1)) {
      const date = localDateInput(cursor);
      const dayTrades = tradesInRange(trades, date, date);
      days.push({
        date,
        day: cursor.getDate(),
        inMonth: cursor.getMonth() === first.getMonth(),
        trades: dayTrades,
        summary: summarizeTrades(dayTrades),
      });
    }
    const weeks = [];
    for (let index = 0; index < days.length; index += 7) {
      const weekDays = days.slice(index, index + 7);
      const startDate = weekDays[0].date;
      const endDate = weekDays[6].date;
      const weekTrades = tradesInRange(trades, startDate, endDate);
      weeks.push({ startDate, endDate, days: weekDays, summary: summarizeTrades(weekTrades), trades: weekTrades });
    }
    const monthStart = localDateInput(first);
    const monthEnd = localDateInput(last);
    const monthTrades = tradesInRange(trades, monthStart, monthEnd);
    return {
      year,
      month,
      monthStart,
      monthEnd,
      weeks,
      monthSummary: summarizeTrades(monthTrades),
      monthTrades,
    };
  }, [calendarMonth, trades]);

  const shiftCalendarMonth = (offset: number) => {
    const [year, month] = calendarMonth.split("-").map(Number);
    const next = new Date(year || new Date().getFullYear(), (month || 1) - 1 + offset, 1);
    setCalendarMonth(monthKey(next));
  };

  const equityCurve = useMemo(() => {
    let cumulative = 0;
    return [...trades]
      .filter((trade) => trade.status === "closed")
      .sort((a, b) => a.date.localeCompare(b.date))
      .map((trade) => {
        cumulative += computeTrade(trade).pnl;
        return {
          date: trade.date.slice(5),
          pnl: Math.round(cumulative),
        };
      });
  }, [trades]);

  const setupChart = useMemo(() => {
    const map = new Map<string, { setup: string; trades: number; pnl: number }>();
    trades.forEach((trade) => {
      const key = trade.setup && trade.setup !== "기타" ? trade.setup : "미분류";
      const current = map.get(key) ?? { setup: key, trades: 0, pnl: 0 };
      current.trades += 1;
      current.pnl += computeTrade(trade).pnl;
      map.set(key, current);
    });

    return [...map.values()].sort((a, b) => b.trades - a.trades).slice(0, 6);
  }, [trades]);

  const tagCloud = useMemo(() => {
    const map = new Map<string, number>();
    trades.forEach((trade) => {
      trade.tags.forEach((tag) => map.set(tag, (map.get(tag) ?? 0) + 1));
    });
    return [...map.entries()].sort((a, b) => b[1] - a[1]).slice(0, 12);
  }, [trades]);

  const setDraftField = <K extends keyof TradeDraft>(key: K, value: TradeDraft[K]) => {
    setDraft((current) => ({ ...current, [key]: value }));
  };

  const resetDraft = () => {
    setDraft((current) => ({
      ...createDraft(),
      accountValue: current.accountValue,
      riskPercent: current.riskPercent,
    }));
    setEditingId(null);
    setActiveWorkspaceTab("journal");
  };

  const saveDraftRecord = () => {
    if (!draft.symbol.trim()) {
      setNotice("종목을 입력해야 저장됩니다.");
      return false;
    }

    const existing = trades.find((trade) => trade.id === editingId);
    const trade = buildTradeFromDraft(draft, existing);
    setTrades((current) => {
      if (!editingId) return [trade, ...current];
      return current.map((item) => (item.id === editingId ? trade : item));
    });
    setEditingId(trade.id);
    setDraft(draftFromTrade(trade));
    setNotice(editingId ? "기록을 수정했습니다." : "새 기록을 저장했습니다.");
    void saveJournalRecordToServer("trade", trade.id, trade, editingId ? "매매일지 수정 저장됨" : "매매일지 저장됨").catch((error) => {
      handleJournalRecordSaveFailure("trade", trade.id, trade, error);
    });
    return true;
  };

  const handleSave = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    saveDraftRecord();
  };

  const deleteTrade = (id: string) => {
    setTrades((current) => current.filter((trade) => trade.id !== id));
    if (editingId === id) resetDraft();
    setNotice("기록을 삭제했습니다.");
    void deleteJournalRecordFromServer("trade", id, "매매 기록 삭제됨").catch((error) => {
      setJournalServerReady(false);
      setJournalSync(error instanceof Error ? `매매 기록 공용 삭제 실패: ${error.message}` : "매매 기록 공용 삭제 실패");
    });
  };

  const openReview = (type: ReviewType, startDate: string, endDate: string) => {
    const periodKey = reviewPeriodKey(type, startDate, endDate);
    const existing = reviewByPeriod.get(periodKey);
    const periodTrades = tradesInRange(trades, startDate, endDate);
    if (existing) {
      setActiveReviewDraft({
        type: existing.type,
        periodKey: existing.periodKey,
        title: existing.title,
        startDate: existing.startDate,
        endDate: existing.endDate,
        completed: existing.completed,
        marketSummary: existing.marketSummary,
        good: existing.good,
        bad: existing.bad,
        lesson: existing.lesson,
        nextPlan: existing.nextPlan,
        score: existing.score,
      });
    } else {
      setActiveReviewDraft(createReviewDraft(type, startDate, endDate, periodTrades, displayCurrency));
    }
  };

  const setReviewDraftField = <K extends keyof ReviewDraft>(key: K, value: ReviewDraft[K]) => {
    setActiveReviewDraft((current) => (current ? { ...current, [key]: value } : current));
  };

  const saveReview = (completed = false) => {
    if (!activeReviewDraft) return;
    const now = new Date().toISOString();
    const existing = reviews.find((review) => review.periodKey === activeReviewDraft.periodKey);
    const next: Review = {
      ...activeReviewDraft,
      id: existing?.id || uid(),
      completed: completed || activeReviewDraft.completed,
      createdAt: existing?.createdAt || now,
      updatedAt: now,
    };
    const nextReviews = [next, ...reviews.filter((review) => review.periodKey !== next.periodKey)].sort((a, b) => b.startDate.localeCompare(a.startDate));
    setReviews(nextReviews);
    setActiveReviewDraft({ ...activeReviewDraft, completed: next.completed });
    setNotice(next.completed ? "결산을 완료했습니다." : "결산을 저장했습니다.");
    saveJournalRecordToServer("review", next.periodKey, next, next.completed ? "결산 완료 저장됨" : "결산 저장됨").catch((error) => {
      handleJournalRecordSaveFailure("review", next.periodKey, next, error);
    });
  };

  const deleteReview = (id: string) => {
    const review = reviews.find((item) => item.id === id);
    setReviews((current) => current.filter((review) => review.id !== id));
    if (expandedReviewId === id) setExpandedReviewId(null);
    setNotice("결산을 삭제했습니다.");
    void deleteJournalRecordFromServer("review", review?.periodKey || id, "결산 삭제됨").catch((error) => {
      setJournalServerReady(false);
      setJournalSync(error instanceof Error ? `결산 공용 삭제 실패: ${error.message}` : "결산 공용 삭제 실패");
    });
  };

  const generateFirstLossFeedback = async () => {
    setAiFeedbackLoading(true);
    setNotice("첫 손실 거래를 다중 타임프레임 기준으로 복기 중입니다.");
    try {
      await refreshAiFeedbackPreflight();
      const response = await fetch(`${MT5_BRIDGE_URL}/ai-feedback/first-loss`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = (await response.json()) as AiFeedbackResponse;
      if (!payload.ok) throw new Error(payload.error || "복기 자료 생성 실패");
      if (payload.trade) {
        const updatedTrade = normalizeStoredTrades([payload.trade])[0];
        const nextTrades = updatedTrade
          ? [
              updatedTrade,
              ...tradesRef.current.filter((trade) => trade.id !== updatedTrade.id),
            ].sort(compareTradesByTradeTimeDesc)
          : tradesRef.current;
        setTrades(nextTrades);
        tradesRef.current = nextTrades;
      } else {
        await pullJournalFromServer("refresh");
      }
      setActiveWorkspaceTab("aiFeedback");
      setExpandedFeedbackId(payload.tradeId || null);
      setNotice(payload.usedBars ? "MT5 bars 기반 복기 자료를 생성했습니다." : "저장된 차트 이미지 기반 복기 자료를 생성했습니다.");
      void refreshAiFeedbackPreflight();
    } catch (error) {
      setNotice(error instanceof Error ? `복기 자료 생성 실패: ${error.message}` : "복기 자료 생성 실패");
    } finally {
      setAiFeedbackLoading(false);
    }
  };

  const generateMissingFeedbackBatch = async () => {
    setAiFeedbackBatchLoading(true);
    setNotice("복기 자료가 없는 거래의 MTF 근거 보드를 생성 중입니다.");
    try {
      const response = await fetch(`${MT5_BRIDGE_URL}/ai-feedback/batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: "missing", overwrite: false }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = (await response.json()) as AiFeedbackBatchResponse;
      if (!payload.ok || !payload.jobId) throw new Error(payload.error || "복기 자료 일괄 생성 실패");
      setActiveWorkspaceTab("aiFeedback");
      setAiFeedbackBatchJob({
        ok: true,
        jobId: payload.jobId,
        status: payload.total ? "queued" : "completed",
        total: payload.total ?? 0,
        completed: 0,
        failed: 0,
      });

      let finalJob: AiFeedbackBatchJob | null = null;
      for (;;) {
        const statusResponse = await fetch(`${MT5_BRIDGE_URL}/ai-feedback/jobs/${encodeURIComponent(payload.jobId)}`);
        if (!statusResponse.ok) throw new Error(`HTTP ${statusResponse.status}`);
        const job = (await statusResponse.json()) as AiFeedbackBatchJob;
        if (!job.ok) throw new Error(job.error || "복기 자료 작업 상태 확인 실패");
        setAiFeedbackBatchJob(job);
        finalJob = job;
        if (job.status === "completed" || job.status === "failed") break;
        await new Promise((resolve) => window.setTimeout(resolve, 1000));
      }

      await pullJournalFromServer("refresh");
      const completed = finalJob?.completed ?? 0;
      const failed = finalJob?.failed ?? 0;
      setNotice(`복기 자료 일괄 생성 완료: ${completed}건 완료${failed ? ` · 실패 ${failed}건` : ""}`);
      void refreshAiFeedbackPreflight();
    } catch (error) {
      setNotice(error instanceof Error ? `복기 자료 일괄 생성 실패: ${error.message}` : "복기 자료 일괄 생성 실패");
    } finally {
      setAiFeedbackBatchLoading(false);
    }
  };

  const readImageFile = (file: File) => {
    if (!file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.onload = () => {
      setDraft((current) => ({
        ...current,
        screenshot: String(reader.result),
        screenshotName: file.name,
        screenshotAnnotations: [],
      }));
    };
    reader.readAsDataURL(file);
  };

  const handleScreenshotUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) readImageFile(file);
    event.target.value = "";
  };

  const handleDrop = (event: DragEvent<HTMLElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files?.[0];
    if (file) readImageFile(file);
  };

  const handlePaste = (event: ClipboardEvent<HTMLDivElement>) => {
    const image = [...event.clipboardData.items].find((item) => item.type.startsWith("image/"));
    const file = image?.getAsFile();
    if (file) readImageFile(file);
  };

  const exportJson = () => {
    const payload = JSON.stringify({ exportedAt: new Date().toISOString(), trades }, null, 2);
    downloadBlob(payload, `trading-journal-${todayInput()}.json`, "application/json;charset=utf-8");
  };

  const exportCsv = () => {
    downloadBlob(toCsv(trades), `trading-journal-${todayInput()}.csv`, "text/csv;charset=utf-8");
  };

  const importJson = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const parsed = JSON.parse(text);
      const imported = Array.isArray(parsed) ? parsed : parsed.trades;
      if (!Array.isArray(imported)) throw new Error("invalid file");

      const normalized = normalizeStoredTrades(imported);
      setTrades(normalized);
      setEditingId(null);
      setNotice(`${normalized.length}개 기록을 불러왔습니다.`);
      void saveJournalToServer(normalized, reviewsRef.current, "JSON 가져오기 저장됨").catch((error) => {
        setJournalServerReady(false);
        setJournalSync(error instanceof Error ? `JSON 가져오기 공용 저장 실패: ${error.message}` : "JSON 가져오기 공용 저장 실패");
      });
    } catch {
      setNotice("JSON 파일을 읽지 못했습니다.");
    } finally {
      event.target.value = "";
    }
  };

  const importMt5Report = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const imported = parseMt5Report(text, file.name, mt5Snapshot?.account).map((trade) =>
        normalizeImportedTrade(trade, mt5Snapshot?.account),
      );
      if (!imported.length) throw new Error("No closed trades found in report.");

      setTrades((current) => {
        const merged = mergeImportedTrades(current, imported);
        void saveJournalToServer(merged, reviewsRef.current, "MT5 보고서 저장됨").catch((error) => {
          setJournalServerReady(false);
          setJournalSync(error instanceof Error ? `MT5 보고서 공용 저장 실패: ${error.message}` : "MT5 보고서 공용 저장 실패");
        });
        return merged;
      });
      setEditingId(null);
      setNotice(`MT5 report imported: ${imported.length} trades merged.`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "MT5 report import failed.");
    } finally {
      event.target.value = "";
    }
  };
  const useSuggestedQuantity = () => {
    setDraftField("quantity", draftDerived.suggestedQuantity);
  };

  const setActiveTradingSymbol = (value: string) => {
    const normalized = normalizeSymbol(value);
    setActiveSymbol(normalized);
    setOrderDraft((current) => ({ ...current, symbol: normalized }));
    setOrderPreview(null);
    setOrderArmed(false);
  };

  const getBridge = async <T,>(path: string): Promise<T> => {
    const response = await fetch(`${MT5_BRIDGE_URL}${path}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return (await response.json()) as T;
  };

  const syncQuery = (basePath: "/snapshot" | "/ea-events") => {
    const since = latestTradeSyncIso(trades);
    const params = new URLSearchParams({ days: String(mt5Days) });
    if (since) params.set("since", since);
    return `${basePath}?${params.toString()}`;
  };

  const updateEaNotice = (snapshot: Pick<Mt5Snapshot, "ea">) => {
    const ea = snapshot.ea;
    if (!ea) {
      setEaNotice("EA 이벤트 상태 확인 전");
      return;
    }

    if (ea.attachmentState === "missing" || !ea.eventFileExists) {
      setEaNotice(ea.attachmentMessage || "EA 이벤트 파일 없음. MT5 차트에 TradeJournalExporterEA를 붙여야 합니다.");
      return;
    }

    if (ea.attachmentState === "stopped") {
      setEaNotice(ea.attachmentMessage || "EA 중지됨. MT5에서 EA와 Algo Trading 상태를 확인하세요.");
      return;
    }

    if (ea.attachmentState === "stale") {
      const age = ea.secondsSinceEventFileModified ? ` · 마지막 파일 갱신 ${Math.round(ea.secondsSinceEventFileModified)}초 전` : "";
      setEaNotice(`${ea.attachmentMessage || "EA heartbeat가 오래되었습니다."}${age}`);
      return;
    }

    const status = ea.lastStatus ? ` · ${ea.lastStatus}` : "";
    const chart = ea.lastStatusChartSymbol ? ` · 차트 ${ea.lastStatusChartSymbol}` : "";
    const version = ea.lastStatusEaVersion ? ` · EA v${ea.lastStatusEaVersion}` : "";
    const positions = typeof ea.lastStatusPositionsTotal === "number" ? ` · 포지션 ${ea.lastStatusPositionsTotal}개` : "";
    const source = ea.eventSource ? ` · ${ea.eventSource.toUpperCase()}` : "";
    const empty = (ea.tradeEventCount ?? 0) === 0 ? " · 다음 MT5 포지션부터 자동 기록" : "";
    const modified = (ea.lastStatusTime || ea.eventFileModifiedAt) ? ` · ${new Date(ea.lastStatusTime || ea.eventFileModifiedAt || "").toLocaleTimeString()}` : "";
    const parseError = ea.parseErrorCount ? ` · 파싱 오류 ${ea.parseErrorCount}` : "";
    setEaNotice(`EA 연결됨${status}${chart}${version}${positions}${source} · 동기화 거래 ${ea.tradeCount ?? 0}건${empty}${modified}${parseError}`);
  };

  const applySnapshot = (snapshot: Mt5Snapshot, updateNotice = true) => {
    const imported = snapshot.trades.map((trade) => normalizeImportedTrade(trade, snapshot.account));
    if (imported.length) {
      setTrades((current) => {
        const merged = mergeImportedTrades(current, imported);
        void saveJournalToServer(merged, reviewsRef.current, "MT5 동기화 저장됨").catch((error) => {
          setJournalServerReady(false);
          setJournalSync(error instanceof Error ? `MT5 동기화 공용 저장 실패: ${error.message}` : "MT5 동기화 공용 저장 실패");
        });
        return merged;
      });
    }
    updateEaNotice(snapshot);
    setMt5Snapshot((current) => ({
      ...snapshot,
      positions: snapshot.positions ?? current?.positions ?? [],
      trades: snapshot.trades ?? current?.trades ?? [],
    }));

    if (updateNotice) {
      const eaSuffix = snapshot.ea?.tradeCount ? ` EA 거래 ${snapshot.ea.tradeCount}건 병합` : "";
      setMt5Notice(`${imported.length}건 거래를 동기화했습니다. 현재 포지션 ${snapshot.positions.length}건을 읽었습니다.${eaSuffix}`);
    }

    if (snapshot.account?.currency) {
      setDraft((current) => ({
        ...current,
        currency: snapshot.account?.currency?.toUpperCase() ?? current.currency,
        accountValue: Number(snapshot.account?.balance ?? snapshot.account?.equity ?? current.accountValue),
      }));
    }
  };

  const syncMt5 = async () => {
    setMt5Loading(true);
    setMt5Notice("MT5 브리지에 연결 중입니다.");

    try {
      const snapshot = await getBridge<Mt5Snapshot>(syncQuery("/snapshot"));
      if (!snapshot.ok) throw new Error(snapshot.error || "MT5 브리지 응답이 올바르지 않습니다.");
      applySnapshot(snapshot);
    } catch (error) {
      setMt5Notice(error instanceof Error ? error.message : "MT5 브리지 연결에 실패했습니다.");
    } finally {
      setMt5Loading(false);
    }
  };

  const usePositionAsDraft = (position: Mt5Position) => {
    setActiveTradingSymbol(position.symbol);
    setDraft(draftFromMt5Position(position, mt5Snapshot?.account));
    setEditingId(null);
    setNotice(`${position.symbol} 현재 포지션을 작성 폼으로 불러왔습니다.`);
  };

  const setOrderField = <K extends keyof OrderDraft>(key: K, value: OrderDraft[K]) => {
    if (key === "symbol") {
      const normalized = normalizeSymbol(String(value));
      setActiveSymbol(normalized);
      setOrderDraft((current) => ({ ...current, symbol: normalized }));
    } else {
      setOrderDraft((current) => ({ ...current, [key]: value }));
    }
    setOrderPreview(null);
    setOrderArmed(false);
  };

  const orderPayload = () => ({
    ...orderDraft,
    symbol: orderDraft.symbol.trim().toUpperCase(),
  });

  const postBridge = async <T,>(path: string, payload: Record<string, unknown>): Promise<T> => {
    const response = await fetch(`${MT5_BRIDGE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return (await response.json()) as T;
  };

  const previewOrder = async () => {
    setOrderLoading(true);
    setOrderArmed(false);
    setOrderNotice("현재 tick과 계좌 기준으로 lot을 계산 중입니다.");

    try {
      const preview = await postBridge<OrderPreview>("/order/preview", orderPayload());
      setOrderPreview(preview);
      if (!preview.ok) throw new Error(preview.error || "주문 미리보기에 실패했습니다.");
      setOrderNotice(
        `${preview.symbol} ${preview.side?.toUpperCase()} ${number.format(preview.volume ?? 0)} lot, 예상 손실 ${formatMoney(
          preview.estimatedLoss ?? 0,
          preview.currency ?? displayCurrency,
        )}`,
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : "주문 미리보기에 실패했습니다.";
      setOrderPreview({ ok: false, error: message });
      setOrderNotice(message);
    } finally {
      setOrderLoading(false);
    }
  };

  const sendLiveOrder = async () => {
    if (!orderPreview?.ok || !orderArmed) return;

    setOrderLoading(true);
    setOrderNotice("실주문을 MT5로 전송 중입니다.");

    try {
      const result = await postBridge<OrderSendResult>("/order/send", {
        ...orderPayload(),
        confirm: "LIVE_ORDER",
        ackRisk: true,
      });

      if (!result.ok) {
        const retcode = result.result?.retcode ? ` retcode=${String(result.result.retcode)}` : "";
        throw new Error(result.error || `MT5 주문이 완료되지 않았습니다.${retcode}`);
      }

      setOrderPreview(result.preview ?? orderPreview);
      setOrderArmed(false);
      setOrderNotice(`주문 전송 완료: ticket ${String(result.result?.order ?? result.result?.deal ?? "-")}`);
      await syncMt5();
    } catch (error) {
      setOrderNotice(error instanceof Error ? error.message : "실주문 전송에 실패했습니다.");
    } finally {
      setOrderLoading(false);
    }
  };

  useEffect(() => {
    if (activeWorkspaceTab !== "chart") {
      setLiveError("");
      return;
    }

    const symbol = normalizeSymbol(activeSymbol);
    if (!symbol) {
      setLiveError("");
      return;
    }

    let cancelled = false;
    const loadLive = async () => {
      try {
        const live = await getBridge<LiveResponse>(`/live?symbol=${encodeURIComponent(symbol)}`);
        if (!live.ok) throw new Error(live.error || "MT5 live 응답이 올바르지 않습니다.");
        if (cancelled) return;

        setLatestTick(live.tick);
        setChartSymbolInfo((current) => live.symbolInfo ?? current);
        setLiveError("");
        setMt5Snapshot((current) => ({
          ok: true,
          generatedAt: live.generatedAt,
          account: live.account ?? current?.account,
          positions: live.positions ?? [],
          trades: current?.trades ?? [],
        }));

        if (live.account?.currency) {
          setDraft((current) => ({
            ...current,
            currency: live.account?.currency?.toUpperCase() ?? current.currency,
            accountValue: Number(live.account?.balance ?? live.account?.equity ?? current.accountValue),
          }));
        }
      } catch (error) {
        if (!cancelled) {
          setLiveError(error instanceof Error ? error.message : "MT5 live 연결에 실패했습니다.");
        }
      }
    };

    void loadLive();
    const timer = window.setInterval(() => void loadLive(), 1000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [activeSymbol, activeWorkspaceTab]);

  useEffect(() => {
    if (activeWorkspaceTab !== "chart") {
      setChartBars([]);
      setChartError("");
      return;
    }

    const symbol = normalizeSymbol(activeSymbol);
    if (!symbol) {
      setChartBars([]);
      setChartError("");
      return;
    }

    let cancelled = false;
    const loadChart = async (showLoading = false) => {
      if (showLoading) setChartLoading(true);
      try {
        const chart = await getBridge<ChartResponse>(
          `/chart?symbol=${encodeURIComponent(symbol)}&timeframe=${activeTimeframe}&bars=500`,
        );
        if (!chart.ok) throw new Error(chart.error || "MT5 chart 응답이 올바르지 않습니다.");
        if (cancelled) return;

        setChartBars(chart.bars ?? []);
        setLatestTick((current) => chart.tick ?? current);
        setChartSymbolInfo((current) => chart.symbolInfo ?? current);
        setChartError("");
      } catch (error) {
        if (!cancelled) {
          setChartBars([]);
          setChartError(error instanceof Error ? error.message : "MT5 chart 연결에 실패했습니다.");
        }
      } finally {
        if (!cancelled && showLoading) setChartLoading(false);
      }
    };

    void loadChart(true);
    const timer = window.setInterval(() => void loadChart(false), 3000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [activeSymbol, activeTimeframe, activeWorkspaceTab]);

  useEffect(() => {
    const timer = window.setInterval(async () => {
      try {
        const snapshot = await getBridge<Mt5Snapshot>(syncQuery("/snapshot"));
        if (snapshot.ok) applySnapshot(snapshot, false);
      } catch {
        // Manual journal data stays usable when MT5 is offline.
      }
    }, 30_000);

    return () => window.clearInterval(timer);
  }, [mt5Days, trades]);

  useEffect(() => {
    const timer = window.setInterval(async () => {
      try {
        const snapshot = await getBridge<Mt5Snapshot>(syncQuery("/ea-events"));
        if (!snapshot.ok) throw new Error(snapshot.error || "EA 이벤트 응답이 올바르지 않습니다.");
        const imported = snapshot.trades.map((trade) => normalizeImportedTrade(trade, snapshot.account));
        if (imported.length) {
          setTrades((current) => {
            const merged = mergeImportedTrades(current, imported);
            void saveJournalToServer(merged, reviewsRef.current, "EA 이벤트 저장됨").catch((error) => {
              setJournalServerReady(false);
              setJournalSync(error instanceof Error ? `EA 이벤트 공용 저장 실패: ${error.message}` : "EA 이벤트 공용 저장 실패");
            });
            return merged;
          });
        }
        updateEaNotice(snapshot);
        setMt5Snapshot((current) =>
          current
            ? {
                ...current,
                account: snapshot.account ?? current.account,
                trades: snapshot.trades ?? current.trades,
                ea: snapshot.ea ?? current.ea,
              }
            : {
                ok: true,
                generatedAt: snapshot.generatedAt,
                account: snapshot.account,
                positions: [],
                trades: snapshot.trades ?? [],
                ea: snapshot.ea,
              },
        );
      } catch {
        // The normal journal remains usable while the EA is not attached yet.
      }
    }, 5000);

    return () => window.clearInterval(timer);
  }, [mt5Days, trades]);

  return (
    <div className="app-shell" onPaste={handlePaste}>
      <aside className="rail">
        <div className="brand">
          <div className="brand-mark">
            <BarChart3 size={22} />
          </div>
          <div>
            <strong>Trade Ledger</strong>
            <span>Risk-first journal</span>
          </div>
        </div>

        <section className="rail-card sync-card">
          <div className="rail-card-head">
            <div>
              <span className="eyebrow">XM / MT5</span>
              <strong>자동 동기화</strong>
            </div>
            <Cloud size={20} />
          </div>
          <div className="sidebar-sync-controls">
            <select value={mt5Days} onChange={(event) => setMt5Days(toNumber(event.target.value))} aria-label="동기화 기간">
              <option value={7}>최근 7일</option>
              <option value={14}>최근 14일</option>
              <option value={30}>최근 30일</option>
              <option value={90}>최근 90일</option>
            </select>
            <button className="primary" type="button" onClick={syncMt5} disabled={mt5Loading}>
              <DatabaseZap size={17} />
              {mt5Loading ? "동기화 중" : "동기화"}
            </button>
          </div>
          <span className="sync-notice compact">{eaNotice || mt5Notice}</span>
        </section>

        <section className="rail-card account-card">
          <div className="rail-card-head">
            <strong>계좌</strong>
            <span>{mt5Snapshot?.account?.login ?? "연결 전"}</span>
          </div>
          <div className="sidebar-kv">
            <span>서버</span>
            <b>{mt5Snapshot?.account?.server ?? "XM MT5"}</b>
            <span>잔고</span>
            <b>{formatMoney(mt5Snapshot?.account?.balance ?? 0, displayCurrency)}</b>
            <span>평가금</span>
            <b>{formatMoney(mt5Snapshot?.account?.equity ?? 0, displayCurrency)}</b>
          </div>
        </section>

        <section className="rail-card positions-card">
          <div className="rail-card-head">
            <strong>현재 포지션</strong>
            <span>{mt5Snapshot?.positions.length ?? 0}</span>
          </div>
          {mt5Snapshot?.positions.length ? (
            <div className="sidebar-positions">
              {mt5Snapshot.positions.slice(0, 4).map((position) => (
                <button className="sidebar-position-row" type="button" key={position.ticket} onClick={() => usePositionAsDraft(position)}>
                  <span className={`direction-badge ${position.direction}`}>{directionLabel[position.direction]}</span>
                  <strong>{position.symbol}</strong>
                  <b className={position.profit >= 0 ? "positive" : "negative"}>{formatMoney(position.profit, displayCurrency)}</b>
                </button>
              ))}
            </div>
          ) : (
            <div className="position-empty compact">포지션 없음</div>
          )}
        </section>

        <div className="rail-stack">
          <div className="rail-stat">
            <span>실현 손익</span>
            <strong className={summary.pnl >= 0 ? "positive" : "negative"}>{formatMoney(summary.pnl, displayCurrency)}</strong>
          </div>
          <div className="rail-stat">
            <span>승률</span>
            <strong>{number.format(summary.winRate)}%</strong>
          </div>
          <div className="rail-stat">
            <span>평균 손익비</span>
            <strong>{summary.avgRewardRisk.toFixed(2)}:1</strong>
          </div>
          <div className="rail-stat">
            <span>규율 점수</span>
            <strong>{summary.avgDiscipline.toFixed(1)}/5</strong>
          </div>
        </div>

        <div className="rail-actions">
          <button type="button" onClick={resetDraft}>
            <Plus size={17} />
            새 기록
          </button>
          <button type="button" onClick={() => importRef.current?.click()}>
            <Upload size={17} />
            JSON 불러오기
          </button>
          <button type="button" onClick={exportCsv} disabled={!trades.length}>
            <FileSpreadsheet size={17} />
            CSV 내보내기
          </button>
          <button type="button" onClick={exportJson} disabled={!trades.length}>
            <FileJson size={17} />
            JSON 백업
          </button>
          <input ref={importRef} className="sr-only" type="file" accept="application/json,.json" onChange={importJson} />
          <input ref={reportImportRef} className="sr-only" type="file" accept={MT5_REPORT_FILE_TYPES} onChange={importMt5Report} />
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <span className="eyebrow">Trading Journal</span>
            <h1>매매일지</h1>
          </div>
          <div className="topbar-actions">
            <span className={`journal-sync ${journalServerReady ? "online" : "offline"}`}>{journalSync}</span>
          </div>
        </header>

        <nav className="workspace-tabs" aria-label="작업 탭">
          <button
            type="button"
            className={activeWorkspaceTab === "journal" ? "active" : ""}
            onClick={() => setActiveWorkspaceTab("journal")}
          >
            <ClipboardList size={18} />
            매매일지
            <span>{trades.length}</span>
          </button>
          <button
            type="button"
            className={activeWorkspaceTab === "analytics" ? "active" : ""}
            onClick={() => setActiveWorkspaceTab("analytics")}
          >
            <BarChart3 size={18} />
            분석
          </button>
          <button
            type="button"
            className={activeWorkspaceTab === "calendar" ? "active" : ""}
            onClick={() => setActiveWorkspaceTab("calendar")}
          >
            <CalendarDays size={18} />
            캘린더
          </button>
          <button
            type="button"
            className={activeWorkspaceTab === "reviews" ? "active" : ""}
            onClick={() => setActiveWorkspaceTab("reviews")}
          >
            <ClipboardList size={18} />
            결산목록
            <span>{reviews.filter((review) => review.completed).length}</span>
          </button>
          <button
            type="button"
            className={activeWorkspaceTab === "aiFeedback" ? "active" : ""}
            onClick={() => setActiveWorkspaceTab("aiFeedback")}
          >
            <Brain size={18} />
            AI 피드백
            <span>{aiFeedbackTrades.length}</span>
          </button>
          <a className="workspace-replay-link" href="/replay">
            <Gauge size={18} />
            시장 재생
          </a>
        </nav>

        <section className={`automation-panel tab-content ${activeWorkspaceTab === "journal" ? "active" : ""}`}>
          <div className="automation-copy">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">XM / MT5</span>
                <h2>자동 동기화</h2>
              </div>
              <Cloud size={22} />
            </div>
            <p>
              MT5 터미널에서 계좌, 현재 포지션, 최근 청산 거래를 읽어와 일지로 병합합니다. 주문 발주는 하지 않고 기록 자동화만 수행합니다.
            </p>
            <div className="automation-controls">
              <label>
                기간
                <select value={mt5Days} onChange={(event) => setMt5Days(toNumber(event.target.value))}>
                  <option value={7}>최근 7일</option>
                  <option value={14}>최근 14일</option>
                  <option value={30}>최근 30일</option>
                  <option value={90}>최근 90일</option>
                </select>
              </label>
              <button className="primary" type="button" onClick={syncMt5} disabled={mt5Loading}>
                <DatabaseZap size={18} />
                {mt5Loading ? "동기화 중" : "MT5 동기화"}
              </button>
            </div>
            <span className="sync-notice">{mt5Notice}</span>
            <span className="sync-notice">{eaNotice}</span>
          </div>

          <div className="account-strip">
            <div>
              <span>계좌</span>
              <strong>{mt5Snapshot?.account?.login ?? "연결 전"}</strong>
            </div>
            <div>
              <span>서버</span>
              <strong>{mt5Snapshot?.account?.server ?? "XM MT5"}</strong>
            </div>
            <div>
              <span>잔고</span>
              <strong>{formatMoney(mt5Snapshot?.account?.balance ?? 0, displayCurrency)}</strong>
            </div>
            <div>
              <span>평가금</span>
              <strong>{formatMoney(mt5Snapshot?.account?.equity ?? 0, displayCurrency)}</strong>
            </div>
          </div>

          <div className="positions-preview">
            <div className="mini-title">
              <span>현재 포지션</span>
              <b>{mt5Snapshot?.positions.length ?? 0}</b>
            </div>
            {mt5Snapshot?.positions.length ? (
              mt5Snapshot.positions.slice(0, 4).map((position) => (
                <button className="position-row" type="button" key={position.ticket} onClick={() => usePositionAsDraft(position)}>
                  <span className={`direction-badge ${position.direction}`}>{directionLabel[position.direction]}</span>
                  <strong>{position.symbol}</strong>
                  <span>{number.format(position.volume)} lot</span>
                  <b className={position.profit >= 0 ? "positive" : "negative"}>{formatMoney(position.profit, displayCurrency)}</b>
                </button>
              ))
            ) : (
              <div className="position-empty">포지션 없음</div>
            )}
          </div>
        </section>

        <section
          className={`trading-cockpit tab-content ${activeWorkspaceTab === "chart" ? "active" : ""} tab-chart`}
        >
          <TradingChart
            symbol={activeSymbol}
            timeframe={activeTimeframe}
            bars={chartBars}
            latestTick={latestTick}
            positions={mt5Snapshot?.positions ?? []}
            symbolInfo={chartSymbolInfo}
            stopLoss={0}
            takeProfit={0}
            loading={chartLoading}
            error={chartError}
            onSymbolChange={setActiveTradingSymbol}
            onTimeframeChange={setActiveTimeframe}
            onStopLossChange={() => undefined}
            onTakeProfitChange={() => undefined}
          />

        <section className="order-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Risk Order</span>
              <h2>1% 리스크 주문</h2>
            </div>
            <Send size={22} />
          </div>

          <div className="order-layout">
            <div className="order-form">
              <div className="direction-toggle compact" role="group" aria-label="주문 방향">
                <button
                  type="button"
                  className={orderDraft.side === "buy" ? "active long" : ""}
                  onClick={() => setOrderField("side", "buy")}
                >
                  <ArrowUpRight size={18} />
                  Buy
                </button>
                <button
                  type="button"
                  className={orderDraft.side === "sell" ? "active short" : ""}
                  onClick={() => setOrderField("side", "sell")}
                >
                  <ArrowDownRight size={18} />
                  Sell
                </button>
              </div>

              <div className="order-inputs">
                <label>
                  심볼
                  <input
                    autoComplete="off"
                    value={orderDraft.symbol}
                    onChange={(event) => setOrderField("symbol", event.target.value.toUpperCase())}
                  />
                </label>
                <label>
                  리스크 %
                  <input
                    inputMode="decimal"
                    value={orderDraft.riskPercent || ""}
                    onChange={(event) => setOrderField("riskPercent", toNumber(event.target.value))}
                  />
                </label>
                <label>
                  SL
                  <input
                    inputMode="decimal"
                    value={orderDraft.stopLoss || ""}
                    onChange={(event) => setOrderField("stopLoss", toNumber(event.target.value))}
                  />
                </label>
                <label>
                  TP
                  <input
                    inputMode="decimal"
                    value={orderDraft.takeProfit || ""}
                    onChange={(event) => setOrderField("takeProfit", toNumber(event.target.value))}
                  />
                </label>
                <label>
                  Slippage
                  <input
                    inputMode="numeric"
                    value={orderDraft.deviation || ""}
                    onChange={(event) => setOrderField("deviation", toNumber(event.target.value))}
                  />
                </label>
                <label>
                  Fill
                  <select
                    value={orderDraft.fillPolicy}
                    onChange={(event) => setOrderField("fillPolicy", event.target.value as OrderDraft["fillPolicy"])}
                  >
                    <option value="IOC">IOC</option>
                    <option value="FOK">FOK</option>
                    <option value="RETURN">RETURN</option>
                  </select>
                </label>
              </div>

              <label className="wide-label">
                주문 메모
                <input
                  value={orderDraft.comment}
                  onChange={(event) => setOrderField("comment", event.target.value)}
                />
              </label>
            </div>

            <div className="order-preview">
              <div className="order-preview-grid">
                <div>
                  <span>진입가</span>
                  <strong>{orderPreview?.entryPrice ? number.format(orderPreview.entryPrice) : "-"}</strong>
                </div>
                <div>
                  <span>계산 lot</span>
                  <strong>{orderPreview?.volume ? number.format(orderPreview.volume) : "-"}</strong>
                </div>
                <div>
                  <span>예상 손실</span>
                  <strong className="negative">
                    {formatMoney(orderPreview?.estimatedLoss ?? 0, orderPreview?.currency ?? displayCurrency)}
                  </strong>
                </div>
                <div>
                  <span>예상 수익</span>
                  <strong className={(orderPreview?.estimatedProfit ?? 0) >= 0 ? "positive" : "negative"}>
                    {formatMoney(orderPreview?.estimatedProfit ?? 0, orderPreview?.currency ?? displayCurrency)}
                  </strong>
                </div>
                <div>
                  <span>손익비</span>
                  <strong>{(orderPreview?.rewardRisk ?? 0).toFixed(2)}R</strong>
                </div>
                <div>
                  <span>Spread</span>
                  <strong>{orderPreview?.spread ? number.format(orderPreview.spread) : "-"}</strong>
                </div>
              </div>

              <div className="order-actions">
                <button className="ghost" type="button" onClick={previewOrder} disabled={orderLoading}>
                  <Calculator size={18} />
                  주문 미리보기
                </button>
                <label className="arm-order">
                  <input
                    type="checkbox"
                    checked={orderArmed}
                    disabled={!orderPreview?.ok || orderLoading}
                    onChange={(event) => setOrderArmed(event.target.checked)}
                  />
                  예상 손실과 lot을 확인함
                </label>
                <button
                  className="danger"
                  type="button"
                  onClick={sendLiveOrder}
                  disabled={!orderPreview?.ok || !orderArmed || orderLoading}
                >
                  <Send size={18} />
                  실주문 전송
                </button>
              </div>

              <span className={orderPreview?.ok === false ? "order-notice error" : "order-notice"}>{orderNotice}</span>
              {liveError ? <span className="order-notice error">Live sync: {liveError}</span> : null}
              {orderPreview?.warnings?.length ? (
                <div className="order-warning">{orderPreview.warnings.join(" ")}</div>
              ) : null}
              {orderPreview?.orderCheck ? (
                <div className="order-check">
                  order_check: {String(orderPreview.orderCheck.retcode ?? "-")} {String(orderPreview.orderCheck.comment ?? "")}
                </div>
              ) : null}
            </div>
          </div>
        </section>
        </section>

        <section className={`metric-grid tab-content ${activeWorkspaceTab === "journal" ? "active" : ""}`}>
          <MetricCard
            icon={<Wallet size={21} />}
            label="실현 손익"
            value={formatMoney(summary.pnl, displayCurrency)}
            detail={`${summary.closed}건 청산`}
            tone={summary.pnl >= 0 ? "good" : "bad"}
          />
          <MetricCard
            icon={<Target size={21} />}
            label="승률"
            value={`${number.format(summary.winRate)}%`}
            detail={`${summary.wins}/${summary.closed || 0} 승`}
            tone={summary.winRate >= 50 ? "good" : "warn"}
          />
          <MetricCard
            icon={<Gauge size={21} />}
            label="평균 손익비"
            value={`${summary.avgRewardRisk.toFixed(2)}:1`}
            detail="SL/TP 입력 거래 기준"
            tone={summary.avgRewardRisk >= 1 ? "good" : "warn"}
          />
          <MetricCard
            icon={<ShieldCheck size={21} />}
            label="규율 점수"
            value={`${summary.avgDiscipline.toFixed(1)}/5`}
            detail="체크리스트 평균"
            tone={summary.avgDiscipline >= 4 ? "good" : "neutral"}
          />
        </section>

        <section className={`workspace tab-content ${activeWorkspaceTab === "journal" ? "active" : ""}`}>
          <form id="trade-form" className="journal-panel" onSubmit={handleSave}>
            <div className="panel-heading">
              <div>
                <span className="eyebrow">{editingId ? "Edit" : "New"}</span>
                <h2>거래 기록</h2>
              </div>
              <div className={`status-pill ${draftDerived.computedResult}`}>
                {resultLabel[draftDerived.computedResult]}
              </div>
            </div>

            {isMt5Draft ? (
              <div className="auto-record-card">
                <div>
                  <span className="eyebrow">MT5 Auto Record</span>
                  <strong>{draft.symbol || "MT5 거래"}</strong>
                  <p>가격, 수량, SL/TP, 청산, 손익은 MT5 동기화로 갱신됩니다. 아래 회고 메모만 작성하면 됩니다.</p>
                </div>
                <div className="auto-record-grid">
                  <span>
                    Entry <b>{draft.entryPrice ? number.format(draft.entryPrice) : "-"}</b>
                  </span>
                  <span>
                    SL <b>{draft.stopPrice ? number.format(draft.stopPrice) : "-"}</b>
                  </span>
                  <span>
                    TP <b>{draft.targetPrice ? number.format(draft.targetPrice) : "-"}</b>
                  </span>
                  <span>
                    PnL <b className={draftDerived.pnl >= 0 ? "positive" : "negative"}>{formatMoney(draftDerived.pnl, draft.currency)}</b>
                  </span>
                </div>
              </div>
            ) : null}

            <fieldset className="auto-locked-fields" disabled={isMt5Draft}>
            <div className="direction-toggle" role="group" aria-label="매매 방향">
              <button
                type="button"
                className={draft.direction === "long" ? "active long" : ""}
                onClick={() => setDraftField("direction", "long")}
              >
                <ArrowUpRight size={18} />
                Long
              </button>
              <button
                type="button"
                className={draft.direction === "short" ? "active short" : ""}
                onClick={() => setDraftField("direction", "short")}
              >
                <ArrowDownRight size={18} />
                Short
              </button>
            </div>

            <div className="form-grid">
              <label>
                날짜
                <input type="date" value={draft.date} onChange={(event) => setDraftField("date", event.target.value)} />
              </label>
              <label>
                시장
                <select value={draft.market} onChange={(event) => setDraftField("market", event.target.value)}>
                  {marketOptions.map((market) => (
                    <option key={market}>{market}</option>
                  ))}
                </select>
              </label>
              <label>
                통화
                <input
                  autoComplete="off"
                  value={draft.currency}
                  onChange={(event) => setDraftField("currency", event.target.value.toUpperCase())}
                />
              </label>
              <label>
                종목
                <input
                  autoComplete="off"
                  placeholder="005930, TSLA, BTC"
                  value={draft.symbol}
                  onChange={(event) => setDraftField("symbol", event.target.value)}
                />
              </label>
              <label>
                셋업
                <select value={draft.setup} onChange={(event) => setDraftField("setup", event.target.value)}>
                  {setupOptions.map((setup) => (
                    <option key={setup}>{setup}</option>
                  ))}
                </select>
              </label>
              <label>
                타임프레임
                <select value={draft.timeframe} onChange={(event) => setDraftField("timeframe", event.target.value)}>
                  {timeframeOptions.map((timeframe) => (
                    <option key={timeframe}>{timeframe}</option>
                  ))}
                </select>
              </label>
              <label>
                상태
                <select value={draft.status} onChange={(event) => setDraftField("status", event.target.value as TradeStatus)}>
                  <option value="open">보유</option>
                  <option value="closed">청산</option>
                </select>
              </label>
            </div>

            <div className="form-grid numbers">
              <label>
                계좌 규모
                <input
                  inputMode="decimal"
                  value={draft.accountValue || ""}
                  onChange={(event) => setDraftField("accountValue", toNumber(event.target.value))}
                />
              </label>
              <label>
                리스크 %
                <input
                  inputMode="decimal"
                  value={draft.riskPercent || ""}
                  onChange={(event) => setDraftField("riskPercent", toNumber(event.target.value))}
                />
              </label>
              <label>
                진입가
                <input
                  inputMode="decimal"
                  value={draft.entryPrice || ""}
                  onChange={(event) => setDraftField("entryPrice", toNumber(event.target.value))}
                />
              </label>
              <label>
                손절가
                <input
                  inputMode="decimal"
                  value={draft.stopPrice || ""}
                  onChange={(event) => setDraftField("stopPrice", toNumber(event.target.value))}
                />
              </label>
              <label>
                목표가
                <input
                  inputMode="decimal"
                  value={draft.targetPrice || ""}
                  onChange={(event) => setDraftField("targetPrice", toNumber(event.target.value))}
                />
              </label>
              <label>
                청산가
                <input
                  inputMode="decimal"
                  value={draft.exitPrice || ""}
                  onChange={(event) => {
                    const exitPrice = toNumber(event.target.value);
                    setDraft((current) => ({
                      ...current,
                      exitPrice,
                      status: exitPrice > 0 ? "closed" : current.status,
                    }));
                  }}
                />
              </label>
              <label>
                수량
                <div className="with-button">
                  <input
                    inputMode="decimal"
                    value={draft.quantity || ""}
                    onChange={(event) => setDraftField("quantity", toNumber(event.target.value))}
                  />
                  <button type="button" className="icon-button" onClick={useSuggestedQuantity} aria-label="권장 수량 적용">
                    <Calculator size={17} />
                  </button>
                </div>
              </label>
              <label>
                수수료
                <input inputMode="decimal" value={draft.fees || ""} onChange={(event) => setDraftField("fees", toNumber(event.target.value))} />
              </label>
            </div>
            </fieldset>

            <details className="optional-section" key={isMt5Draft ? "mt5-notes" : "manual-notes"} open={isMt5Draft || undefined}>
              <summary>
                <span>{isMt5Draft ? "회고 메모" : "회고, 태그, 차트 이미지"}</span>
                <b>{isMt5Draft ? "작성 필요" : "선택 입력"}</b>
              </summary>

              <div className="quality-grid">
                <label>
                  확신도 <strong>{draft.confidence}</strong>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={draft.confidence}
                    onChange={(event) => setDraftField("confidence", toNumber(event.target.value))}
                  />
                </label>
                <label>
                  규율 <strong>{draft.discipline}</strong>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={draft.discipline}
                    onChange={(event) => setDraftField("discipline", toNumber(event.target.value))}
                  />
                </label>
                <label>
                  감정
                  <select value={draft.emotion} onChange={(event) => setDraftField("emotion", event.target.value)}>
                    {emotionOptions.map((emotion) => (
                      <option key={emotion}>{emotion}</option>
                    ))}
                  </select>
                </label>
                <label>
                  등급
                  <select value={draft.grade} onChange={(event) => setDraftField("grade", event.target.value)}>
                    {gradeOptions.map((grade) => (
                      <option key={grade}>{grade}</option>
                    ))}
                  </select>
                </label>
              </div>

              <label className="wide-label">
                태그
                <input placeholder="MT5, XM, London, News" value={draft.tags} onChange={(event) => setDraftField("tags", event.target.value)} />
              </label>

              <div className="text-grid">
                <label>
                  진입 근거
                  <textarea value={draft.thesis} onChange={(event) => setDraftField("thesis", event.target.value)} />
                </label>
                <label>
                  리스크 계획
                  <textarea value={draft.riskPlan} onChange={(event) => setDraftField("riskPlan", event.target.value)} />
                </label>
                <label>
                  잘한 점
                  <textarea value={draft.good} onChange={(event) => setDraftField("good", event.target.value)} />
                </label>
                <label>
                  놓친 점
                  <textarea value={draft.bad} onChange={(event) => setDraftField("bad", event.target.value)} />
                </label>
                <label className="span-two">
                  다음 원칙
                  <textarea value={draft.lesson} onChange={(event) => setDraftField("lesson", event.target.value)} />
                </label>
              </div>

              <ChartImageEditor
                image={draft.screenshot}
                imageName={draft.screenshotName}
                annotations={draft.screenshotAnnotations}
                onImageUpload={handleScreenshotUpload}
                onDrop={handleDrop}
                onRemoveImage={() => {
                  setDraft((current) => ({
                    ...current,
                    screenshot: undefined,
                    screenshotName: undefined,
                    screenshotAnnotations: [],
                  }));
                }}
                onAnnotationsChange={(screenshotAnnotations) => setDraft((current) => ({ ...current, screenshotAnnotations }))}
              />
            </details>

            <div className="form-footer">
              <span>{notice}</span>
              <button className="primary" type="submit">
                <Save size={18} />
                {editingId ? "수정 저장" : "기록 저장"}
              </button>
            </div>
          </form>

          <section className="analysis-panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">Live</span>
                <h2>리스크 보드</h2>
              </div>
              <ClipboardList size={22} />
            </div>

            <div className="preview-symbol">
              <div>
                <span>{draft.market}</span>
                <strong>{draft.symbol || "SYMBOL"}</strong>
              </div>
              <div className={`direction-badge ${draft.direction}`}>{directionLabel[draft.direction]}</div>
            </div>

            <div className="risk-grid">
              <div>
                <span>권장 수량</span>
                <strong>{number.format(draftDerived.suggestedQuantity)}</strong>
              </div>
              <div>
                <span>계획 리스크</span>
                <strong>{formatMoney(draftDerived.plannedRisk, draft.currency)}</strong>
              </div>
              <div>
                <span>실제 리스크</span>
                <strong>{draftDerived.plannedRisk > 0 ? formatPercent(draftDerived.actualRiskPercent) : "-"}</strong>
              </div>
              <div>
                <span>손익비</span>
                <strong>{draftDerived.rewardRisk.toFixed(2)}:1</strong>
              </div>
              <div>
                <span>예상/확정 손익</span>
                <strong className={draftDerived.pnl >= 0 ? "positive" : "negative"}>{formatMoney(draftDerived.pnl, draft.currency)}</strong>
              </div>
            </div>

            <div className="chart-panel">
              <div className="chart-title">
                <span>누적 손익</span>
                <CalendarDays size={17} />
              </div>
              <div className="chart-wrap">
                {equityCurve.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={equityCurve} margin={{ left: -14, right: 8, top: 8, bottom: 4 }}>
                      <defs>
                        <linearGradient id="equity" x1="0" x2="0" y1="0" y2="1">
                          <stop offset="0%" stopColor="#2dd4bf" stopOpacity={0.75} />
                          <stop offset="100%" stopColor="#2dd4bf" stopOpacity={0.05} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke="#29313b" strokeDasharray="4 4" />
                      <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: "#8d98a9", fontSize: 11 }} />
                      <YAxis tickLine={false} axisLine={false} tick={{ fill: "#8d98a9", fontSize: 11 }} />
                      <Tooltip contentStyle={{ background: "#151920", border: "1px solid #303946", borderRadius: 8 }} />
                      <Area type="monotone" dataKey="pnl" stroke="#2dd4bf" fill="url(#equity)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-chart">청산 거래 없음</div>
                )}
              </div>
            </div>

            <div className="chart-panel">
              <div className="chart-title">
                <span>셋업별 손익</span>
                <Brain size={17} />
              </div>
              <div className="chart-wrap short">
                {setupChart.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={setupChart} margin={{ left: -14, right: 8, top: 8, bottom: 4 }}>
                      <CartesianGrid stroke="#29313b" strokeDasharray="4 4" />
                      <XAxis dataKey="setup" tickLine={false} axisLine={false} tick={{ fill: "#8d98a9", fontSize: 11 }} />
                      <YAxis tickLine={false} axisLine={false} tick={{ fill: "#8d98a9", fontSize: 11 }} />
                      <Tooltip contentStyle={{ background: "#151920", border: "1px solid #303946", borderRadius: 8 }} />
                      <Bar dataKey="pnl" fill="#60a5fa" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-chart">기록 없음</div>
                )}
              </div>
            </div>

            <div className="tag-cloud">
              {tagCloud.length ? (
                tagCloud.map(([tag, count]) => (
                  <span key={tag}>
                    #{tag} <b>{count}</b>
                  </span>
                ))
              ) : (
                <span>#태그</span>
              )}
            </div>
          </section>
        </section>

        <section className={`analytics-section tab-content ${activeWorkspaceTab === "analytics" ? "active" : ""}`}>
          <div className="section-head">
            <div>
              <span className="eyebrow">Analytics</span>
              <h2>기간별 분석</h2>
            </div>
            <div className="segmented">
              {(Object.keys(analyticsPeriodLabel) as AnalyticsPeriod[]).map((period) => (
                <button
                  type="button"
                  key={period}
                  className={analyticsPeriod === period ? "active" : ""}
                  onClick={() => setAnalyticsPeriod(period)}
                >
                  {analyticsPeriodLabel[period]}
                </button>
              ))}
            </div>
          </div>

          <div className="analytics-cards">
            <div>
              <span>실현 손익</span>
              <strong className={analyticsSummary.pnl >= 0 ? "positive" : "negative"}>
                {formatMoney(analyticsSummary.pnl, displayCurrency)}
              </strong>
            </div>
            <div>
              <span>승률</span>
              <strong>{analyticsSummary.winRate.toFixed(1)}%</strong>
            </div>
            <div>
              <span>평균 손익비</span>
              <strong>{analyticsSummary.avgRewardRisk.toFixed(2)}:1</strong>
            </div>
            <div>
              <span>거래 수</span>
              <strong>{analyticsSummary.trades}</strong>
            </div>
          </div>

          <div className="analytics-grid">
            <section className="chart-panel">
              <div className="chart-title">
                <span>자금 변화</span>
                <CalendarDays size={17} />
              </div>
              <div className="chart-wrap tall">
                {analyticsEquityCurve.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={analyticsEquityCurve} margin={{ left: -14, right: 8, top: 8, bottom: 4 }}>
                      <defs>
                        <linearGradient id="analytics-equity" x1="0" x2="0" y1="0" y2="1">
                          <stop offset="0%" stopColor="#2dd4bf" stopOpacity={0.75} />
                          <stop offset="100%" stopColor="#2dd4bf" stopOpacity={0.05} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke="#29313b" strokeDasharray="4 4" />
                      <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: "#8d98a9", fontSize: 11 }} />
                      <YAxis tickLine={false} axisLine={false} tick={{ fill: "#8d98a9", fontSize: 11 }} />
                      <Tooltip contentStyle={{ background: "#151920", border: "1px solid #303946", borderRadius: 8 }} />
                      <Area type="monotone" dataKey="pnl" stroke="#2dd4bf" fill="url(#analytics-equity)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-chart">해당 기간 청산 거래 없음</div>
                )}
              </div>
            </section>

            <section className="chart-panel">
              <div className="chart-title">
                <span>승률 / 손익비</span>
                <Gauge size={17} />
              </div>
              <div className="chart-wrap tall">
                {analyticsSummary.trades ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={analyticsMetricChart} margin={{ left: -14, right: 8, top: 8, bottom: 4 }}>
                      <CartesianGrid stroke="#29313b" strokeDasharray="4 4" />
                      <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: "#8d98a9", fontSize: 11 }} />
                      <YAxis tickLine={false} axisLine={false} tick={{ fill: "#8d98a9", fontSize: 11 }} />
                      <Tooltip contentStyle={{ background: "#151920", border: "1px solid #303946", borderRadius: 8 }} />
                      <Bar dataKey="value" fill="#60a5fa" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-chart">분석할 거래 없음</div>
                )}
              </div>
            </section>
          </div>
        </section>

        <section className={`calendar-section tab-content ${activeWorkspaceTab === "calendar" ? "active" : ""}`}>
          <div className="section-head">
            <div>
              <span className="eyebrow">Calendar</span>
              <h2>월간 매매 캘린더</h2>
            </div>
            <div className="month-switcher">
              <button type="button" onClick={() => shiftCalendarMonth(-1)} aria-label="이전 달">
                <ChevronLeft size={18} />
              </button>
              <input
                type="month"
                value={calendarMonth}
                onChange={(event) => setCalendarMonth(event.target.value || monthKey(new Date()))}
                aria-label="캘린더 월"
              />
              <button type="button" onClick={() => shiftCalendarMonth(1)} aria-label="다음 달">
                <ChevronRight size={18} />
              </button>
            </div>
          </div>

          <div className="calendar-board">
            <div className="calendar-weekdays">
              {["일", "월", "화", "수", "목", "금", "토", "주간"].map((day) => (
                <span key={day}>{day}</span>
              ))}
            </div>
            {calendarData.weeks.map((week) => {
              const weekReview = reviewByPeriod.get(reviewPeriodKey("weekly", week.startDate, week.endDate));
              const weekComplete = week.endDate <= todayDate;
              return (
                <div className="calendar-week" key={`${week.startDate}-${week.endDate}`}>
                  {week.days.map((day) => {
                    const dayReview = reviewByPeriod.get(reviewPeriodKey("daily", day.date, day.date));
                    const isFutureDay = day.date > todayDate;
                    return (
                      <div className={`calendar-day ${day.inMonth ? "" : "muted"} ${isFutureDay ? "future" : ""}`} key={day.date}>
                        <div className="calendar-day-top">
                          <strong>{day.day}</strong>
                          <span>{day.summary.trades}건</span>
                        </div>
                        <b className={isFutureDay ? "muted-pnl" : day.summary.pnl >= 0 ? "positive" : "negative"}>
                          {formatCompactMoney(day.summary.pnl, displayCurrency)}
                        </b>
                        <button
                          type="button"
                          className={dayReview?.completed ? "review-button done" : "review-button"}
                          disabled={isFutureDay}
                          onClick={() => openReview("daily", day.date, day.date)}
                        >
                          결산
                        </button>
                      </div>
                    );
                  })}
                  <div className="calendar-week-review">
                    <span>{week.startDate.slice(5)} ~ {week.endDate.slice(5)}</span>
                    <strong className={weekComplete ? (week.summary.pnl >= 0 ? "positive" : "negative") : "muted-pnl"}>
                      {formatCompactMoney(week.summary.pnl, displayCurrency)}
                    </strong>
                    <button
                      type="button"
                      className={weekReview?.completed ? "review-button done" : "review-button"}
                      disabled={!weekComplete}
                      onClick={() => openReview("weekly", week.startDate, week.endDate)}
                    >
                      주간
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="month-review-bar">
            <div>
              <span>월간 손익</span>
              <strong className={calendarData.monthEnd <= todayDate ? (calendarData.monthSummary.pnl >= 0 ? "positive" : "negative") : "muted-pnl"}>
                {formatCompactMoney(calendarData.monthSummary.pnl, displayCurrency)}
              </strong>
            </div>
            <button
              type="button"
              className={
                reviewByPeriod.get(reviewPeriodKey("monthly", calendarData.monthStart, calendarData.monthEnd))?.completed
                  ? "review-button done"
                  : "review-button"
              }
              disabled={calendarData.monthEnd > todayDate}
              onClick={() => openReview("monthly", calendarData.monthStart, calendarData.monthEnd)}
            >
              월간 결산
            </button>
          </div>
        </section>

        <section className={`review-list-section tab-content ${activeWorkspaceTab === "reviews" ? "active" : ""}`}>
          <div className="section-head">
            <div>
              <span className="eyebrow">Reviews</span>
              <h2>결산목록</h2>
            </div>
          </div>

          <div className="review-list">
            {reviews.length ? (
              (["daily", "weekly", "monthly"] as ReviewType[]).map((type) => {
                const items = reviews.filter((review) => review.type === type);
                return (
                  <section className="review-group" key={type}>
                    <h3>{reviewTypeLabel[type]} 결산</h3>
                    {items.length ? (
                      items.map((review) => {
                        const expanded = expandedReviewId === review.id;
                        return (
                          <article className="review-row" key={review.id}>
                            <button
                              type="button"
                              className="review-row-main"
                              onClick={() => setExpandedReviewId(expanded ? null : review.id)}
                            >
                              <div>
                                <span>{review.startDate === review.endDate ? review.startDate : `${review.startDate} ~ ${review.endDate}`}</span>
                                <strong>{review.title}</strong>
                              </div>
                              <span className={review.completed ? "review-state done" : "review-state"}>{review.completed ? "완료" : "작성중"}</span>
                            </button>
                            <button className="delete-button" type="button" onClick={() => deleteReview(review.id)} aria-label={`${review.title} 삭제`}>
                              <Trash2 size={17} />
                            </button>
                            {expanded ? (
                              <div className="review-detail">
                                <pre>{review.marketSummary}</pre>
                                <div className="text-grid">
                                  <label>
                                    잘한 점
                                    <textarea readOnly value={review.good} />
                                  </label>
                                  <label>
                                    보완할 점
                                    <textarea readOnly value={review.bad} />
                                  </label>
                                  <label>
                                    배운 점
                                    <textarea readOnly value={review.lesson} />
                                  </label>
                                  <label>
                                    다음 계획
                                    <textarea readOnly value={review.nextPlan} />
                                  </label>
                                </div>
                              </div>
                            ) : null}
                          </article>
                        );
                      })
                    ) : (
                      <div className="empty-list">{reviewTypeLabel[type]} 결산 없음</div>
                    )}
                  </section>
                );
              })
            ) : (
              <div className="empty-list">
                <ClipboardList size={28} />
                <span>작성된 결산 없음</span>
              </div>
            )}
          </div>
        </section>

        <section className={`ai-feedback-section tab-content ${activeWorkspaceTab === "aiFeedback" ? "active" : ""}`}>
          <div className="section-head">
            <div>
              <span className="eyebrow">Review Board</span>
              <h2>AI 피드백</h2>
            </div>
            <div className="ai-feedback-actions">
              <button className="ghost" type="button" onClick={refreshAiFeedbackPreflight} disabled={aiFeedbackPreflightLoading}>
                {aiFeedbackPreflightLoading ? "확인 중" : "상태 확인"}
              </button>
            </div>
          </div>

          <div className={`ai-feedback-preflight ${aiFeedbackPreflight?.canUseBars ? "ready" : "fallback"}`}>
            <div>
              <span>{aiFeedbackPreflight?.canUseBars ? "MT5 bars 준비됨" : "스크린샷 fallback 가능성"}</span>
              <strong>
                {aiFeedbackPreflight?.symbol || "첫 손실 거래"} ·{" "}
                {aiFeedbackPreflight?.mt5TerminalRunning ? "MT5 실행 중" : "MT5 꺼짐"}
              </strong>
              <p>{aiFeedbackPreflight?.message || "상태 확인을 누르면 Codex 심층 피드백에 쓸 D1~M1 차트 데이터 준비 상태를 확인합니다."}</p>
            </div>
            <div className="ai-feedback-preflight-bars">
              {(aiFeedbackPreflight?.timeframes || ["D1", "H4", "H1", "M30", "M15", "M5", "M1"].map((timeframe) => ({ timeframe, available: false, bars: 0 }))).map((item) => (
                <span className={item.available ? "ok" : "missing"} key={item.timeframe}>
                  {item.timeframe} {item.available ? `${item.bars} bars` : "없음"}
                </span>
              ))}
            </div>
          </div>

          {aiFeedbackBatchJob ? (
            <div className={`ai-feedback-batch ${aiFeedbackBatchJob.status || "queued"}`}>
              <div>
                <span>{aiFeedbackJobStatusLabel[aiFeedbackBatchJob.status || "queued"] || "작업 중"}</span>
                <strong>
                  {aiFeedbackBatchJob.completed ?? 0}/{aiFeedbackBatchJob.total ?? 0} 완료
                  {aiFeedbackBatchJob.failed ? ` · 실패 ${aiFeedbackBatchJob.failed}` : ""}
                </strong>
                {aiFeedbackBatchJob.currentSymbol ? (
                  <p>
                    현재 분석: {aiFeedbackBatchJob.currentSymbol}
                    {aiFeedbackBatchJob.currentTradeId ? ` · ${aiFeedbackBatchJob.currentTradeId}` : ""}
                  </p>
                ) : (
                  <p>HTF/Context/LTF 후보를 자동 선택해서 근거 보드를 생성합니다.</p>
                )}
              </div>
              {aiFeedbackBatchJob.errors?.length ? (
                <div className="ai-feedback-batch-errors">
                  {aiFeedbackBatchJob.errors.slice(-3).map((item) => (
                    <span key={`${item.tradeId}-${item.error}`}>{item.symbol || item.tradeId}: {item.error}</span>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}

          <div className="trade-list ai-feedback-list">
            {aiFeedbackTrades.length ? (
              aiFeedbackTrades.map((trade) => {
                const feedback = trade.aiFeedback;
                if (!feedback) return null;
                const derived = computeTrade(trade);
                const expanded = expandedFeedbackId === trade.id;
                const openTime = trade.brokerMeta?.openTime || trade.createdAt;
                const closeTime = trade.brokerMeta?.closeTime;
                const mt5Time = timeRangeLabel(openTime, closeTime, (value) => zonedDateTimeLabel(value, MT5_SERVER_TIME_ZONE)) || trade.date;
                const holdTime = holdingTimeLabel(trade);
                return (
                  <article className={`trade-row feedback-row ${expanded ? "selected" : ""}`} key={feedback.id}>
                    <button
                      className="trade-main"
                      type="button"
                      onClick={() => setExpandedFeedbackId(expanded ? null : trade.id)}
                    >
                      <div className="trade-symbol">
                        <span>{trade.market}</span>
                        <strong>{trade.symbol}</strong>
                      </div>
                      <div className={`direction-badge ${trade.direction}`}>{directionLabel[trade.direction]}</div>
                      <div className="trade-time">
                        <span>
                          <b>MT5</b>
                          {mt5Time}
                        </span>
                        {holdTime ? <em>홀딩 {holdTime}</em> : null}
                      </div>
                      <div>
                        <span>손익</span>
                        <strong className={derived.pnl >= 0 ? "positive" : "negative"}>{formatMoney(derived.pnl, trade.currency)}</strong>
                      </div>
                      <div>
                        <span>프레임</span>
                        <strong>{feedback.timeframes?.map((timeframe) => timeframe.timeframe).join("/") || "-"}</strong>
                      </div>
                      <div className={`status-pill ${trade.result}`}>{feedback.mentorReview ? "심층 피드백" : "MTF 근거 보드"}</div>
                    </button>

                    {expanded ? (
                      <div className="ai-feedback-detail">
                        {feedback.chartImage ? (
                          <figure className="ai-feedback-chart">
                            <img src={feedback.chartImage} alt={`${trade.symbol} MTF 복기 차트`} />
                            <figcaption>{feedback.chartImageName || "MTF 복기 차트"}</figcaption>
                          </figure>
                        ) : null}

                        <div className="ai-feedback-summary">
                          <div>
                            <span className="eyebrow">{feedback.mentorReview ? "Codex Mentor" : feedback.mentor}</span>
                            <h3>{feedback.mentorReview ? "심층 매매 피드백" : "MTF 근거 보드"}</h3>
                          </div>
                          <div className="ai-feedback-meta">
                            <span className={feedback.usedBars ? "source-live" : "source-fallback"}>
                              {feedback.usedBars ? "MT5 bars 분석" : "스크린샷 fallback"}
                            </span>
                            {feedback.version ? <span>{feedback.version}</span> : null}
                            <span>{compactDateTime(feedback.generatedAt)}</span>
                          </div>
                          {feedback.timeframes?.length ? (
                            <div className="ai-timeframe-strip">
                              {feedback.timeframes.map((timeframe) => (
                                <div className={timeframe.available ? "available" : "missing"} key={`${feedback.id}-${timeframe.timeframe}`}>
                                  <strong>
                                    {timeframe.role ? `${aiFeedbackRoleLabel[timeframe.role] || timeframe.role} ` : ""}
                                    {timeframe.timeframe}
                                  </strong>
                                  <span>{timeframe.available ? `${timeframe.location} · ${timeframe.trend}` : "데이터 없음"}</span>
                                  <small>
                                    {timeframe.sweep} / {timeframe.choch} / FVG {timeframe.fvg ? "Y" : "N"}
                                  </small>
                                  {timeframe.reason ? <small>{timeframe.reason}</small> : null}
                                </div>
                              ))}
                            </div>
                          ) : null}
                          <p>{feedback.mentorReview?.title || feedback.verdict}</p>
                          {feedback.mentorReview ? (
                            <p className="evidence-disclaimer">아래 심층 피드백은 Codex가 거래별 차트, MTF 구조, 일지 메모를 보고 직접 작성한 내용입니다.</p>
                          ) : (
                            <p className="evidence-disclaimer">
                              이 영역은 자동 감지 자료입니다. 최종 손익 원인과 시나리오 평가는 Codex가 거래별 차트와 일지를 보고 직접 작성합니다.
                            </p>
                          )}
                        </div>

                        {feedback.mentorReview?.paragraphs?.length ? (
                          <section className="mentor-review-card">
                            <div className="mentor-review-head">
                              <span className="eyebrow">Mentor Feedback</span>
                              <h3>{feedback.mentorReview.title}</h3>
                            </div>
                            <div className="mentor-review-body">
                              {feedback.mentorReview.paragraphs.map((paragraph, index) => (
                                <p key={`${feedback.id}-mentor-${index}`}>{paragraph}</p>
                              ))}
                            </div>
                          </section>
                        ) : null}

                        <div className="ai-feedback-grid">
                          {feedback.checklist.map((item) => (
                            <div className={`ai-check ${item.status}`} key={`${feedback.id}-${item.label}`}>
                              <span>{item.label}</span>
                              <strong>{aiFeedbackStatusLabel[item.status]}</strong>
                              <p>{item.detail}</p>
                            </div>
                          ))}
                        </div>

                      </div>
                    ) : null}
                  </article>
                );
              })
            ) : (
              <div className="empty-list">
                <Brain size={28} />
                <span>아직 생성된 복기 자료 없음</span>
              </div>
            )}
          </div>
        </section>

        <section className={`trades-section tab-content ${activeWorkspaceTab === "journal" ? "active" : ""}`}>
          <div className="list-head">
            <div>
              <span className="eyebrow">Records</span>
              <h2>저장된 매매</h2>
            </div>
            <div className="filters">
              <label className="search-box">
                <Search size={17} />
                <input value={query} placeholder="종목 검색" onChange={(event) => setQuery(event.target.value)} />
              </label>
              <select value={directionFilter} onChange={(event) => setDirectionFilter(event.target.value as "all" | Direction)}>
                <option value="all">전체 방향</option>
                <option value="long">Long</option>
                <option value="short">Short</option>
              </select>
              <select value={resultFilter} onChange={(event) => setResultFilter(event.target.value as "all" | TradeResult)}>
                <option value="all">전체 결과</option>
                <option value="open">보유</option>
                <option value="win">수익</option>
                <option value="loss">손실</option>
                <option value="breakeven">본전</option>
              </select>
              <div className="date-filter">
                <button
                  className={`date-filter-button ${dateFilter ? "active" : ""}`}
                  type="button"
                  onClick={() => {
                    if (dateFilter) setDateFilterMonth(dateFilter.slice(0, 7));
                    setDateFilterOpen((current) => !current);
                  }}
                  aria-expanded={dateFilterOpen}
                >
                  <CalendarDays size={17} />
                  {dateFilter ? dateFilter.split("-").join(".") : "날짜"}
                </button>
                {dateFilter ? (
                  <button
                    className="date-filter-clear"
                    type="button"
                    onClick={() => {
                      setDateFilter(null);
                      setDateFilterOpen(false);
                    }}
                    aria-label="날짜 필터 해제"
                  >
                    <X size={15} />
                  </button>
                ) : null}
                {dateFilterOpen ? (
                  <div className="mini-calendar" role="dialog" aria-label="매매 날짜 필터">
                    <div className="mini-calendar-head">
                      <button type="button" onClick={() => shiftDateFilterMonth(-1)} aria-label="이전 달">
                        <ChevronLeft size={16} />
                      </button>
                      <strong>{dateFilterMonth.replace("-", ".")}</strong>
                      <button type="button" onClick={() => shiftDateFilterMonth(1)} aria-label="다음 달">
                        <ChevronRight size={16} />
                      </button>
                    </div>
                    <div className="mini-calendar-weekdays">
                      {["S", "M", "T", "W", "T", "F", "S"].map((day, index) => (
                        <span key={`${day}-${index}`}>{day}</span>
                      ))}
                    </div>
                    <div className="mini-calendar-grid">
                      {dateFilterCalendar.map((day) => (
                        <button
                          className={`${day.inMonth ? "" : "muted"} ${day.hasTrades ? "has-trades" : ""} ${dateFilter === day.date ? "selected" : ""}`}
                          type="button"
                          key={day.date}
                          onClick={() => {
                            setDateFilter(day.date);
                            setDateFilterMonth(day.date.slice(0, 7));
                            setDateFilterOpen(false);
                          }}
                        >
                          <span>{day.label}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          </div>

          <div className="trade-list">
            {filteredTrades.length ? (
              filteredTrades.map((trade) => {
                const derived = computeTrade(trade);
                const expanded = editingId === trade.id;
                const activeDerived = expanded ? draftDerived : derived;
                const openTime = trade.brokerMeta?.openTime || trade.createdAt;
                const closeTime = trade.brokerMeta?.closeTime;
                const mt5Time = timeRangeLabel(openTime, closeTime, (value) => zonedDateTimeLabel(value, MT5_SERVER_TIME_ZONE)) || trade.date;
                const koreaTime = timeRangeLabel(openTime, closeTime, (value) => zonedDateTimeLabel(value, "Asia/Seoul"));
                const holdTime = holdingTimeLabel(trade);
                return (
                  <article className={`trade-row ${editingId === trade.id ? "selected" : ""}`} key={trade.id}>
                    <button
                      className="trade-main"
                      type="button"
                      onClick={() => {
                        if (editingId === trade.id) {
                          setEditingId(null);
                          setNotice("일지를 닫았습니다.");
                          return;
                        }
                        setActiveTradingSymbol(trade.symbol);
                        setEditingId(trade.id);
                        setDraft(draftFromTrade(trade));
                        setActiveWorkspaceTab("journal");
                        setNotice("기록을 불러왔습니다.");
                      }}
                    >
                      <div className="trade-symbol">
                        <span>{trade.market}</span>
                        <strong>{trade.symbol}</strong>
                      </div>
                      <div className={`direction-badge ${trade.direction}`}>{directionLabel[trade.direction]}</div>
                      <div className="trade-time">
                        <span>
                          <b>MT5</b>
                          {mt5Time}
                        </span>
                        <span>
                          <b>KST</b>
                          {koreaTime || mt5Time}
                        </span>
                        {holdTime ? <em>홀딩 {holdTime}</em> : null}
                      </div>
                      <div>
                        <span>손익</span>
                        <strong className={derived.pnl >= 0 ? "positive" : "negative"}>{formatMoney(derived.pnl, trade.currency)}</strong>
                        <em className={`trade-pnl-percent ${derived.pnlPercent >= 0 ? "positive" : "negative"}`}>{formatPercent(derived.pnlPercent)}</em>
                      </div>
                      <div>
                        <span>손익비</span>
                        <strong>{derived.rewardRisk > 0 ? `${derived.rewardRisk.toFixed(2)}:1` : "-"}</strong>
                      </div>
                      <div className={`status-pill ${trade.result}`}>
                        {trade.result === "win" && <CheckCircle2 size={15} />}
                        {resultLabel[trade.result]}
                      </div>
                    </button>
                    <button className="delete-button" type="button" onClick={() => deleteTrade(trade.id)} aria-label={`${trade.symbol} 삭제`}>
                      <Trash2 size={17} />
                    </button>
                    {expanded ? (
                      <div className="trade-detail-editor">
                        <ChartImageEditor
                          image={draft.screenshot}
                          imageName={draft.screenshotName}
                          annotations={draft.screenshotAnnotations}
                          onImageUpload={handleScreenshotUpload}
                          onDrop={handleDrop}
                          onRemoveImage={() => {
                            setDraft((current) => ({
                              ...current,
                              screenshot: undefined,
                              screenshotName: undefined,
                              screenshotAnnotations: [],
                            }));
                          }}
                          onAnnotationsChange={(screenshotAnnotations) => setDraft((current) => ({ ...current, screenshotAnnotations }))}
                        />

                        <div className="auto-record-card compact">
                          <div>
                            <span className="eyebrow">MT5 Synced Journal</span>
                            <strong>
                              {draft.symbol || trade.symbol} · {directionLabel[draft.direction]}
                            </strong>
                            <p>{tradeTimeLabel(draft)}</p>
                          </div>
                          <div className="auto-record-grid editable">
                            <div className="record-metric">
                              <span>Entry</span>
                              <b>{draft.entryPrice ? number.format(draft.entryPrice) : "-"}</b>
                            </div>
                            <label className="record-metric">
                              <span>TP</span>
                              <input
                                inputMode="decimal"
                                value={draft.targetPrice || ""}
                                onChange={(event) => setDraftField("targetPrice", toNumber(event.target.value))}
                              />
                            </label>
                            <label className="record-metric">
                              <span>SL</span>
                              <input
                                inputMode="decimal"
                                value={draft.stopPrice || ""}
                                onChange={(event) => setDraftField("stopPrice", toNumber(event.target.value))}
                              />
                            </label>
                            <div className="record-metric">
                              <span>거래량</span>
                              <b>{draft.quantity ? `${number.format(draft.quantity)} lot` : "-"}</b>
                            </div>
                            <div className="record-metric">
                              <span>PnL</span>
                              <b className={activeDerived.pnl >= 0 ? "positive" : "negative"}>{formatMoney(activeDerived.pnl, draft.currency)}</b>
                              {formatPnlComponents(draft) ? <small>{formatPnlComponents(draft)}</small> : null}
                            </div>
                            <div className="record-metric">
                              <span>PnL %</span>
                              <b className={activeDerived.pnlPercent >= 0 ? "positive" : "negative"}>{formatPercent(activeDerived.pnlPercent)}</b>
                            </div>
                            <div className="record-metric">
                              <span>손익비</span>
                              <b>{activeDerived.rewardRisk > 0 ? `${activeDerived.rewardRisk.toFixed(2)}:1` : "-"}</b>
                            </div>
                            <div className="record-metric">
                              <span>계획 리스크</span>
                              <b>{formatMoney(activeDerived.plannedRisk, draft.currency)}</b>
                            </div>
                            <div className="record-metric">
                              <span>실제 리스크</span>
                              <b>{activeDerived.plannedRisk > 0 ? formatPercent(activeDerived.actualRiskPercent) : "-"}</b>
                            </div>
                          </div>
                        </div>

                        <div className="text-grid">
                          <label>
                            진입 근거
                            <textarea value={draft.thesis} onChange={(event) => setDraftField("thesis", event.target.value)} />
                          </label>
                          <label>
                            리스크 계획
                            <textarea value={draft.riskPlan} onChange={(event) => setDraftField("riskPlan", event.target.value)} />
                          </label>
                          <label>
                            잘한 점
                            <textarea value={draft.good} onChange={(event) => setDraftField("good", event.target.value)} />
                          </label>
                          <label>
                            놓친 점
                            <textarea value={draft.bad} onChange={(event) => setDraftField("bad", event.target.value)} />
                          </label>
                          <label className="span-two">
                            다음 원칙
                            <textarea value={draft.lesson} onChange={(event) => setDraftField("lesson", event.target.value)} />
                          </label>
                        </div>

                        <div className="quality-grid">
                          <label>
                            확신도 <strong>{draft.confidence}</strong>
                            <input
                              type="range"
                              min="1"
                              max="5"
                              value={draft.confidence}
                              onChange={(event) => setDraftField("confidence", toNumber(event.target.value))}
                            />
                          </label>
                          <label>
                            규율 <strong>{draft.discipline}</strong>
                            <input
                              type="range"
                              min="1"
                              max="5"
                              value={draft.discipline}
                              onChange={(event) => setDraftField("discipline", toNumber(event.target.value))}
                            />
                          </label>
                          <label>
                            감정
                            <select value={draft.emotion} onChange={(event) => setDraftField("emotion", event.target.value)}>
                              {emotionOptions.map((emotion) => (
                                <option key={emotion}>{emotion}</option>
                              ))}
                            </select>
                          </label>
                          <label>
                            등급
                            <select value={draft.grade} onChange={(event) => setDraftField("grade", event.target.value)}>
                              {gradeOptions.map((grade) => (
                                <option key={grade}>{grade}</option>
                              ))}
                            </select>
                          </label>
                        </div>

                        <div className="form-footer">
                          <span>{notice}</span>
                          <button className="primary" type="button" onClick={saveDraftRecord}>
                            <Save size={18} />
                            일지 저장
                          </button>
                        </div>
                      </div>
                    ) : null}
                  </article>
                );
              })
            ) : (
              <div className="empty-list">
                <ClipboardList size={28} />
                <span>저장된 기록 없음</span>
              </div>
            )}
          </div>
        </section>

        {activeReviewDraft ? (
          <div className="review-drawer-backdrop" role="presentation" onClick={() => setActiveReviewDraft(null)}>
            <aside className="review-drawer" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}>
              <div className="review-drawer-head">
                <div>
                  <span className="eyebrow">{reviewTypeLabel[activeReviewDraft.type]} Review</span>
                  <h2>{activeReviewDraft.title}</h2>
                </div>
                <button type="button" onClick={() => setActiveReviewDraft(null)} aria-label="결산 닫기">
                  <X size={18} />
                </button>
              </div>

              <label>
                매매 요약
                <textarea
                  className="summary-textarea"
                  value={activeReviewDraft.marketSummary}
                  onChange={(event) => setReviewDraftField("marketSummary", event.target.value)}
                />
              </label>
              <div className="text-grid">
                <label>
                  잘한 점
                  <textarea value={activeReviewDraft.good} onChange={(event) => setReviewDraftField("good", event.target.value)} />
                </label>
                <label>
                  보완할 점
                  <textarea value={activeReviewDraft.bad} onChange={(event) => setReviewDraftField("bad", event.target.value)} />
                </label>
                <label>
                  배운 점
                  <textarea value={activeReviewDraft.lesson} onChange={(event) => setReviewDraftField("lesson", event.target.value)} />
                </label>
                <label>
                  다음 계획
                  <textarea value={activeReviewDraft.nextPlan} onChange={(event) => setReviewDraftField("nextPlan", event.target.value)} />
                </label>
              </div>
              <label>
                자기 평가 <strong>{activeReviewDraft.score}</strong>
                <input
                  type="range"
                  min="1"
                  max="5"
                  value={activeReviewDraft.score}
                  onChange={(event) => setReviewDraftField("score", toNumber(event.target.value))}
                />
              </label>
              <div className="form-footer">
                <span>{activeReviewDraft.completed ? "작성 완료된 결산입니다." : "저장하거나 작성 완료로 표시할 수 있습니다."}</span>
                <div className="drawer-actions">
                  <button type="button" onClick={() => saveReview(false)}>
                    <Save size={17} />
                    임시 저장
                  </button>
                  <button className="primary" type="button" onClick={() => saveReview(true)}>
                    <CheckCircle2 size={17} />
                    작성 완료
                  </button>
                </div>
              </div>
            </aside>
          </div>
        ) : null}
      </main>
    </div>
  );
}

export default App;
