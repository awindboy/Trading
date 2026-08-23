# V2 Entry-Survival Research Synthesis — D154A through D154L

Status: CURRENT LONG-FORM HANDOFF  
Date: 2026-08-23  
Authority: `docs/ea/v2/AGENTS_V2.md`

This document is the compact long-session research memory for the current V2 Entry-survival program. It does not change strategy authority.

## 1. Control and objective

V2 control remains:

```text
EXTERNAL_CONTINUATION only
BASELINE_NO_REGIME_GATE
ROOT_OB_DISTAL_20
LAST_OPPOSITE_OB + FVG_ORIGIN_OB
PD = reference only
same-entry Root merge
same-direction add-ons
opposite-direction coexistence blocked
no look-ahead
```

Entry chain:

```text
objective liquidity
-> H1/M30 continuation map
-> pre-existing H1/M30/M15 Root OB
-> actual Root contact
-> valid Root-reaction sweep
-> meaningful M1 body CHoCH
-> fresh same causal-leg FVG
-> widest eligible FVG
-> first retest
-> Entry
-> normalized SL
-> frozen structural objective TP
```

Research control:

```text
post-+1R reference = V3E BANK_2R_LOCK_ONE (mode 9)
EM = OFF
D151 causal audit = ON
```

Final objective is not gross R alone. The strategy should achieve realized WR >=50% as a baseline condition, average winner meaningfully >1R, positive cost-adjusted expectancy, and robustness across markets/periods. A flat 1R exit is not an acceptable final solution.

## 2. Available research panel

Only GOLD currently has multi-year history in the standardized research panel.

```text
GOLD23    2023-01-01 .. 2023-12-21
GOLD24    2024
GOLD25    2025
BTC25     BTCUSD 2025
SILVER25  SILVER 2025
CADJPY25  CADJPY 2025
```

Never invent BTC24, SILVER24 or CADJPY24 evidence.

## 3. Stage separation

Keep these causal questions separate:

```text
Fill -> +1R       = Entry survival
+1R -> +2R        = winner continuation
post +2R          = exit architecture
execution parity  = implementation correctness
portfolio risk    = exposure / clustering
```

A variable discovered in one stage is not automatically reusable in another.

## 4. Winner-continuation / exit background

### D145

Among trades already at +1R, lower M30 protected-to-current-external progress was associated with more room to reach +2R.

Direction of relationship:
- 6/6 market-year aggregates;
- 11/11 comparable market-year x direction cells.

This remains a **winner-continuation variable**, not Entry authority.

### D152 / V3E

`BANK_2R_LOCK_ONE` remains the provisional post-+1R reference.

GOLD25:
```text
53 closed
WR 52.83%
avg winner 1.328R
expectancy +0.203R
total +10.783R
DD 6.807R
Fill->+1R 30/53 = 56.6%
```

BTC25:
```text
125 closed + 2 censored in original D152
WR 44.0%
avg winner 1.225R
expectancy about -0.022R
Fill->+1R 60/127 = 47.2%
```

Post-+1R conversion was already high. Entry survival remained the primary bottleneck.

## 5. Entry-survival research chain

### D148 — failure taxonomy

GOLD23-25, 167 fills; 78 SL-first.

Among SL-first:
```text
27/78 later recovered original +1R before map support loss
51/78 map support failed first
```

Of the 27 recoveries:
```text
9 retained original Root
18 original Root invalidated before recovery
```

Interpretation:
- many losses are genuine broader-premise failures;
- a meaningful minority are local timing/stop-sensitivity failures;
- taxonomy only, not a rescue rule.

### D149 — Episode Management

EM did not solve the general Entry-survival problem. Keep EM OFF during structural Entry research.

### D151 — causal platform

D151 established exact actual-fill outcome tracking:

```text
Stage A: Fill -> +1R
Stage B: +1R -> +2R
Stage C: post +2R
```

Right-censored outcomes remain censored. Execution-divergent runs cannot support profitability conclusions.

