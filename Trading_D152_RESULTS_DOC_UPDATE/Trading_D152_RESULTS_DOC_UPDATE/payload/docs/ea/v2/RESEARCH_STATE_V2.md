# V2 Research State

Last updated: 2026-08-22  
Phase: `D-152 SP V3 COMPLETE -> ENTRY SURVIVAL NEXT`  
Current EA build: `2.02R0L2 / V2_SP_ARCHITECTURE_RESEARCH_V3`  
Authority: `docs/ea/v2/AGENTS_V2.md`  
2021: `KEEP UNTOUCHED`

## Active objective

Primary stretch target:

```text
cost-adjusted realized WR >= 70%
+
average winner > 1R
+
positive expectancy
+
robustness across markets and periods
```

Extreme research frontier:

```text
all accepted trades final aggregate net R >= +1R
```

The extreme frontier is not treated as a guaranteed property.

## Permanent V2 scope

Active order authority remains:

```text
EXTERNAL_CONTINUATION only
```

Reversal execution remains disabled.

## Axis A — Entry survival

Status: **PRIMARY BOTTLENECK / UNSOLVED**

Current D-152 populations:

```text
GOLD25 Fill -> +1R   = 30/53  = 56.6%
BTC25 Fill -> +1R    = 60/127 = 47.2%
```

This is too low for the 70% whole-strategy target even if post-+1R management becomes nearly perfect.

Next research must distinguish:

```text
true map/directional failure
local source failure while HTF survives
same-Root timing / SL sensitivity
correlated repeated Entry failure
```

No post-+1R variable may be backfilled into Entry authorization.

## Axis B — +1R runner discrimination

Status: **PROMISING / KEEP SEPARATE**

The strongest surviving relation remains M30 protected-to-external maturity / remaining room at first +1R.

D-152 did not invalidate the prior STRONG runner interpretation.

This remains a winner-continuation variable, not an Entry gate.

## Axis C — Profit preservation

Status: **PROVISIONAL SOLUTION FOUND**

D-152 compared five V3 architectures against SP V2.

Current leader:

```text
V3E BANK_2R_LOCK_ONE
```

Principle:

```text
protect profit with realized banking
while
preserving residual runner breathing room
```

Closed +2R outcomes:

```text
GOLD 11/12 >= +1R
BTC  31/31 >= +1R
```

Broker-feasible V3E banks:

```text
GOLD 8/8 >= +1R
BTC 27/27 >= +1R
```

V3E is the provisional SP reference, not baseline authority.

## Demoted D-152 paths

```text
V3A KNOWN_DEFAULT_CLOSE
  -> nominal +1R close can realize <+1R after costs

V3B PROFIT_BANK +0.05R
  -> economic floor too thin

V3C BANK_3R_LOCK
  -> too much GOLD tail haircut

V3D STRUCTURAL_BANK
  -> current-M30 +2R discriminator did not justify added complexity
```

Do not rescue these with same-sample threshold tuning.

## Broker-volume constraint

Do not full-close every V3E bank-infeasible runner.

Seven of eight observed infeasible cases still became >+1R runners; only one GOLD case missed +1R.

`KEEP_RUNNER` remains the better research fallback.

## EM

Status: **EXPERIMENTAL / SEPARATE**

Do not combine EM redesign with a new Entry rule until Entry-survival causality is measured independently.

## Current priority

```text
1. freeze D-152 result as development evidence
2. keep V3E as provisional SP reference
3. return primary research to Fill -> +1R
4. design shadow-only causal Entry/re-entry audit
5. use D-153 automated GOLD25/BTC25 matrix runs
6. validate any eventual solution outside the discovery sample before promotion
```
