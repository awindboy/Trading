# V13 HA-6E2 H1 opposition-participation observation contract

Date: `2026-09-27`
Status: `FROZEN BEFORE OUTCOME MEASUREMENT / OBSERVATION ONLY`
Parent: `V13_HA6E_TICK_VOLUME_PARTICIPATION_CONTRACT_20260927.md`

## Trigger for this fixed follow-up

HA-6E1 found that full-H4 relative tick volume is mostly explained by existing H4 price morphology. However, the already-predeclared H1-path diagnostic showed a qualitatively different relation inside `persistent_opposition`: high H4 participation accompanied more next-H4 flips than low participation. This is not action authority; it motivates one narrower participation question.

## Question

When H1 standard-HA bars oppose the active H4 Journey, does the **activity carried by those opposed H1 bars** distinguish a genuine transition from a temporary H1 warning better than total H4 tick activity?

## H1 formula and parity

Rebuild standard H1 Heikin-Ashi from the exported GOLD# H1 OHLC with the same recursive standard formula used by V13. For each completed H4 decision bar, classify the four completed H1 bars inside that H4 interval as aligned/opposed to the active H4 Journey side.

The reconstructed four-bit opposition path and derived path state must exactly match the existing HA-4C path state for all decisions before outcome analysis. Any mismatch stops this probe.

## H1 participation normalization

For each completed H1 bar `h`:

```text
same_hour_median20_h = median(tick_volume of previous 20 completed H1 bars
                              with the same H1 start hour)
h1_relative_tick_volume20_h = tick_volume_h / same_hour_median20_h
```

Only earlier H1 bars enter the baseline. Pre-2024 history may initialize it.

For an H4 decision containing at least one opposed H1 bar:

```text
opposed_h1_activity = mean(h1_relative_tick_volume20 for opposed H1 bars)
```

Secondary descriptive coordinates, not separate signals:

```text
aligned_h1_activity = mean(relative activity of aligned H1 bars), where present
trailing_opposed_activity = mean(relative activity of the final consecutive opposed H1 run)
```

No absolute tick threshold or volume multiplier is allowed.

## Predeclared populations

1. all decisions with at least one H1 opposition;
2. `repaired`;
3. `unrepaired_mixed`;
4. `persistent_opposition` separately;
5. >=10-H4 long Journeys separately.

`no_opposition` is not a primary population because `opposed_h1_activity` is undefined there.

## Predeclared comparisons

- Equal-count quintiles of `opposed_h1_activity` within each path population are descriptive only.
- Outcomes: next-H4 flip, flip within three H4 bars, peak-already-past, remaining favorable excursion and giveback.
- Compare with total-H4 relative tick volume to determine whether H1-localized participation adds information.
- Within `persistent_opposition`, compare outcome gradients inside H4 body/range and ATR-normalized HA-Delta display bins where support permits.
- Report year/side direction stability and all cell counts.
- Report long-Journey false warnings and remaining favorable excursion.

## Stop / promotion boundary

This probe remains observation-only. Stop if the apparent effect is unstable by year/side, disappears after H4 morphology overlap, relies on tiny tails, or merely reproduces total-H4 volume. Any later action experiment requires a separate HA-7 contract and untouched validation.
