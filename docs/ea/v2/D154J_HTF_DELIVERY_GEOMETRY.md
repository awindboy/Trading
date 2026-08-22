# D-154J HTF Delivery Geometry — GOLD25 vs CADJPY25

Status: RESEARCH / SHADOW-ONLY / CONTRASTIVE DISCOVERY
Date: 2026-08-23

## Why these two markets

The current 2025 panel has its widest Fill->+1R contrast between GOLD25 (30/53 = 56.6%) and CADJPY25 (30/113 = 26.5%). D-154J deliberately measures both in the same batch and same calendar year.

This does not assume metals and FX need separate strategies. The purpose is to ask whether the same deterministic setup reaches Entry at materially different structural geometry.

## Causal geometry

For H1 and M30 independently, when the timeframe is mature in the trade direction and has valid protected/external boundaries:

```text
span = direction * (external - protected)
progress = direction * (reference_price - protected) / span
remaining_fraction = direction * (external - reference_price) / span
```

Values are not clamped to [0,1]. Overshoot and pre-protected locations remain observable.

When actual Fill risk is known:

```text
remaining_R = direction * (external - reference_price) / original_fill_to_SL_risk
```

## Stage snapshots

- PLAN
- ROOT_CONTACT
- first post-contact same-direction H1/M30 BOS, if any
- SWEEP
- CHOCH
- PENDING
- FILL

Reference price is the latest causally closed M1 close at stage time, except actual Fill which uses actual Fill price; BOS uses that HTF BOS close.

## Research questions

Descriptive only:
- Does CADJPY tend to reach Root contact/CHOCH/Fill later in its active-map delivery span than GOLD?
- Do winners and losses differ in contact->CHOCH or contact->Fill progress delta?
- Is remaining structural room at Fill systematically different across the two markets?
- Does first post-contact BOS occur at different geometry rather than merely different frequency?

## Prohibited

No progress cutoff, remaining-R cutoff, score, market-specific threshold, H1/M30 cherry-pick, direction exception, or Entry/SL/TP/SP/EM change in this phase. Any candidate relation must be frozen later and validated outside GOLD25/CADJPY25.
