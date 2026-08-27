# V5-036A — Exact M30 Portability Implementation Freeze

Status: `FROZEN BEFORE FIRST-CROSS TRANSFER OUTCOME JOIN`
Date: `2026-08-27`
Parent: `V5_036A_CROSS_ARCH_CONTINUATION_PORTABILITY_CONTRACT.md`
Strategy authority: `NONE`
Production authority: `NONE`

## Stage-0 conclusion

`one_r_m30_range_progress` is portable in principle.

The D-146 measurement reads the global `V1StructureState` M30 trend/protected/external state plus trade direction and
current price. It does not read Root ID, FVG ID, scenario ID, or scenario-owned structure identity.

The V1 M30 structure owner is created by global `INITIAL_BOS` and persists through continuation BOS until protected
structure breaks. Root/FVG/scenario logic consumes this market-structure state; it does not define the protected/external
identity used by the metric.

Therefore V5 may test the same market-state concept on First Cross, but only by reproducing the exact causal V1 M30 state
machine. A generic swing/pivot approximation is prohibited.

## Exact M30 state replay

Input:
- exact existing V5 development M1 data;
- broker-server timestamps;
- point values already frozen for the development replay.

Construct M30 bars from `[bar_open, bar_open+30m)` and make each bar causally available at `bar_open+30m`.

For each closed M30 bar use V1 processing order:

```text
1. EnsureLegStart
2. EvaluateExistingStructureBreaks using PRE-BAR protected/external objects
3. UpdateDirectionalRanges
4. ConfirmWaveIfAny
```

Root/liquidity/scenario side effects are omitted because they do not mutate the M30 protected/external structure state
used by D-146.

### Wave confirmation

Exactly V1:

```text
3 consecutive bearish closed candles -> confirm HIGH wave
3 consecutive bullish closed candles -> confirm LOW wave
doji in the 3-bar sequence -> no confirmation
same-side consecutive confirmed wave -> reject
```

The confirmed wave price is the extreme over the causal leg from the bar after the prior wave occurrence through the
confirmation bar, with the earliest equal extreme retained.

### Structure lifecycle

Exactly V1:

- NEUTRAL/TRANSITION requires both neutral HIGH and LOW waves before `INITIAL_BOS`.
- close above neutral high -> BULLISH INITIAL_BOS.
- close below neutral low -> BEARISH INITIAL_BOS.
- BULLISH protected-low close break -> TRANSITION and clear structural range.
- BEARISH protected-high close break -> TRANSITION and clear structural range.
- BULLISH external-high close break -> continuation BOS; causal correction low, if present, promotes to protected low.
- BEARISH external-low close break -> continuation BOS; causal correction high, if present, promotes to protected high.
- processing a protected/external break precedes same-bar wave confirmation.

## First-Cross +1R observation clock

Population is the already frozen V5-035 clear +1R population, `N=223`.

At the exact First Cross +1R activation timestamp:

- process every M30 bar with availability `<= activation_ts`;
- do not process a still-open M30 bar;
- observation price = exact `Entry + direction * initial_risk` (+1R barrier);
- do not use the activation M1 bar's later high/low as the state price.

A valid state requires:

LONG:
```text
M30 trend = BULLISH
protected_low valid
external_high valid
external_high > protected_low
```

SHORT mirrors.

No missing state is imputed.

Metric:

LONG:
```text
progress = (+1R price - protected_low) / (external_high - protected_low)
```

SHORT:
```text
progress = (protected_high - +1R price) / (protected_high - external_low)
```

Do not clamp progress to `[0,1]`. Values above 1 are allowed, matching D-145's maturity interpretation.

## Available-history initialization QA

Canonical replay starts at the first available M30 bar in each frozen V5 development raw file.

Before joining continuation outcomes, state-only sensitivity replays were started 7, 14, 30, and 60 days later.

Canonical valid state:

```text
122 / 223 = 54.7%
```

By market:

```text
BTCUSD#  38 / 75
GOLD#    35 / 57
USDJPY#  25 / 47
XAUEUR#  24 / 44
```

For every observation where both canonical and delayed-start replay produced a valid state, trend/protected/external
matched exactly for all four delayed starts. Therefore no additional warm-up exclusion is introduced.

## Frozen transfer prediction

Inherited unchanged from D-145:

```text
median progress(+2R runner) < median progress(exhaust before +2R)
```

Outcome is the already frozen V5-035 conservative post-1R outcome:
- `runner`: continuation MFE reaches >=2R before current BE/adverse exit;
- `exhaust`: it does not.

## Breadth reporting / interpretation

Report:
- pooled;
- each market;
- each year;
- LONG and SHORT.

A subgroup is `COMPARABLE` only when it contains at least 5 valid runners and 5 valid exhaust observations.

`STRONG TRANSFER` requires the inherited sign in:
- pooled result;
- every comparable market;
- every comparable year;
- both comparable directions.

Any sign reversal in a comparable direction is especially material because V5-035C already exposed direction
instability.

No threshold, score, conjunction, market veto, direction veto, or management rule may be created from this test.
