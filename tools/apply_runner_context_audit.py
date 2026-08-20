#!/usr/bin/env python3
"""Apply D-145 lightweight runner market-context audit over known D-143/D-144 local overlays.

GitHub main is intentionally still the D-142 commit. This installer reconstructs
known D-143 and D-144 text states from HEAD and refuses unrelated local edits.
It also accepts the observed mixed state where the D-144 EdgeAudit module was
used while the EA identity string remained D-143; D-145 normalizes that identity.
"""
from __future__ import annotations
from pathlib import Path
import hashlib, importlib.util, shutil, subprocess, sys

REPO=Path(__file__).resolve().parents[1]
PAYLOAD=REPO/'payload'
EA=REPO/'mt5/experts/MentorDeterministicV1EA.mq5'
EDGE=REPO/'mt5/experts/EdgeAuditV1.mqh'
DEC=REPO/'docs/ea/DECISIONS.md'
TEST=REPO/'docs/ea/TEST_RESULTS.md'
EXPECTED_HEAD='418471c7a0c9bc9e45bb075f43e1d726daef4ebf'
D143_HELPER=REPO/'tools/_d143_overlay_contract.py'
D144_HELPER=REPO/'tools/_d144_overlay_contract.py'

D143_HASHES={
 'mt5/experts/EdgeAuditV1.mqh':'1301601465bec76784c60ab4f259b7729e18d0355ba6754a35781199c1b908cc',
 'docs/ea/HANDOFF.md':'e605820c3a901588f2573bf3d3d4190b175d06ce9ae78a981ea43b2658087391',
 'docs/ea/BACKLOG.md':'b9c8d67e43d657d8313ae76f61768ea25585ea8301f4231c288e43ad8aa794f0',
 'docs/ea/BASE_EDGE_AUDIT_2025.md':'880e1ce5d99d02fbbb541ed6ef978f941209f987fd59aacef6b2d508f9b3d0af',
 'docs/ea/EDGE_AUDIT_V1.md':'563b7b895b0c42135d9163b411197a4a884bb4fa27865ecfedfec5e3c95f716e',
 'docs/ea/STRATEGY_RESEARCH_STATE.md':'bfb223b304853f757ad56fcf740668d01e545a44ea95edc9c3226eaed8aa4ed9',
}
D144_HASHES={
 'mt5/experts/EdgeAuditV1.mqh':'7c5f875b479f07a1391d5046c8c989bc5f9cce2b9fff8f5294287763a87eae52',
 'docs/ea/HANDOFF.md':'cf8152b007f1b94d634cb18e1aaad33bc9e1826b0511ca20a70bc109067b5f20',
 'docs/ea/BACKLOG.md':'4c583f1ce97fa5d5733db837627428440997b9a3f935afe71eddb3e3e2384fb5',
 'docs/ea/BASE_EDGE_AUDIT_2025.md':'06ed59a62ac66f604a775ebe9b1b461e3be0e67e892acf2e4f298f1fef771cb2',
 'docs/ea/EDGE_AUDIT_V1.md':'6eb595e428cb31e85b4d5ebfd768b194e2c9d2734709847f6fd8335e7cb14aa0',
 'docs/ea/STRATEGY_RESEARCH_STATE.md':'b258ae285835b1f73d394394a5e71394de1f146b769e670d3cb4781ce7a4bce2',
 'docs/ea/REACTION_ENTRY_BARRIER_AUDIT.md':'39b57f99a4d4591c2a6f969f8b15fa310f629df47917e50d187c52158617140d',
}
REPLACEMENT_DOCS=['HANDOFF.md','BACKLOG.md','BASE_EDGE_AUDIT_2025.md','EDGE_AUDIT_V1.md','STRATEGY_RESEARCH_STATE.md']

