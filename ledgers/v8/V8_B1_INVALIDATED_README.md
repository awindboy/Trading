# V8-B1 ledger status

Status: `INVALIDATED_BY_HTF_LOOKAHEAD`

Existing V8-B1 ledgers committed before this correction (including the old robustness/joint/bootstrapped positive-result files) were computed from a direction feature table contaminated by future-completed M15/H1 bars.

They are retained only as forensic history and must not be used as positive direction evidence.

Corrected causal ledgers in this directory are prefixed:

`V8_B1_CAUSAL_...`

Leak examples:

`V8_B1_HTF_LEAK_EXAMPLES.csv`

Authoritative explanation:

`docs/ea/v8/V8_B1_CAUSAL_ALIGNMENT_INVALIDATION.md`
