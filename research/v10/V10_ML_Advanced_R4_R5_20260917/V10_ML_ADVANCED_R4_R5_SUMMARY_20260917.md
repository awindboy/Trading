# V10 Advanced ML R4/R5 Research — 2026-09-17

## Selection boundary
- Model family, preprocessing, hyperparameters, recency weighting, and feature count: selected from 2023/2024 walk-forward only.
- 2025/2026: sequential OOS evaluation.
- 2025 policy thresholds: previous 2024 OOS score distribution.
- 2026 policy thresholds: previous 2025 OOS score distribution.
- No future final-run length or future trade outcome is used as a live feature.

## R4 distributional candidate
- 1,336 selected events / 2,582 units
- PnL +23,704.51
- PF 1.7575
- weighted structural R +491.59R
- sequential R DD 53.11R
- LONG: +18,608.28 / PF 2.066 / +487.72R
- SHORT: +5,096.23 / PF 1.369 / +3.88R
- k1: +4,245.31 / PF 1.402 / +140.36R
- k2: +4,172.05 / PF 1.632 / +102.97R
- k3+: +15,287.15 / PF 2.082 / +248.27R

## Important guardrail result
- L1-2: -10,096.95 / -256.06R
- L3-5: -8,454.39 / -145.24R
- L6-8: +7,167.89 / +226.03R
- L9-11: +15,519.61 / +269.20R
- L12+: +19,568.35 / +397.66R
- Top 1 profitable run = 31.7% of total net PnL; top 5 = 87.8%.

The candidate improves aggregate economics but remains highly right-tail dependent and does not solve short-run chop.

## Preprocessing/model specialization selected
- k1 LONG: XGBoost / engineered / expanding / 8 features
- k1 SHORT: CatBoost / raw / expanding / 8 features
- k2 LONG: XGBoost / raw / expanding / 8 features
- k2 SHORT: XGBoost / engineered / exp-365 recency / 33 features
- k3+ LONG: LightGBM / engineered + causal rank / exp-730 / 16 features
- k3+ SHORT: CatBoost / engineered + causal rank / expanding / 8 features

No single model family or preprocessing dominated all jobs.

## Distribution modeling finding
Standard q10/q50/q90 regression is structurally mismatched to R because Hard-SL outcomes create a discrete mass at R=-1. Stop rates are commonly ~18-33%, so a nominal q10 can correctly sit at the -1 floor while empirical P(R<=q10) is far above 10%.

This motivated R5 hurdle/mixture modeling:
P(stop) + E[R | no stop].

Stop prediction was strong (pre-2025 tuning AUC roughly 0.71-0.86), but using stop avoidance as the main ranking signal reduced economics. R5 mixture policy: +21,572.90 / PF 1.677 / +320.65R. This confirms that predictable stop risk is not the same as economic value.

## Semantic hard-veto finding
Applying prior-only extreme severe / low-survival / low-persistence vetoes on top of R4 did not improve the candidate. Broad survival/persistence vetoes reduced R materially while only modestly reducing DD. These heads should remain contextual inputs, not hard gates.
