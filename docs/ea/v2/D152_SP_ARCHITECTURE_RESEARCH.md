# D-152 V2 Smart Partial V3 Architecture Research

Date: 2026-08-22  
Status: **CONTROLLED RESEARCH VARIANTS / NOT V2 BASELINE AUTHORITY**  
Target build: `2.02R0L2 / V2_SP_ARCHITECTURE_RESEARCH_V3`  
Parent: D-151 GOLD/BTC SP-only causal ledgers  
V1: **FROZEN**  
2021: **KEEP UNTOUCHED**

## 1. Why SP changes now

D-151 clean SP-only ledgers show that SP is already good at converting a trade that reaches +1R into a positive aggregate result, but cannot solve the project-wide 70% win-rate target by itself.

```text
GOLD25: 53 fills, 30 reached +1R = 56.6%
BTC25 : 127 fills, 59 reached +1R = 46.5%
```

Among closed +1R cohorts:

```text
GOLD: 28/30 positive = 93.3%; only 43.3% finished >= +1R
BTC : 55/58 positive = 94.8%; only 36.2% finished >= +1R
```

Therefore post-+1R SP can improve payoff, retained R and conditional outcome quality, but overall WR cannot reach 70% until the independent Fill->+1R survival problem is improved.

## 2. D-151 result entering D-152

### GOLD 2025 SP-only

```text
53 closed
WR 52.83%
avg winner +1.373R
expectancy +0.228R
Total +12.063R
+1R 30/53 = 56.6%
STRONG -> +2R 9/11 = 81.8%
DEFAULT -> +2R 3/19 = 15.8%
```

### BTCUSD 2025 SP-only

```text
127 fills / 126 closed / 1 right-censored actual fill
WR on closed = 44.44%
avg winner +1.103R
expectancy -0.066R
Total -8.337R
+1R 59/127 = 46.5%
STRONG -> +2R 15/18 = 83.3%
DEFAULT -> +2R 17/41 = 41.5%
```

The STRONG +2R relation remains strikingly stable across these two markets (~82-83%). The main unresolved SP problem is what to do after a trade has already proved +2R.

## 3. Why a tighter +2R stop is rejected as the main next architecture

D-151 shadow paths allow a direct counterfactual question: how many eventual +5R trades would have survived a fixed profit floor immediately after +2R?

```text
GOLD eventual +5R = 6
+2R -> +1R floor would preserve only 2/6

BTC eventual +5R = 15
+2R -> +1R floor would preserve only 7/15
```

Even a 0R/Fill floor would have stopped 2/15 BTC trades that later reached +5R. Four BTC trades that later reached their original structural TP actually closed below +1R under the current +2R cost-BE implementation because the real position was stopped before the shadow recovery.

Conclusion:

> Profit protection and runner breathing room should not be treated as the same control variable.

D-152 therefore tests realized-profit banking as an alternative to moving the entire residual stop upward.

## 4. Profit-bank principle

After a +1R partial, the residual runner still owns the original structural SL and TP. At later milestones the EA may close the **minimum broker-valid extra volume** such that, even if all remaining volume later exits at the original normalized SL, modeled aggregate cash is at least a specified floor.

This is not a fitted TP fraction. The close amount is solved from current volume, actual Fill, original SL, known realized cash and broker volume steps.

No bank variant moves the residual SL merely because an integer R milestone was reached.

## 5. Controlled modes

Existing control remains:

```text
V1_EXIT_SMART_PARTIAL_V2
+2R -> dynamic cost-adjusted BE
```

### V3A — KNOWN_DEFAULT_CLOSE

```text
V1_EXIT_SMART_PARTIAL_V3_KNOWN_DEFAULT_CLOSE
```

Only one difference from SP V2:

At +1R, if the M30 protected/external range is causally available and the trade is DEFAULT, then the current M30 external lies before the original +2R price. Close the position fully at +1R instead of protected-partial management.

