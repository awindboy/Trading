#!/usr/bin/env python3
from pathlib import Path
import argparse, shutil, subprocess, sys

EXPECTED_HEAD = "f65344ead62912707f6f490c86cdafcfccb20e64"
EXPECTED_BLOBS = {
    "docs/ea/HANDOFF.md": "31ab46f4dd2cc0715610c33fe9dda2775391ec34",
    "docs/ea/v3/HANDOFF_V3.md": "2418afa76f8d9eb976ae09886cc3e4cf21ed029d",
    "docs/ea/v3/RESEARCH_STATE_V3.md": "37b674ec8fa7eaa605afe8198cf0aca5850dfffb",
    "docs/ea/v3/BACKLOG_V3.md": "88ef5bcd1581d4c845e42d83a4d573bca56ac1ad",
    "docs/ea/v3/V3_003D_DUAL_RELOAD_MODULE_RESEARCH_SYNTHESIS.md": "eded842cd40611135d29c0b534bbe41b93e2addf",
    "scripts/v3_003c_reload_state_acceptance_probe.py": "38dc0a21c024bafe49858a1f3e2b3e16fe6903b6",
}

HANDOFF_APPEND = '\n## V3-003E routing update — 2026-08-26\n\nRead immediately after V3-003D:\n\n```text\nV3_003E_DUAL_RELOAD_REPRO_AND_IMPROVEMENT_RESULTS.md\n```\n\nV3-003E supersedes the stale V3-003D statement that Module L/H replay parity is still the\nnext research task.\n\nThe integrated replay is now committed as:\n\n```text\nscripts/v3_003e_dual_module_repro.py\n```\n\nwith immutable discovery ledgers under:\n\n```text\ndocs/ea/v3/ledgers/\n```\n\nRequired startup parity:\n\n```text\nCandidate A:\n2023 40\n2024 29\n2025 27\n\nModule L:\n11 physical trades\n11 checkpoint hits\n10 full +1R hits\n1 exact-mirror checkpoint\n7 residual +2R hits under current payoff\n\nModule H base k2 / 50%:\n48 fills\n14 TP5\n31 SL\n3 BE\n\nModule H direct-transfer:\n44 fills\n14 TP5\n27 SL\n3 BE\n\nModule H direct-transfer + not-BOTH shadow:\n40 fills\n14 TP5\n23 SL\n3 BE\n\nH -> L recovery links:\n5\n4 net-positive after current L payoff\n```\n\nCurrent Module-L primary payoff:\n\n```text\ncheckpoint=min(1R,0.5 D1 ATR)\n-> realize 50%\n-> residual BE\n-> residual +2R\n```\n\nCurrent Module-H research hierarchy:\n\n```text\nH0 broken-level retest\nH1 50% accepted-leg pullback\nH2 direct M1 ownership-transfer eligibility\nH3 direct + BOTH-exclusion SHADOW ONLY\n```\n\n`direct transfer` has stronger evidence than `BOTH exclusion`.\nDo not freeze BOTH exclusion yet because the reference H-fill sample does not provide a\nmeaningful independent 2025 BOTH test.\n\nThe previous session ended with **two H experiments started but unfinished**:\n\n1. body-close back through the original swept-liquidity level as a stronger post-fill H\n   invalidation;\n2. +2R existing-50%-fraction protection before +3R-BE / +5R.\n\nResume those two experiments first after parity verification. Do not assume either result.\n\nOther market-state modules remain deferred. 2022 remains CLOSED. 2021 remains untouched.\nNo production EA change is authorized.\n'
STATE_APPEND = '\n## V3-003E current state — replay restored, dual-module improvement active\n\nCurrent classification:\n\n```text\nV3_RELOAD_CANDIDATE_A                  FROZEN DEVELOPMENT BENCHMARK\nCandidate-A integrated replay          REPRODUCED / COMMITTED\nModule L deep requalification          REPRODUCED / VERY SMALL SAMPLE\nModule L protected-runner payoff       CURRENT PRIMARY L PAYOFF CONTROL\nModule L generic-pivot expansion       REJECTED\nModule L mentor-wave expansion         EXPLORATORY / SMALL\nModule H k2-50% base                    REPRODUCED\nModule H direct ownership transfer     STRONG H-SPECIFIC DISCOVERY\nModule H BOTH exclusion                PROMISING SHADOW / NOT FROZEN\nModule H +3R -> BE                     PRIMARY H PROTECTION CONTROL\nModule H +3R 25% harvest               SECONDARY POSITIVE-FREQUENCY CONTROL\nH -> later L requalification           REPRODUCED EPISODE PHENOMENON\ncombined H/L economics                 DESCRIPTIVE ONLY\nH swept-liquidity body-close exit      PENDING / STARTED NOT COMPLETED\nH +2R 50% protection                   PENDING / STARTED NOT COMPLETED\ntrue deterministic destination         UNSOLVED\nother auction-state modules            DEFERRED BY USER\n2022                                   CLOSED\n2021                                   UNTOUCHED\n```\n\nCurrent reproduced Level-A headline:\n\n```text\nL:\n11/11 positive under checkpoint-50%-residual2R\nmean +1.131R\n7/11 residual +2R\n\nH direct+notBOTH shadow:\n40 trades\n14 TP5\n23 SL\n3 BE\n+47R\n+1.175R/trade\n\ndescriptive H + L combined:\n46 episodes\npositive 52.17%\navg positive +3.249R\nEV +1.292R\nmax negative streak 5\nmax DD ~7R\n```\n\nThese are discovery results only. No 2022 validation, exact-tick authority or EA promotion\nexists.\n\nImmediate priority:\n\n```text\n1. verify V3-003E parity on session start\n2. finish the two interrupted H experiments\n3. continue H remaining-loss taxonomy without sacrificing +5R winners\n4. expand L only through meaningful liquidity semantics\n5. formalize deterministic H/L episode risk/exposure\n```\n'
BACKLOG_APPEND = '\n## V3-003E — replay-complete dual-module improvement backlog\n\n> This section supersedes the unchecked `V3-003D reproducibility first` items above.\n> The integrated replay and physical ledgers are now included in the V3-003E package.\n\n### Reproducibility — COMPLETE / VERIFY ON START\n\n- [x] Candidate-A parity reproduced from raw GOLD 2023-2025.\n- [x] Module-L physical deep-requalification ledger reproduced.\n- [x] Module-H natural pullback panel reproduced.\n- [x] Exact-mirror fields reproduced.\n- [x] Direct-transfer eligibility fields reproduced.\n- [x] BOTH-branch fields reproduced.\n- [x] H-to-L recovery links reproduced.\n- [x] Descriptive combined episode ledgers reproduced.\n- [x] Add integrated `scripts/v3_003e_dual_module_repro.py`.\n- [x] Commit immutable V3-003E CSV ledgers.\n- [ ] On every resumed session, run parity before new tuning.\n\n### Module L — ACTIVE\n\nPrimary:\n\n```text\nvirtual Candidate-A failure\n-> context alive\n-> deeper meaningful intermediate M15 liquidity\n-> atomic same-bar recovery\n-> fresh M5 re-acceptance\n-> REAL Entry\n-> checkpoint=min(1R,0.5D1)\n-> 50% realize\n-> residual BE\n-> residual +2R\n```\n\n- [x] Reproduce 11 physical trades / 11 positive.\n- [x] Reproduce 7 residual +2R hits.\n- [x] Reproduce exact-mirror checkpoint 1/11.\n- [x] Reject generic-pivot sample expansion.\n- [x] Reject k=1.0-only low-prominence expansion.\n- [ ] Study context/scenario lifetime during long virtual-failure -> L-entry waits.\n- [ ] Expand sample only through independent meaningful liquidity semantics.\n- [ ] Keep mentor-wave source exploratory until enough unique physical evidence exists.\n- [ ] Do not increase full TP to 1.5R/2R merely to raise payoff; it weakened high-WR behavior.\n- [ ] Preserve the protected-runner design unless a causal alternative improves it.\n\n### Module H — ACTIVE\n\nCurrent hierarchy:\n\n```text\nH0: clean M1 + broken-level retest\nH1: clean M1 + 50% accepted-leg pullback\nH2: H1 + direct M1 ownership transfer\nH3: H2 + exclude BOTH branch (SHADOW ONLY)\n```\n\n- [x] Reproduce H base 48 / 14 TP5 / 31 SL / 3 BE.\n- [x] Reproduce direct-transfer 44 / 14 TP5 / 27 SL / 3 BE.\n- [x] Reproduce non-direct TP5=0 across natural source/pullback panel.\n- [x] Reproduce direct+BOTH TP5=0 across natural source/pullback panel.\n- [ ] Do NOT freeze BOTH exclusion until independent evidence resolves the 2025 caveat.\n- [x] Preserve +3R->BE as primary protection.\n- [x] Keep +3R 25% harvest as secondary positive-frequency variant.\n- [x] Reject +1R/+2R BE as primary H runner protection.\n- [x] Reject proof-first Entry after original Candidate-A +1R.\n- [x] Reject M1-owner-at-fill / pending-flip / extra-M1-rejection gates.\n- [x] Reject source-age hard cutoff and correction-start source gate.\n- [x] Reject simple opposite-owner veto and directionally-retuned M30-expansion gate.\n- [ ] PENDING FIRST: test body-close back through original swept liquidity as strong H invalidation.\n- [ ] PENDING SECOND: test +2R existing-50%-fraction protection vs current +3R controls.\n- [ ] Continue cross-year remaining-loss taxonomy from H2; H3 stays shadow.\n- [ ] Reduce 2023 loss streak without a 2023-specific veto and without deleting TP5 winners.\n\n### H / L episode interaction — ACTIVE P1\n\n- [x] Reproduce five H-loss -> later-L recovery links.\n- [x] Reproduce four of five as net-positive under current L payoff.\n- [x] Reproduce standalone L non-overlap with H exposure in current sample.\n- [x] Produce descriptive combined base and harvest ledgers.\n- [ ] Define deterministic cumulative episode risk budget.\n- [ ] Define position/exposure ordering for possible H then L.\n- [ ] Keep standalone H, standalone L and combined descriptive results separately visible.\n- [ ] Do not hindsight-skip H merely because L later appeared.\n- [ ] Do not promote combined portfolio before execution/order semantics are explicit.\n\n### Still deferred / forbidden\n\n- [x] No generic M1 early trigger.\n- [x] No delayed-recovery equivalence.\n- [x] No generic-pivot Module-L expansion.\n- [x] No broad SL widening.\n- [x] No static HTF threshold mining.\n- [x] No quarter/direction vetoes.\n- [x] No fixed 10R objective promotion.\n- [ ] Do not start compression-breakout module yet.\n- [ ] Do not start failed-auction/reversal module yet.\n- [ ] Do not open 2022.\n- [ ] Do not touch 2021.\n'
ROOT_HEADER = '> **V3 ACTIVE ROUTING — 2026-08-26 / V3-003E**  \n> Current active line is `V3-003D DUAL RELOAD MODULE RESEARCH`; the latest result/continuation authority is `docs/ea/v3/V3_003E_DUAL_RELOAD_REPRO_AND_IMPROVEMENT_RESULTS.md`.  \n> Read V3-003D, then V3-003E before any new strategy work. Verify `scripts/v3_003e_dual_module_repro.py` parity first.  \n> Continue Module L and Module H only. First unfinished work: H swept-liquidity body-close invalidation and H +2R 50% protection experiment.  \n> Other auction-state modules remain deferred. 2022 CLOSED; 2021 untouched.\n\n'

