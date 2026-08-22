# Trading D-154H HTF Nested Causal Replay

Base Git HEAD: `0c2561619b70eff6deafa90cf9a79730de2e5848`  
Base EA: `2.07R0L7 / D154G`  
Target EA: `2.08R0L8 / D154H`

This is a fail-closed shadow-instrumentation package. It does not change strategy authority.

## Apply

From the Trading repo root:

```powershell
python .\Trading_D154H_HTF_NESTED_CAUSAL_REPLAY\apply_d154h.py
```

The installer requires the exact committed D-154G HEAD and refuses real local content changes in the files it replaces.

## Compile

Compile `mt5/experts/MentorDeterministicV2EA.mq5` in MetaEditor and require 0 errors. Refresh the Strategy Tester preset and confirm `InpV2D154HHTFNestedReplayAudit`.

## Parity

```powershell
python tools\run_d154h_parity_gold23_q1.py --dry-run
python tools\run_d154h_parity_gold23_q1.py
python tools\compare_d154h_parity.py <OFF.csv> <ON.csv>
```

Require `D154H NON-INTERFERENCE PARITY: PASS`.

## Discovery

Only after parity:

```powershell
python tools\run_d154h_discovery_gold23.py
```

Send the resulting GOLD23 ZIP. The clean discovery window ends 2023-12-21 to avoid the known 2023-12-22 broker market-closed cancellation fault.

Optional local integrity summary:

```powershell
python tools\summarize_d154h_nested_replay.py <discovery.zip>
```

Do not derive or apply an Entry veto from the discovery output locally. The next validation definition is frozen only after causal review.
