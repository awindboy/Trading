# V11 reassembly and capital-timing architecture

Date: `2026-09-23`

Status: `RESEARCH ARCHITECTURE / CONSUMED DEVELOPMENT EVIDENCE / NO TRADE, WAIT, SIZING, OR PRODUCTION AUTHORITY`

## Why this architecture exists

V11 must not remain a V10 entry filter with a few substituted indicators. V10 bundled several distinct decisions into one action:

```text
PHA candidate appears
-> decide participation
-> commit the selected 1/3-unit risk immediately
-> use one Child Hard SL
-> use the FAST campaign exit
```

The reassembly separates five authorities:

1. **candidate creation** — whether a new market attempt exists;
2. **initial participation** — the minimum risk that preserves the right to join;
3. **elastic journey-level capital inventory** — when, how much, and which Child owns additional conviction risk;
4. **Child interruption/termination** — when the funded attempt ends;
5. **new-direction authorization** — whether an opposite independent attempt exists.

This adds a missing capital-funding state before the existing neutral-bridge problem. A candidate can exist causally without receiving full risk immediately. Its prospective Hard SL is still frozen before observation, and touching it kills that candidate even if no capital was funded.

## V10 component reassembly

| Component | Retained information | Reassembled role |
| --- | --- | --- |
| verified raw M1 | touch truth and chronology | causal guard and HTF reconstruction |
| FAST H4 HA | responsive low-noise campaign clock | candidate creation and campaign shell |
| STD H4 HA | smoother state and current structural geometry | interruption/restart coordinate, not wholesale base |
| SLOW H4 HA | deeper synthetic persistence | Parent/capital-ceiling coordinate, not confirmation gate |
| ATR180 | liquidity-era scale | normalize all distances and process rates |
| M15/M30/H1 summaries | causal cross-scale context | funding-state evidence, never automatic direction authority |
| R4 selected-score heads | historical 0/1/3 participation | candidate eligibility separated from actual funding |
| R5 STOP heads | probability the current Hard SL is touched | funding-risk coordinate |
| R5 conditional-R heads | value conditional on surviving | survival-value coordinate |
| R5 scalar EV | collapsed STOP and conditional-R state | demoted to comparator; preserve the two axes separately |
| R7G feedback | prior-exited 180-H4 sizing overlay | maximum funding ceiling after readiness, not automatic immediate deployment |
| normalized MA state | Parent health | continuous context only |
| Wave/M5 process | intrabar settlement/process | candidate funding evidence only if it adds stable value |
| liquidity event grammar | NHA context | interruption interpretation only |
| Hard SL | Child falsification | frozen before observation; never widened |
| first opposite FAST HA | campaign exit | comparator exit clock independent of funding clock |

The retained feature registry contains 84 coordinates: 33 engineered cross-scale, 21 M15/M30/H1 summaries, 13 causal prior ranks, six FAST/STD/SLOW HA coordinates, five path/churn, five trend/direction, and one normalized Child-risk coordinate.

## First stage-0 evidence

The first audit matched the MT5 embedded-model event export to the causal transition ledger and the selected-R7G audit. It recovered `626/626` non-warmup R7G-intended FAST-k1 Children from 2024 through partial 2026.

The fixed +60/+120/+180-minute entries remain old mechanism probes. They were re-evaluated only to test the user's complete economic criterion rather than raw-R retention alone.

The +180-minute probe was the only one that improved the combined frontier materially:

```text
                            immediate     +180m probe
trades                           626             544
Hard SL                          133              65
Hard-SL rate                  21.25%          11.95%
win rate                      35.78%          39.34%
structural R                 +117.31R        +122.00R
R7G-weighted R               +279.65R        +259.82R
max stop streak                    3               2
1% unit-risk max drawdown      26.74%          21.84%
```

Thus it retained `86.9%` of intended trades, removed `51.1%` of Hard SLs, raised win rate by `3.56pp`, increased unweighted structural R by `4.0%`, and retained `92.9%` of R7G-weighted R.

The no-cost sequential compounding illustration ended at `10.47x` for immediate funding and `9.94x` for the +180-minute probe at 1% risk per unit. Matching the immediate policy's observed `26.74%` drawdown allowed `1.234%` risk per unit and ended at `15.80x`. This is consumed, post-selected, cost-free evidence and does not grant sizing authority.

## Critical failures and caveats

