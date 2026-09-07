# V9 Next Research Contract — Parent Journey Continuity and Good Attempts

Date: `2026-09-07`
Status: `ACTIVE NEXT RESEARCH CONTRACT / NO PRODUCTION AUTHORITY`
Market: `GOLD# ONLY`
Untouched reserve: `GOLD# 2021`

## 1. Research purpose

The immediate problem is not to define trend correctly.

It is:

> Can V9 preserve a useful larger market story across local trade resolution, while continuing to take only good local attempts under uncertainty?

January archaeology suggests V9 often identified good local locations but treated internal child/transit memories as if they ended the larger opportunity.
The next phase studies `continuity architecture`.

## 2. Prohibited objectives

Do not optimize:

- trend-label accuracy;
- next-bar / next-leg direction accuracy;
- a universal H1 trend formula;
- HH/HL counts;
- ATR trend thresholds;
- a fixed trend stop;
- a fixed campaign target;
- a parameter that maximizes January P/L.

Do not build an EA or classifier in this phase.

## 3. Two-ledger protocol

### Parent Ledger

Record only when the larger working story materially changes.

Fields:

```text
timestamp
working parent story
why this story is currently more coherent
largest known damage/counterflow
repair status
what behavior would materially weaken/change the parent story
uncertainty
change from previous parent entry
```

Parent states are prose beliefs, not fixed labels.

### Child Trade Ledger

Use the existing V9 trade contract:

```text
timestamp
direction
local route
entry
local falsification
first checkpoint / open route
Risk/S
checkpoint/S when applicable
uncertainty
result
```

Add:

```text
did this child result materially change the parent story? why/why not?
```

## 4. Decision philosophy

A child trade is allowed when it is a good attempt even if the parent story is uncertain.
A counter-parent child trade is allowed when local asymmetry is attractive.

Do not ask:

> Is the trend definitely up or down?

Ask:

> Is this a pitch worth swinging at, given what is currently known?

## 5. Sequential replay method

Use future-hidden replay.

Default observation resolution:

- use H1/H4 to maintain the parent story;
- use M15/M5 only as needed for child opportunity and falsification;
- change resolution adaptively;
- do not force a fixed lookback.

Reveal the future incrementally.

At each material parent update, freeze the parent ledger before revealing more data.
At every child entry, freeze the child trade contract before outcome.

## 6. What to seek deliberately

Seek all of the following, not only winners:

1. child loss while parent journey survives;
2. child win while parent journey later fails;
3. counter-parent child winner;
4. apparent parent damage that repairs;
5. genuine parent route switch;
6. parent belief that remains ambiguous for a long time;
7. repeated good child opportunities in one parent campaign;
8. long parent journey with no good local pitch;
9. false open-route opportunity;
10. large movement that V9 correctly declines because location is poor.

## 7. Memory-role overlay

For important candidates distinguish descriptively:

```text
parent memory
child / transit memory
execution memory
```

Do not determine role from timeframe name alone.

Ask whether restoration/consumption of the memory would change:

- only the local trade;
- the current child route;
- the larger parent story.

## 8. Distance coordinate

Retain:

```text
S = previous-completed H4 Wilder ATR14
```

Use it only to describe scale.

Record when useful:

```text
local Risk/S
child checkpoint/S
parent journey displacement/S
major counterflow/S
```

Do not create thresholds from this phase.

## 9. Exit and campaign treatment

Keep existing CP1 full-exit as the current local trade control while continuity research proceeds.

The key challenger is not passive runner holding.

It is:

```text
child trade resolves
-> parent story persists or changes
-> wait for next good pitch
-> new child trade only if independently justified
```

A large winner can therefore be a campaign of multiple high-quality attempts.

Do not force frequency.

## 10. Research review questions

After each replay segment ask:

- Did we improve opportunity selection, or merely tell a better story?
- Did we need to know final direction to make the decisions we made?
- Did a child result improperly reset the parent belief?
- Did parent belief become a hidden direction gate?
- Did we miss an attractive pitch because no final destination was visible?
- Did we chase because the large movement looked obvious?
- Did we invent an anchor to make R look attractive?
- Did we alter definitions after outcome?

## 11. Promotion gate

Do not formalize Parent Journey until:

- multiple future-hidden campaigns exist;
- both parent-survival and parent-failure examples exist;
- child outcome and parent-state separation remains stable;
- independent sessions produce broadly comparable narratives from the same hidden chart;
- the language does not change after each outcome;
- opportunity selection improves without becoming a direction classifier.

Only then consider shadow instrumentation.

## 12. Authority

Read together with:

1. `AGENTS_V9.md`
2. `HANDOFF_V9.md`
3. `RESEARCH_STATE_V9.md`
4. `V9_TRADING_MINDSET_AND_RESEARCH_GUARDRAILS_20260907.md`
5. `DECISIONS_V9.md`
6. `DECISIONS_V9_ADDENDUM_20260907.md`
7. `DECISIONS_V9_MINDSET_ADDENDUM_20260907.md`
8. `results/V9_PARENT_JOURNEY_ANATOMY_20260907.md`

Production authority remains `NONE`.