D145_DECISION=r'''

---

## D-145 — Study 1R exhaustion versus 2R+ delivery from causal market context, not R optimization

Status: PREPARED LIGHTWEIGHT SHADOW RESEARCH / STRATEGY AUTHORITY UNCHANGED — 2026-08-21

### Trigger

The first D-144 exact-tick run on GOLD 2025 showed that the same continuation fills behave very differently under standardized reward geometry:

```text
51 continuation fills
current structural-TP winners = 14 / 51 = 27.45%
+1R before -1R              = 30 / 51 = 58.82%
+1.5R before -1R            = 25 / 51 = 49.02%
+2R before -1R              = 20 / 51 = 39.22%
```

This is not permission to choose the R point whose pooled hit rate looks best. The project objective is `>=50%` win rate with meaningful reward greater than 1R, so the research problem is now conditional continuation:

> among entries that already prove themselves by reaching +1R, what causally-known market background distinguishes 2R+ delivery from exhaustion before 2R?

### D-145 measurement identity

```text
build = 1.92R1L7
phase = RUNNER_MARKET_CONTEXT_AUDIT_V1_LIGHTWEIGHT
strategy semantics = D134_EXECUTION_CORE_UNCHANGED
strategy authority = NONE
```

The expensive D-144 Root/Sweep/CHoCH/FVG mirror-barrier fan-out is removed. D-143 front-end forward labels are also disabled because that census is complete.

Tick-active research objects are limited to:

```text
selected execution FVG waiting for actual Fill
actual filled runner
```

### Fill snapshot

`EDGE_AUDIT_RUNNER_FILL_SNAPSHOT` freezes only information causally known at Fill, including:

```text
current H1/M30 map/owner/BOS/PB state
current H1/M30 protected->external range position and remaining room in actual R
current latest-12 M30 progression
current M30 net directional advance normalized by mean leg size
current M30 PB count and leg expansion
current M1 state
Root/FVG geometry and stage ages
selected-FVG -> Fill prospective max favorable/adverse displacement
structural objective room in actual Fill-to-SL R
```

### First +1R snapshot

At the first exact +1R touch before SL, `EDGE_AUDIT_RUNNER_1R_SNAPSHOT` records the current market state again plus:

```text
Fill -> +1R elapsed time
max adverse R before +1R
new same/opposite H1/M30/M1 directional events since Fill
new same/opposite protected breaks since Fill
```

Exact observational labels remain:

```text
1R before SL
2R before SL
3R before SL
structural TP before SL
```

### Governance

D-145 does not choose or test a trading threshold. In particular it does not add:

```text
fixed 1.xR TP
owner-age cutoff
FVG-retest-time cutoff
range-position cutoff
M30 progression/advance cutoff
runner score
```

A candidate mechanism must preserve the direction of its relationship across LONG/SHORT, calendar blocks, additional symbols, and later untouched evidence. Numerical cutoffs are downstream implementation questions only after a structural mechanism survives.

`2021 = KEEP UNTOUCHED`.
'''

TEST_APPEND=r'''

---

## 2026-08-21 — D-144 GOLD exact-tick result and D-145 transition

The first D-144 run was restricted to GOLD 2025 because the multi-stage exact-tick barrier population increased tester time by roughly 9x while file size increased only about 15%, indicating per-tick tracker fan-out as the dominant cost.

Continuation actual fills:

```text
51 fills
structural TP = 14 wins / 27.45%
+1R before SL = 30 / 58.82%
+1.5R before SL = 25 / 49.02%
+2R before SL = 20 / 39.22%

+1R direction split:
LONG 21 / 35 = 60.00%
SHORT 9 / 16 = 56.25%
```

Among 37 continuation trades that eventually lost under the existing structural objective, 16 first reached +1R, 11 reached +1.5R, and 7 reached +2R. This demonstrates that the low structural-TP win rate is not equivalent to a uniformly wrong filled direction.

The result is one symbol-year and does not establish a fixed TP. D-145 therefore measures the causal difference between `+1R then exhaust before 2R` and `+1R then reach 2R+`, while removing the D-144 multi-stage barrier fan-out.
'''

def norm(s:str)->str:
    return s.replace('\r\n','\n').replace('\r','\n')

def read(path:Path)->str:
    return norm(path.read_text(encoding='utf-8-sig'))

def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args:str)->str:
    return subprocess.check_output(['git',*args],cwd=REPO,text=True,stderr=subprocess.STDOUT).strip()

def head_text(path:Path)->str:
    rel=path.relative_to(REPO).as_posix()
    return norm(subprocess.check_output(['git','show',f'HEAD:{rel}'],cwd=REPO,text=True,stderr=subprocess.STDOUT))

