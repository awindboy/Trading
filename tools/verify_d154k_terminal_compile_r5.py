#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
from pathlib import Path

STATE=Path("tools/.d154k_r5_compile_state.json")

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()

if not STATE.exists():
    raise SystemExit("ERROR: R5 state missing. Run prepare_d154k_terminal_sync_r5.py first.")

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
        "ERROR: terminal MQ5 no longer matches repo EA.\n"
        f"repo={repo_sha}\nterminal_source={src_sha}"
    )

if ex5_sha==s["terminal_ex5_sha256_before"]:
    raise SystemExit(
        "ERROR: runner-selected EX5 hash did not change after compile.\n"
        "You likely compiled a different MQ5/terminal instance.\n"
        f"Compile exactly: {src}"
    )

print("D-154K TERMINAL COMPILE R5 VERIFIED")
print("repo/source SHA:",repo_sha)
print("EX5 old SHA:",s["terminal_ex5_sha256_before"])
print("EX5 new SHA:",ex5_sha)
print("")
print("Now run:")
print("  python tools/run_d154k_gold_cadjpy25.py")
print("")
print("The runner is patched to FAIL if D154K ON emits zero research rows.")