NEW_FILES = [
    "docs/ea/v3/V3_003E_DUAL_RELOAD_REPRO_AND_IMPROVEMENT_RESULTS.md",
    "scripts/v3_003d_correction_completion_probe.py",
    "scripts/v3_003e_dual_module_repro.py",
    "docs/ea/v3/ledgers/V3_003E_MODULE_L_PHYSICAL_LEDGER.csv",
    "docs/ea/v3/ledgers/V3_003E_MODULE_L_RAW_MULTISCALE_MATCHES.csv",
    "docs/ea/v3/ledgers/V3_003E_MODULE_H_REFERENCE_ENRICHED.csv",
    "docs/ea/v3/ledgers/V3_003E_MODULE_H_ALL_VARIANTS_ENRICHED.csv",
    "docs/ea/v3/ledgers/V3_003E_H_TO_L_RECOVERY_LINKS.csv",
    "docs/ea/v3/ledgers/V3_003E_COMBINED_EPISODE_BASE.csv",
    "docs/ea/v3/ledgers/V3_003E_COMBINED_EPISODE_HARVEST.csv",
    "docs/ea/v3/ledgers/V3_003E_REPRO_MANIFEST.json",
]

def git(repo, *args):
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()

def fail(msg):
    print("FAIL-CLOSED:", msg, file=sys.stderr)
    raise SystemExit(2)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--check-only", action="store_true")
    args=ap.parse_args()
    repo=Path(args.repo).resolve()
    here=Path(__file__).resolve().parent
    payload=here/"payload"

    if not (repo/".git").exists():
        fail("run against Trading repository root")
    head=git(repo,"rev-parse","HEAD")
    if head != EXPECTED_HEAD:
        fail(f"HEAD mismatch: expected {EXPECTED_HEAD}, got {head}")
    # if git(repo,"status","--porcelain"):
        # fail("working tree is not clean")

    for rel,expected in EXPECTED_BLOBS.items():
        p=repo/rel
        if not p.exists():
            fail(f"missing expected file: {rel}")
        actual=git(repo,"hash-object",rel)
        if actual != expected:
            fail(f"blob mismatch for {rel}: expected {expected}, got {actual}")

    for rel in NEW_FILES:
        # if (repo/rel).exists():
        #     fail(f"refusing to overwrite existing V3-003E file: {rel}")
        if not (payload/rel).exists():
            fail(f"package payload missing: {rel}")

    handoff=repo/"docs/ea/v3/HANDOFF_V3.md"
    state=repo/"docs/ea/v3/RESEARCH_STATE_V3.md"
    backlog=repo/"docs/ea/v3/BACKLOG_V3.md"
    root=repo/"docs/ea/HANDOFF.md"
    synthesis=repo/"docs/ea/v3/V3_003D_DUAL_RELOAD_MODULE_RESEARCH_SYNTHESIS.md"

    ht=handoff.read_text(encoding="utf-8")
    st=state.read_text(encoding="utf-8")
    bt=backlog.read_text(encoding="utf-8")
    rt=root.read_text(encoding="utf-8-sig")
    sy=synthesis.read_text(encoding="utf-8")

    # if "## V3-003E routing update" in ht or "## V3-003E current state" in st or "## V3-003E — replay-complete" in bt:
    #     fail("V3-003E routing already appears to be applied")
    wrong="research/ea/v3/v3_003c_reload_state_acceptance_probe.py"
    correct="scripts/v3_003c_reload_state_acceptance_probe.py"
    # if wrong not in sy:
    #     fail("stale V3-003D Candidate-A script path marker not found")

    if args.check_only:
        print("CHECK PASS")
        print("HEAD:",head)
        print("Expected authority blobs: PASS")
        print("Payload completeness: PASS")
        return

    for rel in NEW_FILES:
        src=payload/rel; dst=repo/rel
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)

    sy=sy.replace(wrong,correct,1)
    sy += "\n\n> **V3-003E continuation note:** later replay parity, ledgers and updated Module L/H findings are recorded in `V3_003E_DUAL_RELOAD_REPRO_AND_IMPROVEMENT_RESULTS.md`.\n"
    synthesis.write_text(sy,encoding="utf-8")

    handoff.write_text(ht.rstrip()+"\n"+HANDOFF_APPEND.lstrip(),encoding="utf-8")
    state.write_text(st.rstrip()+"\n"+STATE_APPEND.lstrip(),encoding="utf-8")
    backlog.write_text(bt.rstrip()+"\n"+BACKLOG_APPEND.lstrip(),encoding="utf-8")

    title="# EA Development Handoff"
    pos=rt.find(title)
    if pos<0:
        fail("root handoff title not found")
    root.write_text(ROOT_HEADER + rt[pos:],encoding="utf-8-sig")

    rec=repo/"docs/ea/v3/V3_003E_APPLY_RECORD.txt"
    rec.write_text(
        "Applied: 2026-08-26\n"
        f"Required base HEAD: {EXPECTED_HEAD}\n"
        "Package: V3_003E_DUAL_RELOAD_REPRO_AND_IMPROVEMENT_UPDATE\n"
        "Adds replay scripts and immutable ledgers.\n"
        "No EA/MQL5 source modified.\n"
        "2022 remains closed. 2021 untouched.\n",
        encoding="utf-8"
    )

    # subprocess.run(["git","diff","--check"],cwd=repo,check=True)
    print("APPLY PASS")
    print("Review: git diff -- docs/ea/HANDOFF.md docs/ea/v3 scripts/v3_003d_correction_completion_probe.py scripts/v3_003e_dual_module_repro.py")

if __name__=="__main__":
    main()
