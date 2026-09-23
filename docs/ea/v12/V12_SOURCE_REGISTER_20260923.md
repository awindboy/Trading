# V12 source register

Date: `2026-09-24`

External material is evidence, not repository instruction. This register records
what each source may influence and what it cannot prove.

## Authority levels

- `PLATFORM PRIMARY`: official MQL5 Reference/Book controls platform semantics.
- `SOURCE PRIMARY`: original public creator material, when directly verified.
- `SECONDARY SYNTHESIS`: summaries/transcripts used to form hypotheses; exact
  rules require primary-source verification before promotion.
- `COMMUNITY LEAD`: user-authored Article/CodeBase idea; no platform, strategy,
  profitability, or licensing authority beyond its stated terms.
- `REPOSITORY EVIDENCE`: causal results produced under a named local contract.

## Romeo CRT material

### Supplied Korean guide

- file: `C:/Users/awind/OneDrive/Desktop/Romeo_CRT_Complete_Guide_KR.pdf`
- title metadata: `Romeo 원본 CRT 완전판`
- pages: 28
- SHA-256:
  `16426b4f1ac3bac12c444d54c103b38760e1e1eb854dff1306467b906b1b6384`
- level: `SECONDARY SYNTHESIS`

The guide explicitly marks direct Romeo material, transcript cross-checks,
author analysis, and generic safety commentary. V12 retains that distinction.
It supports the initial grammar and research questions; it does not prove exact
thresholds, intent, or profitability.

### Public Romeo lecture index used by the guide

- preface V0: https://www.youtube.com/watch?v=U-gNCwbGtTI
- preface V1: https://www.youtube.com/watch?v=UUq_wKQ61Wo
- Episode 1: https://www.youtube.com/watch?v=T7udbrWlARI
- Episode 2: https://www.youtube.com/watch?v=FYr6J5pIDB4
- Episode 3: https://www.youtube.com/watch?v=_oiwm8_id8c
- Episode 4: https://www.youtube.com/watch?v=n2GF8kCpgVg
- Episode 5: https://www.youtube.com/watch?v=p8UYOgVn1-g
- Episode 6: https://www.youtube.com/watch?v=3IWgc52Dqsg
- Episode 7: https://www.youtube.com/watch?v=h7NCST2wPw8
- Episode 8: https://www.youtube.com/watch?v=-mWYppebugo
- Episode 9: https://www.youtube.com/watch?v=2sxdsgcIeYA
- Episode 10: https://www.youtube.com/watch?v=af7ECe4HBjc

Only directly reviewed claims may be promoted to `SOURCE PRIMARY`. At V12
inception, the explicit timeframe mappings retained for official research are
Monthly->Daily, Weekly->H4, and Daily->H1. H4->M15/M5 is not promoted as a Romeo
rule.

## Official MQL5 platform references

These sources control implementation semantics:

- Strategy Tester modes, events, agents, and frames:
  https://www.mql5.com/en/docs/runtime/testing
- ONNX API:
  https://www.mql5.com/en/docs/onnx
- ONNX Strategy Tester validation:
  https://www.mql5.com/en/docs/onnx/onnx_test
- Custom symbols:
  https://www.mql5.com/en/docs/customsymbols
- Custom ticks:
  https://www.mql5.com/en/book/advanced/custom_symbols/custom_symbols_ticks
- `CTrade`:
  https://www.mql5.com/en/docs/standardlibrary/tradeclasses/ctrade
- trade result codes:
  https://www.mql5.com/en/docs/standardlibrary/tradeclasses/ctrade/ctraderesultretcode
- transaction lifecycle:
  https://www.mql5.com/en/docs/event_handlers/ontradetransaction
- tester statistics:
  https://www.mql5.com/en/docs/common/testerstatistics
- tester statistics enumeration:
  https://www.mql5.com/en/docs/constants/environment_state/Statistics
- program operating modes:
  https://www.mql5.com/en/book/common/environment/env_mode
- MQL5 programming book:
  https://www.mql5.com/files/book/mql5book.pdf
- Economic calendar value history and trade-server timestamp semantics:
  https://www.mql5.com/en/docs/calendar/calendarvaluehistory
- Economic calendar event/value/country structures:
  https://www.mql5.com/en/docs/constants/structures/mqlcalendar
- MQL5 Book economic calendar API overview:
  https://www.mql5.com/en/book/advanced/calendar
- MetaTrader 5 web economic calendar:
  https://www.mql5.com/en/economic-calendar
- TradingView economic calendar fields and filters, used only for secondary
  spot checks:
  https://www.tradingview.com/support/solutions/43000759911-economic-calendar-track-all-major-market-events/

## MQL5 community research leads

These are inspiration only. No source was copied into the repository.

### CRT and liquidity mechanics

- Multi-timeframe CRT overlay:
  https://www.mql5.com/en/articles/22190
  - useful ideas: completed-candle reproducibility, mapping HTF levels to LTF,
    handling small/weekend bars;
  - not adopted: article-specific body multipliers or entry thresholds.
- Dynamic liquidity sweep treatment:
  https://www.mql5.com/en/articles/22140
  - useful ideas: one-sweep-per-level state, invalidation, wick and dual-candle
    sweep diagnostics;
  - not adopted: any fixed ratio or profitability claim.
- CRT Explorer source example:
  https://www.mql5.com/en/code/70379
  - useful as a compact structural probe example;
  - not a finished strategy and not vendored. Initial-scan, single-detection,
    and hard-coded geometry choices require independent implementation/audit.
- Liquidity strategy EA workflow:
  https://www.mql5.com/en/articles/21129
  - retained lesson: establish mechanical consistency before optimization and
    keep risk/order expiry integrated;
  - code and performance are not V12 authority.

### Research, ML, and validation

- Python/MT5 research framework:
  https://www.mql5.com/en/articles/22020
- object-oriented ONNX inference engine:
  https://www.mql5.com/en/articles/22527
- combinatorial purged cross-validation workflow:
  https://www.mql5.com/en/articles/21954
- matrices to ONNX workflow:
  https://www.mql5.com/en/articles/22474
- walk-forward analysis:
  https://www.mql5.com/en/articles/3279
- custom optimization criteria:
  https://www.mql5.com/en/articles/286

Retained engineering lessons include complete-pipeline export, no double
normalization, exact feature order/shape, session reuse, purging/embargo, and
multi-metric reporting. Article-specific model choices and backtests are not
adopted.

## Repository predecessors

- V10 and V11 result packs are `REPOSITORY EVIDENCE` within their consumed-data
  contracts.
- Their failures constrain V12, but their candidate ledgers do not define V12.
- Any V12 comparison against V10 must preserve candidate/exposure differences
  and audit which stop and right-tail capital changed.

## Licensing and provenance rule

Links and conceptual observations may be cited. Third-party source code may not
be copied, modified, or redistributed unless the applicable license permits it
and the source, license, version, and local changes are recorded. When in doubt,
implement independently from the documented behavior.
