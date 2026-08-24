# V3-002 — GOLD Offline Research Synthesis / Fundamental Falsification

Status: `DISCOVERY SYNTHESIS / NO STRATEGY AUTHORITY`
Date: `2026-08-25`
Market: `GOLD#`
Environment: `XM Ultra Low / XMGlobal-MT5 7`
Discovery data: `2023-2025 M1`
Validation vault: `2022 — DO NOT OPEN`
Untouched: `2021`

## 1. Why this document exists

V3 began because V2 research had become constrained by a sparse deterministic fill
population and by operational formalizations that might not match the actual source
method or the market mechanism.

V3 therefore changed the research unit from:

```text
current EA fills
```

to:

```text
raw GOLD market data
-> broad causal event universe
-> offline replay
-> repeated falsification
```

This document freezes the main experiments, negative results, corrections and current
interpretation produced from the first GOLD-only offline research cycle.

It intentionally records **failed and superseded hypotheses** so that later sessions do
not rediscover them and begin another threshold-mining loop.

No result in this document has production strategy authority.

## 2. Raw data foundation

Accepted GOLD# M1 discovery data:

```text
2023 rows 353,036
2024 rows 353,837
2025 rows 351,929
TOTAL     1,058,802
```

Data quality passed:
- monotonic timestamps;
- no duplicate timestamps;
- valid OHLC;
- nonnegative spread;
- positive tick volume;
- real volume unavailable (`VOL=0`).

Important execution-scale observation:

```text
median nominal spread
2023 ~0.13
2024 ~0.18
2025 ~0.17

median M1 range
2023 ~0.38
2024 ~0.55
2025 ~1.02
```

Therefore the improvement in relative execution conditions into 2025 was driven
substantially by **larger market movement relative to spread**, not only by a narrower
nominal spread.

## 3. V2 opportunity compression was real

The raw data contains far more physical reaction events than the V2 annual fill count.

Early causal swing/sweep censuses produced hundreds to more than one thousand physical
sweep candidates per year depending on source scale.

This supports the original V3 motivation:

> V2's ~50-55 GOLD fills/year did not imply that GOLD itself offered only ~50 meaningful
> market events/year. The deterministic architecture compressed a much larger opportunity
> universe.

The research problem is therefore not merely "find another filter for V2 fills."

## 4. Early sanity family — useful but not authority

The first deliberately simple offline family used approximately:

```text
H1 liquidity
-> same-bar sweep/recovery
-> M5 local structure transition
-> same causal-leg M1 FVG
-> FVG retest
-> sweep-extreme invalidation
```

A representative early configuration produced:

```text
2023 70 trades, +1R survival 48.6%
2024 73 trades, +1R survival 53.4%
2025 61 trades, +1R survival 57.4%
```

This proved that a much simpler raw-data architecture could generate a useful research
population without repeatedly running MT5.

It did **not** establish a strategy.

Later stricter replay invalidated several optimistic versions of this family.

## 5. Important research correction — strict replay

As the replay engine became stricter, V3 stopped giving favorable interpretations to M1
bars with unknown intrabar order.

The stricter research rules included:
- sweep-extreme invalidation before trigger;
- causally known trigger swing only;
- FVG freshness checks;
- spread-aware entry/barrier handling;
- ambiguous Entry/SL/+1R ordering classified conservatively;
- physical-event deduplication.

Several earlier 100+ trade/year results weakened materially under these rules.

Decision:

> Earlier optimistic Level-A counts remain historical research notes only. Later strict
> replay has priority.

## 6. Liquidity lifecycle finding

One useful architecture finding survived repeated re-analysis:

```text
a newly confirmed swing does not automatically erase older unswept liquidity
```

V3 therefore distinguishes:

```text
structure lifecycle
!=
liquidity lifecycle
```

Older causally confirmed levels can remain ACTIVE until actually consumed or otherwise
invalidated by the relevant liquidity-state contract.

This increased the raw opportunity census without relying on outcome-conditioned filters.

## 7. Scale finding — intermediate liquidity matters

Experiments across M5/M15/M30/H1 source scales repeatedly showed:

```text
M5 liquidity
    high frequency, too noisy

M15 / M30
    strongest recurring region

H1
    sparse / slower and not uniformly superior
```

