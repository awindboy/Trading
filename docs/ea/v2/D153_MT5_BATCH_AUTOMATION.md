# D-153 MT5 Batch Backtest Automation

Date: 2026-08-22  
Status: **TEST INFRASTRUCTURE / NO STRATEGY AUTHORITY**  
Strategy code changed: **NO**  
2021: **UNTOUCHED**

## Purpose

For the current V2 research window, manual Strategy Tester operation is replaced by a reproducible sequential runner.

Fixed test universe:

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

Fixed EA research inputs:

```text
ROOT_OB_DISTAL_20
BASELINE_NO_REGIME_GATE
RESEARCH_COMPACT
FIXED_RISK_MONEY = $100
EM = OFF unless a research case explicitly changes it
EdgeAudit = OFF
D151 causal audit = ON
```

The runner does **not** modify Entry, SL, TP, SP, EM, or any trading logic.

## Stable engine vs research cases

```text
tools/mt5_batch_runner.py
    stable infrastructure:
    - locate MT5/data directory/current V2 preset
    - generate per-run tester .set
    - generate /config .ini
    - run terminal64.exe sequentially
    - collect one ledger CSV per run
    - verify EA_START/EA_STOP
    - record divergence/cancel-reject flags
    - archive exact .set/.ini/manifest/log
    - create final ZIP on Windows Desktop

tools/run_d152_gold_btc_2025.py
    research case definition only
```

Future research should normally add a new small case file rather than editing the stable engine.

## Output

Every strategy case receives a unique CSV name, for example:

```text
D152_SP_V3__V3B_PROFIT_BANK__GOLD__2025.csv
D152_SP_V3__V3B_PROFIT_BANK__BTCUSD__2025.csv
```

After the last run the runner creates:

```text
Desktop/Trading_D152_SP_V3_YYYYMMDD_HHMMSS.zip
```

The ZIP contains all CSVs plus:

```text
batch_manifest.json
run_log.txt
repro/*.set
repro/*.ini
```

The ZIP is the preferred artifact to send back for analysis.

## MT5 discovery

The runner looks for an MT5 data directory that contains:

```text
MentorDeterministicV2EA.ex5
a current Tester .set containing the V2 input names
```

It uses the terminal data-directory `origin.txt` to find the corresponding `terminal64.exe`.

If multiple installations require an override:

```powershell
$env:MT5_DATA_DIR="C:\Users\...\AppData\Roaming\MetaQuotes\Terminal\<hash>"
$env:MT5_TERMINAL_EXE="C:\Program Files\...\terminal64.exe"
```

## Operational rule

Close MT5 before starting a batch. The runner uses `ShutdownTerminal=1`, so each test owns one terminal lifecycle and the next case starts only after the prior one has finished.

Account-level Strategy Tester fields `Deposit`, `Currency`, `Leverage`, and `ExecutionMode` are currently inherited from the terminal's existing tester configuration rather than silently inventing new project values. They remain constant within a batch. If those values are later frozen as project authority, they should be added explicitly to the stable runner.

## Current D-152 matrix

The first batch contains six isolated SP modes per symbol:

```text
CTRL SP V2
V3A KNOWN_DEFAULT_CLOSE
V3B PROFIT_BANK
V3C BANK_3R_LOCK
V3D STRUCTURAL_BANK
V3E BANK_2R_LOCK_ONE
```

Total: `6 x 2 symbols = 12` Strategy Tester runs.
