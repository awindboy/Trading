# V5 Development Handoff

Last updated: `2026-08-27`
Current phase: `V5-034A FIRST CROSS 240M EXTERNAL VALIDATION`
Current candidate: `V5_FIRST_CROSS_240M_HALF_EMA_RUNNER`
Candidate status: `DEVELOPMENT PASS / FROZEN FOR VALIDATION`
Production authority: `NONE`

## Startup — mandatory

Read in order:

1. latest GitHub HEAD;
2. root `AGENTS.md`;
3. root `docs/ea/HANDOFF.md`;
4. `AGENTS_V5.md`;
5. this file;
6. `RESEARCH_STATE_V5.md`;
7. `V5_030A_FIRST_CROSS_240M_DEVELOPMENT_RESULTS.md`;
8. `V5_034A_FIRST_CROSS_240M_VALIDATION_CANDIDATE_FREEZE.md`;
9. `V5_034A_EXTERNAL_VALIDATION_CONTRACT.md`;
10. `V5_034A_PREVALIDATION_PARITY_AUDIT.md`;
11. `DECISIONS_V5_APPEND_D178.md`;
12. `V5_RECURSIVE_FALSIFICATION_PROTOCOL.md`;
13. `V5_NEXT_SESSION_OPERATING_PROTOCOL.md`;
14. `BACKLOG_V5.md`.

GitHub wins over chat memory.

## What happened after V5-001A

The first boundary proxy failed under adversarial controls.

The project then ran a long success-first sequence rather than rescuing that proxy:

```text
balance/breakout
failed breakout/retest
Holy Grail
Turtle Soup
Anti
Momentum Pinball
80-20
failed Holy Grail forecast
First Cross
```

Read:
- `V5_002_TO_V5_025_SUCCESS_FIRST_SYNTHESIS.md`
- `V5_026_TO_V5_033_FIRST_CROSS_SYNTHESIS.md`

The important result is not that every successful-trader setup worked mechanically. Most did not.

The important result is that the research eventually found one **development candidate** whose Entry, loss truncation and
winner lifecycle jointly satisfy the project's central development economics.

## Current candidate

```text
240m First Cross
+ first causal 3-bar higher-low/lower-high pivot
+ stop-entry beyond completed confirmation bar
+ structural pivot stop
+ 50% realized at +1R
+ runner stop -> BE
+ runner exit on adverse completed 240m EMA20 close or slow-line zero reversal
```

No later context filter is included.

## Development result

```text
N                    406
WR                   53.94%
avg positive net R   +1.197R
spread-adjusted EV   +0.148R/trade
```

Pooled EV is positive in 2023, 2024 and 2025.

Market EV:
- BTCUSD# positive;
- GOLD# positive;
- XAUEUR# positive;
- USDJPY# negative.

Every leave-one-market-out and leave-one-year-out pooled EV remains positive.

However weekly-block uncertainty still crosses zero and GOLD# 2022 consumed diagnostic is roughly flat.

Therefore:

```text
DEVELOPMENT PASS
!=
VALIDATION PASS
```

## Frozen negative follow-ups

Do not add:
- daily 3/10 alignment (`V5-031A`, 2025 reversed);
- ATR volatility adequacy (`V5-032A`, frozen gate failed);
- an USDJPY veto;
- another Holy Grail runner (`V5-033A` closed before validation).

These are not missing tweaks.

## Immediate next task

External validation only:

```text
XAUJPY#  2023-2025
XAUCNH#  2023-2025
GAUCNH#  2023-2025
GAUUSD#  2023-2025
```

Use the same broker/feed family and recorded spread.

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_v5_034_external_validation.ps1 `
  -Python python `
  -DataMap .\config\v5_034_external_data_map.local.json `
  -OutDir .\v5_034_external_results
```

At handoff time these raw validation CSVs were not found in the active session/File Library.

Pre-validation replay parity/reproducibility hardening is complete. The original development result was reproduced;
one same-M1 adverse-exit/BE ordering case was corrected without changing candidate classification. The external runner
now freezes raw SHA-256 identities before outcomes and applies the deterministic A-F gate. Read
`V5_034A_PREVALIDATION_PARITY_AUDIT.md`.

## Hard stops

- do not inspect GOLD# 2021;
- do not retune V5-030A;
- do not remove a negative validation market;
- do not change timeframe;
- do not add commission/slippage assumptions chosen to save a result;
- do not restart AI/RL as a rescue;
- do not modify the MT5 production EA.

If V5-034A fails, record failure first. A new success-first discovery phase requires a genuinely new mechanism and
new preregistration.

If V5-034A passes, freeze the result before opening GOLD# 2021 or writing an MT5 research EA.
