# EA Test Results

No baseline EA Strategy Tester results yet.

## Required reporting format

For every significant V1 test record:

- EA version / commit
- symbol
- broker
- account mode if relevant
- tester period
- tester model
- trading period
- H4 history first date
- H1 history first date
- M30 history first date
- M15 history first date
- M5 history first date
- M1 history first date
- H4 active long-horizon liquidity count at READY
- bootstrap READY time / `execution_epoch_start`
- startup source context
- magic number
- sizing mode
- submitted volume
- spread / commission assumptions
- number of strategy-valid signals
- number of submitted orders
- number of execution-infeasible signals
- number of rejected orders
- number of filled trades
- win / loss
- profit factor
- expectancy in R
- max drawdown if available
- protocol violations
- execution divergences
- known implementation defects

Profitability results are invalid if known protocol violations remain.