A particularly useful abstraction emerged:

> The signal may not be "M15" or "M30" literally. The useful object appears closer to an
> **intermediate-prominence physical swing**, often visible on both M15 and M30.

Prominent M15 swings frequently collapsed onto the same physical price as M30-visible
swings.

Do not interpret this as a frozen timeframe rule yet.

## 8. Same-bar sweep/recovery survived; delayed recovery weakened

Across multiple families, widening the sweep definition from:

```text
penetration + same M1 close recovery
```

to two, three or five bars of delayed recovery increased frequency but generally reduced
quality.

The interpretation that survived is not "one minute is magical."

It is:

> The penetration and rejection should look like one atomic price event rather than a
> prolonged fight around the level.

This remains a useful event-definition candidate.

## 9. FVG findings changed materially during falsification

### 9.1 Early result

Early replay often favored the WIDEST causal-leg FVG over first/last alternatives.

This suggested that the V2 `WIDEST` selector could contain real information even if the
surrounding V2 structure chain was too restrictive.

### 9.2 Later fundamental result

When entry timing was compared directly:

```text
M30-visible reaction family
trigger-close entry
vs
wait for FVG midpoint retest
```

representative results were:

```text
             trigger-close     midpoint retest
2023            53.3%              52.4%
2024            56.1%              46.3%
2025            55.3%              36.4%
```

Therefore the later and stronger interpretation is:

```text
FVG as causal displacement footprint       = still plausible
mandatory FVG retracement entry authority = not supported
```

Current V3 must **not** assume that waiting for the FVG is better simply because the mentor
method used it as a discretionary execution concept.

## 10. Sweep alone has almost no alpha

A fundamental naive-control test compared the same broad M15 liquidity sweep/recovery
event against time/risk-matched controls.

Representative +1R results:

```text
sweep reaction
2023 ~44.5%
2024 ~44.6%
2025 ~43.6%

matched random trend-aligned control
2023 ~44.9%
2024 ~44.4%
2025 ~43.2%
```

Conclusion:

> A liquidity sweep by itself is not an Entry edge.

Do not spend future research cycles optimizing the sweep wick geometry as if sweep alone
were predictive.

## 11. Local structure transition matters more than sweep alone

Adding a meaningful M5 local-structure transition after the sweep raised the population
toward the ~50% region.

Representative sweep-context M5 trigger-close results:

```text
2023 ~50.5%
2024 ~51.5%
2025 ~50.0%
```

Generic M5 BOS controls were approximately:

```text
2023 ~46.8%
2024 ~47.9%
2025 ~50.6%
```

Interpretation:

> Local structural acceptance appears more important than the sweep alone, while the
> incremental value of the sweep context is time-varying.

## 12. Mirror-direction test changed the problem definition

A decisive falsification was to replay the exact same event/risk in the opposite direction.

Without higher-level direction context:

```text
sweep + local structure event
strategy/reaction direction
2023 ~46.8%
2024 ~46.8%
2025 ~46.1%

exact mirror
2023 ~48.5%
2024 ~48.0%
2025 ~50.2%
```

Therefore:

> `sweep + local structure transition` is not a self-contained directional edge.

The project should not keep trying to perfect Entry geometry while leaving direction/state
classification unresolved.

## 13. Fixed momentum-horizon direction was unstable

Direction definitions based on a single trailing horizon such as:

```text
3h / 6h / 12h / 24h momentum
```

were unstable across years.

Leave-one-year-out horizon selection failed to generalize cleanly.

Therefore do not search for a magical fixed direction horizon.

## 14. Winner/loser ML filter mining hit a ceiling

Pre-entry features included:
- multi-horizon momentum;
- directional efficiency;
- volatility ratios;
- spread/risk;
- risk/local volatility;
- sweep candle rejection;
- trigger displacement;
- sweep-to-trigger delay;
- liquidity age;
- FVG attributes;
- time of day;
- direction.

Leave-one-year-out models were approximately coin-flip:

```text
Logistic AUC
2023 ~0.46-0.51
2024 ~0.47-0.56
2025 ~0.47-0.53

Random Forest / Gradient Boosting
similarly unstable
```