def load(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(mod)
    return mod

def expected_states():
    d143=load(D143_HELPER,'d143_contract')
    d144=load(D144_HELPER,'d144_contract')
    # D-143 expected text from checked HEAD.
    ea143=d143.patch_ea(head_text(EA)).rstrip()+'\n'
    dec143=head_text(DEC)
    dec143=d143.replace_once(dec143,
        'Status: D-142A PREPARED / LOCAL COMPILE + AUDIT-OFF/AUDIT-ON PARITY PENDING — 2026-08-20',
        'Status: D-142A VALIDATED / D-143 FRONT-END AUDIT SUPERSEDES NEXT RESEARCH STEP — 2026-08-20','D-142 status')
    if '## D-143 — Front-end causal audit' not in dec143:
        dec143=dec143.rstrip()+d143.D143_DECISION.rstrip()+'\n'
    test143=head_text(TEST)
    if '## 2026-08-20 — D-142A parity PASS and first six-symbol front-end audit' not in test143:
        test143=test143.rstrip()+d143.TEST_APPEND.rstrip()+'\n'

    ea144=d144.patch_ea_d144(ea143).rstrip()+'\n'
    dec144=dec143
    dec144=d144.replace_once(dec144,
        'Status: PREPARED SHADOW RESEARCH / STRATEGY AUTHORITY UNCHANGED — 2026-08-20\n\n### Trigger\n\nD-142A passed its audit OFF/ON parity gate, then the first six-symbol 2025 contrast panel exposed a more upstream problem than the originally planned fill-barrier experiment.',
        'Status: ANALYZED SHADOW RESEARCH / D-144 EXACT-TICK BARRIER AUDIT IS NEXT — 2026-08-20\n\n### Trigger\n\nD-142A passed its audit OFF/ON parity gate, then the first six-symbol 2025 contrast panel exposed a more upstream problem than the originally planned fill-barrier experiment.',
        'D-143 status')
    if '## D-144 — Measure Root reaction and entry timing' not in dec144:
        dec144=dec144.rstrip()+d144.D144_DECISION.rstrip()+'\n'
    test144=test143
    if '## 2026-08-20 — D-143 six-symbol front-end causal result and D-144 measurement transition' not in test144:
        test144=test144.rstrip()+d144.TEST_APPEND.rstrip()+'\n'
    return (ea143,dec143,test143),(ea144,dec144,test144)

def known_hash(rel:str,actual:str)->bool:
    return actual in {D143_HASHES.get(rel,''),D144_HASHES.get(rel,'')}

def require_known_local():
    if git('rev-parse','HEAD')!=EXPECTED_HEAD:
        raise RuntimeError('Git HEAD moved. Re-check GitHub before applying D-145; do not force-apply.')
    s143,s144=expected_states()
    current=(read(EA),read(DEC),read(TEST))
    for label,cur,a,b in zip(('EA','DECISIONS','TEST_RESULTS'),current,s143,s144):
        if cur!=a and cur!=b:
            raise RuntimeError(f'{label} is neither the exact D-143 nor exact D-144 known overlay.')
    for rel in ['mt5/experts/EdgeAuditV1.mqh']+[f'docs/ea/{x}' for x in REPLACEMENT_DOCS]:
        p=REPO/rel
        if not p.exists() or not known_hash(rel,sha(p)):
            raise RuntimeError(f'Unknown local audit file state: {rel}')
    hist=REPO/'docs/ea/REACTION_ENTRY_BARRIER_AUDIT.md'
    if hist.exists() and sha(hist)!=D144_HASHES['docs/ea/REACTION_ENTRY_BARRIER_AUDIT.md']:
        raise RuntimeError('Unknown REACTION_ENTRY_BARRIER_AUDIT.md state.')
    return s144

def patch_ea_d145(text:str)->str:
    # Accept either known D-143 or D-144 identity text; normalize to D-145.
    if '#property description "Mentor deterministic V1 EA - exact-tick reaction/entry barrier audit harness"' in text:
        text=text.replace('#property description "Mentor deterministic V1 EA - exact-tick reaction/entry barrier audit harness"',
                          '#property description "Mentor deterministic V1 EA - lightweight runner market-context audit harness"',1)
    elif '#property description "Mentor deterministic V1 EA - unified front-end causal audit research harness"' in text:
        text=text.replace('#property description "Mentor deterministic V1 EA - unified front-end causal audit research harness"',
                          '#property description "Mentor deterministic V1 EA - lightweight runner market-context audit harness"',1)
    else: raise RuntimeError('EA property identity anchor missing.')

    if '// D-144 shadow-only REACTION / ENTRY EXACT-TICK BARRIER AUDIT implementation.' in text:
        text=text.replace('// D-144 shadow-only REACTION / ENTRY EXACT-TICK BARRIER AUDIT implementation.',
                          '// D-145 shadow-only LIGHTWEIGHT RUNNER MARKET-CONTEXT AUDIT implementation.',1)
    elif '// D-143 shadow-only FRONT-END CAUSAL AUDIT / unified-ledger implementation.' in text:
        text=text.replace('// D-143 shadow-only FRONT-END CAUSAL AUDIT / unified-ledger implementation.',
                          '// D-145 shadow-only LIGHTWEIGHT RUNNER MARKET-CONTEXT AUDIT implementation.',1)
    else: raise RuntimeError('EA include phase anchor missing.')

    if 'build=1.92R1L6 property_version=1.00 magic=%I64d phase=REACTION_ENTRY_BARRIER_AUDIT_V1_EXACT_TICK' in text:
        text=text.replace('build=1.92R1L6 property_version=1.00 magic=%I64d phase=REACTION_ENTRY_BARRIER_AUDIT_V1_EXACT_TICK',
                          'build=1.92R1L7 property_version=1.00 magic=%I64d phase=RUNNER_MARKET_CONTEXT_AUDIT_V1_LIGHTWEIGHT',1)
    elif 'build=1.92R1L5 property_version=1.00 magic=%I64d phase=FRONT_END_CAUSAL_AUDIT_V1_UNIFIED_LEDGER' in text:
        text=text.replace('build=1.92R1L5 property_version=1.00 magic=%I64d phase=FRONT_END_CAUSAL_AUDIT_V1_UNIFIED_LEDGER',
                          'build=1.92R1L7 property_version=1.00 magic=%I64d phase=RUNNER_MARKET_CONTEXT_AUDIT_V1_LIGHTWEIGHT',1)
    else: raise RuntimeError('EA build identity anchor missing.')
    return text

def main()->int:
    try:
        (_,dec144,test144)=require_known_local()
        required=['mt5/experts/EdgeAuditV1.mqh']+[f'docs/ea/{x}' for x in REPLACEMENT_DOCS]+[
            'docs/ea/REACTION_ENTRY_BARRIER_AUDIT.md','docs/ea/RUNNER_CONTEXT_AUDIT.md']
        for rel in required:
            if not (PAYLOAD/rel).exists(): raise RuntimeError(f'Missing payload: {rel}')

        ea=patch_ea_d145(read(EA))
        dec=dec144
        if '## D-145 — Study 1R exhaustion versus 2R+ delivery' not in dec:
            dec=dec.rstrip()+D145_DECISION.rstrip()+'\n'
        test=test144
        if '## 2026-08-21 — D-144 GOLD exact-tick result and D-145 transition' not in test:
            test=test.rstrip()+TEST_APPEND.rstrip()+'\n'

        EA.write_text(ea.rstrip()+'\n',encoding='utf-8',newline='\n')
        shutil.copyfile(PAYLOAD/'mt5/experts/EdgeAuditV1.mqh',EDGE)
        DEC.write_text(dec,encoding='utf-8',newline='\n')
        TEST.write_text(test,encoding='utf-8',newline='\n')
        for name in REPLACEMENT_DOCS:
            shutil.copyfile(PAYLOAD/'docs/ea'/name,REPO/'docs/ea'/name)
        shutil.copyfile(PAYLOAD/'docs/ea/REACTION_ENTRY_BARRIER_AUDIT.md',REPO/'docs/ea/REACTION_ENTRY_BARRIER_AUDIT.md')
        shutil.copyfile(PAYLOAD/'docs/ea/RUNNER_CONTEXT_AUDIT.md',REPO/'docs/ea/RUNNER_CONTEXT_AUDIT.md')
        shutil.rmtree(PAYLOAD)
        print('D-145 RUNNER MARKET-CONTEXT AUDIT applied successfully.')
        print('Next: MetaEditor compile, then GOLD audit OFF/ON parity + runtime comparison.')
        return 0
    except Exception as e:
        print(f'ERROR: {e}',file=sys.stderr); return 1

if __name__=='__main__': raise SystemExit(main())
