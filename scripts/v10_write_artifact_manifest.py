#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,csv,hashlib
from pathlib import Path

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def count_rows(p):
    if p.suffix.lower()!='.csv':return ''
    with p.open('r',encoding='utf-8-sig',newline='') as f:
        n=sum(1 for _ in csv.reader(f))
    return max(0,n-1)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('repo');args=ap.parse_args();repo=Path(args.repo).resolve();root=repo/'docs/ea/v10/results'
    rows=[]
    for p in sorted(root.rglob('*')):
        if not p.is_file():continue
        if p.name=='V10_REPRODUCIBILITY_ARTIFACT_SHA256_20260916.csv':continue
        rel=p.relative_to(repo).as_posix()
        rows.append({'path':rel,'bytes':p.stat().st_size,'rows':count_rows(p),'sha256':sha(p)})
    out=root/'V10_REPRODUCIBILITY_ARTIFACT_SHA256_20260916.csv'
    with out.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['path','bytes','rows','sha256']);w.writeheader();w.writerows(rows)
    print(out)
if __name__=='__main__':main()
