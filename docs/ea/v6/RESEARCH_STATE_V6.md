# V6 Research State

Status: `ACTIVE`  
Date: `2026-08-29`  
Phase: `V6-003 DIRECTIONAL-PRIOR EXTERNAL-VALIDATION PREP`  
Production authority: `NONE`  
Promoted production candidate: `NONE`  
Current research benchmark: `MENV-004 PRETRADE SCALE x ACCEPTANCE H`  
Directional validation candidate: `P2 H1 DISP24 x MENV HIGH_HIGH`  
Base HEAD for this documentation update: `982839b0a1ea166fc534272f2024a72cedfb8326`

## 1. Research allocation

Consumed panel:

```text
GOLD 2022-2025
XAUEUR 2023-2025
USDJPY 2023-2025
BTCUSD 2023-2025
```

`GOLD 2021 = UNTOUCHED`.

These 13 market-year environments are development/falsification data, not final validation.

## 2. Permanent historical constraints

- V3 Candidate B was strong on GOLD23-25 and collapsed on GOLD22.
- R1 M5 DMI largely duplicated local-event direction.
- R2/R2P improved GOLD robustness but did not port universally.
- R3/R4 were strong GOLD specializations and failed portability.
- V3 precision/delivery semantics are not assumed invariant.
- L is independent from H and remains unresolved.
- Simple profit protection can raise positive frequency while destroying the required winner payoff.

See `V6_002_MULTI_ENVIRONMENT_RESEARCH_RESULTS.md` and prior V6 result docs for full history.

## 3. MENV-004 current benchmark

Exact causal state:

```text
scale      = planned H risk / completed D1 ATR14
acceptance = M5 acceptance margin / completed D1 ATR14

HIGH_HIGH =
    scale > earlier same-market expanding median(scale)
AND acceptance > earlier same-market expanding median(acceptance)
```

Warmup = 20 earlier valid broad-direct opportunities.

Exact replay:

```text
620 broad-direct causal-valid
540 state-valid
163 HIGH_HIGH parents
151 fills
144 exposure accepted

48 positive
WR 33.33%
avg positive +3.484R
EV +0.494792R
total +71.25R
12/13 market-years positive
```

## 4. V6-003A parity correction

The first directional-prior child re-audited the full raw lineage before opening outcomes.

Correct D1 semantics are the committed V3 calendar-D1 ATR14 with next-day availability. Do not delete the first observed D1 bar by a separate “partial day” heuristic.

Correct pending-entry semantics begin strictly after `trigger_time`.

These two checks reproduce the current MENV benchmark exactly, including every market-year outcome row.

## 5. Frozen directional-prior atlas

At `sweep_time`, using completed bars only:

```text
P1 = H1 DMI14 direction
P2 = H1 24-bar signed displacement
S1 = H1 BOS owner
S2 = M30 BOS owner
S3 = H1/M30 concordant owner
```

Across 620 opportunities:

```text
P1: 202 ALIGNED / 418 OPPOSED
P2: 220 ALIGNED / 400 OPPOSED
S1: 223 ALIGNED / 397 OPPOSED
S2: 166 ALIGNED / 454 OPPOSED
S3: 119 ALIGNED / 350 OPPOSED / 151 NEUTRAL
```

P1/P2 absolute direction agreement = 84.52%.

## 6. First-atlas result

Broad 620-event path:

```text
586 fills
273 +1R
138 +3R
94 +5R
```

### P1

P1 aligned vs opposed is essentially flat:

```text
+1R 46.88% vs 46.45%
+3R 24.48% vs 23.10%
+5R 16.15% vs 15.99%
```

When P1 and P2 disagree, P2 wins materially.

**P1 is CLOSED as an independent prior.**

### P2 broad

```text
ALIGNED: 210 fills / +1 49.05% / +3 26.67% / +5 18.57%
OPPOSED: 376 fills / +1 45.21% / +3 21.81% / +5 14.63%
```

This is too weak/asymmetric for standalone direction authority. Broad benefit is concentrated in SHORT and cluster intervals cross zero.

## 7. P2 x MENV HIGH_HIGH candidate interaction

Within 151 HIGH_HIGH fills:

```text
P2 ALIGNED N=53:
+1R 58.49%
+3R 41.51%
+5R 35.85%

P2 OPPOSED N=98:
+1R 50.00%
+3R 28.57%
+5R 19.39%
```

Pooled deltas:

```text
+1R +8.49pp
+3R +12.94pp
+5R +16.46pp
```

+5R market aggregate:

