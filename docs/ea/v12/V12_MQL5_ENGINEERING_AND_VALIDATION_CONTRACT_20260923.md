# V12 MQL5 engineering and validation contract

Date: `2026-09-23`

Status: `ENGINEERING CONTRACT / NO EA OR PRODUCTION AUTHORITY`

## 1. Separation of responsibilities

```text
Python causal oracle
  defines bars, states, features, and expected event ledger

MQL5 event probe
  reproduces the same ledger inside MT5

MQL5 research EA
  is allowed only after parity and tests execution/economics

production EA
  requires a later explicit promotion contract
```

Do not combine all four stages into one opaque optimization EA.

## 2. Tester-mode policy

The MT5 Strategy Tester supports several generation modes. V12 uses them for
different purposes:

- Open prices only: compile/event-loop smoke tests where no intrabar claim is
  made;
- 1 Minute OHLC: fast deterministic state-machine and ledger-parity diagnostics;
- Every tick based on real ticks: required economic evidence whenever entry,
  Hard SL, target, spread, or order timing can differ intrabar.

A favorable 1 Minute OHLC result is never substituted for real-tick evidence.
If exact tick history is unavailable, affected orderings remain ambiguous.

Official reference:
https://www.mql5.com/en/docs/runtime/testing

## 3. Event-ledger parity gate

Before P/L testing, Python and MQL5 must match on a frozen sample for:

- parent/child IDs and timestamps;
- C1/C2 O/H/L/C and range-interaction class;
- trigger primitives and decision timestamp;
- entry/SL/target coordinates for every active variant;
- FAST/STD/SLOW and Wave feature vectors where used;
- missing/ambiguous/excluded reason codes;
- feature names, order, data types, and schema hash.

Report exact match counts, tolerances in symbol points, first mismatch examples,
source hash, terminal build, symbol specification, and timezone/session spec.

## 4. Custom-symbol and data use

Custom symbols may be used to import a verified research history and freeze
symbol properties. Custom ticks are preferred when true ordering is required.
The import manifest must record tick/M1 hashes, digits, point, tick size/value,
contract size, sessions, spread policy, and timezone conversion.

References:

- https://www.mql5.com/en/docs/customsymbols
- https://www.mql5.com/en/book/advanced/custom_symbols/custom_symbols_ticks

## 5. Order lifecycle

Use `CTrade` only as the request interface; a successful method return is not
proof of execution. Inspect `ResultRetcode`, order/deal identifiers, and the
terminal transaction stream.

`OnTradeTransaction` can receive multiple transactions for one request and their
arrival order is not guaranteed. Handlers must remain short, correlate by request
and order/deal IDs, and write an append-only lifecycle ledger.

References:

- https://www.mql5.com/en/docs/standardlibrary/tradeclasses/ctrade
- https://www.mql5.com/en/docs/standardlibrary/tradeclasses/ctrade/ctraderesultretcode
- https://www.mql5.com/en/docs/event_handlers/ontradetransaction

The ledger must distinguish at least:

- request accepted/rejected;
- order placed/expired/cancelled;
- partial/full fill;
- SL/TP/manual/strategy exit;
- market closed;
- invalid price/stops/volume;
- no money;
- disconnected or unresolved transaction.

Market-closed requests are execution failures. Do not score them as strategy
losses and do not backfill them at the next open unless a future contract grants
that behavior.

## 6. ONNX boundary

MQL5 can load and run ONNX models and validate them in Strategy Tester. V12 will
export the complete preprocessing and model pipeline together where supported.

Required model manifest:

- training data hashes and consumed cutoff;
- split/fold definitions and embargo;
- feature names/order/types and normalization constants;
- tensor input/output names and shapes;
- model and schema hashes;
- Python reference vectors and expected outputs;
- MQL5 tolerance report;
- calibration and stability report.

Do not normalize once in the exported pipeline and again in MQL5. Do not call an
ONNX session per tick when the decision clock is H1/H4.

References:

- https://www.mql5.com/en/docs/onnx
- https://www.mql5.com/en/docs/onnx/onnx_test

## 7. Optimization and statistics

`OnTester`, `OnTesterPass`, frames, and `TesterStatistics` may collect a vector
scorecard. No single custom fitness number has authority to hide stop count,
right-tail loss, exposure, or instability.

Minimum tester report:

- gross/net R and cost assumptions;
- Children, wins, stops, ambiguous and failed orders;
- stopped units and stop-chain morphology;
- right-tail bucket retention;
- maximum and time-under drawdown;
- concurrent gross/net exposure;
- lane/side/year/era breakdown;
- calibration metrics for each ML head;
- parity and contamination incidents.

References:

- https://www.mql5.com/en/docs/common/testerstatistics
- https://www.mql5.com/en/docs/constants/environment_state/Statistics
- https://www.mql5.com/en/docs/runtime/testing

## 8. Validation ladder

1. schema validation and synthetic state tests;
2. raw-M1 causal Python event universe;
3. blind label audit of trigger primitives;
4. Python/MQL5 event-ledger parity;
5. no-ML real-tick baseline economics;
6. HA/Wave incremental ablation;
7. purged walk-forward/CPCV ML shadow with calibration;
8. frozen future shadow after the consumed cutoff;
9. only then consider an EA promotion contract.

Passing a lower gate does not imply passing a higher one.

## 9. External implementation ideas

MQL5 Articles and CodeBase examples may suggest architecture, completed-candle
processing, one-sweep-per-level handling, or ONNX packaging. They must be
reimplemented against this contract. Community backtests and source code are not
V12 evidence by themselves.
