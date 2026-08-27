## D-178 — Harden V5-034A replay before opening external outcomes

Status: `ACTIVE / FROZEN PRE-VALIDATION IMPLEMENTATION DECISION`
Date: `2026-08-27`

The original V5-034 replay was first reproduced on the exact V5-030A development files. It matched the frozen development result exactly.

A contract-parity audit then found one execution-order defect:

```text
completed 240m adverse signal available at M1 timestamp T
-> contract requires runner exit at M1 open(T)
-> hard BE remains an intrabar order after that open
```

The original code checked the M1 high/low BE condition before the open-time adverse exit. Only one of 406 development trades was affected; correcting it changed pooled EV from approximately `+0.148050R` to `+0.148163R` and did not alter development classification.

This is an implementation-accuracy correction, not candidate retuning.

Before external data are opened, freeze the V5-034A uncertainty implementation as:

```text
block           symbol x ISO calendar week of fill_ts
sampling        blocks with replacement, preserving trades inside each block
replications    100000
seed            5034
interval        empirical 2.5% / 97.5%
```

Validation must run in two phases:
1. preflight-only raw identity/integrity audit;
2. full replay only after the saved audit is supplied and all raw SHA-256 identities still match.

Do not change the Entry, stop, +1R partial, runner logic, timeframe, market panel, or validation gate as a consequence of this hardening.

External panel and GOLD# 2021 remain unopened.
