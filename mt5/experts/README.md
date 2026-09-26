# Operational Expert Advisors

`TradeJournalExporterEA.mq5` remains the operational journal/export utility.

## Active V13 research EA

`V13HAOnlyMax10EA.mq5` implements the frozen V13 Baseline 0:

```text
standard completed H4 Heikin-Ashi only
one Child per completed same-color H4 HA bar
maximum 10 Children per Journey
first opposite completed H4 HA closes all and reverses
no SL / no TP / no filter / no ML
```

It is a research/tester EA only and has no live-trading authority.

The EA requires hedging position accounting so each Child remains independently
visible in MT5 history. It fails closed on execution errors instead of silently
retrying.

V12 has no active strategy EA. Existing V10 EAs are frozen historical
comparators and do not represent V13.
