## D-179 — Lock the V5-034A validation population in code before external outcomes

Status: `ACTIVE / FROZEN PRE-VALIDATION POPULATION DECISION`
Date: `2026-08-27`

A post-push audit of the hardened V5-034A replay found that the candidate rules and uncertainty gate were frozen, but
one governance invariant was not yet fail-closed in code: the script accepted whatever market keys appeared in the
local data map and only required that 2023/2024/2025 were present somewhere in the loaded data.

That could allow an accidental validation population change without changing the strategy itself, for example:

```text
- omit one frozen external market;
- substitute another symbol under the data map;
- include 2022 or 2026 rows in pooled validation;
- supply a materially incomplete calendar year;
- swap a raw file under the wrong symbol key.
```

Before any external outcomes are opened, freeze the replay population as:

```text
markets exactly = XAUJPY#, XAUCNH#, GAUCNH#, GAUUSD#
years exactly   = 2023, 2024, 2025
coverage        = every required year must contain all 12 calendar months
timestamps      = strict M1 alignment, sorted, unique
file identity   = each configured filename must contain its canonical symbol stem
```

The existing raw SHA-256 / point / file-order preflight remains mandatory.

This is validation-population and data-integrity hardening, not candidate retuning. Entry, stop, partial, runner,
timeframe, cost proxy, bootstrap, validation gates and frozen market set are unchanged.

No V5-034A external outcome and no GOLD# 2021 data were opened while making this decision.
