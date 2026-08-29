# V6-003E EA Overlay — Apply / Compile / Test

Expected repository HEAD before extraction:

```text
545f7756e357c03b06561d2090b7055815fd56b0
```

From the Trading repository root, verify:

```powershell
git rev-parse HEAD
git status --short
```

Fail closed if HEAD differs or there are unexpected local edits.

Extract this ZIP directly into the repository root. It only adds new files in this R0 package; it does not replace V1/V2.

Added:

```text
mt5/experts/MentorDeterministicV6EA.mq5
docs/ea/v6/V6_003E_MT5_ROLE_CORE_REPRO_CONTRACT.md
docs/ea/v6/V6_003E_EA_APPLY_README.md
```

Compile `mt5/experts/MentorDeterministicV6EA.mq5` in MetaEditor.

Required first compile gate:

```text
0 errors
```

Recommended first Strategy Tester run:

```text
Symbol: GOLD / GOLD# matching the broker dataset
Timeframe: M1
Model: Every tick based on real ticks
Range: consumed control first (prefer continuous 2023-2025 with enough warmup)
Account: hedging mode
InpExecuteTrades = true
InpWriteEventCsv = true
```

The CSV is written under the Strategy Tester file sandbox as:

```text
mentor_v6_role_core_r0_events.csv
```

Do not interpret P/L until event/routing parity is checked. Send back:
- MetaEditor compile output;
- Strategy Tester report;
- tester Journal log if errors occurred;
- generated V6 event CSV.

After review, commit and push only the intended files.
