# V5 Development Handoff

Last updated: `2026-08-27`
Current phase: `V5-001A PREVIOUS-DAY PROXY INSUFFICIENT / V5-002 BALANCE-BOUNDARY PREREGISTERED`
Production authority: `NONE`

## Why V5 opened

V1-V3 repeatedly showed that a human-authored chart ontology can create strong discovery performance and then fail temporal/cross-market validation.

V4 responded by withholding the old ontology and asking a neural model to learn predictive representation from broad causal sequences. That research remains useful, but it still asks a hard generic question:

```text
What will the next return be?
```

The user then reframed the research target:

```text
Do not ask only why technical analysis fails.
Ask what technically oriented traders who survived and made money were actually doing differently.
```

A literature/practitioner pass found a recurring distinction:

```text
novice:
pattern / indicator = signal

experienced successful trader:
pattern = visible expression of market state;
context + interaction + invalidation + payoff architecture determine meaning
```

## Corpus v1

Initial high-value sources:

- Toby Crabel — observation -> pattern -> concept -> principle -> statistics -> strategy; contraction/expansion; breakout success/failure; wave character.
- Linda Bradford Raschke — principles of price behavior; context-dependent setup modeling; explicit distinction between mean-reversion environments and explosive momentum.
- Peter Brandt — classical chart patterns as balance/distribution possibilities; proper diagnosis; breakout completion; asymmetric payoff.
- Richard Dennis / William Eckhardt / Turtles — trend emergence, volatility-normalized sizing, complete system architecture, exit/risk importance.
- Ed Seykota — price/trend evidence over narrative; trailing stops/risk control.
- Tom Basso — entry can be weak/random while lifecycle, exits, diversification and sizing dominate system behavior.

Evidence quality is recorded in `V5_SUCCESS_FIRST_TRADER_CORPUS_V1.md`.

## Strongest cross-source convergence

The most promising common object is not an indicator.

It is:

```text
STATE-CONDITIONED BOUNDARY RESOLUTION
```

A market approaches a known boundary while in some state, interacts with it, then either:

```text
ACCEPTS beyond the boundary
-> directional expansion / continuation

REJECTS the new price area
-> failed breakout / return to prior range

REMAINS UNRESOLVED
-> two-sided balance / noise / censoring
```

Why this is attractive:
- Brandt's rectangles/H&S are completed by boundary resolution.
- Raschke explicitly studies price behavior at pre-defined levels and opening/range context.
- Crabel treats breakout success/failure as a foundational market problem.
- Turtles wait for price to demonstrate a breakout rather than predict it.
- Carol Osler's actual FX order data provides a microstructure explanation for reversal near support/resistance and acceleration after a break.
- order-flow research shows price impact depends on imbalance and market depth.

## Immediate task order

1. apply/push this V5 bootstrap;
2. do not open V4 validation data or GOLD 2021;
3. freeze V5-001 event-ledger schema before outcome analysis;
4. build shadow-only event ledger on already-open development data;
5. record full interaction/post-event path, not a hand-tuned win/loss label;
6. analyze whether context variables form stable transition families;
7. only then pre-register a candidate conditional state model;
8. reserve independent validation for the model, not for exploratory storytelling.

## V5-001 first data scope

Open development data already outcome-exposed in prior work may be used for discovery:

```text
GOLD#    2023-2025
BTCUSD#  2023-2025
XAUEUR#  2023-2025
USDJPY#  2023-2025
```

They are not pristine V5 validation.

Do not open:
- XAUJPY# / XAUCNH# / GAUCNH# / GAUUSD# 2023-2025 yet;
- GOLD# 2021.

GOLD# 2022 remains consumed V3 validation, not pristine.

## Hard stops

- no V5 trade rule from corpus anecdotes alone;
- no claim that tick volume == true order flow;
- no rebranding a V3 failed module as V5 success;
- no best-boundary / best-horizon selection followed by calling the same data validation;
- no AI/RL rescue before the semantic state question is defined;
- no EA modification in V5-001.


## V5-001A result — 2026-08-27
Read `V5_001A_PREVIOUS_DAY_BOUNDARY_RESULTS.md`.

The unmatched previous-day extreme result was selection-confounded. After causal pre-state matching, PDH/PDL did not
show stable directional resolution versus internal Q75/Q25 controls.

Classification: `OBSERVABLE PROXY INSUFFICIENT`.

Do not rescue previous-day high/low with filters. V5-002 returns to the trader corpus and tests whether the continuous
character of a *formed range itself* conditions its later breakout.
