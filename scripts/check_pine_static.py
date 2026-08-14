from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_PATTERNS = {
    "script declaration": r"^(indicator|strategy)\(",
    "learning object toggle": r"Show Learning Objects",
    "instrument preset": r"Market preset|Instrument Adaptation",
    "ATR buffer": r"SL buffer mode|ta\.atr\(atrLen\)",
    "trade guide toggle": r"Show Trade Guides",
    "setup label toggle": r"Show Setup Labels",
    "liquidity sweep": r"buySideSweep\s*=|sellSideSweep\s*=",
    "BOS/CHoCH": r"CHoCH|BOS",
    "BOS/CHoCH structure lines": r"f_draw_structure_break|line\.style_dotted",
    "FVG detection": r"bullFvg\s*=|bearFvg\s*=",
    "OB detection": r"f_find_bull_ob|f_find_bear_ob",
    "fresh zone strict setup": r"hasFreshBullZone|hasFreshBearZone|bullFreshLtfZone|bearFreshLtfZone",
    "trade guide lines": r"guideEntryTop|guideSl|guideTp",
    "PD equilibrium": r"Equilibrium 50%",
    "alerts": r"alertcondition\(",
}


DISPLAY_ONLY_REQUIRED_PATTERNS = {
    "script declaration": r"^indicator\(",
    "display-only marker": r"DISPLAY_ONLY_ICT_COCKPIT",
    "guaranteed indicator output": r"plot\(na,.+display\s*=\s*display\.none",
    "liquidity sweep": r"buySideSweep\s*=|sellSideSweep\s*=",
    "BOS/CHoCH": r"CHoCH|BOS",
    "BOS/CHoCH structure lines": r"f_draw_structure_break|line\.style_dotted",
    "FVG detection": r"bullFvg\s*=|bearFvg\s*=",
    "OB detection": r"f_find_bull_ob|f_find_bear_ob",
    "first bullish structure break": r"na\(lastBrokenHighTime\)\s+or\s+lastWaveHighTime\s*!=\s*lastBrokenHighTime",
    "first bearish structure break": r"na\(lastBrokenLowTime\)\s+or\s+lastWaveLowTime\s*!=\s*lastBrokenLowTime",
    "alternating structural waves": r"lastWaveKind\s*=\s*0",
    "three bearish wave confirmation": r"threeBear\s*=\s*close\s*<\s*open\s+and\s+close\[1\]\s*<\s*open\[1\]\s+and\s+close\[2\]\s*<\s*open\[2\]",
    "three bullish wave confirmation": r"threeBull\s*=\s*close\s*>\s*open\s+and\s+close\[1\]\s*>\s*open\[1\]\s+and\s+close\[2\]\s*>\s*open\[2\]",
    "causal bullish pullback": r"externalPullbackLow",
    "causal bearish pullback": r"externalPullbackHigh",
    "protected bullish body break": r"protectedBullBreak.+close\s*>\s*protectedHigh",
    "protected bearish body break": r"protectedBearBreak.+close\s*<\s*protectedLow",
    "independent internal trend": r"var\s+int\s+internalTrend\s*=\s*0",
    "bullish internal transition": r"structureChoch\s*:=\s*internalTrend\s*!=\s*0\s+and\s+internalTrend\s*!=\s*DIR_BULL",
    "bearish internal transition": r"structureChoch\s*:=\s*internalTrend\s*!=\s*0\s+and\s+internalTrend\s*!=\s*DIR_BEAR",
    "structure line style control": r"externalStructureLineStyle\s*=\s*input\.string",
    "liquidity line style control": r"liquidityLineStyle\s*=\s*input\.string",
    "zone border style control": r"f_zone_border_style",
    "global line width control": r"globalLineWidth\s*=\s*input\.int",
    "quarter-size sweep triangle": r"label\s+sweepTriangle\s*=.+size\s*=\s*2",
    "sweep triangle gap control": r"sweepTriangleGap\s*=\s*input\.float",
    "right-edge liquidity caption": r"label\.set_x\(liq\.caption,\s*sourceCloseTime\s*\+\s*captionOffset\)",
    "confirmed event offset": r"TfEvent\s+confirmed\s*=\s*current\[1\]",
    "PD equilibrium": r"균형가\s*/\s*EQ 50%",
    "bull FVG fill picker": r"bullFvgBgColor\s*=\s*input\.color",
    "bull FVG border picker": r"bullFvgBorderColor\s*=\s*input\.color",
    "bear FVG fill picker": r"bearFvgBgColor\s*=\s*input\.color",
    "bear FVG border picker": r"bearFvgBorderColor\s*=\s*input\.color",
    "bull OB fill picker": r"bullObBgColor\s*=\s*input\.color",
    "bull OB border picker": r"bullObBorderColor\s*=\s*input\.color",
    "bear OB fill picker": r"bearObBgColor\s*=\s*input\.color",
    "bear OB border picker": r"bearObBorderColor\s*=\s*input\.color",
    "font size control": r"fontSizeOption\s*=\s*input\.string",
    "alerts": r"alertcondition\(",
}


