# V10 Bounded-m3 Actual-Tick Diagnostic — Execution-Fidelity Findings

Date: `2026-09-16`  
Status: `ACTUAL-TICK DIAGNOSTIC / EXECUTION-SEMANTIC DEFECT FOUND / NOT VALIDATION PASS`  
Market: `GOLD# ONLY`  
Reference GitHub HEAD: `8f20e02065ab7a530d685d516a9efb928a592ead`  
Tester EA: `V10_HA_BoundedM3_ActualTickReplay_R0`  
Production authority: `NONE`

## 1. Purpose

This document records the first actual-tick Strategy Tester run of the exact reproducible V10 bounded-m3 selected-entry ledger.

The goal was execution fidelity, not another model scan.

Inputs produced by the test:

```text
V10_bounded_m3_actual_tick_events.csv
ReportTester-318585216.xlsx
```

The raw tester headline is **not** accepted as strategy performance because a market-closed campaign-exit defect changed holding time and exposure.

## 2. Frozen M1-screening reference

Persisted bounded-m3 research reference:

```text
selected entries       1,159
units                   2,313
PnL                   +14,827.57
PF                       1.553395
DD                     2,638.04
structural R           +388.88R
max single order             3
max concurrent              12
Oracle recall             80.42%
Oracle precision          39.34%
```

## 3. Raw MT5 Tester result

Tester settings:

```text
GOLD#
M1
2024-01-01 through 2026-09-15 tester interval
100% real ticks
initial deposit $10,000
1:500 leverage
unit lot 0.01
```

Headline:

| Metric | Raw actual-tick tester |
|---|---:|
| Closed positions | **984** |
| Deals | 1,968 |
| Net profit | **+$16,220.67** |
| Gross profit | +$39,846.87 |
| Gross loss | -$23,626.20 |
| Profit Factor | **1.686554** |
| Balance max DD | $1,959.66 / 8.52% |
| Equity max DD | **$3,960.22 / 15.27%** |
| Sharpe | 2.899708 |
| Win rate | 38.82% |
| Largest win | +$2,414.28 |
| Largest loss | -$319.62 |
| LONG | 606 / 41.09% won |
| SHORT | 378 / 35.19% won |

The raw PnL improvement versus M1 research must not be interpreted as an actual-tick validation win.

## 4. Event-ledger counts

Total event rows:

```text
3,273
```

Breakdown:

```text
FAST_HA_FLIP                    1,248
ENTRY_FILL                        984
FAST_NHA_EXIT                     732
ENTRY_REJECT                      174
FAST_NHA_EXIT_REJECT              134
ENTRY_REJECT_SL_ALREADY_TOUCHED     1
```

All 174 ordinary entry rejects were:

```text
retcode=10018 market closed
```

The single structural fail-closed case was:

```text
2026-07-06
SHORT Ask already at/above structural SL
```

This fail-closed behavior is consistent with the no-resurrection / fixed-SL guardrail.

## 5. Entry opportunity loss

The 1,159 selected research events decompose exactly into:

```text
984 fills
174 market-closed entry rejects
1 SL-already-touched reject
= 1,159
```

Therefore the signal set was not missing. Execution availability removed 175 selected opportunities.

Reference-ledger economics of the 175 non-filled events:

```text
347 units
M1-reference PnL +1,332.13
PF 1.306
structural R +58.03R
```

By size:

```text
1-unit rejected subset  -> about -$156.11
3-unit rejected subset  -> about +$1,488.24
```

Market closure therefore did not merely filter bad opportunities.

## 6. Common-fill parity before isolating the exit defect

For the 984 actually filled signal IDs, their M1-reference economics were:

```text
PnL +13,495.44
PF 1.60136
structural R +330.84R
```

Raw actual tick for the same filled population:

```text
PnL +16,220.67
PF 1.68655
```

Raw delta:

```text
+$2,725.23
```

