# V13 Baseline 0 — extended actual-tick diagnostic

Date analyzed: `2026-09-26`
Status: `DIAGNOSTIC / STRUCTURAL PARITY EVIDENCE / NOT OFFICIAL EXACT-WINDOW ECONOMICS`

## Source

User-provided MT5 Strategy Tester workbook:

`ReportTester-318585216.xlsx`

SHA-256:

`deaf28634e97ebf1cf9805ecb0504d5b7ff1a49e8725439e0c4f752e20926cc3`

## Tester header

```text
terminal: XMGlobal-MT5 7
build: 6230
EA: V13HAOnlyMax10EA
symbol: GOLD#
period: H4
report test range: 2024-01-01 .. 2026-09-26
history quality: 100% real ticks
deposit: 10,000 USD
leverage: 1:500
InpMagicNumber: 1300260926
InpLotPerChild: 0.01
InpDeviationPoints: 30
InpVerbose: true
```

## Whole-report summary

These metrics describe the **extended** report and must not be used as the
canonical V13 Baseline-0 comparator:

```text
net profit: +7,180.62 USD
gross profit: +49,992.07 USD
gross loss: -42,811.45 USD
profit factor: 1.167727
balance DD absolute: 1,485.81 USD
balance DD maximal: 3,701.92 USD / 19.12%
equity DD absolute: 1,494.41 USD
equity DD maximal: 5,406.66 USD / 25.82%
equity DD relative: 29.26% / 4,622.08 USD
positions/trades: 3,977
deals: 7,954
winning positions: 1,446 / 36.36%
losing positions: 2,531 / 63.64%
LONG positions: 2,159 / 42.38% won
SHORT positions: 1,818 / 29.21% won
largest winning position: +699.75 USD
largest losing position: -226.32 USD
average winning position: +34.572663 USD
average losing position: -16.914836 USD
```

## Canonical-prefix structural check

Order/deal comments encode entries as:

`V13|Jxxxxxx|Cxx|L/S`

Deduplicating those entry identities before `2026-08-29 00:00` gives:

```text
unique Child entries: 3,859
Journey IDs: J000001 .. J000966
J000001 .. J000965 Child count: 3,858
J000966 Child count at cutoff: 1
```

Closed-Journey child-count distribution for J000001..J000965:

```text
1 Child: 187 Journeys
2: 202
3: 139
4: 113
5: 79
6: 59
7: 40
8: 33
9: 25
10: 88
```

This exactly matches the deterministic standard-H4 sanity reconstruction for the
965 closed Journeys and 3,858 closed Children. J000966 begins with a SHORT Child
at `2026-08-28 20:00` and remains open at the supplied source cutoff.

The repaired EA therefore passes the most important structural parity check for
using the tester history as an HA research ledger.

## Execution observation

The report includes entries just after broker session reopening, for example
`2024-01-03 01:02:01`, rather than permanently halting at the midnight boundary.
This is consistent with the execution-recovery repair doing its intended job.

## Why this is not the official baseline receipt

The frozen protocol currently requires:

```text
To: 2026-08-28
Leverage: 1:100
```

This report instead uses:

```text
To: 2026-09-26
Leverage: 1:500
```

Therefore the whole-report money statistics are diagnostic only. An exact-window
rerun is still required before a future strategy variant is promoted on economic
performance.

## Research interpretation

Do not overfit this primitive strategy.

The useful baseline observation is that HA persistence and HA lag are visible in
the Journey structure:

- strong same-color runs naturally build exposure into sustained moves;
- HA requires enough opposite raw movement before color changes;
- later same-color Children can therefore enter nearer the mature end of a move
  and experience more giveback;
- this is evidence about the representation, not immediate authority for a
  smaller Child cap or a SHORT ban.

The next task is HA-0 measurement: quantify the morphology and lifecycle of the
same standard HA without altering trades.
