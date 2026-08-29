# V7-001 Kim Jikseon Method Specification

Status: `METHOD MEMORY / RESEARCH FORMALIZATION`
Exact-original-method claim: `NO`

## 1. Provenance

This document formalizes the trading method as described directly by the user,
who studied Kim Jikseon's material before the later mentor-style trading research.

The user associates the method with:
- Kim Jikseon,
- Korean Traders Association / 한국트레이더협회 Naver Cafe,
- Double-B / 더블비,
- 더캔이지추격깨,
- KTR.

Some parts are discretionary and are not fully expressible as exact formulas.
V7 must preserve that uncertainty rather than inventing precise rules.

## 2. Main chart

The main operating chart is H1.

The trader waits for candle close before making the decision.

This causal boundary is important:
no H1-close decision may use later candles.

## 3. Double-B

Two Bollinger Bands are shown simultaneously.

### Standard band
- period: 20
- standard deviation: 2
- applied price: CLOSE

### Fast/extreme band
- period: 4
- standard deviation: 4
- applied price: OPEN

A Double-B situation occurs when the same H1 candle reaches/pierces both relevant bands
on one side.

The important meaning is not simply overbought/oversold.

The conceptual meaning is:

> Even a normal Bollinger Band contains price with high frequency.
> Requiring simultaneous interaction with two differently constructed bands selects a rarer
> event in which ordinary price behavior has broken down and liquidity/volatility may be expanding.

Therefore:

```text
DOUBLE-B != DIRECTION
DOUBLE-B = RARE EVENT / ATTENTION TRIGGER
```

## 4. Three trading families

### BASIC (기본)
The familiar edge fade:
- lower-side event can support LONG;
- upper-side event can support SHORT.

But the side alone is insufficient.
Range/rotation context and lack of accepted directional expansion should support the fade.

### BREAKOUT (돌파)
Trade with fresh directional expansion.

A strong body close beyond bands can be evidence, but V7 discovery shows it is neither
necessary nor sufficient by itself.

The actual question is whether the event is a **fresh expansion** with room to continue.

### TURNING (변곡)
Capture a directional transition.

The key V7 interpretation is **terminal expansion**:
a rare event can be the final/climactic extension of an already mature move.

A visually powerful candle can therefore be either breakout or turning.

## 5. 더캔이지추격깨

The user's remembered mnemonic/context table is:

```text
더블비
캔들
이평선
지지저항
추세선
이격도(볼밴)
깼는지(세션 첫 캔들의 고/저가)
```

The table is not currently treated as a mechanical additive score.

### Double-B
What rare event occurred?
Upper, lower, ambiguous, fresh, repeated?

### Candle
Questions can include:
- body acceptance vs wick rejection;
- close location inside the candle;
- displacement vs exhaustion;
- relationship to prior candles;
- whether the candle is unusually large relative to current KTR.

### Moving average
Questions can include:
- direction;
- price location relative to the average;
- maturity / distance from the average;
- whether the event is early in a move or heavily extended.

### Support / resistance
Use only causally known levels.

Questions:
- fresh structural break?
- range boundary?
- prior accepted/rejected level?
- remaining room before next meaningful barrier?

### Trendline
This is explicitly discretionary.

If it cannot be drawn/assessed reliably from the available chart without hindsight,
record `UNKNOWN` and do not substitute an arbitrary regression line merely to fill the cell.

### Bollinger separation / deviation
Not just "wide or narrow".

Questions:
- fresh expansion?
- compression release?
- terminal blow-off?
- price extension still confirmed by short-horizon band behavior?
- long-horizon extension large while short-horizon propulsion weakens?

### Session opening candle break
For Asia / Europe / US:
- identify first H1 candle of the session;
- observe its high/low;
- ask whether price only wicked through, accepted beyond, rejected back inside, or never broke it.

Exact broker-server mapping must be frozen per feed.

## 6. KTR

KTR is the True Range of the first H1 candle of the Asia, Europe, or US session.

KTR is interpreted as a measure of the session's current force/distance scale.

The user's description explicitly allows adaptive decisions:
- a huge KTR can make 3KTR TP absurdly distant;
- a tiny KTR can make 1KTR SL too tight;
- a small KTR may justify a wider multiple such as 3.5KTR;
- staged entry may be placed in 0.5KTR increments.

No single KTR multiplier is current authority.

## 7. KTR and structural geometry

The V7 decision should work in this order:

1. determine the contextual thesis;
2. identify price-level invalidation;
3. convert that distance into KTR;
4. judge whether the KTR multiple is sensible for the current regime;
5. identify realistic target/next barrier;
6. convert available room into KTR;
7. decide whether RR and context justify entry.

Thus KTR is a **coordinate system**, not the thesis.

## 8. Staged-entry interpretation

Staged entry is optional and setup-dependent.

Current requested discovery convention:
- adds every 0.5 KTR when planned;
- common SL;
- each leg individually sized to lose the same 1R at common SL.

Important implication:
if 7 legs fill and the common SL is hit, the campaign loses 7R.

Therefore staged entry must be planned before adverse movement occurs.

### Where staging may make sense
- planned breakout pullback;
- BASIC mean-reversion zone;
- a thesis in which adverse excursion inside a defined zone is expected.

### Where blind staging is dangerous
- momentum breakout that is failing;
- unconfirmed TURNING fade;
- any trade where moving against the position is evidence that the thesis is wrong.

## 9. Current V7 decision vocabulary

Every event should end in one of:

```text
ENTER_NOW_LONG
ENTER_NOW_SHORT
WAIT_CONFIRM_LONG_BIAS
WAIT_CONFIRM_SHORT_BIAS
WAIT_NO_DIRECTION
SKIP
```

And one archetype label:

```text
BASIC
BREAKOUT
TURNING
UNKNOWN
```

This avoids forcing every rare event into a trade.
