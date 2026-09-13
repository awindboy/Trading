# V9 Mechanical Policy Freeze Candidate

Date: `2026-09-14`
Status: `ACTIVE RESEARCH FREEZE CANDIDATE / NOT PRODUCTION AUTHORITY / NOT HIDDEN-DATA PERMISSION`
Base evidence: `V9_CHALLENGE_EXIT_EXPOSURE_COST_RUNTIME_CHECKPOINT_20260914.md`
Market: `GOLD# ONLY`

## Policy

```text
1. Reconstruct causal H1/H4 from authoritative revealed M1.

2. H4 liquidity uses two-left / two-right swing geometry.
   Object is usable only after the second right H4 bar is complete.

3. Maintain:
   PRIMARY_ACTIVE(side)
   CHALLENGED / UNRESOLVED

4. Eligible Arrival:
   Grammar resolves to PRIMARY_ACTIVE at an H4-liquidity Arrival.

5. Entry:
   if no Child is already open,
   enter immediately in PRIMARY_ACTIVE direction
   using the Arrival boundary as the research price reference.

6. SAME_NEAREST:
   record as continuation-quality context only.
   Do not require it for entry.

7. Hard SL:
   LONG  -> highest active known H1 SSL below entry
   SHORT -> lowest active known H1 BSL above entry
   using causal two-left / two-right H1 liquidity.

8. Hard SL is frozen before entry and never widened.
   No valid H1 structural SL -> no Child.

9. Exposure:
   one active Child at a time for the frozen baseline.
   This is a studied exposure convention, not a retry limit.

10. Open Child:
    same-side H4 liquidity Arrival -> HOLD.

11. First opposite H4 liquidity Arrival:
    PRIMARY_ACTIVE -> CHALLENGED
    -> FULL EXIT Child.

12. While CHALLENGED:
    no new directional Child.

13. Next H4-liquidity resolution:
    old primary wins or challenger earns.
    The resolving Arrival returns Grammar to PRIMARY_ACTIVE
    and may authorize a fresh immediate Child.

14. Same-M1 Hard-SL / semantic-exit ordering:
    INTRAMINUTE_EXECUTION_AMBIGUOUS.
    Never choose an invented ordering.
```

## Explicit non-rules

No:

- fixed TP;
- minimum R;
- SAME_NEAREST ratio threshold;
- fixed-GOLD SL;
- cooldown;
- retry cap;
- no-chase distance;
- duration timeout;
- trade/day quota;
- forced LONG/SHORT balance;
- AI trade selection;
- LTF confirmation trigger.

## Current consumed evidence

One-position, H1 structural SL, CHALLENGED full exit:

```text
2024      +43.84R / PF 2.41
2025H1    +20.29R / PF 3.20
2026JF     +8.08R / PF 3.08
combined  +72.21R / PF 2.63 / DD 4.43R
```

At 1x observed M1 spread sensitivity:

```text
combined +71.16R / PF 2.59
```

At 3x observed spread stress:

```text
combined +69.06R / PF 2.50
```

This document freezes the consumed-data research candidate only.
Exact executable fill authority and hidden-data permission remain separate gates.
