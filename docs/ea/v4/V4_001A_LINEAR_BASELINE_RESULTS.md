# V4-001A — Prepared Dataset and Frozen Linear Baseline

Status: `COMPLETE DEVELOPMENT CONTROL / NEURAL STAGE-A NOT YET RUN OFFICIALLY`
Date: `2026-08-27`

## 1. Development data preparation

The four already-open development markets were prepared with the frozen V4-001 causal feature builder.
No external validation-vault market was opened.

| Symbol | M1 rows | 15m decision labels | 2023 | 2024 | 2025 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GOLD# | 1,058,802 | 63,015 | 21,015 | 21,056 | 20,944 |
| BTCUSD# | 1,571,009 | 103,841 | 34,583 | 34,705 | 34,553 |
| XAUEUR# | 1,058,885 | 62,893 | 20,875 | 21,105 | 20,913 |
| USDJPY# | 1,113,194 | 71,596 | 23,884 | 23,947 | 23,765 |
| **Total** | **4,801,890** | **301,345** | **100,357** | **100,813** | **100,175** |

Prepared store size in the research runtime was approximately 381 MB.

Raw-file hashes and symbol point specifications are recorded in `V4_001A_PREPARED_DATA_MANIFEST.json`.

## 2. Label balance

The 15-minute direction target is close to balanced rather than a trivial majority-class problem.
Annual up-frequency was generally around 49%-52% across markets.

Therefore AUC remains the primary discrimination metric.

## 3. Linear baseline definition

Frozen by `V4_001A_STAGE_A_EXECUTION_PROTOCOL.md`.

Feature dimension:

```text
344
```

No symbol ID, Candidate A, sweep, FVG, BOS/owner or H/L field is included.

## 4. Temporal results

| Fold | Train N | Eval N | AUC15 |
| --- | ---: | ---: | ---: |
| train 2023 -> eval 2024 | 100,357 | 100,813 | **0.51651** |
| train 2023-2024 -> eval 2025 | 201,170 | 100,175 | **0.51153** |

These small AUC values are not trading authority. They establish that a cheap linear summary of the V4 causal
inputs already extracts a weak but non-zero development signal that the neural model must beat.

## 5. Strict future-isolated leave-one-market-out results

Training excludes the held-out market entirely and uses the other three markets in 2023-2024. Evaluation is the
held-out market in 2025.

| Held-out target | Train N | Eval N | Linear AUC15 |
| --- | ---: | ---: | ---: |
| GOLD# | 159,099 | 20,944 | **0.50980** |
| BTCUSD# | 131,882 | 34,553 | **0.50265** |
| XAUEUR# | 159,190 | 20,913 | **0.51064** |
| USDJPY# | 153,339 | 23,765 | **0.50721** |

These four values are frozen before the authoritative neural Stage-A run and are used by the Stage-A verdict
script. They may not be changed because the neural model narrowly misses them.

## 6. Same-period LOMO disposition

An earlier development calculation considered training on other markets over the same 2023-2025 calendar span
as the held-out market. It is **not used in the primary Stage-A gate**.

Reason: for correlated markets, training labels from the exact same future event interval weaken the meaning of
"independent market transfer." The stricter 2023-2024 -> held-out-2025 fold was frozen instead before the
authoritative neural outcome.

## 7. Neural status

A tiny CPU-only diagnostic was run solely to prove the leakage-safe runner executes end-to-end. It used only
800 fit samples, 200 inner-validation samples, 200 outer samples, one seed and one epoch.

Classification:

```text
DIAGNOSTIC / NON-AUTHORITY
```

Its performance must not be compared with the full baseline or used to alter the architecture.

The full official three-seed Stage-A run remains pending on CUDA-capable compute.
