# V8 Backlog

Status date: `2026-08-31`
Active phase: `V8-B INTERNAL-ONLY DIRECTION / SEQUENTIAL EVIDENCE`

## V8-A — frozen

- [x] +/-10.0, 15m/30m/60m movement target.
- [x] Portable 53-feature causal M1 model.
- [x] MT5 movement-probability indicator.
- [x] Python/MQL equation parity.
- [x] Exact continuous 2024-2026 M5 probability reconstruction for internal research.
- [ ] Keep V8-A unchanged while direction research continues.

## Direction corrections

- [x] Invalidate V8-B1 M15/H1 lookahead.
- [x] Add permanent HTF availability regression guard.
- [x] Cancel stale B1 MT5 direction implementation.
- [x] Reject delayed-response results that keep the original C0 after waiting.
- [x] Independently rebuild selective direction tails.
- [x] Reject non-reproducible 70-90% direction-tail result.
- [x] Separate movement-filter effect from direction via directional excess.

## Internal-only V8-B experiments completed

- [x] V8-A snapshot as direction input.
- [x] V8-A trajectory / slope / acceleration / shape.
- [x] Price + V8-A joint sequence.
- [x] Small temporal CNN.
- [x] Event-centered geometry.
- [x] Causal regime canonicalization.
- [x] Directional semivariance/body/wick/activity decomposition.
- [x] Tick-activity / signed price-impact proxies.
- [x] Score fusion / stacking.
- [x] All-M5 direction training.
- [x] Recent-year / rolling-retraining controls.
- [x] Event-family direction diagnostics.
- [x] Confidence-tail selection.
- [x] Exact independent B28 reconstruction.
- [x] Non-overlap and cluster-bootstrap checks on exact rebuild.

## Immediate internal research

- [ ] Finish exact V8-A trajectory × event-family matrix.
- [ ] Test V8-A rising/falling/extreme-state interactions without outcome-tuned thresholds.
- [ ] Build sequential WAIT policy with fixed observation delays.
- [ ] At every delayed decision reset C0 and targets to current price +/-10.0.
- [ ] Compare t=0 vs t=+1/+3/+5/+10m under identical recentered targets.
- [ ] Report move rate, conditional direction accuracy, chosen hit and directional excess.
- [ ] Report MAE/MFE and whether opposite barrier/path damage occurs first.
- [ ] Run outcome-blind non-overlap.
- [ ] Split robustness by month, hour, event family and predicted direction.
- [ ] Use weekly/monthly block bootstrap.
- [ ] If no stable direction remains, stop retrospective feature mining and move to prospective human-direction labels.

## Explicitly de-scoped

- [x] External/cross-market V8-B2 source-of-move branch is not active.
- [ ] Do not reopen external markets without an explicit project decision.

## MT5 direction implementation

- [ ] No direction companion yet.
- [ ] Only implement after a strictly causal, independently reproducible candidate survives 2024 discovery -> 2025 validation -> 2026 stress.

## Final validation

- [x] 2022-2026 remain open development.
- [ ] Keep GOLD# 2021 locked.
