from __future__ import annotations

from pathlib import Path
import hashlib
import shutil
import subprocess
import sys

EXPECTED_HEAD = "7cb26133235c45a3756492af951900f15213f8cb"

EXPECTED_BLOBS = {'docs/ea/HANDOFF.md': 'd98e221ffc4b430ee20b289266573b9da41b9373', 'docs/ea/STRATEGY_RESEARCH_STATE.md': 'c1c766bd0c52b66934e705d5188fab86c5950d63', 'docs/ea/BACKLOG.md': '04dda3330558200bdbe41b4a5f6f9cedf5c8bfb7', 'docs/ea/DECISIONS.md': 'b67fa8af44cd4cb9ac907afec0a4f470f4ded447', 'docs/ea/TEST_RESULTS.md': '710445d3b5d80de4cc020d992f64bcd769daa95a', 'docs/ea/v2/HANDOFF_V2.md': '5c97abe6b91d5fbe32e135b08d5e8a991817c002', 'docs/ea/v2/RESEARCH_STATE_V2.md': 'acb3abb5839223f376cb5f52feaa0e4bc3b8d400', 'docs/ea/v2/BACKLOG_V2.md': '6dc2c4926ddbf620accada993e339c400e5276b7', 'docs/ea/v2/D153_MT5_BATCH_AUTOMATION.md': '7126a026319f2efa04fe304a48363b482d29f9b6'}

V2_REPLACEMENTS = [
    Path("docs/ea/v2/HANDOFF_V2.md"),
    Path("docs/ea/v2/RESEARCH_STATE_V2.md"),
    Path("docs/ea/v2/BACKLOG_V2.md"),
    Path("docs/ea/v2/D153_MT5_BATCH_AUTOMATION.md"),
]
NEW_FILE = Path("docs/ea/v2/D152_SP_V3_RESULTS.md")

