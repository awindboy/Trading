# D-149 SMART PARTIAL + EPISODE MANAGEMENT RESEARCH V1

Date: 2026-08-21  
Status: **IMPLEMENTED / LOCAL VALIDATION PENDING**  
Build: `1.95R1L11 / SP_EM_RESEARCH_V1`  
Baseline strategy authority: **UNCHANGED**  
Baseline control: `V1_EXIT_ORIGINAL + V1_EM_OFF`  
2021: **KEEP UNTOUCHED**

## 1. Purpose

D-149 begins solution research on two different causes of poor realized equity shape:

```text
A. valid +1R reaction -> later giveback
   -> Smart Partial (SP)

B. repeated losses under the same directional structural premise
   -> Episode Management (EM)
```

The two mechanisms are independent toggles and must be tested independently before the combined result is interpreted.

## 2. Required four-run matrix

```text
A. V1_EXIT_ORIGINAL      + V1_EM_OFF               baseline control
B. V1_EXIT_SMART_PARTIAL + V1_EM_OFF               SP isolated
C. V1_EXIT_ORIGINAL      + V1_EM_CAUSAL_EPISODE_V1 EM isolated
D. V1_EXIT_SMART_PARTIAL + V1_EM_CAUSAL_EPISODE_V1 SP + EM combined
```

Do not infer the effect of either component from run D alone.

## 3. Smart Partial (SP) V1

SP begins only after actual Fill. Entry, original normalized SL, position sizing, frozen structural objective and structural TP are unchanged.

R remains permanently:

```text
R0 = abs(actual_fill - original_normalized_SL)
```

### 3.1 First +1R state freeze

At the first exact observed +1R reach, freeze the causally available M30 scenario-direction state. No later M30 state is backfilled.

The primary D-145 result was that +2R runners consistently had less-mature M30 protected-to-external delivery at +1R. D-146 also pre-registered a structural, non-fitted geometry distinction:

```text
original +2R price lies before / at current M30 external
vs
original +2R price lies beyond current M30 external
```

D-149 uses exactly this structural distinction.

### 3.2 `STRONG_RUNNER`

Required at first +1R:

```text
M30 trend = scenario direction
protected available
external available
valid protected -> external span
remaining distance from +1R price to current M30 external >= 1.0 original R
```

Equivalent market meaning:

```text
current M30 external is at or beyond the original +2R price
```

Action:

```text
close 25% of CURRENT position volume once
keep approximately 75% for the frozen structural TP
```

The `1.0R` boundary is not a fitted percentile or optimized progress score. It is the direct geometric boundary for whether another full R fits before the current external.

GOLD 2025 D-146 development evidence for this structural room class was 9/11 reaching +2R. This supports research use, not promotion.

### 3.3 `DEFAULT`

If the strong definition is not satisfied, including unavailable valid M30 range:

```text
close 50% of CURRENT position volume once at/after first +1R
```

Missing M30 state is never imputed as strong.

### 3.4 No repeated haircut

Unlike D-147 `R_STEP_PARTIAL`, SP does **not** continue taking 50% of remaining volume at every integer R.

```text
+1R -> one state-dependent partial only
+2R, +3R, ... -> no additional mechanical partial
```

The purpose is to stop destroying the large-winner tail.

### 3.5 +2R break-even protection

At the first observed +2R or higher, protection has priority:

```text
remaining SL -> actual Fill price
```

The frozen structural TP remains unchanged. After the BE move, the remainder is allowed to run to structural TP or BE.

This guarantees non-negative **strategy-price R** on the remaining position after +2R; spread, commission, swap or slippage can still make the residual deal slightly negative in net-money terms.

If broker stops/freeze rules temporarily make the BE request illegal, retry on later ticks. A rejected action is logged. If a true partial is infeasible because of minimum/step volume, never substitute a full close; BE protection at +2R remains eligible.

## 4. Episode Management (EM) V1

EM is scoped only to `EXTERNAL_CONTINUATION`. Reversal behavior is unchanged.

EM does not decide that a market is bad from a score. It controls repeated exposure to the same causal directional premise.

### 4.1 Episode identity

```text
episode = frozen active_map_tf + frozen owner_id + direction
```

Thus an H1-led continuation episode remains the same episode across multiple Roots while the same H1 owner remains authority. A new owner creates a new episode.

### 4.2 Serialize same-episode exposure

At most one pending/filled exposure from the same episode may be live at once.

A second same-episode opportunity is blocked while the first is pending, filled, cancel-unresolved or execution-divergent.

This removes correlated same-owner add-ons only in the EM variant. Baseline `EM_OFF` preserves current same-direction add-on semantics.

### 4.3 First realized loss

A trade is an EM winner only if aggregate final `realized_net_money > 0`.

After the first net non-positive result in an episode:

