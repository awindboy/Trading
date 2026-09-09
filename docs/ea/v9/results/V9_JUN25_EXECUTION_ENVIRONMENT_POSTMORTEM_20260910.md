# V9 June 2025 Execution-Environment Postmortem

Date: `2026-09-10`
Status: `CONSUMED DEVELOPMENT EVIDENCE / NOT CLEAN VALIDATION`
Market: `GOLD# ONLY`

## 1. Bottom line

June should not be summarized as `V9 cannot work`, `the market was just sideways`, or `the stop was too small`.

The strongest transfer is:

> V9 was asking an AI to make too many interpretive decisions before the objective market geometry and review environment were sufficiently standardized.

This interacted with same-auction churn and local stop selection, producing long loss clusters and poor payoff capture.

---


## 2. Evidence limitations

June is not clean validation. Preserve these limitations:

- current GitHub SSOT does not contain a fully recoverable J-001 through J-024 individual trade ledger;
- known qualitative-contamination dates existed;
- several cadence/reveal incidents occurred and exposed intervals were not backfilled;
- the post-2025-06-12 causal tooling standard improved parity but did not retroactively clean the earlier segment;
- June ended at `2025-06-30 23:57` with J-082 LONG still open; no July outcome is used to score or rescue that trade in this June postmortem.

Therefore June findings are used as execution/process evidence, not as precise strategy-performance authority.

---

## 3. What remained good

Retain:

- real pre-entry Hard SL;
- never widening the stop;
- stopped Childs were not rescued later;
- Parent and Child stayed conceptually separate;
- LONG/SHORT evaluation became materially more balanced than May first pass;
- some Parent-Journey positions generated genuinely large MFE/winners.

The problem was not that every V9 principle failed.

---

## 4. Baseball-theory audit

V9 deliberately accepts losses.

A sequence such as:

```text
-1R
-1R
+5R
```

can be entirely healthy.

June instead produced multiple clusters where many paid attempts failed while several winners were realized small relative to available Parent-Journey excursion.

That is a process warning because both sides of the intended convex architecture were pressured:

```text
too many paid swings
+
winners not always allowed to dominate
```

This does not imply a target win rate or a maximum losing streak.

---

## 5. Loss mechanism A — same-auction churn

Example window:

```text
2025-06-17 06:00 -> 2025-06-18 06:59
high-low range about 33.95p
start-to-end net move about +0.98p
average completed H1 range about 10.42p
```

The market traveled widely in both directions while ending nearly unchanged.

J-037 through J-045 repeatedly promoted local breakdown/reclaim/inversion events inside this broader rotation into new paid attempts.

The issue was not that the local events were imaginary. The issue was that `new price event` was too often treated as `good pitch`.

Permanent transfer:

```text
WHAT IS NEW? remains necessary
but new != worthwhile
```

Do not create an N-loss cooldown from this episode.

---

## 6. Loss mechanism B — local falsification inside directional movement

Example window:

```text
2025-06-26 10:00 -> 16:59
high-low range about 40.33p
start-to-end net move about -19.83p
average completed H1 range about 11.82p
```

This was not simply flat, yet J-068 through J-073 formed a six-loss cluster.

### J-073

```text
SHORT entry 3319.51
Hard SL     3325.00
risk           5.49p

16:19 M1 high 3325.20 -> Child stopped
16:36 M1 low  3309.97
```

The later decline does not rescue J-073.

It does raise the correct postmortem question:

> Was the selected 3325-area local structure truly enough to falsify the current SHORT Child, or was it ordinary intrahour reuse inside a larger directional environment?

The answer is not `always widen stops`.

The correction is objective anchor provenance and explicit attempt-scale alignment.

---

## 7. Loss mechanism C — repeated inversion inside another rotational auction

Example window:

```text
2025-06-30 07:00 -> 15:59
high-low range about 22.21p
start-to-end net move about +3.06p
average completed H1 range about 8.50p
```

J-077 through J-081 repeatedly failed around the same broad auction.

### J-077

```text
LONG entry 3280.57
Hard SL    3277.50
risk          3.07p

07:24 stop
07:26 low  3277.00
07:50 high 3285.43
07:53 high 3286.27
```

Again the later rally cannot rescue the stopped Child.

The example shows why a small local anchor needs stronger objective justification when it is given full stop authority.

---

## 8. Why `small SL` is not itself the diagnosis

Several successful V9 entries also used small stops.

A small stop can be exactly what creates a convex trade if the selected structure is a real Child falsification boundary.

Therefore do not infer:

```text
SL < average H1 range => bad
SL/S < X => bad
```

No such threshold is authorized.

The correct question is:

> What objective structure is being lost, and why does that loss end this attempt?

---

## 9. Why `CP1 2p` was misleading

June trade tables sometimes displayed the nearest remembered structure as `CP1`, occasionally only 1–5 points from entry.

This made Parent-Journey trades look as if they risked several points to target a tiny gain.

More importantly, the complete route ahead was not always represented.

Permanent correction:

```text
nearest structure != TP
nearest structure != automatic CP1
```

Future packets show the entire deterministic forward structure list and distances in points/R/S.

Only a true Local Bridge gets a fixed destination by default.

---

## 10. Winner-management problem

June included cases with substantial MFE followed by much smaller realized gains.

This does not prove that trailing stops or profit locks are needed.

The missing environment was:

```text
objective forward structures mapped before entry
+
early AI review when those structures are actually reached/crossed
+
H1 heartbeat for slow deterioration
```

A Parent-Journey should not exit simply because it is +5p/+10p or because the first nearby structure is touched.

It should also not wait blindly through every important opposing structure until most of the move is returned.

The event-driven runtime is intended to solve **review timing**, while the AI keeps the discretionary hold/exit judgment.

---

## 11. AI-overload finding

The June harness required many overlapping concepts:

- Parent support/damage;
- opposite case;
- Child role;
- independence;
- repair/reclaim language;
- memories;
- journey maturity;
- mirror check;
- hidden-veto check;
- campaign status fields;
- etc.

These fields were created for auditability, but too many mandatory discretionary labels can shift model capacity from `is this a good trade?` toward `can I complete the form consistently?`.

Post-June correction:

### Keep

- Parent belief;
- opposite case;
- good-pitch decision;
- one-sentence attempt thesis;
- objective SL structure choice;
- scale;
- WHAT IS NEW only on retry;
- concise HOLD/EXIT/REMAP evidence.

### Remove from mandatory execution

- detailed memory-role taxonomy;
- Child subtype taxonomy;
- compulsory repair/reclaim categorization;
- verbose per-trade mirror/hidden-veto essays;
- large campaign checklist every H1.

This is simplification of the harness, not abandonment of strategic discipline.

---

## 12. Review-scheduler problem

June's causal timeframe protocol was a major improvement, but practical operation still often became:

```text
advance one H1
or
advance one M15
then think
```

A real API trader needs:

```text
continuous local M1 monitoring
+
mechanical SL/destination guards
+
objective mapped structure events
+
AI call on those events
+
H1 heartbeat as maximum Parent-Journey review delay
```

This is now the active runtime direction.

---

## 13. What June does not authorize

Do not add:

- N-loss cooldown;
- max attempts;
- sideways-market ban;
- minimum R;
- minimum stop size;
- ATR stop;
- fixed take-profit;
- fixed trailing/BE/partial;
- indicator authority;
- forced side balance.

June is consumed development evidence for improving execution control, not a threshold-fitting dataset.
