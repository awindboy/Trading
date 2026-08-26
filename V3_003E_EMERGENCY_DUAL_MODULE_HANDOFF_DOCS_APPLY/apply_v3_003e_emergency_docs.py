#!/usr/bin/env python3
from pathlib import Path
import argparse, subprocess

EXPECTED_HEAD = '02e5fa578579883f6fdd2ed5936e9d17ff8cb05a'
NEW_DOC = 'docs/ea/v3/V3_003E_DUAL_RELOAD_MODULE_ADVANCES_AND_EMERGENCY_HANDOFF.md'
HANDOFF_APPEND = '\n## V3-003E emergency continuation — 2026-08-26\n\nRead immediately after `V3_003D_DUAL_RELOAD_MODULE_RESEARCH_SYNTHESIS.md`:\n\n```text\nV3_003E_DUAL_RELOAD_MODULE_ADVANCES_AND_EMERGENCY_HANDOFF.md\n```\n\nThis document captures the research completed after V3-003D before the session hit its\nconversation-length limit.\n\nCritical new routing:\n\n```text\nModule L primary payoff:\ncheckpoint=min(1R,0.5D1)\n-> 50% realize\n-> residual BE\n-> residual 2R\n\nModule H stronger eligibility:\nclean M1\n-> direct M1 ownership transfer\n-> 50% pullback research candidate\n-> +3R BE\n-> +5R\n\nModule H BOTH branch:\nshadow exclusion candidate only; NOT frozen\n\nH failure -> later L deep requalification:\nreproducible episode-recovery phenomenon; NOT hindsight routing\n```\n\nMost important operational issue: the prior synthesis referenced a Candidate-A replay script\nthat is not present in the current GitHub HEAD. The next session must commit the complete\nCandidate-A -> Module-L -> Module-H replay/ledger chain **before additional tuning**.\n\nTwo H experiments were started but not completed at the session boundary:\n1. original swept-liquidity body-close failure/invalidation after H fill;\n2. +2R 50%-fraction loss-magnitude/protection variant.\nDo not assume outcomes for either; resume them explicitly.\n\n2022 remains CLOSED. 2021 remains untouched. Other market-state modules remain deferred.\n'
STATE_APPEND = '\n## V3-003E emergency state update — 2026-08-26\n\n```text\nCandidate A raw replay                    REPRODUCED LOCALLY / GITHUB SCRIPT GAP FOUND\nModule L deep requalification             REPRODUCED\nModule L checkpoint 50% + residual 2R      CURRENT PRIMARY PAYOFF CONTROL\nModule L generic-pivot expansion           REJECTED\nModule L mentor-wave expansion             SMALL / EXPLORATORY\nModule H 50% pullback 3R-BE 5R             REPRODUCED\nModule H direct M1 ownership transfer      STRONG H-SPECIFIC DISCOVERY\nModule H BOTH exclusion                    PROMISING / NOT FROZEN / 2025 CAVEAT\nModule H +3R BE                            PRIMARY PROTECTION CONTROL\nModule H +3R 25% harvest                   SECONDARY POSITIVE-FREQUENCY CONTROL\nH -> later L recovery                      REPRODUCED EPISODE PHENOMENON\ncombined H/L economics                     DESCRIPTIVE ONLY / NO PORTFOLIO AUTHORITY\nswept-liquidity body-close H invalidation  PENDING / NOT COMPLETED\nH +2R 50% protection experiment            PENDING / NOT COMPLETED\nother auction-state modules                DEFERRED\n2022                                       CLOSED\n2021                                       UNTOUCHED\n```\n\nImmediate priority is a committed reproducibility pack, then the two pending H experiments,\nthen H remaining-loss taxonomy and L semantic sample expansion.\n'
BACKLOG_APPEND = '\n## V3-003E — emergency continuation backlog\n\n### MUST DO FIRST — repair reproducibility authority\n\n- [ ] Commit common Candidate-A replay engine; prior documented path is missing from GitHub.\n- [ ] Commit Module-L downstream replay + physical dedupe ledger.\n- [ ] Commit Module-H downstream replay + pending/fill ledger.\n- [ ] Reproduce `40/29/27` Candidate-A population exactly.\n- [ ] Reproduce Module-L `11 trades / 11 checkpoint / 10 +1R / mirror 1 checkpoint`.\n- [ ] Reproduce Module-H `48 / 14 TP5 / 31 SL / 3 BE` reference before downstream gates.\n- [ ] Reproduce direct-transfer and BOTH-branch classifications without P/L retuning.\n- [ ] Commit episode IDs linking H failure to later L requalification.\n\n### Module L active\n\n- [ ] Research control: checkpoint=min(1R,0.5D1) -> 50% realize -> residual BE -> residual 2R.\n- [ ] Reproduce 11/11 positive and 7/11 residual-2R on primary physical ledger.\n- [ ] Keep exact mirror in same report.\n- [ ] Study scenario/context lifetime during long virtual-failure -> L-entry waits.\n- [ ] Expand sample only through independent meaningful liquidity semantics.\n- [ ] Keep generic M15 pivots and k=1.0-only additions rejected.\n- [ ] Keep mentor-wave union exploratory until enough unique evidence exists.\n\n### Module H active\n\n- [ ] Keep broken-level H0 as simple control.\n- [ ] Keep 50% pullback H1 as geometry research candidate, not frozen threshold.\n- [ ] Reproduce direct M1 ownership-transfer elimination of non-direct +5R failures across source/pullback panel.\n- [ ] Keep BOTH exclusion shadow-only until caveat is resolved; do not claim 2025 validation where BOTH observations are absent.\n- [ ] Continue remaining 5R-loss taxonomy with no year-specific veto.\n- [ ] PENDING: test body-close back through original swept liquidity as stronger post-fill H invalidation.\n- [ ] PENDING: test +2R existing-50%-fraction protection variant; do not assume it improves H.\n- [ ] Preserve +3R->BE as primary protection unless new test beats it without losing TP5 winners.\n- [ ] Keep +3R 25% harvest as separate positive-frequency robustness control.\n\n### H/L episode interaction\n\n- [ ] Reproduce the 5 H-loss -> later-L-recovery episodes.\n- [ ] Keep H authorization independent; do not hindsight-skip H because L later appeared.\n- [ ] Build deterministic cumulative-risk episode ledger.\n- [ ] Reproduce standalone L non-overlap with H exposure.\n- [ ] Report standalone H, standalone L and combined descriptive performance separately.\n- [ ] Do not promote combined H/L portfolio before exact ordering/exposure rules exist.\n\n### Still forbidden/deferred\n\n- [x] No generic M1 early trigger.\n- [x] No delayed-recovery equivalence.\n- [x] No generic-pivot Module-L sample expansion.\n- [x] No broad SL widening.\n- [x] No +1R/+2R BE for H primary 5R runner.\n- [x] No proof-first H Entry after original Candidate-A +1R.\n- [x] No static HTF gate mining to explain 2023 only.\n- [x] No fixed-10R objective promotion.\n- [ ] Do not open 2022.\n- [ ] Do not touch 2021.\n- [ ] Do not begin other auction-state modules until L/H current work is mature or ceiling documented.\n'
ROOT_PATCH = '\ufeff> **V3 ACTIVE ROUTING — 2026-08-26 / V3-003E EMERGENCY HANDOFF**  \n> Current active research phase is `V3-003D DUAL RELOAD MODULE RESEARCH`; latest continuation record is `docs/ea/v3/V3_003E_DUAL_RELOAD_MODULE_ADVANCES_AND_EMERGENCY_HANDOFF.md`.  \n> Read `docs/ea/v3/AGENTS_V3.md`, `docs/ea/v3/HANDOFF_V3.md`, `docs/ea/v3/RESEARCH_STATE_V3.md`, `V3_003D_DUAL_RELOAD_MODULE_RESEARCH_SYNTHESIS.md`, then `V3_003E_DUAL_RELOAD_MODULE_ADVANCES_AND_EMERGENCY_HANDOFF.md` before any new strategy work.  \n> First task in the next session is to commit/reproduce the missing Candidate-A -> Module-L -> Module-H replay and ledgers. Do not tune before that.  \n> Continue Module L and Module H only. Other auction-state modules remain deferred. 2022 CLOSED; 2021 untouched.\n\n'

