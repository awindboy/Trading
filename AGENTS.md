# Trading repository authority

Last synchronized: `2026-09-29`
Base GitHub `main` checked: `1555d2b06b4dabdbadf14366c26e4f2177506463`

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
7. read the frozen Baseline-0 contract and the current LTF-route action contract;
8. read the LTF-route receipt and MQL5 validation protocol before tester work;
9. read the LTF-route actual-tick replay receipt;
10. read `V13_HA9_TRADE_MODE_COVERAGE_20260928.md` and the LTF research chronicle
   before proposing another timeout, re-arm, runner, correction-envelope or
   exit-horizon variant.

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

The current research candidate is the LTF route q75/q50 state machine. HA-9
and SA-1 remain historical comparators; SA-1 is the current actual-tick
ordinary-equity reference.

```text
Child #1: frozen Baseline 0 unchanged
replacement add-on lane:
  live H4 PHA
  -> M30 correction + fresh causal M15 POI interaction
  -> causal M30/H1 forward destination topology
  -> strict-prior OOF hurdle-EV q75 admission, fixed 0.01 lot
  -> first destination is proof, not TP
  -> first post-delivery damaged correction uses strict-prior OOF q50 repair
```

See `V13_LTF_ROUTE_Q75_Q50_ACTION_CONTRACT_20260929.md`. The interrupted
session's exact q50 ledger remains absent. Reconstruction A recovered the same
population and passed exact actual-tick policy parity, but is not promoted:
its stronger payoff/net comes with worse loss frequency, win rate, streak and
exposure than SA-1. It is not embedded-model authority.

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
- Do not replace the predeclared q75 admission/q50 repair ranks with post-hoc
  q65/q70 thresholds or convert q75 into fitted position sizing.
- 2024-01-01..2026-08-28 remains consumed development history.
- MQL5 Strategy Tester `Every tick based on real ticks` is required for official
  execution economics.

## Current execution boundary

SA-1 has an actual-tick report and Journal receipt: 1,783 canonical Children,
`+$2,791.87`, PF `1.215`, realized DD `$971.77`. It remains the execution
reference, not the active architecture.

LTF-route Reconstruction A has a hashed 1,477-event ledger and `2,954/2,954`
ordered `Every tick based on real ticks` parity: `+$4,461.37`, PF `1.301`, 554
wins / 922 losses / 1 flat, realized DD `$1,018.77`, equity DD `$1,787.36`,
streak 15 and maximum concurrency 8. This verifies Reconstruction A only; it
does not reproduce the missing interrupted-session q50 ledger.

The next legitimate evidence is predeclared forward shadow after the consumed
cutoff or a genuinely new frozen mechanism. No q65/q70, fitted repair threshold,
sizing or side/year rescue is authorized.
