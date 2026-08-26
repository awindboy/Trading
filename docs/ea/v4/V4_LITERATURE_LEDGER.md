# V4 Literature / Open-Source Ledger

Status: `ACTIVE RESEARCH INPUT / NOT STRATEGY AUTHORITY`
Last research pass: `2026-08-27`

Purpose: prevent V4 from becoming a closed loop around the assistant's prior knowledge. New major model families,
pretraining objectives, RL algorithms or agent architectures must be checked against current literature and
maintained open-source implementations before adoption.

## L-001 — Kronos

- Paper: `Kronos: A Foundation Model for the Language of Financial Markets`, arXiv:2508.02739, accepted AAAI 2026.
- Repo: `https://github.com/shiyu-coder/Kronos`
- Pinned repo commit for V4 diagnostic: `67b630e67f6a18c9e9be918d9b4337c960db1e9a`.
- License: MIT.
- Public model used first: `NeoQuasar/Kronos-mini`, ~4.1M parameters, tokenizer `Kronos-Tokenizer-2k`.
- Reported pretraining: >12B K-line records from 45+ exchanges; specialized K-line tokenizer + autoregressive model.
- V4 value: finance-native transfer prior and counterexample to training every representation from scratch.
- V4 caveat: public documentation does not give a sufficiently clear temporal cutoff for every pretraining source;
  an open 2026 upstream issue explicitly asks for this clarification. Therefore 2023-2025 local performance is
  `TRANSFER_DIAGNOSTIC_ONLY`, not pristine OOS evidence.
- Do not import: downstream trading claims without our own cost/OOS protocol.

## L-002 — Fin-JEPA

- Repo: `https://github.com/cedricwyh/fin-jepa`
- Pinned research reference commit: `58506d6e31ecb2c65f9c69ea1f1bc146ef08f8b9`.
- License: MIT.
- Public description: ~367K parameters, 64-d representation, PriceEncoder, 4-layer causal Transformer predictor,
  SIGReg collapse prevention.
- Original domain: daily equity features, not MT5 minute broker bars.
- V4 value: motivates testing predictive latent self-supervision before supervised return labels.
- V4 adaptation: `V4_001_MarketJEPA` reuses our frozen causal patch information set, predicts the same target market's
  next 15m latent state, then freezes the encoder for a linear direction probe.
- Important: this is an original project adaptation, not a reproduction claim.

## L-003 — MOMENT

- Paper: `MOMENT: A Family of Open Time-series Foundation Models`, ICML 2024 / arXiv:2402.03885.
- Repo: `https://github.com/moment-timeseries-foundation-model/moment`
- Reference commit: `38f7310ad594100747ca2a8357e9c7ca7d323e0e`.
- Package: `momentfm==0.1.5`.
- First V4 external model: `AutonLab/MOMENT-1-small`, ~37.9M parameters, embedding mode available.
- V4 value: generic TS foundation-model transfer control against finance-specific pretraining.
- V4 caveat: external pretraining corpus means local 2023-2025 performance is not pristine V4 validation.

## L-004 — TSFM benchmark-integrity warning

- Research: `Time Series Foundation Models: Benchmarking Challenges and Requirements`, arXiv:2510.13654 (2025).
- Key V4 lesson: as foundation-model pretraining corpora grow, spatiotemporal overlap and global-event memorization
  can invalidate supposed OOS comparisons. Future-time and domain isolation must be explicit.
- Action: R3/R4 cannot promote a V4 candidate unless pretraining provenance becomes sufficiently auditable.

## L-005 — Financial multivariate TSFM transfer evidence

- Research: `Time Series Foundation Models for Multivariate Financial Time Series Forecasting`, arXiv:2507.07296.
- Reported lesson: pretrained TSFMs can improve sample efficiency, but specialized models may still equal or exceed
  them; domain-specific adaptation matters.
- Action: tournament keeps from-scratch, domain-specific self-supervision and external pretraining as separate axes.

## Later RL ledger requirement

Before V4-002 chooses PPO/SAC/CQL/IQL/Decision Transformer/other methods, add a new literature pass covering the
exact sequential-control problem, offline-data support, non-stationarity, risk objective and execution model.
No RL algorithm is pre-selected by this ledger.
