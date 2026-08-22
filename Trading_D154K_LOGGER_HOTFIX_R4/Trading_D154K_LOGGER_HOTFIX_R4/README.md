# D-154K Logger Hotfix R4

Use this after D-154K R3 has already been applied.

The supplied Q1 parity evidence proved the D-154K input and hooks were executing:

```text
GOLD Q1:   +20 suppressed log calls = start + 9 snapshots + 9 outcomes + stop
CADJPY Q1: +78 suppressed log calls = start + 38 snapshots + 38 outcomes + stop
```

The issue was the existing `RESEARCH_COMPACT` whitelist: it emitted `D154G_*`,
`D154H_*`, and `D154J_*`, but not `D154K_*`.

R4 only:
1. adds `D154K_*` to the compact research-log whitelist;
2. updates D154K parity canonicalization to normalize the expected
   `csv_rows_written` and `log_calls_suppressed` summary counters.

No strategy authority or D-154K measurement formula is changed.

## Apply

From repo root:

```powershell
python .\Trading_D154K_LOGGER_HOTFIX_R4\apply_d154k_logger_hotfix_r4.py
```

Compile the EA with 0 errors, then rerun:

```powershell
python tools\run_d154k_gold_cadjpy25.py
```

The runner will perform dual-symbol Q1 parity first and only continue to the
full-year GOLD25 + CADJPY25 study if parity passes.
