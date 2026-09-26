# V13 research code

V13 currently has no active Python feature stack.

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
