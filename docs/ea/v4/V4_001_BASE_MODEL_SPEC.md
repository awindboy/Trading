# V4-001 Base Model Specification — `V4_001_CausalPatchPolicy`

Status: `FROZEN BASELINE ARCHITECTURE FOR DEVELOPMENT`
Date: `2026-08-27`

## 1. Design objective

The first V4 model is intentionally small and inspectable.
The frozen 14-feature configuration contains **383,820 trainable parameters** in the current implementation.
It must be expressive enough to learn multi-scale and cross-market interactions without being so large that
parameter count, GPU budget or optimizer search becomes the dominant research variable.

The design borrows two general time-series ideas without importing a pre-trained trading ontology:
- patch tokenization for long causal histories;
- attention fusion for interactions among time scales and markets.

## 2. Input tensor organization

For each target decision at time `t`, load every available development context market with a binary target flag.
The local encoder is shared across symbols and receives **no learned symbol identity**.
This is deliberate: the first model must be capable of being evaluated on an unseen target symbol later.

Streams:

| Timeframe | Completed bars | Patch size | Max patch tokens |
| --- | ---: | ---: | ---: |
| M1 | 256 | 8 | 32 |
| M5 | 192 | 6 | 32 |
| M30 | 96 | 4 | 24 |
| H4 | 42 | 3 | 14 |

Each stream also carries:
- valid/padding mask;
- age in minutes of the newest completed bar at decision time.

## 3. Local stream encoder

Per timeframe:

```text
[patch_len x features]
-> flatten
-> Linear(d_model=64)
-> LayerNorm
-> positional embedding
-> 2-layer TransformerEncoder
   heads=4
   feedforward=128
   GELU
   dropout=0.10
-> masked mean pool
```

Weights are shared across markets for a given timeframe.
This forces the model to learn transferable sequence motifs rather than a separate neural strategy for each symbol.

## 4. Cross-market/timeframe fusion

Every market/timeframe pooled vector becomes one token.
Add:
- learned timeframe embedding;
- learned target/non-target embedding;
- MLP embedding of log stream age.

Then:

```text
all stream tokens
-> 2-layer TransformerEncoder
   d_model=64
   heads=4
   feedforward=128
-> target-token mean + global-token mean
-> fusion MLP
-> latent z_t (128)
```

There is no symbol embedding in V4-001.

## 5. Distributional heads

For horizons `[15,60,240]` minutes:

```text
return_mu_norm       3 outputs
return_log_scale     3 outputs
direction_logit      3 outputs
abs_return_norm      3 outputs
```

Loss:

```text
1.0 * Gaussian NLL(normalized future return)
0.5 * BCE(direction)
0.25 * SmoothL1(normalized absolute return)
```

Loss weights are frozen baseline constants. They are not selected from P/L.

## 6. Optimization baseline

```text
optimizer       AdamW
learning rate   3e-4
weight decay    1e-4
batch size      256 target (reduce only for memory)
epoch cap       30
early stopping  validation NLL patience 5
grad clip       1.0
seeds           17, 29, 43
```

If the GPU cannot hold batch 256, use gradient accumulation to preserve effective batch size where practical.
A hardware-driven batch reduction is not a strategy parameter change.

## 7. Normalization

Per symbol/timeframe use only causal rolling/EWM statistics.
Do not standardize using the whole training year or whole file when an online-equivalent causal transform exists.

Primary causal scale:

```text
EWM std of log returns, span 256 bars for that timeframe
```

Tick volume:

```text
log1p(tick_volume)
-> causal EWM z-score
```

## 8. Why no symbol embedding

A learned symbol ID can let the network memorize market-specific biases.
The first cross-market question is whether one representation transfers.
Therefore symbol identity is withheld from the base model.

If later evidence shows stable market-conditional behavior, market metadata may be introduced as a separate
ablation after the no-ID baseline is recorded.

## 9. Why no RL yet

The model first answers:

```text
Does z_t carry stable information?
```

The first controller then answers:

```text
Is that information economically useful after spread?
```

Only after both questions have evidence should sequential credit assignment be introduced.

## 10. First ablations after baseline result

Allowed only after the base result is immutable:

1. target-only vs cross-market context;
2. remove H4;
3. remove M1;
4. remove tick volume;
5. optional masked-patch self-supervised pretraining.

Do not run a large architecture sweep before these causal ablations.
