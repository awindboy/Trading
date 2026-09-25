# V12 Phase 1M — H1 transition Child

Status: **complete, reproducible, failed stability gate**  
Evidence: consumed development history through `2026-09-18 23:57`  
Authority: diagnostic only; no trade or sizing authority

## Result

An H1 `k=1` FAST realignment under a completed-H4 Parent is materially different
from entering every H1 PHA, but it does not yet provide reliable conviction.

| lane | Children | total stops | stops / 100 | win rate | R / unit | PF | equal-total-stop-budget R / H4 unit |
|---|---:|---:|---:|---:|---:|---:|---:|
| H4 core | 6,857 | 1,802 | 26.28 | 32.27% | 0.0557 | 1.139 | 0.0557 |
| H1 k1 | 8,514 | 2,539 | 29.82 | 31.91% | 0.0259 | 1.059 | 0.0229 |
| H1 k1 + H4 FAST | 3,608 | 1,141 | 31.62 | 31.37% | 0.0620 | 1.136 | 0.0515 |
| H1 k1 + H4 FAST/STD | 3,202 | 1,020 | 31.86 | 31.32% | 0.0614 | 1.134 | 0.0507 |

The H4-FAST lane reduces total stops by `36.7%`, maximum stop streak from 11 to
6, and maximum simultaneous units from 21 to 1. At the same total stop budget it
retains `92.4%` of H4 R. Those are real exposure benefits.

They are not a higher-confidence result. Stop density worsens from `26.28` to
`31.62`, win rate falls from `32.27%` to `31.37%`, and 2024 and 2026 are
negative. Pooled net R is `223.57`, but 2023 alone contributes `229.46`; the
other four years sum to `-5.89R`. The top 1% of positive outcomes contributes
`20.7%` of positive R versus `11.5%` for H4. SHORT remains negative. The frozen
four-of-five-year stability gate therefore fails.

## Interpretation

`k=1` is a useful event definition because it removes repeated same-run entries
without an arbitrary cooldown. Its lower stop count comes from fewer independent
attempts, not from a better per-attempt hit rate. The surviving economics are
more tail-concentrated and almost entirely supplied by one consumed year, so the
lane cannot justify larger size.

## Integrity

- Two independent seven-file packs are byte-identical.
- All V12 tests pass (`62`); complete-pack validation passes.
- The source prefix hash is `04e074ca...ec4c939`; no post-cutoff price row was
  parsed and GOLD# 2021 remains sealed.

## Decision

Do not promote H1 `k=1`, H4 alignment, or their combination to trade or sizing
authority. The useful lesson is architectural: lowering the execution clock must
create a native Parent/Child event, not reproduce V10 on smaller bars or obtain
apparent safety by merely reducing frequency. The next defensible lane is the
existing official D1 CRT Parent -> H1 Child mapping, with stop and right-tail
quality judged jointly and H4 retained as context rather than an HA veto.
