# V13 right-tail rule audit

Date: `2026-09-28`
Purpose: identify older V13 text whose **current interpretation** changes after
the loss-frequency-first objective update.

## 1. Active authority changed in this package

The following active documents are replaced/updated and now state that right-tail
preservation is a diagnostic rather than an automatic gate:

- repository `AGENTS.md`;
- `docs/ea/v13/AGENTS_V13.md`;
- `docs/ea/v13/HANDOFF_V13.md`;
- `docs/ea/v13/RESEARCH_STATE_V13.md`;
- `docs/ea/v13/V13_DOCUMENT_AUTHORITY_MAP_20260926.md`;
- `docs/ea/v13/V13_HA_RESEARCH_ROADMAP_20260926.md`;
- `docs/ea/v13/V13_HA_RESEARCH_ROADMAP_STATUS_ADDENDUM_20260928.md`.

## 2. Historical documents intentionally not rewritten

Search of the base HEAD found right-tail/long-Journey language in historical
stage contracts and synthesis/receipts, including HA-4/5/6/7/8 materials.
Those files document the hypotheses and rejection logic that existed when those
experiments were frozen. Rewriting them would alter the research record.

Examples include:

- HA-6 contracts requiring long-Journey false-warning accounting;
- HA-7 receipt/synthesis emphasizing the +341.09-point skipped tail subset;
- HA-8A receipt documenting profitable high predicted-flip-risk Children;
- X1/X2 receipts documenting profitable long-Journey false warnings.

Those facts remain valid. What changes is the **current decision rule applied to
new experiments**.

## 3. Superseded active interpretation

Older prose such as:

```text
preserve the large continuation tail
right-tail damage is decisive
continuation tails dominate payoff, therefore reject
```

must not be used by itself to reject HA-9 or later candidates.

Current interpretation:

```text
1. measure ordinary loss reduction and win-rate change;
2. measure loss streak / drawdown / rolling-block quality;
3. measure tail cost and trimmed robustness;
4. judge the complete trade-off, without an automatic tail veto.
```

## 4. What remains mandatory

This update does not authorize hiding tail damage. Top-N winner trimming and
long-Journey decomposition remain mandatory because they show whether an
apparent improvement is merely a different concentration of outliers.
