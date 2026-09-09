# V9 May 2025 Second-Pass Strategy-Compliance Replay

Date: `2026-09-09`
Classification: `RETROSPECTIVE STRATEGY-COMPLIANCE AUDIT / OUTCOME-CONTAMINATED / NOT VALIDATION`
GitHub authority HEAD checked: `147df4b74ff90135374991152a7b7338becd86ee`
Authoritative M1 SHA256 verified: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## Purpose

This replay intentionally re-trades May after the first May replay and after the month outcome is known. It is therefore not future-hidden evidence and must never replace a clean validation period. Its purpose is narrower: test whether the existing V9 strategy language can be applied in a more internally consistent and auditable way than the first May pass.

The old P039-P062 ledger remains historical evidence. This file is a separate second-pass audit and does not rewrite it.

## Frozen execution interpretation for this pass

- Parent is a working belief, never a direction veto.
- Opposite-direction Parent/Child opportunities receive symmetric consideration.
- `nearest known high/low R` is not used as an unauthorized minimum-R entry gate.
- A Child is preferred when its market role is stronger than a single reaction: repeated hold, hold+departure, meaningful repair failure, return/reuse, or actual value relocation.
- Every entry freezes a real Hard SL that invalidates the current Child.
- Hard SL is never widened; later same-direction movement never rescues a stopped Child.
- Parent-Journey positions are reviewed every completed H1, tightening to M15 when deterioration becomes material.
- Campaign exit is based on loss of progression ability, not fixed R locks, stochastic/EMA signals, or final-top/bottom prediction.
- Indicators remain shadow-only.

## April carry

P038 remains the grandfathered April carry and is not recomputed as May Hard-SL R. The May-boundary protective stop remains 3331.29. The campaign-health exit at 2025-05-01 08:59 @ 3236.67 remains a defensible carry-management decision and is kept separate from the second-pass new-entry metrics.

## Second-pass ledger

| ID | Entry time | Side | Entry | Hard SL | Scale | Exit | Exit type | R | MFE R | S |
|---|---|---|---:|---:|---|---:|---|---:|---:|---:|
| R2-01 | 2025-05-02 08:14 | LONG | 3252.63 | 3248.90 | PARENT-JOURNEY | 3248.90 | HARD SL | -1.00 | 2.60 | 29.30 |
| R2-02 | 2025-05-02 10:59 | LONG | 3258.98 | 3250.90 | PARENT-JOURNEY | 3250.90 | HARD SL | -1.00 | 1.27 | 29.30 |
| R2-03 | 2025-05-02 19:44 | SHORT | 3233.67 | 3236.50 | LOCAL BRIDGE | 3224.67 | DESTINATION | +3.18 | 3.29 | 27.75 |
| R2-04 | 2025-05-05 09:59 | LONG | 3262.11 | 3253.40 | PARENT-JOURNEY | 3381.68 | MANUAL CAMPAIGN | +13.73 | 20.17 | 26.94 |
| R2-05 | 2025-05-07 07:59 | SHORT | 3382.05 | 3388.20 | PARENT-JOURNEY | 3388.20 | HARD SL | -1.00 | 0.56 | 32.47 |
| R2-06 | 2025-05-08 07:59 | SHORT | 3382.04 | 3409.00 | PARENT-JOURNEY | 3356.08 | MANUAL CAMPAIGN | +0.96 | 2.29 | 30.50 |
| R2-07 | 2025-05-08 18:29 | SHORT | 3346.92 | 3360.50 | PARENT-JOURNEY | 3327.20 | MANUAL CAMPAIGN | +1.45 | 5.32 | 32.56 |
| R2-08 | 2025-05-12 08:59 | SHORT | 3276.11 | 3285.10 | PARENT-JOURNEY | 3233.53 | MANUAL CAMPAIGN | +4.74 | 7.61 | 32.34 |
| R2-09 | 2025-05-14 14:44 | SHORT | 3231.21 | 3239.50 | PARENT-JOURNEY | 3162.55 | MANUAL CAMPAIGN | +8.28 | 13.33 | 27.66 |
| R2-10 | 2025-05-15 13:14 | LONG | 3174.11 | 3163.80 | PARENT-JOURNEY | 3222.09 | MANUAL CAMPAIGN | +4.65 | 7.55 | 30.63 |
| R2-11 | 2025-05-20 10:59 | LONG | 3222.86 | 3207.50 | PARENT-JOURNEY | 3326.41 | MANUAL CAMPAIGN | +6.74 | 7.98 | 28.82 |
| R2-12 | 2025-05-23 06:59 | LONG | 3302.04 | 3290.50 | PARENT-JOURNEY | 3328.55 | MANUAL CAMPAIGN | +2.30 | 5.53 | 25.73 |
| R2-13 | 2025-05-27 06:59 | SHORT | 3341.21 | 3347.60 | PARENT-JOURNEY | 3321.58 | MANUAL CAMPAIGN | +3.07 | 8.80 | 20.53 |
| R2-14 | 2025-05-28 13:59 | SHORT | 3313.38 | 3325.90 | PARENT-JOURNEY | 3274.60 | MANUAL CAMPAIGN | +3.10 | 5.43 | 21.27 |
| R2-15 | 2025-05-29 13:14 | LONG | 3288.79 | 3276.00 | PARENT-JOURNEY | 3316.59 | MANUAL CAMPAIGN | +2.17 | 3.31 | 24.33 |

