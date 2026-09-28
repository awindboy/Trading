# V13 HA-9 counterfactual exit matrix receipt

Last synchronized: `2026-09-28`
Status: `CONSUMED DEVELOPMENT + POST-CUTOFF QUASI-HOLDOUT / REJECTED / NOT ACTION AUTHORITY`

## 1. Question

With actual MT5 entries fixed, can a natural H1, FAST-H4 or standard-H4 exit
horizon improve HA-9's ordinary equity quality? In particular, can an
unproven add-on receive one additional completed H1 based on its timeout state
instead of being closed immediately?

No per-trade best exit is selected. Every matrix column is one predeclared
policy applied to the whole named population.

## 2. Execution convention

- completed standard H1 opposite color: exit at the next available H1 open;
- completed FAST-R25 H4 opposite color: exit at the next available H4 open;
- standard-H4: actual MT5 Journey close;
- one-H1 timeout extension: after the actual timeout, hold through exactly one
  additional completed H1 and exit at the following available H1 open;
- LONG exits use raw Bid open;
- SHORT exits use raw Bid open plus exported spread times `0.01` as an Ask
  proxy.

The spread proxy is not official Strategy Tester economics. Actual entries and
the actual Child/Journey identities remain fixed.

## 3. Time bucket versus actual event population

The 734 canonical 4–8h losing add-ons are only a duration proxy. The event
ledger contains:

```text
1,355 PROOF_TIMEOUT add-ons
  986 losses
  368 wins
    1 flat
```

Of these, 634 coincide with the standard-H4 Journey close, so no extension is
available. The economically actionable timeout population is 721 add-ons.
Research must use the event reason and action availability, not only an elapsed
time bucket.

## 4. Global horizon replacement fails the active objective

Add-on-only results:

| Exit policy | Wins | Losses | WR | Net USD | Realized DD | Max loss streak |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Actual HA-9 | 1,787 | **1,100** | **61.90%** | +1,204.47 | **693.33** | **9** |
| Opposite H1 HA | 1,093 | 1,799 | 37.79% | +3,118.61 | 525.45 | 13 |
| Opposite FAST-H4 | 1,121 | 1,772 | 38.75% | +10,074.87 | 2,151.29 | 22 |
| Opposite STD-H4 | 1,078 | 1,814 | 37.28% | +5,635.90 | 3,353.52 | 32 |

FAST-H4 and standard-H4 create more net by restoring right-tail exposure, but
they also add roughly 670–714 losing add-ons, lengthen loss streaks and worsen
ordinary equity quality. They are not replacements for HA-9 under the active
evaluation doctrine. Opposite H1 reduces drawdown but still creates 699 more
losses and lowers win rate by 24 points.

This also shows why a large counterfactual net result cannot by itself identify
a runner policy.

## 5. Consumed-sample timeout extension looked promising

On the canonical 3,858-Child consumed period:

| Combined policy | Wins | Losses | WR | Net USD | PF | DD | Max streak |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Actual HA-9 | 2,118 | 1,734 | 54.98% | +3,067.50 | 1.135 | 1,313.10 | 14 |
| Extend all actionable timeouts | 2,158 | 1,695 | 56.01% | +3,513.96 | 1.151 | 1,357.10 | 13 |
| Extend persistent/mixed only | 2,166 | **1,686** | **56.23%** | +3,287.74 | 1.144 | **1,295.02** | **13** |

The persistent-opposition/unrepaired-mixed selector reduced losses by 48 and
improved net in 2024, 2025 and 2026. This was the strongest consumed-sample
combination and contradicted the intuitive `repair deserves more time` story:

- repaired extension increased loss count by five;
- no-opposition extension increased loss count by four;
- persistent opposition and unrepaired mixed supplied the loss-count reduction.

Because this state selection was inspected on consumed data, it was frozen
before examining post-cutoff Child-level states and sent to a quasi-holdout.

## 6. Post-cutoff quasi-holdout rejects the mechanism

The report and raw H1 overlap after the canonical cutoff from
`2026-08-31 01:02` through the last usable counterfactual exit on
`2026-09-22 21:00`.

```text
99 completed Children
74 add-ons
18 actionable timeouts with one-H1 data
11 persistent-opposition/unrepaired-mixed selections
```

| Combined policy | Wins | Losses | Net USD | PF | Realized DD | Max streak |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Actual | 51 | 48 | +7.13 | 1.008 | 477.37 | 8 |
| Extend all actionable | 52 | 47 | **-98.13** | 0.896 | **542.63** | 8 |
| Extend persistent/mixed | 51 | 48 | **-70.59** | 0.924 | **525.34** | 8 |

Within the 18 actionable timeout trades themselves, actual timeout produced
five wins, 13 losses and `-$61.25`. One-H1 extension produced six wins, 12
losses and `-$166.51`. One extra winning classification cost `$105.26` and
nearly doubled the population drawdown.

The post-cutoff period is small and not pristine because full-report aggregate
outcomes were already known. Nevertheless, the adverse effect is large and in
the wrong direction on net, PF and drawdown. It is sufficient to reject this
mechanism rather than rescue it with another state exception.

## 7. Decision

Rejected:

- global H1, FAST-H4 or standard-H4 replacement exits;
- blanket one-H1 timeout extension;
- one-H1 extension selected by repaired state;
- one-H1 extension selected by persistent-opposition/unrepaired-mixed state.

HA-9's immediate timeout remains unchanged. The causal H1 states are still
descriptive, but they did not support a stable extension action.

The next work should not optimize the extension length. It should move to the
next distinct mechanisms in the backlog:

1. runner identification that preserves quick harvesting unless continuation
   is independently proven;
2. information-based re-arm after a failed Child;
3. separation of an existing proven runner from permission to add another late
   tactical Child.

## 8. Reproduction artifacts

- `research/v13/ha9_counterfactual_exit_matrix.py`
- `output/v13_ha9_counterfactual_exit_matrix_20260928/summary.json`
- `research/v13/ha9_timeout_extension_holdout.py`
- `output/v13_ha9_timeout_extension_holdout_20260928/summary.json`
