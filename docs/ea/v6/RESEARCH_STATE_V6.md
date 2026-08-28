# V6 Research State

Status: `ACTIVE`
Date: `2026-08-29`
Phase: `V6-003 MULTI-ENVIRONMENT DIRECTIONAL-PRIOR RESEARCH`
Production authority: `NONE`
Promoted production candidate: `NONE`
Current research benchmark: `MENV-004 PRETRADE SCALE x ACCEPTANCE H`
Base HEAD for this documentation update: `ced2bb276ce6471162bcc49af3522eaa3d038694`

## 1. Research allocation

Consumed research panel:

```text
GOLD 2022-2025
XAUEUR 2023-2025
USDJPY 2023-2025
BTCUSD 2023-2025
```

13 market-year environments.

```text
GOLD 2021 = UNTOUCHED
```

These 13 environments are explicitly research/development/falsification data. Future final validation requires newly frozen untouched data.

## 2. Generation history

### V3 Candidate B control

GOLD 2023-2025:

```text
53 trades
WR 52.83%
avg+ 2.775R
EV +0.994R
```

GOLD 2022:

```text
24 trades
WR 25.0%
avg+ 1.458R
EV -0.385R
```

This collapse remains the central design constraint.

### V6 R1

Rejected directional/maturity router:

```text
41 trades
WR 29.27%
avg+ 2.604R
EV +0.055R
DD 16.5R
```

M5 DMI direction was largely redundant with the event's own M5 transition.

### V6 R2 / R2P

R2 GOLD 2023-2025:

```text
75 trades
WR 41.33%
avg+ 2.924R
EV +0.622R
DD 10R
```

R2P:

```text
75 trades
WR 44.0%
avg+ 2.300R
EV +0.452R
DD 8.5R
```

R2 improved GOLD period robustness but failed universal market portability.

### R3

R3 development result:

```text
31 trades
WR 77.42%
avg+ 2.643R
EV +1.821R
total +56.438R
DD 1R
```

Portability failed. ADX H-state relation reversed on some independent markets.

### R4

R4 development result:

```text
36 trades
WR 69.44%
avg+ 2.718R
EV +1.582R
total +56.938R
DD 2R
```

High-ADX directional alignment recovered some H, but did not fix 2022/cross-market generalization.

## 3. Multi-environment methodological reset

The project stopped treating GOLD 2023-2025 as the default development truth.

Research now asks:

```text
Does the same named state retain strategic meaning
across market-year environments?
```

Important negative recurrences:
- no universal standalone conventional indicator;
- ADX level is not universal H meaning;
- V3 Candidate-A precision can reverse;
- M30 expansion-only delivery can reverse;
- simple structural room failed;
- path efficiency weakened to simple momentum/displacement;
- L requires separate state research.

## 4. MENV-004 current benchmark

Frozen causal pre-trade state:

```text
scale = planned sweep-extreme risk / D1 ATR
acceptance = M5 acceptance margin / D1 ATR
```

Historical reference:
- same market;
- earlier broad-direct opportunities only;
- expanding median;
- current opportunity excluded;
- state valid after 20 prior opportunities.

```text
HIGH_HIGH = scale > past scale median
            AND
            acceptance > past acceptance median
```

Opportunity counts:

```text
broad-direct opportunity N = 620
state-valid N               = 540
HIGH_HIGH parent N          = 163
filled N                    = 151
accepted after exposure N   = 144
```

Economics:

```text
WR          33.33%
avg winner  +3.484R
avg loser   -1R
EV          +0.495R/trade
total       +71.25R
max DD      15.25R
loss streak 10
```

Environment breadth:
- 12/13 market-years positive;
- only USDJPY 2025 negative.

Market totals:
- BTCUSD +32.5R across 49 trades;
- GOLD +18.75R across 38;
- XAUEUR +17.25R across 32;
- USDJPY +2.25R across 25.

Direction:
- LONG 84 / EV +0.607R;
- SHORT 60 / EV +0.338R.

