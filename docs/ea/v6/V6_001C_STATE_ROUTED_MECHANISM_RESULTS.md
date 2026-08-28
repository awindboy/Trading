# V6-001C — State-Routed Mechanism Research Results

Status: `COMPLETED EXPLORATORY ARCHITECTURE BRIDGE / NO PRODUCTION AUTHORITY`  
Date: `2026-08-28`  
Primary market: `GOLD#`  
Research periods: `GOLD 2023-2025 + consumed GOLD 2022 historical comparison`  
Cross-market diagnostics: `XAUEUR# / USDJPY# / BTCUSD# 2023-2025`  
Production authority: `NONE`

## 1. Methodology correction that defines this result

V6-001B began by attaching interpretable indicators to the exact V3-003C broad event. During the research session the user corrected an important methodological mistake:

> V6 indicators are not supposed to rank or classify the outcomes of already-frozen V3 trades. They are supposed to describe market state, and that state should change which trading mechanism is executed. The correct test is to replay the market with the new V6 mechanism and compare the resulting trades with V3.

The active research object therefore changed from:

```text
indicator -> old V3 winner/loser discrimination
```

to:

```text
causal market-state measurement
-> mechanism selection / authorization
-> new trade generation from raw M1
-> V3 vs V6 economic comparison
```

`AUC` is not a V6 promotion criterion. Earlier AUC-style diagnostics are retained only as historical exploratory work and must not be used to select or promote a V6 strategy.

## 2. Reproducibility prerequisites

Before opening V6 state-routed P/L, the V3 replay chain was restored from current GitHub authority.

Authoritative scripts:

```text
scripts/v3_003c_reload_state_acceptance_probe.py
scripts/v3_003d_correction_completion_probe.py
scripts/v3_003e_dual_module_repro.py
```

Raw GOLD 2023-2025 replay reproduced the V3-003E authority:

```text
Candidate A k=2:
2023 40
2024 29
2025 27

Module L:
11 physical trades
11 checkpoint hits
10 full +1R hits
7 residual +2R hits
1 exact-mirror checkpoint

Module H base k2 / 50%:
48 fills
14 TP5
31 SL
3 BE

Module H direct-transfer:
44 fills
14 TP5
27 SL
3 BE
```

The frozen V3 Candidate-B comparison was also reproduced:

```text
53 accepted trades
positive rate       52.83%
avg positive        +2.775R
EV                  +0.994R/trade
total               +52.69R
max DD              8.0R
```

The comparison engine therefore had to reproduce V3 before any V6 result was interpreted.

## 3. State-coordinate construct audit

The exploratory indicator work expanded beyond the initial H1/H4 standard atlas into multiple timeframes, settings and interpretable combinations. That exploration is not strategy authority; its useful output was a set of state concepts.

The three most useful coordinates were:

```text
M5 DMI(5)  = very recent local directional pressure
H4 ADX(14) = intermediate trend/delivery maturity/strength
D1 ATR(14) = background daily movement/noise scale
```

Construct checks independent of trade outcome showed:

- M5 DMI(5) direction strongly tracked very recent 15-30 minute directional pressure;
- H4 ADX>=25 corresponded to higher H4 directional efficiency and lower H4 choppiness;
- D1 ATR supplied a causal scale for the daily movement environment.

A valid market-state measurement does not automatically imply the initially assumed trading meaning. The strategy replay below forced that interpretation to be falsified.

### 3.1 Breadth of the exploratory indicator work

Before the methodology correction, the exploratory atlas was expanded substantially beyond the committed initial H1/H4 panel. The research history included approximately:

```text
6 primary timeframes: M5 / M15 / M30 / H1 / H4 / D1
additional intermediate TF probes: H2 / H3 / H6 / H8 / H12
702 single indicator/setting combinations
29 indicator/state families
15 fixed MTF composites
1,254 interpretable multi-indicator combinations
1,210 dense neighborhood combinations around the main local-pressure / slower-capacity / background-noise family
```

The analysis was decomposed by year, LONG/SHORT, half-year and quarter where sample size allowed, and was connected to V3-native variables such as risk, sweep-to-trigger latency, liquidity age and level count.

Important negative findings from this exploratory phase:

