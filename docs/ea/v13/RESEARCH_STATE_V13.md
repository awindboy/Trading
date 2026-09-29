# V13 research state

Last synchronized: `2026-09-29`
Status: `BASELINE 0 FROZEN / LTF ROUTE RECONSTRUCTION A ACTUAL-TICK VERIFIED / NOT PROMOTED`
Market: `GOLD# ONLY`
Base GitHub `main`: `1555d2b06b4dabdbadf14366c26e4f2177506463`

## 0. Current state — 2026-09-29 supersession

Sections 1–13 below remain the historical HA-only/HA-9 research record. The
active branch now replaces H4 add-ons with M30/M15 pullback Children and models
delivery of a causal M30/H1 strategic destination.

Current architecture:

```text
unchanged Baseline-0 Child #1
+ strict-prior OOF q75 hurdle-EV LTF admission
+ first-destination delivery as runtime proof
+ strict-prior OOF q50 first-correction repair permission
```

SA-1 remains the actual-tick ordinary-quality reference (`1,783`,
`+$2,791.87`, PF `1.215`, DD `$971.77`, WR `50.17%`, streak 10).

The interrupted LTF session result remains unrecoverable bit-for-bit because
its exact q50 event ledger was not saved. A definition-faithful Reconstruction
A recovered the same 512 LTF / 1,477 combined population and has now passed
2,954/2,954 ordered actual-tick policy parity:

```text
net / PF                    +$4,461.37 / 1.301
wins / losses / flats      554 / 922 / 1
non-flat WR                37.53%
realized / equity DD       $1,018.77 / $1,787.36
max loss streak / exposure 15 / 8 positions
```

It is not promoted: against SA-1, improved payoff and net come with more losses,
much lower win rate, longer streaks and greater exposure. The current boundary
is forward shadow or a genuinely new predeclared mechanism, not threshold
rescue or embedded production implementation. See the 2026-09-29 actual-tick
replay receipt.

## 1. Frozen comparator

Baseline 0 remains standard completed-H4 HA, one Child per same-color completed
H4 up to 10 successful entries, opposite H4 close-all/reverse, fixed unit size.

Canonical idealized parity:

```text
closed Journeys 965
closed Children 3,858
net +8,147.11
Child PF 1.19995
wins/losses/flats 1,430 / 2,427 / 1
```

## 2. Consumed historical evidence

HA-0..HA-6 established HA morphology, H1 path, causal raw swing, HASTOC, MA,
ATR, ADX/DMI and tick-activity relationships. HA-7's first H1/volume Child veto
was rejected. HA-8A modestly ranked three-H4 HA flips but did not isolate bad
economic Children. X1 delayed ECB EUR/USD and X2 same-broker EURUSD# H4 did not
improve Journey-birth loss selection.

These results remain valid historical evidence. They do not authorize those
filters or models.

## 3. Objective update

The active objective is now ordinary trade quality:

- fewer losing Children;
- higher non-flat win rate;
- shorter loss streaks;
- shallower chronological drawdown;
- more positive typical trade blocks;
- less dependence on a few giant Journeys.

Large continuation winner preservation is **not** a hard requirement. Tail cost
must be disclosed but can be accepted when ordinary trade quality materially
improves. See `V13_OBJECTIVE_AND_EVALUATION_UPDATE_20260928.md`.

## 4. HA-8B/8C follow-on diagnosis

Economic retargeting showed an important distinction:

- whole-Journey loss prediction at Child #1 remained weak;
- direct add-on Child terminal-loss prediction contained modest information,
  especially from side + ordered H1 state, but not enough for the desired large
  loss-frequency improvement;
- larger tabular feature stacks, lower-TF feature expansion, payoff regression,
  simple sequence history and more complex nonlinear models did not create the
  needed step change.

This pushed research away from prediction/filtering and toward runtime
confirmation/management.

## 5. HA-9 mechanism

For Child #2..#10 only:

1. enter at Baseline-0 timing after a same-color completed H4;
2. use that signal H4 raw favorable extreme as a proof level;
3. allow exactly the following H4 to prove continuation;
4. if proven, protect at `max(entry, signal high)` LONG or
   `min(entry, signal low)` SHORT;
5. the lock is active only after the proof observation;
6. if never proven by the next H4 boundary, close that add-on;
7. keep Journey/Child numbering and Child #1 unchanged.

## 6. HA-9 causal audit result

| Metric | Baseline | HA-9 |
| --- | ---: | ---: |
| Losing Children | 2,427 | **1,685** |
| Winning Children | 1,430 | **2,151** |
| Flats | 1 | 22 |
| Non-flat win rate | 37.08% | **56.07%** |
| Net points | +8,147.11 | +3,946.06 |
| PF | 1.19995 | 1.17634 |
| Trade-sequence max DD | 3,756.99 | **1,283.65** |
| Max consecutive losses | 25 | **14** |

Losses fall by 742 (`30.6%`). The candidate remains positive in 2024, 2025 and
2026 in the idealized reconstruction.

Typical block quality also moves upward:

```text
10-trade positive share: 40.0% -> 50.65%
25-trade positive share: 47.40% -> 57.79%; median -14.86 -> +17.18
50-trade positive share: 51.95% -> 61.04%; median +5.96 -> +18.65
100-trade positive share: 55.26% -> 71.05%
```

