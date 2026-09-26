# V13 HA-1 morphology and persistence receipt

Date: `2026-09-27`

Status: `DESCRIPTIVE DEVELOPMENT EVIDENCE / NO TRADE RULE CHANGE`

Source/formula/window: HA-0 receipt and `research/v13/ha_representation_audit.py`.
All figures below use completed standard-HA H4 states and *subsequent* flip
labels. Quantile boundaries were observed after the data and are not gates.

| Completed HA state | Next H4 color flip |
|---|---:|
| No opposite wick | 14.6% (1,915 observations) |
| Opposite wick present | 31.3% (2,192 observations) |
| Weakest body/range quintile | 41.9% |
| Strongest body/range quintile | 8.6% |
| Body strength and absolute Delta both contract vs prior same-Journey bar | 40.0% (1,184 observations) |

This reproduces the central earlier-session finding: HA morphology contains
transition information beyond color alone. It does **not** establish an
executable exit. Body/range and opposite wick are geometrically related, not
independent evidence. The earlier exploratory analysis reported a strong
negative association between their ratios; do not add them as separate votes.
Same-color bar count alone showed little monotonic aging in that analysis.

Opposite-wick reappearance is defined in the audit as a wick appearing after
a no-opposite-wick bar within the same Journey. Across repeated events there
were 556 occurrences. Taking only the first per Journey yields 413 Journeys:
42.6% flipped in the next bar, 58.8% within two, and 68.5% within three.
This symptom can precede a flip, but some Journeys flip without it and many
symptoms do not flip immediately.

These are in-sample descriptive associations on consumed history, not
out-of-sample probabilities or instructions to trade.