Decision:

> The current Entry family does not justify continued feature mining for a universal
> winner/loser classifier.

ML remains allowed for **market-state discovery**, but not as an excuse to keep fitting
trade-level labels.

## 15. Selective continuation looked better than forced continuation/reversal

When broad M30/H1 structural consensus agreed with the reaction direction, a selective
continuation population produced representative discovery results near:

```text
2023 38 trades, +1R 55.3%
2024 46 trades, +1R 56.5%
2025 43 trades, +1R 62.8%
```

Surrounding structure-definition variants often retained the same broad direction.

However when HTF context opposed the reaction and the trade was simply flipped into an
HTF-direction reversal/continuation trade, representative results were only:

```text
2023 ~44.9%
2024 ~46.2%
2025 ~53.7%
```

Current interpretation:

```text
HTF context agrees with reaction
    -> selective continuation candidate

HTF context conflicts with reaction
    -> NO TRADE is more defensible than forced reversal
```

This is still discovery evidence, not strategy authority.

## 16. Naive controls show the ICT-inspired context is not pure decoration

A very broad generic trend-following control:

```text
HTF consensus
-> generic M5 BOS
-> recent FVG
```

generated thousands of trades/year but roughly:

```text
2023 44.8%
2024 46.8%
2025 52.9%
```

Matched structural-state controls also generally trailed the selective liquidity-reaction
event in 2023/2024.

However in 2025 generic trend/BOS conditions became much stronger and the incremental value
of the liquidity event largely disappeared.

Interpretation:

> The current event is not merely a complicated name for generic trend following, but its
> incremental value is non-stationary.

## 17. Quarter instability remains the decisive unresolved problem

A representative selective-continuation family showed strong annual aggregates but weak
cells such as:

```text
2023 Q3 ~27-30% +1R
2024 Q2 ~37%
2025 early-year cells materially weaker than 2025 Q4
```

In some bad cells the exact mirror direction did materially better.

This is stronger evidence than a normal losing streak:

> The same pattern can represent a different auction state in different periods.

Therefore annual pooled performance is insufficient for V3 promotion.

## 18. Failure mechanisms differ across weak periods

Shadow post-SL recovery analysis suggested that weak periods do not all fail for the same
reason.

Examples:
- 2023 Q3 / 2024 Q2 contained many cases where the directional premise failed before the
  original +1R path recovered.
- 2025 Q2 contained more stop-sensitive cases that later recovered while the broader premise
  was still alive.

This explains why one simple regime threshold or one universal SL-widening rule failed.

## 19. Broad SL widening is rejected

Some stop-sensitive losers required approximately:

```text
+1R or more additional adverse travel beyond the original SL
```

and some much more.

Therefore a small ATR/percentage widening would rescue only a subset, while a large widening
would destroy payoff geometry.

Current research interpretation:

```text
sweep-extreme / structural invalidation
```

remains more defensible than broad outcome-driven SL widening.

## 20. Winner continuation remains real enough to study separately

Across multiple V3 populations, once +1R was reached, a substantial portion continued to
+2R and beyond.

Representative selective-continuation results included:

```text
P(+2R | +1R) ~ two-thirds to ~70%
meaningful +3R/+5R tails remained
```

Simple SP thought experiments repeatedly showed that:

```text
small positive floor near +1R
+
material residual runner
```

can produce average winners above 1R in discovery data.

But exit research must remain separate from the unresolved Entry/state problem.

## 21. Superseded micro-optimization findings

The following observations appeared useful in one or more early families but are **not**
current authority because later architecture changes weakened or contradicted them:

```text
exact FVG midpoint as mandatory Entry
exact M5 prominence k value
exact M15 prominence k value
fixed 30/60/120-minute trigger or retest deadline
single fixed momentum horizon
specific H1-opposite strong-runner rule
single session or quarter veto
broad Root/FVG-style distance thresholds
```

Do not restart these searches without a new causal reason.

## 22. Fundamental research lesson

The first GOLD V3 cycle changed the core question from:

```text
Which sweep / CHOCH / FVG / SL combination is best?
```

to:

```text
What auction state is GOLD in,
and which strategy module belongs to that state?
```

This is the active conceptual pivot.
