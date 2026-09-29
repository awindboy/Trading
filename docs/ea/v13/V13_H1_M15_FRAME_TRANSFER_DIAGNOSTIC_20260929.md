# V13 Whole-Frame Compression Diagnostic — H4/H1 to H1/M15 — 2026-09-29

Status: `REJECTED MAIN-FRAME CHANGE / USEFUL SCALE-INVARIANCE OBSERVATION`

This diagnostic is preserved because it changed the direction of the research.

## Transfer

```text
H4 main HA -> H1 main HA
H1 internal path -> M15 internal path
one-H4 proof window -> one-H1 proof window
same SA-1 / HA-9 concepts otherwise
```

## Session result

Approximate causal-replay metrics recorded during the session:

```text
H4/H1 SA-1
Journeys ~965
Trades 1,783
912W / 859L / 12 flat
Net +3,423.29
PF 1.269
DD ~948.70
loss streak 12

H1/M15 transfer
Journeys ~3,863
Trades 6,822
3,267W / 3,529L plus flats
Net +1,602.14
PF 1.058
DD ~1,002.19
loss streak 18
```

Year result for the transferred strategy was approximately:

```text
2024 -254.77 / PF 0.953
2025 +260.25 / PF 1.027
2026 +1,596.66 / PF 1.128
```

Trade count expanded roughly 3.8x while net fell below half of the H4/H1 idealized SA-1 result. Typical trade-block quality was near coin-flip and top-winner dependence increased; removing the top five profitable Journeys was enough to push the transferred result slightly negative.

## Interpretation

SA-1 admission/proof **shape** remained surprisingly similar across scale, suggesting that directional acceptance is not unique to H4. But the economic continuation distance was much smaller and noisier on H1/M15.

Decision:

- reject H1/M15 as the new main V13 frame;
- keep H4 as Parent/trend authority;
- use M30/M15 raw structure as intra-H4 location/reaction information.

These figures are session diagnostics and are not the current action ledger. They are retained to prevent repeating the same whole-frame transfer.
