# V12 Phase-1B H4-M5 journey and V10 overlay contract

Date frozen: `2026-09-23`

Status: `DEVELOPMENT OBSERVATION CONTRACT / CONSUMED EVIDENCE ONLY / NO TRADE AUTHORITY`

Contract version: `v12-phase1b-h4m5-journey-v1`

## 1. Purpose

Phase 1B does not ask whether one CRT entry beats V10. It asks whether a causal
CRT state machine can explain the beginning, continuation, interruption, and end
of price journeys, and whether that state gives structural meaning to V10's PHA
and NHA events.

The phase has two linked but separately reported views:

1. `CRT_NATIVE_JOURNEY`: exhaustive H4 C1/C2 hypotheses, M5 confirmation, key-
   level inventory, and one canonical active journey state;
2. `V10_CRT_OVERLAY`: the frozen V10 R7G Children and FAST-HA transitions mapped
   onto that state without changing admission, exit, or size.

Absolute R is not the primary gate because V10 can fund several Children inside
one journey while the CRT-native view first establishes the journey itself.

## 2. Source and authority boundary

- Input is verified GOLD# raw M1 revealed chronologically through
  `2026-09-18 23:57` only.
- H4, M5, D1, W1, and calendar-month bars are rebuilt from that prefix.
- H4 -> M5 is a V12 empirical shadow lane. It is not attributed to Romeo and
  cannot receive entry or production authority from this result.
- The frozen V10 R3 universe and R7G Stage-3 ledger are comparison overlays only.
  They cannot create or relabel a CRT journey.
- The V11 fixed H1/H4 2-left/2-right liquidity topology remains closed as a
  broad admission classifier. Phase 1B does not rescan its widths or thresholds.

## 3. Causal key-level inventory

The external one-use liquidity inventory contains completed-bar highs and lows:

- previous H4 high and low;
- previous broker day high and low;
- previous broker week high and low;
- previous broker calendar month high and low.

Each object records source time, price, family, side, `known_at`, first strict
point-rounded M1 breach, and whether birth and breach share one M1. Equality is
a touch, not consumption. A consumed object never becomes active again.

Current month, week, day, and H4 opens are persistent reference coordinates,
not one-use liquidity objects. CRT C1 high, low, and midpoint are internal
journey targets and remain separate from the external inventory.

No family is converted into a hidden importance score. At each decision the
ledger records the nearest active level above and below within every family,
raw and H4-ATR180-normalized distance, active counts, and levels consumed by the
just-completed H4.

## 4. Exhaustive H4 C1/C2 hypotheses

Every consecutive completed H4 pair forms C1/C2 and uses the frozen seven-way
interaction grammar from Phase 0.

- high sweep and return -> rejection hypothesis SHORT;
- low sweep and return -> rejection hypothesis LONG;
- high outside acceptance -> continuation hypothesis LONG;
- low outside acceptance -> continuation hypothesis SHORT;
- no-extreme and dual/conflicted states -> no directional activation.

Rejection activation requires `MODEL1_RELATIVE_THICK_M5_V1`: the Phase-1A
relative-thick ranking is applied to completed M5 bars inside C2, followed by the
first later completed M5 close beyond the trigger's opposite extreme. It uses no
numeric thickness threshold and may confirm no later than the next completed H4
bar.

Outside acceptance becomes an observation activation when C2 is completed. It
does not authorize a Child because a continuation trigger and destination
contract are not yet frozen.

## 5. Canonical journey state machine

Only one canonical observation journey is active at a time:

```text
NEUTRAL
-> ACTIVE_LONG or ACTIVE_SHORT
-> same-direction activation: REINFORCEMENT
-> opposite-direction activation: old journey ends, new journey starts
-> completed-H4 structural failure without opposite activation: NEUTRAL
-> source cutoff: OPEN_AT_CUTOFF
```

A reinforcement is a possible new-information/Child location, not automatic
capital. It updates the current structural boundary only when its activation is
completed and causal.

Structural failure is frozen by activation family:

