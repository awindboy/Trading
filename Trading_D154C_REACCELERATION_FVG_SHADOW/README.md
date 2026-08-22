# Trading D-154C Reacceleration-FVG Shadow

Targets current committed D-154B state.

- HEAD: `af4643738192b68109adc5ddc192234619690a20`
- EA blob: `42b0632df8388dc8800c6b4b6820272c6cff1208`
- Target local research build: `2.05R0L5`
- Strategy authority change: **none**

## What D-154C tests

```text
TRANSITION baseline Fill
-> first SAME-direction M1 INITIAL_BOS
-> do NOT chase confirmation price
-> first NEW same-direction M1 FVG
-> first retracement into that FVG
-> shadow Entry at FVG proximal edge
-> original normalized SL
-> recomputed +1R
```

If the original baseline reaches +1R or SL before the FVG retest, D-154C does not backfill a trade.

## Apply

From repository root:

```powershell
python <EXTRACTED_PACKAGE>\apply_d154c.py
```

The installer:
- requires exact HEAD and EA blob;
- requires the V2 EA itself to be clean;
- ignores unrelated package/archive working-tree changes;
- performs all source transformations in memory before writing;
- refuses to overwrite existing D-154C repo tool files;
- does not commit or push.

## Run

1. Compile EA — require **0 errors**.
2. Refresh the Strategy Tester preset so `InpV2D154CReaccelerationFvgAudit` appears.
3. Run:
   `python tools\run_d154c_parity_gold_q1.py`
4. Compare OFF/ON ledgers:
   `python tools\compare_d154c_parity.py <OFF.csv> <ON.csv>`
5. Only after PASS:
   `python tools\run_d154c_gold_btc_2025.py`
6. Return the generated ZIP.

Permanent project docs are intentionally not updated in this package.