def run(cmd, cwd):
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', default='.')
    ap.add_argument('--check-only', action='store_true')
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    here = Path(__file__).resolve().parent

    if not (repo/'.git').exists():
        raise SystemExit('FAIL: not a git repository')
    head_now = run(['git','rev-parse','HEAD'], repo)
    if head_now != EXPECTED_HEAD:
        raise SystemExit(f'FAIL: HEAD {head_now} != expected {EXPECTED_HEAD}')
    # if run(['git','status','--porcelain'], repo):
    #     raise SystemExit('FAIL: working tree is not clean')

    h = repo/'docs/ea/v3/HANDOFF_V3.md'
    s = repo/'docs/ea/v3/RESEARCH_STATE_V3.md'
    b = repo/'docs/ea/v3/BACKLOG_V3.md'
    r = repo/'docs/ea/HANDOFF.md'
    dest = repo/NEW_DOC

    for p in [h,s,b,r]:
        if not p.exists():
            raise SystemExit(f'FAIL: missing {p.relative_to(repo)}')
    if dest.exists():
        raise SystemExit('FAIL: V3-003E document already exists')

    ht = h.read_text(encoding='utf-8')
    st = s.read_text(encoding='utf-8')
    bt = b.read_text(encoding='utf-8')
    rt = r.read_text(encoding='utf-8-sig')

    if '## V3-003E emergency continuation' in ht:
        raise SystemExit('FAIL: HANDOFF_V3 already patched')
    if '## V3-003E emergency state update' in st:
        raise SystemExit('FAIL: RESEARCH_STATE_V3 already patched')
    if '## V3-003E — emergency continuation backlog' in bt:
        raise SystemExit('FAIL: BACKLOG_V3 already patched')
    if 'V3-003D routing update' not in ht or 'V3-003D current state' not in st or 'V3-003D — dual reload module research' not in bt:
        raise SystemExit('FAIL: expected V3-003D authority markers missing')

    if a.check_only:
        print('CHECK PASS')
        print('HEAD', head_now)
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text((here/NEW_DOC).read_text(encoding='utf-8'), encoding='utf-8')
    h.write_text(ht.rstrip()+'\n'+HANDOFF_APPEND.lstrip(), encoding='utf-8')
    s.write_text(st.rstrip()+'\n'+STATE_APPEND.lstrip(), encoding='utf-8')
    b.write_text(bt.rstrip()+'\n'+BACKLOG_APPEND.lstrip(), encoding='utf-8')

    title = '# EA Development Handoff'
    idx = rt.find(title)
    if idx < 0:
        raise SystemExit('FAIL: root handoff title missing')
    r.write_text(ROOT_PATCH + rt[idx:], encoding='utf-8')

    print('APPLY PASS')

if __name__ == '__main__':
    main()
