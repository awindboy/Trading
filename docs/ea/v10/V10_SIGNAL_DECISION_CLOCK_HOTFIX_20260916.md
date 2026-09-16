# V10 Signal Decision Clock Hotfix — Effective Time vs Actual Tick Time

Date: `2026-09-16`  
Status: `REPRODUCIBILITY / DATA-SEMANTIC HOTFIX`  
Production authority: `NONE`

## 1. Defect

The first reproducibility pack treated the raw entry-event timestamp as if it were the research decision timestamp.

For an `ENTRY_FILL`, MT5 can log the first executable fill tick one or two seconds after the H4 decision clock. The EA already records the intended signal clock in the event detail as:

```text
effective_ts=YYYY.MM.DD HH:MM:SS
```

Example:

```text
baseline decision_ts : 2025-01-09 08:00:00
EA effective_ts      : 2025.01.09 08:00:00
entry/fill event     : 2025.01.09 08:00:01
```

This is not a signal mismatch.

## 2. Canonical semantics

From this hotfix onward:

```text
decision_ts / decision_time
= research signal clock
= EA effective_ts when present

entry_event_time
= raw logger timestamp for the entry event

entry_time_actual
= actual MT5 deal/fill timestamp
```

`signal_id` remains the primary identity key.

No arbitrary time tolerance is used to reconcile a signal. The baseline decision timestamp must match `effective_ts` exactly when `effective_ts` exists.

## 3. First-run evidence

In the first bounded-m3 actual-tick evidence:

```text
1,159 selected signals
34 filled signals had entry-event timestamps after effective_ts
33 were +1 second
1 was +2 seconds
```

These lags are execution chronology, not research-decision drift.

## 4. Causal feature implication

The pre-hotfix selected-signal MTF feature ledger used the logger timestamp for these 34 rows. Its features are derived only from completed M15/M30/H1/H4 bars. The hotfix requires the recorded H4 source end to be no later than the canonical baseline decision time before canonicalizing those rows.

Future feature-ledger builds use `effective_ts` directly.

## 5. Research authority

This hotfix changes no strategy threshold, selection rule, lot map, SL, exit policy, or research conclusion. It only corrects the distinction between the research decision clock and actual execution chronology.
