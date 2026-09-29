# V13 Research Chronicle — SA-1 Actual Tick to LTF Better-Price Child — 2026-09-29

Status: `HISTORICAL RESEARCH CHRONICLE / CURRENT AUTHORITY UNCHANGED UNTIL GITHUB COMMIT`

This chronology records the major questions tested after the SA-1 research package was produced. It is meant to prevent future sessions from reopening failed branches or mistaking exploratory upper bounds for validated strategy performance.

## 1. SA-1 actual-tick test and Journal

The pushed `V13SA1CleanContinuationEA` was run in MT5 Strategy Tester with `Every tick based on real ticks` and fixed `0.01 lot` semantics. Canonical cutoff economics:

```text
1,783 completed Children
894W / 888L / 1 flat
Net +$2,791.87
PF 1.215
DD $971.77
Max loss streak 10
```

The Child identities matched the causal SA-1 selection by Journey/Child/side. Canonical Journal counts include 818 admitted add-ons, 561 proofs, 556 lock hits and 257 proof timeouts. See the dedicated receipt.

### Key decomposition

```text
Child1
965 trades / 330W / 635L
+$1,862.51 / PF 1.177
Avg W +$37.52 / Avg L -$16.57 / payoff 2.26

SA-1 Add-ons
818 trades / 564W / 253L / 1 flat
+$929.36 / PF 1.374
Avg W +$6.06 / Avg L -$9.83 / payoff 0.62
```

This made the new problem explicit: SA-1 reduced loss frequency but the add-on lane still had poor price/payoff economics.

## 2. Immediate runner probes after SA-1

The first question was whether the current HA-9 proof or early Child ordinal could directly identify a runner.

### First-proof runner diagnostic

On consumed history, holding the first proofed candidate longer initially looked attractive (about 282 cases; 127W/155L, average win about +$36 vs average loss about -$21, net roughly +$1.28k). But the fresh post-cutoff sample immediately weakened: 10 cases, 4W/6L, about -$74.8. This was not promoted.

### C2 hold diagnostic

The first add-on/C2 held to Journey end also looked strong on consumed history (about 382 trades, PF roughly 1.44, net about +$1.80k), but the small new post-cutoff slice was 4W/9L and about -$70.5. Child ordinal was therefore rejected as runner authority.

### Proof breakout re-entry

Entering again at proof with the breakout level as immediate defense failed because almost every proof later revisited the breakout lock. In the explored first-proof set, about 276/282 would have been stopped/revisited. `proof = no-pullback trend` was rejected.

### Wider structural stop after proof

Using the signal-H4 opposite extreme as a wider structural risk bound improved payoff, but year/direction stability was poor; it did not justify a new rule. A much narrower state — proof followed by surviving to the first completed H1 without touching the breakout lock — showed extreme payoff in only about 13 observations and was correctly treated as an anecdotal archetype, not a rule.

## 3. Whole-frame compression experiment: H4/H1 -> H1/M15

A direct scale transfer was tested to see whether the whole V13 mechanism was timeframe-invariant:

```text
main HA: H4 -> H1
internal path: H1 -> M15
proof window: one H4 -> one H1
SA-1 semantics otherwise preserved
```

The shape of the state was surprisingly stable: SA-1 admission rate and proof/no-proof separation remained similar. But economics did not.

Approximate session diagnostic:

```text
H4/H1 SA-1 idealized
1,783 trades
Net +3,423
PF 1.269
DD ~949

H1/M15 transfer
6,822 trades
Net ~+1,602
PF ~1.058
DD ~1,002
loss streak 18
```

2024 became negative and 2025 was near breakeven; top-5 profitable Journeys were enough to push the lower-frame result negative. The full-frame shift was rejected.

### Important interpretation

The **state geometry** looked scale-recurrent, but the **economic excursion** did not. Lower timeframe continuation was often directionally correct but too small. This suggested using M30/M15 as a microscope inside the H4 Parent rather than replacing the H4 Parent.

## 4. Research pivot: raw LTF pullbacks hidden inside same-color H4 HA

The central insight from the user was that HA smoothing deliberately hides raw-candle pullbacks. Therefore the relevant object is not an H4 PHA/NHA ratio; it is the series of raw M30/M15 corrections occurring **while the H4 HA remains the same color**.

New representation:

```text
H4 HA same-color run = Parent / PHA container
M30 raw swing/impulse/correction = location
M15 FVG/OB interaction = reaction context / opportunity clock
```

This also directly addresses the V10 problem of repeatedly adding at new highs after another PHA/H4 extension.

## 5. Raw retracement and POI reaction anatomy

