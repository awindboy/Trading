#!/usr/bin/env python3
"""Recover the mixed 72c0d4c D-145 repository state without changing strategy semantics."""
from pathlib import Path
import locale, os, shutil, subprocess, sys

EXPECTED_HEAD='72c0d4c35affaaa671407188dc5c18fb41550a96'
PACKAGE_ROOT=Path(__file__).resolve().parents[1]
PAYLOAD=PACKAGE_ROOT/'payload'
TARGETS=[
 'mt5/experts/MentorDeterministicV1EA.mq5',
 'mt5/experts/EdgeAuditV1.mqh',
 'docs/ea/HANDOFF.md','docs/ea/BACKLOG.md','docs/ea/BASE_EDGE_AUDIT_2025.md',
 'docs/ea/EDGE_AUDIT_V1.md','docs/ea/STRATEGY_RESEARCH_STATE.md',
 'docs/ea/REACTION_ENTRY_BARRIER_AUDIT.md','docs/ea/RUNNER_CONTEXT_AUDIT.md',
 'docs/ea/DECISIONS.md','docs/ea/TEST_RESULTS.md',
]
REPLACEMENTS=['HANDOFF.md','BACKLOG.md','BASE_EDGE_AUDIT_2025.md','EDGE_AUDIT_V1.md','STRATEGY_RESEARCH_STATE.md','REACTION_ENTRY_BARRIER_AUDIT.md','RUNNER_CONTEXT_AUDIT.md']
D144_DECISION="\n\n---\n\n## D-144 — Measure Root reaction and entry timing with standardized exact-tick barriers before changing strategy\n\nStatus: ANALYZED ON GOLD 2025 / SUPERSEDED FOR BROAD RUNS BY D-145 / STRATEGY AUTHORITY UNCHANGED — 2026-08-21\n\n### Trigger\n\nThe six-symbol D-143 front-end panel showed three simultaneous effects:\n\n```text\n1. H1/M30 bearish continuation classification is weak as an unconditional forward direction signal.\n2. Root Contact frequently recovers a local scenario-direction response, including in trades that later lose.\n3. The response deteriorates materially by the current CHoCH/FVG timing, while one directional premise can fan out into repeated Root/PLAN exposure.\n```\n\nSimple static front-end filters did not reveal a robust path to the user's eventual `>=50%` realized win-rate objective. D-144 therefore changes the measurement geometry, not the strategy.\n\n### Frozen D-144 measurement\n\nResearch identity:\n\n```text\nbuild = 1.92R1L6\nphase = REACTION_ENTRY_BARRIER_AUDIT_V1_EXACT_TICK\nstrategy semantics = D134_EXECUTION_CORE_UNCHANGED\nstrategy authority = NONE\n```\n\nStages:\n\n```text\nROOT_CONTACT\nSWEEP\nCHOCH\nFVG\nACTUAL_FILL\n```\n\nFrozen targets:\n\n```text\n+1.0R vs -1R\n+1.5R vs -1R\n+2.0R vs -1R\n```\n\nNo target is chosen by optimization.\n\n### Comparable stage R\n\nAt each preplanned physical Root Contact, the first tick at/after the causally known contact close freezes:\n\n```text\nROOT_OB_DISTAL_20 stop geometry\n+\nmarket-executable scenario-direction entry side\n=\ncontact_R\n```\n\nThe same absolute `contact_R` distance is reused for ROOT_CONTACT, SWEEP, CHOCH and FVG virtual market entries. This isolates stage timing/information loss from a changing R scale.\n\nEvery stage is measured in:\n\n```text\nSAME_DIRECTION\nFLIPPED_DIRECTION\n```\n\nLONG outcome barriers use Bid and SHORT outcome barriers use Ask. First-hit ordering is therefore taken from exact tester ticks, not reconstructed from M1 OHLC.\n\n### Actual fill\n\nACTUAL_FILL uses:\n\n```text\nfill_R = abs(fill_price - normalized_sl)\n```\n\nThe same-direction tracker is the directly relevant standardized entry-edge test. The flipped tracker uses the same numeric fill and R only as a direction-isolation control and is explicitly non-executable as an opposite market fill.\n\nIf the fill is not observed in the same whole second as `fill_at`, exact fill barrier reconstruction is refused and logged as skipped.\n\n### Governance\n\nD-144 does not add:\n\n```text\nSHORT veto\nowner-age cutoff\nRoot-count cutoff\nH1/M30 agreement gate\nCHoCH reference filter\nTP replacement\nSL replacement\n```\n\nA stage crossing 50% in pooled 2025 data is not sufficient for promotion. Breadth by symbol/month/direction and later untouched validation remain required.\n\n`2021 = KEEP UNTOUCHED`.\n\n### First exact-tick evidence — GOLD 2025\n\n```text\ncontinuation fills = 51\nstructural TP winners = 14 / 27.45%\n+1R before SL = 30 / 58.82%\n+1.5R before SL = 25 / 49.02%\n+2R before SL = 20 / 39.22%\n\n+1R split:\nLONG 21/35 = 60.00%\nSHORT 9/16 = 56.25%\n```\n\nThe stage/mirror fan-out increased tester time by roughly 9x, so D-144 is retained as evidence but not used for broad runner-context runs.\n"
D145_DECISION='\n\n---\n\n## D-145 — Study 1R exhaustion versus 2R+ delivery from causal market context, not R optimization\n\nStatus: PREPARED LIGHTWEIGHT SHADOW RESEARCH / STRATEGY AUTHORITY UNCHANGED — 2026-08-21\n\n### Trigger\n\nThe first D-144 exact-tick run on GOLD 2025 showed that the same continuation fills behave very differently under standardized reward geometry:\n\n```text\n51 continuation fills\ncurrent structural-TP winners = 14 / 51 = 27.45%\n+1R before -1R              = 30 / 51 = 58.82%\n+1.5R before -1R            = 25 / 51 = 49.02%\n+2R before -1R              = 20 / 51 = 39.22%\n```\n\nThis is not permission to choose the R point whose pooled hit rate looks best. The project objective is `>=50%` win rate with meaningful reward greater than 1R, so the research problem is now conditional continuation:\n\n> among entries that already prove themselves by reaching +1R, what causally-known market background distinguishes 2R+ delivery from exhaustion before 2R?\n\n### D-145 measurement identity\n\n```text\nbuild = 1.92R1L7\nphase = RUNNER_MARKET_CONTEXT_AUDIT_V1_LIGHTWEIGHT\nstrategy semantics = D134_EXECUTION_CORE_UNCHANGED\nstrategy authority = NONE\n```\n\nThe expensive D-144 Root/Sweep/CHoCH/FVG mirror-barrier fan-out is removed. D-143 front-end forward labels are also disabled because that census is complete.\n\nTick-active research objects are limited to:\n\n```text\nselected execution FVG waiting for actual Fill\nactual filled runner\n```\n\n### Fill snapshot\n\n`EDGE_AUDIT_RUNNER_FILL_SNAPSHOT` freezes only information causally known at Fill, including:\n\n```text\ncurrent H1/M30 map/owner/BOS/PB state\ncurrent H1/M30 protected->external range position and remaining room in actual R\ncurrent latest-12 M30 progression\ncurrent M30 net directional advance normalized by mean leg size\ncurrent M30 PB count and leg expansion\ncurrent M1 state\nRoot/FVG geometry and stage ages\nselected-FVG -> Fill prospective max favorable/adverse displacement\nstructural objective room in actual Fill-to-SL R\n```\n\n### First +1R snapshot\n\nAt the first exact +1R touch before SL, `EDGE_AUDIT_RUNNER_1R_SNAPSHOT` records the current market state again plus:\n\n```text\nFill -> +1R elapsed time\nmax adverse R before +1R\nnew same/opposite H1/M30/M1 directional events since Fill\nnew same/opposite protected breaks since Fill\n```\n\nExact observational labels remain:\n\n```text\n1R before SL\n2R before SL\n3R before SL\nstructural TP before SL\n```\n\n### Governance\n\nD-145 does not choose or test a trading threshold. In particular it does not add:\n\n```text\nfixed 1.xR TP\nowner-age cutoff\nFVG-retest-time cutoff\nrange-position cutoff\nM30 progression/advance cutoff\nrunner score\n```\n\nA candidate mechanism must preserve the direction of its relationship across LONG/SHORT, calendar blocks, additional symbols, and later untouched evidence. Numerical cutoffs are downstream implementation questions only after a structural mechanism survives.\n\n`2021 = KEEP UNTOUCHED`.\n'
TEST_APPEND='\n\n---\n\n## 2026-08-21 — D-144 GOLD exact-tick result and D-145 transition\n\nThe first D-144 run was restricted to GOLD 2025 because the multi-stage exact-tick barrier population increased tester time by roughly 9x while file size increased only about 15%, indicating per-tick tracker fan-out as the dominant cost.\n\nContinuation actual fills:\n\n```text\n51 fills\nstructural TP = 14 wins / 27.45%\n+1R before SL = 30 / 58.82%\n+1.5R before SL = 25 / 49.02%\n+2R before SL = 20 / 39.22%\n\n+1R direction split:\nLONG 21 / 35 = 60.00%\nSHORT 9 / 16 = 56.25%\n```\n\nAmong 37 continuation trades that eventually lost under the existing structural objective, 16 first reached +1R, 11 reached +1.5R, and 7 reached +2R. This demonstrates that the low structural-TP win rate is not equivalent to a uniformly wrong filled direction.\n\nThe result is one symbol-year and does not establish a fixed TP. D-145 therefore measures the causal difference between `+1R then exhaust before 2R` and `+1R then reach 2R+`, while removing the D-144 multi-stage barrier fan-out.\n'

