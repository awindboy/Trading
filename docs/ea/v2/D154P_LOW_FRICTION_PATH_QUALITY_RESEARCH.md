# D-154P — Low-Friction Pre-Fill Path-Quality Discovery

Status: `ACTIVE RESEARCH CONTRACT / NO STRATEGY AUTHORITY`  
Date: `2026-08-24`  
Parent result: `D154O Stage B = Outcome B`

## Why this phase

D154O separated two facts:

```text
1. execution friction relative to local strategy scale matters;
2. low execution friction alone does not reproduce GOLD-like Entry survival.
```

The next question is therefore not another spread threshold and not a return to
forcing SILVER/CADJPY-like markets to work.

The next question is:

> Within an already low-friction execution environment, what **pre-Fill causal path / regime property**
> distinguishes Fill->+1R survivors from SL-first failures?

## Stage separation

This phase is Entry-survival research only.

```text
Fill -> +1R       = in scope
+1R -> +2R        = not an Entry variable
post +2R          = exit research
D154M quote flips = execution mechanism, already measured
portfolio         = out of scope
```

Do not reuse M30 +1R winner-continuation maturity as an Entry gate.

## Discovery population

Primary 2025 discovery population is restricted to **execution-clean, sufficiently sampled,
low-friction markets** from the frozen D154O cohort:

```text
GOLD#      55 fills
BTCUSD#   127 fills
XAUEUR#    58 fills
USDJPY#    94 fills
```

These provide four useful market contexts with 334 resolved Fill->barrier outcomes.

Descriptive-only small samples:

```text
XAUJPY#    14
XAUCNH#    12
GAUCNH#    14
GAUUSD#    10
```

Controls may be reported for context but must not define the low-friction discovery relation:

```text
SILVER#
EURUSD#
ETHUSD#
```

`GBPUSD#` is excluded from causal outcome analysis because its Stage-B run contained
a pending-cancel execution divergence. It remains a frozen control record and must not
be replaced after outcome visibility.

2021 remains untouched.

## First step — use existing ledgers before adding instrumentation

Do not modify the strategy EA first.

Use the existing D151 + D154K + D154M Stage-B ledgers to exhaust pre-Fill information already recorded.

Candidate variable families may include:

### A. causal timing

```text
PLAN -> Root contact
Root contact -> sweep
sweep -> CHoCH
FVG known -> Fill
```

Wall-clock seconds crossing market-closed intervals must not be treated as equivalent
to active-market bar counts. If timing appears promising, add shadow-only active-bar
instrumentation before validation rather than fitting a seconds threshold.

### B. planned geometry

Use geometry frozen before Fill where possible:

```text
planned Entry
original normalized SL
Root width
selected FVG width
planned risk
Root width / planned risk
FVG width / planned risk
```

Do not use actual post-Fill outcome to redefine the geometry.

### C. causal M1 path quality

Existing D154K reaction descriptors:

```text
reaction efficiency
reaction path / TR
reaction net / TR
reaction total range / TR
favorable / TR
adverse / TR
risk / reaction TR
FVG / reaction TR
Root / reaction TR
```

Spread-normalized metrics remain execution-suitability evidence and are not to be
re-fitted as per-trade Entry thresholds.

### D. categorical structural context

Existing map/source/timeframe states may be described, but previously rejected static
H1/M30 alignment or D154J exhaustion logic must not be silently resurrected.
A genuinely new causal hypothesis requires a new rationale.

## Discovery method

For every candidate variable:

1. compare `PLUS_1R` vs `SL_FIRST`;
2. preserve market identity;
3. preserve LONG/SHORT;
4. report coverage;
5. report robust medians/quantiles;
6. report a threshold-free effect size such as Cliff's delta;
7. reject a relation that is dominated by one market/direction;
8. do not optimize a cutoff on 2025;
9. do not combine variables into an ad-hoc score.

2025 is **discovery only** for any new D154P hypothesis.

## Reconnaissance note

A preliminary non-authoritative scan of the Stage-B ledger was used only to plan D154P.

No single existing pre-Fill variable was strong enough to authorize a rule.

Some weak discovery signals exist, including planned Root-to-risk geometry and several
timing/path descriptors, but they are not strategy evidence and must not be promoted
from this same 2025 sample.

This reconnaissance is explicitly not validation.

## Hypothesis freeze

After the systematic discovery table is produced:

- retain only a small number of causally interpretable relationships;
- write the exact variable definition;
- state expected direction;
- state population/coverage;
- freeze the hypothesis before a disjoint-year test;
- do not choose a threshold from 2025.

If no relationship survives market/direction consistency checks, close D154P rather than
manufacturing a multivariate score.

## Validation

Validation must use a disjoint period, preferably 2024 where complete real-tick history exists,
with the same low-friction markets and unchanged strategy semantics.

```text
XM Ultra Low
Every tick based on real ticks
same deterministic Entry architecture
D151 shadow audit
only the minimal D154P instrumentation needed
```

If an existing ledger field is sufficient, do not add new tick-level logging.

2021 stays untouched.

A relation that reverses materially in validation is rejected; do not retune its threshold
to preserve the hypothesis.

## Promotion gate

Even a validated D154P relationship does not automatically become an Entry filter.

Any future strategy variant still requires:

```text
realized WR >= 50%
average winner meaningfully > 1R
positive cost-adjusted expectancy
acceptable drawdown / loss streak
multi-market + temporal robustness
no unresolved execution divergence
```

No strategy change is authorized by this contract.