Descriptive result:

- Trades: **15**
- Positive: **12**
- Loss: **3**
- Net: **+51.37R**
- LONG / SHORT: **7 / 8**
- Parent-Journey / Local Bridge: **14 / 1**

These R values are M1 descriptive price-risk accounting, not exact broker Bid/Ask/slippage economics.

## Trade-by-trade audit

### R2-01 — LONG — -1.00R

- **Entry:** 2025-05-02 08:14 @ 3252.63
- **Entry reason:** May 1 하락 campaign이 약화된 뒤 May 2에 3249~3258 새 upper business가 생김. 3249 부근 hold 뒤 재출발을 LONG Child로 판단.
- **Hard SL:** 3248.90 — 3249 launch/hold 영역 상실. 3248.90 touch 시 현재 LONG Child 종료.
- **Intended scale:** PARENT-JOURNEY
- **Exit:** 2025-05-02 09:50 @ 3248.90 / HARD SL
- **Exit reason:** Hard SL touch. 이후 상승해도 이 Child는 rescue하지 않음.
- **MFE:** 2.60R

### R2-02 — LONG — -1.00R

- **Entry:** 2025-05-02 10:59 @ 3258.98
- **Entry reason:** R2-01 stop 이후 가격이 3249를 reclaim하고 3263대 새 upper business를 형성. 이전 실패와 다른 reclaim + new high가 생겨 재LONG.
- **Hard SL:** 3250.90 — reclaim 이후 유지된 3251대 hold 상실. SL 3250.90.
- **Intended scale:** PARENT-JOURNEY
- **Exit:** 2025-05-02 15:31 @ 3250.90 / HARD SL
- **Exit reason:** Hard SL touch. Parent 가능성과 별개로 retry Child 종료.
- **MFE:** 1.27R

### R2-03 — SHORT — +3.18R

- **Entry:** 2025-05-02 19:44 @ 3233.67
- **Entry reason:** 두 LONG 실패 뒤 3264→3230의 새 lower relocation, 3236 repair failure가 생김. 더 큰 Parent를 단정하지 않고 짧은 lower bridge만 거래.
- **Hard SL:** 3236.50 — 3236 repair high 복구. SL 3236.50.
- **Intended scale:** LOCAL BRIDGE
- **Exit:** 2025-05-02 19:56 @ 3224.67 / DESTINATION
- **Exit reason:** 사전 Local Bridge destination 3224.67 도달.
- **MFE:** 3.29R

### R2-04 — LONG — +13.73R

