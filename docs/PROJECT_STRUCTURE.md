# Project Structure

## Authority

- Strategy contract: `AGENTS.md`
- Project entry: `README.md`
- Active-system registry: `PROJECT_MANIFEST.json`
- Generated Gemini contracts: `mentor_context_pack/api_contracts/`

## Active Code

- `scripts/mentor_replay_v4_core.py`: replay/live closed-M1 event and execution core
- `scripts/mentor_ai_replay_v4.py`: replay orchestration and model provider routing
- `scripts/mentor_ai_live_v4.py`: MT5 archive, clock, broker reconciliation
- `scripts/build_ground_truth_v2.py`: raw-M1 candidate and audit-ledger builder
- `scripts/audit_ground_truth_v2_codex.py`: independent semantic/execution audits

## Ground Truth Status

There is currently no frozen June 2026 Ground Truth.

`output/ground_truth_v2_june2026_v451` is invalidated and contains a
`BLOCKED_REPORT.md`. Its two trades are forensic evidence only. The defect was
that a physical family was recorded only at its first snapshot, so a later
legally knowable objective was omitted.

The replacement must be stateful: one accepted PLAN remains frozen until a
contractual terminal event. New liquidity that matures while that PLAN remains
valid must not create hundreds of duplicate benchmark candidates.

## Artifact Boundaries

- `output/`: active generated evidence and explicitly blocked runs
- `archive/`: legacy code and superseded outputs; active code must not import it
- `data/`: journal and local secret/config data
- `research/`: mentor-video analysis and research notes

Candidate counts, rendered images, compilation, or passing unit tests are not
Ground Truth completion evidence. Completion requires the audit gates described
in `docs/operations/GROUND_TRUTH_V2_AUDIT.md`.
