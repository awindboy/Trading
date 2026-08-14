# Mentor AI Replay Architecture V3

## 목적

Gemini가 `AGENTS.md`의 스승님식 판단 절차를 과거 GOLD 차트에서 미래 데이터 없이 재현하는지 검증한다. 이 파이프라인은 수익성이나 실거래 승인을 증명하지 않으며 MT5 주문도 전송하지 않는다.

## 권한 분리

### 로컬 엔진

- M1 NPZ를 읽고 H1/M30/M15/M5/M1 확정봉을 생성한다.
- 모든 봉은 실제로 알 수 있게 된 시각 이후에만 제공한다.
- 압축 봉에 `TF:openEpoch` 형식의 고정 `barId`를 붙인다.
- 모델이 선택한 `barId`를 원본 OHLC로 해석한다. 모델이 임의 가격을 만들 수 없다.
- watch event까지 빠르게 재생하고 limit 체결, Bid/Ask spread, SL/TP 결과를 판정한다.
- 결정 원장과 사용량을 append-only hash chain으로 기록한다.

로컬 엔진의 MAP activity detector는 M5의 큰 몸통 구조 전달과 직전 확정 M15 반대색 캔들을 이용해 **API 호출 시점만 알린다**. 이것은 OB·방향·objective 판정이 아니며 주문 권한도 없다.

### Gemini

- Lite 모델은 `MAP_SCOUT`에서 root OB/objective 후보만 최대 3개 제출한다.
- reviewer 모델은 `MAP_REVIEW`에서 root와 objective의 인과관계만 승인·감시·거절한다. 현재 무료 플랜 실행은 Lite로 통일한다.
- `REFINEMENT`에서는 같은 가격 사건을 설명하는 causal child OB만 고른다.
- `TRIGGER`에서는 refined OB 접촉 뒤의 mature sweep, meaningful M1 CHoCH, execution OB만 판단한다.
- `PENDING_REVIEW`에서는 동결된 주문을 유지·취소하거나, 계약이 완성된 경우에만 기존 미체결 주문을 `DELIVERY_FVG_REPLACEMENT`로 원자적으로 교체한다.

어느 모델도 가격, UTC, 주문 수치를 직접 작성하지 않는다. 모든 가격은 선택된 `barId`의 OHLC에서 엔진이 산출한다.

## 상태 머신

```text
FLAT
  -> MAP_SCOUT
  -> MAP_REVIEW
  -> WATCHING_MAP 또는 PREPARED
  -> REFINEMENT
  -> ARMED
  -> TRIGGER
  -> PENDING
  -> FILLED 또는 CANCELED
```

- `WATCHING_MAP`은 root·objective·접근가·무효화만 보존하며 주문 권한이 없다.
- root 접근, objective 선도달, source 무효화, child 접촉, local trigger candidate가 다음 판단을 깨운다.
- 독립 MAP 호출에는 이전 `NO_TRADE`나 조회 예산 설명을 전달하지 않는다.
- MAP에서 child, sweep, CHoCH, entry, SL, TP 누락을 거절 이유로 사용할 수 없다.

## 호출 절약

- 기본 MAP 검토 간격은 6시간이다. 그 사이의 새 구조 전달은 로컬 MAP activity가 즉시 깨운다.
- 새 M15 root가 H1 검토 사이에 생기는 문제를 막기 위해 로컬 MAP activity가 추가 호출을 깨울 수 있다.
- causal map이 `WATCHING_MAP`에 들어가면 root 접근 전까지 API를 호출하지 않는다.
- `ARMED` 뒤에는 로컬 M1 후보 탐색이 sweep/body-break 가능성을 찾은 시점에만 TRIGGER를 호출한다.
- 일일 하드 한도는 호출 32회, 토큰 180,000개이며 목표는 120,000개 이하다.
- reviewer JSON 출력 상한은 2,048토큰이다. 실제 판단 응답보다 큰 8,192토큰 예약으로 정상 호출을 조기 차단하지 않는다.
- MAP은 Lite 1회와 후보가 있을 때만 reviewer 1회를 사용한다. 나머지 단계는 reviewer만 사용한다.

## 정답지

현재 실행 정답은 `output/mentor_aug21_truth_v3/`이다.

