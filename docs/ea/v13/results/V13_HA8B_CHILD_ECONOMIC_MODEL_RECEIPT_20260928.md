# V13 HA-8B — Child marginal-economics ML receipt

Date: `2026-09-28`
Status: `CONSUMED DEVELOPMENT / CHRONOLOGICAL OOF OBSERVATION / NO EA OR ACTION AUTHORITY`
Frozen-before-run contract: `../V13_HA8B_CHILD_ECONOMIC_MODEL_CONTRACT_20260928.md`
Source: `research/v13/ha8b_child_economic_model.py`
Local generated audit: `output/v13_ha8b_child_economic_20260928/` (not Git)
GitHub main checked before the run: `29e0073e57553d8fe1fd14b843daf09164a7a248`

## Direct answer

The economic target matters. A three-head, regularized linear model using
current Child/previous-Journey state and previously audited HA context produced
a **development lead for add-on Child value ranking** that HA-8A's reversal
score did not: its lowest estimated-value fifth contained 330 losses and 142
wins, with **-2,256.50 GOLD price points** in 472 add-on
Children. But it still contained +5,266.46 gross winning points, including
+1,695.52 in 87 long-Journey Children, and the Journey-cluster bootstrap
interval for its mean includes zero. Its overall loss Brier and marginal-value
MAE were **worse** than the simpler H4/H1 model. This is not a validated veto,
profit improvement, or a reason to resize the EA.

The primary *repeated losing Journey* problem remains unsolved at birth: the
same full linear model's lowest-value 156 first Children contained only 64 of
442 OOF repeat-losing Journeys and were net **+324.43** points. The position-
state-only linear variant put 114 losing and 42 winning first Children in its
lowest fifth, but just 55/442 repeat-losing Journeys. A Child-loss selector is
not automatically a repeat-loss Journey selector.

## Causal/source audit

- HA-8B input ledger was written/hashed before terminal labels were loaded.
  `--build-features` streamed the source rows and raw H4 range prefix;
  `--evaluate` separately built economic labels after verifying the hash.
- Input rows: 4,108, strictly increasing by signal and actual `known_at`.
  SHA256 feature ledger:
  `aa4741232de258e9ae33851524373996d3c869c4f5f33f180f8cd2b6b7e96e93`.
  H4 source SHA256:
  `b080fb5463df1f80592cfeeecacc4d422069b69ac40635b912d03d97873aecbf`.
- Baseline-0 parity: 965 closed Journeys, 3,858 closed Children, +8,147.11
  idealized GOLD price points. Every Child terminal point PnL matched the
  independent HA-8A child-economic ledger: 3,858/3,858, maximum difference 0.
- OOF: 3,134 Children from 778 unique Journeys (778 births and 2,356 add-ons).
  Fold training used only Journeys whose exit had become known before the
  first test decision; training Journey counts were 186/378/546/724 across
  the four expanding folds. Labels for 3/3/4/1 earlier Children respectively
  were unavailable at the fold boundary and were excluded from fitting.
- HA-8B uses **actual decision `known_at`** for fold assignment. X2 used H4
  signal time and thus had 777 OOF births; HA-8B additionally includes
  Journey 188, signaled 2024-06-28 20:00 but first executable/known at
  2024-07-01 01:00. Those populations must not be compared as identical.
- The current-open price is known at the decision and is used only to compute
  live/reference position PnL and the later outcome label. No absolute price,
  year, Journey ID, outcome, or final Journey length is a model input.
  Preprocessing is fitted in each training fold only. Four regression tests
  passed, including prior-20 range and input-whitelist checks. Rebuilding
  features produced the same hash.

## Predictive score versus economic ranking

`P(loss)` Brier lower is better. Marginal-value MAE is in the normalized
prior-20-H4-range coordinate, not GOLD points. The low-value group is a
**retrospective OOF rank bucket**, not a causal trade filter. Models were
predeclared; the table does not select a winner.

