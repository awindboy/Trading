# MT5 Bridge

`mt5_bridge.py`는 웹 매매일지와 로컬 MT5를 연결하는 HTTP 서비스입니다.

## Responsibilities

- `data/journal.json` 읽기와 저장
- EA JSONL/CSV 이벤트 병합
- MT5 history backfill
- 계좌, 포지션, chart bar, tick 조회
- 웹과 모바일이 같은 서버 저장소를 사용하도록 동기화

웹 주문 전송 기능은 현재 운영 범위가 아닙니다.

## Run

```powershell
python -m pip install -r bridge\requirements.txt
npm run mt5
```

상태 확인:

```text
http://127.0.0.1:8765/health
```

통합 운영은 `launchers/TradingJournalLauncher.cmd`를 사용합니다.