- rejection LONG: completed H4 close strictly below C2 low;
- rejection SHORT: completed H4 close strictly above C2 high;
- high outside-acceptance LONG: completed H4 close at or below C1 high;
- low outside-acceptance SHORT: completed H4 close at or above C1 low.

C1 midpoint, opposite edge, and external key-level arrivals are milestones.
They do not end a journey by themselves. There is no fixed bar timeout.

## 6. Journey observations and outcomes

Decision records contain only information known at activation or reinforcement:

- branch, direction, M5 confirmation fields, and structural boundary;
- C1 midpoint and opposite edge;
- external level inventory and current open coordinates;
- FAST/STD/SLOW H4 HA state;
- broker weekday, H4 start hour, and elapsed calendar coordinates;
- raw and H4-ATR180 normalized distances.

Separate outcome records may contain:

- end timestamp and reason;
- midpoint, opposite-edge, and external-level milestone timestamps;
- reinforcement count;
- favorable/adverse excursion and signed close-path efficiency;
- level-consumption sequence and last arrival before termination;
- duration and H4 count.

No future milestone, end reason, later HA run length, realized R, or V10 outcome
may enter a decision record.

## 7. V10 Child overlay

Every frozen selected R7G Child is mapped at its original decision timestamp to:

- `ALIGNED_ACTIVE_JOURNEY`;
- `OPPOSED_ACTIVE_JOURNEY`; or
- `NO_ACTIVE_JOURNEY`.

For active journeys the decision ledger also records causal milestone stage,
journey age, reinforcement count, key-level context, and the ordinal number of
the selected aligned V10 Child. V10 `R`, stop, funded units, and right-tail fields
remain in a physically separate outcome link.

Phase 1B reports first aligned Child versus later aligned Children to measure
participation capacity. It does not infer that later Children should be funded,
blocked, or resized.

## 8. Completed FAST-HA transition overlay

At every completed FAST-HA direction change, classify only what is known then:

- `OPPOSITE_CRT_AUTHORIZED`: a CRT journey in the new HA direction is active;
- `OLD_JOURNEY_AFTER_KEY_ARRIVAL`: the old-direction CRT journey remains active
  and consumed a same-direction external level during the ending HA run;
- `OLD_JOURNEY_COUNTERFLOW`: the old-direction journey remains active without
  such an arrival;
- `OLD_JOURNEY_FAILED_NO_OPPOSITE`: the old journey structurally failed but no
  opposite CRT journey is active;
- `NEUTRAL_ROTATION`: no active or newly failed CRT journey explains the flip.

Later FAST-run length and the old/new-direction Child outcomes are answer-sheet
fields in a separate outcome link. A completed NHA may interrupt a Child without
authorizing opposite risk.

## 9. Evaluation

The primary result is explanatory, not an optimized P/L curve. Report:

- H4 time coverage by active journeys and neutral state;
- activation, reinforcement, structural-failure, and opposite-replacement counts;
- journey signed close-path efficiency, midpoint/opposite-edge attainment, and
  external key-level arrival by family;
- activation lag and journey duration in H4 and ATR-normalized price units;
- FAST-HA flip coverage across the five causal explanation states;
- V10 stop, stopped-unit, weighted-R, right-tail, and stop-chain morphology by
  journey relation, stage, first/later aligned Child, year, side, weekday, and
  broker H4 start hour;
- whether the same semantic ordering is stable rather than merely pooled.

No result may become a veto or sizing rule in Phase 1B. The analysis must not
claim that lower absolute stops caused by lower coverage are selective.

## 10. Reproducibility and contamination

- Decision and outcome files are separate and keyed by stable IDs.
- Same-M1 ordering remains explicit where exact ticks are absent.
- The builder must parse zero post-cutoff price rows.
- Independent reruns must produce byte-identical output packs.
- Tests must cover level birth/consumption, weekend gaps, M5 confirmation,
  reinforcement, opposite replacement, structural failure, cutoff, HA flip
  classification, and decision/outcome separation.

All results are consumed development evidence. GOLD# 2021 and chronology after
`2026-09-18 23:57` remain unread reserves.