- `AG21-001`: `AGENTS.md` 회귀 C를 올바른 final sweep 이후 다시 구성한 실행 가능한 기준 사례다.
- root는 M30 16:00, refinement는 M15 16:15과 M5 16:30, objective는 첫 internal SSL `3325.03`이다.
- 17:38 관통과 17:39 회복을 분리하고, 17:45 body CHoCH 뒤 causal execution OB retest만 주문으로 인정한다.
- 과거의 조기 3344.73 short는 sweep 성숙도, spread SL, scenario scope를 위반하므로 정답에서 제외한다.

기존 `2/2 EXACT`는 저장된 가격을 체결 엔진에 넣은 검증이며 독립적인 차트 판단 재현성으로 보지 않는다.

## 단계별 결과 분류

1. `MAP_MISS`: 방향과 scenario scope를 찾지 못함
2. `ROOT_MISS`: map은 맞지만 root candle이 다름
3. `OBJECTIVE_MISS`: root는 맞지만 목적 유동성이 다름
4. `REFINEMENT_MISS`: causal child를 찾지 못함
5. `TRIGGER_MISS`: sweep·CHoCH·execution lineage가 다름
6. `ORDER_MISS`: 인과 체인은 맞지만 주문을 승인하지 못함
7. `CAUSAL_MATCH`: 모든 인과 단계가 기준 사례와 일치

거래 가격 비교 결과는 `parity.csv`, 단계별 결과는 `funnel_parity.csv`에 저장된다.

## 실행과 검증

`launchers/Gemini_Replay_Run.cmd`는 다음 순서로 실행한다.

1. Python compile 및 로컬 계약 회귀 검사
2. 과거 Gemini 오류 corpus 재검사
3. 데이터·스키마·broker spec·API key preflight
4. 2025-08-21 미래 차단 재생
5. 재생 종료 후에만 V3 정답지를 열어 가격 및 funnel 비교

로컬 회귀 검사는 원본 NPZ에서 `AG21-001`의 root, child touch, 성숙 유동성, 관통, 후속 회복, body CHoCH, execution OB와 구조적 SL/TP가 모두 도달 가능함을 확인한다. 이 검사가 실패하면 Gemini API를 호출하지 않는다.

## 보안과 검증 경계

- API key는 `data/mentor_ai_replay_secret.json`에만 둔다.
- 실패한 모델 응답은 안전한 WAIT/CANCEL로 변환하며 임의 주문으로 복구하지 않는다.
- 미래 봉, 존재하지 않는 `barId`, 원본 OHLC 밖 가격은 거절한다.
- V3 이전 실행 원장은 날짜와 trigger 의미가 다르므로 resume할 수 없다.
- 하루 재현성 검증을 통과하기 전에는 장기간 재생, 실시간 운용, 실거래 연결로 확장하지 않는다.

## V3.8 chronology and wake-up guards

- Every approved MAP stores `frozenAtUtc`. A refinement touch earlier than that timestamp is rejected so a newly discovered scenario cannot consume a historical touch retrospectively.
- Local trigger detection follows only events after the approved refined touch. The maturity source must precede the touch, while sweep, recovery, and CHoCH must occur after it.
- CHoCH wake-up is edge-triggered. Remaining beyond an already-broken reference cannot wake the model again on each M1 close.
- Reviewer structured output is capped at 2,048 tokens because valid decisions are much smaller; unused output capacity is no longer included in the safety reserve.

## V3.9 event-owned touch and bounded context

- A MAP review marked `WATCH` remains `WATCHING_MAP`; an old root touch can no longer promote a newly discovered map to `PREPARED`.
- REFINEMENT preserves a valid causal child while discarding only an invalid pre-freeze touch. The first later child retest is detected and recorded by the local OHLC engine with zero provider calls.
- After ARM, the engine fast-forwards to a local trigger candidate instead of requesting a same-minute TRIGGER judgment before any post-touch structure can exist.
- MAP packets contain H1/M30/M15 only; M1 is withheld from MAP in accordance with AGENTS.md. REFINEMENT receives only post-freeze M1 bars.
- Prompt ceilings are now 10k/8k bytes for MAP scout/review, 12k for refinement, 14k for trigger, and 12k for pending review. The per-run hard token limit remains 180,000.

## V3.10 causal root and trigger episode guards

- A root candidate is rejected locally unless at least one later closed candle on the same timeframe body-closes beyond the root range in the proposed delivery direction.
- A TRIGGER rejection consumes the physical sweep episode that produced it. Different micro references attached to the same sweep cannot repeatedly call the model.
- When the model approves a valid sweep-to-CHoCH chain but names a non-opposite execution candle, the engine derives the final opposite-color OB from that already-approved displacement instead of requesting another judgment.
