# V8-A-N-SLOW Dynamic Structural State Research — 2026-09-03

Status: `DEVELOPMENT EVIDENCE / STRUCTURAL PHASE COMPLETE / NO PRODUCTION AUTHORITY`
Market: `GOLD#`
Development evidence: `2022-2026`
Reserve: `GOLD# 2021 untouched`

## 1. Authority and population

Per project direction on 2026-09-03, the reconstructed Slow-N Phase-0 / Phase-2 population is now treated as the **exact project population authority** for downstream V8 research. Small historical parity differences versus the earlier stored ledgers are no longer a research blocker and must not be reopened unless a direct contradiction is found.

Reconstructed fresh75 / acceptance counts:

```text
Phase-0
2024 fresh75 648 -> acceptance 281
2025 fresh75 533 -> acceptance 234
2026 fresh75 322 -> acceptance 154

Phase-2
2024 fresh75 735 -> acceptance 318
2025 fresh75 583 -> acceptance 239
2026 fresh75 291 -> acceptance 144
```

Total accepted events:
`2024 599 / 2025 473 / 2026 298`.

The generator is the current Slow-N 4-class model semantics:
`class0 <=15m / class1 15-30m / class2 30-60m / class3 not by 60m`, with `P15 = class0 probability`.

Primary lifecycle remains:
`fresh75 -> <=15m 0.25 H4ATR M1-close reveal -> >=25% pullback with origin retained -> 0.25 H4ATR M1-close reclaim/ACCEPTANCE`.

## 2. Static retention revalidation on the exact population

Primary label remains wick integrity of the accepted pullback extreme.

Chronological micro3 (`prog1 + run_accept + prog3`) AUC:

| Horizon | P0 2025 | P0 2026 | P2 2025 | P2 2026 |
|---|---:|---:|---:|---:|
| 15m | .720 | .756 | .742 | .755 |
| 30m | .701 | .723 | .699 | .710 |
| 60m | .705 | .722 | .702 | .705 |

15m base retention:
`P0 36.8% / 34.4%; P2 37.7% / 34.7%` (2025/2026).

Conclusion:
static acceptance-time micro3 remains a real **initial structural-quality ranking signal**. It is not generic continuation probability.

## 3. Dynamic break hazard

After acceptance, conditional break hazards were evaluated on surviving risk sets:

```text
0->1m
1->3m
3->5m
5->10m
10->15m
```

The strong causal-control model used current structural geometry/process information:
- current normalized distance to pullback extreme;
- nearest structural approach so far;
- progress/MFE so far;
- accepted reveal/pullback/reclaim geometry;
- reveal/retest/acceptance timing.

Geometry/process AUC:

| Interval | P0 2025 | P0 2026 | P2 2025 | P2 2026 |
|---|---:|---:|---:|---:|
| 0->1m | .879 | .833 | .850 | .831 |
| 1->3m | .791 | .846 | .801 | .845 |
| 3->5m | .811 | .822 | .840 | .863 |
| 5->10m | .756 | .824 | .844 | .821 |
| 10->15m | .787 | .802 | .667 | .740 |

Adding acceptance-time micro3 after these controls usually added approximately zero or negative incremental AUC. Current-time micro3 also added approximately zero.

Conclusion:
`micro3` should **not** be repeatedly recomputed as the main dynamic updater.

Working architecture:

```text
ACCEPTANCE
-> acceptance-time micro3 = initial structural-quality prior
-> dynamic geometry/process state = ongoing break-hazard updater
```

The dynamic state is structural, not a direction classifier.

## 4. Hierarchical competing risk

The original flat `BREAK / SAME75 / OPP75` competition is rejected because opposite-side 0.75ATR is structurally nested behind the pullback-extreme failure boundary.

Correct State A:

```text
ACCEPTANCE alive
-> BREAK
-> SAME-SIDE 0.75ATR delivery
-> unresolved/timeout
```

Events that already reached same-side 0.75ATR before or at acceptance are `PRE_SAME75` and excluded from the live risk set.

Within 60m after acceptance, among non-preconsumed events, SAME75 before BREAK is initially only about 20-25% of resolved cases.

Conditional SAME75-before-BREAK rate among still-alive events:

```text
t=0m  ~20-25%
t=5m  ~35-41%
t=15m ~42-51%
```

This survival conditioning is real, but current barrier geometry/path explains most of its predictability. Models using distance-to-break + distance-to-target + path state produced roughly AUC .67-.79 across future cells. Adding acceptance micro3 generally did not improve the bridge.

