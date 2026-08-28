# V6-002 / Multi-Environment Research Results

Status: `COMPLETED RESEARCH SYNTHESIS / NO PRODUCTION AUTHORITY`
Date: `2026-08-29`
Base HEAD before documentation update: `ced2bb276ce6471162bcc49af3522eaa3d038694`

## 1. Purpose

This document freezes the research chain from V6-001C through R3/R4 and the subsequent multi-environment MENV studies.

It prevents future sessions from:
- repeating consumed formulations;
- interpreting GOLD 2023-2025 specialization as generalization;
- forgetting the trade-count constraint;
- migrating failed exit/L variables into new stages.

## 2. R1/R2/R2P bridge

R1:
- rejected;
- 41 trades;
- EV +0.055R;
- poor year/direction breadth;
- M5 DMI direction was mostly redundant with the broad event.

R2:
- 75 GOLD23-25 trades;
- WR 41.33%;
- avg+ 2.924R;
- EV +0.622R.

R2P:
- 75 trades;
- WR 44.0%;
- avg+ 2.300R;
- EV +0.452R.

R2 did not collapse on consumed GOLD22 but was Q4 concentrated and did not port to XAUEUR/BTC.

## 3. R3 shadow and strategy

Exact H-direct control:

```text
44 H-direct fills
14 TP5
27 SL
3 BE
```

R3 ADX shadow:

```text
NOT_MATURE:
N 22 / WR 59.09% / avg+ 3.923R / EV +1.909R / total +42R

MATURE:
N 22 / WR 18.18% / avg+ 3.563R / EV -0.170R / total -3.75R
```

The preregistered R3 construction criterion passed.

R3 GOLD23-25:

```text
N 31
WR 77.42%
avg+ 2.643R
EV +1.821R
total +56.438R
DD 1R
loss streak 1
```

All development years and both directions were positive.

But unchanged R3 did not generalize. Approximate consumed diagnostic EVs:
- GOLD22 about -0.132R;
- XAUEUR about -0.401R;
- USDJPY about -0.032R;
- BTCUSD about -0.181R.

H-direct state decomposition showed:
- GOLD23-25: NOT_MATURE much better than MATURE;
- GOLD22 and USDJPY retained only a weak relative ordering;
- XAUEUR and BTCUSD reversed the relation.

Conclusion: strong development specialization, no universal H authority.

## 4. R4

R4 asked whether high ADX was harmful only when its directional pressure opposed H.

States:
- LOW_ADX;
- HIGH_ALIGN;
- HIGH_OPPOSE.

Development shadow passed, but HIGH_ALIGN sample was small.

R4 GOLD23-25:

```text
N 36
WR 69.44%
avg+ 2.718R
EV +1.582R
total +56.938R
DD 2R
loss streak 2
```

Cross/historical diagnostics did not solve generalization:
- GOLD22 roughly -0.330R;
- XAUEUR roughly -0.331R;
- USDJPY roughly -0.041R;
- BTC roughly breakeven.

No threshold rescue.

## 5. Regression into V3 precision

The project then asked whether V3 Candidate-A "precision" itself is invariant.

Within low-ADX/direct H:
- Candidate-A PASS was excellent on GOLD23-25;
- Candidate-A PASS was negative on GOLD22 while Candidate-A FAIL was strongly positive;
- BTC/XAUEUR did not recover edge simply by preserving PASS.

Delivery-state 2x2 decomposition showed `EXP_ONLY` instability:

```text
GOLD23-25  +1.625R
GOLD22     -0.500R
XAUEUR     -0.526R
USDJPY     +0.088R
BTCUSD     -0.370R
```

Do not delete EXP_ONLY post hoc. The scientific result is that the same deterministic precision label can change meaning by environment.

## 6. Multi-environment environment fingerprint

13 market-year research environments were adopted.

Simple regime features did not make GOLD22 uniquely separable from GOLD23-25.

Broad event density was higher in GOLD22, but simple trend strength, path efficiency and volatility-state measures overlapped substantially.

This increased the plausibility of concept/event-meaning shift rather than a single obvious regime switch.

## 7. Failed direct-state ideas

The following did not survive well enough:
- more 24h structural room;
- path efficiency after comparison with simple momentum/displacement;
- fixed-clock trend-strength routing;
- direct cross-market breadth formulations.

## 8. Scale x acceptance discovery

Event-relative geometry produced the first strong multi-environment relation.

Primary dimensions:

```text
planned structural risk / D1 ATR
M5 acceptance margin / D1 ATR
```

Environment-median exploratory results were then replaced by a causal past-only baseline.

The final pre-trade version uses all prior same-market broad-direct opportunities, not only prior fills.

## 9. MENV-004 exact causal formulation

Before current opportunity outcome or fill:

```text
state_valid after 20 prior same-market opportunities

high_scale =
  current risk/D1ATR > median(prior risk/D1ATR)

high_accept =
  current acceptance/D1ATR > median(prior acceptance/D1ATR)

H authority = high_scale AND high_accept
```

No future opportunity is in the median.

Opportunity/fill chain:

```text
620 broad-direct
540 state valid
163 HH parent opportunities
151 fills
144 exposure accepted
```

MENV-004 result:

```text
N 144
positive 48
WR 33.33%
avg+ 3.484R
EV +0.495R
total +71.25R
DD 15.25R
loss streak 10
```

