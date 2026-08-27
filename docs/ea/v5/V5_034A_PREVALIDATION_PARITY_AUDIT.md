# V5-034A — Pre-Validation Replay Parity Audit

Status: `COMPLETED BEFORE EXTERNAL DATA OPEN`
Date: `2026-08-27`
Candidate: `V5_FIRST_CROSS_240M_HALF_EMA_RUNNER`
Production authority: `NONE`

## Purpose

Before consuming the frozen external validation panel, verify that the committed replay:

- reproduces the frozen V5-030A development result on the original development files;
- matches the written order/exit timing contract;
- fails closed on raw-data identity and structural corruption;
- implements the entire V5-034A gate, including deterministic weekly-block uncertainty.

No external validation market and no GOLD# 2021 data were opened during this audit.

## Development bundles re-used for parity only

Uploaded bundle identities:

```text
GOLD#(7).zip
SHA-256 6088ebed8290dd2835df640ae213e49c934cbd9b6c127885e2b661fa27afe455

GoldLike(2).zip
SHA-256 846ec595b732184350adaec12f6cdbcc7e06bfda39c9f65979930b1719160fbb
```

Raw-file identities:

```text
GOLD# 2023  d4991ae1ddefd3fcf049efbf9525270a01c692a53e2c963c558199f829d5ed2f
GOLD# 2024  21518cf93f059b0f44743419320cfd1aa0939b1de7dd8f7cccf0b581a6785160
GOLD# 2025  d8d5f2ecc6e6fb6882209a4bf21e5cd37fbe6e50eea7e09421b0cd7a8b3e7605
BTCUSD#     d477f7063da7e91e959dc4126a4d49b7e8665316012428cb822ab6e97133c9fe
USDJPY#     e86e92724330db492046331f593808f43cc99459a12c0b05a365f02f35450909
XAUEUR#     906a46f0aaead4f8c97c3d569aa143424e3a4fe03431bdc015926092974fef95
```

The files passed the audit used here:
- strictly increasing timestamps;
- no duplicate timestamps;
- valid OHLC geometry;
- finite numeric fields;
- no negative recorded spread;
- all required 2023/2024/2025 years present.

Development self-test point values were:

```text
GOLD#    0.01
BTCUSD#  0.01
XAUEUR#  0.01
USDJPY#  0.001
```

These values reproduce the prior development result exactly before the timing correction. External validation symbol point sizes must still come from the MT5 symbol specification; do not infer them from these values.

## Original replay reproduction

The pre-hardening GitHub replay reproduced the frozen V5-030A development document exactly:

```text
N                    406
WR                   53.9408867%
avg positive net R   +1.196587R
EV                   +0.148050R/trade
total                 +60.108203R
avg spread cost       0.095477R/trade
```

Market Ns/WR/EV and pooled year results also matched the frozen document.

Therefore the uploaded files are the same development authority population used by the current V5 result.

## One timing-parity defect found

The written freeze says a completed adverse 240m signal is executed at the next available M1 open at that signal-bar timestamp, while the BE runner stop remains active intrabar.

The pre-hardening replay checked the same M1 bar's full high/low for BE before applying the open-time adverse exit.

Only one of 406 resolved development trades changed under the contract-correct ordering:

```text
symbol        BTCUSD#
fill          2025-12-09 14:20
+1R partial   2025-12-09 17:40
adverse 240m  2025-12-11 04:00
old outcome   +0.457074R  (same-M1 BE classified first)
contract      +0.503239R  (04:00 M1 open adverse exit first)
delta         +0.046164R
```

This is an implementation-order correction, not a strategy/filter change.

Corrected development self-test:

```text
N                    406
WR                   53.9408867%
avg positive net R   +1.196798R
EV                   +0.148163R/trade
total                 +60.154367R
avg spread cost       0.095477R/trade
```

The development classification remains unchanged:

```text
DEVELOPMENT PASS / VALIDATION REQUIRED
```

## Deterministic uncertainty freeze

Before external outcomes, V5-034A uncertainty is operationalized as:

```text
cluster         = symbol x ISO calendar week of fill_ts
resampling      = observed clusters sampled with replacement
within block    = preserve every trade in the sampled cluster
replications    = 100000
RNG seed        = 5034
interval        = empirical 2.5% / 97.5% quantiles
```

Development self-test produces 347 clusters and:

```text
EV 95%                  [-0.020302R, +0.336264R]
WR 95%                  [49.0244%, 58.8384%]
avg positive net R 95%  [0.966486R, 1.470136R]
```

The lower EV bound still crosses zero. No development claim is upgraded.

## Pipeline hardening

The validation runner now uses two phases:

```text
preflight-only
-> write raw SHA-256 / coverage / integrity audit
-> stop before outcomes

full validation
-> require the saved expected audit
-> verify raw hashes/point/file order unchanged
-> run the immutable candidate
-> compute A-F gates + deterministic bootstrap
```

Full validation fails closed if:
- a file is missing;
- raw SHA-256 changes after preflight;
- point or file order changes;
- timestamps are duplicated or unsorted;
- OHLC is impossible;
- spread is negative;
- required years are absent.

## Current external-data status

The development bundles do **not** contain:

```text
XAUJPY#
XAUCNH#
GAUCNH#
GAUUSD#
```

A File Library search in this session also found no raw M1 files for the frozen external panel.

Therefore V5-034A remains:

```text
FROZEN / EXTERNAL DATA UNOPENED
```

Next empirical action remains acquisition/export of the exact four external 2023-2025 M1 datasets from the same broker/feed family.