```text
BTCUSD +26.15pp
GOLD   +20.11pp
USDJPY +18.05pp
XAUEUR  -2.75pp
```

Both LONG and SHORT pooled +5R deltas are positive.

Cluster bootstrap for +5R barely excludes zero; stratified permutation one-sided p is about 0.061. Continuous scale/acceptance remains a plausible confound.

Interpretation:

> A strong local MENV reaction aligned with a completed-H1 displacement prior may have more distant continuation capacity.

Name: `cross-scale continuation capacity`.

Status: `EXTERNAL VALIDATION CANDIDATE ONLY`.

## 8. Accepted MENV economics by P2

Exact 144 accepted trades:

```text
P2 ALIGNED:
N 51
WR 41.18%
avg positive 3.786R
EV +0.971R
total +49.50R

P2 OPPOSED:
N 93
WR 29.03%
avg positive 3.250R
EV +0.234R
total +21.75R
```

Do not turn this into an aligned-only strategy:
- WR still <50%;
- N collapses 144 -> 51;
- consumed-panel selection would violate the routing/trade-density rules.

## 9. Counter-prior branch

For 79 HIGH_HIGH P2-opposed events that later hit the local structural stop:

```text
24h prior-direction endpoint median -0.044 D1 ATR
24h endpoint positive 45.6%
48h endpoint median +0.013 D1 ATR
48h endpoint positive 50.6%
```

Automatic `OPPOSED -> trade prior direction` is rejected.


## 10. Corrected direction-first research state

V6-003B moved direction authority to the prior **before** the local M5 event finalized direction.

Broad pre-direct geometry-valid population:

```text
1391 opportunities
620 direct-transfer
771 non-direct
```

Removing direct-transfer and relying on prior direction did not work economically. The best broad indicator prior remained near/under zero EV.

Therefore direct local-transfer information remains useful timing/quality evidence even when direction is assigned upstream.

## 11. Conventional indicator direction atlas

Direction-first direct accepted economics:

```text
H1 DMI             N190 EV +0.005R
H1/H4 DMI          N139 EV -0.110R
H1/H4 MACD         N146 EV +0.110R
Aroon25 H1/H4      N135 EV -0.072R
Vortex14 H1/H4     N104 EV +0.084R
RSI14 H1/H4        N117 EV +0.150R
DISP24 control     N209 EV +0.133R
H1/M30 structure   N113 EV +0.064R
```

The unconditional direct-event control is negative:

```text
560 accepted / EV -0.055R
```

Thus pre-event direction state has some selection meaning, but named indicators are not automatically the source of that meaning.

## 12. RSI falsification

A same-architecture simpler control was frozen:

```text
H1 14-bar signed displacement
H4 14-bar signed displacement
same sign -> direction
else NEUTRAL
```

It agrees with RSI14 H1/H4 99.18% on jointly available direct events and is economically stronger:

```text
DISP14 direct:
90 accepted
WR 30.0%
avg+ 3.25R
EV +0.275R

RSI14 direct:
117 accepted
WR 29.06%
avg+ 2.956R
EV +0.150R
```

Therefore RSI is not an independent indicator edge.

## 13. Breadth state

DISP14 direct has positive EV in 8/13 market-years and negative EV in 5/13. Several environment cells have only 2-6 trades.

Stratified permutation diagnostics remain weak (one-sided raw-lifecycle-R p about 0.115 for DISP14).

Do not promote or tune.

## 14. Current scientific interpretation

Conventional indicators did not solve direction authority independently.

The strongest remaining clue is:

> multi-horizon directional price persistence can help define a causal prior before local timing, but its continuation/failure mechanism is not yet understood well enough for strategy authority.

This differs from returning direction authority to local structure. The prior remains architecturally upstream; the next task is to explain when directional persistence has continuation meaning versus reversal/correction meaning.

## 15. Active next child

Prepare a new pre-outcome contract for directional persistence **mechanism**, not another indicator/window comparison.

Research questions:
- broad persistent move versus one-leg impulse;
- continuation versus rebound/reversal volatility state;
- causal reassertion after local counter-move;
- ability to recover opportunity N without replacing direct local information with noise.

No DISP14/24 window tuning.
No conventional indicator rescue.
GOLD 2021 remains untouched.

## 16. Final promotion gate remains

```text
WR >= 50%
avg positive NET R >= 2R
cost-adjusted EV > 0
sufficient N / trade density
robust market-period breadth
acceptable DD/streak
no unacceptable winner concentration
independent validation
exact execution evidence
```

No production authority exists.
