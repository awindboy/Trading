# V13 research code

V13's observation-only Python audits:

`ha_representation_audit.py` reproduces HA-0..HA-3 descriptive ledgers from
chronological GOLD# H4 and raw M1 source files. It is not an EA feature stack,
trading signal generator, or an official economic backtest. Decision fields and
future labels are written separately under `output/v13_ha3_20260927/`.

`ha4_mtf_audit.py` streams raw GOLD# M1 to reconstruct H4 plus one context
timeframe. Run `--stage d1` and `--stage h1` separately, with the matching
export path used only to verify OHLC parity. It writes decision-time features,
future labels and a compact summary separately under
`output/v13_ha4_d1_20260927/` or `output/v13_ha4_h1_20260927/`. No D1/H1
field changes Baseline-0 trading.

For HA-4C/D, rerun `ha4_mtf_audit.py` into *new* local D1/H1 output
directories; it now also records the ordered within-H4 H1 color path and
completed-context Delta contraction. Then run
`ha_integrated_state_audit.py --ha3 <HA-3 output> --h1 <new H1 output>
--d1 <new D1 output> --output <local integrated output>`. The integration
checks source hashes, timeframe parity, identical Standard-H4 Journey IDs and
PRE/POST EMA2 Open/Close/color identity. It writes matched decision features,
future labels and a compact JSON summary separately. It is neither a strategy
variant nor a real-tick economic backtest. The contracts and compact findings
are under `docs/ea/v13/` and `docs/ea/v13/results/`.

`ha5_causal_raw_swing_audit.py` streams raw GOLD# M1 through the frozen
canonical cutoff, rebuilds H4 with export parity, and confirms strict
five-bar H4 raw-price pivots only after their right-hand bars complete.
It compares the already-known raw levels against unchanged HA-4C/D decisions
and separately stored future labels. Example invocation from repository root:

```powershell
python research/v13/ha5_causal_raw_swing_audit.py --m1 'data/GOLD#/GOLD#_M1_202201030100_202609222358.csv' --h4 'data/GOLD#/GOLD#_H4_202201030000_202609230000.csv' --integrated output/v13_ha4c_integrated_20260927 --output output/v13_ha5_raw_swing_20260927
```

This is observation-only, not an MT5 backtest or an HA-5 action rule. See the
frozen contract and compact receipt under `docs/ea/v13/`.
Run `python research/v13/test_ha5_causal_raw_swing_audit.py` for the mirrored
LONG/SHORT, level-change and close-versus-probe state checks.

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
