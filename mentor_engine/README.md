# Mentor Scenario Engine

`mentor_engine` is the deterministic research implementation of the 21-video
Mentor Protocol. It does not use the legacy V5-V32 trade authorization rules.

## Pipeline

```text
closed M1 clock
-> H1/M30/M15/M5/M1 waves and structure
-> participant-stop liquidity
-> swing-owned HTF OB and causal LTF OB refinement
-> sweep and source reaction episode
-> M5 correction context
-> M1 sweep and body-close CHoCH confirmation
-> refined LTF OB limit entry, structural SL, scope-compatible objective
```

Standalone HTF FVG sources, first-position FVG execution, and in-position FVG
add-ons are disabled in the baseline. The add-on model remains deferred until
the OB-refinement baseline is reproducible.

The baseline also enforces one active pending order or position. A first
position uses the CHoCH displacement's `LAST_OPPOSITE_OB`; an FVG remains
delivery evidence only. Reusing the same map/source/sweep/CHoCH/entry-OB chain
is rejected.

H1 is the highest active map timeframe. M5 never authorizes an order; it only
establishes the correction leg that the M1 sweep and CHoCH must belong to.

The default Q1 replay loads structure state from 2024-10-01, starts economic
counting on 2025-01-01, and stops before 2025-04-01.

```powershell
npm run test-mentor-engine
npm run replay-mentor-q1
```

Artifacts are written under `output/mentor_engine/GOLD_2025_Q1/`:

- `ledger.jsonl`: every context rejection, scenario, order, and result.
- `trades.csv`: complete map/source/sweep/trigger/objective lineage.
- `summary.json`: timeframe counts, full funnel, economics, and approval gates.
- `VALIDATION.md`: concise gate result and unavailable cost/equity fields.
- `charts/`: selected map/context/trigger charts when matplotlib is available.

## Approval Boundary

Semantic fact coverage is not Casebook chart-replay parity. The current
Casebook has video timestamps and decisions but no machine-readable historical
OHLC fixtures, so `protocolPassed=false` is intentional. Python execution uses
M1 OHLC and spread; it does not claim tick-exact fill order, commission, swap,
or account drawdown. The existing `MentorScenarioTraderEA.mq5` is an
experimental Strategy Tester port and is hard-blocked outside the tester. A
separate live build must not be created until Casebook replay, economic, and
OOS gates pass.
