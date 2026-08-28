# V6-003C Conventional Direction-Indicator Atlas Freeze
Date: 2026-08-29
Base HEAD: 982839b0a1ea166fc534272f2024a72cedfb8326
Status: PRE-OUTCOME FREEZE

Purpose: falsify whether a conventional indicator can carry causal direction authority before the local event, rather than optimize indicator settings.

Frozen direction priors, completed H1 + H4 consensus only:
- AR25: Aroon(25): Up > Down = LONG, Down > Up = SHORT; H1/H4 disagree -> NEUTRAL.
- VI14: Vortex(14): VI+ > VI- = LONG, VI- > VI+ = SHORT; H1/H4 disagree -> NEUTRAL.
- RSI14: Wilder RSI(14): >50 = LONG, <50 = SHORT; H1/H4 disagree -> NEUTRAL.

Controls already consumed/frozen:
- MACD_H1H4 = sign EMA12-EMA26 consensus.
- DISP_H1_24 = simple 24-completed-H1 displacement.

No ADX threshold, no 70/30 RSI extreme rule, no parameter variants, no scoring/majority vote, no optimization.

Primary architecture: indicator direction first -> matching V3 sweep/recovery + M5 transition confirms timing -> existing direct-transfer flag is reported separately. Test both broad confirmation and frozen direct-transfer local confirmation; do not choose whichever looks best post hoc.

Kill condition: indicator does not recurrently outperform the simple displacement control or only works via heavy N collapse / one market / one direction.
