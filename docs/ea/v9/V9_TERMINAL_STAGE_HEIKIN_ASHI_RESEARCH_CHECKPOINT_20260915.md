# V9 Terminal-Stage Heikin-Ashi Research Checkpoint

Date: `2026-09-15`
Status: `CONSUMED-DATA SHADOW RESEARCH / HINDSIGHT ORACLE INCLUDED / NOT STRATEGY AUTHORITY`
Market: `GOLD# ONLY`
Base GitHub HEAD: `da0bf0592f1d5d447f224803182dec57fcf5d8b7`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## 1. Research motivation

The active prototype's Anchor exits at `CHALLENGE_OPENS`. Chart review showed that some high-quality journeys, especially large winning moves, can give back substantial unrealized profit before the opposite H4-liquidity Arrival finally opens challenge.

H4 Heikin-Ashi was proposed as a trend-smoothing exit observation:

```text
LONG  -> first/second completed bearish H4 HA
SHORT -> first/second completed bullish H4 HA
```

The intended role is profit protection, not new entry direction.

## 2. Frozen Heikin-Ashi definition

For each completed H4 source bar:

```text
HA_CLOSE = (O + H + L + C) / 4

first HA_OPEN = (O + C) / 2
later HA_OPEN = (previous HA_OPEN + previous HA_CLOSE) / 2

bull = HA_CLOSE > HA_OPEN
bear = HA_CLOSE < HA_OPEN
```

`HA1` = first completed opposite-color H4 HA.

`HA2` = second consecutive completed opposite-color H4 HA.

The signal becomes known only at the H4 bar-completion boundary. Screening exits use that source H4 close. Structural/base exit remains first if it occurred earlier.

H4 OHLC parity was checked against authoritative M1 before the initial HA study.

## 3. First experiment — HA armed from Anchor entry

Population: `295` deterministic Anchors shared by BASE/HA comparisons.

| Exit | PnL | PF | WR | DD | Median hold | Median peak-to-exit giveback |
|---|---:|---:|---:|---:|---:|---:|
| BASE CHALLENGE/SL | +4,194.36 | 2.331 | 43.73% | 292.94 | 70.6h | 2.20 ATR180 |
| HA1 from entry | +2,089.18 | 1.965 | 47.80% | 316.46 | 19.2h | 1.25 ATR180 |
| HA2 from entry | +2,490.10 | 2.013 | 45.76% | 316.77 | 27.9h | 1.52 ATR180 |

Result:

- HA does reduce giveback and shortens exposure;
- HA1 is more sensitive than HA2;
- both materially reduce total Anchor PnL because normal mid-journey pullbacks are mistaken for termination;
- ordinary H4 candle-color controls were worse than HA, supporting that HA smoothing itself contains useful information.

This rejects `arm HA immediately after Anchor entry` as a direct replacement exit.

## 4. Journey decomposition of the failure

The HA-from-entry result was not uniformly bad.

The main pattern was:

```text
short/weak journey
-> early opposite HA often cuts loss/giveback usefully

long multi-Child journey
-> early opposite HA often appears during normal pullback
-> large right-tail winner is cut too early
```

Therefore the research focus shifted from `is HA good?` to `when should HA have exit authority?`.

## 5. Terminal activation oracle design

A deliberately non-causal oracle was used to answer only this upper-bound question:

> What if HA monitoring started only after the route's true final accepted Child?

Definition:

1. build the existing accepted-Child route ledger causally;
2. after the full outcome is known, identify the route's last accepted Child;
3. mark its entry time as `TERMINAL_ORACLE_ARMED_AT`;
4. ignore every opposite HA before that time;
5. after that time, use HA1 or HA2;
6. if current role exit/SL occurs earlier, current exit wins;
7. compare Anchor-only HA versus closing every still-open Child at the HA event.

The `true last accepted Child` is **future information**. This test is not a candidate live rule. It estimates the maximum value of correct activation timing.

## 6. Deterministic population

Source role-based ledger:

```text
1,250 accepted Children
1,139 deterministic resolved Children used for economic comparison
295 deterministic ANCHOR
844 deterministic CONTINUATION
```

Base M1 role policy:

```text
PnL +8,530.74
PF 2.023
WR 65.58%
DD 440.35
```

## 7. Oracle results — strategy wide

| Policy | N | PnL | Delta vs BASE | PF | WR | DD | Changed exits |
|---|---:|---:|---:|---:|---:|---:|---:|
| BASE | 1,139 | +8,530.74 | — | 2.023 | 65.58% | 440.35 | 0 |
| terminal HA1, Anchor only | 1,139 | +12,173.84 | +3,643.10 | 2.732 | 68.83% | 328.57 | 211 |
| terminal HA2, Anchor only | 1,139 | +11,167.85 | +2,637.11 | 2.505 | 67.52% | 355.54 | 168 |
| **terminal HA1, all still-open Children** | **1,139** | **+13,863.22** | **+5,332.48** | **3.475** | **70.41%** | **288.75** | **320** |
| terminal HA2, all still-open Children | 1,139 | +12,102.57 | +3,571.83 | 2.853 | 68.83% | 289.85 | 247 |