def git(repo: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", *args], cwd=repo,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    out=(cp.stdout or b"").decode("utf-8",errors="replace").strip()
    err=(cp.stderr or b"").decode("utf-8",errors="replace").strip()
    if cp.returncode != 0:
        raise RuntimeError(err or out or f"git {' '.join(args)} failed")
    return out

def replace_once(s: str, old: str, new: str, label: str) -> str:
    n=s.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: expected one anchor, found {n}")
    return s.replace(old,new,1)

def append_block(s: str, marker: str, block: str) -> str:
    if marker in s:
        return s
    if not s.endswith("\n"):
        s += "\n"
    return s + "\n" + block.rstrip() + "\n"

def verify(repo: Path) -> None:
    head=git(repo,"rev-parse","HEAD")
    if head != EXPECTED_HEAD:
        raise RuntimeError(
            f"unexpected HEAD; expected {EXPECTED_HEAD}, actual {head}"
        )
    for rel, expected in EXPECTED_BLOBS.items():
        actual=git(repo,"rev-parse",f"HEAD:{rel}")
        if actual != expected:
            raise RuntimeError(
                f"unexpected blob for {rel}; expected {expected}, actual {actual}"
            )
        cp=subprocess.run(["git","diff","--quiet","HEAD","--",rel],cwd=repo)
        if cp.returncode != 0:
            raise RuntimeError(f"target has local edits: {rel}")
    if (repo/NEW_FILE).exists():
        raise RuntimeError(f"unexpected existing file: {NEW_FILE}")

def update_root_handoff(repo: Path) -> None:
    p=repo/"docs/ea/HANDOFF.md"
    s=p.read_text(encoding="utf-8")
    s=replace_once(
        s,
        "Repository base before this handoff package: `3ba8e121b567be9043ff524f5a7d2b4936fe5992`",
        "Repository base before this documentation update: `7cb26133235c45a3756492af951900f15213f8cb`",
        "HANDOFF repo base"
    )
    s=replace_once(
        s,
        "Current research phase: **D-152 SP V3 CONTROLLED ARCHITECTURE COMPARISON / LOCAL COMPILE + TEST PENDING**",
        "Current research phase: **D-152 SP V3 MATRIX COMPLETE / V3E PROVISIONAL SP REFERENCE / ENTRY SURVIVAL NEXT**",
        "HANDOFF phase"
    )
    block="""## D-152 completed SP V3 matrix — current routing

The D-153 automated GOLD25/BTCUSD25 real-tick batch is complete and clean.

Primary research result:

```text
V3E BANK_2R_LOCK_ONE
= provisional post-+1R SP reference
= NOT baseline authority
```

Read immediately:

`docs/ea/v2/D152_SP_V3_RESULTS.md`

Key interpretation:

```text
GOLD25 Fill -> +1R = 56.6%
BTC25 Fill -> +1R  = 47.2%

post-+1R management is no longer the primary bottleneck
next primary research = Entry survival
```

Do not perform additional same-sample SP threshold tuning before the Entry-survival causal study.

D-153 batch automation is validated end-to-end and should be reused for subsequent GOLD25/BTC25 research matrices.
"""
    s=append_block(s,"## D-152 completed SP V3 matrix — current routing",block)
    p.write_text(s,encoding="utf-8",newline="")

def update_root_state(repo: Path) -> None:
    p=repo/"docs/ea/STRATEGY_RESEARCH_STATE.md"
    s=p.read_text(encoding="utf-8")
    s=replace_once(
        s,
        "Repository base before handoff package: `b3068c0b445005fe455405ed18fb1f82198231df`",
        "Repository base before current documentation update: `7cb26133235c45a3756492af951900f15213f8cb`",
        "STATE repo base"
    )
    s=replace_once(
        s,
        "Current code/research identity: `2.00R0L0 / V2_CONTINUATION_ONLY_BOOTSTRAP`",
        "Current code/research identity: `2.02R0L2 / V2_SP_ARCHITECTURE_RESEARCH_V3`",
        "STATE identity"
    )
    s=replace_once(
        s,
        "Current research phase: **D-150 V2 CONTINUATION-ONLY FORK**",
        "Current research phase: **D-152 SP V3 COMPLETE / ENTRY SURVIVAL NEXT**",
        "STATE phase"
    )
    old_obj="""The target remains:

```text
realized win rate >= 50%
+
average winner / target meaningfully > 1R
+
positive expectancy after spread/commission/slippage
+
robustness across symbols and periods
```

A 50% win rate at exactly 1R is gross breakeven and is not the project objective.
"""
    new_obj="""The active V2 stretch target is:

```text
cost-adjusted realized win rate >= 70%
+
average winner > 1R
+
positive expectancy
+
robustness across symbols and periods
```

The extreme research frontier is:

```text
all accepted trades final aggregate net R >= +1R
```

This is an aspiration, not a guaranteed property. A 50% win rate at exactly 1R remains insufficient after costs.
"""
    if old_obj in s:
        s=s.replace(old_obj,new_obj,1)
    block="""## D-152 SP V3 completed result

The clean GOLD25/BTCUSD25 matrix establishes `V3E BANK_2R_LOCK_ONE` as the provisional SP reference.

```text
GOLD V3E:
WR 52.83%
final >= +1R 33.96%
avg winner +1.328R
expectancy +0.203R
DD 6.807R

BTC V3E:
WR 44.00% on closed
final >= +1R 32.80%
avg winner +1.225R
expectancy -0.022R
DD 14.233R
```

V3E is not baseline authority.

The key stage ceiling is now Entry survival:

```text
GOLD25 Fill -> +1R = 56.6%
BTC25 Fill -> +1R  = 47.2%
```

At roughly 95% post-+1R positive conversion, the 70% final-WR target would require Fill->+1R survival near 73.7%.

Therefore primary research returns to Entry survival. Additional GOLD25/BTC25 SP threshold tuning is paused.

Detailed result:
`docs/ea/v2/D152_SP_V3_RESULTS.md`
"""
    s=append_block(s,"## D-152 SP V3 completed result",block)
    p.write_text(s,encoding="utf-8",newline="")

def append_root_docs(repo: Path) -> None:
    p=repo/"docs/ea/BACKLOG.md"
    s=p.read_text(encoding="utf-8")
    block="""## D-152 completed / next Entry-survival phase

- [x] Complete GOLD25/BTCUSD25 SP V3 automated matrix.
- [x] Select V3E `BANK_2R_LOCK_ONE` as provisional SP reference.
- [x] Demote V3A/V3B/V3C/V3D for now.
- [x] Reject blanket full-close fallback on broker-infeasible V3E banks.
- [x] Validate D-153 batch automation end-to-end.
- [ ] Pause same-sample SP threshold tuning.
- [ ] Return primary research to `Fill -> +1R` Entry survival.
- [ ] Use shadow-only causal measurement before any real re-entry/Entry change.
- [ ] Keep EM separate until Entry mechanism is understood.
"""
    p.write_text(append_block(s,"## D-152 completed / next Entry-survival phase",block),encoding="utf-8",newline="")

    p=repo/"docs/ea/DECISIONS.md"
    s=p.read_text(encoding="utf-8")
    block="""## D-152 SP V3 matrix decision — 2026-08-22

The clean GOLD25/BTCUSD25 matrix selects `SMART_PARTIAL_V3_BANK_2R_LOCK_ONE` (V3E) as the **provisional post-+1R SP reference**.

This is not baseline promotion and does not change `AGENTS_V2.md` or `EA_SPEC_V2.md`.

Decision rationale:

- V3E most consistently advances the `final net R >= +1R` frontier while preserving average winner >1R.
- Closed +2R cohort finished >=+1R in 11/12 GOLD and 31/31 BTC cases.
- Broker-feasible V3E banks finished >=+1R in 8/8 GOLD and 27/27 BTC cases.
- V3E materially reduced GOLD drawdown and reduced concentration in the largest winners.
- BTC expectancy improved close to breakeven but remains slightly negative, so promotion is not justified.
- V3A/V3B/V3C/V3D are demoted for now.
- A blanket `bank infeasible -> full close` fallback is rejected because 7/8 observed infeasible cases still became >+1R runners.
- Additional same-sample SP threshold tuning is paused.

The next primary bottleneck is Entry survival (`Fill -> +1R`), which remains 56.6% GOLD25 and 47.2% BTC25 in this matrix.
"""
    p.write_text(append_block(s,"## D-152 SP V3 matrix decision — 2026-08-22",block),encoding="utf-8",newline="")

    p=repo/"docs/ea/TEST_RESULTS.md"
    s=p.read_text(encoding="utf-8")
    block="""## D-152 SP V3 automated matrix — 2026-08-22

Batch artifact:

```text
Trading_D152_SP_V3_20260822_044945.zip
SHA256 e28cc77bb7c6419b958fdd77873a1e81fdf546ab9f52c7c776532cdf0e607d37
```

Test universe:

```text
GOLD / BTCUSD
2025.01.01 -> 2025.12.31
M1
Every tick based on real ticks
EM OFF
D151 audit ON
6 SP modes x 2 symbols = 12 runs
```

Integrity:

```text
all terminal return codes = 0
EA_START / EA_STOP present
execution divergence = 0
pending cancel rejection = 0
```

Provisional leader: `V3E BANK_2R_LOCK_ONE`.

GOLD V3E:

```text
53 closed
WR 52.83%
final >= +1R 33.96%
avg winner +1.328R
expectancy +0.203R
total +10.783R
max closed-R DD 6.807R
```

BTCUSD V3E:

```text
127 fills / 125 closed / 2 right-censored
WR 44.00% on closed
final >= +1R 32.80%
avg winner +1.225R
expectancy -0.022R
total -2.750R
max closed-R DD 14.233R
```

No censored trade is imputed.

Detailed matrix and interpretation:
`docs/ea/v2/D152_SP_V3_RESULTS.md`
"""
    p.write_text(append_block(s,"## D-152 SP V3 automated matrix — 2026-08-22",block),encoding="utf-8",newline="")

def main() -> int:
    pkg=Path(__file__).resolve().parents[1]
    payload=pkg/"payload"
    repo=Path.cwd().resolve()

    if not (repo/".git").exists():
        print("ERROR: run from Trading repository root.",file=sys.stderr)
        return 2

    try:
        verify(repo)
    except Exception as e:
        print(f"ERROR: {e}",file=sys.stderr)
        return 2

    # replacements/new V2 docs
    for rel in V2_REPLACEMENTS:
        src=payload/rel
        dst=repo/rel
        if not src.exists():
            print(f"ERROR: payload missing {rel}",file=sys.stderr)
            return 2
        shutil.copy2(src,dst)

    shutil.copy2(payload/NEW_FILE,repo/NEW_FILE)

    try:
        update_root_handoff(repo)
        update_root_state(repo)
        append_root_docs(repo)
    except Exception as e:
        print(f"ERROR during deterministic document transform: {e}",file=sys.stderr)
        return 2

    print("D-152 results documentation update applied.")
    print("EA/source strategy code modified: NO")
    print("V3E status: provisional SP reference, NOT baseline authority")
    print("Next primary research: Entry survival")
    print("")
    print("Review:")
    print(r"  git status --short")
    print(r"  git diff -- docs/ea docs/ea/v2")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
