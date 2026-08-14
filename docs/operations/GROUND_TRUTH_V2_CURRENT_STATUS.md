# Ground Truth V2 Current Status

Status: `BLOCKED_CLEAN_MONTHLY_LEDGER_REQUIRED`

## Local Code Status

- Strategy authority: `AGENTS.md`
- Pipeline: `4.51-ground-truth-v2`
- Active Gemini contracts: `PLAN`, `TRIGGER_WATCH`, `DELIVERY_REVIEW`
- Delivery add-on ordering is disabled.
- Delivery FVG replacement SL uses the outer causal structural invalidation;
  FVG distal is not a standalone hard-SL source.
- Current H1/M30 objectives remain primary. At most two distant unconsumed H1
  objectives are retained only as fallback when no current objective provides
  at least `1R` after executable Entry and SL are known.
- Replay/live orchestration, three-risk-slot arbitration, restart, latency,
  fake broker, contract coverage, and Ground Truth finalizer regression suites
  pass locally.
- A Codex usage-limit or timeout failure is now a resumable provider pause;
  semantic or schema failures still seal the run.

## Rejected Diagnostic Ledger R2

Run: `codex_gtv2_june2026_stateful_r2_20260814`

- completed: `true`
- trades: `16`
- total: `-11.1989389920R`
- rejected because eight prohibited Delivery FVG add-ons were ordered and the
  old FVG-distal SL contract was active
- this run is not Ground Truth and cannot be a Gemini benchmark

## Rejected Partial Ledger R3

Run: `codex_gtv2_june2026_stateful_r3_20260814`

- covered only `2026-06-01` through `2026-06-15`
- trades closed: `5`
- partial total: `-0.5879690873R`
- stopped because the isolated Codex provider reached its usage limit
- no Delivery FVG add-on trade was created
- accepted replacement orders use `DELIVERY_CAUSAL_STRUCTURE` SL geometry
- early rejected delivery reviews were made before the final authority and
  contract correction, so the run contains mixed decision contracts
- incomplete coverage and mixed contracts independently disqualify this run
  from Ground Truth status

## Required Clean Run

A new run must start at June 1 with the final, frozen `AGENTS.md`, contracts,
runner, core, and renderer hashes. It must not resume R2 or R3.

After the clean chronological ledger completes, run these independent gates:

1. chronological repeat audit
2. shuffled counterfactual audit
3. daily no-trade MTF audit
4. trigger packet role-evidence audit
5. stateful plan and risk-slot audit
6. accepted-role packet coverage and hash-chain finalization

Only after every gate passes may `output/ground_truth_v2_june2026_v451` be
frozen and used for Gemini parity testing.

## Current Completion Statement

- Local code implementation and synthetic/fake-broker verification: `PASS`
- Frozen June Ground Truth V2: `NOT COMPLETE`
- Gemini comparison against frozen Ground Truth: `NOT RUN`
- Live-shadow parity and real MT5 DEMO fill: `NOT RUN`

Do not claim Ground Truth completion, Gemini parity, or demo/live readiness
until the clean run and all independent audits pass.
