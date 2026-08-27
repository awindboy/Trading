# V5-015A — Holy Grail Self-Financing Partial + Maximum EMA Runner Pre-registration

Status: PRE-REGISTERED BEFORE OUTCOME ANALYSIS
Date: 2026-08-27
Parent: V5-014A ratcheting EMA20 runner.
Strategy authority: NONE.

Problem:
A fixed 50/50 partial is arbitrary and can let a published target-first winner become a net losing trade if the runner
reverses. The source says to exit "part" and tighten the balance, without specifying a fraction.

Frozen parameter-free sizing rule at the prior-swing target:
Let:
- T = causal target_R of the published prior-swing objective;
- C = frozen one-spread cost_R;
- runner worst-case structural-stop outcome = -1R gross.

Choose the MINIMUM target fraction f that makes the whole trade net breakeven even if the runner later reaches -1R:

    f = (1 + C) / (1 + T)

If f >= 1, exit 100% at target (no economically financeable runner).
Otherwise:
- exit fraction f at target;
- run fraction (1-f);
- use the unchanged V5-014A ratcheting completed-bar EMA20 stop;
- no runner profit target.

This formula is derived from risk conservation, not fitted performance:
f*T + (1-f)*(-1) - C = 0.

Loss before prior target remains -1R-C.

Promotion gate at one timeframe:
- final net-positive trade rate >=50% pooled and in >=18/24 adequate groups;
- average realized gross winner >1R pooled and median group;
- pooled net EV >0;
- median group net EV >0;
- net EV >0 in >=18/24 adequate groups;
- no single market/year necessary;
- improvement over target-only V5-006B and fixed 50/50 variants in the economic objective.
No partial fraction tuning.
