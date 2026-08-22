# Trading D-154B local shadow package

This package continues the uncommitted D-154A working tree. It does **not** commit, push, or update permanent project docs.

## Apply

From the Trading repository root:

```powershell
python <EXTRACTED_PACKAGE>\apply_d154b.py
```

The installer fails closed unless:
- Git HEAD is still `3bf78e1...`;
- the HEAD V2 EA blob is the expected D-152 base;
- no staged changes exist;
- the only tracked working-tree modification is the D-154A V2 EA;
- required D-154A markers are present;
- D-154B has not already been applied.

## Run sequence

1. Compile `mt5/experts/MentorDeterministicV2EA.mq5` — require **0 errors**.
2. Refresh the Strategy Tester preset once so `InpV2D154BConfirmationAudit` appears.
3. `python tools\run_d154b_parity_gold_short.py`
4. `python tools\compare_d154b_parity.py <OFF.csv> <ON.csv>`
5. Only after parity PASS: `python tools\run_d154b_gold_btc_2025.py`
6. Return the generated ZIP.
7. Optional local summary:
   `python tools\summarize_d154b_confirmation.py <CSV_OR_DIRECTORY> [...]`

The D-154A result memo is included only in this package's `research/` folder; it is not automatically copied into the repository.
