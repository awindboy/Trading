# V12 research code inventory

V12 is the active CRT/HA/Wave/ML hybrid research generation.

## Retained Phase-0 artifacts

- `v12_crt_event_contract.schema.json`: machine-readable boundary between a
  causal decision record and a later outcome record. It contains synthetic
  examples only.
- `validate_v12_event_schema.py`: dependency-free integrity check for the schema,
  examples, OHLC invariants, hash/timestamp format, and C2-branch direction map.

Run:

```powershell
python research/v12/validate_v12_event_schema.py
```

Passing this validation establishes only that the contract is internally
consistent. It does not build market candidates or prove CRT, HA, Wave, ML, or
trading performance.

## Next retained implementation

The next script should build the exhaustive W1->H4 and D1->H1 C1/C2 universe
from verified raw M1 in chronological order. It must not depend on a V10 event
ledger. Before that implementation is accepted, freeze:

- raw-M1 source and broker-clock/session manifest;
- equality/point-rounding policy;
- partial/weekend parent-bar policy;
- exact event-definition version;
- output decision/outcome file separation.

Large ledgers and diagnostics belong under ignored `output/`.

## Predecessor reuse boundary

V10/V11 code may provide tested OHLC aggregation, HA, ATR normalization, Wave,
feature-registry, and parity utilities. Reuse requires explicit imports or copied
functions with a named role and tests. V10 selected-event ledgers may be used only
as comparators; they cannot seed V12 candidates.
