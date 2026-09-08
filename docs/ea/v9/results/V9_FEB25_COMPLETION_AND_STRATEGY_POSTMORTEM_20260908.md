# V9 February 2025 Completion and Strategy Postmortem

Date: `2026-09-08`
Status: `DEVELOPMENT / OUTCOME-INFORMED POSTMORTEM / NO PRODUCTION AUTHORITY`
Market: `GOLD# ONLY`
Source M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
Reserve: `GOLD# 2021 UNOPENED`

## 1. Purpose

This review is deliberately NOT an exercise in saying:

> "Price later went there, so we should have held until there."

The purpose is to inspect February's chart data and frozen trade journal and ask:

- What did V9 repeatedly read at the wrong scale?
- Which structures were given too much authority?
- Why did loss clusters occur even when direction flipped?
- Why were many winners still small in market-scale terms?
- What must change in the strategy's reasoning so the same mistakes are less likely in new unseen data?

Outcome knowledge may be used only to diagnose recurring process limitations. It must not be converted into exact-top/bottom rules or retroactively rescued trades.

---

## 2. February is complete

Final causal replay state:

```text
2025-02-28 23:57
FLAT
```

Final child population:

```text
24 closed
10 structural positive
14 structural loss
```

This count is descriptive decision evidence, not an execution-valid WR.

---

## 3. The market-scale observation

February contained multiple large H1/H4 directional journeys while V9 repeatedly reasoned around small local memories.

Descriptive examples include broad moves on the order of:

```text
~2772 -> ~2882
~2854 -> ~2943
~2892 -> ~2956
~2954 -> ~2833
```

These are not objective trend partitions and are not future rules.
They show only that the environment repeatedly offered movement materially larger than V9's routine 2-10 point child checkpoints.

The key diagnosis is:

```text
market opportunity scale > V9 decision scale
```

---

## 4. Why the original February logic churned

V9 correctly learned in January that:

```text
child failure != parent failure
```

February then increased re-participation.

But in practice V9 still often did:

```text
large parent story
-> tiny local reaction
-> tiny local anchor
-> trade
-> newest tiny anchor breaks
-> full exit
-> another tiny reaction
-> "new" trade
```

This created two symmetric errors:

1. repeated entries inside the same unresolved auction;
2. premature full exits when only a child transit structure failed.

The seven-loss P017-P023 cluster is the clearest symptom.

---

## 5. Strategy correction: Scale Alignment

A good location is not merely a place with a close stop.

A high-quality journey entry requires:

```text
nearby local falsification
+
that local failure carries meaningful information about the larger thesis
+
large room if the larger thesis works
```

If a 2-3 point M5 anchor can fail as routine noise while the H1/H4 opportunity is still completely intact, the trade is not truly scale-aligned.

Do not repair this by widening the stop after entry.
The strategy must wait until larger context and local execution geometry overlap better.

---

## 6. Strategy correction: separate structure authority

Not every memory deserves equal exit authority.

Use role hierarchy:

```text
Execution anchor
Child origin
Child transit memory
Parent failure area
Parent major arrival
```

A child transit memory can produce reaction and even temporary child damage without ending the parent journey.

This is the central correction to the completed February behavior.

---

## 7. Strategy correction: freeze Intended Journey Scale

Before entry state whether the trade is primarily:

```text
LOCAL BRIDGE
or
PARENT-JOURNEY PARTICIPATION
```

The label does not predict outcome.
It determines what scale of evidence should govern lifecycle decisions.

A trade entered for parent-journey participation must not silently become a nearest-memory scalp after entry.

A local bridge trade can still be valid, but its small capture must not be mistaken for successful trend participation.

---

## 8. P003-P005: repeated child reset inside one larger process

The local invalidations were legitimate as local trade failures.
The larger mistake was repeatedly acting as if each local reaction created a sufficiently new market thesis.

The market around the 2813-2830 region was still resolving acceptance while the larger upward route remained meaningful.

The corrected reasoning is:

```text
child died
-> close child
-> preserve parent state
-> ask what genuinely new market information exists
-> do not re-enter merely because another micro reaction appeared
```

P006 later demonstrated what a more meaningful renewed opportunity looked like.

---

## 9. P010 and P016: child anchors were promoted too high

Both trades benefited from broader continuation context.
During management, newer local anchors acquired full-exit authority.

The postmortem question is NOT whether later price proved the exits wrong.
It is:

> Did the loss of the newest child anchor actually invalidate the same scale of thesis that justified the original journey trade?

In several cases the answer was not clearly yes.

The strategy must distinguish child damage from campaign invalidation.

---

## 10. P011: blocks the naive `hold longer` solution

P011 had large favorable excursion followed by abrupt deterioration.

This means the correction cannot be:

```text
ignore local structure
hold everything until the parent is obviously dead
```

Large-scale management still needs timely recognition of genuine failure.
The open research problem is which deterioration has strategic authority, not whether to stop managing.

---

## 11. P013/P014/P023: OPEN ROUTE without maturity context

These trades show that:

```text
known upper memory consumed
+
small pullback anchor
!=
automatically good continuation location
```

The missing contextual variable is `Journey Maturity`.

Before an OPEN ROUTE entry ask:

