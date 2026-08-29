# V7 phase-transition apply package

Base repository: `awindboy/Trading`  
Required exact HEAD: `102791741620ca6cffe061f077d83116a1e46c09` (`V6 validation finish`)

This package does **not** change the V6 EA trading code.

It:
- activates V7 routing;
- closes V6 strategy-semantic development;
- adds V7 research contract/method/results/decisions/backlog;
- adds V6 final validation/close synthesis;
- stores the 24-event V7 discovery ledgers;
- appends global D073-D080 decisions.

## Apply

From PowerShell:

```powershell
cd <path-to-unzipped-package>
powershell -ExecutionPolicy Bypass -File .\apply_v7.ps1 -RepoRoot "C:\path\to\Trading"
```

The script is fail-closed:
- HEAD must be exactly `102791741620ca6cffe061f077d83116a1e46c09`;
- working tree must be clean;
- important existing files must match their expected Git blob SHAs.

Then review:

```powershell
cd C:\path\to\Trading
git diff --check
git diff --stat
git diff -- docs/ea/HANDOFF.md
git diff -- docs/ea/v7
```

Commit/push only after review.

Suggested commit:

```text
V7 Double-B context KTR research transition
```