def decode_process_output(data:bytes)->str:
    # Git for Windows normally writes paths as UTF-8 even when Python's
    # preferred console encoding is CP949. Try explicit encodings instead of
    # text=True so Korean/OneDrive paths do not make repo discovery fail.
    encodings=['utf-8-sig','utf-8',sys.getfilesystemencoding(),locale.getpreferredencoding(False)]
    seen=set()
    for enc in encodings:
        if not enc or enc.lower() in seen:
            continue
        seen.add(enc.lower())
        try:
            return data.decode(enc).strip()
        except UnicodeDecodeError:
            continue
    return data.decode('utf-8',errors='replace').strip()

def find_git_executable():
    found=shutil.which('git')
    if found:
        return found
    if os.name=='nt':
        candidates=[
            Path(os.environ.get('ProgramFiles',r'C:\Program Files'))/'Git/cmd/git.exe',
            Path(os.environ.get('ProgramFiles',r'C:\Program Files'))/'Git/bin/git.exe',
            Path(os.environ.get('LOCALAPPDATA',''))/'Programs/Git/cmd/git.exe',
        ]
        for p in candidates:
            if str(p) and p.exists():
                return str(p)
    raise RuntimeError('git.exe was not found from Python. Verify `git --version` in this PowerShell, or install/add Git for Windows to PATH.')

