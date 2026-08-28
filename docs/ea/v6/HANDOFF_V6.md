# V6 Development Handoff

Last updated: `2026-08-29`
Base GitHub HEAD before this update: `ced2bb276ce6471162bcc49af3522eaa3d038694`
Current phase: `V6-003 MULTI-ENVIRONMENT DIRECTIONAL-PRIOR RESEARCH`
Current production authority: `NONE`
Current promoted production candidate: `NONE`
Current research benchmark: `MENV-004 PRETRADE SCALE x ACCEPTANCE H`
Untouched final-period reserve: `GOLD 2021`

## 1. Mandatory startup

Read in order:

1. latest GitHub HEAD;
2. root `AGENTS.md`;
3. root `docs/ea/HANDOFF.md`;
4. `docs/ea/WORKFLOW_AND_ZIP_HANDOFF.md`;
5. `docs/ea/v6/AGENTS_V6.md`;
6. this handoff;
7. `RESEARCH_STATE_V6.md`;
8. `V6_002_MULTI_ENVIRONMENT_RESEARCH_RESULTS.md`;
9. `V6_003A_DIRECTIONAL_PRIOR_RESEARCH_CONTRACT.md`;
10. `DECISIONS_V6.md`;
11. `BACKLOG_V6.md`.

GitHub wins over chat memory.

## 2. Why the phase changed

V3 and early V6 research were too anchored to GOLD 2023-2025.

The user explicitly changed the research policy:

> GOLD 2022 and multiple markets/years must participate in discovery so that a rule is not designed around one favorable environment.

The consumed research panel is now 13 market-year environments:

```text
GOLD 2022-2025
XAUEUR 2023-2025
USDJPY 2023-2025
BTCUSD 2023-2025
```

This is development/falsification, not pristine final validation.

## 3. V6 chain completed before multi-environment reset

### R1

`ADX>=25 + M5 DMI aligned -> H`, opposed -> L.

GOLD 2023-2025:

```text
41 trades
WR 29.27%
avg+ 2.604R
EV +0.055R
DD 16.5R
```

Rejected. M5 DMI direction was about 90% redundant with the broad event direction.

### R2

`ADX<25 -> H`, `ADX>=25 -> L`.

GOLD 2023-2025:

```text
75 trades
WR 41.33%
avg+ 2.924R
EV +0.622R
DD 10R
```

Meaningful GOLD benchmark, not universal architecture.

GOLD 2022 stayed positive overall (`EV +0.200R`) but was Q4 concentrated; L reversed negative.

Cross-market R2:
- XAUEUR negative;
- USDJPY near breakeven;
- BTCUSD strongly negative.

### R2P

Existing +2R/50% H protection control:

```text
75 trades
WR 44.0%
avg+ 2.300R
EV +0.452R
DD 8.5R
```

## 4. R3/R4 precision-preserving H research

R3 shadow on exact V3 H-direct 44-fill development population:

```text
NOT_MATURE ADX<25:
22 trades
WR 59.09%
avg+ 3.923R
EV +1.909R

MATURE ADX>=25:
22 trades
WR 18.18%
EV -0.170R
```

R3 GOLD 2023-2025 strategy:

```text
31 trades
WR 77.42%
avg+ 2.643R
EV +1.821R
total +56.438R
DD 1R
```

But unchanged R3 remained negative or weak on GOLD 2022 / XAUEUR / USDJPY / BTCUSD. H-state portability analysis showed the ADX relation reversed on XAUEUR and BTCUSD.

R4 allowed high-ADX H only when H4 DMI direction aligned with H:

```text
36 trades
WR 69.44%
avg+ 2.718R
EV +1.582R
total +56.938R
DD 2R
```

Development remained strong, but 2022 worsened and cross-market portability was not solved.

Conclusion:
- R3/R4 are consumed evidence of GOLD-specific specialization;
- ADX level/direction is not a universal H-state solution.

## 5. Candidate-A / V3 precision regression

Within comparable low-ADX/direct H opportunity:
- Candidate-A precision strongly helped GOLD 2023-2025;
- it reversed on GOLD 2022;
- it did not create robust edge on XAUEUR/BTC.

The `delivery_state = M30 expansion >1 OR owner alignment` internals were decomposed.

The `EXP_ONLY` branch was particularly unstable:

