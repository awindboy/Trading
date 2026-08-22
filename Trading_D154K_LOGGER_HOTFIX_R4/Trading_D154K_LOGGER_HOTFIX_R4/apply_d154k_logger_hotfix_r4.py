#!/usr/bin/env python3
from __future__ import annotations
import subprocess
from pathlib import Path

BASE_HEAD="8d37866e42c59669fd4ee8fa7bfacbeb50c1e546"
EA=Path("mt5/experts/MentorDeterministicV2EA.mq5")
RUNNER=Path("tools/run_d154k_gold_cadjpy25.py")

EXPECTED_DIRTY={
    "mt5/experts/MentorDeterministicV2EA.mq5",
    "docs/ea/HANDOFF.md",
    "docs/ea/v2/HANDOFF_V2.md",
    "docs/ea/v2/RESEARCH_STATE_V2.md",
    "docs/ea/v2/BACKLOG_V2.md",
    "docs/ea/DECISIONS.md",
    "docs/ea/v2/D154J_HTF_DELIVERY_GEOMETRY_RESULTS.md",
    "docs/ea/v2/D154K_CROSS_SCALE_REACTION_NOISE.md",
    "tools/run_d154k_gold_cadjpy25.py",
    "tools/summarize_d154k_cross_scale.py",
}

def git(*args:str)->str:
    p=subprocess.run(["git",*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode:
        raise SystemExit("ERROR: git "+" ".join(args)+"\n"+
                         p.stderr.decode("utf-8",errors="replace"))
    return p.stdout.decode("utf-8",errors="strict").strip()

def write_preserve(path:Path,text:str)->None:
    raw=path.read_bytes()
    bom=raw.startswith(b"\xef\xbb\xbf")
    nl="\r\n" if b"\r\n" in raw else "\n"
    out=text.replace("\r\n","\n").replace("\r","\n").replace("\n",nl).encode("utf-8")
    if bom:
        out=b"\xef\xbb\xbf"+out
    path.write_bytes(out)

head=git("rev-parse","HEAD")
if head!=BASE_HEAD:
    raise SystemExit(f"ERROR: expected Git HEAD {BASE_HEAD}, got {head}")

if not EA.exists() or not RUNNER.exists():
    raise SystemExit("ERROR: D-154K R3 local files are missing; apply R3 first.")

status=git("status","--porcelain")
dirty_paths=set()
for line in status.splitlines():
    if not line.strip():
        continue
    path=line[3:] if len(line)>=4 else ""
    path=path.replace("\\","/")
    if " -> " in path:
        path=path.split(" -> ",1)[1]
    dirty_paths.add(path)

unexpected={
    p for p in dirty_paths
    if p not in EXPECTED_DIRTY
    and not p.startswith("Trading_D154K_CROSS_SCALE_REACTION_NOISE")
    and not p.startswith("Trading_D154K_LOGGER_HOTFIX_R4")
}
if unexpected:
    raise SystemExit(
        "ERROR: unrelated local state present; fail-closed:\n  "+
        "\n  ".join(sorted(unexpected))
    )

ea=EA.read_text(encoding="utf-8-sig")
required_markers=[
    '#property version   "2.10"',
    'input bool   InpV2D154KCrossScaleReactionAudit = false;',
    'bool D154KEnabled()',
    'LogLine("D154K_CROSS_SCALE_SNAPSHOT"',
    'D154KOnFill(scenario_index,observed_at);',
    'D154KOnTesterStart(TimeCurrent());',
    'D154KOnTesterEnd(TimeCurrent());',
]
missing=[m for m in required_markers if m not in ea]
if missing:
    raise SystemExit(
        "ERROR: local EA is not the expected applied D-154K state; missing:\n  "+
        "\n  ".join(missing)
    )

old = (
    '   if(StringFind(event_name,"D154J_")==0)\n'
    '      return true;\n'
    '   // Regime Research V1 can be independently recomputed from these M30 facts.'
)
new = (
    '   if(StringFind(event_name,"D154J_")==0)\n'
    '      return true;\n'
    '   if(StringFind(event_name,"D154K_")==0)\n'
    '      return true;\n'
    '   // Regime Research V1 can be independently recomputed from these M30 facts.'
)

if 'if(StringFind(event_name,"D154K_")==0)' in ea:
    raise SystemExit("ERROR: D154K compact-log whitelist already present; nothing to apply.")
if ea.count(old)!=1:
    raise SystemExit(f"ERROR: compact-log whitelist marker expected once, found {ea.count(old)}")
ea=ea.replace(old,new,1)

runner=RUNNER.read_text(encoding="utf-8-sig")
old_runner = (
    '        d["detail"]=re.sub(r"csv_rows_written=\\\\d+","csv_rows_written=<NORMALIZED>",d.get("detail",""))\n'
    '        out.append(tuple(d.get(k,"") for k in ("observed_at","event","timeframe","available_at","object_id","detail")))'
)
new_runner = (
    '        detail=d.get("detail","")\n'
    '        detail=re.sub(r"csv_rows_written=\\\\d+","csv_rows_written=<NORMALIZED>",detail)\n'
    '        detail=re.sub(r"log_calls_suppressed=\\\\d+","log_calls_suppressed=<NORMALIZED>",detail)\n'
    '        d["detail"]=detail\n'
    '        out.append(tuple(d.get(k,"") for k in ("observed_at","event","timeframe","available_at","object_id","detail")))'
)

if "log_calls_suppressed=<NORMALIZED>" in runner:
    raise SystemExit("ERROR: runner counter normalization already patched; nothing to apply.")
if runner.count(old_runner)!=1:
    raise SystemExit(f"ERROR: runner canonical marker expected once, found {runner.count(old_runner)}")
runner=runner.replace(old_runner,new_runner,1)

write_preserve(EA,ea)
write_preserve(RUNNER,runner)

print("D-154K LOGGER HOTFIX R4 applied.")
print("Changes:")
print(" - RESEARCH_COMPACT now emits D154K_* events.")
print(" - parity comparator normalizes expected csv_rows_written and log_calls_suppressed counters.")
print("Recompile MentorDeterministicV2EA.mq5 with 0 errors.")
print("Then rerun: python tools/run_d154k_gold_cadjpy25.py")
