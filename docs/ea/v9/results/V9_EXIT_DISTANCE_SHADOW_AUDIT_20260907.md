# V9 Exit / Distance Shadow Audit — 2025-01 and 2026-01

Date: 2026-09-07
Status: DEVELOPMENT / RETROSPECTIVE SHADOW AUDIT / NO PRODUCTION AUTHORITY
Market: GOLD# ONLY
Raw M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
Reserve: GOLD# 2021 untouched

## 1. Question

Keep the already-recorded V9 entry logic fixed and audit only Exit/Distance architecture.

Primary questions:

1. Is `first active memory = full exit` truncating winner tails?
2. Does a simple `50% at CP1 + 50% structural runner` improve capture?
3. Does H4 ATR normalization change the interpretation of “near/far” across periods?
4. Can a consumed memory with no overhead destination become `OPEN ROUTE` rather than automatic NO TRADE?

This is retrospective development evidence. It does not upgrade 2025/2026 into OOS validation.

## 2. Distance scale

Use the V8 slow-scale convention:

```text
S(t) = Wilder ATR14 of the immediately previous fully completed H4 bar
```

The scale is fixed for the current H4 block.

Exact entry-time scales reconstructed from the authoritative M1 file:

| Case | Decision | previous-completed H4 ATR14 S |
|---|---|---:|
| 2025 PAPER-001 | 2025-01-08 12:00 | 11.2552 |
| 2026 PAPER-002 | 2026-01-13 16:00 | 34.6678 |
| 2026 PAPER-003 | 2026-01-13 20:15 | 35.6051 |
| 2026 PAPER-004 | 2026-01-14 02:45 | 35.3512 |
| 2026 PAPER-005 | 2026-01-15 10:00 | 33.8721 |
| 2026 PAPER-006 | 2026-01-16 19:00 | 31.2682 |
| 2026 PAPER-007 | 2026-01-29 12:00 | 74.3867 |

V9-PAPER-001 does not preserve an exact decision timestamp in the authority journal, so exact S is intentionally not inferred from a matching price print.

## 3. Exact normalized geometry

| Trade | risk p | risk/S | CP1 p | CP1/S | CP1 R |
|---|---:|---:|---:|---:|---:|
| 2025 PAPER-001 | 4.24 | 0.377 | 6.26 | 0.556 | 1.48 planned |
| P002 | 11.22 | 0.324 | 15.28 | 0.441 | 1.362 |
| P003 | 6.84 | 0.192 | 15.66 | 0.440 | 2.289 |
| P004 | 6.27 | 0.177 | 12.23 | 0.346 | 1.951 |
| P005 | 5.28 | 0.156 | 9.72 | 0.287 | 1.841 |
| P006 | 11.73 | 0.375 | 18.27 | 0.584 | 1.557 planned |
| P007 | 20.88 | 0.281 | 29.62 | 0.398 | 1.419 |

Important correction from the earlier annual-median sanity check: January 2025 S was much lower than the 2025 annual median, and PAPER-007 S was much higher than the 2026 annual median. Snapshot-level S is therefore mandatory.

The completed 2026 winners were generally reaching CP1 after only about `0.29-0.44S` except PAPER-007 (~0.40S). Their large R came primarily from close structural invalidation, not from capturing a large fraction of the market’s volatility episode.

## 4. Exit controls

Audit only the CP1-reached cohort where post-CP causal journal states exist.

A — current V9 control:

```text
100% exit at CP1
```

C — neutral partial-runner challenger:

```text
50% exit at CP1
50% remain under structural management
```

The 50/50 split is a neutral research control, not an optimized ratio.

Runner exit references use the earliest available journal-recognition point for rejection/restoration where possible. PAPER-005 requires retrospective M1 reconstruction because the original journal cadence jumped from 12:30 to 18:00; its runner result is therefore less authoritative than the other rows.

## 5. A vs C result

| Trade | CP1 role after arrival | A full-exit R | runner-leg R | C 50/50 R | C - A |
|---|---|---:|---:|---:|---:|
| P002 | rejection / failed acceptance | 1.362 | 0.807 | 1.085 | -0.277 |
| P003 | rejection / reacceptance above destination | 2.289 | 0.987 | 1.638 | -0.651 |
| P004 | acceptance/consumption, later failure | 1.951 | 1.536 | 1.743 | -0.207 |
| P005 | ambiguous, then original invalidation | 1.841 | ~-1.644 | ~0.098 | ~-1.742 |
| P007 | opposing restoration | 1.419 | -1.033 | 0.193 | -1.226 |

Same CP cohort totals:

```text
A sum  = +8.861R
A mean = +1.772R

C sum  = +4.758R
C mean = +0.952R

C - A  = -4.104R
```

Even if PAPER-005 runner is given an optimistic hard-reference exit of exactly -1R instead of the later first-clear settlement reconstruction, C remains materially below A.

PAPER-006 is unchanged by A/C because CP1 was never reached before the weekend gap. 2025 PAPER-001 is unchanged because falsification occurred before CP1.

## 6. Why C failed despite large continuation MFE

The key distinction is `available MFE != captured runner profit`.