```text
GOLD23-25  +1.625R EV
GOLD22     -0.500R
XAUEUR     -0.526R
USDJPY     +0.088R
BTCUSD     -0.370R
```

Do not simply delete EXP_ONLY after seeing outcomes. The lesson is that V3 "precision" is not a universally invariant quality scale.

## 6. Multi-environment reset and environment fingerprint

The project stopped treating GOLD 2022 as an anomalous external validation year and moved all consumed data into one research panel.

Outcome-blind environment fingerprints showed GOLD 2022 overlaps GOLD 2023-2025 on many simple volatility/trend/process features. Broad-event density was notably higher in 2022.

Working interpretation:
- simple visible regime shift is insufficient;
- concept shift / event-meaning change remains plausible.

Simple 24h room did not generalize.
Path efficiency weakened against simpler displacement/momentum controls.

## 7. MENV-004 — current benchmark

Causal event-relative dimensions:

```text
structural_scale = planned sweep-extreme risk / D1 ATR
acceptance_scale = M5 acceptance margin / D1 ATR
```

Past expanding median is computed from earlier same-market broad-direct opportunities only.

Valid after 20 prior opportunities.

```text
HIGH_HIGH = scale > past median(scale)
            AND
            acceptance > past median(acceptance)
```

Pre-trade population:
- 620 broad-direct opportunities;
- 540 causal-state-valid;
- 163 HIGH_HIGH parents;
- 151 filled;
- 144 accepted after opposite-direction exposure control.

Exposure-adjusted economics:

```text
N 144
WR 33.33%
avg winner +3.484R
EV +0.495R
total +71.25R
DD 15.25R
loss streak 10
12/13 market-years positive
```

Market EV:

```text
BTCUSD +0.673R
GOLD   +0.493R
XAUEUR +0.539R
USDJPY +0.090R
```

Directions:

```text
LONG 84 trades / EV +0.607R
SHORT 60 trades / EV +0.338R
```

This is the strongest current V6 cross-environment H benchmark.

## 8. MENV-004 stage facts

For the same 144 accepted entries:

```text
+1R reached: 77 / 144 = 53.47%
+2R reached: 55 / 144 = 38.19%
+3R reached: 48 / 144 = 33.33%
+5R reached: 35 / 144 = 24.31%

P(+2R | +1R) = 71.43%
P(+3R | +1R) = 62.34%
P(+5R | +1R) = 45.45%
```

Interpretation:
- Entry -> +1R survival already exceeds 50% in this research population;
- realized WR remains 33% because current lifecycle gives many +1R survivors back;
- exit research must preserve the large-winner tail rather than force every trade out at +1R.

Oracle diagnostic only, not a strategy:
if +1R survivors that fail before +3R could be harvested at +1R while +3R/+5R runners remained unchanged, the same 144 entries could theoretically support roughly:

```text
WR 53.47%
avg winner about 2.55R
EV about +0.90R
```

This proves feasibility, not causal implementability.

## 9. Exit/continuation falsification after MENV-004

Mechanical +1R partial/BE controls:

```text
25% partial:
WR 53.47%
avg winner 1.468R
EV +0.319R

50% partial:
WR 53.47%
avg winner 1.312R
EV +0.236R
```

They solve WR by damaging payoff; not final candidates.

MENV-005 M5 structural hard lock:

```text
N 144
WR 42.36%
avg winner 2.030R
EV +0.284R
```

Closed/degraded: too many genuine TP5 runners cut early.

MENV-006 completed-close M5 protected-break exit:

```text
N 144
WR 40.97%
avg winner 2.091R
EV +0.278R
```

Closed/degraded.

MENV-007 to MENV-010 shadow studies showed:
- first correction is common in both failures and genuine runners;
- first opposite/local break is not sufficiently pure;
- first M5 close acceptance does not stably separate continuation;
- losing the +1R milestone after correction still occurs in many eventual +3R/+5R winners.

Do not equate clean path with runner quality.

MENV-011 one-time +0.5R lock after +1R:

```text
N 144
WR 53.47%
avg winner 1.104R
EV +0.125R
```

Closed. It preserves full position size but still destroys too much large-winner payoff. No 0.4R/0.6R rescue.

## 10. Trade-count expansion falsification

MENV-012 replaced the HH AND with a natural compensation product:

```text
(scale / past median scale)
x
(acceptance / past median acceptance)
> 1
```

Same exposure rule:

