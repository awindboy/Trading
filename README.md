# Trading workspace

이 저장소는 V12 CRT hybrid 연구, V11 Wave Candle 관찰 자산, V10 HA/ML
비교 자산, MT5 도구, 웹 매매일지를 관리합니다. GitHub `main`이 프로젝트의
장기 기억입니다.

## 현재 전략 연구

활성 세대는 `V12` 하나입니다.

시작 순서:

1. `AGENTS.md`
2. `docs/ea/v12/AGENTS_V12.md`
3. `docs/ea/v12/V12_DOCUMENT_AUTHORITY_MAP_20260923.md`
4. `docs/ea/v12/HANDOFF_V12.md`
5. `docs/ea/v12/RESEARCH_STATE_V12.md`
6. `docs/ea/v12/V12_ORIGIN_AND_CRT_HYBRID_THESIS_20260923.md`
7. `docs/ea/v12/V12_CRT_NUMERIC_OBSERVATION_CONTRACT_20260923.md`
8. `docs/ea/v12/V12_MQL5_ENGINEERING_AND_VALIDATION_CONTRACT_20260923.md`

현재 구조:

```text
CRT = candidate / Parent-journey state
HA + Wave + liquidity = candidate observations
ML = shadow-only conditional outcome estimates
raw M1 causal replay = research oracle
MQL5 ledger parity + actual ticks = implementation/economic verification
```

첫 공식 레인은 `W1 -> H4`와 `D1 -> H1`입니다. `H4 -> M15/M5`는 별도
shadow 탐구이며 아직 로메오 규칙도, V12 매매 규칙도 아닙니다.

V12의 trade authority와 production authority는 모두 `NONE`입니다. 아직
V12 EA, 검증된 진입 모델, 성과 결과는 없습니다.

## 주요 자산

| 영역 | 경로 |
| --- | --- |
| V12 권위/상태 | `docs/ea/v12/` |
| V12 연구 계약/스키마 | `research/v12/` |
| V11 종료 기록 | `docs/ea/v11/` |
| V11 Wave Candle | `mt5/indicators/V11WaveCandle.mq5` |
| frozen V10 comparator | `docs/ea/v10/`, `research/v10/README.md` |
| 파생 출력 | ignored `output/` |

## 기본 검증

```powershell
npm run check-workspace
npm run build
python research/v12/validate_v12_event_schema.py
```

비밀정보는 `data/mentor_ai_replay_secret.json` 등 Git 비추적 경로에만
저장합니다.
