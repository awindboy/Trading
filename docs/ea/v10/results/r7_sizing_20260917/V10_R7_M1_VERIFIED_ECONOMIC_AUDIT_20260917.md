# V10 R7 M1-Verified Economic Audit — 2026-09-17

Research-only. No authority or EA promotion. GitHub main at audit: `aa7685b9e243ddff058f0dbcdb8e416260b41244`.

## Unit semantics
`target_pnl` is GOLD price movement per 1 unit, not MT5 account-currency profit. The raw-M1 builder defines `pnl = direction * (exit_price - entry)`.
Account-money columns below use an explicit sensitivity only: starting reference balance $1,000, fixed non-compounding risk budget 1% = $10 per unit-R. They exclude commission, lot rounding, slippage and campaign-risk limits. M1 spread is converted to R before the 1% sensitivity.

## Parity
- Authoritative raw M1 SHA256 matches the committed R3 hash.
- 2,182 non-stop Children: M1 open-to-open PnL exact parity.
- 658 STOP Children: first M1 stop-touch timestamp exact parity 658/658; 8 are gap/open-stop flags.

## Overall
| Policy | Units | Net R | PF_R | Spread-adj R | Raw price-PnL | Spread-adj price-PnL | 1% fixed-risk net USD |
|---|---:|---:|---:|---:|---:|---:|---:|
| R4_BASE | 3095 | 485.07 | 1.583 | 463.89 | 23,234.65 | 22,590.76 | $4,638.89 |
| R7G_ALL | 3881 | 741.01 | 1.682 | 712.86 | 30,883.72 | 30,074.67 | $7,128.65 |
| R7G_NO_K3P_SHORT | 3815 | 754.42 | 1.711 | 726.75 | 30,194.87 | 29,397.62 | $7,267.54 |

## Year — R7G_NO_K3P_SHORT
| Year | Net R | Spread-adj R | Raw price-PnL | Spread-adj price-PnL | 1% fixed-risk net USD |
|---|---:|---:|---:|---:|---:|
| 2024 | 45.47 | 39.41 | 204.86 | 110.52 | $394.09 |
| 2025 | 471.46 | 455.99 | 11,768.64 | 11,370.73 | $4,559.90 |
| 2026 | 237.49 | 231.36 | 18,221.37 | 17,916.37 | $2,313.55 |

## Quarter — R7G_NO_K3P_SHORT
| Quarter | Net R | Spread-adj R | Raw price-PnL | Spread-adj price-PnL | 1% fixed-risk net USD |
|---|---:|---:|---:|---:|---:|
| 2024Q4 | 45.47 | 39.41 | 204.86 | 110.52 | $394.09 |
| 2025Q1 | 211.21 | 204.89 | 2,961.88 | 2,854.70 | $2,048.87 |
| 2025Q2 | 52.72 | 49.08 | 3,545.83 | 3,425.01 | $490.85 |
| 2025Q3 | 58.97 | 56.19 | 837.40 | 776.06 | $561.94 |
| 2025Q4 | 148.55 | 145.82 | 4,423.54 | 4,314.97 | $1,458.24 |
| 2026Q1 | 161.04 | 159.26 | 13,458.69 | 13,345.02 | $1,592.57 |
| 2026Q2 | 26.73 | 25.17 | 2,105.99 | 2,020.87 | $251.69 |
| 2026Q3 | 49.72 | 46.93 | 2,656.69 | 2,550.48 | $469.30 |

## Stage — R7G_NO_K3P_SHORT
| Stage | Net R | Spread-adj R | Raw price-PnL | Spread-adj price-PnL | 1% fixed-risk net USD |
|---|---:|---:|---:|---:|---:|
| k1 | 279.65 | 267.22 | 8,136.19 | 7,835.11 | $2,672.24 |
| k2 | 151.89 | 145.93 | 5,126.28 | 4,971.90 | $1,459.26 |
| k3p | 322.88 | 313.60 | 16,932.40 | 16,590.61 | $3,136.04 |

## Direction — R7G_NO_K3P_SHORT
| Direction | Net R | Spread-adj R | Raw price-PnL | Spread-adj price-PnL | 1% fixed-risk net USD |
|---|---:|---:|---:|---:|---:|
| LONG | 767.75 | 749.26 | 24,928.74 | 24,421.54 | $7,492.61 |
| SHORT | -13.34 | -22.51 | 5,266.14 | 4,976.09 | $-225.07 |

## Run length — R7G_NO_K3P_SHORT
| Run length | Net R | Spread-adj R | Raw price-PnL | Spread-adj price-PnL | 1% fixed-risk net USD |
|---|---:|---:|---:|---:|---:|
| L1-2 | -485.26 | -493.45 | -15,497.77 | -15,677.44 | $-4,934.49 |
| L12+ | 588.71 | 586.57 | 25,652.42 | 25,579.69 | $5,865.72 |
| L3-5 | -177.67 | -186.92 | -9,373.23 | -9,637.22 | $-1,869.23 |
| L6-8 | 409.12 | 403.89 | 10,213.09 | 10,034.74 | $4,038.85 |
| L9-11 | 419.52 | 416.67 | 19,200.36 | 19,097.85 | $4,166.69 |

## Exit — R7G_NO_K3P_SHORT
| Exit | Net R | Spread-adj R | Raw price-PnL | Spread-adj price-PnL | 1% fixed-risk net USD |
|---|---:|---:|---:|---:|---:|
| FAST_HA_EXIT | 1228.42 | 1205.84 | 43,739.08 | 43,036.21 | $12,058.36 |
| STOP | -474.00 | -479.08 | -13,544.21 | -13,638.59 | $-4,790.82 |

## Key diagnostics
- R7G upgrade-only economics: 393 upgraded Children, 166 winners / 227 losers; +15,602.22 raw price-profit vs -7,953.15 raw price-loss = +7,649.07 net price-PnL.
- Upgrade run-length split: L1-2 -4,037.55 price-PnL; L3-5 -924.02; L6-8 +2,436.67; L9-11 +2,811.40; L12+ +7,362.57.
- k3p SHORT upgrades: -13.41R but +688.85 raw price-PnL. This divergence is why risk-based and raw-price economics must be reported separately.
- R7G_NO_K3P_SHORT run-block bootstrap vs R4: observed +269.35R; 95% [118.37R, 442.21R], P(delta>0)=99.99% on consumed evidence.
- Max concurrent diagnostic exposure: R4 40 units; R7G and NO_K3P_SHORT 48 units. At 1% risk per unit this would imply 48% nominal committed risk, so the fixed-risk USD sensitivity is not a production equity simulation.
- M1 spread stress assumes 0.01 price point and Bid-bar convention: long pays entry spread, short pays exit spread. Commission/slippage are not modeled.