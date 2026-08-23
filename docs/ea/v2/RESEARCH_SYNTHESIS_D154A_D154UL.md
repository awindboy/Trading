# V2 Research Synthesis — through D154UL

Status: CURRENT SESSION-HANDOFF SYNTHESIS  
Date: 2026-08-24

## Control

V2 strategy authority remains unchanged:

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

No D154 research phase has authorized a new Entry filter.

## Research stages remain separate

```text
Fill -> +1R       = Entry survival
+1R -> +2R        = winner continuation
post +2R          = exit architecture
execution         = broker/quote mechanics
portfolio         = exposure risk
```

## Important rejected/demoted Entry explanations

D154A-J did not support universal Entry gates based on:
- Fill-time M1 maturity;
- delayed same-direction INITIAL_BOS;
- replacement fresh-FVG retest;
- post-SL new Root;
- M1 TRANSITION-at-sweep veto;
- stale prior-owner Root;
- same-owner BOS refresh cancellation;
- static H1/M30 alignment;
- post-contact HTF BOS veto;
- simple HTF protected-to-external exhaustion.

D154J specifically rejected the explanation that CADJPY simply enters much later inside HTF delivery geometry.

## Winner continuation

D145 remains stage-limited:
- lower M30 protected->external progress at +1R correlated with more continuation room;
- this is not Entry authority.

V3E BANK_2R_LOCK_ONE remains the provisional post+1R research reference.

## D154K/L — cross-market execution scale

D154K found GOLD25 and CADJPY25 had broadly similar strategy geometry relative to local M1 reaction scale, while execution friction differed sharply.

Standard-account 2025:

```text
          spread/reactionTR   spread/1R   spread/FVG   Entry survival
GOLD            0.342          0.028       0.462         56.6%
BTC             1.015          0.063       1.026         47.2%
SILVER          1.701          0.147       2.099         39.1%
CADJPY          2.125          0.150       2.688         26.5%
```

The 2025 market ordering was exact:
- friction: GOLD < BTC < SILVER < CADJPY;
- survival: GOLD > BTC > SILVER > CADJPY.

Status:
```text
cross-market cost-scale mechanism = supported
per-trade spread threshold         = not supported
universal yearly determinant       = not established
```

## D154M — post-Fill quote-side causal component

Actual executable barrier side:

```text
LONG  = BID
SHORT = ASK
```

Entry-side quote shadow:

```text
LONG  = ASK
SHORT = BID
```

Standard-account actual SL-first -> shadow +1R flips:

```text
GOLD       1
BTC        7
SILVER     0
CADJPY    17
```

CADJPY actual survival improved from 26.5% to 41.6% in shadow; BTC from 47.2% to 52.8%.

This proved a real causal execution mechanism but not a universal cause because SILVER had zero flips.

## D154UL — Ultra Low natural experiment

The account/feed moved to XM Ultra Low `#` symbols.

Ultra Low 2025:

```text
          spread/reactionTR   spread/1R   spread/FVG   Entry survival
GOLD#           0.162          0.014       0.247         58.2%
BTCUSD#         0.541          0.032       0.551         48.8%
SILVER#         1.303          0.108       1.500         38.3%
CADJPY#         1.631          0.124       2.056         30.1%
```

D154M flips fell:

```text
GOLD       1 -> 0
BTC        7 -> 3
SILVER     0 -> 0
CADJPY    17 ->10
```

Scenario populations remained highly overlapping, especially BTC and CADJPY. Across 329 common Standard/Ultra scenarios:
```text
SL_FIRST -> PLUS_1R = 7
PLUS_1R -> SL_FIRST = 0
```

Conclusion:
- lowering friction genuinely improved part of the execution problem;
- friction remains only a partial explanation;
- high-friction markets remain poor even on Ultra Low.

## Strategic pivot after D154UL

The research priority is no longer:

> How do we force the same Entry architecture to work on every high-friction market?

It is now:

> Does the strategy reproduce its edge across a broader universe of markets whose execution scale is naturally similar to GOLD#?

This creates D154O.

## D154O

D154O is a two-stage market-universe study:

### Stage A
One fixed week of outcome-blind raw M1+spread data across a broad user-supplied Ultra Low symbol universe.

Frozen week:
```text
2026-08-17 .. 2026-08-23
```

Use chart-only proxies. Do not claim they are exact D154K variables.

### Stage B
Freeze Gold-like shortlist and a small non-Gold-like control cohort before any one-year outcomes.

Then run 2025 full real-tick strategy evidence and exact D154K/M metrics.

If low-friction markets independently reproduce strong Entry survival, prioritize that compatible market universe rather than rescuing high-friction markets.

If they do not, execution scale is only one necessary/helpful condition and research returns to underlying regime/path quality.

## D154N

Pending-to-Fill quote-side delay/depth audit remains documented but DEFERRED.

It is no longer the immediate next phase.

## Next session

The user will provide a broad list of Ultra Low tradable symbols.

The assistant must not run one-year performance tests first.

First build the fixed-week raw market screen, compute GOLD-relative execution proxies, freeze the shortlist/control manifest, and only then run 2025 strategy tests.