Range-unavailable DEFAULT stays on SP V2 behavior. STRONG is unchanged. +2R cost-BE remains unchanged.

This uses the already-frozen structural boundary, not a new fitted threshold.

D-151 path counterfactual (not strategy evidence) suggested replacing known-range DEFAULT outcomes by their +1R execution would change total R approximately:

```text
GOLD +0.94R
BTC  +2.71R
```

The effect is direction-concentrated in this sample, so this is research-only and must not be promoted from GOLD/BTC25.

### V3B — PROFIT_BANK

```text
V1_EXIT_SMART_PARTIAL_V3_PROFIT_BANK
```

+1R behavior remains SP V2.

At +2R:

```text
remove automatic cost-BE ratchet
bank the minimum additional volume needed so modeled aggregate outcome
at original SL >= +0.05R
leave residual SL at original normalized SL
leave structural TP unchanged
```

Goal: make +2R->loss economically difficult while permitting retracement below Fill when the larger trend remains intact.

### V3C — BANK_3R_LOCK

```text
V1_EXIT_SMART_PARTIAL_V3_BANK_3R_LOCK
```

Same as V3B, plus:

```text
if +3R is later reached,
bank the minimum extra volume needed so modeled original-SL fallback >= +1.05R
```

This tests a two-stage proof concept:

```text
+2R proves enough to remove negative aggregate fallback
+3R proves enough to bank a full meaningful winner
```

The residual runner still keeps original SL/structural TP.

### V3D — STRUCTURAL_BANK

```text
V1_EXIT_SMART_PARTIAL_V3_STRUCTURAL_BANK
```

At first +2R, re-read the causally-current M30 protected/external range.

```text
M30 range valid and current external >= original +3R
    -> bank only +0.05R fallback; preserve runner

M30 range valid but external lies before +3R
    -> bank +1.05R fallback

M30 range unavailable
    -> do not assume exhaustion; bank only +0.05R fallback
```

This is the dynamic structural hypothesis. The `1R` room boundary means exactly whether another full R to +3 is still inside the current M30 protected->external delivery; it is not a fitted percentile.

### V3E — BANK_2R_LOCK_ONE

```text
V1_EXIT_SMART_PARTIAL_V3_BANK_2R_LOCK_ONE
```

+1R behavior remains SP V2. At first +2R, bank the minimum additional volume needed so modeled aggregate fallback at the original normalized SL is at least `+1.05R`; the residual runner still keeps the original SL and structural TP.

This is deliberately aggressive and exists as a controlled frontier test for the new `final R >= +1R` objective. Unlike a `+2R -> +1R` stop, it cannot stop the runner solely because price retraces; the cost is smaller remaining runner size.

## 6. What remains unchanged

All D-152 modes preserve:

```text
continuation-only authority
Entry chain
original normalized SL geometry at Entry
frozen structural TP
fixed-risk sizing control
no reversal
no look-ahead
D151 causal audit
EM independently switchable; use EM_OFF for first SP comparison
```

No D-152 mode is baseline authority.

## 7. Test matrix

Use identical GOLD25 and BTC25 settings, `EM_OFF`, D151 audit ON.

Existing D151 SP V2 ledgers are the parent control. First new tests:

```text
A = V3A KNOWN_DEFAULT_CLOSE
B = V3B PROFIT_BANK
C = V3C BANK_3R_LOCK
D = V3D STRUCTURAL_BANK
E = V3E BANK_2R_LOCK_ONE
```

Do not combine A with B/C/D until isolated effects are known.

Primary evaluation:

```text
aggregate WR
% final R >= +1R
avg winner
expectancy
total R
DD / loss streak
+1R cohort positive conversion
+1R cohort final >= +1R
+2R cohort retained R
structural-TP shadow winners killed/saved relative to SP V2
large-winner concentration
```

After GOLD/BTC, validate promising relations on GOLD23/24 and then SILVER/CADJPY before promotion.
