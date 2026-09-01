# V8 Development Handoff

Last updated: `2026-09-01`
Current phase: `V8-A-N NORMALIZED FRESH-HIGH STRATEGY RESEARCH`
Production authority: `NONE`
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## 1. Immediate authority state

### V8-A
Frozen absolute-$10 movement control.

### V8-A2
Retained absolute-$10 86-feature survival challenger and rank/state layer. Not promoted.

### V8-A-N
New retained ATR-normalized movement challenger. Current active research branch.

### V8-C LONG
Provisional frozen, MT5 real-tick verified. Do not change entry.

### Fixed-$10 fresh75
Development control only. Direction remains around ~59% on consumed 2025/2026 evidence. Fixed $10 SL with ~$13 TP produced a useful ~1.30R comparison point, but no authority.

## 2. Why V8-A-N was opened

Fixed $10 changed effective difficulty dramatically across years.

All-M5 P15 fixed-$10 base rate:

```text
2022 0.57%
2023 0.38%
2024 1.04%
2025 7.34%
2026 28.83%
```

For `2 * causal M5 ATR14`:

```text
2022 18.41%
2023 18.77%
2024 18.61%
2025 18.50%
2026 18.19%
```

P30/P60 show the same stabilization.

Future excursion / ATR distribution is also highly stable across years.

This is strong evidence that volatility normalization addresses a real target-definition problem.

## 3. Prototype model status

A2 pipeline parity was reproduced before normalized training.

Prototype V8-A-N models exist for:

```text
0.75, 1.00, 1.25, 1.50, 1.75, 2.00, 2.50, 3.00 ATR
```

They are research-only.

Independent distance models have rare monotonicity violations. Final model architecture must enforce distance/horizon ordering.

## 4. New fresh-high movement populations

### 1.25 ATR fresh75

```text
2024 N1958, P15 hit 81.38%
2025 N2230, P15 hit 79.03%
2026 N1690, P15 hit 77.09%
```

### 1.50 ATR fresh75

```text
2024 N809, P15 hit 81.64%
2025 N834, P15 hit 77.85%
2026 N551, P15 hit 80.04%
```

### 2.00 ATR fresh75

```text
2024 N180, P15 hit 80.90%
2025 N151, P15 hit 73.29%
2026 N131, P15 hit 75.19%
```

All have very high 30m/60m movement realization.

The next task is to choose/freeze a normalized movement trigger using structural/movement criteria, not direction P/L.

## 5. Old fixed-$10 fresh75 remains a control

Original fresh75:

```text
previous fixed-$10 P15 <75%
current fixed-$10 P15 >=75%
```

On that population, extending fixed SL=$10 to TP=$13 gave:

```text
2025 WR52.63% EV +0.207R
2026 WR52.07% EV +0.198R
```

TP=$13.5 stayed just above 50% in both years but is the observed boundary.

Use `$10/$13` as a comparison control only.

Do not optimize more decimal TP values.

## 6. Critical next-stage separation

The normalized strategy must be built in this order:

```text
N1 normalized movement trigger
          ↓ freeze
N2 direction engine
          ↓ freeze
N3 ATR-consistent SL/TP
          ↓ freeze
N4 complete-strategy comparison
```

Do not use final P/L to select N1.

Do not copy the old fresh75 direction engine into N2 without revalidation.

Do not tune N3 while changing N2.

## 7. N1 candidate decision criteria

Compare `1.25 / 1.50 / 2.00 ATR` fresh75 populations on:

- P15/P30/P60 realized movement precision;
- count per year/month;
- year stability;
- trigger clustering and spacing;
- ATR distribution;
- session distribution;
- probability/rank distribution;
- implementation complexity;
- independence from one short volatility burst.

No direction labels or P/L in N1 selection.

## 8. N2 direction research

After N1 is frozen, rebuild direction research for that exact population.

Candidate information families may include:

- M1/M5 candle sequence;
- M5/M15/H1 partial and completed geometry;
- stochastic/momentum/exhaustion;
- signed activity/tick-volume;
- swing/liquidity location;
- session as context;
- raw quote microstructure if needed;
- centralized futures/macro information only as a later new-source branch.

Target remains mandatory LONG/SHORT unless a separate selective-strategy branch is explicitly opened.

## 9. N3 ATR-consistent economics

Only after direction freeze.

Initial simple family should be preregistered, e.g.:

```text
SL 1.0 ATR / TP 1.0 ATR
SL 1.0 ATR / TP 1.25 ATR
SL 1.0 ATR / TP 1.5 ATR
```

Potential alternative SL scales may be opened only under a new predeclared experiment, not by dense post-hoc grid rescue.

Report actual dollar SL/TP distributions as well as R.

## 10. Evidence status

2022-2026 are development evidence for V8-A-N.

Do not claim independent production validation from these years.

`GOLD# 2021 remains locked`.

Before reserve use, the complete trigger + direction + risk/payoff architecture must be frozen and MT5 execution semantics defined.

## 11. Next session

1. refresh GitHub HEAD;
2. read AGENTS/HANDOFF;
3. open `V8_A_N_ATR_NORMALIZED_MOVEMENT_RESEARCH_20260901.md`;
4. run N1 structural trigger comparison only;
5. freeze one trigger family;
6. then begin N2 direction engine research;
7. do not touch 2021.
