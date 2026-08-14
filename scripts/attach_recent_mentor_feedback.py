from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge.mt5_bridge import JOURNAL_DB_FILE


REVIEWS = {
    "mt5:362122361:267444832": (
        "GOLD Short -14.00 | 재진입은 맞았지만 스탑 위치가 틀렸다",
        [
            "이 거래의 아이디어 자체는 그날의 다른 숏보다 훨씬 낫다. M30은 premium/bearish이고, M5와 M1 모두 bearish CHoCH와 FVG/OB를 갖고 있었다. 메모처럼 고점대에서 이미 숏을 보던 상황에서 반등이 M1 FVG로 들어올 때 추가 숏을 검토한 것은 하락 시나리오에 맞는 실행이었다.",
            "다만 M30에는 아직 bearish CHoCH가 없었고, M5에는 새 BSL sweep 없이 CHoCH만 있었다. 즉 이 반등은 하락 continuation을 위한 되돌림일 가능성이 있었지만, 바로 위 유동성까지 한 번 더 끌어올릴 여지도 남아 있었다. 실제로 가격은 4126.70의 FVG 상단 스탑을 먼저 건드린 뒤 다시 하락했다. 이후 하락했다고 해서 진입이 맞았다는 뜻은 아니다. 무효화 지점을 FVG 테두리와 동일시한 것이 문제다.",
            "다음 같은 재진입에서는 FVG 경계가 아니라 그 FVG를 만들기 직전의 M1/M5 swing high 또는 BSL 위를 무효화 지점으로 둬야 한다. 그만큼 스탑이 멀어져 손익비가 나빠지면 거래를 포기하는 것이 맞다. 더 좋은 방식은 첫 FVG 터치가 아니라, FVG 상단 유동성을 한 번 처리한 뒤 다시 bearish displacement가 나온 경우만 재진입하는 것이다.",
        ],
    ),
    "mt5:362122361:267458007": (
        "GOLD Short -12.70 | premium은 진입 신호가 아니다",
        [
            "이 거래는 숏을 볼 위치만 있었고, 숏을 실행할 구조는 없었다. M30과 M5가 모두 bullish였고, M5와 M1 모두 bearish CHoCH/BOS가 확인되지 않았다. M30/M5의 BSL sweep도 실제 매도 전환으로 이어졌다는 증거가 아니었다.",
            "진입가는 4123.20이고 스탑은 4125.74였다. 약 3분 만에 스탑이 났다는 것은 가격이 공급구역에서 거절받은 것이 아니라 아직 상방 흐름 안에 있었다는 뜻이다. M1 FVG 하나가 보였더라도, bullish orderflow 속 FVG는 반전용 공급구역이 아니라 다음 상승 전의 작은 조정일 수 있다.",
            "이 유형은 명확히 no-trade로 분류해야 한다. 다음에는 premium에 도달했더라도 BSL sweep 이후 M1의 bearish displacement가 직전 protected low를 깨고, 그 displacement가 만든 fresh bearish FVG로 되돌릴 때까지 기다려야 한다. 그 전의 숏은 구조 매매가 아니라 고점 맞히기다.",
        ],
    ),
    "mt5:362122361:266971050": (
        "GOLD Short -42.88 | 맞는 HTF 방향에서 너무 낮은 가격을 팔았다",
        [
            "이 거래는 H1/M30/M15만 보면 bearish 시나리오가 있었다. H1과 M30은 premium/bearish이며 CHoCH와 FVG/OB가 있었기 때문에, 상위 관점에서 숏을 찾는 것까지는 자연스럽다. 하지만 실제 진입 4093.96 시점의 M5는 discount/bullish였다. 즉 상위 하락의 좋은 공급구역에서 판 것이 아니라, 이미 아래로 진행된 구간에서 되돌림을 기다리지 못하고 숏을 추격한 것이다.",
            "M15와 M5 어느 쪽에서도 새 BSL sweep이 없었다. 그래서 M5의 bullish CHoCH는 단순 반등이 아니라, 숏이 들어갈 위치까지 가격을 복귀시키는 힘으로 작동했다. 10시간 이상 보유한 뒤 4136.84에서 스탑이 난 것은 HTF 방향이 틀렸다기보다 실행 가격이 틀린 경우다. 같은 시기 다른 숏 포지션까지 겹치면서 한 번의 상방 복귀가 여러 포지션을 동시에 훼손했다.",
            "HTF bearish일수록 오히려 discount에서 새 숏을 금지해야 한다. M5가 premium으로 복귀해 BSL을 처리하고 bearish CHoCH를 다시 만들 때만 숏을 열어야 한다. 그때까지 오지 않으면 놓치는 것이 정상이다. 또한 장시간 보유 중 M5가 bullish 구조를 유지하면 원래 TP를 고집하지 말고, 반대 구조가 유지되는 동안의 보유 근거를 별도로 다시 확인해야 한다.",
        ],
    ),
    "mt5:362122361:267420794": (
        "GOLD Short -21.80 | 실제로는 수익이 아니라 동시 스탑 손실",
        [
            "먼저 기록을 바로잡아야 한다. 웹에 남아 있던 +$34.10은 EA의 미청산 스냅샷이었고, MT5 청산 원장의 실제 결과는 4136.84에서 -$21.80 스탑 손실이다. 이 거래는 수익으로 복기하면 안 된다. 같은 시각 266971050 숏도 함께 스탑이 나면서, 비슷한 하락 시나리오에 노출이 중첩됐다.",
            "M30은 premium/bearish, M5도 bearish였기 때문에 상위 아이디어는 숏 방향과 맞았다. 그러나 진입 직전 M1은 bullish였고, M5/M1 모두 새 BSL sweep 없이 CHoCH만 잡혔다. M1의 bullish 흐름을 무시한 채 같은 방향 숏을 추가한 셈이다. 이 구조에서 4136.64처럼 가까운 스탑은 위쪽 유동성 회수에 취약했다.",
            "앞으로 같은 방향 포지션이 이미 열려 있으면 두 번째 진입은 첫 포지션보다 기준을 높여야 한다. 최소한 첫 진입 이후 생긴 별도의 BSL sweep과 새 bearish displacement가 있어야 하며, 두 포지션의 합산 손실이 계좌 기준 사전 한도를 넘으면 추가 진입을 금지해야 한다. 방향이 같다고 위험이 분산되는 것이 아니라, 같은 무효화 구간에 몰린다.",
        ],
    ),
    "mt5:362122361:267502031": (
        "GOLD Long -144.00 | 분석 손실이 아니라 마진 강제청산",
        [
            "MT5 원장 기준 이 거래의 실제 결과는 -$144.00이다. 웹에 보이던 -$7.60은 오래된 EA 이벤트 값이었다. 진입은 4134.02, 수동 SL은 4131.17이었지만 실제 청산은 4119.62에서 stop-out으로 발생했다. 따라서 이 거래는 스탑이 지켜진 손실이 아니라, 계좌가 포지션을 더 이상 유지할 수 없어 청산된 사건이다.",
            "차트 관점에서도 H1과 M30은 bullish이지만 모두 premium이었고, SSL sweep이 없었다. M1 bullish CHoCH/FVG가 있었다 해도 상위 premium에서의 롱은 continuation 추격이다. 0.10 lot은 이 계좌 크기에서 구조 스탑과 맞지 않는 수량이었다. 가격이 4131.17을 넘긴 순간 원래 시나리오는 이미 무효였는데, 포지션은 그보다 훨씬 아래까지 남아 계좌 위험으로 전환됐다.",
            "가장 먼저 고쳐야 할 것은 진입 기법이 아니라 손실 상한이다. 주문 전에 반드시 브로커 쪽 SL이 실제로 걸렸는지 확인하고, 해당 SL에 닿았을 때의 손실이 계좌의 정한 비율을 넘으면 수량을 줄여야 한다. H1 bullish라도 premium에서 롱을 하려면 M30/M5의 SSL sweep과 재상승 displacement가 필요하다. 이것이 없으면 1분 신호만으로 0.10 lot을 열 근거가 없다.",
        ],
    ),
    "mt5:362122361:267590305": (
        "GOLD Short -7.31 | 구조는 있었지만 보호 주문 없이 들어갔다",
        [
            "이 거래는 6건 중 차트 구조만 놓고 보면 가장 검토할 만한 숏이었다. H1은 premium/bearish이며 BSL sweep과 CHoCH가 있었고, M5도 BSL sweep, CHoCH, bearish FVG/OB가 잡혔다. 다만 M30은 아직 bullish이고, M5 진입 위치는 discount였다. 상위 bearish 시나리오가 있어도 실제 매도는 되돌림 위치에서 해야 한다는 경고가 동시에 있었다.",
            "결정적인 문제는 SL과 TP가 0으로 기록된 채 진입했다는 점이다. 4122.51에서 숏을 열고 4129.82에서 stop-out이 났다. 이는 시장 구조에 의한 계획 손절이 아니라 마진 레벨 18.93%에서 브로커가 강제 종료한 것이다. 좋은 구조 판독도 무효화 가격과 주문 보호가 없으면 계좌 관리 관점에서는 좋은 거래가 아니다.",
            "다음에는 H1 bearish 신호가 있어도 M30 bullish와 M5 discount가 동시에 보이면 즉시 매도하지 말고, M5가 premium으로 되돌린 뒤 새 bearish FVG를 만드는지 기다려야 한다. 그리고 주문 창을 닫기 전 SL/TP가 실제 가격으로 채워졌는지 확인하는 것은 분석과 별개의 필수 체크다. 보호 주문이 없으면 어떤 ICT 시나리오도 실행하면 안 된다.",
        ],
    ),
}


