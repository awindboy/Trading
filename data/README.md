# Data Directory

## Current state

- `journal.json`: 웹 매매일지의 현재 데이터
- `mentor_ai_replay_secret.json`: 로컬 API 비밀 설정, Git 제외 대상
- `mentor_ai_live_v4`: live shadow 상태와 캐시

## Backups

- `backups`: 웹 일지와 복구용 스냅샷
- `journal.*backup*.json`: 기존 루트 백업도 이 폴더로 통합

시장 원본 데이터는 현재 코드 호환성을 위해 `output/datasets`에 유지합니다. 향후 경로 마이그레이션 전에는 `scripts/mentor_ai_replay_v4.py`와 관련 도구의 기본 dataset 경로를 함께 변경해야 합니다.

백업은 현재 삭제하지 않습니다. 다음 정리 단계에서 동일 hash, 생성일, 복구 필요성을 기준으로 보존 정책을 결정합니다.
