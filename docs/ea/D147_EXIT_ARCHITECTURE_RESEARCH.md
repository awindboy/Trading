# D-147 EXIT ARCHITECTURE RESEARCH V1

Status: `GOLD 2025 THREE-MODE RESULT RECORDED / CROSS-MARKET NOT YET VALIDATED`

Build target:

```text
1.93R1L9 / EXIT_ARCHITECTURE_RESEARCH_V1
```

Strategy authority: `NONE — controlled research variant`

Baseline authority remains `AGENTS.md` / `EA_SPEC.md`. `2021` remains untouched.

## Research question

How much of the current realized-performance problem is caused by post-fill profit giveback rather than Entry survival?

D-144/D-145 established that many fills make meaningful favorable R before the existing structural-objective architecture eventually realizes a loss. D-145 also established that `Fill -> +1R` survival is a separate unsolved problem. D-147 therefore changes only post-fill management and keeps Entry and initial geometry identical.

## Frozen common geometry

All three modes use the exact same:

```text
scenario authorization
Root / Sweep / CHoCH / FVG pipeline
Entry
position sizing
original normalized SL
frozen structural objective
initial structural TP
```

The structural TP remains attached in every mode in D-147. Removing it would be a separate future experiment.

## Mode 0 — ORIGINAL

```text
V1_EXIT_ORIGINAL
```

No post-fill D-147 action is allowed. The filled position remains owned by the original server SL/TP exactly as in the D-146 baseline.

This mode is the control and must pass canonical event parity against D-146 before the other modes can be interpreted.

## Mode 1 — R_STEP_TRAILING

```text
V1_EXIT_R_STEP_TRAILING
```

At actual fill, freeze forever:

```text
R0 = abs(actual_fill - original_normalized_SL)
```

Use executable exit-side price:

```text
LONG  -> Bid
SHORT -> Ask
```

When a new integer R milestone is observed:

```text
+1R -> move SL to  0R (actual fill)
+2R -> move SL to +1R
+3R -> move SL to +2R
+4R -> move SL to +3R
...
```

If price gaps across multiple integer-R levels before the next observed tick, the SL catches up directly to the latest causally observed staircase level. R is never recomputed after the SL changes.

The modification waits if the broker stops/freeze distance makes the target SL illegal. An OrderSend rejection is logged and retried; such a run must be treated as execution-impaired research evidence until reviewed.

## Mode 2 — R_STEP_PARTIAL

```text
V1_EXIT_R_STEP_PARTIAL
```

At each newly reached integer R milestone, close:

```text
50% of CURRENT remaining volume
```

Examples before broker volume normalization:

```text
1.00 -> +1R close 0.50 -> 0.50 remains
0.50 -> +2R close 0.25 -> 0.25 remains
0.25 -> +3R close 0.125 -> 0.125 remains
```

The fraction is hard-frozen at `0.50` and is deliberately **not** an input. D-147 does not optimize the partial percentage.

Partial volume is normalized down to the broker volume step. A partial is valid only if both the close volume and the remaining volume satisfy broker minimum-volume requirements. If a true partial is impossible:

```text
DO NOT substitute a full close
DO NOT alter SL/TP
mark partial management disabled for that position
let the remainder continue on original SL + structural TP
```

Only one pending integer-R partial is submitted per observed tick. If price gaps across multiple R steps, the later steps remain causally queued and can execute on later ticks while the position is still open.

## Realized accounting

Partial mode creates multiple exit deals for one position. Therefore D-147 aggregates every `DEAL_ENTRY_OUT / OUT_BY / INOUT` deal belonging to the position when the position finally closes.

Final trade net money is:

```text
entry commission + entry fee
+ sum(exit deal profit)
+ sum(exit deal commission)
+ sum(exit deal swap)
+ sum(exit deal fee)
```

Research trade R is calculated from the frozen actual-fill risk money:

```text
net_R = realized_net_money / actual_fill_risk_money
```

A realized winner is defined as `net_R > 0`, not merely “a partial was taken.”

## Explicit non-goals

D-147 does not use:

```text
M30 progress threshold
remaining-room threshold
outward-refresh gate
protected-break exit
Entry veto
winner score
LONG/SHORT-specific threshold
fixed 1R or fixed 2R TP replacement
```

D-145/D-146 continuation-state evidence may be revisited only after the mechanical exit comparison is understood.

## Required validation

### A. Compile

`MentorDeterministicV1EA.mq5` must compile with `0 errors`.

### B. Baseline-control parity

Run `V1_EXIT_ORIGINAL` under the exact same Strategy Tester conditions as the D-146 baseline, preferably with `InpEnableEdgeAudit=false` for both compared performance runs.

Canonical comparator:

```powershell
python tools\compare_d147_original_baseline.py <D146_LEDGER.csv> <D147_ORIGINAL_LEDGER.csv>
```

