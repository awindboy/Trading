export type ReplayTimeframe = "M1" | "M5" | "M15" | "M30" | "H1";
export type ReplayDirection = "long" | "short";
export type ReplayScenarioScope =
  | "EXTERNAL_CONTINUATION"
  | "INTERNAL_ROTATION"
  | "EXTERNAL_REVERSAL";
export type DrawingKind = "ob" | "fvg" | "poi" | "liquidity" | "bos" | "choch" | "sweep" | "trend" | "note";

export type M1Bar = {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  spread: number;
};

export type ReplayBar = M1Bar & {
  confirmed: boolean;
};

export type ReplayDataset = {
  name: string;
  size: number;
  symbol: string;
  timeframe: string;
  point: number;
  firstTime: number;
  lastTime: number;
  bars: number;
};

export type ReplayDataResponse = {
  ok: boolean;
  error?: string;
  dataset: ReplayDataset;
  symbol: string;
  timeframe: "M1";
  replayStart: number;
  replayEnd: number;
  sourceStart: number;
  bars: M1Bar[];
  replayBars: number;
  warmupBars: number;
};

export type PriceAnchor = {
  time: number;
  price: number;
};

export type ReplayDrawing = {
  id: string;
  kind: DrawingKind;
  timeframe: ReplayTimeframe;
  direction?: ReplayDirection;
  label: string;
  color: string;
  createdAt: number;
  anchors: PriceAnchor[];
  evidenceStatus?: "validated" | "manual";
};

export type ScenarioSnapshot = {
  id: string;
  createdAt: number;
  title: string;
  scope?: ReplayScenarioScope;
  direction: ReplayDirection | "neutral";
  mapTimeframe: ReplayTimeframe;
  sourceTimeframe: ReplayTimeframe;
  objective: string;
  invalidation: string;
  waitingFor: string;
  thesis: string;
};

export type ReplayOrderPlan = {
  id: string;
  createdAt: number;
  cancelledAt?: number;
  cancelReason?: string;
  sourceEvidenceValid?: boolean;
  entryEvidenceValid?: boolean;
  stopEvidenceValid?: boolean;
  semanticEvidenceValid?: boolean;
  performanceEligible?: boolean;
  semanticAudit?: {
    elements: Record<string, boolean>;
    failureCodes: string[];
    failureReasons: string[];
  };
  requiredStructuralStop?: number;
  evidenceIssue?: string;
  direction: ReplayDirection;
  executionModel?: "refined-ob-retest" | "delivery-fvg-replacement" | "delivery-fvg-addon";
  orderType: "market" | "limit";
  entry: number;
  triggerInvalidation?: number;
  scenarioInvalidation?: number;
  stop: number;
  objectivePrice?: number;
  targetBuffer?: number;
  target: number;
  rationale: string;
  scenarioId?: string;
  scenarioScope?: ReplayScenarioScope;
};

export type ReplayOrderState = ReplayOrderPlan & {
  status: "pending" | "filled" | "win" | "loss" | "cancelled";
  filledAt?: number;
  closedAt?: number;
  exitPrice?: number;
  resultR?: number;
  intrabarAmbiguous?: boolean;
};

export type ReplayEvent = {
  id: string;
  time: number;
  type: "session" | "scenario" | "drawing" | "order" | "fill" | "win" | "loss" | "note";
  title: string;
  detail?: string;
};

export type ReplaySession = {
  id: string;
  name: string;
  symbol: string;
  dataset: string;
  weekStart: number;
  weekEnd: number;
  cursorTime: number;
  maxSeenTime: number;
  timeframe: ReplayTimeframe;
  speed: number;
  createdAt: string;
  updatedAt: string;
  drawings: ReplayDrawing[];
  scenarios: ScenarioSnapshot[];
  orders: ReplayOrderPlan[];
  events: ReplayEvent[];
};

export type ReplaySessionSummary = {
  id: string;
  name: string;
  symbol: string;
  dataset: string;
  weekStart: number;
  createdAt: string;
  updatedAt: string;
  cursorTime: number;
  maxSeenTime: number;
  eventCount: number;
  drawingCount: number;
  orderCount: number;
};
