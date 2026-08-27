# V5-034A — External Market Validation Contract

Status: `PRE-REGISTERED / VALIDATION DATA UNOPENED`
Date: `2026-08-27`
Candidate: `V5_FIRST_CROSS_240M_HALF_EMA_RUNNER`
Production authority: `NONE`

## 1. Validation purpose

Test whether the frozen V5-030A/V5-034A candidate survives markets that were not used to design First Cross, choose
240m, choose its management, or reject later filters.

## 2. Frozen external validation panel

Use every market from the previously outcome-blind V2/V4 validation vault:

```text
XAUJPY#   2023-2025
XAUCNH#   2023-2025
GAUCNH#   2023-2025
GAUUSD#   2023-2025
```

Do not replace a difficult market with another symbol after seeing results.

The panel was already frozen before V5-030A existed.

## 3. Environment

Preferred data:
- same broker/account/server family as development;
- M1 OHLC;
- tick volume optional for this candidate;
- recorded spread;
- exact symbol point.

Changing broker/feed is a separate execution environment and must be labeled as such.

## 4. Frozen replay

Run only:

```text
scripts/v5_034_first_cross_validation.py
```

using the exact candidate freeze.

No development recalibration.

## 5. Level-A validation gate

All must pass:

### A. Pooled economics

```text
WR >= 50%
avg positive net R > 1.0R
spread-adjusted EV > 0
```

### B. Market breadth

```text
EV > 0 in >=3 of 4 validation markets
```

All four markets must be reported.

### C. Temporal breadth

Pooled validation EV must be positive separately in:

```text
2023
2024
2025
```

### D. Concentration

Every leave-one-validation-market-out pooled EV must remain positive.

### E. Uncertainty

Weekly symbol-week block-bootstrap 95% interval for pooled EV must have:

```text
lower bound > 0
```

If A-D pass but E fails narrowly, classification is `INCONCLUSIVE`, not PASS and not permission to retune.

### F. Sample adequacy

No market with fewer than 40 resolved trades may be used to claim that market as a positive breadth pass.

A low-N market remains reported as `INSUFFICIENT`.

## 6. Failure handling

If validation fails:

```text
DO NOT
- remove the bad market;
- change 240m;
- add ATR/daily/session filters;
- move the +1R partial;
- retune EMA/slow exits;
- use GOLD# 2021 to rescue.
```

Record the failure and close V5-034A.

Only then may success-first discovery reopen with a genuinely new mechanism.

## 7. PASS handling

If external Level-A PASS:

1. freeze result document;
2. do not change the candidate;
3. open `GOLD# 2021` only through a new explicit final temporal-confirmation decision;
4. after temporal confirmation, implement an isolated MT5 research EA;
5. run Every Tick Based on Real Ticks with commission, spread and slippage/execution accounting;
6. verify Python/MT5 event parity.

External Level-A PASS is not production authority.

## 8. Current data availability

At the 2026-08-27 handoff, the four external validation raw M1 files were not found in the active session/File Library search.

Therefore the next session should **not** reopen development data while waiting.

Acquire/export these exact broker M1 files, verify hashes/coverage, then run the frozen replay.
