# V13 research state

Last synchronized: `2026-09-28`
Status: `BASELINE 0 FROZEN / HA-9 BREAKTHROUGH CANDIDATE / ACTUAL-TICK VALIDATION PENDING`
Market: `GOLD# ONLY`
Base GitHub `main`: `29e0073e57553d8fe1fd14b843daf09164a7a248`

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
