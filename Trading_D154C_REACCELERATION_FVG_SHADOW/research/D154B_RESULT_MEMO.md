# D-154B Result Memo — Immediate Confirmation Entry Rejected

Date: 2026-08-22  
Status: **DISCOVERY COMPLETE / UNIVERSAL IMMEDIATE-CONFIRMATION ENTRY REJECTED**

Question tested:

```text
TRANSITION at actual Fill
-> first same-direction post-Fill M1 INITIAL_BOS
-> immediate executable shadow Entry
-> original normalized SL
-> recomputed +1R
```

Result:

| Market | shadow candidates | +1R | SL | survival |
|---|---:|---:|---:|---:|
| GOLD | 20 | 6 | 14 | 30.0% |
| BTCUSD | 26 | 16 | 10 | 61.5% |
| pooled | 46 | 22 | 24 | 47.8% |

Among the same 46 candidates, the immediate confirmation Entry rescued zero baseline failures while converting six baseline +1R successes into shadow failures.

Decision:

1. Do not promote `INITIAL_BOS -> immediate market Entry`.
2. Treat same-direction owner completion as a possible state-confirmation fact, not a sufficient price.
3. Test whether a **new post-confirmation displacement/FVG retracement** can restore entry geometry.
4. Do not combine this with post-SL re-entry, EM, or SL redesign.
