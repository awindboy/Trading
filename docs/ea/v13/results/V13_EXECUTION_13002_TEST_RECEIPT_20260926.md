# Execution revision 13.002 test receipt

2026-09-26. Execution fault injection only; not Baseline-0 economic evidence.

- EA source SHA256: `af31a9b0bde37039574af604eda30361190147cf70ae223e872d06a30b607d4f`
- Compiled EA SHA256: `23223c479d8eacc947e8d82f62b855b0491f4f032464f3cb79bffc697fd38e82`
- Harness source SHA256: `0cdd87bf1c1e54a3f64647a2cba036c2ef97c097eb53c67f7cde40274ffd0eef`
- Production compile: zero errors/warnings, 871 ms.
- Harness compile: zero errors/warnings, 802 ms.
- MT5 build 5836, dedicated portable audit terminal; simulated EURUSD H4 clock,
  2024-01-02, 1-minute OHLC mode. No real trade APIs in the harness.
- `V13_TEST_SUMMARY|failures=0|broker_orders=0`: 17 PASS, zero FAIL.
- Agent log: dedicated audit terminal's
  `Tester/Agent-127.0.0.1-3000/logs/20260926.log`, run around 22:01:55 local.
- Compile logs: ignored `output/v13_compile.log` and
  `output/v13_test_compile.log`.

The first test launch could not start because the audit terminal lacks GOLD#.
EURUSD was used only to execute the synthetic fault harness. No GOLD# economics,
real-tick baseline result, broker-order fault reproduction or live readiness is
claimed. For exact scenarios and remaining limits, see
`../V13_EXECUTION_RECOVERY_20260926.md`.
