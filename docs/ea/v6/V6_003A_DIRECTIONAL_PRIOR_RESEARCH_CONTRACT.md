# V6-003A — Multi-Environment Directional-Prior Research Contract

Status: `ACTIVE CHILD / PRE-OUTCOME DESIGN`
Date: `2026-08-29`
Production authority: `NONE`
Research benchmark control: `MENV-004`
Research panel: `13 consumed market-year environments`
GOLD 2021: `UNTOUCHED`

## 1. Research question

> Does a causal directional market prior, known before the local liquidity/ownership event finalizes direction, add independent and recurrent information about which direction/mechanism should be traded?

This is intentionally different from the old question:

```text
local event says LONG
-> does RSI/DMI/MACD agree with LONG?
```

The new role is:

```text
directional prior/state -> WHICH DIRECTION / WHICH MECHANISM
local price structure   -> WHEN / ENTRY GEOMETRY
scale x acceptance      -> DESTINATION AUTHORITY
```

## 2. Why this child exists

V3 gave deterministic local structure too much direction authority.

Prior V6 direction-sensitive indicators were usually transformed into event-direction coordinates after the event already chose a side. R1 M5 DMI was aligned with the event about 90% of the time, demonstrating redundancy.

The user explicitly reopened the architectural question:
- indicators may add evidence to direction itself;
- price structure should remain timing/risk confirmation rather than the sole directional authority.

## 3. Research population

Primary consumed research panel:

```text
GOLD 2022-2025
XAUEUR 2023-2025
USDJPY 2023-2025
BTCUSD 2023-2025
```

No market/year may be selected because it is profitable.

GOLD 2021 remains untouched.

## 4. Observation time

Directional-prior features must be frozen **before the local M5 ownership transition that finalizes the broad-event direction**.

Prefer the last fully completed relevant bars available immediately before the atomic M1 sweep/recovery begins.

If an implementation cannot identify this boundary without ambiguity, fail closed and document the causal timestamp before opening outcomes.

No unfinished HTF bar is allowed.

## 5. First step — current literature/web review

Before selecting the first indicator prior, review current sources on:
- time-series momentum / trend persistence;
- multi-horizon trend state;
- directional movement / trend-strength decomposition;
- regime-dependent reversal/continuation;
- volatility-scaled directional signals;
- robustness under nonstationarity / multiple environments.

The literature review is for mechanism design, not for importing optimized published parameters.

Record:
- state meaning;
- causal data requirements;
- known failure modes;
- simpler controls.

## 6. Measurement freeze before outcomes

After the review, freeze a **small interpretable atlas** before looking at directional-prior P/L.

The first child must contain:
- at least one conventional directional-pressure measurement;
- at least one simple price/displacement control;
- existing H1/M30 deterministic map direction as a structural control.

Do not screen hundreds of indicator settings.

No score, weighted vote, optimizer, or machine-learning classifier in V6-003A.

## 7. State labels

For each frozen directional prior, relative to a later local event classify:

```text
ALIGNED
OPPOSED
NEUTRAL / UNAVAILABLE
```

But the prior itself must be computed independently of the later event direction.

Do not use future event direction in the indicator calculation.

## 8. Primary shadow questions

Before strategy rerouting, report:

```text
opportunity N
N by market-year
N by LONG/SHORT local event
prior availability
ALIGNED / OPPOSED / NEUTRAL counts
```

Then measure raw path outcomes from the same local opportunity geometry:

```text
Fill -> +1R
Fill -> +3R
Fill -> +5R
fixed-clock ATR-normalized MFE/MAE
```

The purpose is to verify state meaning, not choose a threshold.

## 9. Required decompositions

Report:
- market-year;
- market-year x local-event direction where N permits;
- prior direction;
- local-event direction;
- prior/local agreement state;
- trade-count density.

Pooled results cannot promote the prior.

## 10. Simpler explanations

Every candidate directional prior must be compared with:
- simple signed displacement/momentum over a frozen horizon;
- the existing H1/M30 structural-map direction;
- the local event direction alone.

If a conventional indicator adds no information beyond simple displacement, do not call it a new state edge.

## 11. Strategy authority sequence

Only if a prior has recurrent nontrivial meaning may one downstream raw-replay architecture be frozen.

The first strategy variant should prefer **routing** over veto:

Possible conceptual states:

```text
prior ALIGNED with local event
-> continuation / H candidate

prior OPPOSED to local event
-> correction/reversal hypothesis or reduced destination
   only if a separately named mechanism exists

prior NEUTRAL
-> structure-only control or no change
```

Do not define `OPPOSED -> opposite H` automatically.

## 12. Trade-count constraint

The same-panel current MENV-004 accepted N is 144.

The directional-prior program is not successful if its only effect is:

```text
144 H trades
-> much smaller high-score subset
```

without a compensating independent module or major robustness benefit.

Track both:
- selected/authorized N;
- total combined architecture N.

A useful direction layer may recover new opportunities that the deterministic local-direction authority previously excluded.

## 13. Opposite thesis

> Local liquidity/ownership structure already contains nearly all usable directional information; higher-timeframe indicators are redundant, lagging, or regime-dependent and cannot improve direction authority across environments.

This thesis is equally plausible and must be tested.

## 14. Kill/degrade conditions

Downgrade/close the first directional-prior formulation if:
- alignment meaning reverses materially across markets/periods;
- a simpler displacement control explains the same relation;
- benefit exists only in pooled results;
- it reduces trade count heavily without architectural benefit;
- it merely duplicates local M5 ownership;
- it requires market-specific thresholds;
- it improves one stage while destroying average winner/EV elsewhere.

Do not rescue by trying nearby periods/windows after outcomes.

## 15. Research boundary

No production EA changes.

No GOLD 2021.

No AI/ML unless explicitly reopened later.

No outcome-selected market universe.

No exit tuning in the same child.