```text
new Root alone       != enough
new sweep alone      != enough
new CHoCH/FVG alone  != enough
```

One retry becomes possible only after fresh same-direction **map delivery** occurs after the loss.

H1-led episode refresh:

```text
same H1 owner continuation BOS
OR
new same-direction M30 INITIAL_BOS / BOS
```

M30-led episode refresh:

```text
same M30 owner continuation BOS
```

A refresh that occurred before the loss cannot unlock the retry.

### 4.4 Second consecutive episode loss

If the one refreshed retry also ends net non-positive:

```text
same episode -> HARD LOCK
```

No further trade under that owner is allowed. The lock ends naturally only when the strategy itself creates a different H1/M30 owner, which is a different episode identity.

### 4.5 Positive result

A positive realized-net close resets `consecutive_losses = 0` for that episode.

Execution-divergent trades do not update EM state.

### 4.6 No time cooldown

EM does not use:

```text
N hours after loss
N days after loss
loss-streak ATR filter
owner-age threshold
quality score
```

Re-entry permission is event-causal.

## 5. SP / EM interaction

SP and EM intentionally interact only through final realized outcome.

Example:

```text
trade reaches +1R
-> SP realizes profit
-> later remainder exits
-> aggregate trade net > 0
-> EM sees WIN, not LOSS
```

Thus SP can remove giveback trades from loss streaks. EM then controls repeated exposure among the remaining genuine net losses.

## 6. Logging

D-149 adds low-volume compact rows:

```text
D149_RESEARCH_START / STOP
D149_SP_STATE_FROZEN
D149_SP_PARTIAL_ACCEPTED / REJECTED / INFEASIBLE
D149_SP_BE_MOVED / REJECTED / ALREADY_PROTECTED
D149_EM_STRUCTURE_REFRESH
D149_EM_AUTHORIZED
D149_EM_BLOCKED
D149_EM_RESULT / RESULT_SKIPPED
```

D-147 action rows are also now retained in `RESEARCH_COMPACT` so prior D-147 logging suppression does not recur.

## 7. D-148 audit compatibility

The existing D-148 EdgeAudit assumes unchanged ORIGINAL execution population. Therefore:

```text
InpEnableEdgeAudit=true
```

is allowed only when:

```text
InpExitManagementMode = V1_EXIT_ORIGINAL
InpEpisodeManagementMode = V1_EM_OFF
```

SP/EM performance runs should use `InpEnableEdgeAudit=false`.

## 8. Validation order

1. Apply package only to exact Git HEAD recorded in the package.
2. MetaEditor compile `MentorDeterministicV1EA.mq5` with `0 errors`.
3. Short GOLD baseline control: `ORIGINAL + EM_OFF`, Audit OFF.
4. Compare against a D-148 ORIGINAL baseline ledger with `tools/compare_d149_baseline.py`.
5. Require behavior parity after diagnostic rows/counters are normalized.
6. GOLD 2025 A/B/C/D under identical Strategy Tester settings.
7. Require zero execution divergence before profitability interpretation.
8. Run `tools/summarize_d149_sp_em.py` on each ledger.
9. Repeat A/B/C/D on GOLD 2023 and clean GOLD 2024.
10. Only after GOLD multi-year behavior is understood, expand to cross-market validation.

Recommended settings:

```text
Every tick based on real ticks
InpRegimeResearchMode = V1_REGIME_BASELINE_NO_GATE
InpStopLossModel = V1_SL_ROOT_OB_DISTAL_20
InpPositionSizingMode = V1_SIZE_FIXED_RISK_MONEY
InpFixedRiskMoneyPerTrade = 100
InpEventLogMode = V1_LOG_RESEARCH_COMPACT
InpEnableEdgeAudit = false
```

## 9. Evaluation

At minimum compare:

```text
realized net WR
average winner R
average loser R
cost-adjusted expectancy R/trade
total net R
max closed-trade drawdown R
longest realized loss streak
LONG / SHORT
winner concentration
SP STRONG vs DEFAULT state counts and realized results
SP partial / BE action integrity
EM blocked opportunity counts by reason
EM first-loss retries
EM hard locks
trade count / exposure reduction
execution divergence
```

The desired combined outcome is not simply fewer trades. The best result reduces correlated loss clusters and giveback while preserving enough large winners to keep average winner meaningfully above 1R and expectancy positive.

## 10. Frozen research parameters

For D-149 V1:

```text
SP STRONG partial = 25%
SP DEFAULT partial = 50%
SP strong room boundary = 1.0R to current M30 external
SP BE trigger = +2R
EM hard lock = second consecutive same-episode net loss
```

These are not optimizer inputs. Do not tune them after seeing GOLD 2025. Any changed fraction, room definition or loss-count policy is a separately registered variant.
