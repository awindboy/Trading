# V12 Phase-1D temporal and economic-event state result

Date: `2026-09-24`

Status: `CONSUMED-DEVELOPMENT MECHANISM RESULT / SHADOW CANDIDATES ONLY / NO TRADE OR SIZING AUTHORITY`

Contract: `v12-phase1d-temporal-event-state-v1`

## Question

Phase 1D tests time as a state coordinate rather than a weekday/hour filter:

1. is recurring broker-clock activity stable across liquidity eras;
2. do scheduled releases add activity beyond their normal clock time;
3. are frozen V10 stopped units or FAST-flip failures concentrated in a joint
   clock, event, and CRT-journey state without deleting the right tail?

## Sources and causal boundary

- `1,669,073` raw GOLD# M1 rows were streamed through
  `2026-09-18 23:57`; the first unrevealed row was `2026-09-21 01:00` and zero
  post-cutoff price rows were parsed.
- MT5 exported `68,377` calendar rows. Eight duplicated value IDs returned
  conflicting timestamps across a query-chunk boundary; all eight IDs were
  excluded rather than resolved by hindsight. The retained snapshot contains
  `68,361` values and `20,271` timed event clusters.
- Calendar time offset `0` ranked first for 15-minute USD-high range lift among
  offsets `-1..+4`, supporting a direct numeric join for this snapshot. This is
  empirical clock parity, not a named London/New York timezone claim.
- Actual and normalized surprise are used only after the release. Historical
  snapshot revisions remain a disclosed limitation.

## Stable broker-clock finding

The user's observation about broker hour `16` is real after normalizing each
day's activity:

| year | hour-16 rank | daily tick-volume share | versus median hour |
|---:|---:|---:|---:|
| 2022 | 1 | 9.55% | 2.30x |
| 2023 | 1 | 10.46% | 2.83x |
| 2024 | 1 | 9.62% | 2.54x |
| 2025 | 1 | 8.16% | 2.00x |
| 2026 through cutoff | 2 | 6.97% | 1.69x |

The peak drifted to hour `17` in 2026, so the useful object is a changing
liquidity clock, not a permanent `16:00` label.

Time alone is not a safe admission rule. Frozen V10 hour-16 Children carried
`111` stopped units (`17.13 / 100 funded`) but also `+203.53R`, PF `2.06`, and
`235.36R` of >=5R right-tail units. Hour `20` had much lower stopped exposure
but only `+2.74R`. Minimizing stops by hour would discard conviction capacity.

## Economic events explain incremental activity

Each release cluster is compared with the prior eight same-weekday,
same-broker-minute windows. Median post-release lift is:

| scope | 15m tick-volume lift | 15m range lift | 60m range lift | 240m range lift |
|---|---:|---:|---:|---:|
| any high | 1.09x | 1.10x | 1.07x | 1.03x |
| USD high | 1.11x | 1.15x | 1.10x | 1.03x |
| USD moderate/high | 1.07x | 1.06x | 1.04x | 1.01x |

Events therefore add a short-lived activity dimension beyond clock time. They
do not provide direction and their median incremental effect mostly decays
within four hours.

## Frozen V10 Child result

The unchanged comparator remains `1,649` Children, `3,881` funded units,
`486` stopped units, `+741.01R`, PF `1.68`, and `1,011.41R` of >=5R right-tail
units.

The broad scheduled-event result is not a universal veto:

- USD-high `15–30` minutes after release had high stopped exposure but still
  earned `+72.85R` and retained `78.10R` of right tail.
- hour `16` had high stopped exposure but strong net R and right tail.
- large realized surprise increased stopped exposure but all three surprise
  bins retained positive V10 R.

One predeclared grid cell deserves future shadow observation:

- all Children `30–60` minutes before a USD moderate/high event: `86`
  Children, `206` units, `40` stopped units (`19.42 / 100`), `-33.63R`, PF
  `0.51`, and only `5.78R` of right tail;
- after conditioning on broker hour `20` and an aligned active CRT journey:
  `35` Children, `93` units, `23` stopped units (`24.73 / 100`), `-13.85R`,
  PF `0.57`, and `5.78R` of right tail;
- other hour-20 aligned Children: `196` Children, `468` units, `18` stopped
  units (`3.85 / 100`), `+3.62R`, and `28.59R` of right tail.

The interaction is not yet a rule. It has only 35 observations; 2024 had no
stops in either matched subgroup, and the event family is heterogeneous
(auctions, FOMC, Baker Hughes, speeches, and releases). It is retained as one
joint-state shadow feature, not as evidence that all important news is bad.

## FAST flip and realized-shock finding

For NHA/FAST flips within 240 minutes after a USD moderate/high event, causal
same-event surprise magnitude separated transition quality:

| prior-release surprise | flips | linked k1 stop rate | mean new FAST run |
|---|---:|---:|---:|
| abs z <= 1 | 87 | 16.28% | 3.62 H4 bars |
| 1 < abs z <= 2 | 128 | 23.62% | 3.09 H4 bars |
| abs z > 2 | 167 | 27.11% | 2.90 H4 bars |

The effect is most suggestive when Phase-1B already calls the flip old-journey
counterflow or after-key-arrival, but those interaction cells are sparse. A
large surprise should therefore change the interpretation of an NHA from
"new journey evidence" toward "event-shock transition risk"; it does not grant
an entry veto or reverse direction by itself.

## Decision

Phase 1D establishes that time is a real missing state dimension, but rejects
three shortcuts:

- fixed hour/session veto;
- all-news avoidance;
- surprise-direction oracle.

Retain two shadow-only observations for later frozen chronology:

1. `H20 + aligned active journey + scheduled USD moderate/high in 30–60m` as a
   possible pre-release exposure-risk state;
2. `post-release surprise magnitude + Phase-1B flip meaning` as a transition
   interpretation coordinate.

Neither may change V10/V12 admission, exit, size, or capital until independent
future evidence and Python/MQL5 parity exist. The Phase-1C rolling target
inventory remains the structural next task; temporal state should be joined to
it rather than replacing it.
