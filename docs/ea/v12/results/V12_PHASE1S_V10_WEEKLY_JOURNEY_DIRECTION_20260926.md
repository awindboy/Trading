# V12 Phase 1S — V10 weekly-journey direction result

Status: **complete and reproducible / stop-risk information, directional-veto failure / no action authority**  
Date: `2026-09-26`

## Causal reconstruction

The frozen V10 R7G population contains `1,649` Children. For every V10 decision,
raw M1 was streamed chronologically and the prior/current broker week, completed
days, completed H4 bars, prior-week boundary consumption, and already-released
USD moderate/high event response were reconstructed strictly before the decision.
All `1,649` snapshots have a last-M1 timestamp earlier than the decision.

Three expanding out-of-time folds cover `1,219` Children from `2025-04-01`
through `2026-09-18`. The boundary week is embargoed so no train and test row
share a broker week. An initial process build made before that embargo repair was
discarded and is not used below. Two final 15-file builds are byte-identical and
both validators pass.

## What the weekly state predicts

The primary `WEEK_PRICE_EVENT` stop head has OOS AUC `0.684`, `0.627`, and
`0.709` across the three folds. The corresponding `R >= 2` journey head has AUC
only `0.571`, `0.498`, and `0.609`. Weekly price path therefore carries stable
stop-risk information, but the available state does not reliably identify which
high-risk Child lacks journey value. Adding released-event response does not
produce a robust improvement over weekly price path alone.

The train-defined top badness band confirms the distinction:

- kept: `931` Children, `11.28%` stopped-Child rate, `249.32R`;
- flagged: `288` Children, `22.22%` stopped-Child rate, `248.94R`;
- the flagged band contains `123.90R` of the baseline's `170.70R` >=5R tail.

The model has found a high-variance transition state: stops and major journeys
both become more likely. It has not found a disposable direction state.

## Frozen capital comparison

| Policy | Children | Units | Stopped units | Stops / 100 | Net R | DD | >=5R tail |
|---|---:|---:|---:|---:|---:|---:|---:|
| V10 R7G baseline | 1,219 | 2,851 | 353 | 12.38 | 498.26 | 57.00 | 170.70 |
| Weekly full-direction veto | 931 | 2,207 | 225 | 10.19 | 249.32 | 57.98 | 46.80 |
| Seed-protected extra-unit guard | 1,219 | 2,495 | 289 | 11.58 | 338.21 | 51.58 | 97.23 |

The full veto removes `36.26%` of stopped units, but it also removes `49.96%`
of net R and `72.58%` of >=5R tail. At the baseline stopped-unit budget it
produces only `78.50%` of baseline R. Net R is lower in all three test folds.
Both LONG and SHORT stop density improve, but LONG R falls from `501.35R` to
`268.50R`, while SHORT deteriorates from `-3.09R` to `-19.18R`.

The seed-protected view also fails the economic question. It removes `18.13%`
of stopped units but loses `32.12%` of net R and `43.04%` of >=5R tail. This is
not merely a problem caused by deleting the one-unit seed.

Using the established non-compounding sensitivity of `$10` per unit-R, the OOS
baseline is `+$4,982.60` with `-$3,530` cumulative stopped risk. Full veto is
`+$2,493.18` with `-$2,250`; seed protection is `+$3,382.10` with `-$2,890`.
These are structural-R sensitivities, not MT5 balance simulations.

## Decision

All primary gates fail except pooled stop-density improvement and stop-density
improvement on both sides. Do not promote the weekly score, event fields,
top-20% band, full veto, or seed-protected guard.

The retained mechanism is narrower: continuous weekly settlement and boundary
consumption describe transition intensity and Hard-SL risk. They do not supply
direction authorization for an existing V10 Child. The next valid large-flow
study should return to the V12 assembly: a W1 CRT Parent must create the H4
directional candidate through rejection versus outside-acceptance state, and HA
may then time the Child. Phase-1S state may accompany that candidate as a shadow
risk coordinate, but V10 entries must not be relabeled as V12 candidates.