Removing the top 10 profitable Journeys leaves Baseline `-5,785.30` versus HA-9
`+74.26`, so HA-9 is much less dependent on extreme winners even though its
untrimmed net is lower.

## 7. Why timeout is retained

Breakout-lock alone produced 55.10% non-flat win rate and +4,250.83 points, but
2024 remained `-366.95` and trade-sequence DD was 2,056.69. Adding the one-H4
proof timeout reduced DD to 1,283.65 and moved 2024 to +37.15. Timeout is thus a
quality/stability component, not a total-net optimizer.

## 8. Current boundary

HA-9 is a **breakthrough research candidate**, not production authority.
The next evidence is actual-tick MQL5 execution parity. The current environment
cannot compile MQL5, so source-level EA delivery does not count as compile proof.

Do not tune HA-9 parameters before tester parity. If actual-tick results diverge,
first attribute the difference to spread, Bid/Ask proof/lock semantics, tick
ordering, slippage or execution recovery.

## 9. Actual-tick trade-mode diagnosis

An extended MT5 report was reconstructed into 3,977 completed Children. The
canonical cutoff contains 3,858 actual Children and joins one-to-one to the
ideal HA-9 ledger. This is preliminary economic evidence, not event-reason
parity.

The actual ledger confirms two different roles:

```text
Child #1: 965 trades, 34.30% non-flat WR, +$1,863.03, median 13.04h
Add-ons: 2,893 trades, 61.90% non-flat WR, +$1,204.47, median 2.96h
```

Among add-ons, 734 canonical losses occur in the 4–8h timeout band and 733 had
no proof. H1 repair raises later recovery probability, while persistent H1
opposition, H4 delta contraction, opposite-wick state and FAST-H4 opposition
identify more terminal failures. However, only 9.54% of the whole loss pile is
positive if held to the standard-H4 Journey exit, so removing timeout broadly is
rejected.

For 1,460 sub-4h winning add-ons, the standard-H4 exit beats the actual exit in
only 38.77%. Time-to-proof alone does not identify a runner. The next research
step is therefore a predeclared H1/FAST-H4/standard-H4 counterfactual exit matrix,
not feature stacking or simple longer holding.

See:

- `V13_HA9_TRADE_MODE_RESEARCH_BACKLOG_20260928.md`
- `results/V13_HA9_TRADE_MODE_PHASE1_RECEIPT_20260928.md`

## 10. Counterfactual exit result

Global H1, FAST-H4 and standard-H4 add-on exits all increased losing-Child
frequency sharply. FAST-H4 produced a much larger right tail, but add-on losses
rose from 1,100 to 1,772, realized DD from `$693.33` to `$2,151.29`, and the
maximum loss streak from 9 to 22. This violates the active objective.

A natural one-H1 extension after actionable timeout looked favorable on the
consumed period. A post-hoc persistent-opposition/unrepaired-mixed selector
reduced combined losses by 48 and improved consumed-period net and DD. It then
failed the short post-cutoff quasi-holdout: among 99 Children it did not reduce
loss count, changed net from `+$7.13` to `-$70.59`, and increased DD from
`$477.37` to `$525.34`.

The timeout extension is rejected without parameter rescue. Immediate HA-9
timeout remains unchanged. See
`results/V13_HA9_COUNTERFACTUAL_EXIT_MATRIX_RECEIPT_20260928.md`.

## 11. Information-based re-arm result

Blocking re-entry after one tactical failure until a new extreme, raw-swing
close, H1 no-opposition state or H4 delta re-expansion removed more winners than
losses in every variant. Requiring two consecutive failures reduced the damage,
but the best consumed-data diagnostic removed 34 winners and 31 losses, slightly
worsened DD, and showed weak year stability.

On the short post-cutoff quasi-holdout it skipped four winners and one loser,
changing `+$7.13` to `-$18.12`. Information-based re-arm is rejected. Do not
replace it with a fitted cooldown. See
`results/V13_HA9_INFORMATION_REARM_RECEIPT_20260928.md`.

## 12. Runner/tactical role result

Converting the first proven add-on to a FAST-H4 runner raised consumed-period
net to `+$5,780.22`, but losses rose by 210, win rate fell to 49.55%, DD rose to
`$1,417.42`, and maximum loss streak rose to 19. This is right-tail restoration,
not ordinary-equity improvement.

Requiring aligned H1 close acceptance reduced runner assignments to 56 and
improved net/DD, but still created ten extra losses. In the short post-cutoff
overlap, two qualifying actual winners became one win and one loss, changing
their `+$15.06` to `-$7.19`.

Suppressing new add-ons while a runner lived removed far more winners than
losses and collapsed win rate. C10 is negative but C4–C9 are not monotonic, so
no late-ordinal veto is authorized. See
`results/V13_HA9_RUNNER_TACTICAL_ROLE_RECEIPT_20260928.md`.

## 13. Trade-mode program boundary

The original proposal's actionable priority chain is complete through timeout
decomposition, exit horizons, state timeout, re-arm and runner/tactical roles.
The market/pullback/breakout selector is not executed because no stable holding
mode exists to select; sizing is not authorized for the same reason. Structural
stop variants cannot address the dominant no-proof timeout population and await
event parity before lower-leverage post-proof mechanics are expanded.

See `V13_HA9_TRADE_MODE_COVERAGE_20260928.md` for the 23-item coverage map.
