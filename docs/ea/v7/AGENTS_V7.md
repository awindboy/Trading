# V7 Research Instructions

Status: `ACTIVE`
Generation: `V7`
Research family: `Double-B / 더캔이지추격깨 / KTR`
Production authority: `NONE`

## 1. Purpose

V7 is a deliberate reset from the prior mentor-style deterministic H/L1/L2 research.

The goal is not to translate discretionary chart reading into arbitrary indicator scores.
The goal is to test whether rare Double-B events can be **contextually classified in real time**
into useful trade archetypes and whether KTR can provide a rational event-specific risk/target map.

## 2. Source authority

For V7 method semantics, use the following authority order:

1. the user's direct description of the Kim Jikseon method in this project;
2. V7 documents in this directory;
3. original/public Kim Jikseon teaching material when explicitly inspected;
4. implementation proxies only when clearly labeled as proxies.

Do not claim an implementation is the exact original method unless the exact source rule is known.

## 3. Core separation

Never collapse these roles:

```text
Double-B      = event detection
Context       = direction / archetype / timing
KTR           = normalized distance / session force
Risk architecture = sizing / staged entry / campaign exposure
```

A variable useful in one role does not automatically gain authority in another role.

## 4. Double-B semantics

Main chart is H1 unless a future preregistered experiment changes it.

Current Double-B definition:

- Bollinger A: period 20, standard deviation 2, applied to CLOSE.
- Bollinger B: period 4, standard deviation 4, applied to OPEN.
- A Double-B event occurs when one H1 candle reaches/pierces both upper bands
  or reaches/pierces both lower bands.
- Candle close must be known before a discretionary trade decision.
- Double-B is rare-event information only. It does not itself define LONG/SHORT.

## 5. Context table

The remembered 더캔이지추격깨 components are:

```text
더블비
캔들
이평선
지지저항
추세선
이격도(볼밴)
깼는지(세션 첫 캔들 고/저)
```

Do not force all components into equations.

For every event each component may be recorded as:

```text
SUPPORTS_LONG
SUPPORTS_SHORT
NEUTRAL
UNKNOWN / NOT RELIABLY ASSESSED
```

Natural-language reasoning is allowed and preferred over a fake quantitative proxy
when the evidence cannot be represented faithfully.

## 6. Archetypes

V7 currently uses four first-class outcomes:

### BASIC
Range/rotation extreme. The event is faded toward equilibrium.

### BREAKOUT
Fresh expansion. The event is continuation/acceptance into a new directional move.

### TURNING
Terminal expansion. The rare event is the late/climactic part of a mature move.

### WAIT / SKIP
The event is real but the close does not contain enough asymmetry to justify a trade.
`WAIT_CONFIRM` is a valid decision, not a failure to classify.

## 7. KTR semantics

KTR is the True Range of the first H1 candle of each major session:
- Asia,
- Europe,
- US.

Exact broker-server timestamp mapping is execution-environment specific and must be documented
before any automated replay.

KTR is interpreted as the session's current distance/force scale.

Do not use a universal fixed formula such as:
`LOW KTR -> always 3.5KTR SL`
or
`HIGH KTR -> always 1KTR SL`.

Instead ask:

```text
Where is structural invalidation?
How many current KTR is that?
How much realistic room remains to target?
Is the setup momentum, mean reversion, or turning?
```

## 8. Staged entry

Current discovery convention, requested by the user:

- optional additional entries may be spaced at 0.5 KTR;
- every filled leg is sized so that its own loss at the common SL is exactly 1 risk unit;
- therefore N filled legs can lose N R at the common SL.

This is intentionally aggressive and is **not production risk authority**.

Track both:
1. `campaign_R_sum` = sum of leg R outcomes;
2. `campaign_risk_normalized_return` = campaign P/L divided by total stop-risk of filled legs.

Never hide the growth in campaign exposure created by additional legs.

## 9. Discovery vs validation

Outcome-informed reverse engineering is allowed only when explicitly labeled `DISCOVERY / HINDSIGHT`.

The 24 events in `V7_002` are consumed discovery data.

They may teach vocabulary and hypotheses, but:
- cannot validate those hypotheses;
- cannot be reused to estimate V7 expectancy;
- cannot justify tuned KTR thresholds.

A proper validation event must be future-hidden at decision time.

## 10. V6 boundary

V6 H/L1/L2 is closed as a strategy-development branch.

Do not:
- rescue L1;
- re-optimize H;
- tune L2 age;
- add V7 Double-B filters to V6 retrospectively.

Historical V6 code/results remain available for reproducibility only.

## 11. Final strategy goals remain unchanged

A future promoted system must ultimately show:
- realized WR >= 50%;
- average positive payoff meaningfully above 1R, with final project objective >= 2R;
- clearly positive spread/commission/slippage-adjusted expectancy;
- robustness across independent markets and periods;
- acceptable drawdown and loss-streak behavior;
- no hidden hindsight dependence.

V7 currently satisfies none of these claim-grade requirements.
