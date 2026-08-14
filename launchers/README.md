# Launcher Index

모든 CMD는 프로젝트 루트를 작업 디렉터리로 사용합니다.

## 운영

- `TradingJournalLauncher.cmd`: 웹 서버, MT5 bridge, MT5를 함께 관리
- `Mentor_AI_Live_Shadow.cmd`: 주문 없는 live shadow 관찰기

## Mentor AI Replay V4

- `Gemini_Replay_Setup.cmd`: API 키 설정과 preflight
- `Sol_Replay_Run.cmd`: 2025-08-21 단일일 Sol 검증
- `Gemini_Replay_Run.cmd`: 동일 기간 Gemini 검증
- `Sol_Replay_Week.cmd`, `Gemini_Replay_Week.cmd`: 2025-08-18~22 주간 검증
- `Sol_Replay_High_Activity_Week.cmd`, `Gemini_Replay_High_Activity_Week.cmd`: 고활동 기간 검증
- `Gemini_Replay_Resume.cmd`: 중단된 V4 실행 재개

실행 전에 `docs/architecture/MENTOR_AI_REPLAY_V4.md`에서 현재 benchmark 지위와 제한을 확인합니다.