- **Entry:** 2025-05-05 09:59 @ 3262.11
- **Entry reason:** May 5 3253~3260에서 여러 시간 repeated hold, 3265 departure, 재사용/유지가 나타남. 단순 bounce가 아니라 새 upward business로 판단.
- **Hard SL:** 3253.40 — 3253~3254 repeated hold 영역 상실. SL 3253.40.
- **Intended scale:** PARENT-JOURNEY
- **Exit:** 2025-05-07 01:59 @ 3381.68 / MANUAL CAMPAIGN
- **Exit reason:** May 7 첫 H1에서 3437.81까지 favorable extreme 뒤 3380.34까지 급락, 4개 M15가 연속 adverse settlement. campaign progression materially deteriorating.
- **MFE:** 20.17R

### R2-05 — SHORT — -1.00R

- **Entry:** 2025-05-07 07:59 @ 3382.05
- **Entry reason:** R2-04 종료 뒤 upper campaign이 크게 손상. 3393 repair 뒤 lower staging을 새 SHORT Child로 시도.
- **Hard SL:** 3388.20 — 3387대 local repair reclaim. SL 3388.20.
- **Intended scale:** PARENT-JOURNEY
- **Exit:** 2025-05-07 08:44 @ 3388.20 / HARD SL
- **Exit reason:** Hard SL touch. bearish Parent 가능성은 남지만 현재 Child는 실패.
- **MFE:** 0.56R

### R2-06 — SHORT — +0.96R

- **Entry:** 2025-05-08 07:59 @ 3382.04
- **Entry reason:** R2-05 실패 이후 May 8에 3414.73까지 완전히 새로운 upper repair가 생긴 뒤 3402→3396→3382로 3개 H1 lower settlement. 독립된 failed-upper-repair Child.
- **Hard SL:** 3409.00 — 3409 이상 재수용 시 현재 lower departure Child 훼손. SL 3409.00.
- **Intended scale:** PARENT-JOURNEY
- **Exit:** 2025-05-08 15:59 @ 3356.08 / MANUAL CAMPAIGN
- **Exit reason:** 3320.25 favorable low 이후 약 6시간 새 저점 없이 3339→3342→3344→3356으로 adverse settlement와 counterflow business가 지속.
- **MFE:** 2.29R

### R2-07 — SHORT — +1.45R

- **Entry:** 2025-05-08 18:29 @ 3346.92
- **Entry reason:** R2-06 exit 뒤 repair가 3369.59까지 더 확장된 후 3360 shelf를 잃고 3346대로 급히 departure. 이전 Child와 다른 새 repair episode.
- **Hard SL:** 3360.50 — departure shelf 3360 재복구. SL 3360.50.
- **Intended scale:** PARENT-JOURNEY
- **Exit:** 2025-05-09 10:59 @ 3327.20 / MANUAL CAMPAIGN
- **Exit reason:** 3274.69 새 favorable low 뒤 여러 H1 동안 3324→3321→3325→3327로 repair settlement가 유지되어 progression 상실.
- **MFE:** 5.32R

### R2-08 — SHORT — +4.74R

- **Entry:** 2025-05-12 08:59 @ 3276.11
- **Entry reason:** 주말 뒤 gap-down 자체는 추격하지 않음. 3284.73 repair가 끝난 뒤 다시 3276대로 lower route가 재개되어 SHORT.
- **Hard SL:** 3285.10 — 3284 repair high 재복구. SL 3285.10.
- **Intended scale:** PARENT-JOURNEY
- **Exit:** 2025-05-12 15:59 @ 3233.53 / MANUAL CAMPAIGN
- **Exit reason:** 3207.69 favorable low 뒤 H1 settlement가 3224→3233으로 연속 상승, M15 counterflow도 지속. campaign deterioration.
- **MFE:** 7.61R

### R2-09 — SHORT — +8.28R

- **Entry:** 2025-05-14 14:44 @ 3231.21
- **Entry reason:** May 12~14 repair 뒤 May 14에 3229~3239 broad auction. 3239.15 upper repair가 실패하고 14:30 M15가 3231.21로 명확히 departure. role이 분명한 SHORT Child.
- **Hard SL:** 3239.50 — 3239 repair business 재복구. SL 3239.50.
- **Intended scale:** PARENT-JOURNEY
- **Exit:** 2025-05-15 11:59 @ 3162.55 / MANUAL CAMPAIGN
- **Exit reason:** 3120.69 favorable low 뒤 M15가 3140→3148→3150, retrace도 새 저점을 못 만들고 3158→3162로 다시 상승. progression 상실.
- **MFE:** 13.33R

