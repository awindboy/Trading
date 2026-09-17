# V10 R4/R5 Follow-up R6 — Consolidated Research Result (2026-09-17)

## Scope and status
- GitHub SSOT HEAD used: `aa7685b9e243ddff058f0dbcdb8e416260b41244` (`update V10 R4,5`).
- R4/R5 source ledgers were byte-level SHA checked against GitHub before R6 assembly.
- Gold liquidity heterogeneity is handled with fixed sampled quarters: 2024 Q2/Q4 development, 2025 Q2/Q4 and 2026 Q1/Q2 consumed follow-up evidence.
- All 2024-2026 sampled quarters are now **consumed development evidence**. No independent validation remains in this period.
- No R6 result is promoted to V10 production authority.

## Stage 2D — Liquidity-relative representation
A trailing 92-day causal empirical percentile representation was tested within stage/direction against RAW and HYBRID inputs. Future rows were not used.

Selected by the frozen development criterion: **RAW + LogisticRegression**.

Top representation summary:
```
   rep family  mean_ap_lift  min_ap_lift  std_ap_lift  mean_recall  min_recall    mean_R     min_R  mean_stop
   RAW  LOGIT      2.065855     1.141400     0.731114     0.374239    0.222222  0.068690 -0.416555   0.443046
RANK3M  LOGIT      2.048300     1.112681     0.717825     0.333366    0.142857  0.058225 -0.352699   0.425448
HYBRID  LOGIT      1.847339     1.239317     0.611854     0.265741    0.142857 -0.035842 -0.398124   0.420212
HYBRID    HGB      1.792145     0.938800     0.855215     0.279497    0.166667  0.009123 -0.358948   0.396620
   RAW    HGB      1.716713     1.143512     0.930702     0.285317    0.142857  0.007740 -0.393898   0.407414
RANK3M    HGB      1.452385     0.963690     0.377050     0.315443    0.222222  0.062691 -0.332072   0.377133
```

Conclusion: the causal 3-month rank representation did **not** solve the regime-transfer problem. The strongest mean AP-lift remained RAW+LOGIT (2.066), while RANK3M+LOGIT was close (2.048) but not superior. Relative normalization alone is insufficient.

Notable liquidity shift example: 2026Q2 versus its prior 3-month reference showed p_stop median shift +0.413 IQR, distribution-width +0.312 IQR, q90 +0.219 IQR, EV -0.234 IQR, and stop-distance ATR -0.314 IQR. This confirms large state-distribution migration across Gold regimes.

## Stage 3 — Downside/right-tail meta integration
The compact meta used R5 EV plus a Ridge residual correction informed by causal inner-quarter right3 OOF evidence. Existing R4 q50/q75 0/1/3 semantics were retained; no new hidden threshold or risk rule was introduced.

Quarter-sampled aggregate economics:

| Policy | Structural R | PF_R | DD_R | Units | Stop-unit | Severe-unit | 3R+ child retention | 5R+ child retention |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| R4 YEAR-Q baseline | 268.58 | 1.623 | 53.11 | 1651 | 10.0% | 20.2% | 53.2% | 33.3% |
| R4 prior-quarter-Q | 262.79 | 1.576 | 50.43 | 1733 | 10.4% | 20.5% | 53.2% | 33.3% |
| R6 meta quarter-Q | 215.93 | 1.271 | 104.68 | 1834 | 31.6% | 40.6% | 67.7% | 66.7% |

The meta retained more right-tail children, but paid for them with much higher stop/severe exposure and roughly doubled DD. Its delta versus R4 YEAR-Q was -52.65R; run-block bootstrap 95% interval was [-326.69, 238.02]R.

Conclusion: **right-tail preservation alone is not enough**. The meta learned a convex-opportunity signal but failed to price downside/campaign cost reliably across regimes.

