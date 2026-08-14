# MentorScenarioTraderEA

This is the first executable MT5 port of the Mentor Protocol. It is a
research baseline, not an approved live strategy.

The decision chain is:

```text
H1/M30 trend and OB owner
-> M15/M5 causal refinement
-> M1 source touch and liquidity sweep
-> M1 body CHoCH
-> CHoCH displacement OB retest
-> fixed external swing objective
```

The EA uses only closed bars for decisions. Source invalidation is checked on
the owner timeframe, not by an arbitrary M1 close. A pending order is GTC and
is cancelled when the source is invalidated, the objective is delivered before
entry, or the pending order disappears. After a position is filled, the EA
does not apply a time exit or a structure exit; the initial SL/TP decide the
result.

This research build sends orders only inside Strategy Tester.
`InpEnableLiveTrading` is retained for `.set` compatibility but cannot enable
live orders. A separate reviewed live build will be required after protocol
parity, economic, and OOS gates pass. The EA writes diagnostic lines to the
Experts log and, when enabled, to:

`MQL5/Files/trading_journal/mentor_scenario_events.jsonl`

Do not compare the tester's number of trades to the manual replay as an exact
parity result yet. First compare owner timeframe, source zone, sweep, CHoCH,
entry, SL, and TP for the same week.
