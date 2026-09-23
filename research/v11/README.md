# V11 research code inventory

V11 is a frozen Wave Candle predecessor. V12 is active.

## Retained implementation

- `../../mt5/indicators/V11WaveCandle.mq5`: MT5 H4 Wave Candle v0.5, rendering completed-M5 settlement density around selectable FAST/STD/SLOW HA or raw OHLC shells without drawing an LTF path.

## Consumed-data representation diagnostic

- `analyze_v11_wave_edge.py`: fixed comparison of the outer H4/FAST-HA shell versus the same shell plus frozen Wave coordinates, both on the completed pre-entry H4 and at a forming-H4 +60m checkpoint. Outputs are development evidence only and remain under ignored `output/`.
- `analyze_v11_liquidity_arrival_wave.py`: chronological raw-M1 reconstruction of causal H1/H4 swing-liquidity objects, their consumption by the completed pre-entry H4, the still-active destination topology at the R7G decision, and Wave settlement relative to the consumed boundary. It fixes three layers—outer shell, plus liquidity topology, plus liquidity-relative Wave—and keeps all ledgers and model outputs under ignored `output/`.
- `analyze_v11_ha_flip_liquidity_reason.py`: event-semantic diagnostic separating a completed PHA's causal context into H4 arrival, farther H4 route, local H1-only context, or no known liquidity context, then describing an immediate NHA as arrival response, in-transit counterflow, local rotation, or unanchored rotation. Future run fields are outcomes only.
- `analyze_v11_std_ha_liquidity_reason.py`: matched FAST-versus-STD base reconstruction. It independently rebuilds each HA run and Child from causal H4, replays the prior-STD-HA structural stop on raw chronological M1, validates the FAST side against the official 6,770-row V10 universe, and compares flip churn, stop burden, liquidity explanations, k1 transfer, and right-tail sensitivity.
- `analyze_v11_neutral_bridge.py`: one-pass raw-M1 transition-episode replay. It rebuilds M5/H4 in-stream, freezes completed-NHA and +60/+120/+180-minute forming-Wave observations, kills prospective opposite Children on pre-authorization Hard-SL touch, and compares raw progress, Wave efficiency, liquidity context, extra HA confirmation, stop chains, and descriptive risk capacity. Its fixed times and causal rolling median are mechanism probes only.
- `analyze_v11_post_stop_chain.py`: downstream sequential audit of the frozen causal transition ledger. It activates defensive logic only after an actual stop and reports stops prevented, non-stops and positive R discarded, repeat-stop events, maximum streak, and total R. It is the authority for interpreting neutral-bridge selectivity.
- `analyze_v11_reassembly_stage0.py`: joins the user-supplied embedded-model event export to the causal FAST-k1 transition ledger and the selected-R7G audit, inventories the retained V10 component/feature families, and evaluates immediate versus fixed delayed funding probes on trade coverage, stop burden, win rate, structural/weighted R, and descriptive risk capacity. Fixed waits remain mechanism probes only.
- `analyze_v11_reassembly_stage1.py`: reconstructs the exact 84-coordinate V10 feature registry and runs leakage-corrected prior-year sequential action-value models for immediate/+60/+120/+180 funding. It records the rejected binary selective-funding branch.
- `analyze_v11_reassembly_stage2.py`: keeps one immediate unit on every selected k1 Child and audits release of the remaining R7G ceiling at fixed probes, Stage-1 model actions, and a raw-M1 causal FAST-k2 event. It measures stopped loss-units separately from stopped Children.
- `analyze_v11_reassembly_stage3_portfolio.py`: restores all 1,649 resolved selected R7G Children, independently selected k2+ allocations, tranche overlap, realization order, and concurrent gross/net exposure around the retained k1 capital ladder.
- `analyze_v11_reassembly_stage4_campaign_capital.py`: reassigns two-unit conviction capital from each Child to one shared causal slot per FAST journey, compares k1-continuation versus new-Child priority, and records rejection of the fixed one-slot architecture.
- `analyze_v11_reassembly_stage5_damage_inventory.py`: audits which stop types and extra-capital requests Stage 4 removed, separates cross-run from same-run full-size stop chains, and tests the frozen same-run Hard-SL damage plus one-surviving-Child repair state machine.
- `analyze_v11_new_skeleton_phase_space.py`: final ledger-independent causal-H4
  experiment. It compares FAST, STD, SLOW, and a STD/SLOW-memory phase skeleton
  without using V10 selected events or stop labels.
- `analyze_v11_new_skeleton_progress_ladder.py`: capital-release audit on the
  independent STD/SLOW-memory skeleton. It distinguishes lower full-size stop
  burden from actual stopped-Child recognition.

## Local-only development output

Visual prototypes, compile logs, generated metrics, and temporary comparison renders stay under ignored `output/`. They are not authority or independent validation.

## Current boundary

No V11 trading rule, EA, or production artifact exists. The retained Python
runners generate consumed-data diagnostics only. V11 is closed; V12 owns all new
strategy research.
