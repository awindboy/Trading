# Scripts Index

현재 자동화 연구의 활성 기준은 `AGENTS.md`와 Ground Truth V2 파이프라인이다.
이름만 보고 구형 replay 스크립트를 실행하지 말고 아래 활성 경로를 사용한다.

## Ground Truth V2 / Mentor Replay V5

- `build_mentor_api_contracts.py`: `AGENTS.md`에서 활성 Gemini 계약과 coverage matrix 생성
- `build_ground_truth_v2.py`: raw M1 사건 원장, 후보 패킷, 3중 감사 큐 생성 및 최종 동결
- `mentor_replay_v4_core.py`: replay/live 공통 시장·상태 코어 (`5.0-ground-truth-v2`)
- `mentor_ai_replay_v4.py`: Gemini 및 scripted-provider replay orchestration
- `mentor_ai_live_v4.py`: 동일 closed-M1 orchestration을 사용하는 shadow observer
- `test_ground_truth_v2_integration.py`: objective family, multi-lane, risk, latency 통합 검사
- `test_mentor_ai_replay_v4.py`, `test_mentor_ai_live_v4.py`: replay/live 회귀 검사

Ground Truth 후보 생성은 완료가 아니다. `BLOCKED_REPORT.md`가 있으면 3중 의미 감사를
마치지 않은 상태이며 Gemini 성능이나 수익성의 기준으로 사용할 수 없다.

Python import 호환성을 위해 파일은 현재 한 디렉터리에 유지합니다. 이름만 보고 실행하지 말고 아래 분류를 따릅니다.

## 현재 Mentor AI Replay V4

- `mentor_ai_replay_v4.py`: CLI와 replay orchestration
- `mentor_replay_v4_core.py`: 데이터, 상태, 로컬 사건 처리
- `mentor_ai_live_v4.py`: MT5 closed-M1 shadow observer
- `gemini_replay_provider.py`: Gemini structured response provider
- `codex_replay_provider.py`: Codex CLI provider
- `manual_replay_provider.py`: 수동 provider
- `mt5_rate_source.py`: MT5 데이터와 symbol specification
- `test_mentor_ai_replay_v4.py`, `test_mentor_ai_live_v4.py`: 현재 회귀 검사
- `audit_oct20_24_legacy_truth.py`: 최근 legacy benchmark 감사 도구

## 웹 일지와 MT5 운영

- `trading_journal_launcher.py`
- `install_mt5_ea.py`, `install_mt5_indicator.py`
- `check_mt5_journal_pipeline.py`, `watch_mt5_journal_pipeline.py`
- `test_ea_event_pipeline.py`
- `generate_ai_trade_feedback.py`, `import_mentor_feedback_to_journal.py`

## TradingView

- `check_pine_static.py`

## Workspace maintenance

- `check_workspace_structure.py`: 루트와 활성 output 분류가 다시 흐트러졌는지 검사

## 연구 및 레거시

그 밖의 `build_*`, `run_mentor_*`, 이전 replay, reverse-engineering, manual-ground-truth 스크립트는 연구 재현용입니다. 현재 V4의 진입점이나 매매 권한으로 사용하지 않습니다. 관련 산출물은 대부분 `archive/outputs/legacy`에 있습니다.

레거시 스크립트를 실행하려면 먼저 해당 코드의 `ROOT / "output" / ...` 경로가 archive 이동으로 깨졌는지 확인해야 합니다.
