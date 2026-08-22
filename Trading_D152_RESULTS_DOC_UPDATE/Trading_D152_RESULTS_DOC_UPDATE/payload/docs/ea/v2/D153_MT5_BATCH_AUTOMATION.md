# D-153 MT5 Batch Backtest Automation

Date: 2026-08-22  
Status: **VALIDATED END-TO-END / TEST INFRASTRUCTURE**  
Strategy authority: **NONE**  
2021: **UNTOUCHED**

## Purpose

Manual repetitive MT5 Strategy Tester operation is replaced by a reproducible sequential runner.

Current fixed research universe:

```text
symbols: GOLD, BTCUSD
period: 2025.01.01 -> 2025.12.31
chart period: M1
tick model: Every tick based on real ticks (Model=4)
optimization: OFF
forward: OFF
visual: OFF
cloud agents: OFF
```

Fixed EA research defaults:

```text
ROOT_OB_DISTAL_20
BASELINE_NO_REGIME_GATE
RESEARCH_COMPACT
FIXED_RISK_MONEY = $100
EM = OFF unless a case explicitly overrides it
EdgeAudit = OFF
D151 causal audit = ON
```

The runner does not itself modify Entry, SL, TP, SP, EM, or scenario authority.

## Stable engine vs research cases

```text
tools/mt5_batch_runner.py
    stable test infrastructure

tools/run_<research>_gold_btc_2025.py
    phase-specific case matrix only
```

Future research should normally change only the case-definition file unless the test infrastructure itself needs repair.

## Validated workflow

The D-152 12-run matrix validated the complete chain:

```text
discover current MT5/V2 EX5/tester preset
-> generate per-run .set
-> generate /config .ini
-> run terminal64.exe
-> wait for completion
-> locate unique ledger CSV
-> verify EA_START/EA_STOP
-> record divergence/cancel-rejection flags
-> retain exact repro .set/.ini
-> create manifest/log
-> package all results into Desktop ZIP
```

Observed Windows tester-agent result path required support for:

```text
%APPDATA%\MetaQuotes\Tester\<tester-hash>\Agent-*\MQL5\Files
```

The runner now searches this location in addition to terminal-local/Common paths.

## First validated batch

D-152 SP V3:

```text
6 SP modes
x
2 symbols
=
12 real-tick 2025 runs
```

Artifact:

```text
Trading_D152_SP_V3_20260822_044945.zip
SHA256 e28cc77bb7c6419b958fdd77873a1e81fdf546ab9f52c7c776532cdf0e607d37
```

All 12 runs were usable for research analysis.

## Operational rule

Close MT5 before starting a batch.

Each test uses `ShutdownTerminal=1`; the next test begins only after the previous terminal lifecycle ends.

Each case must have a unique `InpEventCsvFile`.

## Account-level tester fields

`Deposit`, `Currency`, `Leverage`, and `ExecutionMode` are currently inherited from the terminal's configured tester state rather than invented by the runner.

Within a batch they remain common to all compared cases.

If the project later freezes these account-level fields as explicit research authority, add them to the stable runner configuration.

## Future use

The preferred workflow is now:

```text
research hypothesis
-> ChatGPT supplies strategy change if needed
-> ChatGPT supplies phase-specific case matrix
-> user runs one Python command
-> runner creates Desktop ZIP
-> ZIP is returned for raw-ledger analysis
```
