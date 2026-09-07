# V9 Paper Trading Journal — Consolidated January Development Record

Date synchronized: `2026-09-07`
Status: `DEVELOPMENT / DISCRETIONARY REPLAY`
Execution authority: `M1 DESCRIPTIVE ONLY UNLESS EXACT TICK IS EXPLICITLY AVAILABLE`
Production authority: `NONE`
Market: `GOLD# ONLY`
Raw M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
Reserve: `GOLD# 2021 untouched`

## Journal rules

Every trade records its thesis before future outcome.

Required fields:

```text
trade id
decision timestamp
direction
parent context
current child route
falsification anchor
genuine restoration/invalidation behavior when known
first natural destination
structural room
uncertainty
```

Management uses only newly revealed information. Do not rewrite the original thesis.

No strategy-level WR/PF/expectancy claim is authorized from these contaminated development examples.

---

## Trade summary

| ID | Date | Dir | Entry | Falsification | CP1 / Destination | Outcome | Descriptive R |
|---|---|---|---:|---|---|---|---:|
| V9-PAPER-001 | 2026-01-07 | SHORT | ~4445.70 | ~4463.60 restore | 4417-4409 | destination resolved | +1.52R |
| V9-PAPER-002 | 2026-01-13 16:00 | LONG | ~4609.72 | restore below 4598.5-4600 | 4625-4630 | destination resolved | +1.36R |
| V9-PAPER-003 | 2026-01-13 20:15 | SHORT | ~4593.66 | restore/accept above 4600-4602 | 4575-4578 | destination resolved | +2.29R |
| V9-PAPER-004 | 2026-01-14 02:45 | LONG | ~4605.77 | re-loss below 4599-4600 | 4618-4623 | destination resolved | +1.95R |
| V9-PAPER-005 | 2026-01-15 10:00 | LONG | ~4603.78 | genuine re-loss below 4598.5-4599 | 4613.5-4617.5 | destination resolved | +1.84R |
| V9-PAPER-006 | 2026-01-16 19:00 | SHORT | ~4589.27 | restore above 4600-4602 | 4564-4571 | weekend-gap invalidation | ~-3.36R first-print mark* |
| V9-PAPER-007 | 2026-01-29 12:00 | SHORT | ~5512.62 | restore/accept above 5532-5535 | 5474-5483 | destination resolved | +1.42R |
| V9-2025JAN-PAPER-001 | 2025-01-08 12:00 | LONG | ~2653.74 | genuine re-loss below 2649-2650 | 2660-2663 | structural invalidation | -1.04R |

`*` P006 is not exact executable P/L. The market reopened beyond the structural invalidation after weekend closure.

---

## V9-PAPER-001 — 2026-01-07 SHORT

### Pre-entry

```text
Entry ~4445.70
Falsification ~4463.60 genuine upper restoration
Destination 4417-4409
Risk ~17.90p
```

Thesis: prior upper child structure was not maintaining value and settlement centers had migrated lower. The trade did not require a universal bearish trend claim.

### Management / exit

No automatic BE or partial was used. Price reached the pre-identified lower destination and the trade resolved near ~4418.58.

Descriptive result: `~+1.52R`.

Lesson: the Decision Corridor can create >1R naturally from local asymmetry, but this trade is process rehearsal only.

---

## V9-PAPER-002 — 2026-01-13 LONG

### Frozen thesis

```text
Timestamp 16:00
Entry ~4609.72
Parent: Daily/H4 bullish price discovery, H1 child corrected into 4578-4600 balance
Child: recovery through 4585/4595/4600; accepted ~4599.5-4601 launch base
Falsification: genuine restoration below ~4598.5-4600
CP1: ~4625-4630
Risk ~11.22p
Room to CP1 edge ~15.28p
```

### Lifecycle

16:44 M1 high ~4625.91 entered CP1 before falsification.

Descriptive result: `~+1.36R`.

Post-CP archaeology later showed unstable acceptance/rejection around the high. The CP1 full exit remains a useful control in this case.

Key limitation: falsification was not stress-tested.

---

## V9-PAPER-003 — 2026-01-13 SHORT

### Frozen thesis

```text
Timestamp 20:15
Entry ~4593.66
Falsification: genuine restoration/acceptance above ~4600-4602
CP1: ~4575-4578
Risk ~6.84p
CP1 reward ~15.66p
```

The entry waited for repair rather than chasing the initial breakdown.

### Management / result

Price probed near the falsification area (including ~4601.91) but did not rebuild value above it. The thesis remained alive and CP1 was reached around 22:33.

Descriptive result: `~+2.29R`.

Lesson: `touch/penetration != genuine restoration`; failed repair can create an unusually close functional anchor. Reproducibility of that distinction remains unresolved.

---

## V9-PAPER-004 — 2026-01-14 LONG

### Frozen thesis