It removes only build/audit/D147 diagnostic rows. All remaining rows must match exactly.

Required:

```text
D147 ORIGINAL PARITY: PASS
```

### C. GOLD 2025 three-mode test

Use identical conditions:

```text
Symbol: GOLD
Model: Every tick based on real ticks
InpRegimeResearchMode: V1_REGIME_BASELINE_NO_GATE
InpStopLossModel: V1_SL_ROOT_OB_DISTAL_20
InpPositionSizingMode: V1_SIZE_FIXED_RISK_MONEY
InpFixedRiskMoneyPerTrade: 100
InpEventLogMode: V1_LOG_RESEARCH_COMPACT
InpEnableEdgeAudit: false
```

Run separately:

```text
ORIGINAL
R_STEP_TRAILING
R_STEP_PARTIAL
```

For each ledger:

```powershell
python tools\summarize_d147_exit_architecture.py <ledger.csv>
```

Compare at minimum:

```text
realized net win rate
average winner net R
average loser net R
net expectancy R/trade
gross price-P&L expectancy R/trade
max closed-trade equity drawdown in R
longest losing streak
LONG / SHORT split
large-winner dependence
trailing/partial action counts
rejections / partial infeasibility
unresolved positions
```

### D. Generalization

Only after GOLD baseline parity and a clean three-mode result, expand as needed to:

```text
GOLD 2023
GOLD 2024
GOLD 2025
BTCUSD 2025
SILVER 2025
CADJPY 2025
```

Do not select a mode from one market/year and call it final. Compare relation and trade-off breadth across periods, markets, and direction.

## Promotion boundary

D-147 is an experiment, not a new strategy authority. A mode is not promoted merely because it raises total R on GOLD 2025. It must be judged against the project target:

```text
realized win rate >= 50%
average winner meaningfully > 1R
positive cost-adjusted expectancy
acceptable drawdown / streak behavior
cross-market and cross-period robustness
```

Entry survival remains a separate research branch regardless of D-147 outcome.

## GOLD 2025 three-mode result — 2026-08-21

User-provided ledgers:

```text
GOLD_original.csv  SHA-256 6cae85b2913e81e7e847fb0c7794ee7c0926f1dfae140d37bd038f735a18d7d1
GOLD_step.csv      SHA-256 462afaaf843d85b2a97a9f5287083f3c76cc83d9a426bfb7e21ca82f34acb2ab
GOLD_particial.csv SHA-256 13b9ed5b95f3ec1db6a8138c10746f5f89f800f8e484c795d600e99c946c58ee
```

All modes retained the same 58 fills / 58 closes and zero execution divergence. The same Entry / initial SL / structural TP population was preserved.

All-scope cost-adjusted net result:

| Mode | WR | Avg winner | Avg loser | Expectancy | Total net R | Max DD | Loss streak |
|---|---:|---:|---:|---:|---:|---:|---:|
| ORIGINAL | 24.14% | +3.827R | -1.092R | +0.095R | +5.532R | -23.00R | 11 |
| R_STEP_TRAILING | 29.31% | +1.623R | -0.685R | -0.008R | -0.478R | -9.35R | 9 |
| R_STEP_PARTIAL | 43.10% | +1.419R | -0.867R | +0.118R | +6.864R | -9.00R | 8 |

Continuation-only (51 trades):

```text
ORIGINAL: WR 27.45%, expectancy +0.254R, avg winner +3.827R, max DD 19.53R
TRAILING: WR 31.37%, expectancy +0.015R, avg winner +1.540R, max DD 8.10R
PARTIAL:  WR 47.06%, expectancy +0.187R, avg winner +1.402R, max DD 7.66R
```

The 21 continuation trades that never reached +1R were identical across all three modes. Among 16 ORIGINAL trades that reached +1R and later realized a loss, PARTIAL improved all 16 and converted 10 into positive net trades, while preserving all 14 original continuation winners as positive trades. TRAILING protected giveback but cut too many large winners.

Interpretation: mechanical PARTIAL is the strongest GOLD-2025 exit candidate, but it still reduces large-winner payoff and is not cross-market validated. A later smart-partial study may use the already-discovered +1R continuation state, but is not part of D-148.

Instrumentation caveat: D147_* action rows are suppressed under RESEARCH_COMPACT, so execution-action counts were not directly visible in these three ledgers. The realized trade accounting and identical fill population remain usable; D-147 action-log QA remains separate.

## D-149 handoff from mechanical partial to Smart Partial

D-147 mechanical `R_STEP_PARTIAL` remains a control. D-149 does not tune it. The new `SMART_PARTIAL` changes the architecture in one deliberate way: one partial at +1R, fraction selected by the D145/D146 +1R M30 continuation geometry, then +2R BE protection with no further mechanical partials. This is intended to preserve large structural winners that D-147 repeatedly cut at every integer R.
