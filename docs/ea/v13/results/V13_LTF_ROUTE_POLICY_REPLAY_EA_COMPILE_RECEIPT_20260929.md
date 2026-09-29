# V13 LTF route policy-replay EA compile receipt

Date: `2026-09-29`
Status: `SOURCE COMPILE CONFIRMED / ACTUAL-TICK PARITY RECEIPT PUBLISHED`

Artifact:

`mt5/experts/V13LTFRouteQ75Q50_PolicyReplayEA.mq5`

```text
source SHA-256  94156bdd0221de876733f45110221d901b21ab02d5e05477bf78d421480a546f
EX5 SHA-256     1d9c7e00eb2a337c35e22b15bc538c3cd403be08e8ddafc9e1bc59f03d612710
EX5 bytes       49,420
MetaEditor      XM Global MT5 MetaEditor64
result          0 errors, 0 warnings
elapsed         1,131 ms
target          X64 Regular
```

Implemented execution protections:

- hedging account and exact symbol/lot checks;
- strict ledger schema, order and one-entry/one-exit pairing checks;
- same-timestamp ordering supplied by the frozen ledger (`EXIT` before `ENTRY`);
- transient failure retry for market closed, requote, price change/off,
  connection, timeout, lock and frozen states;
- no backfill when the first executable tick arrives after a frozen exit;
- permanent failure and position/comment/count mismatch halt fail-closed;
- fixed `V13Q75_EVENT|` Journal prefix for parity parsing.
- per-event balance deltas plus exact-tick equity DD and concurrency telemetry.

The EX5 is a local compile product and need not be committed. This receipt does
not establish live readiness. Policy-ledger parity and actual-tick economics
are documented separately in
`V13_LTF_ROUTE_Q75_Q50_ACTUAL_TICK_REPLAY_RECEIPT_20260929.md`.