- Is the market near a fresh launch?
- Has meaningful new business formed after consumption?
- Is the journey established but not obviously late?
- Is the trade being taken at late extension because a tiny pullback makes the stop look attractive?

Do not turn these questions into fixed distance thresholds yet.

---

## 12. P017-P020: broad-auction interior churn

The market repeatedly translated and repaired both directions.
V9 treated each local failed repair as a new directional opportunity.

The higher-scale correction is:

> First determine whether value is genuinely migrating or whether both routes remain capable of repeated repair inside one broad auction.

Interior micro failures inside a broad unresolved auction should have less strategic authority than edge failure or genuine value relocation.

This does NOT mean `unresolved parent => no trade`.
It means a trade needs better location and scale meaning than an interior micro pattern.

---

## 13. P021/P022: execution stop vs holding thesis mismatch

The larger repair context was traded using very small anchors.
Those anchors could fail without clearly killing the broader repair.

The correct lesson is not to use a wider stop after entry.

It is:

> If ordinary expected noise can hit the local invalidation while the larger thesis remains alive, wait for a better entry where the local structure matters more.

This is the practical meaning of Scale Alignment.

---

## 14. P024: useful contrast, not final answer

P024 formed after new business persisted for hours and then departed again.
That makes it a useful contrast to fast reaction-based losers.

The positive hypothesis is:

```text
new business actually established
+
subsequent departure
+
meaningful return location
```

may be more important than simply seeing one reaction and one bounce.

But P024 still resolved at a local destination and therefore does not prove that larger-journey capture is solved.

---

## 15. February 25-28: Parent Journey did not sufficiently change ambition

The lower route repeatedly migrated value lower, repaired, and failed again.
V9 correctly refused to chase already-extended lows.

The remaining problem was that after refusing to chase, the strategy often behaved as if the campaign opportunity was over.

Required correction:

```text
missed leg
!=
missed campaign
```

If the parent route remains coherent, wait for the next meaningful repair and seek a scale-aligned entry.
Do not chase; do not reset ambition to zero merely because the nearest low was reached.

---

## 16. Why many R outcomes remained small

Two distinct reasons:

### A. Entry asymmetry was often only moderate

Some trades used 4-8 point structural risk against only modest nearby room.
A close-ish stop is not enough.

### B. Position lifecycle often remained child-scale

Even when a larger Parent Journey existed, nearby child memories frequently ended the entire position.

Therefore:

```text
small R winner
```

can be evidence of either:

- mediocre entry asymmetry; or
- good entry but poor larger-journey participation.

Future journals must separate those two.

---

## 17. New measurement separation

Every future trade should report separately:

```text
Initial risk points
Initial-risk R
Captured points
Captured S
Trade MFE points / R
```

After the parent campaign is historically resolved, add shadow diagnostics:

```text
Parent journey span / MFE
Journey capture ratio
```

A +4R trade that captured 8 points of a much larger journey is a good local trade but poor journey capture.
A 30-point capture with a 10-point risk may be meaningful movement capture but weak entry asymmetry.
The target architecture is good local risk plus meaningful market-scale participation.

---

## 18. What changes next

Change the questions, not numeric thresholds.

Before entry:

1. What is the Parent Journey working belief?
2. Is the market genuinely migrating or still in the same broad auction?
3. Is this new information or another reaction inside the same auction?
4. What journey scale am I trying to participate in?
5. Is the local execution anchor actually meaningful at that larger scale?
6. If right, is there materially larger room than the initial risk without inventing an arbitrary TP?
7. Is this OPEN ROUTE fresh/established or late extension?

During management:

1. Which scale of structure was damaged?
2. Is this child pullback or campaign deterioration?
3. Has value genuinely relocated against the thesis?
4. Am I giving a micro anchor full-position authority without justification?
5. Am I ignoring a genuine shock merely because I want a larger winner?

After exit:

1. Was the child invalidated correctly?
2. Did the parent survive?
3. Is the next opportunity genuinely new?
4. Did this trade capture a local bridge or meaningfully participate in the parent journey?

---

## 19. What does NOT change

Retain:

- no direction oracle;
- no hindsight rescue;
- child loss does not automatically kill parent;
- parent does not authorize a child by itself;
- nearby meaningful falsification remains valuable;
- no forced trade frequency;
- no exact-top prediction;
- no fixed ATR-generated structure;
- no threshold fitted from one month;
- GOLD# 2021 remains locked.

---

## 20. Final February conclusion

February showed that V9 successfully moved beyond the January problem of almost never participating.

But it also showed the next failure mode:

> V9 entered and exited with too much authority assigned to nearby structure, so ordinary local oscillation could produce repeated losses and larger campaigns could still be reduced to small bridge captures.

The next V9 generation of research should therefore behave as:

```text
ENTER LOCALLY
THINK AT THE JOURNEY SCALE
MANAGE STRUCTURE BY ITS ACTUAL AUTHORITY
EXIT WHEN THE INTENDED THESIS IS GENUINELY DAMAGED
REMAIN AVAILABLE WHILE THE PARENT CAMPAIGN SURVIVES
```

This is a discretionary research revision, not a formalized strategy rule set.
