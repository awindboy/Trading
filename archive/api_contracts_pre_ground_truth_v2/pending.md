# PENDING contract
- Lifecycle is PREPARED -> ARMED -> TRIGGERED -> PENDING -> FILLED or CANCELED.
- Reauthorize owner, scope, objective, source freshness, and protected swing at each new H1/M15 close. Only lastReauthorizedAtUtc may change.
- Cancel before fill on objective-first, root/child body invalidation, protected-swing break, full POI consumption, opposing owner, stale episode, or map not reauthorized.
- Never change frozen entry/SL/TP after order creation. After fill, only original SL or TP judges the scenario.
- DELIVERY_FVG_REPLACEMENT is allowed only for an already frozen unfilled OB scenario after clear same-objective displacement creates a fresh FVG plus causal OB/protected swing. The frozen original may be an unfilled broker order or an engine-owned `HTF_OB_REACTION_INTENT` whose root, child, entry, invalidation, and objective were fixed before the replacement review. Cancel the old OB intent, use only the first FVG retest, keep the same TP, and never hold both orders.
- DELIVERY_FVG_ADDON remains disabled.