- no standalone indicator survived the strongest half-year stability screen as a universal answer;
- the fixed state-transition atlas did not produce a stable six-cell Entry-survival relation;
- the fixed statistical price-process panel (variance ratio, autocorrelation, sign entropy, jump share, vol-of-vol, range CV) reversed across year/direction cells;
- the fixed direct XAUEUR/USDJPY breadth formulation did not provide stable Entry-survival meaning;
- several pooled or setting-specific clues weakened after direction/time decomposition.

The main positive exploratory recurrence was a broad family resembling:

```text
very recent local directional pressure
× intermediate trend/delivery capacity
÷ background movement/noise
```

A wide parameter plateau appeared inside GOLD 2023-2025, but later old-trade/AUC falsification and cross-market checks showed that this relation was not a portable universal classifier. Because the user then corrected the methodology, the proper legacy of this exploration is only:

> it generated interpretable state hypotheses to test through actual strategy replay. It did not authorize a score, AUC target, optimized parameter set, or trading filter.

The preregistered macro/rates child was not completed to a claim-grade outcome before the methodology change. It remains an optional future mechanism-linked context family, not a completed result.

## 4. V6 R1 — continuation/correction router

R1 was frozen before its P/L was opened:

```text
H4 ADX >= 25
+ M5 DMI(5) aligned with event direction
-> H continuation mechanism

H4 ADX >= 25
+ M5 DMI(5) opposed
-> L correction mechanism

H4 ADX < 25
-> NO_TRADE
```

GOLD 2023-2025 R1:

```text
41 trades
positive rate       29.27%
avg positive        +2.604R
EV                  +0.055R/trade
total               +2.25R
max DD              16.5R
2023 EV             -0.158R
2024 EV             -0.182R
2025 EV             +0.659R
SHORT EV            -0.638R
LONG EV             +0.714R
```

Classification:

```text
R1 REJECTED
```

The main diagnosis was structural redundancy. M5 DMI(5) was aligned with the broad-event direction in about 90% of events, which is unsurprising because the broad event already requires completed M5 ownership transition back toward the event direction. M5 DMI sign was therefore not a strong independent regime selector.

## 5. Recursive reversal — H4 maturity meant the opposite of the first thesis

When the same broad-H mechanism was decomposed by H4 ADX state, the relation was opposite to R1's assumption.

```text
H4 ADX < 25:
59 H trades
EV +0.733R/trade
2023 / 2024 / 2025 all positive
LONG / SHORT both positive

H4 ADX >= 25:
46 H trades
EV +0.027R/trade
SHORT EV strongly negative
```

This recurrence is consistent with prior project evidence:

- V3 H `BOTH`, a more strongly progressed higher-timeframe state, produced no +5R winners in discovery;
- D-145 winner continuation found that large runners tended to have less-consumed M30 directional structure at +1R.

The working interpretation became:

> Module H may be healthier when the larger directional process is not already mature/consumed, rather than when conventional trend strength is already high.

This is a state-mechanism interpretation, not authority for `ADX<25` as a universal filter.

## 6. V6 R2 — maturity router

R2 removed M5 DMI from routing and inverted the H4 interpretation:

```text
H4 ADX < 25
-> H

H4 ADX >= 25
-> L
```

D1 ATR remained a scale/payoff input where already required by Module L; it was not optimized into a new gate.

### GOLD 2023-2025

```text
75 trades
positive rate       41.33%
avg positive        +2.924R
EV                  +0.622R/trade
total               +46.645R
max DD              10.0R
max loss streak     10

2023 EV             +0.454R
2024 EV             +0.768R
2025 EV             +0.645R

LONG EV             +1.054R
SHORT EV            +0.129R
```

R2 does not meet the final project target of >=50% realized positive rate, but it is not a failed research result. It has positive expectancy, average positive payoff well above 2R, positive annual breadth, and positive LONG/SHORT expectancy.

Correct classification:

```text
MEANINGFUL DEVELOPMENT CANDIDATE / BENCHMARK
FINAL JOINT TARGET NOT YET MET
NO PRODUCTION AUTHORITY
```

## 7. V6 R2P — existing +2R 50% H protection control

No new payoff grid was searched. R2P reused the existing V3 H control:

```text
+2R:
    realize 50%
    residual keeps original SL
+3R:
    residual -> BE
+5R:
    final exit
```

The old V3 reference for this payoff was reproduced before applying it to R2.

GOLD 2023-2025 R2P:

```text
75 trades
positive rate       44.0%
avg positive        +2.300R
EV                  +0.452R/trade
total               +33.895R
max DD              8.5R
max loss streak     6
all three years EV  positive
LONG / SHORT EV     positive
```

