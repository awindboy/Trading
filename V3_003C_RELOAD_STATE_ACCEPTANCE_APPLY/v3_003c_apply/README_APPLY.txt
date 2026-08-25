V3-003C Reload State × Local Acceptance Apply Package

Required Git HEAD:
785768f3bcefd4abf8cd4cff4009ae2f7bf57482

What it does:
- adds the immutable V3-003C result document;
- adds the standalone Level-A reproduction script;
- updates HANDOFF_V3, BACKLOG_V3 and DECISIONS;
- freezes V3_RELOAD_CANDIDATE_A as a research/development benchmark;
- makes NO EA source changes;
- does NOT open 2022 or 2021.

Apply from a clean Trading repository root:

    python <unzipped-package>/apply_v3_003c.py

The installer fails closed if the Git HEAD or expected project markers do not match.

Reproduce the main Level-A research from the accepted GOLD ZIP:

    python scripts/v3_003c_reload_state_acceptance_probe.py "<path-to-GOLD-zip>"

Optional slower source-scale sweep:

    python scripts/v3_003c_reload_state_acceptance_probe.py "<path-to-GOLD-zip>" --sensitivity