Initial causal episode studies found a monotonic deterioration pattern: as LTF raw pullback depth increased, probability of rebreaking the prior impulse extreme fell. POI touch alone was not helpful because deeper corrections touch more POIs. Reaction conditional on location was more informative.

The session-level object anatomy showed large separation between primary-direction POI rejection and accept-through, especially on M15, but that relationship was not stable enough to become a hard `REJECT-only` strategy rule.

The durable lesson was:

```text
location/depth and POI reaction are separate information axes;
POI existence alone is not an entry signal.
```

## 6. Dynamic prior-survived correction envelope

Instead of fitting 50%, 61.8%, 0.75 ATR, etc., the research introduced a parameter-free relative state:

```text
prior envelope
= deepest correction the current H4 HA run has already survived and re-expanded from

current correction inside envelope
= within demonstrated trend tolerance

current correction breaches envelope
= trend is experiencing a correction deeper than anything previously survived
```

The first version used POI-linked correction episodes and showed strong deterioration when the envelope was breached. Combining breach with POI acceptance was terminal-like, while breach plus rejection could still be repair-like. This became the basis for runner protection.

## 7. New LTF Child action experiments

### Direct POI-rejection entry + H4 flip hold

Trading every rejection directly was negative/weak. The descriptive POI edge did not automatically convert into trading expectancy.

### POI distal Hard SL

A wick-based POI distal stop was too sensitive because valid rejections can first penetrate deeply. A pullback-extreme stop did not solve the problem either. No minimum stop or ATR floor was invented to rescue the result.

### M15 repair/MSS confirmation

Waiting for an opposing M15 swing to be reclaimed improved confirmation but entered too late and damaged R. This recreated the V10 late-entry problem and was rejected.

## 8. First correction-envelope breach as protection exit

Waiting for a full POI accept-through was too late. A simpler event performed better:

```text
enter LTF Child during pullback
-> hold while runner stays within demonstrated correction tolerance
-> first later correction that exceeds prior survived envelope: protect/exit
-> if no breach: fallback opposite H4 HA flip
```

This became the current K0 LTF lane.

2024-2026 standalone LTF lane:

```text
2,039 opportunities
833W / 1,204L / 2 flat
Net +$3,319.42
PF 1.210
DD $1,521.43
Avg W +$23.00 / Avg L -$13.16 / payoff 1.75
```

2022/23 historical stress remained only slightly positive, rather than collapsing.

## 9. ML branch

A 3,672-row chronological LTF event dataset was built with raw and H4-ATR180 normalized features. Prior-year-only outer folds and label-resolution purge were used.

### Successful ML use: state information

Rebreak classification improved consistently from location -> location+reaction -> full path. Full robust-logistic AUC was roughly 0.75-0.78 across 2024-26. Remaining-MFE rank correlation was roughly 0.32-0.36.

### Failed ML use: direct realized money / sizing

Direct P/L prediction was weak. Tail-score 2x/3x sizing did not consistently beat random-upsize controls. Proof-stage ML was essentially random (AUC ~0.45-0.51). The direct V10-style 180-H4 feedback transplant also failed. ML remains instrumentation, not action authority.

## 10. Child-lane replacement

Instead of overlaying LTF Children on top of SA-1 add-ons, the cleaner architecture was tested:

```text
Child1 remains unchanged
SA-1 add-on lane removed
LTF K0 pullback Children replace it
```

2024-2026:

```text
3,004 total trades
Net +$5,181.93
PF 1.197
DD $1,716.49
WR 38.74%
Avg W +$27.12 / Avg L -$14.33 / payoff 1.89
Max loss streak 22
```

All three years were positive. Net/payoff improved materially, but ordinary-equity quality worsened versus SA-1. This is the most important **structural** shadow result, because it directly addresses late H4 add-on entry.

## 11. Staged funding after actual M30 re-expansion proof

A further experiment added risk only after the prior M30 impulse extreme was actually rebroken:

```text
K1: +1 unit after proof
K2: +2 units after proof
```

2024-26 consumed dollars were strong:

```text
K1 replacement: +$8,010.66 / PF 1.235 / DD $2,281.66
K2 replacement: +$10,839.39 / PF 1.256 / DD $2,846.83
```

But the LTF staged lane turned negative in 2022 and 2023, and loss streak/DD rose materially. Therefore the large headline net is an **upper research candidate**, not a strategy promotion.

## 12. Current resolution

### Most stable actual reference

`SA-1 actual tick` remains the ordinary-quality benchmark.

### Most important new structural candidate

`Child1 + LTF K0 replacement` is the branch to refine, because it directly improves entry/payoff without depending on ML or aggressive proof leverage.

