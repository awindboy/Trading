# 대표 사례 사용법

`case_index.jsonl`은 `scripts/build_mentor_context_pack.py`가 현재 공식 원장과 strict as-of 이미지에서 생성한다.

- `TRADE`: 주문 전에 동결된 판단과 종료 결과를 함께 보되, 먼저 이미지와 `order_decision`만 읽고 스스로 구조를 설명한 뒤 결과를 확인한다.
- `NO_TRADE` / `CANCELED`: 거래를 만들지 않은 이유를 학습한다.
- `chart_as_of <= decision_as_of`가 아닌 이미지는 builder와 validator가 거부한다.
- 이미지의 박스나 자동 라벨을 정답으로 사용하지 않는다. 이 Pack의 이미지는 raw as-of chart여야 한다.
- BLIND_DEMO 대상 기간과 사례 기간이 겹치면 해당 사례를 모델 입력에서 제외한다.

대표 사례는 성과를 과장하기 위한 최고 수익 거래 모음이 아니다. 다음 범주를 의도적으로 섞는다.

- HTF OB reaction 승리와 정상 손실
- Delivery FVG replacement
- INTERNAL_ROTATION과 EXTERNAL_CONTINUATION
- source 무효화, objective 선도달, stale source, FVG 추격 거절

