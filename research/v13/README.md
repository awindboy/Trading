# V13 research code

V13 has one observation-only Python audit:

`ha_representation_audit.py` reproduces HA-0..HA-3 descriptive ledgers from
chronological GOLD# H4 and raw M1 source files. It is not an EA feature stack,
trading signal generator, or an official economic backtest. Decision fields and
future labels are written separately under `output/v13_ha3_20260927/`.

The active baseline implementation is:

`../../mt5/experts/V13HAOnlyMax10EA.mq5`

Execution revision 13.002 is tested by
`../../mt5/tests/V13ExecutionRecoveryTest.mq5`, which includes the actual EA
functions with fake trade/position APIs. This is fault-injection evidence only,
not a Python feature stack or a trading result. The recovery contract and
validation limits are under `docs/ea/v13/V13_EXECUTION_RECOVERY_20260926.md`.

Python may be added later only for explicit V13 analysis tasks such as Journey
failure decomposition or parity validation. Do not import V10-V12 feature code
into V13 merely because it already exists.
