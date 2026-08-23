#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
from pathlib import Path

STATE=Path("tools/.d154m_compile_state.json")

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()

if not STATE.exists():
    raise SystemExit("ERROR: D154M compile state missing. Run apply_d154m_and_handoff.py first.")

s=json.loads(STATE.read_text(encoding="utf-8"))
repo=Path(s["repo_ea"])
src=Path(s["terminal_source"])
ex5=Path(s["terminal_ex5"])
for p in (repo,src,ex5):
    if not p.exists():
        raise SystemExit(f"ERROR: missing {p}")

repo_sha=sha256(repo)
src_sha=sha256(src)
ex5_sha=sha256(ex5)

if repo_sha!=src_sha:
    raise SystemExit(
        "ERROR: runner terminal MQ5 differs from repo D154M source.\n"
        f"repo={repo_sha}\nterminal={src_sha}"
    )

if ex5_sha==s["terminal_ex5_sha256_before"]:
    raise SystemExit(
        "ERROR: exact runner-selected EX5 did not change after compile.\n"
        f"Compile exactly: {src}"
    )

print("D154M TERMINAL COMPILE VERIFIED")
print("repo/source SHA:",repo_sha)
print("EX5 old SHA:",s["terminal_ex5_sha256_before"])
print("EX5 new SHA:",ex5_sha)
print("")
print("Run:")
print("  python tools/run_d154m_friction_counterfactual.py")
