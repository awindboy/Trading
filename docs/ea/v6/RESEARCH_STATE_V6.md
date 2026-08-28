# V6 Research State

Status: `ACTIVE`  
Date: `2026-08-28`  
Phase: `V6-002 PRECISION-PRESERVING STATE-ROUTED ARCHITECTURE RESEARCH`  
Production authority: `NONE`  
Promoted candidate: `NONE`  
Research benchmark: `R2 primary / R2P alternate`  
Primary market: `GOLD#`

## Generation boundary

```text
V5 CLOSED
V6 ACTIVE
```

V6 exists to solve the V3 period/market generalization limitation by identifying causal market state and using it to change strategy mechanism, not by ranking old V3 trades.

## Current methodology

```text
state construct
-> causal availability / semantic check
-> mechanism hypothesis
-> raw replay creates new trades
-> compare V3 vs V6 full economics
-> recursive falsification
```

AUC is not a promotion criterion. AI/ML is not an active route.

## Completed evidence

### V3 baseline

GOLD 2023-2025 Candidate B:

```text
53 trades
WR 52.83%
avg+ 2.775R
EV +0.994R
```

GOLD 2022 consumed validation:

```text
24 trades
WR 25.0%
avg+ 1.458R
EV -0.385R
```

### V6 R1

Rejected. Broad-event DMI/ADX continuation router produced only +0.055R EV with poor breadth and DD 16.5R.

### V6 R2 GOLD 2023-2025

```text
75 trades
WR 41.33%
avg+ 2.924R
EV +0.622R
DD 10R
2023/24/25 positive
LONG/SHORT positive
```

### V6 R2P GOLD 2023-2025

```text
75 trades
WR 44.0%
avg+ 2.300R
EV +0.452R
DD 8.5R
```

### GOLD 2022 historical stress comparison

```text
R2  : 40 trades / WR 35.0% / avg+ 2.428R / EV +0.200R / DD 6.75R
R2P : 40 trades / WR 37.5% / avg+ 1.966R / EV +0.112R / DD 7.5R
```

R2 did not collapse like V3, but Q4 generated most of the annual profit.

Module stability:

```text
R2 H: +0.704R development -> +0.538R 2022
R2 L: +0.293R development -> -0.429R 2022
```

### Cross-market architecture diagnostic

```text
             V3 EV       R2 EV      R2P EV
XAUEUR      -0.247      -0.353      -0.284
USDJPY      -0.135      -0.017      -0.108
BTCUSD      +0.090      -0.334      -0.310
```

R2 is therefore a meaningful GOLD period-robustness benchmark, not a universal market architecture.

## Current scientific interpretation

The strongest surviving interpretation is:

> V3 local reaction/requalification semantics contain useful precision, while market-state measurements may be better used to decide strategic destination and maturity than to replace the precision substrate.

The current H4 ADX result is interpreted as a maturity/consumption clue, not generic trend-following strength.

The L mechanism needs its own state hypothesis. `H condition false -> L` is not supported.

## Active question

`R3 H-MATURITY`:

> Can the V3 Candidate-B H precision substrate be preserved while H4 maturity selectively authorizes the H large-payoff destination?

Read `V6_002_R3_PRECISION_PRESERVING_H_STATE_CONTRACT.md` before execution.

## Competing explanations still open

```text
selection/multiplicity
covariate shift
hidden/omitted context
concept shift
event-formulation insufficiency
market suitability
execution environment
```

No single cause is promoted.

## Evaluation policy

Research candidates are judged on a vector, not one threshold:

```text
N / WR / avg winner / avg loser / EV / total R
DD / streak / annual breadth / direction breadth
module contribution / winner concentration / execution sensitivity
```

Final promotion still requires WR>=50%, avg positive NET R>=2R, positive cost-adjusted EV, and independent validation.

## Validation/data status

```text
GOLD 2023-2025   CONSUMED RESEARCH
GOLD 2022        CONSUMED HISTORICAL COMPARISON
XAUEUR/USDJPY/BTCUSD 2023-2025 CONSUMED ARCHITECTURE DIAGNOSTICS
GOLD 2021        UNTOUCHED
```

## Hard stops

- no AUC-driven strategy selection;
- no indicator/window/threshold tournament;
- no market-specific threshold rescue;
- no defining L as inverse H without separate evidence;
- no automatic cross-stage variable reuse;
- no production EA change;
- no GOLD 2021.