def main() -> int:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    with sqlite3.connect(JOURNAL_DB_FILE, timeout=30) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=30000")
        connection.execute("BEGIN IMMEDIATE")
        for trade_id, (title, paragraphs) in REVIEWS.items():
            row = connection.execute("SELECT data FROM trades WHERE id=?", (trade_id,)).fetchone()
            if row is None:
                raise RuntimeError(f"Trade not found: {trade_id}")
            trade = json.loads(row["data"])
            feedback = trade.get("aiFeedback") if isinstance(trade.get("aiFeedback"), dict) else {}
            feedback.update(
                {
                    "generatedAt": now,
                    "mentor": "Codex / ICT 멘토",
                    "version": "codex-mentor-review-v2",
                    "usedBars": True,
                    "analysisSource": "mt5-bars-and-deal-ledger",
                    "title": "심층 매매 피드백",
                    "verdict": "MT5 청산 원장과 다중 시간봉 bars를 함께 사용한 거래별 복기입니다.",
                    "mentorReview": {
                        "title": title,
                        "generatedAt": now,
                        "source": "MT5 deal ledger + MTF bars",
                        "paragraphs": paragraphs,
                    },
                }
            )
            trade["aiFeedback"] = feedback
            trade["updatedAt"] = now
            connection.execute(
                "UPDATE trades SET data=?, updated_at=? WHERE id=?",
                (json.dumps(trade, ensure_ascii=False), now, trade_id),
            )
        connection.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('updatedAt', ?)", (now,))
    print(f"RECENT_MENTOR_FEEDBACK_ATTACHED={len(REVIEWS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