- `180 minutes` is not a discovered market law. It is a post-hoc fixed checkpoint already prohibited as a trading rule.
- The effect was not economically symmetric. LONG weighted R was nearly preserved (`267.50R -> 266.31R`), while SHORT changed from `+12.15R` to `-6.49R`.
- Existing R5 outputs did not identify who benefited from waiting. Spearman correlation of wait-versus-immediate weighted-R delta was `0.010` with `P(STOP)` and `0.022` with `E[R|non-stop]`; median-quadrant effects changed sign by year.
- The compounding illustration omits spread, slippage, fill lifecycle, and simultaneous portfolio constraints.
- The result covers selected k1 Children only, not the full R7G portfolio.

## Stage-1 and Stage-2 reassembly

The leakage-corrected Stage-1 study reconstructed all 84 V10 coordinates, added causal Wave/liquidity/checkpoint state, and finally added the separate R5 stop and conditional-R heads. Prior-year action-value models still could not select immediate/+60/+120/+180 funding reliably. On 2025-2026, the least defensive all-parts policy retained `90.6%` of weighted R but funded only `62.7%` of candidates and retained `72.5%` of L6 positive R. The binary selective-funding model is rejected.

Stage 2 therefore separates **participation size** from **conviction size**:

```text
selected FAST k1 candidate
-> one unit participates immediately
-> remaining R7G ceiling stays dormant
-> a later causal event may release the ceiling
```

The first event comparator is same-direction FAST continuation into k2 with the original k1 Hard SL retained as the pre-release guard. Across the 626 selected Children it preserved 100% candidate participation, reduced stopped loss-units `279 -> 183`, reduced three-unit full stops `73 -> 25`, and reduced adjacent three-unit stop pairs `10 -> 1`. Combined R fell `279.65R -> 220.79R`, but 1%-unit drawdown fell `26.74% -> 19.92%`; at equal observed drawdown the descriptive ending multiple changed `10.47x -> 14.17x`.

This is a retained architecture lead, not a sizing rule. Conventional stopped Children remain `133 -> 133`, because the initial unit is always exposed.

## Stage-3 and Stage-4 portfolio boundary

The complete `1,649`-Child replay retained the k1 ladder as a mechanism comparator: stopped units fell `486 -> 390`, three-unit full stops fell `127 -> 79`, and `92.06%` of combined R remained. The full portfolio also exposed the limitation hidden by k1-only accounting. Maximum concurrent gross exposure stayed at `48` units because independently selected k2+ Children continued to recreate their own R7G allocations.

A more fundamental one-slot journey architecture then preserved one unit on every Child and allowed only one shared two-unit conviction tranche per FAST run. It cut peak exposure to `18` and stopped units to `320-332`, but retained only `56.9-59.3%` of R and lost the equal-drawdown frontier. The fixed one-slot cap is rejected.

Stage 5 showed that absolute R retention was not the decisive issue. The one-slot cap blocked `550` requests with only `5.27%` stop incidence and `+243.02R`; it removed mature-run edge. The k1 ladder, by contrast, reduced cross-run full-size stop pairs `13 -> 2` and alternating-direction pairs `9 -> 0` while retaining `92.06%` of R. New-run transition risk and established-journey conviction must therefore be different capital states.

The active object is **elastic capital inventory** with three explicit layers: one-unit participation, transition conviction earned by causal continuation, and same-run damage/repair governing only future extra requests. It is not a fixed wait, binary entry filter, unlimited per-Child ceiling, or fixed campaign cap.

## Research decision

The retained lead is **capital staging as a separate strategy dimension**, not a 180-minute wait or a binary selector.

The next mechanism must ask:

> Can a valid candidate receive small participation risk while the full causal V10 state controls when, and how much of, the dormant R7G ceiling is released?

The action target is therefore not next HA, regime, generic STOP, or a visual Wave label. It is the incremental value, ownership, persistence, and loss burden of each additional capital unit. Any model must use chronological outer-year tests, preserve `P(STOP)` and conditional-R as separate coordinates, and compare complete policies on the scalable-performance frontier. Failure to predict binary funding value closes the selective-model branch; it does not authorize the fixed +180-minute probe. FAST k2 remains an event comparator, and the complete portfolio is now the minimum evaluation surface.

## Reproduction

- scripts: `research/v11/analyze_v11_reassembly_stage0.py` through `analyze_v11_reassembly_stage5_damage_inventory.py`;
- ignored outputs: `output/v11_reassembly_stage0_20260922/` through `output/v11_reassembly_stage5_20260923/`;
- source event SHA-256: `c4348a34aa35d1e9793283cebbf1a028327c10e3e1c5a4fde2a9e74e3ff801a7`;
- source episode SHA-256: `e4f87448c89472a2322692051e496a9b60c62adbe2401640c3660e3492b54e0d`;
- selected-audit SHA-256: `2258b4cd35f814bbd324d2a4207323ea89a555e3bbe15f2b8e313aa7168409a9`.