R2P improves realized-positive frequency and drawdown relative to R2 but sacrifices payoff and expectancy.

Current role:

```text
R2  = primary economic benchmark
R2P = payoff/positive-frequency alternate
```

Do not optimize partial fraction or R-level from these consumed outcomes.

## 8. GOLD 2022 historical comparison

GOLD 2022 was already consumed by V3 validation before V6-001C. This is NOT pristine V6 validation. It is a harsh historical comparison of frozen R2/R2P behavior against the failed V3 architecture.

The raw 2022 source reproduced the old V3 Candidate-B result exactly:

```text
V3 Candidate B
24 trades
positive rate       25.0%
avg positive        +1.458R
EV                  -0.385R/trade
total               -9.25R
max DD              10.25R
max loss streak     8
```

### R2 on the same 2022 market

```text
40 trades
positive rate       35.0%
avg positive        +2.428R
EV                  +0.200R/trade
total               +7.987R
max DD              6.75R
max loss streak     6
```

### R2P on the same 2022 market

```text
40 trades
positive rate       37.5%
avg positive        +1.966R
EV                  +0.112R/trade
total               +4.487R
max DD              7.50R
max loss streak     6
```

Important qualification:

```text
R2 2022 quarterly total:
Q1  -0.25R
Q2  -1.25R
Q3  -3.00R
Q4 +12.49R
```

The annual positive result is concentrated in Q4. R2 therefore did not collapse like V3, but it cannot be called uniformly stable within 2022.

## 9. 2022 module decomposition

The strongest historical-comparison result was Module H.

```text
R2 H 2023-2025:
60 trades
positive rate 36.7%
avg positive +3.648R
EV +0.704R

R2 H 2022:
26 trades
positive rate 38.5%
avg positive +3.000R
EV +0.538R
```

R2 L did not generalize:

```text
R2 L 2023-2025:
15 trades
positive rate 60.0%
EV +0.293R

R2 L 2022:
14 trades
positive rate 28.6%
EV -0.429R
```

The evidence therefore supports preserving the H-stage state hypothesis while treating the inverse rule `ADX>=25 -> L` as unsupported.

## 10. Cross-market replay

The same unmodified V3/R2/R2P rules were replayed on all full 2023-2025 markets already available in the current GoldLike set:

```text
XAUEUR#
USDJPY#
BTCUSD#
```

Symbol point precision was respected:

```text
XAUEUR# / BTCUSD# = 0.01
USDJPY#            = 0.001
```

No market-specific threshold or rule was changed.

| Market | Strategy | Trades | Positive | Avg positive | EV/trade | Total R | Max DD |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| XAUEUR | V3 | 72 | 25.0% | +2.014R | -0.247R | -17.75R | 37.5R |
| XAUEUR | R2 | 88* | 27.6% | +1.346R | -0.353R | -30.686R | 31.186R |
| XAUEUR | R2P | 88* | 33.3% | +1.149R | -0.284R | -24.686R | 25.186R |
| USDJPY | V3 | 61 | 27.9% | +2.103R | -0.135R | -8.25R | 12.75R |
| USDJPY | R2 | 88 | 27.3% | +2.604R | -0.017R | -1.50R | 10.5R |
| USDJPY | R2P | 88 | 28.4% | +2.140R | -0.108R | -9.50R | 10.5R |
| BTCUSD | V3 | 110 | 33.6% | +2.241R | +0.090R | +9.916R | 17.334R |
| BTCUSD | R2 | 169 | 27.2% | +1.447R | -0.334R | -56.430R | 57.930R |
| BTCUSD | R2P | 169 | 30.8% | +1.242R | -0.310R | -52.430R | 52.930R |

`*` XAUEUR R2/R2P had one censored terminal trade; economic metrics used resolved trades.

## 11. Cross-market interpretation

R2 did NOT solve universal market generalization.

```text
GOLD period robustness improved materially
!=
R2 is a universal market architecture
```

### XAUEUR

- V3 negative;
- R2/R2P also negative;
- R2 H strongly negative;
- L approximately near breakeven.

### USDJPY

- V3 negative;
- R2 materially improved from `-0.135R` to about `-0.017R/trade`, nearly breakeven;
- L was positive while H remained weakly negative.

### BTCUSD

- V3 itself remained weakly positive (`+0.090R/trade`);
- R2 strongly deteriorated (`-0.334R/trade`);
- both R2 H and L were negative.