Therefore:
`dynamic competing risk` is useful state information, but it is not new directional alpha.

## 5. Wick breach versus close integrity

Wick equality still counts as a sensitive structural break for the primary retention label, but it must no longer be treated as automatic terminal invalidation.

At 15m, approximately:
- `WICK_INTACT`: ~30-38% of accepted events;
- `WICK_ONLY_BREAK but M1 closes remain inside`: ~6-11%;
- `CLOSE_BREAK`: ~55-62%.

Among events that had not already delivered same-side 0.75ATR by 15m, later 60m same-side delivery:

```text
WICK_INTACT       48.8% pooled
WICK_ONLY_BREAK   40.3% pooled
CLOSE_BREAK       24.8% pooled

CLOSE_INTACT
(WICK_INTACT + WICK_ONLY_BREAK)
                   47.3% pooled
CLOSE_BREAK        24.8% pooled
```

So close integrity carries materially stronger strategic-validity meaning than a single wick touch.

However, micro3 predicts wick retention more strongly than close retention. Therefore do not replace the wick label with close retention. Use a staged structural state:

```text
PRISTINE = wick intact
DAMAGED = wick breached but close integrity retained
CLOSE_BROKEN = stronger structural invalidation
```

No trading exit rule is frozen from these states yet.

## 6. Post-break state

Among State-A BREAK events, the break M1 itself closed back inside the pullback structure roughly 41-48% of the time.

For close-through breaks, subsequent:
`close repair back inside structure` versus `additional adverse 0.10S move`
was approximately balanced.

From break close, equal-distance +/-0.10S competition was:

```text
original-direction side: 452
adverse side:            475
```

essentially chance.

Conclusion:
- wick break is not reversal;
- close-through break is not reliable opposite-direction continuation;
- post-break direction remains unfrozen.

## 7. Direction / regime interaction

Static 15m retention ranking remains direction-asymmetric.

Micro3 AUC:

```text
P0 2025 SHORT .793 / LONG .621
P0 2026 SHORT .821 / LONG .695
P2 2025 SHORT .779 / LONG .697
P2 2026 SHORT .846 / LONG .674
```

This is persistent enough to treat direction as an interaction variable, but not enough to create a SHORT-only trading rule from consumed years.

Quarter stress remains mostly positive but regime-sensitive. Weakest substantial cells remain around:
- `2025Q3 ~.61-.63`
- `2026Q2 ~.66-.71`

No threshold rescue and no quarter-specific permission rule.

## 8. Raw tick status

Full Slow-N acceptance-time raw-tick incremental research remains fail-closed.

Existing coverage audit:
`aligned = 83.853%`
`joint aligned/placebo = 69.660%`

Predeclared gates:
`aligned >=90%`
`joint >=80%`.

Therefore no tick feature may be promoted from this incomplete coverage.

## 9. BB-B status

BB-B remains a retained secondary context from the current Slow-N fresh population:
`Phase-0 N64 65.63% / Phase-2 N63 65.08%`.

No new BB-B acceptance/retention gate is frozen here. The structural phase does not require a BB-B threshold before practical movement/payoff characterization.

## 10. Structural phase freeze before practical research

The research semantics are now frozen enough to begin the next stage without optimizing entries/exits yet:

```text
ONSET
-> actual direction reveal
-> pullback
-> reclaim / ACCEPTANCE
-> initial structural-quality prior (micro3)
-> dynamic structural state
   PRISTINE / DAMAGED / CLOSE_BROKEN
-> geometry/process hazard
-> competing BREAK vs SAME75 vs unresolved
```

Mandatory guardrails:
- retention != generic momentum;
- equal-distance direction remains near chance;
- dynamic AUC is mostly structural geometry, not alpha;
- no production threshold;
- no P/L threshold search;
- no 2021 use.

## 11. Next stage — practical movement/payoff characterization

The next research stage may now begin.

It must first characterize, without optimizing TP/SL:

- MFE while structure is alive;
- current directional displacement;
- giveback from MFE;
- target-distance distribution;
- first-hit time distribution;
- short-move versus large-winner continuation;
- how these distributions change by PRISTINE / DAMAGED / CLOSE_BROKEN state;
- how dynamic break risk and directional progress jointly separate `take smaller profit` versus `runner candidate`.

Only after that descriptive/causal mapping survives P0/P2, years, direction and regime should explicit entry/SL/TP economics be preregistered.

`GOLD# 2021` remains locked.
