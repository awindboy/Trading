# Trading workspace

이 저장소는 V13 전략 연구, 과거 V10–V12 증거, MT5 EA/지표와 재현 가능한
연구 산출물을 관리합니다. GitHub `main`이 프로젝트의 장기 기억입니다.

## 현재 전략 연구

활성 세대는 `V13` 하나입니다. V12 이하는 역사적 증거입니다.

시작 순서:

1. `AGENTS.md`
2. `docs/ea/v13/AGENTS_V13.md`
3. `docs/ea/v13/V13_DOCUMENT_AUTHORITY_MAP_20260926.md`
4. `docs/ea/v13/V13_OBJECTIVE_AND_EVALUATION_UPDATE_20260928.md`
5. `docs/ea/v13/HANDOFF_V13.md`
6. `docs/ea/v13/RESEARCH_STATE_V13.md`
7. `docs/ea/v13/V13_LTF_ROUTE_Q75_Q50_ACTION_CONTRACT_20260929.md`
8. `docs/ea/v13/results/V13_LTF_ROUTE_Q75_Q50_RESEARCH_RECEIPT_20260929.md`
9. `docs/ea/v13/V13_LTF_ROUTE_Q75_Q50_MQL5_VALIDATION_PROTOCOL_20260929.md`
10. `docs/ea/v13/results/V13_LTF_ROUTE_Q75_Q50_ACTUAL_TICK_REPLAY_RECEIPT_20260929.md`

현재 구조:

```text
H4 standard HA = Parent/Journey와 unchanged Child #1
M30 correction + fresh M15 POI = replacement LTF Child clock
causal M30/H1 destinations = forward route
strict-prior OOF q75 hurdle EV = fixed-size admission
first destination delivery = proof, not TP
strict-prior OOF q50 = first damaged-correction repair permission
policy ledger + actual ticks = execution/economic verification
```

SA-1은 현재 ordinary-quality actual-tick 비교 기준입니다. 중단된 세션의
정확한 q50 원장은 남지 않았지만, 같은 정의로 만든 Reconstruction A는
1,477개 거래/2,954개 action의 actual-tick parity를 통과했습니다. 결과는
`+$4,461.37`, PF `1.301`이지만 SA-1보다 손실 횟수·승률·연속 손실·노출이
나빠 승격하지 않았습니다. 현재 EA는 동결된 정책 원장을 실행하는 replay
harness이며 ML을 내장한 production EA가 아닙니다.

## 주요 자산

| 영역 | 경로 |
| --- | --- |
| V13 권위/상태 | `docs/ea/v13/` |
| V13 결과/원장 | `docs/ea/v13/results/` |
| V13 연구 코드 | `research/v13/` |
| frozen comparator EA | `mt5/experts/V13HAOnlyMax10EA.mq5` |
| SA-1 actual-tick reference EA | `mt5/experts/V13SA1CleanContinuationEA.mq5` |
| q75/q50 policy replay EA | `mt5/experts/V13LTFRouteQ75Q50_PolicyReplayEA.mq5` |
| 과거 V10–V12 | `docs/ea/v10/`, `docs/ea/v11/`, `docs/ea/v12/` |
| 파생 출력 | ignored `output/` |

MQL5 공식 경제 검증은 `Every tick based on real ticks`와 Journal event
parity를 모두 요구합니다. 소스 컴파일 성공만으로 전략 성과나 실거래
준비 상태를 주장하지 않습니다.