### D154A — M1 state at Fill

GOLD23:
```text
TRANSITION      49/107 = 45.8%
opposite mature 35/62  = 56.5%
same mature      6/11  = 54.5%
```

Simple Fill-time M1 maturity gate rejected.

### D154B — wait for same-direction M1 INITIAL_BOS

Transition fills delayed until first same-direction INITIAL_BOS:
- did not rescue losses;
- converted multiple baseline winners into failures.

Rejected.

### D154C — confirmation -> fresh same-direction FVG -> first retracement

Paired baseline/shadow outcome was effectively identical in discovery.

Rejected as a replacement Entry trigger.

### D154D — new Root after SL-first

Discovery new-Root recovery looked strong but collapsed OOS.

Rejected.

### D154F — exact M1 Root->Sweep->CHoCH->FVG causal lineage

Direct frozen-boundary relation did not produce a robust general gate.

Discovery `TRANSITION at sweep` looked very weak, but validation failed and reversed in BTC/CADJPY.

Rejected as Entry veto.

### D154G — HTF Root birth lineage / stale owner

Primary stale prior-owner hypothesis had zero observed exposure:

```text
PRIOR_SAME_TF_OWNER = 0 / 457 fills
```

Same-owner BOS refresh proxy:
- strong discovery weakness;
- validation failed;
- very low coverage.

Static H1/M30 alignment also failed to generalize.

Rejected.

### D154H — ordered H1/M30 replay

D154H stopped compressing HTF state into one scalar and reconstructed ordered H1/M30 INITIAL_BOS/BOS/PROTECTED_BREAK events plus PLAN/ROOT_CONTACT/SWEEP/CHOCH/PENDING/FILL anchors.

GOLD23 discovery found:
```text
post-contact same-direction H1/M30 BOS before CHOCH
exposed: 4/17 = 23.5%
clean:  30/48 = 62.5%
```

This suggested the Root reaction may already have delivered HTF continuation before the M1 trigger completes.

### D154I — validation of post-contact HTF delivery event

Frozen primary:
```text
ROOT_CONTACT < same-direction H1/M30 continuation BOS <= accepted CHOCH
```

Validation pooled:
```text
BOS exposed 25/74 = 33.8%
clean      137/317 = 43.2%
```

But GOLD24 and BTC25 reversed direction. No universal veto.

Secondary `H1_PRIMARY_M30_TRANSITION at SWEEP` also failed.

Rejected.

### D154J — uncompressed HTF delivery geometry

Contrast: GOLD25 vs CADJPY25.

Hypothesis that CADJPY underperformed because Entry was later / more exhausted inside protected->external HTF geometry was rejected.

At Fill, descriptive medians:
```text
plan progress:
GOLD25    ~0.585
CADJPY25  ~0.501

remaining fraction:
GOLD25    ~0.381
CADJPY25  ~0.499

remaining distance in initial R:
GOLD25    ~1.59R
CADJPY25  ~2.44R
```

CADJPY entered with more, not less, HTF room.

Even matched broad structure retained a large gap. Example H1-primary + M30-aligned LONG:
```text
GOLD25    about 70%
CADJPY25  about 18.5%
```

Current HTF geometry alone cannot explain cross-market transfer failure.

### D154K — cross-scale reaction / noise

Question: are strategy geometry and broker friction operating at different scale relative to the causal M1 Root reaction?

Key discovery pair:

```text
                         GOLD25      CADJPY25
Fill->+1R                56.6%       26.5%
1R / reaction M1 TR      11.67       12.36
Root width / TR           6.03        6.45
reaction efficiency       0.038       0.038
FVG width / TR            0.628       0.794
```

Core strategy geometry was broadly similar relative to local M1 movement.

Execution friction was not:

```text
spread / reaction TR      0.342       2.125
spread / 1R               0.028       0.150
spread / FVG              0.462       2.688
```

Median spread ticks were similar:
```text
GOLD25    40 ticks
CADJPY25  42 ticks
```

