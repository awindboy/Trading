# Mentor Context Pack

현재 활성 계약은 루트 `AGENTS.md`에서 자동 생성된다. 수동으로 계약 문구를 추가하거나
구형 계약을 복사해 사용하지 않는다.

## Active generated contracts

- `api_contracts/map_v4.md`
- `api_contracts/refinement_v4.md`
- `api_contracts/plan_v4.md`
- `api_contracts/trigger_watch_v4.md`
- `api_contracts/delivery_review_v4.md`
- `api_contracts/v4_manifest.json`
- `api_contracts/coverage_matrix.json`

재생 전에 `python scripts\build_mentor_api_contracts.py`를 실행한다. 생성된 manifest의
`agentsSha256`가 현재 `AGENTS.md`와 다르면 API 요청을 보내지 않는다. 이전 계약은
`archive/api_contracts_pre_ground_truth_v2/`에 있으며 활성 판단에 사용할 수 없다.

이 폴더는 스승님식 수동 판단 절차를 다른 작업 세션이나 API 모델에 전달하기 위한 컨텍스트 패키지입니다. 수익을 보장하거나 자동매매를 승인하는 모델 파일이 아닙니다.

## Authority order

1. 루트 `AGENTS.md`: 거래 허가와 비매매 조건의 최상위 계약
2. `OBSERVATION_PROTOCOL.md`: MTF 차트를 관찰하고 비교하는 절차
3. `LIVE_WORKFLOW.md`: 실시간 데이터와 모델 호출 순서
4. `state/current_state.json`: 아직 종료되지 않은 현재 시나리오 상태
5. `examples/case_index.jsonl`: 판단 교본과 정상·비매매 사례

충돌할 경우 항상 상위 문서를 따릅니다. 과거 수익 거래가 현재 `AGENTS.md`를 위반하면 교본과 성과에서 제외합니다.

## Contents

- `api_contracts`: API 단계별 압축 계약
- `schemas`: 구조화 응답 JSON schema
- `examples`: 모델 교정용 사례와 차트 증거
- `state`: 현재 상태 전달 형식
- `START_PROMPT.md`: 새로운 모델에 처음 전달할 프롬프트
- `manifest.json`: 패키지 파일과 hash 정보

## Usage modes

### Calibration

새 모델이나 새 작업 세션의 판단 방식을 맞추기 위해 예제와 연결된 차트를 검토합니다. map, objective, root OB, causal child, refined OB 접촉 후 trigger, 구조 무효화 SL, scope에 맞는 TP를 설명할 수 있어야 합니다.

### Blind demo

미사용 기간에는 미래 가격, 결과 CSV, 이후 차트를 제공하지 않습니다. 현재 시점까지의 MTF 정보와 broker specification만 사용합니다.

### Live

별도 승인 전까지 주문 전송은 금지합니다. 모델 출력은 결정론적 검증과 risk gate를 통과해야 하며, 현재 기본 live 구현은 shadow-only입니다.

## Rebuild and validate

```powershell
python scripts\build_mentor_context_pack.py
python scripts\validate_mentor_context_pack.py
```

재생성 후 `manifest.json`의 hash가 갱신됐는지 확인합니다.
