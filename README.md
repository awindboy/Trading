# Trading workspace

이 저장소는 V10 전략 연구, MT5 연구 EA, 웹 매매일지, 과거 Mentor/TradingView 도구를 함께 관리합니다. GitHub `main`이 프로젝트의 장기 기억입니다.

## 현재 전략 연구

활성 세대는 `V10` 하나입니다.

시작 순서:

1. `AGENTS.md`
2. `docs/ea/v10/AGENTS_V10.md`
3. `docs/ea/v10/V10_DOCUMENT_AUTHORITY_MAP_20260921.md`
4. `docs/ea/v10/HANDOFF_V10.md`
5. `docs/ea/v10/RESEARCH_STATE_V10.md`
6. `docs/ea/v10/V10_NEXT_RESEARCH_CONTRACT_NORMALIZED_STATE_FORWARD_20260921.md`

현재 구조:

```text
H4 FAST HA campaign clock
+ frozen R4/R5/R7G historical comparator
+ causal ATR-normalized H4/H1/M15 shadow state
-> future-only observation after 2026-08-28
```

목표는 단순한 다음 HA/방향 예측이 아니라, 반복 손절을 줄이면서 지속 추세의 큰 우측 꼬리를 보존하는 것입니다.

V10 production authority는 `NONE`입니다. R7G 결과와 두 EA는 연구·테스터 자산이며 실거래 준비 증명이 아닙니다.

## 현재 V10 자산

| 영역 | 경로 |
| --- | --- |
| 권위/상태 | `docs/ea/v10/` |
| compact result packs | `docs/ea/v10/results/` |
| 연구 코드 | `research/v10/README.md` |
| exact replay EA | `mt5/experts/V10R7G_ExactActualTickReplayEA.mq5` |
| full embedded EA | `mt5/experts/V10R7G_FullEmbeddedML_EA.mq5` |
| 파생 출력 | ignored `output/` |

## 보조 시스템

- 웹 매매일지: `src/`, `bridge/mt5_bridge.py`
- MT5 도구: `mt5/`
- TradingView 도구: `tradingview/`
- 과거 Mentor/Ground Truth 파이프라인: 비교·유지보수용이며 V10 전략 권위가 아님
- V9와 이전 세대: frozen historical evidence

## 기본 개발 검증

```powershell
npm run check-workspace
npm run build
```

V10 Python 연구 코드는 `.venv` 환경에서 compile/receipt validation을 수행합니다. 구체적인 검증 명령은 `research/v10/README.md`와 해당 checkpoint를 따릅니다.

비밀정보는 `data/mentor_ai_replay_secret.json` 등 Git 비추적 경로에만 저장합니다.