DISPLAY_ONLY_FORBIDDEN_PATTERNS = {
    "setup label control": r"\bshowSetupLabels\b",
    "trade guide control": r"\bshowTradeGuides\b",
    "setup condition": r"\bbullSetup\b|\bbearSetup\b",
    "entry guide": r"\bguideEntry(?:Top|Bottom)\b",
    "SL/TP guide": r"\bguideSl\b|\bguideTp\b",
    "HTF setup filter": r"\buseHtfBias\b|\bhtfBullOk\b|\bhtfBearOk\b",
    "PD setup filter": r"\busePdFilter\b|\bpdBullOk\b|\bpdBearOk\b",
    "SL/TP setup calculation": r"\bslBuffer\b|\btargetLookback\b|\blongTpCandidate\b|\bshortTpCandidate\b",
    "raw pivot promoted directly to structure": r"\brawBullBreak\b|\brawBearBreak\b",
}


ARCHIVE_REQUIRED_PATTERNS = {
    "script declaration": r"^indicator\(",
    "guaranteed indicator output": r"plot\(na,.+display\s*=\s*display\.none",
    "archive marker": r"PROVEN_ZONE_ARCHIVE",
    "unresolved FVG display": r"미해소 FVG 표시",
    "unresolved OB display": r"미해소 OB 표시",
    "separate FVG cap": r"maxActiveFvg",
    "separate OB cap": r"maxActiveOb",
    "separate resolved FVG cap": r"maxResolvedFvg",
    "separate resolved OB cap": r"maxResolvedOb",
    "active border color picker": r"activeBullFvgBorder\s*=\s*input\.color",
    "active fill color picker": r"activeBullFvgFill\s*=\s*input\.color",
    "history border color picker": r"historyBullFvgBorder\s*=\s*input\.color",
    "history fill color picker": r"historyBullFvgFill\s*=\s*input\.color",
    "FVG detection": r"bullFvg\s*=|bearFvg\s*=",
    "OB detection": r"f_find_bull_ob|f_find_bear_ob",
    "first bullish OB creation": r"na\(lastBullObOrigin\)\s+or\s+bullObLeft\s*!=\s*lastBullObOrigin",
    "first bearish OB creation": r"na\(lastBearObOrigin\)\s+or\s+bearObLeft\s*!=\s*lastBearObOrigin",
    "zone state": r"type ZoneState",
    "pivot qualification": r"ta\.pivothigh|ta\.pivotlow",
    "first-visit filter": r"첫 방문 피벗만 인정",
    "reaction-distance filter": r"최소 반응 폭 필수",
    "structure-break filter": r"단기 구조 돌파 필수",
    "liquidity-sweep filter": r"유동성 스윕 필수",
    "resolved history": r"keepResolved|resolvedBoxes",
    "Korean alerts": r"alertcondition\(.+새 상승 FVG",
}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/check_pine_static.py <file.pine>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    if not text.startswith("//@version="):
        errors.append("missing Pine version header")

    if "PROVEN_ZONE_ARCHIVE" in text:
        required_patterns = ARCHIVE_REQUIRED_PATTERNS
    elif "DISPLAY_ONLY_ICT_COCKPIT" in text:
        required_patterns = DISPLAY_ONLY_REQUIRED_PATTERNS
    else:
        required_patterns = REQUIRED_PATTERNS

    for name, pattern in required_patterns.items():
        if not re.search(pattern, text, flags=re.MULTILINE):
            errors.append(f"missing required module: {name}")

    if "PROVEN_ZONE_ARCHIVE" in text or "DISPLAY_ONLY_ICT_COCKPIT" in text:
        for line_number, line in enumerate(text.splitlines(), start=1):
            if "input." not in line:
                continue
            strings = [
                match[1]
                for match in re.findall(r"""(['"])(.*?)(?<!\\)\1""", line)
            ]
            if not strings:
                errors.append(f"input title not found on line {line_number}")
                continue
            title_index = 1 if "input.string" in line else 0
            if len(strings) <= title_index or not re.search(r"[가-힣]", strings[title_index]):
                errors.append(f"non-Korean input title on line {line_number}")
            if "DISPLAY_ONLY_ICT_COCKPIT" in text and "tooltip" not in line:
                errors.append(f"missing Korean tooltip on line {line_number}")

    if "DISPLAY_ONLY_ICT_COCKPIT" in text:
        for name, pattern in DISPLAY_ONLY_FORBIDDEN_PATTERNS.items():
            if re.search(pattern, text, flags=re.MULTILINE):
                errors.append(f"setup-only module must be removed: {name}")

    is_strategy = re.search(r"^strategy\(", text, flags=re.MULTILINE) is not None
    if is_strategy:
        for name, pattern in {
            "strategy entry": r"strategy\.entry\(",
            "strategy exit": r"strategy\.exit\(",
            "strategy order controls": r"Entry model|Cancel unfilled limit|Timeframe mode",
            "30m precision mode": r"30m \+ 1m Precision",
        }.items():
            if not re.search(pattern, text, flags=re.MULTILINE):
                errors.append(f"missing required strategy module: {name}")

    if re.search(r"\bfor\s+.+\s+to\s+.+\s+by\s+-\d+", text):
        errors.append("Pine for-loop step should not use a negative 'by' value")

    if re.search(r"label\.new\(bar_index,\s*(?:low|high),\s*(?:bullBreakName|bearBreakName).*style=label\.style_label_", text):
        errors.append("BOS/CHoCH should be drawn as structure lines, not candle bubble labels")

    pairs = [("(", ")"), ("[", "]")]
    for opening, closing in pairs:
        if text.count(opening) != text.count(closing):
            errors.append(f"unbalanced {opening}{closing} characters")

    if "\t" in text:
        errors.append("tabs found; Pine indentation should use spaces")

    if errors:
        print("PINE_STATIC_CHECK_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PINE_STATIC_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
