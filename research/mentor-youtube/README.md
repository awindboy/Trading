# 스승님 YouTube 매매법 원전 정리

## 목적

이 폴더는 사용자가 지정한 21개 영상만을 원전으로 삼아 스승님의 매매법을
재구성한다. 다른 ICT 강의, 용어 사전, GitHub 전략, 일반적인 SMC 해석은
근거로 끌어오지 않는다.

목표는 많은 개념을 수집하는 것이 아니다. 영상 전체에서 반복해서 확인되는
최소한의 판단 절차를 정확히 이해하고, 차트에서 재현할 수 있는 규칙과
스승님의 재량 판단을 구분하는 것이다.

## 문서 안내

- `VIDEO_DIGESTS.md`: 21개 영상을 순서대로 분석한 타임스탬프 기반 소화본
- `MENTOR_MINIMAL_METHOD.md`: 영상 전체에서 교차 확인한 최소 매매법과 체크리스트
- `CURRENT_ALGORITHM_REASSESSMENT.md`: 현재 V32/V3와 스승님 방식의 차이 및 재설계 경계
- `raw/*.json`: 영상별 한국어 자막, 메타데이터, 구간 정보
- `visuals/*_contact.jpg`: 핵심 영상의 전 구간을 균등 샘플링한 차트 화면 검증 자료

## 자료 품질

- 21개 영상 모두 한국어 자막을 확보했다.
- 자동 자막에는 `FVG`, `CHoCH`, `BOS`, `liquidity sweep` 등의 영문 용어가
  `FG`, `처치`, `수입`처럼 잘못 전사된 구간이 있다. 문서에서는 영상의 차트
  표기와 전후 문맥을 함께 보고 용어를 복원했다.
- 핵심 12개 영상은 자막뿐 아니라 전 구간 콘택트 시트로 차트 표시도 대조했다.
- 영상에 나온 수익과 승률은 스승님의 자기 보고다. 독립 검증된 백테스트
  결과가 아니므로 전략 규칙의 근거와 수익성 증거를 구분한다.

## 핵심 결론

21개 영상의 공통 골격은 다음 한 줄로 압축된다.

> 현재 가격이 향하는 유동성을 파악하고, 주로 H1 스윙 부근의 OB를 찾은 뒤
> 그 OB를 구성한 하위 시간봉 OB까지 세분화한다. 해당 위치에서 작은 시간봉
> 추세 전환을 확인하고, 그 전환 displacement가 만든 M1 FVG 되돌림에 진입하여
> 다음 유동성까지 보유한다.

HTF OB와 LTF FVG의 역할은 다르다. HTF OB는 가격이 반응할 원인 위치를 정하고,
하위 OB refinement는 그 위치와 무효화 범위를 좁힌다. 실제 기본 진입은 그 위치에서
M1 추세가 전환될 때 생긴 FVG 되돌림이다. FVG가 없으면 기본형 주문도 없다.
기존 포지션이 목적지로 전달되는 중 생긴 FVG는 별도 추가진입 모델로 구분한다.

여기서 중요한 것은 `FVG/OB가 보였다`가 아니라 다음 네 질문이다.

1. 지금 가격은 어느 방향의 유동성을 향하고 있는가?
2. 진입 후보 주변에 실제로 다른 트레이더의 손절이 모일 이유가 있는가?
3. 그 유동성을 가져간 뒤 작은 시간봉의 추세가 실제로 바뀌었는가?
4. 틀렸음을 인정할 가격과 다음 목적지가 차트 구조로 설명되는가?

## 영상 목록

| # | 영상 | 길이 | 문서상 역할 |
| ---: | --- | ---: | --- |
| 1 | [해외에서 이미 유명한 차트이론](https://www.youtube.com/watch?v=6l3mktEl9PM) | 11:30 | 전체 개념 입문 |
| 2 | [ICT트레이딩 진입 전략](https://www.youtube.com/watch?v=7sQryLbDm6A) | 11:08 | 기본 진입 순서 |
| 3 | [FVG + liquidity 원리와 정리](https://www.youtube.com/watch?v=stffuxegJLk) | 28:08 | 보수적 진입과 SL/TP |
| 4 | [Price Action의 심리](https://www.youtube.com/watch?v=PcufwRQn3zE) | 17:30 | 손절 유동성의 심리 |
| 5 | [OB전략이 실패한 이유](https://www.youtube.com/watch?v=sZr8tlQEv7U) | 22:04 | 추세 맥락과 OB |
| 6 | [PD Array](https://www.youtube.com/watch?v=b9LzAMEu0JI) | 11:11 | 가격대 보조 판단 |
| 7 | [15m ICT Trading](https://www.youtube.com/watch?v=mcPF2iX1N-Y) | 07:59 | 단일 15분봉 사례 |
| 8 | [실시간 트레이딩 2](https://www.youtube.com/watch?v=KlECfDT1yas) | 08:48 | 실전 판단과 불확실성 |
| 9 | [지금 진입 Yes or No?](https://www.youtube.com/watch?v=4J4YzAsrWbI) | 16:59 | 시간봉 전환 사례 |
| 10 | [진입 전략 1: Trend](https://www.youtube.com/watch?v=Q5vjDNLSNXM) | 21:54 | 외부/내부 구조와 추세 |
| 11 | [진입 전략 2: Liquidity](https://www.youtube.com/watch?v=bCmYPKTj-pc) | 18:16 | 유동성 식별 |
| 12 | [진입 전략 3: FVG/OB](https://www.youtube.com/watch?v=nFo44-vQUKE) | 13:37 | FVG/OB 정의와 맥락 |
| 13 | [진입 전략 4: Time frame](https://www.youtube.com/watch?v=aFdHzpa9o48) | 36:09 | 다중 시간봉 통합 |
| 14 | [비트코인 실시간 매매 분석](https://www.youtube.com/watch?v=dD4PE-MlWmM) | 21:52 | 빠른 FVG 반전 진입 |
| 15 | [실패와 또 다른 기회](https://www.youtube.com/watch?v=8cU6xdYaXaE) | 35:01 | 손실, 본절, 재기회 |
| 16 | [원리와 맥락 이해](https://www.youtube.com/watch?v=uhuyEbeJZP4) | 29:06 | 단순 FVG/OB 매매 비판 |
| 17 | [가격이동 분석이 맞았나요?](https://www.youtube.com/watch?v=iXOVCbwQh8A) | 14:11 | 내부 목표와 부분 청산 |
| 18 | [손절 기준 / 재진입 시나리오](https://www.youtube.com/watch?v=7inzWhh_tdY) | 15:44 | 시나리오 무효화와 반전 |
| 19 | [매매일지 작성법](https://www.youtube.com/watch?v=x0duegy7hH8) | 16:20 | 연구/실행 일지 분리 |
| 20 | [부담과 감사를 느낀 아서](https://www.youtube.com/watch?v=DARyWRgiN48) | 11:47 | 30분봉에서 15분봉으로 원인 탐색 |
| 21 | [빠르게 분석해봅시다](https://www.youtube.com/watch?v=v2d-oOuu03s) | 16:50 | 외부/내부 추세 실전 적용 |

## 사용 원칙

- `MENTOR_MINIMAL_METHOD.md`를 전략의 단일 기준 문서로 사용한다.
- 영상 한 편에서만 등장한 변형은 핵심 규칙으로 승격하지 않는다.
- 규칙으로 만들 수 없는 재량 판단은 억지 수치화하지 않고 연구 가설로 남긴다.
- 수익성은 영상의 사례가 아니라 별도 데이터와 미사용 기간으로 검증한다.