This apparent improvement is dominated by a campaign-exit execution defect described below.

## 7. Critical defect: FAST-NHA exit intent was not persistent

The intended campaign comparator is:

```text
first completed opposite FAST H4 HA
-> close surviving old-direction campaign
```

Observed EA behavior when the broker was closed:

```text
opposite FAST HA finalized
-> close requested
-> retcode / condition: market closed
-> close rejected
-> exit intent not latched
-> no mandatory retry at first tradable tick
-> stale position remains alive
-> later FAST HA flips can leave it open for hours/days
```

Event evidence:

```text
FAST_NHA_EXIT_REJECT
134 rejected close requests
across 84 distinct timestamps
all recorded as market closed
```

This is not ordinary slippage. It changes strategy semantics.

## 8. Consequence: exposure inflation and opposite-campaign overlap

Raw deal reconstruction:

```text
expected research max concurrent:
12 units

observed actual-tick gross max:
16 units
```

Observed time with both LONG and SHORT gross exposure simultaneously open:

```text
~311.0 hours
```

This overlap is largely a consequence of stale campaign positions surviving failed FAST-NHA exits.

The bounded-m3 research comparator did not authorize “failed NHA exit -> hold until a later HA event”.

## 9. Concrete example: signals 640 / 641

Research ledger:

```text
signal 640
decision 2025-12-18 16:00
3 units LONG

signal 641
decision 2025-12-18 20:00
3 units LONG

intended natural FAST exit:
2025-12-19 01:00
```

M1-reference combined result:

```text
about -$9.39
```

At `2025-12-19 01:00`, the opposite FAST exit was rejected because the market was closed.

The two positions remained open until the later flip on `2025-12-23 20:00`.

Their eventual actual-tick profits were approximately:

```text
+$412.59
+$418.11
= +$830.70
```

The difference is execution-semantic contamination, not evidence that the V10 signal became better on ticks.

## 10. Affected versus normally executed trades

The execution audit identified approximately:

```text
131 filled positions
241 units
```

as materially affected by failed FAST-NHA exit persistence.

Their M1-reference economics:

```text
PnL +$1,877.37
PF ~1.910
R +72.30R
```

Raw actual-tick economics after unintended additional holding:

```text
PnL about +$4,742.48
```

Excess versus M1 reference:

```text
about +$2,865.11
```

This explains more than the entire raw `+$2,725.23` common-fill improvement; the remaining normally executed subset was slightly worse than M1.

## 11. Normal-execution parity is encouraging

Remove the 131 exit-contaminated positions.

Remaining:

```text
853 positions
```

M1-reference:

```text
PnL +$11,618.07
PF ~1.570
R +258.55R
```

Actual tick:

```text
PnL +$11,478.19
PF ~1.558
R +252.57R
```

Differences are small:

```text
PnL about -1.2%
R about -2.3%
```

Interpretation:

> where execution semantics remained comparable, the M1 first-touch research approximation did not collapse under real-tick Bid/Ask execution.

This is useful evidence, but it is not yet a complete validation because the full campaign-exit implementation was defective.

## 12. Oracle-likeness after executable entry availability

Persisted bounded m3:

```text
true Oracle bars 567
selected Oracle bars 456
recall 80.4%
precision 39.3%
```

Actual fills contained:

```text
395 Oracle=True
589 Oracle=False
```

Executable-fill view:

```text
Oracle recall:
395 / 567 = 69.7%

Oracle precision:
395 / 984 = 40.1%
```

Actual-tick economics of filled groups:

```text
Oracle=True
PnL +$31,326.25
PF ~9.84

Oracle=False
PnL -$15,105.58
PF ~0.248
```

The main V10 problem survives actual execution: destructive non-Oracle participation remains the dominant drag.

## 13. Sizing-tier evidence

Actual filled result by bounded size:

```text
1-unit:
493 trades
PnL +$2,998.35
PF ~1.527

3-unit:
491 trades
PnL +$13,222.32
PF ~1.737
```

