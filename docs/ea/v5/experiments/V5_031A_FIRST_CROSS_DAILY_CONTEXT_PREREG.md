# V5-031A First Cross 240m + Daily 3/10 Context
Status: FROZEN BEFORE OUTCOME ANALYSIS
Date: 2026-08-27
Parent: V5-030A.

Source basis: Raschke/3-10 materials explicitly describe using setups across multiple timeframes and using the 3/10 slow line as trend state. This test asks whether the 240m first retracement/reversal is more reliable when it resolves in the direction of the already-established daily trend.

Frozen filter at 240m setup completion:
- construct daily bars causally; only completed daily bar is available;
- daily fast = SMA3 - SMA10; daily slow = SMA16(fast);
- LONG eligible only if latest completed daily slow > 0;
- SHORT eligible only if latest completed daily slow < 0;
- no magnitude/slope/ADX threshold.

Entry, structural stop, +1R 50% partial, BE runner, EMA20/slow 240m runner exit, spread cost and ambiguity handling are exactly V5-030A.
Report all four markets, all years and both directions. GOLD# 2022 may be used only as consumed diagnostic after development metrics; GOLD# 2021 remains untouched.