The strongest upper bound is `terminal HA1 -> close all still-open Children`.

Relative to BASE:

```text
PnL +62.5%
PF  2.023 -> 3.475
WR  65.58% -> 70.41%
DD  440.35 -> 288.75
```

Again: this is not causal validation.

## 8. Year-by-year oracle result

### terminal HA1, all still-open Children

| Entry year | BASE PnL | HA1 oracle PnL | Delta |
|---|---:|---:|---:|
| 2022 | +234.66 | +914.82 | +680.16 |
| 2023 | +867.71 | +1,322.78 | +455.07 |
| 2024 | +1,287.89 | +2,001.39 | +713.50 |
| 2025 | +2,711.21 | +4,244.12 | +1,532.91 |
| 2026 | +3,429.27 | +5,380.11 | +1,950.84 |

All five entry years improve in this hindsight upper bound.

### terminal HA2, all still-open Children

| Entry year | BASE PnL | HA2 oracle PnL | Delta |
|---|---:|---:|---:|
| 2022 | +234.66 | +671.25 | +436.59 |
| 2023 | +867.71 | +1,205.92 | +338.21 |
| 2024 | +1,287.89 | +1,832.39 | +544.50 |
| 2025 | +2,711.21 | +3,558.77 | +847.56 |
| 2026 | +3,429.27 | +4,834.24 | +1,404.97 |

HA1 is the stronger oracle candidate once activation timing is perfect.

## 9. Role decomposition

### ANCHOR

```text
BASE             +4,194.36 / PF 2.331 / WR 43.73% / DD 292.94
terminal HA1     +7,837.46 / PF 5.254 / WR 56.27% / DD 154.10
terminal HA2     +6,831.47 / PF 4.057 / WR 51.19% / DD 207.53
```

### CONTINUATION

```text
BASE             +4,336.38 / PF 1.836 / WR 73.22% / DD 268.05
terminal HA1     +6,025.76 / PF 2.603 / WR 75.36% / DD 172.16
terminal HA2     +5,271.10 / PF 2.226 / WR 75.00% / DD 198.56
```

Under HA1 all-open, `109` Continuation exits change in addition to `211` Anchor exits.

This means the terminal HA event potentially resolves the entire remaining route exposure, not only the Anchor runner.

## 10. Direction decomposition

### UP

```text
BASE             +6,969.65 / PF 2.826
terminal HA1     +9,904.71 / PF 4.938
terminal HA2     +8,673.63 / PF 3.862
```

### DOWN

```text
BASE             +1,561.09 / PF 1.345
terminal HA1     +3,958.51 / PF 2.283
terminal HA2     +3,428.94 / PF 1.979
```

Both sides improve in the oracle. No direction-specific rule is justified.

## 11. Journey decomposition

Using full accepted-Child count per route and summing deterministic resolved Children:

```text
302 routes contain at least one deterministic resolved Child
65 SINGLE routes
237 MULTI routes
```

### SINGLE

```text
BASE          -952.33 / PF 0.269
terminal HA1  -281.54 / PF 0.650
terminal HA2  -546.94 / PF 0.414
```

### MULTI

```text
BASE          +9,483.07 / PF 3.688
terminal HA1 +14,144.76 / PF 8.786
terminal HA2 +12,649.51 / PF 6.130
```

This is the key contrast with HA-from-entry: terminal activation preserves and improves the multi-Child right tail instead of cutting it early.

## 12. Interpretation

The best current interpretation is:

```text
Heikin-Ashi is not a reliable universal Journey-end detector.
Heikin-Ashi may be a strong reversal/profit-protection event after terminal participation has already been reached.
```

Role split:

```text
liquidity / route state
-> determine whether terminal participation is plausible

Heikin-Ashi
-> after arming, detect actual H4 momentum reversal
```

This separates `where are we in the journey?` from `has momentum now reversed?`.

## 13. What must not be promoted

Do not promote:

- `true last Child` itself;
- `Nth Child` or `4+ Child` thresholds;
- fixed route age/duration;
- fixed MFE threshold;
- HA1/HA2 as current authority;
- direction-specific HA rules;
- the gross oracle economics as expected live PnL.

The `last Child` is only the answer-sheet boundary used to show that activation timing contains large potential value.

## 14. Next research implication

The next task is no longer broad exit-feature search.

It is:

> Build the simplest causal estimate of `TERMINAL_STAGE` that reproduces enough of the oracle activation benefit to improve sequential economics, while preserving large multi-Child right-tail journeys.

Use `V9_NEXT_RESEARCH_CONTRACT_TERMINAL_STAGE_CAUSAL_DETECTION_20260915.md`.

## 15. Execution caveat

This checkpoint uses consumed-data M1/H4 close-price screening. H4 HA close exits have not yet been re-run through MT5 actual real ticks with executable Bid/Ask fills, gap handling, market-closed retries, commission/swap, or restart behavior.

Any future causal candidate must pass those layers before strategy authority can change.