### R2-10 — LONG — +4.65R

- **Entry:** 2025-05-15 13:14 @ 3174.11
- **Entry reason:** R2-09 exit 뒤 3120 low에서 3140~3165까지 sustained higher settlement, 3164 retest hold 뒤 3174 departure. bearish Child 종료와 별개의 새 upward Child.
- **Hard SL:** 3163.80 — 3164 retest/hold 상실. SL 3163.80.
- **Intended scale:** PARENT-JOURNEY
- **Exit:** 2025-05-16 04:59 @ 3222.09 / MANUAL CAMPAIGN
- **Exit reason:** 3252 favorable high 뒤 H1 3237→3243→3222로 adverse migration, 마지막 H1은 EMA9 아래 강한 lower settlement. upward campaign materially damaged.
- **MFE:** 7.55R

### R2-11 — LONG — +6.74R

- **Entry:** 2025-05-20 10:59 @ 3222.86
- **Entry reason:** May 20 3204~3213에서 repeated hold가 오래 지속되고 3220/3225 위로 departure. 이전 bearish route가 유지되지 못한 뒤 생긴 fresh upper business.
- **Hard SL:** 3207.50 — 3208 부근 base/reuse 상실. SL 3207.50.
- **Intended scale:** PARENT-JOURNEY
- **Exit:** 2025-05-22 09:59 @ 3326.41 / MANUAL CAMPAIGN
- **Exit reason:** 3345.42 favorable high 뒤 3338→3332→3326으로 3개 H1 lower settlement, 새 high 없음. campaign warning이 연속 확인됨.
- **MFE:** 7.98R

### R2-12 — LONG — +2.30R

- **Entry:** 2025-05-23 06:59 @ 3302.04
- **Entry reason:** May 22 급락 뒤 바로 LONG하지 않음. May 23 3290~3303에서 반복 hold 후 3303 위 initial departure가 나와 새 upward Child로 진입.
- **Hard SL:** 3290.50 — 3290~3291 base 상실. SL 3290.50.
- **Intended scale:** PARENT-JOURNEY
- **Exit:** 2025-05-26 12:59 @ 3328.55 / MANUAL CAMPAIGN
- **Exit reason:** May 23 3365.89까지 진행 후 May 26에 새 high 없이 value가 3353→3342→3337→3328로 장시간 하향 migration. Parent campaign deterioration.
- **MFE:** 5.53R

### R2-13 — SHORT — +3.07R

- **Entry:** 2025-05-27 06:59 @ 3341.21
- **Entry reason:** May 27 3349.95 high 뒤 3331 lower departure, 3347.24 repair가 다시 실패. upper repair failure를 SHORT Child로 판단.
- **Hard SL:** 3347.60 — 3347 repair high 재복구. SL 3347.60.
- **Intended scale:** PARENT-JOURNEY
- **Exit:** 2025-05-28 11:59 @ 3321.58 / MANUAL CAMPAIGN
- **Exit reason:** 3284.95 favorable low 이후 overnight repair가 이어지고 May 28 3307→3308→3319→3321로 H1 settlement가 연속 상승.
- **MFE:** 8.80R

### R2-14 — SHORT — +3.10R

- **Entry:** 2025-05-28 13:59 @ 3313.38
- **Entry reason:** R2-13 exit 뒤 repair가 3325.50까지 더 확장된 후 3319→3313으로 명확히 lower departure. 이전 실패 후 새 repair episode가 완성됨.
- **Hard SL:** 3325.90 — 3325.50 repair business 재복구. SL 3325.90.
- **Intended scale:** PARENT-JOURNEY
- **Exit:** 2025-05-29 06:59 @ 3274.60 / MANUAL CAMPAIGN
- **Exit reason:** 3245.40 new low를 만든 H1이 3263.55에 크게 되돌리고 이후 3270→3274로 settlement 상승. lower progression 상실.
- **MFE:** 5.43R

