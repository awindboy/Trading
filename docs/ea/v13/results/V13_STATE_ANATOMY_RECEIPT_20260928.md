# V13 State-Anatomy / Trade-Path Classification receipt

Date: `2026-09-28`
Status: `CONSUMED DEVELOPMENT / OBSERVATION ONLY / NO ACTION AUTHORITY BY ITSELF`
Base GitHub `main`: `652dcd070206f04a51eb5a7451a253393b60ee03`

## Question

Why do some HA-9 add-on Children align immediately after entry while others spend the same Journey for hours without proving the signal-H4 favorable extreme? Holding duration is treated as a **result label**, not a causal feature.

## Populations

From 2,893 canonical actual-tick add-ons:

| Label | N |
| --- | ---: |
| `<=1h winner` | 816 |
| `1-4h winner` | 644 |
| `4-8h loss` | 734 |
| `>=8h survivor` | 87 |
| other | 612 |

Proof rates confirm that the 4-8h loss population is essentially the no-proof timeout problem: `0.14%` proved versus `100%` of <=1h winners and `89.44%` of 1-4h winners.

## Method

- T0: signal-H4 / entry-known state only.
- T1..T4: identical causal checkpoints after first, second, third and fourth completed H1.
- State representation: H4/H1 HA, partial-H4 transition, M1/M5/M15/M30 path morphology, directional progress, MFE/MAE, efficiency, crossings, activity, raw-swing progression.
- Matching: quarter, side, Child ordinal and entry-lag state, with continuous H4 geometry matching.
- Uncertainty: Journey-grouped validation / bootstrap rather than treating Children as independent.

## T0 result

T0 alone is weak for the broad winner/loss problem. Journey-grouped CV AUC for static T0 was `0.526`.

The strongest T0 separation for immediate winners was favorable raw-close position. In the <=1h winner versus 4-8h loser matched population, mean side-oriented raw-close position was `0.202` versus `-0.015`, SMD `1.02`.

## T1 result

The first completed H1 contains a much larger state separation. In matched 1-4h winner versus 4-8h loser pairs:

- directional raw progress difference: `0.305` H4-range units;
- M1 efficiency difference: `0.120`;
- MAE difference: `-0.169` H4-range units;
- partial-H4 directional delta difference: `0.255`;
- relative activity itself was almost flat: `-0.014`.

Journey-grouped dynamic T1 AUC was `0.736`; adding T0 only moved it to `0.739`. The dominant axis is therefore actual directional progress after entry, with HA/path transition adding secondary information.

## State-sequence result

H1 path order matters. `opposed -> aligned` repair is materially different from persistent opposition, and a current aligned state is not equivalent to having been aligned from the start. This supports the State-Anatomy premise that transition sequence is more informative than a standalone HASTOC/Delta/wick reading.

The three-state coherent alignment bootstrap also separates strongly at T1: coherent-aligned win rate `77.3%` versus coherent-opposed `30.4%`.

## Archetype conclusion

K-means silhouette values were low-to-moderate rather than cleanly separated islands (`k=2` about `0.24`). The data are better described as a continuous **directional-acceptance axis** plus secondary HA/path transition, not three perfectly discrete natural clusters.

The recurring descriptive paths are:

- clean expansion;
- productive repair;
- failed alignment;
- persistent non-progress.

These names describe observed paths; they are not standalone trading rules.

## Action implication

The strongest practical implication is to use **pre-entry signal-H4 cleanliness** for admission rather than turning T1/T2 into another post-entry exit-horizon rule. Dynamic state is powerful diagnostically but too late to remove a loss trade once the Child is already open. This observation motivated SA-1; the action test is documented separately.