This is strong evidence that replacing V3 local precision with a broad-event `ADX state -> H/L` router is not portable across markets.

A key positive clue remains:

> BTC shows that V3 local precision can remain useful where broad R2 H destroys it. V6 should preserve causal V3 precision and use market state to modify destination/authorization rather than replace the precision substrate wholesale.

## 12. What is now closed

Do not repeat these formulations without a genuinely new causal reason:

```text
AUC / old-trade classification as the main V6 objective
M5 DMI sign as an independent broad-event router
R1: ADX>=25 + DMI aligned -> H
R1: ADX>=25 + DMI opposed -> L
simple universal broad-event ADX router across all markets
simple inverse rule ADX>=25 -> L as a general L authorization
R2P parameter/fraction/R-level optimization on consumed outcomes
```

## 13. What survives

The following remain useful research objects:

```text
R2 GOLD 2023-2025 economic benchmark
R2 GOLD 2022 consumed historical comparison
R2P payoff alternate
H4 maturity as a possible H-stage context variable
V3 local reaction/requalification precision substrate
market suitability as a separate strategy-design problem
```

R2 is NOT production authority and not final validation.

## 14. Next phase — V6-002

Next active phase:

```text
V6-002 PRECISION-PRESERVING STATE-ROUTED ARCHITECTURE RESEARCH
```

The first controlled child is `R3 H-MATURITY`.

### R3 core question

> Can V6 preserve the V3 local precision/requalification substrate, while using causal market state only to decide when the H large-payoff destination remains healthy?

Initial R3 boundary:

```text
preserve V3 Candidate-A / H direct-transfer precision semantics
preserve L as a separate research object
use H4 maturity only at the H stage
no broad-event replacement of V3 precision
no market-specific ADX thresholds
no payoff-grid optimization
```

### Required comparison panel

Every R3 architecture change must be reported together on:

```text
GOLD 2023-2025
GOLD 2022 — consumed historical stress comparison only
XAUEUR 2023-2025
USDJPY 2023-2025
BTCUSD 2023-2025
```

No single GOLD improvement may hide destruction of an independent market.

### Evaluation

Do not classify a research candidate from win rate alone.

Report jointly:

```text
trade count
realized positive rate
average positive R
average negative R
EV/trade
total R
max DD
max loss streak
year breadth
direction breadth
H/L contribution
winner concentration
cost/execution sensitivity when appropriate
```

The final project target remains:

```text
positive rate >= 50%
avg positive NET R >= 2R
cost-adjusted EV > 0
```

But `final target not met` is not synonymous with `research hypothesis worthless`.

## 15. Later V6-002 research directions

After R3, priority order is:

1. `H-stage maturity / remaining-capacity research`
   - determine whether H4 maturity is actually measuring unused delivery capacity rather than conventional trend strength;
   - compare with existing V3/D-145 structure-consumption evidence without automatically reusing post-+1R variables as Entry filters.

2. `L-specific correction-completion state research`
   - do NOT define L as merely the inverse of H;
   - identify causal state transitions that make a deep requalification meaningful;
   - preserve atomic/deeper-reload semantics.

3. `market suitability`
   - R2 cross-market failure shows that strategy-compatible market selection is part of strategy design;
   - future market universes must be screened outcome-blind before profitability is opened.

4. `external/source-of-move context`
   - rates/USD/flow/positioning/scheduled-event state remains eligible only when tied to a specific failure mechanism;
   - no unrelated external-variable tournament.

5. `execution and final economics`
   - only after architecture stabilizes;
   - exact tick / commission / slippage / swap / MT5 reproduction remain later gates.

## 16. Validation status

```text
GOLD 2023-2025   = consumed V6 research/development
GOLD 2022        = consumed historical falsification/comparison; NOT pristine V6 validation
GoldLike markets = consumed architecture generalization diagnostics
GOLD 2021        = UNTOUCHED
```

Do not open GOLD 2021 until a later V6 architecture is deliberately frozen for that role.

## 17. One-line handoff

> V6 has produced its first economically meaningful state-routed GOLD candidates: R2/R2P improve period robustness and R2-H survives the consumed 2022 stress comparison, but broad ADX routing is not portable across markets and L remains unstable; preserve R2 as a benchmark, preserve V3 local precision, and move to V6-002 R3 precision-preserving H-stage state routing before any final validation or EA promotion.
