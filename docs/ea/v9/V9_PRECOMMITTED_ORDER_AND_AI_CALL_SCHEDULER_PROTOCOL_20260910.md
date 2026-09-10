# V9 Precommitted Order and AI-Call Scheduler Protocol

Date: `2026-09-10`
Status: `DEFERRED IMPLEMENTATION REFERENCE`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`

## Current status

Do not implement this as the immediate V9 research priority.

First mature the chart-native HTF market map.

## Retained principle

Do not call AI continuously to search for trades.

Use:

```text
HTF MARKET MAP
-> WAIT
-> MEANINGFUL SCENARIO / POI
-> LTF EXECUTION PLAN
-> ARMED ORDER OR CONDITION
-> LOCAL RUNTIME MONITORING
```

Prepare executable conditions before price reaches them when practical.

## Later scheduler role

After the strategy is mature, runtime should handle:

- pending entries;
- cancellation;
- expiry;
- pre-fill invalidation;
- Hard SL;
- fixed destination when used;
- selected HTF review events;
- maximum-staleness fail-safe.

Ordinary candle completion should not automatically call the large model.

## Parent-Journey

Do not poll AI on every M1/M5/M15 candle.

Call AI when:

- a major mapped HTF structure is reached;
- a predeclared remap event occurs;
- progression is materially damaged;
- maximum-staleness fail-safe requires review.

## Re-entry

After a stopped Child require a new pitch.

Ask:

```text
WHAT OBJECTIVE FACT CHANGED?
IS THE NEW PITCH WORTH RISK?
```

Do not use retry counts or cooldown.
