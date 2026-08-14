# Trading Workspace

이 작업공간은 웹 매매일지, MT5/TradingView 도구, 스승님식 매매 연구와
Mentor AI 재생 파이프라인을 함께 관리합니다.

새 Codex 세션은 다음 순서로 시작합니다.

1. `AGENTS.md`: 유일한 전략 실행 계약
2. `PROJECT_MANIFEST.json`: 현재 활성 코드와 검증 명령
3. `docs/architecture/MENTOR_AI_GROUND_TRUTH_V2.md`: 현재 파이프라인 경계
4. 작업 대상 하위 폴더의 `README.md`

## 현재 승인 상태

- 전략 권한: `AGENTS.md`
- 파이프라인: `4.51-ground-truth-v2`
- Ground Truth V2: `output/ground_truth_v2_june2026_v451` 완료 판정 무효화
- 현재 상태: 동적 objective 갱신 누락이 확인되어 `BLOCKED`; 기존 2건과
  `+0.1293R`은 참고용 forensic 결과일 뿐 정답지가 아님
- 최신 감사 상태: `docs/operations/GROUND_TRUTH_V2_CURRENT_STATUS.md`
- Gemini 6월 재현: 동결 정답지 기준 비교 가능, 아직 재현 성공 판정 전
- Live: 공통 closed-M1 엔진과 shadow 경로 검증 완료, 실제 shadow parity 미실행
- DEMO: fake MT5 adapter 검증 완료, 실제 DEMO 체결 미실행
- 실계좌 주문: 하드 차단
- `archive/`와 과거 `output/`은 전략 권한이나 정답지가 아님

## 활성 경로

| 영역 | 시작 파일 |
| --- | --- |
| 전략 계약 | `AGENTS.md` |
| Ground Truth V2 | `scripts/build_ground_truth_v2.py` |
| Gemini replay | `scripts/mentor_ai_replay_v4.py` |
| 공통 사건 엔진 | `scripts/mentor_replay_v4_core.py` |
| Live shadow | `scripts/mentor_ai_live_v4.py` |
| 생성된 Gemini 계약 | `mentor_context_pack/api_contracts/` |
| 웹 매매일지 | `src/`, `bridge/mt5_bridge.py` |
| MT5 도구 | `mt5/` |
| TradingView 지표 | `tradingview/` |

## 핵심 검증

```powershell
python scripts\build_mentor_api_contracts.py
python scripts\test_mentor_ai_replay_v4.py
python scripts\test_mentor_ai_live_v4.py
python scripts\test_ground_truth_v2_integration.py
python -m py_compile scripts\mentor_replay_v4_core.py scripts\mentor_ai_replay_v4.py scripts\mentor_ai_live_v4.py scripts\build_ground_truth_v2.py
```

Ground Truth discovery는 후보 원장만 생성하고 blocked 상태로 끝납니다. chronological,
counterfactual shuffled, daily no-trade MTF, trigger-role 감사를 모두 완료한 뒤에만
`finalize`할 수 있습니다. 현재 동결본의 완료 근거는 해당 폴더의 `manifest.json`과
`accepted_ground_truth.jsonl`입니다.

## 웹 매매일지

```powershell
npm install
npm run dev
```

기본 주소는 `http://127.0.0.1:5173/`입니다.

API 키는 `data/mentor_ai_replay_secret.json`에만 저장하며 외부 저장소에 올리지 않습니다.