### Not authorized

K1/K2 staged funding, current ML sizing, proof ML and feedback upgrades.

### Next mandatory work

Rebuild the prior-survived correction envelope from **every causal raw M30 correction**, not only the POI-linked opportunity ledger. Retest K0 first. Only if K0 remains stable should K1 be revisited, then an actual-tick MQL5 research EA should be built.
# Final continuation after the packaged checkpoint

The original package ended before the next-contract work was completed. The
same research session subsequently produced the following additional findings.
They are preserved here as session evidence; the final per-event policy ledger
and fitted fold artifacts were not saved.

## True all-M30 envelope

- 7,389 corrections, 4,366 survived corrections and 2,435 true envelope
  breaches were reconstructed.
- Removing POI linkage made the lane worse: about `+$1,508`, PF `1.115` versus
  the prior POI-linked `+$3,319`, PF `1.210`.
- POI linkage therefore acted as a useful noise filter; it was not merely a
  cosmetic ICT label.
- A POI limit-entry variant improved median entry by only about `0.01` and
  reduced net; rejected.

Healthy/no-prior-breach cases and already-breached cases had nearly the same
win rate but sharply different payoff:

```text
healthy/no prior   1,628   +$3,728   PF 1.289   WR 41.0%   payoff 1.85
breached             411     -$409   PF 0.862   WR 40.4%   payoff 1.27
```

This showed why win-rate-only filtering had repeatedly failed. Healthy-only
made the 25-trade median positive, but failed 2023, so it was not promoted as a
hard veto.

## Liquidity, normalization and strategic destination

H4 ATR180 medians changed from roughly `12.5` in 2024 to `19.8` in 2025 and
`41.3` in 2026. ATR normalization belongs in coordinates and exposure control;
it did not explain away the 2023 weakness or solve intermittent equity.

Simple nearest-liquidity distance, destination count, H1 label and ladder gaps
were non-monotonic. The useful state was whether the **first causal strategic
destination was actually delivered**:

```text
not delivered   976   -$9,093   PF 0.11   WR 21.7%   payoff 0.41
delivered       811  +$13,026   PF 4.75   WR 64.4%   payoff 2.63
```

Delivery was not converted into a TP: doing so collapsed payoff/net. Adding at
first/second/third delivery worked in 2024-26 but failed 2022/23. Predicting
post-delivery tail length was random (`AUC ~0.47..0.54`).

Predicting first-destination delivery itself was materially more stable. The
combined LTF-state + route-topology model reported AUC `.724/.761/.744/.737`
for 2023/2024/2025/2026. Route information added signal beyond local shape.

## Final q75/q50 state machine

Probability alone was not treated as money. The admission score became:

```text
P(delivery) * remaining ATR room
- P(failure) * historical no-delivery average loss ATR
```

Only strict-prior OOF q75 admitted an LTF Child. q75 did not increase size.
After delivery, the first damaged M30 correction used a separate strict-prior
OOF q50 repair decision: low score exited protectively; high score received one
repair chance. Child #1 stayed unchanged because every attempted Child-1 early
exit or rescue model damaged its high-payoff role.

Session-reported final 2024-26 candidate:

```text
1,477 trades, 548W / 929L, WR 37.10%
+$4,173.10, PF 1.289, payoff 2.19, expectancy +$2.83
realized DD $916.92, max loss streak 13
10-trade median +$9.60; 25-trade median +$34.11
```

The q75 LTF lane alone was reported as 512 trades, `+$2,310.59`, PF `1.59`,
DD `$363.51`, payoff `2.15`. The 2023 historical stress was only mildly
positive and had negative ordinary block medians. Post-hoc q65/q70 variants
were not promoted.

## Interrupted implementation boundary and completion

The research session stopped before saving the final q75/q50 event ledger and
before building its EA. Its reported result still must not be described as
reproduced.

Reconstruction A subsequently rebuilt the declared architecture without
fitting to the old totals, recovered the same 512 LTF / 1,477 combined trade
counts, froze the event ledger and passed 2,954/2,954 ordered actual-tick
Journal parity. Actual ticks produced `+$4,461.37`, PF `1.301`, 554 wins / 922
losses / 1 flat, realized DD `$1,018.77`, exact-tick equity DD `$1,787.36`,
streak 15 and maximum concurrency 8.

That closes the implementation/parity gap but not the strategy objective.
Relative to SA-1, Reconstruction A earns more through payoff while producing
more losses, much lower win rate, longer streaks and greater exposure. It is
therefore retained as positive structural/shadow evidence and not promoted to
an embedded production EA.