```text
239 trades
WR 27.20%
avg winner 3.288R
EV +0.166R
total +39.75R
DD 29.5R
```

Trade count increased 66%, but quality and breadth degraded; USDJPY became negative.

Conclusion:
- more trades cannot be manufactured by simply relaxing HH;
- scale and acceptance appear to need independent confirmation for the large-payoff H role.

## 11. Non-H reaction study

MENV-013 examined causal-valid non-H broad-direct events.

Trigger-close was frequently revisited:

```text
359 fills
311 checkpoint hits
86.63% checkpoint frequency
```

But trigger-close payoff under the H sweep-extreme risk geometry was tiny, with market medians around only a few hundredths of R.

Interpretation:
- non-H is not necessarily directionally wrong;
- the local reaction is often real;
- the known H risk/destination geometry cannot monetize it economically.

MENV-014 then used the local M5 broken level as SL and trigger close as TP.

It failed strongly:
- GOLD22 19 fills / WR 15.8% / EV about -0.692R;
- GOLD23-25 73 / 15.1% / -0.732R;
- XAUEUR 62 / 11.3% / -0.802R;
- USDJPY 60 / 5.0% / -0.869R;
- BTCUSD 121 / 5.8% / -0.845R.

Same-M1 fill/invalidation ambiguity was common and conservatively counted against the strategy.

Do not widen the M5 stop by an optimized multiplier to rescue this consumed result.

## 12. L-specific research

The project also tested a broad L/correction-completion population of roughly 301 candidates.

Overall +1R survival was around the low-40% range and varied strongly by environment.

Tested L ideas included:
- parent-relative scale/acceptance;
- parent-liquidity reclaim;
- M1 clean/direct transfer;
- higher-TF alignment;
- M1 renegotiation;
- M30 process persistence.

They did not generalize.

L10 `M30 VR12 > 1` improved pooled numbers but failed environment recurrence:

```text
persistent +1R about 46.4% / EV about -0.083R
nonpersistent +1R about 37.1% / EV about -0.223R

environment +1R improvement: 3/7
environment EV improvement: 2/7
```

L10 closed. Do not tune q/window.

## 13. Extra-market breadth attempt

Available 2025-09-17 to 2025-12-30 raw M1:

```text
GAUCNH broad-direct 13
XAUCNH broad-direct 11
GAUUSD broad-direct 8
XAUJPY broad-direct 7
```

No market reaches the frozen 20-prior-opportunity baseline needed by MENV-004. Do not lower the history requirement. Acquire longer history if these markets are used later.

## 14. New active research question — direction authority

Previous indicator work mostly did:

```text
local/V3 event already picks direction
-> indicator agrees or disagrees
```

This may be structurally too late.

The active V6-003 question is now:

> Can completed higher/intermediate-timeframe indicators and market state form a causal LONG/SHORT/NEUTRAL directional prior before the local liquidity/ownership event finalizes direction, with price structure then used primarily for timing and risk?

Conceptual target:

```text
directional prior/state -> WHERE / WHICH DIRECTION
liquidity/structure     -> WHEN / ENTRY GEOMETRY
scale x acceptance      -> DESTINATION AUTHORITY
```

This is not authorization to buy/sell from indicators alone.

## 15. Exact next task

Read `V6_003A_DIRECTIONAL_PRIOR_RESEARCH_CONTRACT.md`.

Do not continue MENV exit tuning first.

The next work is:

1. current web/literature review of directional/regime evidence;
2. freeze a minimal interpretable pre-event directional-prior atlas before outcomes;
3. compute priors before local direction finalization on all 13 research environments;
4. compare `ALIGNED / OPPOSED / NEUTRAL` relative to local events;
5. compare against simpler displacement/momentum and existing H1/M30 structure direction;
6. if a prior has recurrent meaning, construct one raw-replay direction-routing architecture;
7. report trade count and trade density, not only EV;
8. do not use directional state only as another veto unless economically and architecturally justified.

## 16. Hard restrictions

- no GOLD 2021;
- no AUC-driven promotion;
- no indicator/window/threshold tournament;
- no market-specific threshold rescue;
- no automatic H variable -> L variable;
- no cross-stage migration without a new contract;
- no production EA change yet;
- no forcing every +1R survivor into a 1R winner;
- no lowering MENV-004 20-history requirement to include short datasets;
- no trade-count collapse hidden behind pooled EV.
