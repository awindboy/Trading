# V13 SA-1 Actual-Tick + Journal Receipt — 2026-09-29

Status: `ACTUAL-TICK ECONOMICS CONFIRMED / ADMISSION-CHILD PARITY CONFIRMED / FULL TIMESTAMP EVENT CROSS-JOIN NOT RE-RUN HERE`

GitHub base checked: `1555d2b06b4dabdbadf14366c26e4f2177506463`.
Canonical cutoff: `2026-08-28 20:00:00`.
Tester source: `evidence/ReportTester-318585216.xlsx`.
Journal source: `evidence/20260928.log` (UTF-16 LE).

## Canonical actual-tick economics

```text
Children       1,783
Wins             894
Losses           888
Flats              1
Non-flat WR     50.17%
Net          +$2,791.87
PF               1.215
Max DD         $971.77
Max loss streak     10
Avg winner      +$17.67
Avg loser       -$14.65
Payoff             1.21
```

### Year

```text
2024  680 trades  318W / 361L / 1F   -$37.54    PF 0.986
2025  676 trades  362W / 314L         +$1,521.53 PF 1.362
2026  427 trades  214W / 213L         +$1,307.88 PF 1.215
```

## Child-role decomposition

```text
Child1
965 trades / 330W / 635L
Net +$1,862.51
PF 1.177
Avg W +$37.52 / Avg L -$16.57 / payoff 2.26

SA-1 Add-ons
818 trades / 564W / 253L / 1 flat
Net +$929.36
PF 1.374
Avg W +$6.06 / Avg L -$9.83 / payoff 0.62
```

This decomposition motivates the new research: SA-1 add-ons are frequently right but enter late enough that payoff remains poor.

## Journal event counts

Canonical counts through cutoff:

```text
ADMISSION           3,142
  pass                818
  reject            2,324
ENTRY               1,784   # includes the next boundary/opening state around cutoff; economic completed ledger is 1,783
PROOF                 561
LOCK_HIT              556
PROOF_TIMEOUT_DUE     257
CHILD_EXIT            794
JOURNEY_START         966
JOURNEY_END           965
READY                    1
RETRY                5,944
HALT                     0
```

Full tester run through late September:

```text
ADMISSION 3,232 / pass 840 / reject 2,392
ENTRY 1,836
PROOF 578
LOCK_HIT 573
PROOF_TIMEOUT_DUE 262
JOURNEY_START 996 / JOURNEY_END 995
HALT 0
```

The exact SA-1 selected Child identities previously matched the causal replay 1,783/1,783 by `(Journey, Child ordinal, side)`. This package preserves that result. It does **not** claim a newly executed proof/lock timestamp-by-timestamp Python cross-join; the Journal counts are included so that audit can be repeated.
