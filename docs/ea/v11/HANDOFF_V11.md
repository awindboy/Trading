# V11 frozen handoff

Last synchronized: `2026-09-23`

Status: `FROZEN PREDECESSOR / OBSERVATION ASSET / NO TRADE AUTHORITY`

## What V11 produced

- Wave Candle v0.5.1: selectable FAST/STD/SLOW HA or raw H4 shell plus completed-
  M5 settlement-density contour and selected-candle O/H/C/L lines;
- a neutral-bridge grammar separating Child interruption from opposite-direction
  authorization;
- complete stop/right-tail/exposure audits of V10-bound capital staging;
- one ledger-independent STD/SLOW-memory skeleton and progress-ladder test.

## Final conclusion

Static Wave geometry, liquidity-arrival topology, fixed bridge waits, broad
binary ML funding, whole-base STD substitution, and fixed campaign caps did not
solve selective stop reduction. Capital staging reduced full-size stopped units
and alternating stop pairs, but did not reduce stopped-Child count.

The independent STD/SLOW-memory skeleton recorded a lower descriptive stop rate
but failed side/year robustness and used a wider bridge stop. Its progress ladder
controlled size, not stop recognition. See
`results/V11_NEW_SKELETON_PHASE_AND_PROGRESS_LADDER_DIAGNOSTIC_20260923.md`.

## Reuse in V12

- retain the MT5 Wave Candle as an observation instrument;
- reuse tested HA/Wave/normalization/parity components only with explicit V12
  roles;
- do not seed V12 candidates from the V10/V11 event ledger;
- do not promote any V11 threshold or capital rule.
