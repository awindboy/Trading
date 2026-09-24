# V12 Phase-1E session, weekday, and event interaction result

Date: `2026-09-24`

Status: `CONSUMED-DEVELOPMENT MECHANISM RESULT / NO TRADE OR SIZING AUTHORITY`

Contract: `v12-phase1e-session-weekday-event-interaction-v1.1`

## Calendar correction and named-session authority

The first Phase-1D calendar export was not valid enough for named sessions. Its
first January 2022 query was three hours behind later queries and duplicated
eight IDs at the next chunk boundary. The corrected exporter waits for server
synchronization, requires two stable sentinel reads, and uses one full-range
query. It returned `68,369` rows and `68,369` unique value IDs.

One independent source anomaly remained: ten US Employment Situation members
on 2025-11-20 were stamped server 15:30, although BLS records the delayed
release at 08:30 ET. The locked override moves only those ten exact IDs to
server 16:30. After it, all 56 nonfarm-payroll and all 38 Fed-rate-decision
sentinels match a fixed server `UTC+3` clock with DST-aware New York time.

The corrected Phase-1D build has `20,274` timed clusters. Its key 86-Child and
35-Child interaction counts and R results are unchanged; offset zero remains
the best event/activity alignment. Thus the old source receipt was wrong, but
the retained Phase-1D mechanism conclusions survive the correction.

## Actual session activity

The session windows are DST-aware market landmarks, not a claim that OTC gold
has one centralized exchange session.

| session phase | M1 minutes | tick volume / minute | summed M1 range / minute |
|---|---:|---:|---:|
| London-New York overlap | 224,093 | 245.43 | 1.698 |
| London before New York | 396,566 | 140.51 | 1.055 |
| New York after London | 317,009 | 131.59 | 0.942 |
| Asia precious-metals core | 509,871 | 119.30 | 0.961 |
| Outside core windows | 221,534 | 77.67 | 0.853 |

Absolute activity rises sharply across liquidity eras, so the retained output
also reports every cell by year and daily activity share. The overlap remains
the highest tick-volume-per-minute phase in each consumed year rather than only
in the pooled level.

The user's observed 16:00 liquidity concentration is therefore mostly the
London/New York handoff and overlap, not a timeless broker-hour property.

## V10 capital by entry session

| entry session | Children | funded units | stopped units / 100 | net R | >=5R right tail |
|---|---:|---:|---:|---:|---:|
| Asia core | 543 | 1,267 | 14.05 | +250.46 | 329.24 |
| London-New York overlap | 177 | 397 | 15.37 | +98.21 | 117.86 |
| London before New York | 374 | 888 | 16.10 | +294.28 | 331.15 |
| New York after London | 315 | 753 | 8.76 | +2.74 | 84.46 |
| Outside core windows | 240 | 576 | 6.60 | +95.32 | 148.70 |

This is the central result. The two lowest-stop phases do not carry the most
conviction capital. London before New York has the highest broad stop burden
and also the highest net R and right tail. New York after London has a much
lower stop burden but nearly zero net R; its 95% week-block interval for net R
is `-65.43R` to `+84.18R`. A session-based stop filter would confuse lower
exposure quality with lower stop frequency.

The same warning holds inside CRT relation. Opposed Children during London
before New York had `30.54` stopped units per 100, yet retained `+88.41R` and
`115.46R` of right tail. Relation plus session still does not create a safe
veto.

## Weekday result

New York Friday and Wednesday carried the highest broad stopped exposure:

- Friday: 227 Children, `19.77` stopped units per 100, `+92.89R`, `143.26R`
  right tail;
- Wednesday: 318 Children, `16.84` stopped units per 100, `+134.14R`,
  `265.96R` right tail, and a nine-stop maximum chain;
- Thursday: only `9.73` stopped units per 100 while retaining `+218.41R` and
  `279.05R` right tail.

Friday and Wednesday are therefore useful transition-risk coordinates, not
standalone avoidance rules. The apparently weak Asia-Friday cell has only 49
Children and changes from negative in 2024–2025 to positive in 2026. Several
high-stop session/weekday/CRT cells are strongly profitable because their right
tail dominates, including opposed London-before-New-York Thursday.

## FAST/NHA meaning by session

Linked k1 stop rates after a FAST flip were `35.5%–37.9%` in Asia/London phases
but only `13.0%–14.3%` in New-York-after-London/outside-core phases. Mean new
FAST-run length stayed close to 3.2–3.35 H4 bars in every phase. Time therefore
changes the immediate whipsaw probability more clearly than the eventual run
length, but this is largely tied to the six discrete H4 decision slots and is
not an independent directional oracle.

## Decomposition of the retained H20 event state

All 231 hour-20 aligned Children are classified as New York after London, so a
session label adds no further separation. The 35 pre-USD-moderate/high Children
remain distinct from the 196 controls:

| H20 aligned state | Children | stopped units / 100 | net R | >=5R tail | 95% stop interval | 95% net-R interval |
|---|---:|---:|---:|---:|---:|---:|
| event in 30–60m | 35 | 24.73 | -13.85 | 5.78 | 10.23–42.67 | -34.36–+8.26 |
| other | 196 | 3.85 | +3.62 | 28.59 | 1.32–6.96 | -40.64–+49.44 |

It is not merely a Friday/Baker-Hughes proxy. The event cell contains 17
auction, 11 Baker-Hughes, and 6 FOMC Children, with stops also present on Monday,
Tuesday, Wednesday, and Friday. It is directionally poor in all three observed
years, but only 35 Children across 27 ISO weeks and its net-R interval still
crosses zero. It remains a higher-priority frozen shadow interaction, not trade
authority.

## Decision

Session and weekday add real descriptive information, especially for when an
NHA/FAST flip is likely to whipsaw. They do not solve the core V10 problem by
themselves: high-stop states often own the largest right tail, while some
low-stop states have little net economic value.

The next useful unit is not `session` or `weekday` alone. It is a competing
state measured at the same Child:

`CRT journey relation + target completeness + FAST/NHA meaning + session phase
+ weekday + scheduled/realized event state`.

The H20 pre-event interaction should be carried unchanged into that target-
state study. Friday/Wednesday and London transition risk should remain shadow
coordinates. No cell in this study may change admission, exit, or size on the
consumed history.