But local movement/risk scale was much smaller in CADJPY:
```text
reaction TR ticks:
GOLD25    ~126
CADJPY25  ~20

risk ticks:
GOLD25    ~1748
CADJPY25  ~274
```

Interpretation:
- not simply "CADJPY structure is smaller";
- strategy geometry relative to local movement is comparable;
- broker spread relative to that geometry is radically different.

This did **not** establish a per-trade spread filter. Winner/loss splits were not consistently monotonic within markets.

### D154L — independent cost-scale transfer validation

Frozen primary metric:
```text
market-period median spread / Root-contact->CHOCH mean M1 TR
```

Hypothesis:
```text
higher relative execution friction -> lower Fill->+1R survival
```

Validation cells:
- GOLD24
- BTC25
- SILVER25

Historical context:
- GOLD23

Exact medians:

```text
cell       survival     spread/TR   spread/R    spread/FVG
GOLD23     34/65=52.3%  0.5487      0.0423      0.8966
GOLD24     24/52=46.2%  0.5723      0.0425      0.8311
GOLD25     30/53=56.6%  0.3417      0.0281      0.4615
BTC25      60/127=47.2% 1.0147      0.0632      1.0256
SILVER25   18/46=39.1%  1.7011      0.1471      2.0992
CADJPY25   30/113=26.5% 2.1255      0.1496      2.6875
```

2025 cross-market ordering was exact:

```text
relative friction:
GOLD < BTC < SILVER < CADJPY

Entry survival:
GOLD > BTC > SILVER > CADJPY
```

Status:
```text
cross-market cost-scale mechanism = SUPPORTED
per-trade spread filter           = NOT SUPPORTED
universal year/regime determinant = NOT ESTABLISHED
baseline strategy change          = NONE
```

The GOLD years show that cost scale does not explain all temporal regime variation. Cost is a transfer/viability mechanism, not a complete alpha model.

## 6. Current strongest interpretation

The strongest surviving cross-market mechanism is:

> The deterministic M1 Entry architecture can represent similar market geometry relative to local price movement, yet become structurally less viable when broker bid/ask friction is large relative to the causal M1 reaction, FVG width, and 1R.

This has a plausible barrier-race mechanism:
- LONG fills on ASK but exits/SL observations are executable through BID;
- SHORT fills on BID but exits/SL observations are executable through ASK.

A large spread therefore starts the executable barrier race at a disadvantage relative to the Entry-side price path.

However, correlation at market level does not tell us how many SL-first outcomes were actually flipped by quote-side friction.

## 7. D154M next causal question

D154M directly measures that missing counterfactual.

Actual:
```text
LONG  actual barrier quote = BID
SHORT actual barrier quote = ASK
```

Shadow:
```text
LONG  shadow barrier quote = ASK
SHORT shadow barrier quote = BID
```

Frozen:
```text
same actual Fill
same original normalized SL
same exact +1R price
same observed tick stream
```

The shadow is named **entry-side quote barrier race**, not "zero spread". It removes the exit-side quote crossing from the barrier comparison while preserving the actual quote stream.

Primary descriptive quantity:
```text
actual SL_FIRST -> shadow PLUS_1R
```

Report by market and direction.

No D154M result may directly authorize:
- spread threshold;
- symbol exclusion;
- SL widening;
- target change;
- altered fill model;
- Entry veto.

## 8. Research habits to preserve

Do not:
- threshold-fit after seeing one market/year;
- rescue failed hypotheses with LONG/SHORT or source-TF exceptions;
- combine weak variables into a quality score;
- backfill future structure into past snapshots;
- treat right-censored as winners/losses;
- mix execution divergence with strategy profitability;
- turn +1R continuation variables into Entry gates.

Prefer:
- one causal question per phase;
- discovery vs validation separation;
- shadow instrumentation before strategy changes;
- same-year cross-market comparison for transfer questions;
- multi-year GOLD for temporal robustness;
- baseline/control parity before using new audit evidence.
