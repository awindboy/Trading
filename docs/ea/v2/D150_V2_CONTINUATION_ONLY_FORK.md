# D-150 — V2 Continuation-Only Fork

Date: 2026-08-22
Status: `IMPLEMENTED PACKAGE / LOCAL COMPILE PENDING`
Fork base: `123b41c880dbce2a17d560b4b7b081934d744700`
Target: `2.00R0L0 / V2_CONTINUATION_ONLY_BOOTSTRAP`

## Decision

The project stops developing first-position reversal trading and creates a new V2 line dedicated to trend-following continuation.

This is not a result-driven one-symbol veto. It is a project-scope decision based on the accumulated research direction: the active solution work is already continuation-specific, reversal has not produced a durable positive contribution, and mixing it into equity curves obscures the problems V2 is now trying to solve.

## Separation contract

```text
V1 file remains untouched.
V1 documents/history remain reproducible.
V2 gets a new EA file and V2 authority documents.
```

V2 code is forked from the current D149 V2 harness only to retain deterministic execution and research instrumentation. The reversal draft assignment is removed from the V2 path; legacy reversal state code remains inert/diagnostic for compile compatibility.

## Three V2 research programs

```text
A. Runner discrimination
   +1R-only reaction vs true 2R+ continuation

B. Profit preservation
   protect accumulated profit without truncating the multi-R tail

C. Genuine loss architecture
   explain <1R failures and clustered loss episodes, then choose prevention/re-entry/exposure solutions
```

These programs must not be collapsed into one score.
