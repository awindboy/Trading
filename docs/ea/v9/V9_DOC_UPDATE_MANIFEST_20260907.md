# V9 Documentation Update Manifest — 2026-09-07

Purpose: complete repo-relative documentation replacement/addition package for the current V9 research state.

## Base-state guard

Expected Git HEAD before applying:

```text
0880cafaac8752e2976ca970244dab6a215955d9
```

If local/repository HEAD differs unexpectedly, **fail closed** and compare the newer V9 authority before replacing files.

Authoritative raw M1 SHA256 used by the replay/audit:

```text
626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2
```

GOLD# 2021 was not opened.

## Files in this package

### Complete replacements

- `docs/ea/v9/HANDOFF_V9.md`
- `docs/ea/v9/RESEARCH_STATE_V9.md`
- `docs/ea/v9/V9_PAPER_TRADING_JOURNAL_20260907.md`

### New authority/research documents

- `docs/ea/v9/DECISIONS_V9_ADDENDUM_20260907.md`
- `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_EXIT_DISTANCE_OPEN_ROUTE_20260907.md`
- `docs/ea/v9/results/V9_CAUSAL_REPLAY_202501.md`
- `docs/ea/v9/results/V9_CAUSAL_REPLAY_202601.md`
- `docs/ea/v9/results/V9_JAN_2025_2026_DEEP_REVIEW_20260907.md`
- `docs/ea/v9/results/V9_EXIT_DISTANCE_SHADOW_AUDIT_20260907.md`
- `docs/ea/v9/results/v9_exit_distance_20260907/V9_EXIT_SHADOW_AUDIT_A_vs_C.csv`

## What this update records

- January 2026 sequential discretionary replay through the user-selected stopping point;
- all V9-PAPER-001 through V9-PAPER-007 development trades;
- January 2025 full-month period-transfer replay and its one structural loss;
- 2025/2026 deep review of market-reading portability and strategy robustness;
- exact previous-completed H4 ATR14 distance normalization for the audited entries;
- A full-CP1-exit vs C 50/50 structural-runner shadow audit;
- downgrade of naive partial/passive runner architecture;
- identification of `capture latency` as an exit bottleneck;
- `SEQUENTIAL CONTINUATION RE-ENTRY` as the main continuation challenger;
- `OPEN ROUTE / PRICE DISCOVERY` as a separate research state;
- requirement that open-route trades still have a nearby thesis-dependent anchor;
- execution-continuity distinction from structural falsification;
- tightened journal requirements for genuine restoration and parent-context effect;
- next research contract and formalization prohibitions;
- continued 2021 lock.

## Not included / intentionally unchanged

- no V9 EA or code;
- no indicator/classifier/score/threshold/veto;
- no root `AGENTS.md` rewrite because the active V9 routing itself did not change;
- no replacement of historical `DECISIONS_V9.md`; new decisions are appended through the routed addendum;
- no rewrite of the original manual-replay archaeology document;
- no modification of V8 or earlier-generation authority;
- no production-performance claims.

## Suggested apply sequence

1. verify HEAD;
2. extract this ZIP at repository root;
3. inspect `git diff -- docs/ea/v9`;
4. verify only the listed V9 documentation files changed/appeared;
5. commit/push the documentation update;
6. on the next session, refresh GitHub HEAD before resuming research.
