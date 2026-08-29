# Trading Project Workflow and ZIP Handoff Contract

Status: `ACTIVE PROJECT WORKFLOW AUTHORITY`
Date: `2026-08-29`
Applies to: Trading EA research/documentation/code handoffs
GitHub repository: `awindboy/Trading`

## 1. Single Source of Truth

GitHub is the project's permanent memory and Single Source of Truth.

Every resumed session must:

1. check latest GitHub HEAD;
2. read root `AGENTS.md`;
3. read `docs/ea/HANDOFF.md`;
4. read active generation AGENTS/HANDOFF;
5. read current research-state/result/contract files named by that handoff;
6. inspect exact code/data before changing strategy semantics.

Chat history is a workbench, not durable authority.

## 2. Responsibilities

Assistant:
- research design and recursive falsification;
- source/literature research;
- code/review and offline analysis;
- complete repo-relative replacement artifacts;
- documentation and ledgers;
- explicit expected-Git-state checks.

User:
- local Windows/MT5 compile;
- MT5 Strategy Tester execution;
- local Git review;
- commit and push.

## 3. Research discipline

Preserve deterministic controls. Keep separate:

```text
event/source meaning
directional prior
local path / Entry timing
H destination
L monetization
winner continuation
exit lifecycle
execution
market suitability
portfolio/exposure
```

Discovery and validation remain distinct. No look-ahead, threshold rescue after outcomes, outcome-driven market selection, cross-stage authority migration, or right-censored relabeling.

Every favorable result must face:
- opposite thesis;
- simpler control;
- year/direction/market decomposition;
- concentration and trade-count checks;
- causal availability audit;
- stage-specific interpretation.

## 4. Trade-count rule

Trade count is an independent promotion dimension.

Always report:

```text
opportunity N
state-valid N
fill N
accepted N
N by market-year
N by direction
trade density
```

Do not loosen a causal quality condition solely to manufacture trades.

## 5. Default ZIP delivery standard

Default handoff is a **script-free repo-relative overlay ZIP**.

Correct structure:

```text
ZIP root
├─ docs/
│  └─ ea/
│     └─ ...
├─ scripts/ ... only when required
└─ mt5/ ... only when required
```

No enclosing transport folder inside the ZIP.

User extracts directly into the Trading repository root and accepts replacement of existing files.

## 6. Known failed apply methods

Do not use by default:
- PowerShell 5.1 `git -C <Unicode OneDrive path>` apply flows;
- Microsoft Store Python absolute writes through the Korean OneDrive repo path;
- generated Git patch as primary handoff;
- double-nested launcher packages.

## 7. Required preflight

Every package states its expected base HEAD.

For the V6-003D role-conditioned documentation package:

```text
8f9c6e3e03906f2e8b4c146c3b3bb4741f6ad0e2
```

Before extraction, from repository root:

```powershell
git rev-parse HEAD
git status --short
```

If HEAD differs, fail closed and rebuild from latest GitHub.

If target files have unexpected local edits, review them before extraction.

## 8. Apply and review

1. Keep ZIP outside repository if practical.
2. Extract ZIP contents directly into `Trading` root with Windows Explorer.
3. Accept replacement.
4. Run:

```powershell
git status --short
git diff --check
git diff -- docs/ea
```

5. Confirm transport ZIP itself is not staged.
6. Stage only intended files.
7. Commit and push manually.
8. Next session re-checks new GitHub HEAD.

The assistant must not claim the package was applied until user confirmation or a later GitHub HEAD shows it.

## 9. ZIP construction QA

Before delivery verify:
- expected base HEAD recorded;
- every ZIP member repo-relative;
- no duplicate enclosing package directory;
- no apply launcher unless explicitly required;
- UTF-8 LF text, no BOM;
- payload SHA-256 hashes recorded in manifest;
- ZIP integrity passes;
- required research topics are present;
- no stale active-phase string remains in current V6 authority documents included in the package;
- code/data artifacts are not silently omitted when the handoff depends on them.

## 10. Deletion rule

Overlay ZIP adds/replaces files but does not safely encode deletion. Any future deletion must be listed separately and fail closed on unexpected paths.

## 11. One-line project rule

> Chat is the workbench, GitHub is the memory; research claims survive only when causal definitions, economic breadth, trade count, and recursive falsification survive together.
