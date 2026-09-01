# V8-A-N N2 — M5 Bollinger(20,2) State-Combination Research

Date: 2026-09-02  
Status: **DEVELOPMENT / SHADOW EVIDENCE ONLY**  
Population: frozen N1 = 1.50ATR fresh P15 75-cross, GOLD#, 2024-2026  
2021: **UNTOUCHED**

## 1. Research question

Instead of forcing Bollinger information into a LONG/SHORT voter, classify the chart state around the N1 probability-surge candle using:

- recent close location relative to lower / middle / upper Bollinger references;
- whether the trigger candle closes outside a band or only remains nearer one side;
- normalized distance from SMA20 and how that distance changes;
- whether the distance from the SMA tends to expand or contract;
- Bollinger bandwidth expansion/contraction;
- how often price crosses the middle line.

Primary window was frozen as **5 prior completed M5 bars + the N1 trigger bar**.  
The analogous 3-bar and 8-bar histories are used only as robustness checks.

The trigger candle was verified mechanically: for all 2,149 N1 events, it is the completed M5 bar exactly five minutes before `decision`.

## 2. State definitions

Bollinger = SMA20 +/- 2 population standard deviations.

Normalized SMA gap:

`gap = (close - SMA20) / (upper - SMA20)`

Therefore:
- upper band = +1
- SMA = 0
- lower band = -1

Close anchor:
- `LOWER`: gap <= -0.5
- `MID`: -0.5 < gap < +0.5
- `UPPER`: gap >= +0.5

Outside state is recorded separately:
- `OUT_L`: gap < -1
- `IN`: inside bands
- `OUT_U`: gap > +1

`prior residence` = which anchor dominates the prior n bars.

`abs-gap path AWAY` = among consecutive bars, absolute SMA distance increases more often than it decreases.

`bandwidth path CONTRACT/EXPAND` = whether band width decreases or increases more often over the window.

No outcome-optimized Bollinger threshold was fitted.

## 3. Marginal result: individual Bollinger elements are weak

No single state is a useful universal direction voter.

Examples:
- trigger LOWER / MID / UPPER alone: approximately 51% UP each in the pooled sample.
- bandwidth expansion alone: approximately 50% direction.
- bandwidth contraction alone: somewhat UP-biased pooled, but unstable by year.
- SMA-gap rising/falling alone: near 50%.
- simply closing outside upper/lower bands is not symmetrically directional.

The information is mainly in **state transitions/combinations**, not isolated Bollinger values.

## 4. Most interpretable cross-window state: BB-A

### `MIDDLE residence -> trigger NEAR LOWER but still inside bands`

Primary n=5 definition:
- prior five M5 closes are predominantly nearest the SMA/middle reference;
- trigger candle closes nearest the lower band;
- trigger candle does **not** close below the lower band.

Observed first-hit direction = **DOWN**:

- 2024: N27 / 59.26% DOWN
- 2025: N25 / 64.00% DOWN
- 2026: N26 / 57.69% DOWN
- pooled: N78 / 60.26% DOWN

Window robustness:

- n=3: 60.00 / 63.64 / 58.33% DOWN
- n=5: 59.26 / 64.00 / 57.69% DOWN
- n=8: 53.57 / 60.87 / 61.90% DOWN

This is the cleanest **downside state** that survives changing the recent-history length.

Interpretation: the N1 trigger emerges from a middle-band residence and migrates into the lower-side zone, but without an outright lower-band close. This behaves more like early downside acceptance/transition than a lower-band mean-reversion signal.

## 5. Strongest cross-window upside state: BB-B

### `MIDDLE residence -> trigger closes ABOVE UPPER band + SMA distance tends to widen`

Definition:
- prior n bars predominantly reside near the middle reference;
- trigger closes above the upper Bollinger band;
- absolute distance from SMA increases on a majority of steps.

Direction = **UP**.

For n=5:
- 2024: N58 / 58.62% UP
- 2025: N48 / 60.42% UP
- 2026: N44 / 59.09% UP
- pooled: N150 / 59.33% UP

Window robustness:
- n=3: 64.29 / 60.00 / 55.26% UP
- n=5: 58.62 / 60.42 / 59.09% UP
- n=8: 58.97 / 63.64 / 62.50% UP