### R2-15 — LONG — +2.17R

- **Entry:** 2025-05-29 13:14 @ 3288.79
- **Entry reason:** SHORT exit 뒤 3276~3283에서 repeated hold, 3288.79로 upper departure. 단순 반등이 아니라 lower campaign 종료 후 새 upper Child.
- **Hard SL:** 3276.00 — 3276 hold/base 상실. SL 3276.00.
- **Intended scale:** PARENT-JOURNEY
- **Exit:** 2025-05-29 22:59 @ 3316.59 / MANUAL CAMPAIGN
- **Exit reason:** 3331.11 favorable high 이후 3324→3321→3316으로 3개 H1 adverse settlement, new high 없음.
- **MFE:** 3.31R

## Major no-trade decisions

- May 1 after P038 exit: downside campaign was exhausted/damaged but the opposite Parent was not yet developed; remain flat.
- May 7 after R2-05 stop through early May 8: a stopped SHORT is not rescued and the broad repair remained two-way until May 8 produced a distinct 3414 upper repair and multi-H1 lower departure.
- May 9 after R2-07 exit through the weekend: strong repair made the lower campaign ambiguous; no same-auction re-short. Wait for May 12 new lower business.
- May 16 after R2-10 exit through May 19: the sharp lower counterflow damaged the new LONG campaign, but the market remained transitional/two-way. Do not immediately flip repeatedly.
- May 22 after R2-11 exit: wait for May 23 base/hold rather than buying the first rebound.
- May 30: post-R2-15 market remained broad/two-way until a late shock; no clean completed repair/role sequence justified another Parent entry before month end.

## Comparison with first May pass

| | First pass | Second-pass compliance audit |
|---|---:|---:|
| New trades | 24 | 15 |
| Positive trades | 5 | 12 |
| Net | -6.66R | +51.37R |
| LONG / SHORT | 1 / 23 | 7 / 8 |
| Large Parent winner | none above +3.18R | +13.73R, +8.28R, +6.74R |

The second-pass result is NOT evidence that +51.37R was realistically obtainable prospectively. The full month is already known. The crucial finding is that the same high-level V9 authority permitted two dramatically different discretionary implementations.

## Main finding

The first May pass did not simply suffer bad variance. It drifted away from the stated V9 objective in several ways:

1. It became directionally asymmetric: 23 SHORT / 1 LONG.
2. `No chase` and nearest-known-memory geometry became an implicit minimum-R veto even though the authority explicitly rejects a fixed minimum-R filter.
3. A causally independent Child was often treated as sufficient pitch quality; role strength was underweighted.
4. Counterflow Children were too easily promoted into Parent route changes, especially against strong upward campaigns.
5. More than half the first-pass trades were Local Bridges or locally managed attempts, while V9's actual objective is material Parent-Journey participation.

The second pass corrects those process drifts, but its much better result creates a different problem: V9 is still too discretionary for an external reviewer to reproduce from the written rules alone.

## What must change before using another month to judge the strategy

Do not add outcome-fitted price thresholds. Instead make the discretionary decision process auditable:

- Every flat review must record Parent support, Parent damage, auction state, current Child role, and the strongest opposite-direction case.
- Every entry must explicitly state why the Child is a worthwhile pitch, not merely why it is independent.
- Add a mandatory symmetry question: `If the chart were vertically mirrored, would I accept the same evidence in the opposite direction?`
- Record `why now?` and `why not the opposite side?` before entry.
- For every rejected candidate, record which strategic requirement failed. Do not use undocumented phrases such as `already moved too much` as a veto.
- Campaign exits must cite the actual H1/M15 progression evidence that failed and whether route repair was attempted/succeeded.

This is process formalization, not market-rule formalization. It should make the AI trader inspectable without turning V9 into a threshold machine.

## Status

- First May ledger: retained as failed/biased discretionary execution evidence.
- Second May ledger: retained as retrospective compliance audit only.
- Neither May ledger is independent validation.
- Formalization gate remains closed.
- Before June, the immediate research task should be to freeze the auditable decision worksheet and then use it unchanged in a genuinely future-hidden period.