## 5. MENV-004 path decomposition

```text
+1R 77 / 144
+2R 55 / 144
+3R 48 / 144
+5R 35 / 144
```

So:

```text
Fill -> +1R = 53.47%
+1R -> +2R = 71.43%
+1R -> +3R = 62.34%
+1R -> +5R = 45.45%
```

The final 50% WR target is therefore not blocked solely by Entry survival inside MENV-004.

## 6. Exit research state

Closed/degraded:
- 25% +1R partial + BE: WR 53.47%, avg winner 1.468R, EV +0.319R;
- 50% +1R partial + BE: WR 53.47%, avg winner 1.312R, EV +0.236R;
- MENV-005 structural lock: WR 42.36%, avg winner 2.030R, EV +0.284R;
- MENV-006 protected-break exit: WR 40.97%, avg winner 2.091R, EV +0.278R;
- MENV-011 one-time +0.5R lock: WR 53.47%, avg winner 1.104R, EV +0.125R.

Main lesson:

> Simple profit protection converts giveback into wins but destroys the large-winner payoff needed by the project.

Shadow MENV-007/008/009/010 also showed that normal runners frequently undergo correction, opposite local movement, or temporary loss of the +1R milestone.

Do not equate clean path with winner continuation.

## 7. Trade-count / relaxed-state research

MENV-012 increased accepted N:

```text
144 -> 239
```

but degraded:

```text
WR 27.20%
avg winner 3.288R
EV +0.166R
DD 29.5R
```

USDJPY became negative.

Interpretation:
- trade count matters;
- but low-quality event restoration is not a valid way to meet the count objective.

## 8. Non-H research

MENV-013:
- 359 non-H fills;
- 311 trigger-close checkpoint hits;
- 86.63% local checkpoint frequency.

The local reaction is common, but the reward relative to H sweep-extreme risk is economically tiny.

MENV-014 local M5 stop/trigger target failed severely across every market segment.

Interpretation:

```text
not HIGH_HIGH
!= no directional reaction

not HIGH_HIGH
= often local reaction without known large-payoff monetization geometry
```

This is a mechanism clue, not a tradable module.

## 9. L research state

Independent L research was performed rather than defining `not H -> L`.

A broad L2-style population supplied much larger candidate N but weak and unstable Entry survival.

Parent-relative geometry, liquidity reclaim, M1 direct/clean, higher-TF alignment, renegotiation, and M30 persistence did not produce a robust cross-environment state.

L10 VR12 persistence closed after poor environment recurrence.

L remains open scientifically but has no current promoted mechanism.

## 10. Trade-count state

MENV-004 accepted N by market:

```text
BTCUSD 49
GOLD   38
XAUEUR 32
USDJPY 25
```

N by environment is uneven; USDJPY 2023 has only 2 accepted trades.

Therefore:
- pooled 144 is useful discovery evidence, not sufficient final proof;
- direction/exit studies on only the +1R survivors (77 total) quickly create 1-3 trade cells;
- before over-engineering exit state, widen the usable research universe or develop an independent module.

## 11. Short additional gold-like data

2025-09-17 to 2025-12-30:
- GAUCNH 13 broad-direct;
- XAUCNH 11;
- GAUUSD 8;
- XAUJPY 7.

All fail the frozen 20-prior-history requirement for MENV-004 state initialization.

Do not lower 20.

## 12. Current architectural question

The project is now regressing above MENV-004.

Potential V3 limitation:

> Local deterministic structure may have been given too much authority over trade direction itself.

Earlier V6 directional indicators were mostly tested after the local event already chose direction, so they often duplicated the event.

New target:

```text
causal directional prior
-> local liquidity/structure confirmation and timing
-> event quality / destination routing
```

Indicators may participate in direction authority if they add independent, recurrent information.

They do not receive permission to trade without price structure.

## 13. Active next child

`V6_003A_DIRECTIONAL_PRIOR_RESEARCH_CONTRACT.md`

The next result must not be another exit tweak.

## 14. Final promotion gate remains

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