```text
Timestamp 02:45
Entry ~4605.77
Prior bearish ~4600 anchor had been genuinely restored and role-inverted
Falsification: genuine re-loss below ~4599-4600
CP1: ~4618-4623
Risk ~6.27p
CP1 reward ~12.23p
```

03:17 M1 high ~4618.15 reached CP1.

Descriptive result: `~+1.95R`.

Post-CP archaeology later showed that CP1 was eventually accepted/consumed and much larger MFE existed. However slow structural runner recognition would still have given back most of that excursion. P004 therefore motivates continuation-capture research but does not validate passive runner holding.

---

## V9-PAPER-005 — 2026-01-15 LONG

### Frozen thesis

```text
Timestamp 10:00
Entry ~4603.78
Child: lower 4581-4597 memory defended, value repaired above 4600
Falsification: genuine re-loss/reacceptance below ~4598.5-4599
CP1: ~4613.5-4617.5
Risk ~5.28p
CP1 reward ~9.72p
```

Immediate M1 penetrated as low as ~4597.8 but did not rebuild lower value. CP1 was reached at 12:08.

Descriptive result: `~+1.84R`.

Lesson: this is a central borderline functional-falsification example. A hard price stop and a structural invalidation decision would have behaved differently. Post-CP two-way rotation strongly argues against naive passive runner holding.

---

## V9-PAPER-006 — 2026-01-16 SHORT

### Frozen thesis

```text
Timestamp 19:00
Entry ~4589.27
Parent: larger bullish structure, local bearish child traversal
Repair tested broken 4580-4600 memory from below
Falsification: genuine restoration/reacceptance above ~4600-4602
CP1: ~4564-4571
Risk ~11.73p
Reward to ~4571 ~18.27p
```

Friday trading came close to the destination but did not reach it and did not restore the structural falsification.

Monday reopened around ~4628.71, far beyond the anchor.

Lifecycle: `INVALIDATED — WEEKEND GAP / EXECUTION-CENSORED FAILURE`.

Descriptive first-print adverse mark: `~-3.36R`; not exact executable P/L.

Permanent lesson:

```text
near structural falsification != near executable realized loss
```

Do not convert this one case into a mechanical Friday veto.

---

## V9-PAPER-007 — 2026-01-29 SHORT

### Frozen thesis

```text
Timestamp 12:00
Entry ~5512.62
Parent: Daily/H4 bull price discovery but damaged top child
Large scar ~5598; failed repair near ~5595
Smaller child repair only to ~5529.65
Falsification: genuine restoration/acceptance above ~5532-5535
CP1: ~5474-5483
Risk ~20.88p
Reward to near edge ~29.62p
```

12:58 M1 low ~5482.36 entered CP1.

Descriptive result: `~+1.42R`.

Lesson: the trade authority was not the large scar itself. A later smaller child repair created a nearer counterfactual anchor. This supports hierarchical route switching. Anchor selection remains qualitative.

---

## V9-2025JAN-PAPER-001 — 2025-01-08 LONG

### Frozen thesis

```text
Timestamp 12:00
Entry ~2653.74
Parent: H4/D1 broad recovery from late-Dec lows
Child: 2645-2647 base -> migration 2652-2654; pullback to 2649.57 repaired
Falsification: genuine re-loss/acceptance below ~2649-2650
CP1: ~2660-2663
Risk ~4.24p
Planned room ~6.26p (~1.48R)
```

### Exit

M1 sequence:

```text
13:27 close 2649.53
13:28 close 2649.32
13:29 close 2648.95
```

This was treated as genuine value restoration below the repaired base rather than a wick.

Exit reference ~2649.32.

Descriptive result: `~-1.04R`.

Price later rallied to ~2666. This does not rescue the trade. The original child thesis was already invalidated; the later rise is a new episode.

---

## January-level evidence summary

### January 2026

- 7 trades including the first process rehearsal;
- 6 destination-resolved winners;
- 1 gap/execution-censored failure;
- destination-winner sum ~+10.38R;
- not validation.

### January 2025

- 1 actual trade;
- 1 structural loss ~-1.04R;
- many NO TRADE / NOT YET decisions;
- not validation.

Main transfer conclusion:

> V9 market-reading discipline transferred more clearly than trade frequency or performance.

---

## Exit/Distance feedback after journal review

Exact H4-normalized distance audit shows that several 2026 winners reached CP1 after only ~0.3-0.4S. Their strong R was mainly entry-location quality, not large trend capture.

A neutral `50% CP1 + 50% original-falsification runner` challenger underperformed the CP1 full-exit control in the audited cohort.

Therefore:

- do not widen TP mechanically;
- do not promote passive runners;
- keep CP1 full-exit as control;
- study `exit -> new earned continuation re-entry`;
- separately study `OPEN ROUTE` price-discovery entries with nearby thesis-dependent anchors.

See:

- `results/V9_EXIT_DISTANCE_SHADOW_AUDIT_20260907.md`
- `V9_NEXT_RESEARCH_CONTRACT_EXIT_DISTANCE_OPEN_ROUTE_20260907.md`
