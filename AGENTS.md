# Trading repository authority

Last synchronized: `2026-09-28`
Base GitHub `main` checked: `29e0073e57553d8fe1fd14b843daf09164a7a248`

## Active generation

V13 is the only active strategy-research generation. V12 and earlier are
historical evidence only.

Start every V13 session in this order:

1. refresh GitHub `awindboy/Trading` latest `main`;
2. read `docs/ea/v13/AGENTS_V13.md`;
3. read `docs/ea/v13/V13_DOCUMENT_AUTHORITY_MAP_20260926.md`;
4. read `docs/ea/v13/V13_OBJECTIVE_AND_EVALUATION_UPDATE_20260928.md`;
5. read `docs/ea/v13/HANDOFF_V13.md`;
6. read `docs/ea/v13/RESEARCH_STATE_V13.md`;
7. read the frozen Baseline-0 contract and the current HA-9 action contract;
8. read the HA-9 receipt and MQL5 validation protocol before tester work.

## Frozen comparator

Baseline 0 remains the frozen control:

```text
completed standard H4 HA
same-color run = Journey
Child #1 on qualifying flip; one add-on per later same-color H4
maximum 10 successful Child entries
first opposite completed H4 closes remaining Journey Children
same opposite event starts the next Journey after close-all
fixed unit size
no Hard SL / TP / ML action / external filter
```

## Active action candidate

HA-9 is the current research candidate, not production authority.

```text
Child #1: Baseline 0 unchanged
Child #2..#10:
  enter at Baseline-0 timing
  next H4 must break the signal H4 favorable raw extreme
  if proven -> lock at max(entry, signal high) LONG / min(entry, signal low) SHORT
  if not proven within one H4 -> close that Child
  opposite H4 HA still closes all remaining Journey positions
```

See `V13_HA9_ADDON_PROOF_LOCK_ACTION_CONTRACT_20260928.md` for exact timing.

## Current evaluation doctrine

The active priority is **loss-frequency and ordinary equity quality**, not
preservation of every large right-tail Journey.

Primary evidence:

- loss-count reduction;
- non-flat win rate;
- consecutive losses;
- chronological drawdown and ordinary 10/25/50/100-trade block quality;
- year stability;
- large-winner-trimmed robustness.

Large continuation winners remain visible as a cost diagnostic, but touching a
profitable long Journey is no longer an automatic rejection reason. Historical
HA-6/7/8 contracts and receipts are not rewritten; current interpretation is
superseded by `V13_OBJECTIVE_AND_EVALUATION_UPDATE_20260928.md`.

## Causal and research rules

- Never inspect future price before the historical decision/action timestamp.
- Never add a hindsight trade after accidental reveal.
- Never resurrect a closed/stopped Child using later information.
- Do not invent hidden minimum-R, cooldown, retry, fixed no-chase, side balance,
  or parameter thresholds.
- Do not optimize the one-H4 proof window or proof/lock price on the same
  consumed sample merely to rescue a tester result.
- 2024-01-01..2026-08-28 remains consumed development history.
- MQL5 Strategy Tester `Every tick based on real ticks` is required for official
  execution economics.