The 3-unit tier had better unit economics in this consumed sample, so its contribution was not purely leverage multiplication.

The quartile map remains research-only.

## 14. Direction split

Actual filled result:

```text
UP / LONG-side selected signals:
606
PnL +$11,905.59
PF ~1.754

DOWN / SHORT-side:
378
PnL +$4,315.08
PF ~1.550
```

Both directions were profitable in the raw diagnostic, but the result remains materially LONG-concentrated.

## 15. Hard-SL execution tail

Broker-side structural SL generally remained close to intended `-1R`, but real gaps can exceed it.

Aggregate SL execution audit indicated an average stopped result around:

```text
-1.032R
```

A notable weekend gap around 2026-04-10 -> 2026-04-13 produced roughly:

```text
-2.58R
-2.94R
```

on two Children sharing the same structural invalidation area.

Therefore:

> structural Hard SL defines intended risk geometry; it does not guarantee account loss is capped at exactly -1R across market gaps.

## 16. Balance DD versus equity DD

Do not headline Balance DD alone:

```text
Balance max DD:
$1,959.66 / 8.52%

Equity max DD:
$3,960.22 / 15.27%
```

The equity result reflects floating exposure and is the more relevant warning for stacked V10 campaigns.

The exit-persistence defect contributed to exposure inflation.

## 17. Correct execution semantics for the next rerun

For the **exit comparator**, a completed opposite FAST H4 HA creates an immutable close intention for all surviving old-direction campaign positions.

Required validation behavior:

```text
FAST NHA finalized
-> mark old-direction survivors EXIT_PENDING

if close succeeds:
    Child closes

if close fails only because market is closed / temporarily non-tradable:
    keep EXIT_PENDING
    retry on subsequent ticks
    first executable close wins

later HA color changes:
    do NOT cancel the already-earned EXIT_PENDING state
```

Priority ordering on a tick:

```text
1. process structural Child death
2. process pending campaign exits
3. finalize newly completed H4 / create new exit intents
4. retry / execute pending exits
5. only then consider any entry decision allowed by the chosen entry-execution comparator
```

A stopped Child remains dead.

## 18. Entry rejects are a separate policy question

Do **not** silently apply the exit retry rule to entries.

Current test semantics:

```text
entry decision at timestamp
market closed
-> entry rejected / skipped
```

A separate explicit execution comparator may later test:

```text
FIRST_TRADABLE_TICK entry
```

but that is a new execution hypothesis and must report:

- delay;
- fill displacement;
- whether structural SL has already been crossed;
- whether FAST direction is still valid;
- economics versus SKIP.

No hidden no-chase threshold is allowed.

## 19. Validation status

Current evidence supports:

```text
ENTRY / SL / successful-exit subset
-> encouraging tick parity

full bounded-m3 actual-tick policy
-> NOT YET VALIDATED
```

The raw `+$16,220.67 / PF 1.687` must not be stored as promoted V10 performance.

The next valid headline must come from the unchanged bounded-m3 signal payload with corrected exit-intent persistence.

## 20. Exact next test

Rerun the same 2025-2026 executable bounded-m3 payload with:

```text
same 1,159 selected signal definitions
same 1/3 units
same structural SLs
same FAST HA formula
same entry policy as current control: timestamp fill-or-skip
same first opposite FAST H4 exit comparator

ONLY execution fix:
EXIT_PENDING persistence + retry after temporary market closure
```

Acceptance checks:

```text
no stale opposite-campaign overlap caused by rejected exits
max concurrent should return to the intended policy geometry
every market-closed NHA exit either:
    later closes at first tradable tick
    or the Child dies structurally first

all retries are ledgered with:
signal / ticket
earned exit timestamp
retry timestamp
actual close timestamp
retcode history
```

Only after this rerun should actual-tick PnL / PF / DD be compared to the M1 research reference.
