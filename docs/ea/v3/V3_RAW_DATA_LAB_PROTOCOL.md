# V3 Raw Data Lab Protocol

Status: `ACTIVE DATA CONTRACT`
Date: `2026-08-24`

## 1. Preferred exchange format

Do not use MT5's internal history binaries as the normal file handoff.

Internal terminal files are useful as a cache but are not the preferred V3 analysis format:

```text
M1 internal history: *.hcc
tick internal history: *.tkc
```

Export to CSV from MT5.

## 2. Where MT5 keeps downloaded history

In MT5:

```text
File
-> Open Data Folder
```

Then broker history is normally under:

```text
<bases>\<broker-server>\history\<symbol>\
```

Minute history is stored internally as yearly HCC files.

Example shape:

```text
...\bases\<XM-server>\history\GOLD#\2025.hcc
```

Real tick cache is normally under:

```text
<bases>\<broker-server>\ticks\<symbol>\
```

Example:

```text
...\bases\<XM-server>\ticks\GOLD#\
```

Tick cache is stored internally in TKC files, commonly by month.

Do not copy/delete these while MT5 is running.

## 3. Best way to export data for V3

Recommended built-in MT5 route:

```text
Market Watch
-> right click
-> Symbols
-> Bars tab
```

Then:

1. select `GOLD#`;
2. select `M1`;
3. set the requested date range;
4. click `Request`;
5. verify the actual returned start/end;
6. click `Export`;
7. save as CSV.

For ticks:

```text
Symbols
-> Ticks tab
-> select GOLD#
-> date range
-> Request
-> Export
```

The built-in M1 CSV normally contains:

```text
DATE
TIME
OPEN
HIGH
LOW
CLOSE
TICKVOL
VOL
SPREAD
```

Tick CSV normally contains timestamp plus Bid/Ask/Last/volume/flags fields available
from the broker feed.

## 4. First V3 upload request

Upload **only discovery data first**:

```text
symbol:
GOLD#

period:
2023-01-01 through 2025-12-31

timeframe:
M1

required:
DATE
TIME
OPEN
HIGH
LOW
CLOSE
TICKVOL
SPREAD

preferred:
VOL / real volume too, if MT5 exports it
```

Either is acceptable:

```text
GOLD#_M1_2023.csv
GOLD#_M1_2024.csv
GOLD#_M1_2025.csv
```

or one continuous file covering all three years.

ZIP compression is preferred.

## 5. Do NOT upload yet

Do not upload for V3 discovery:

```text
2022
2021
```

2022 is reserved as the V3 validation vault.
2021 stays untouched.

Also do not start by uploading multi-gigabyte tick history unless requested.

## 6. Tick-data request order

After the M1 laboratory identifies promising strategy families, V3 will request
tick data only where exact intrabar ordering matters.

Likely first request:

```text
GOLD# ticks
specific discovery year/month windows
```

If full-year tick export is manageable, use one year per ZIP.

If manual MT5 tick export truncates the requested range, do not silently combine
partial data. Record actual first/last timestamp and report the limitation.

## 7. Metadata to send with the CSV

Include a small text file or message containing:

```text
broker:
account type:
server:
symbol exact name:
symbol path/category:
digits:
point:
tick size if known:
contract size if known:
exported server-time range:
```

For the current project this matters because execution environment and symbol
specifications have changed measured friction materially.

## 8. Data-quality rules

V3 ingestion must fail closed on:

- non-monotonic timestamps;
- duplicated M1 timestamps unless explicitly reconciled;
- missing required OHLC;
- high < max(open, close, low);
- low > min(open, close, high);
- negative spread;
- unexplained large date gaps inside expected trading sessions;
- requested/actual date-range mismatch.

Weekend/holiday closures are not treated as missing data by themselves.

## 9. Higher timeframes

Do not export M5/M15/M30/H1/H4 separately for normal V3 research.

V3 will rebuild them from M1 to guarantee one causal clock and consistent aggregation.

Small MT5 samples of higher-timeframe bars may later be used only to verify aggregation parity.

## 10. Why M1 first

M1 is small enough for rapid repeated experiments and is the canonical base history
from which MT5 builds higher timeframes.

It is sufficient for most:
- structure;
- liquidity;
- zone;
- session;
- trigger;
- first-retest;
- standardized barrier

research.

Ticks are added later for exact execution and same-bar ordering.
