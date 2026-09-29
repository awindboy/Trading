# V13 LTF route q75/q50 actual-tick replay receipt

Date: `2026-09-29`
Status: `RECONSTRUCTION A / ACTUAL-TICK POLICY PARITY PASS / CONSUMED DEVELOPMENT / NOT PROMOTED`

## Scope and identity

The interrupted research session did not save its final q50 event ledger or
fitted fold artifacts. The local result below is therefore a clean
**Reconstruction A**, not a claim that the old session policy was recovered
bit-for-bit.

The reconstruction kept the declared architecture and ranks:

- unchanged Baseline-0 Child #1;
- causal M30/H1 destination topology;
- strict-prior OOF hurdle-EV q75 admission;
- strict-prior OOF q50 first-repair permission;
- fixed `0.01` lot and no q65/q70, sizing, year or side rescue.

It independently recovered the same population sizes: 965 Child-#1 Journeys,
512 LTF Children and 1,477 combined trades.

## Frozen artifacts

```text
combined action ledger rows       2,954
combined events                   1,477
combined ledger SHA-256           dc09bbef5602622089e80a3ee12dd3257430fdeeb3042ad57571211c20f2f5be
final tester Journal SHA-256       09afca05d9239a7121190de436d04f705b29b5d60aaf548149079bcd92459cac
EA source SHA-256                  94156bdd0221de876733f45110221d901b21ab02d5e05477bf78d421480a546f
EA EX5 SHA-256                     1d9c7e00eb2a337c35e22b15bc538c3cd403be08e8ddafc9e1bc59f03d612710
MetaEditor result                  0 errors / 0 warnings
tester model                       Every tick based on real ticks
tester period                      2024-01-01 .. 2026-08-29
real ticks processed               183,208,623
bars generated                     940,833
```

The Journal is retained locally outside Git because it is about 20 MB. The
repository stores the frozen ledger, its hashes, all normalized
`V13Q75_EVENT|` marker rows, the parsed per-event execution ledger and the
parity JSON.

## Event parity

```text
ENTRY successes                    1,477
EXIT successes                     1,477
ordered ledger/action parity       PASS (2,954 / 2,954)
ENTRY_EXPIRED                      0
EXIT_NO_POSITION                   0
HALT                               0
REPLAY_COMPLETE                    1
```

Market closure generated 16,565 transient `10018` attempts across 50 policy
rows. Every affected row later completed; unresolved failed rows were zero.
This proves the replay EA does not stop at the first closed-market failure. It
also exposes a production concern: session-aware scheduling/backoff should
replace one-second tick-by-tick retry before any live EA upgrade.

## Actual-tick economics

| Metric | Combined | Child #1 | LTF q75/q50 |
| --- | ---: | ---: | ---: |
| Trades | 1,477 | 965 | 512 |
| Wins / losses / flats | 554 / 922 / 1 | 328 / 636 / 1 | 226 / 286 / 0 |
| Non-flat win rate | 37.53% | 34.02% | 44.14% |
| Net | **+$4,461.37** | +$1,863.72 | **+$2,597.65** |
| PF | **1.301** | 1.177 | **1.607** |
| Average win / loss | +$34.77 / -$16.05 | +$37.75 / -$16.54 | +$30.44 / -$14.97 |
| Payoff | 2.17 | 2.28 | 2.03 |
| Expectancy | +$3.02 | +$1.93 | +$5.07 |
| Realized exit-order DD | $1,018.77 | $762.49 | $494.85 |
| Maximum loss streak | 15 | 11 | 10 |

Exact-tick equity peak-to-trough drawdown was `$1,787.36`; maximum concurrent
positions were `8`. Final balance and equity were both `$14,461.37`.
The combined break-even win rate implied by average win/loss was `31.59%`, below
the realized `37.53%`.

Year slices:

| Exit year | Trades | W / L / flat | Net | PF | Realized DD | Streak |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2024 | 605 | 208 / 397 / 0 | +$208.73 | 1.061 | $552.23 | 14 |
| 2025 | 527 | 220 / 306 / 1 | +$2,489.95 | 1.532 | $368.77 | 15 |
| 2026 | 345 | 126 / 219 / 0 | +$1,762.69 | 1.263 | $1,018.77 | 13 |

## Ordinary blocks and tail dependence

Chronological non-overlapping blocks:

| Block | Positive share | Median P/L |
| --- | ---: | ---: |
| 10 trades | 56.46% | +$13.54 |
| 25 trades | 57.63% | +$37.95 |
| 50 trades | 62.07% | +$87.48 |
| 100 trades | 64.29% | +$289.28 |

No complete 10/25/50/100-trade block combined a greater-than-50% win rate with
negative P/L.

After removing the most profitable H4 runs from both lanes together:

```text
top 1 removed     +$3,512.00
top 3 removed     +$2,395.99
top 5 removed     +$1,649.60
top 10 removed      +$211.69
top 20 removed    -$2,006.70
```

The H4-run mapping is exact for all 512 LTF events (`h4_run_id - Child-#1
journey = 716`).

## Attribution against idealized Reconstruction A

```text
idealized combined proxy          +$4,530.11
actual-tick combined              +$4,461.37
execution difference                 -$68.74

idealized LTF lane                +$2,667.60
actual-tick LTF lane              +$2,597.65
execution difference                 -$69.95
```

The close match supports execution parity for Reconstruction A. It does not
turn this consumed period into independent validation.

## Decision against the active objective

SA-1 remains the ordinary-quality execution reference: 1,783 trades, 894 wins,
888 losses, 50.17% non-flat win rate, `+$2,791.87`, PF `1.215`, realized DD
`$971.77` and maximum loss streak 10.

Reconstruction A produces more dollars and much better payoff with 306 fewer
trades, but it has **34 more losses, 340 fewer wins, a 12.64-point lower win
rate, a five-trade longer loss streak, slightly worse realized DD and materially
larger exact-tick equity DD/exposure**. Its positive net is driven by payoff,
not by solving V13's primary repeated-loss problem.

Therefore:

- policy parity and positive execution economics are accepted;
- the LTF route remains valuable structural evidence and a shadow candidate;
- it does **not** replace SA-1 as the ordinary-equity reference;
- it is **not** promoted to an embedded or production EA on this consumed
  sample;
- q65/q70, fitted thresholds, side/year exceptions and size rescue remain
  prohibited.

Any next economic claim requires a predeclared forward shadow period after the
consumed cutoff or a genuinely new frozen mechanism, not more tuning of this
ledger.
