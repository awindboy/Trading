# V8-001B — R1 Numerical Sequence Protocol

Status: `FROZEN BEFORE R1 RESULTS`
Date: `2026-08-30`
Representation: `V8-001A-r3 event-centered`

## Input

Use all frozen H1/M15/M5/M1 completed windows.

Price-level fields are `price - event_close_reference`.
Magnitude/meta fields remain native in the persisted representation.

Model-only optimizer scale:

- price offsets and price-unit magnitudes (ATR/std) divide by the frozen wide visual half-span for that TF;
- tick volume / spread / source-row / volume fields divide by a training-fold-only RMS computed from bars in
  the training years;
- no input feature is mean-centered, so event-close zero remains zero;
- evaluation-year data never fits the input scaler.

## Architecture

For each timeframe independently:

```text
sequence [T,F]
-> Conv1d F->24, kernel 5, stride 2
-> GELU
-> Conv1d 24->32, kernel 5, stride 2
-> GELU
-> global mean pool + global max pool
-> 64-d latent
```

Concatenate four timeframe latents plus factual event/time token, then:

```text
267-ish dims
-> Linear 128
-> GELU
-> Linear 9 path targets
```

No attention, no semantic trend/range labels, no pretrained market model.

## Targets

Nine primary raw event-centered targets:

```text
MFE / MAE / RET at 15m, 60m, 240m
```

Target values are standardized using training-fold mean/std only for optimizer conditioning; all reported
metrics are inverse-transformed back to raw GOLD price units.

## Training

```text
optimizer: AdamW
learning rate: 1e-3
weight decay: 1e-4
batch size: 256
max epochs: 8
internal validation: chronological last 15% of training rows
early-stop patience: 2
loss: SmoothL1
seed: 8001 for first diagnostic
```

The architecture/hyperparameters may not be changed after seeing Fold A merely to improve Fold B/C.

## Folds

```text
A: 2022-2023 -> 2024
B: 2022-2024 -> 2025
C: 2022-2025 -> 2026 YTD
```

The first run is a single-seed diagnostic. Claim-grade continuation requires repeating the exact frozen run
with additional seeds; a weak first run is not permission to redesign from evaluation outcomes.