GIT=find_git_executable()

def run(cwd,*args):
    argv=[GIT if args and args[0]=='git' else args[0], *args[1:]]
    proc=subprocess.run(argv,cwd=str(cwd),stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    if proc.returncode!=0:
        err=decode_process_output(proc.stderr or proc.stdout)
        raise RuntimeError(f"Command failed ({proc.returncode}): {' '.join(map(str,argv))} :: {err}")
    return decode_process_output(proc.stdout)

def locate_repo():
    candidates=[Path.cwd(), Path(__file__).resolve().parent, *Path(__file__).resolve().parents]
    seen=set(); diagnostics=[]
    for c in candidates:
        try:
            c=c.resolve()
        except Exception:
            continue
        if c in seen or not c.exists():
            continue
        seen.add(c)
        try:
            root_text=run(c,'git','rev-parse','--show-toplevel')
            root=Path(root_text).resolve()
            if (root/'mt5/experts/MentorDeterministicV1EA.mq5').exists():
                return root
            diagnostics.append(f'{c}: Git root found but EA missing: {root}')
        except Exception as e:
            diagnostics.append(f'{c}: {e}')
    detail=' | '.join(diagnostics[:4])
    raise RuntimeError('Trading Git repository not found. Discovery details: '+detail)

def read(p): return p.read_text(encoding='utf-8-sig').replace('\r\n','\n').replace('\r','\n')
def write(p,s): p.write_text(s.rstrip()+'\n',encoding='utf-8',newline='\n')

def require_clean(repo,rel):
    rc=subprocess.run([GIT,'diff','--quiet','HEAD','--',rel],cwd=str(repo)).returncode
    if rc!=0: raise RuntimeError(f'Local edits detected in {rel}. Commit/stash/revert them before recovery.')

def patch_ea(text):
    changed=0
    pairs=[
      ('#property description "Mentor deterministic V1 EA - unified front-end causal audit research harness"', '#property description "Mentor deterministic V1 EA - lightweight runner market-context audit harness"'),
      ('// D-143 shadow-only FRONT-END CAUSAL AUDIT / unified-ledger implementation.', '// D-145 shadow-only LIGHTWEIGHT RUNNER MARKET-CONTEXT AUDIT implementation.'),
      ('build=1.92R1L5 property_version=1.00 magic=%I64d phase=FRONT_END_CAUSAL_AUDIT_V1_UNIFIED_LEDGER', 'build=1.92R1L7 property_version=1.00 magic=%I64d phase=RUNNER_MARKET_CONTEXT_AUDIT_V1_LIGHTWEIGHT'),
    ]
    for old,new in pairs:
        if old in text:
            text=text.replace(old,new,1); changed+=1
        elif new not in text:
            # The comment anchor is diagnostic; the two identity anchors are mandatory.
            if old.startswith('#property') or old.startswith('build='):
                raise RuntimeError(f'EA identity anchor missing: {old[:70]}')
    if 'build=1.92R1L7 property_version=1.00 magic=%I64d phase=RUNNER_MARKET_CONTEXT_AUDIT_V1_LIGHTWEIGHT' not in text:
        raise RuntimeError('D-145 EA_START identity was not established.')
    return text

def main():
    try:
        repo=locate_repo()
        head=run(repo,'git','rev-parse','HEAD')
        if head!=EXPECTED_HEAD:
            raise RuntimeError(f'Git HEAD is {head}, expected {EXPECTED_HEAD}. Re-check GitHub before applying; do not force.')
        for rel in TARGETS:
            p=repo/rel
            if not p.exists(): raise RuntimeError(f'Missing tracked file: {rel}')
            require_clean(repo,rel)

        edge=read(repo/'mt5/experts/EdgeAuditV1.mqh')
        if '#define V1_EDGE_AUDIT_BUILD       "1.92R1L7"' not in edge or 'RUNNER_MARKET_CONTEXT_AUDIT_V1_LIGHTWEIGHT' not in edge:
            raise RuntimeError('EdgeAuditV1.mqh is not the expected D-145 lightweight module.')
        runner=read(repo/'docs/ea/RUNNER_CONTEXT_AUDIT.md')
        if 'Build: `1.92R1L7`' not in runner:
            raise RuntimeError('RUNNER_CONTEXT_AUDIT.md is not the expected D-145 contract.')

        ea=patch_ea(read(repo/'mt5/experts/MentorDeterministicV1EA.mq5'))
        write(repo/'mt5/experts/MentorDeterministicV1EA.mq5',ea)

        for name in REPLACEMENTS:
            src=PAYLOAD/'docs/ea'/name
            if not src.exists(): raise RuntimeError(f'Missing package payload: {src}')
            shutil.copyfile(src,repo/'docs/ea'/name)

        dec=read(repo/'docs/ea/DECISIONS.md')
        if '## D-144 — Measure Root reaction and entry timing' not in dec:
            dec=dec.rstrip()+D144_DECISION.rstrip()+'\n'
        if '## D-145 — Study 1R exhaustion versus 2R+ delivery' not in dec:
            dec=dec.rstrip()+D145_DECISION.rstrip()+'\n'
        write(repo/'docs/ea/DECISIONS.md',dec)

        test=read(repo/'docs/ea/TEST_RESULTS.md')
        if '## 2026-08-21 — D-144 GOLD exact-tick result and D-145 transition' not in test:
            test=test.rstrip()+TEST_APPEND.rstrip()+'\n'
        write(repo/'docs/ea/TEST_RESULTS.md',test)

        # Final identity assertions.
        ea2=read(repo/'mt5/experts/MentorDeterministicV1EA.mq5')
        if '1.92R1L5 property_version' in ea2 or 'phase=FRONT_END_CAUSAL_AUDIT_V1_UNIFIED_LEDGER' in ea2:
            raise RuntimeError('Stale D-143 EA identity remains after recovery.')
        hand=read(repo/'docs/ea/HANDOFF.md')
        if 'Current phase: **RUNNER MARKET-CONTEXT AUDIT**' not in hand:
            raise RuntimeError('HANDOFF D-145 phase assertion failed.')

        print('D-145 repository-state recovery applied successfully.')
        print(f'Repository: {repo}')
        print('Strategy semantics were not changed; EdgeAuditV1.mqh was verified but not modified.')
        print('Next: MetaEditor compile -> GOLD Jan audit OFF/ON parity -> runtime comparison.')
        subprocess.run([GIT,'diff','--stat','--',*TARGETS],cwd=str(repo),check=False)
        return 0
    except Exception as e:
        print(f'ERROR: {e}',file=sys.stderr); return 1

if __name__=='__main__': raise SystemExit(main())
