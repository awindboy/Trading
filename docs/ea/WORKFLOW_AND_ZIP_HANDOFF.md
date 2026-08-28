# Trading Project Workflow and ZIP Handoff Contract

Status: `ACTIVE PROJECT WORKFLOW AUTHORITY`
Date: `2026-08-29`
Applies to: Trading EA research/documentation/code handoffs
GitHub repository: `awindboy/Trading`

## 1. Single Source of Truth

GitHub is the project's permanent memory and Single Source of Truth.

Every resumed session must:

1. check the latest GitHub HEAD;
2. read root `AGENTS.md`;
3. read root `docs/ea/HANDOFF.md`;
4. read the active generation AGENTS/HANDOFF;
5. read the current research-state/result/contract documents named by that handoff;
6. inspect exact code/data before changing strategy semantics.

Chat history is a workspace, not durable authority. After the user applies, compiles/tests if needed, commits and pushes, the next session must re-read GitHub rather than trusting a previous chat summary.

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

Do not promise background work.

## 3. Research discipline

Preserve deterministic controls. Keep separate:

```text
Entry/event meaning
directional prior
H destination / large-payoff authorization
L correction completion
winner continuation
exit lifecycle
execution
market suitability
portfolio/exposure
```

A variable discovered at one stage has no automatic authority at another stage.

Discovery and validation must remain distinct. No look-ahead, no threshold rescue after opening outcomes, no market selection after observing P/L, and no right-censored outcome relabeling.

Every favorable result must face:
- the opposite thesis;
- a simpler explanation/control;
- year and direction decomposition;
- independent-market decomposition;
- concentration and trade-count checks;
- stage-specific interpretation.

## 4. Trade-count rule

Trade count is an independent promotion dimension.

When the market/time universe expands, the research program should normally gain usable opportunity count rather than converge toward a tiny specialist sample.

Always report:
- total opportunity N;
- causal-state-valid N;
- fill N;
- accepted/exposure-adjusted N;
- N by market-year;
- N by direction;
- trade density relative to the available period.

A filter that improves EV only by collapsing the enlarged panel to a very small sample is downgraded unless it is explicitly a specialist module and the combined architecture still has adequate breadth.

Do not loosen a causal baseline or threshold solely to manufacture more trades.

## 5. Default ZIP delivery standard

For Windows repositories that may live under OneDrive and Korean/Unicode paths, the default handoff is a **script-free repo-relative overlay ZIP**.

The ZIP itself must satisfy all of the following:

```text
ZIP root
├─ docs/
│  └─ ea/
│     └─ ...
├─ scripts/ ... only when needed
└─ mt5/ ... only when needed
```

There must be **no enclosing transport folder inside the ZIP**.

Correct ZIP entry:

```text
docs/ea/v6/HANDOFF_V6.md
```

Incorrect:

```text
Trading_V6_UPDATE/docs/ea/v6/HANDOFF_V6.md
Trading_V6_UPDATE/Trading_V6_UPDATE/docs/ea/v6/HANDOFF_V6.md
```

The user extracts the ZIP directly into the repository root with Windows Explorer and accepts replacement of existing files.

This uses Windows Explorer's native Unicode-path handling and avoids passing the Korean repository path through PowerShell, Python, or generated patch tooling.

## 6. Known failed apply methods — do not repeat by default

The following methods failed in the real project environment and are prohibited as the default ZIP mechanism:

### 6.1 PowerShell 5.1 `git -C <repo path>`

Observed failure:
- Korean path `문서` was corrupted when passed to native `git.exe`;
- Git reported that it could not change into the mangled repository path.

Do not build a package whose correctness depends on PowerShell 5.1 passing the absolute Unicode repo path to `git -C`.

### 6.2 Microsoft Store Python absolute repository file I/O

Observed failure on Python 3.13 from WindowsApps:

```text
OSError: [Errno 22] Invalid argument:
'C:\Users\...\OneDrive\문서\Trading\AGENTS.md'
```

Both `Path.write_text()` and normal Python open/write through the absolute OneDrive+Unicode repository path are therefore not an approved default apply mechanism.

### 6.3 Dynamically generated Git patch as the primary handoff

Observed failure:

```text
git apply --check
error: corrupt patch at line ...
```

A patch may be used only when separately validated and materially necessary. It is not the default documentation/code handoff.

### 6.4 Double-nested launcher packages

Do not depend on a user running a launcher from:

```text
...\PACK\PACK\APPLY.cmd
```

Transport nesting creates avoidable path ambiguity. The overlay ZIP standard removes this class of problem.

## 7. Required preflight before overlay extraction

Every handoff must state its expected base HEAD.

For this package:

```text
ced2bb276ce6471162bcc49af3522eaa3d038694
```

From the `Trading` repository root, before extraction:

```powershell
git rev-parse HEAD
git status --short
```

If HEAD differs from the package's expected base HEAD, **do not force apply**. Re-read the latest GitHub state and rebuild the package.

If target files have unexpected local changes, review them before extraction.

## 8. Apply and review procedure

1. Keep the ZIP outside the repository if practical.
2. Open the ZIP with Windows Explorer.
3. Extract its contents directly into the `Trading` repository root.
4. Accept file replacement.
5. From the repository root run:

```powershell
git status --short
git diff --check
git diff -- docs/ea
```

6. Confirm the transport ZIP itself is not staged.
7. Stage only intended repo files.
8. Commit and push manually.
9. In the next ChatGPT session, re-check the new GitHub HEAD before continuing.

The assistant must not claim a package was successfully applied until the user confirms local review or a subsequent GitHub HEAD shows the update.

## 9. ZIP construction QA

Before giving a ZIP to the user, the assistant must verify:

- expected base HEAD is recorded;
- every ZIP member is repo-relative;
- no duplicate enclosing package directory exists;
- no apply launcher/script exists unless explicitly required;
- UTF-8 text payloads have LF endings and no BOM;
- payload SHA-256 hashes are recorded in a manifest;
- ZIP integrity test passes;
- required research topics are present in the new authority/handoff/result docs;
- no stale active-phase string remains in the current V6 authority documents except when clearly labeled historical;
- code/data artifacts are not silently omitted when the handoff depends on them.

## 10. Deletion rule

An overlay ZIP can add and replace files but cannot safely express deletion by itself.

If a future update requires deletion:
- list the exact repo-relative delete paths separately;
- fail closed on unexpected paths;
- do not hide deletion inside a launcher unless explicitly requested and validated.

## 11. One-line project rule

> Chat is the workbench, GitHub is the memory; research claims survive only when causal definitions, economic breadth, trade count, and recursive falsification survive together.