| Frozen model | Loss Brier | Loss AUC | Value MAE | Add-on lowest 20% losses/wins | Add-on low net points |
| --- | ---: | ---: | ---: | ---: | ---: |
| Child-stage historical mean | 0.23962 | 0.5118 | 1.07566 | rank undefined on tied scores | — |
| Linear H4/H1 | **0.23632** | 0.5694 | **1.07417** | 319 / 153 | +961.76 |
| Linear + position history | 0.23654 | 0.5664 | 1.07645 | 326 / 146 | -1,764.22 |
| Linear + measured context | 0.23723 | 0.5673 | 1.08126 | 330 / 142 | -2,256.50 |
| Shallow H4/H1 | 0.23752 | 0.5723 | 1.08246 | 325 / 147 | -632.34 |
| Shallow + position history | 0.24143 | 0.5619 | 1.09516 | 292 / 180 | -432.23 |
| Shallow + measured context | 0.24004 | 0.5657 | 1.10186 | 302 / 170 | -1,822.80 |

The add-on OOF population had 1,420 losses, 935 wins, one flat and +6,489.18
net points. The full linear model's lowest fifth captured **330/1,420 =
23.2% of losses** and **142/935 = 15.2% of winners**. This improves economic
concentration over HA-8A's flip-risk fifth (20.2% / 19.7%), but the HA-8A
and HA-8B OOF populations differ slightly and this is only a diagnostic,
not a head-to-head economic strategy comparison.

For that full linear low-value fifth: gross winners +5,266.46, gross losers
-7,522.96, net -2,256.50 points across 204 Journeys. Its 87 >=10-bar
Journey Children contributed **+1,695.52** points; 10 Children in the
ten highest-profit Journeys contributed **+2,272.61**. A veto would lose
those winners. The worst five selected Journeys contributed -1,767.10,
and the best five +2,588.50, so episode concentration is substantial.
Journey-cluster bootstrap 95% descriptive interval for the group's mean GOLD
points per Child was about **-12.25 to +5.66**, crossing zero. This is not
independent future validation or a formal trade-edge confidence interval.

Per-fold lowest-fifth add-on net points, ranked separately **within each
future test fold for description only**:

| Model | 2024-H2 | 2025-H1 | 2025-H2 | 2026 to cutoff |
| --- | ---: | ---: | ---: | ---: |
| Linear H4/H1 | -195.1 | -525.2 | -1,010.9 | +149.2 |
| Linear + position history | -196.1 | -642.1 | -1,032.1 | -1,554.8 |
| Linear + measured context | -8.4 | -446.4 | -886.9 | -995.1 |
| Shallow + measured context | -173.8 | +405.9 | +268.7 | -1,939.1 |

These fold buckets do **not** sum to the pooled lowest-fifth bucket: each
fold has its own retrospective ranking and fixed ~20% size. No score cutoff
was available causally from these future fold distributions. The shallow
family is less stable than the linear family. The full linear loss Brier
improved on the stage mean in 2024-H2 and both 2025 folds, but worsened in
2026 (`0.24337` versus `0.23718`); it did not earn reliable probability
calibration. The separate long-Journey classifier had pooled AUC 0.8014,
but much of this is mechanical at late Child ages: at Child #1 AUC was only
0.6618, and that head was never an action guard.

## What this establishes and does not

The **new information dimension with the clearest economic effect** was
causally known position/previous-Journey state, not a more complex estimator:
linear + position history made the weak add-on score bucket net-negative in
the consumed OOF sample, while the shallow model degraded aggregate metrics.
The measured HA context sharpened the pooled low-value add-on bucket but
weakened overall calibration and was nearly neutral in 2024-H2.

This result does **not** solve repeat-loss Journey admission. It also does not
justify dropping 20% of Children, raising risk, or calling +2,256.50 an
implementable profit gain. The bucket is retrospective, gross/idealized,
and price-point-only. A filtered strategy would alter actual position state;
any later action variant must maintain an explicit **shadow Baseline-0**
position history if it wants these exact features, and must preserve the
original ten-slot horizon. The exact-window real-tick MT5 Baseline-0 economic
receipt remains pending. No HA-8B model, threshold, exit or sizing change is
promoted. No EA file changed.

Next legitimate questions are distinct: (1) a predeclared, executable,
past-calibrated add-on admission policy with shadow-state parity and real-tick
economics, and (2) a separately contracted, Journey-birth model explicitly
targeting **repeat loss after a losing Journey**. The current 2024-2026
history is already consumed; both require untouched future validation before
strong authority.
