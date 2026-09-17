# V10 Advanced ML R4 — distributional / recency / model-family study

Selection rule: model family, preprocessing, hyperparameters, recency weighting and feature count were chosen using 2023/2024 walk-forward validation only. 2025/2026 are sequential OOS. Score-source (mean/q10/q50/q90) was chosen from 2024 OOS only; 2025 thresholds come from 2024 OOS scores, and 2026 thresholds from 2025 OOS scores.

## Comparison
| candidate                      |     pnl |      pf |       R |   events |   units |
|:-------------------------------|--------:|--------:|--------:|---------:|--------:|
| LiveML_R2_proxy                | 12158.9 | 1.523   | 333.04  |      976 |    1896 |
| Advanced_R2_stage_direction    | 19280.1 | 1.73552 | 383.305 |     1167 |    2173 |
| Advanced_R4_distributional     | 23704.5 | 1.75755 | 491.594 |     1336 |    2582 |
| Bounded_m3_authority_reference | 14827.6 | 1.5534  | 388.877 |     1159 |    2313 |

## R4 policy
| scope   |   events |   units |      pnl |         R |      pf |       wr |     ddR |
|:--------|---------:|--------:|---------:|----------:|--------:|---------:|--------:|
| ALL     |     1336 |    2582 | 23704.5  | 491.594   | 1.75755 | 0.388473 | 53.1072 |
| 2025    |      851 |    1655 |  9484.21 | 351.002   | 1.64605 | 0.385429 | 43.6092 |
| 2026    |      485 |     927 | 14220.3  | 140.592   | 1.85609 | 0.393814 | 53.1072 |
| LONG    |      868 |    1704 | 18608.3  | 487.716   | 2.06567 | 0.428571 | 39.5113 |
| SHORT   |      468 |     878 |  5096.23 |   3.87795 | 1.3685  | 0.314103 | 68.4306 |
| k1      |      517 |     779 |  4245.31 | 140.362   | 1.40166 | 0.365571 | 26.7829 |
| k2      |      264 |     578 |  4172.05 | 102.967   | 1.63236 | 0.359848 | 12.4765 |
| k3p     |      555 |    1225 | 15287.2  | 248.265   | 2.08234 | 0.423423 | 41.8258 |

## Selected score source
| stage   | direction   | source   |   spearman2024 |    lift2024 |
|:--------|:------------|:---------|---------------:|------------:|
| k1      | LONG        | q10      |      0.0836451 | -0.314198   |
| k1      | SHORT       | q50      |      0.170058  |  0.00513723 |
| k2      | LONG        | q50      |      0.184989  |  0.11428    |
| k2      | SHORT       | q10      |      0.243895  | -0.0649885  |
| k3p     | LONG        | q50      |      0.193853  | -0.162484   |
| k3p     | SHORT       | q50      |      0.371448  |  0.0647123  |

## Selected experts
- k1 LONG: xgb / eng / expanding / 8 features / tune rho 0.039
- k1 SHORT: cat / raw / expanding / 8 features / tune rho 0.121
- k2 LONG: xgb / raw / expanding / 8 features / tune rho 0.166
- k2 SHORT: xgb / eng / exp365 / 33 features / tune rho 0.127
- k3p LONG: lgb / eng_rank / exp730 / 16 features / tune rho 0.192
- k3p SHORT: cat / eng_rank / expanding / 8 features / tune rho 0.130

## OOS mean-model Spearman
| stage   | direction   |   year |   spearman | family   | preprocess   | recency   |   nfeat |
|:--------|:------------|-------:|-----------:|:---------|:-------------|:----------|--------:|
| k1      | LONG        |   2025 |  0.0333101 | xgb      | eng          | expanding |       8 |
| k1      | LONG        |   2026 |  0.0173554 | xgb      | eng          | expanding |       8 |
| k1      | SHORT       |   2025 |  0.112874  | cat      | raw          | expanding |       8 |
| k1      | SHORT       |   2026 |  0.151256  | cat      | raw          | expanding |       8 |
| k2      | LONG        |   2025 |  0.181833  | xgb      | raw          | expanding |       8 |
| k2      | LONG        |   2026 | -0.0553244 | xgb      | raw          | expanding |       8 |
| k2      | SHORT       |   2025 |  0.159221  | xgb      | eng          | exp365    |      33 |
| k2      | SHORT       |   2026 |  0.153229  | xgb      | eng          | exp365    |      33 |
| k3p     | LONG        |   2025 | -0.0158155 | lgb      | eng_rank     | exp730    |      16 |
| k3p     | LONG        |   2026 |  0.0617442 | lgb      | eng_rank     | exp730    |      16 |
| k3p     | SHORT       |   2025 |  0.177835  | cat      | eng_rank     | expanding |       8 |
| k3p     | SHORT       |   2026 |  0.13808   | cat      | eng_rank     | expanding |       8 |

## Right-tail concentration
|   top_n |     pnl |    share |
|--------:|--------:|---------:|
|       1 |  7505.5 | 0.316627 |
|       5 | 20807.5 | 0.877785 |
|      10 | 27051.8 | 1.14121  |