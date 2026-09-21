# V10 research instructions

Last synchronized: `2026-09-21`
Status: `ACTIVE RESEARCH / HA-PRIMARY / NORMALIZED-STATE FORWARD SHADOW`
Production authority: `NONE`
Market: `GOLD# ONLY`

## 1. Resume order

1. refresh GitHub `main`;
2. read repository `AGENTS.md`;
3. read `V10_DOCUMENT_AUTHORITY_MAP_20260921.md`;
4. read `HANDOFF_V10.md`;
5. read `RESEARCH_STATE_V10.md`;
6. read `V10_NEXT_RESEARCH_CONTRACT_NORMALIZED_STATE_FORWARD_20260921.md`;
7. inspect only the compact result packs listed by the authority map.

Earlier V10 checkpoints are evidence, not current routing. They cannot override these files.

## 2. Research objective

V10 keeps H4 FAST HA as the primary campaign and participation clock. The active problem is:

> Can causal, liquidity-normalized state identify avoidable high-risk Children while preserving the rare persistent-run right tail?

The objective is not to predict every next HA, label a universal market regime, or maximize classification accuracy.

## 3. Frozen comparator

The current historical comparator is the reproduced R4/R5/R7G chain:

```text
raw M1
-> causal H4/M15/M30/H1 reconstruction
-> R4 0/1/3 base participation
-> R5 STOP and conditional-R EV context
-> R7G prior-exited 180-H4 feedback sizing overlay
-> Child Hard SL
-> first opposite completed FAST H4 HA campaign exit
```

R7G changes exposure, not the selected Child set. Historical 2024-2026 results are consumed evidence and remain a comparator, not a promoted strategy.

The exact replay and full embedded EAs are executable research artifacts only. The user's MT5 export confirms a real tester run occurred; market-closed order failures are an execution-lifecycle issue deferred to a later EA upgrade. Full row-level production parity is not certified.

## 4. Causal input and observation contract

- Raw M1 is the primary source.
- Rebuild higher timeframes chronologically from the revealed prefix.
- Use only completed information at each decision.
- Images cannot create or veto a trade.
- Canonical decision key is `signal_id + effective decision timestamp`.
- Execution timestamp is not the signal timestamp.
- Hard SL is fixed before entry and is never widened.
- A stopped Child remains dead.
- Preserve exact-tick ambiguity instead of inventing intraminute order.

Observation cadence for discretionary replay remains:

```text
FLAT / ordinary observation       H1 plus H4 context
SERIOUS CANDIDATE                 sequential completed M15
entry/SL ambiguity                M5/M1 only when needed
Parent-Journey holding            every H1, M15 on warning
Local Bridge                      M15-centered
```

## 5. Liquidity-era normalization

Absolute Gold ranges are not portable across years. Current research must use:

- same-timeframe causal Wilder ATR180 for distance, span, slope, and provisional HA margin;
- scale-free fractions for MA-ribbon support, ordering, and penetration;
- prior-only references when a percentile is required;
- separate calendar-era reporting before pooling.

Do not transfer a raw-dollar or raw-point threshold from one era to another.

## 6. Current shadow coordinates

### 6.1 Frozen narrow seed-defense shadow

`V10_INTRAH4_SEED1_Q10_DEFENSE` is observation-only:

```text
existing newest R7G 1-unit Child
+ still alive at forming-H4 +60m
+ direction-adjusted provisional FAST-HA margin / prior H4 ATR180
  <= -0.1641973584634039
-> hypothetical exit of that newest 1-unit Child only
```

No order, catch-up, older Child, or 3-unit Child is changed.

### 6.2 Normalized MA-ribbon state

The retained representation family is:

```text
H4 WMA20 OC2 normalized slope/span
H1 WMA20 OC2 normalized edge/span
M15 SMA/WMA60 support/order/deterioration
```

This family is shadow state only. No MA type, line count, threshold, or intersection is an entry veto.

## 7. Rejected or closed action rules

- broad regime classifier as admission authority;
- generic negative-R head;
- direct next-HA prediction as entry/exit authority;
- general intrabar NHA early exit;
- action-value Ridge exit model;
- progression proof gate;
- damage-repair lockout;
- fixed breached-line trend-death rule;
- universal direction exclusion;
- hidden cooldown, retry count, minimum-R, no-chase, or campaign cap.

Closed rules remain closed unless a new contract supplies genuinely new chronology or a new causal mechanism. Threshold retuning on the same data is not new evidence.

## 8. Promotion boundary

No shadow coordinate may alter R7G orders until all of the following exist:

1. fixed semantics before observation;
2. exact Python/MQL feature parity where EA implementation is intended;
3. future-only event logging after the consumed cutoff;
4. stop reduction and stop-streak evidence;
5. explicit positive-Child and L6+ right-tail regret;
6. structural-R, raw PnL, cost, and committed-risk accounting;
7. concentration and run-block uncertainty checks;
8. a separate promotion decision.

## 9. Repository discipline

- Current authority is replaced, not extended with new override blocks.
- Compact evidence belongs in `docs/ea/v10/results/`.
- Generated row ledgers and grids belong in ignored `output/`.
- Retained code and its purpose are listed in `research/v10/README.md`.
- Git history is the archive for deleted predecessor contracts and bulky evidence.
