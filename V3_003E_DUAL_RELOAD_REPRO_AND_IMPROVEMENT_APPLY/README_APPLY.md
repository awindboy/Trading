# V3-003E apply package

Required Git HEAD:

`02e5fa578579883f6fdd2ed5936e9d17ff8cb05a`

This package:

- adds the detailed V3-003E result/handoff document;
- corrects the stale Candidate-A script path in V3-003D;
- adds the missing V3-003D helper used by the integrated replay;
- adds `scripts/v3_003e_dual_module_repro.py`;
- adds immutable Module-L / Module-H / H-L discovery ledgers;
- updates root/V3 handoffs, research state and backlog;
- makes **no EA/MQL5 changes**;
- does **not** open 2022 or touch 2021.

Apply from a clean Trading repository:

```powershell
python apply_v3_003e.py --repo C:\path\to\Trading --check-only
python apply_v3_003e.py --repo C:\path\to\Trading
git diff --check
git diff -- docs/ea/HANDOFF.md docs/ea/v3 scripts/v3_003d_correction_completion_probe.py scripts/v3_003e_dual_module_repro.py
```

Reproduce after apply:

```powershell
python scripts/v3_003e_dual_module_repro.py "<path-to-GOLD-2023-2025-zip-or-csv-dir>" --out .\tmp_v3_003e_repro
```

The replay fails closed if discovery data contain years outside 2023-2025.
