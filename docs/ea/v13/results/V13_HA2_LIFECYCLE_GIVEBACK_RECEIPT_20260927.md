# V13 HA-2 lifecycle, lag and giveback receipt

Date: `2026-09-27`

Status: `DESCRIPTIVE DEVELOPMENT EVIDENCE / NO EARLY-EXIT RULE`

Source/formula/window: HA-0 receipt and `research/v13/ha_representation_audit.py`.
For each closed standard-HA Journey, the favorable raw M1 high/low is found
from first next-H4-open entry until the opposite-color exit open. Giveback is
`favorable high - exit raw open` for LONG and `exit raw open - favorable low`
for SHORT. It is a GOLD **price distance**, not money or MT5 P/L.

```text
closed Journeys                                      965
median raw extreme -> opposite-color exit         7.35 hours
median favorable-extreme giveback                 21.41 GOLD price
90th-percentile giveback                          62.48 GOLD price
extreme in flip bar or preceding two H4 bars       86.3%
```

Median giveback by Journey-start year:

| 2024 | 2025 | 2026 through Aug 28 |
|---:|---:|---:|
| 13.53 | 23.18 | 46.05 |

The calendar-year slices are diagnostic, not independent validations. Similar
time lag can cost different price distances as GOLD# volatility changes.
The raw extreme is a **future outcome label**; it was not known when the
Journey was open. The fact that most extrema occur near the eventual color
flip also warns against exiting on the first contraction or wick symptom.

The most clearly observed future action problem is exit/giveback, with late
additional funding a related symptom. This is a research priority, not an
authorized exit trigger. Baseline 0 remains unchanged.
