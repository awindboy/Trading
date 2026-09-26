# V13 document authority map

As of `2026-09-26`, read V13 in this order:

1. `AGENTS_V13.md` — active generation boundary, frozen baseline, causal rules,
   comparison period, and research discipline.
2. `HANDOFF_V13.md` — shortest resume point and immediate next action.
3. `RESEARCH_STATE_V13.md` — established facts, preliminary sanity result, and
   what remains unverified.
4. `V13_BASELINE0_HA_MAX10_CONTRACT_20260926.md` — exact strategy semantics.
5. `V13_MQL5_BACKTEST_PROTOCOL_20260926.md` — exact tester setup and required
   output/report fields.
6. `results/README.md` — compact result routing and official-result boundary.
7. `../../../mt5/experts/V13HAOnlyMax10EA.mq5` — frozen MQL5 implementation of
   Baseline 0.
8. `../../../mt5/tester/V13HAOnlyMax10.GOLD.actualticks.2024_2026.ini` — starter
   tester configuration; the Strategy Tester GUI remains authoritative for the
   broker/account-specific setup.

## Precedence

V13 controls active strategy research. V12 and earlier remain historical
records. If an older document suggests importing CRT, liquidity, ML, Wave,
multi-speed HA, structural SL, or another filter into the active baseline, that
suggestion has no V13 authority until a new V13 contract explicitly adds it.