This is the strongest **structurally robust upside archetype**. It survives every year and every tested recent-history length.

Important asymmetry: the symmetric lower-band version does **not** work.  
`MIDDLE residence -> below lower band + distance widening` is near 50% overall and reverses by year.

Therefore the finding is not a generic symmetric “band breakout” rule.

## 6. Strongest n=5-specific state: BB-C

### `trigger inside bands + SMA-gap shifted downward + >=2 middle-line crosses`

Direction = **DOWN**:

- 2024: N28 / 64.29%
- 2025: N26 / 61.54%
- 2026: N17 / 64.71%
- pooled: N71 / 63.38%

This is the strongest annual-minimum result in the primary n=5 categorical scan.

It also interacts interestingly with N2-R1. On the 22 cases where N2-R1 points opposite the BB-C direction, BB-C is correct 72.73% pooled. Year-level disagreement samples are only 11 / 5 / 6, so this is **not** an override rule yet.

BB-C does not reproduce cleanly at n=3 and n=8, so it should be treated as a **5-bar/25-minute-context discovery**, not a general Bollinger law.

## 7. Another n=5 state: BB-D

### `prior MIDDLE residence + bandwidth contracting + exactly one middle-line cross`

Direction = **UP**:

- 2024: 60.00%
- 2025: 61.54%
- 2026: 62.50%
- N160 / pooled 61.25%

This is interesting because it explicitly uses the user's bandwidth idea: a middle-centered state that is compressing, with one center transition, is UP-biased in the N1 population.

However, it is not robust to n=3 or n=8 and its disagreement with N2-R1 is unstable, especially in 2025. Treat it as discovery only.

## 8. Exact six-candle anchor sequences

Exact `L/M/U` sequences are too sparse to use as authority.

For example `MMMMMU` is UP-biased:
- N55 pooled / 61.82% UP
- 2024 63.16%
- 2025 64.71%
- 2026 57.89%

But most exact sequences have small annual counts and many sequences reverse across years.

Therefore the useful abstraction is **residence + trigger transition + distance path + bandwidth path**, not literal six-character patterns.

## 9. Multiple-testing audit

The primary n=5 scan covered 749 eligible pair/triple/quadruple categorical states after sample floors.

Best observed minimum annual accuracy = 61.54%.

Within-year label permutation across the same family:
- null mean best-min ≈ 60.1%
- family-wise empirical p ≈ 0.268

So the strongest n=5 combination is **not exceptional enough after family-wide multiplicity** to promote.

The cross-window analog scan is more conservative, requiring the same semantic state across n=3/5/8. Its strongest state is BB-B, but the family-wise empirical p is still ≈ 0.306.

Therefore these are **structured development candidates, not validated edge**.

## 10. Main research interpretation

The useful Bollinger information does not appear to be:

`upper band = LONG / lower band = SHORT`

or

`band widening = continuation / narrowing = reversal`.

Instead the more useful object is the **path by which the N1 trigger arrives at its Bollinger location**.

Two candidate market states stand out:

```text
A. middle residence
   -> trigger migrates to lower-side zone but remains inside
   -> DOWN-biased (~60%)

B. middle residence
   -> trigger closes through upper band
   -> SMA distance has been widening
   -> UP-biased (~59-61%, robust across n=3/5/8)
```

A third, stronger but narrower state is:

```text
inside-band choppy state
+ multiple SMA crosses
+ net normalized position shifts down
-> DOWN-biased (~63%, n=5-specific)
```

This supports keeping Bollinger as a **state/context representation**, not converting each component into a vote.

## 11. Decision

- Keep N1 unchanged.
- Do not add Bollinger as another generic voter.
- Retain BB-A and BB-B as the cleanest cross-window state candidates.
- Retain BB-C as a stronger but narrower n=5 discovery state.
- Do not promote any of them yet because the family-wise scan does not rule out selection effects.
- Next high-value test: condition the already discovered `M5 Stoch -> M1 transition -> raw-tick RUN flip` sequence on these frozen Bollinger states to see whether Bollinger describes **when that transition mechanism is reliable**, rather than asking Bollinger to predict direction by itself.