## Stage 4 — Campaign/exposure overlays
Because current authority does not define a new account-risk utility, aggregate risk budget, or 1-vs-3 utility penalty, no new campaign sizing law was invented. Two bounded overlays were tested within existing R4 semantics.

### A. Full downgrade overlay
Selected development variant: HYBRIDCTX + HGB.
- Baseline: 268.58R, PF_R 1.623, DD_R 53.11, 1651 units.
- Overlay: 158.76R, PF_R 1.871, DD_R 16.64, 696 units.
- Delta: **-109.83R**.

It cut drawdown sharply by removing exposure, but discarded too much convex payoff.

### B. Size-only downgrade (keep every selected Child; only 3→1 downgrade)
Selected development variant: HYBRIDCTX + HGB.
- Baseline: 268.58R, PF_R 1.623, DD_R 53.11, 1651 units.
- Size-only: 188.05R, PF_R 1.620, DD_R 32.70, 1069 units.
- Delta: **-80.53R**.
- 3R+/5R child retention remained unchanged because no Child was removed.

Every sampled quarter lost R under this size-only overlay. The model reduces volatility but still cannot identify which 3-unit exposures can be safely reduced without cutting the profitable tail.

## Existing R6 candidate audit under the same sampled-quarter contract
Aggregate sampled-quarter results:

| Candidate | R | PF_R | DD_R | Stop-unit | 3R+ retention | 5R+ retention |
|---|---:|---:|---:|---:|---:|---:|
| R4 | 268.58 | 1.623 | 53.11 | 10.0% | 53.2% | 33.3% |
| R6D_ROLE_HYBRID | 240.66 | 1.553 | 54.93 | 11.2% | 45.2% | 23.8% |
| R6C_META_CLS | 235.57 | 1.545 | 51.30 | 12.1% | 41.9% | 23.8% |
| R6E_SPECIALIST_META | 221.14 | 1.419 | 60.14 | 17.0% | 51.6% | 42.9% |
| R6F_RESIDUAL | 190.17 | 1.233 | 98.12 | 19.0% | 56.5% | 28.6% |
| R6B_STAGE_META | 158.87 | 1.360 | 66.63 | 13.1% | 37.1% | 19.0% |


No R6B-R6F candidate beats the R4 sampled-quarter baseline. R6D_ROLE_HYBRID is the closest on R, but still trails and has slightly worse DD. R6F captures more right-tail children but materially increases stop exposure and DD.

## Final research conclusion
1. **Direct realized-R meta regression is the wrong objective.** It mostly learns STOP avoidance and loses the right tail.
2. **Standalone right3 classification is also insufficient.** 2024-selected HGB did not generalize across 2025/2026 quarter regimes.
3. **Simple causal relative-ranking does not fix Gold liquidity migration.** The 92-day rank view did not outperform raw evidence.
4. **Specialist stacking has signal but not stable economic interpretation.** It can identify convex opportunity in some regimes, but downside pricing and exposure control remain unstable.
5. **Campaign-aware sizing cannot be solved by a generic 3→1 downgrade score.** It reduces DD only by sacrificing too much R.
6. **R4 remains the best current R4/R5-family research baseline under the fixed sampled-quarter contract.** This is a research conclusion, not a production promotion.

## What should be researched next
The evidence points away from another model-family/hyperparameter scan. The next justified research contract should focus on **explicit regime-conditioned calibration / mixture-of-experts**, where Gold liquidity state is represented as a causal context variable and specialist mappings are allowed to differ by regime without using future outcomes. Required safeguards:
- regime/context representation must be causal and selected only from prior evidence;
- no hard LONG/SHORT balancing or hidden thresholds;
- stage/direction specialists remain separate where evidence supports it;
- calibration should be evaluated per sampled quarter and worst-quarter, not pooled only;
- right-tail retention and short-run damage must remain simultaneous guardrails;
- a new untouched validation slice/market is required before any authority promotion.

2021 GOLD remains untouched under the current authority unless a separate frozen validation contract explicitly releases it.