| Trade | max favorable R before runner resolution | runner exit R | giveback from MFE to runner exit |
|---|---:|---:|---:|
| P002 | 2.211 | 0.807 | 1.404R |
| P003 | 3.480 | 0.987 | 2.493R |
| P004 | 5.740 | 1.536 | 4.204R |
| P005 | 3.659 | -1.644 | 5.303R |
| P007 | 1.998 | -1.033 | 3.031R |

There was favorable tail after CP1 in every audited row. The problem is not absence of excursion. The problem is that discretionary recognition of `acceptance / rejection / restoration` is slow enough that most of the tail can be given back before the runner is closed.

This reproduces the V8 finding in V9 language:

```text
large excursion exists
!=
passive / slow structural holding captures it
```

Therefore do not promote `partial + original-falsification runner` merely because CP1 looks short in S units.

## 7. P004 is not sufficient evidence for a runner

P004 had the strongest latent continuation:

- CP1 ~4618;
- later MFE from original entry reached ~5.74R before the runner-resolution point;
- CP1 was eventually accepted/consumed.

However a simple runner still exited around ~1.54R when the later upper route failed, below the original CP1 full-exit ~1.95R.

A separate continuation re-entry after apparent consumption was also probed retrospectively:

```text
approx re-entry 2026-01-14 05:45 close ~4628.05
falsification reference ~4623
risk ~5.05p = ~0.143S
```

It produced about +2.30R favorable excursion before a sharp return below the consumed node; a 07:45 close-based failure reference would be about -1.70R.

So even `memory consumed -> open route` is not automatically a profitable continuation trade. Consumption is context, not sufficient entry authority.

## 8. Open-route archaeology

### Positive example: 2026-01-20

At 07:00 the prior ~4690 opening high had been translated through. Under the old V9 contract this was NO TRADE because no overhead destination existed.

A reconstructed open-route state would be:

```text
07:00: prior ~4690 memory consumed -> OPEN ROUTE / ARMED
07:15: pullback low ~4694.74, close ~4695.86, still above consumed memory
```

Using ~4690 genuine restoration as the counterfactual anchor:

```text
entry reference ~4695.86
risk ~5.86p
S ~30.3242
risk ~0.193S
```

Observed development path:

```text
60m favorable MFE  ~0.705S
120m favorable MFE ~0.724S
240m favorable MFE ~1.181S
by 2026-01-21 13:00 max favorable MFE ~6.356S / ~32.9 initial-R
MAE before that large excursion only ~0.053S
```

This is a strong archaeology example that `no overhead memory` can be positive information when a nearby thesis-dependent anchor survives.

It is not validation because the family was defined after this trajectory was already known.

### Counterexample / weak geometry: 2025-01-30

After ~2785 was consumed, a pullback/recovery reference around 21:30 was ~2792.82.

If the genuinely thesis-dependent anchor remains the old ~2785 memory:

```text
risk ~7.82p
S ~11.1912
risk ~0.699S
```

This is much worse location than the 2026-01-20 example. The later path did reach ~2817, but the entry was not attractive merely because the route was open.

Therefore:

```text
PRICE DISCOVERY != TRADE
OPEN ROUTE + NEAR THESIS-DEPENDENT FALSIFICATION may be tradeable
```

Do not manufacture a closer anchor from a tiny pullback if losing that pullback would not actually falsify the open-route thesis.

## 9. Revised interpretation

The current evidence rejects the simple progression:

```text
CP1 is short in S
-> keep half as runner
-> larger average winner
```

Instead separate three problems:

```text
A. routine bridge capture
B. continuation recognition/capture
C. open-route / price-discovery entry
```

Current full-exit CP1 remains the control for A.

For B, the research bottleneck is now `capture latency`: can continuation be recognized and protected before most MFE is given back?

For C, absence of destination is no longer an automatic veto, but open route requires a nearby counterfactual anchor. Consumption alone is insufficient.

## 10. Current decisions

Retain:

- existing V9 entry logic as control;
- first active memory as a real pre-entry room constraint;
- previous-completed H4 ATR14 as the distance coordinate;
- CP1 full exit as the current control;
- explicit distinction between destination arrival, acceptance, rejection and consumption.

Downgrade / do not promote:

- fixed-point near/far judgments across years;
- `50% CP1 + 50% original structural runner` as the default solution;
- full runner under original falsification;
- `consumed memory = automatic continuation entry`;
- `no destination = automatic NO TRADE`.

Next research:

1. preserve A full-exit as control;
2. study continuation capture without changing entry eligibility;
3. compare `exit then re-enter after earned continuation` against `keep runner`;
4. for open-route states, prerecord the consumed memory, the nearest thesis-dependent restoration anchor, risk/S, and evidence that pullback repair has earned authority;
5. seek negative open-route samples deliberately;
6. keep GOLD# 2021 locked.

## 11. Evidence caveats

- 2025/2026 are consumed development evidence.
- Exact M1 is descriptive, not Bid/Ask execution authority.
- Functional restoration remains discretionary.
- P005 runner exit reconstruction is retrospective due coarse original checkpoint cadence.
- No WR/PF/expectancy validation claim is authorized from this audit.