12/13 environments positive.

By market:

```text
BTCUSD 49 / EV +0.663R approximately
GOLD   38 / EV +0.493R
XAUEUR 32 / EV +0.539R
USDJPY 25 / EV +0.090R
```

The exact ledger files in this package contain the environment-level values.

## 10. Robustness/falsification around MENV-004

The HH advantage was stress-checked against:
- fixed +1R/-1R outcome;
- fixed +3R/-1R outcome;
- existing H payoff;
- 6h/24h/48h clock horizons;
- D1-ATR-normalized favorable excursion;
- random-selection matched-count nulls;
- stronger nulls inside high-scale and high-acceptance subsets;
- initialization-history sensitivity.

The relation did not reduce to stop width alone.

Important stage interpretation:
- acceptance carries much of the Entry-survival information;
- scale x acceptance interaction appears more important for larger continuation/opportunity;
- it is not purely a risk-reduction state because MAE does not uniformly improve.

## 11. MENV-004 stage population

```text
+1R 77
+2R 55
+3R 48
+5R 35
```

This motivated winner-protection research without reducing Entry N.

## 12. MENV-005 / MENV-006

MENV-005:
- first +1R;
- causal M5 correction;
- same-direction BOS;
- lock to correction swing.

```text
N 144
WR 42.36%
avg+ 2.030R
EV +0.284R
```

It converted some losers but cut too many genuine TP5 runners.

MENV-006 used completed-close protected-break semantics instead of wick-touch stop.

```text
N 144
WR 40.97%
avg+ 2.091R
EV +0.278R
```

Still too destructive.

Closed without stop-buffer optimization.

## 13. MENV-007 to MENV-010

Post-+1R shadow research tested:
- first correction vs next R;
- first local range resolution;
- first M5 close retention;
- post-correction +1R retention vs directional renewal.

The common negative result:

> Genuine large runners frequently correct, lose local levels, or temporarily lose the +1R milestone before resuming.

Therefore:
- clean-path filters are unsafe;
- first-correction/first-break events are insufficient exhaustion definitions.

Example MENV-010 among 77 +1R survivors:

```text
LOSE_1R_FIRST              45
DIRECTIONAL_RENEW_FIRST    17
THREE_R_FIRST               9
NO_VALID_CORRECTION         6
```

Even `LOSE_1R_FIRST` contained many later +3R/+5R runners.

## 14. MENV-011

Single midpoint protection:

```text
first +1R
-> keep 100% position
-> one-time SL to +0.5R
-> no further R-step trailing
```

Result:

```text
N 144
WR 53.47%
avg+ 1.104R
EV +0.125R
total +18R
```

Closed. No 0.4R/0.6R rescue.

## 15. MENV-012 trade-count expansion

Natural compensation rule:

```text
(scale / past median scale)
x
(acceptance / past median acceptance)
> 1
```

Same exposure semantics:

```text
N 239
WR 27.20%
avg+ 3.288R
EV +0.166R
total +39.75R
DD 29.5R
loss streak 12
```

N rose by about 66% but quality/breadth deteriorated.

This is the primary negative control for the trade-count rule:
- more N is required long term;
- but N cannot be manufactured by weakening a meaningful state.

## 16. MENV-013 / MENV-014 non-H interpretation

MENV-013:
- 359 non-H fills;
- trigger-close checkpoint hit 311 times;
- 86.63% checkpoint hit.

This established that non-H is often directionally reactive.

But trigger-close reward relative to H risk is tiny.

MENV-014 used:
- same 50% pullback Entry;
- broken M5 level as local invalidation;
- trigger close as target.

It failed across all market groups, with very low WR and strongly negative EV. Fill and local invalidation often occurred in the same M1 bar; ambiguous same-bar cases were conservatively counted as losses.

Scientific interpretation:

> Non-H contains local directional information but the known risk/destination architecture does not monetize it.

## 17. L research

A separate correction-completion research line was maintained.

No H-variable inversion was allowed.

A ~301-candidate L population provided frequency but poor/unstable survival.

Tested causal ideas did not survive environment recurrence.

L10 M30 variance-ratio persistence:
- pooled persistent subset looked better;
- environment recurrence was only 3/7 for +1R and 2/7 for EV.

Closed without q/window tuning.

## 18. Trade count as a design constraint

The current 13-environment MENV-004 accepted population is 144.

This is larger and broader than V3 Candidate B but still thin in some environment-direction cells.

Future architecture work must not silently turn the enlarged research universe into a tiny filtered sample.

Preferred methods to increase usable N:
- longer history on the same frozen state;
- additional outcome-blind markets with adequate causal warmup;
- independent complementary mechanism/module;
- direction routing that recovers valid opportunities.

Disfavored:
- relaxing causal history;
- threshold shopping;
- post-hoc market selection;
- applying H failure as automatic L.

## 19. Current directional-prior insight

The project now recognizes that earlier indicator studies mostly used direction-adjusted features after the local event had already selected direction.

That does **not** fully answer whether indicators can contribute to direction authority.

V6-003 therefore begins from:

```text
pre-event causal directional prior
+
local liquidity/ownership event
+
event-quality state
```

See the active contract.

## 20. No authority claims

Nothing in this document changes the production EA.

GOLD 2021 remains closed.

All current economics are research/offline evidence until exact execution gates are completed.
