#!/usr/bin/env python3
from pathlib import Path
import argparse, json, hashlib
from v4_001_common import write_prepared_symbol


def sha256(p: Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()


def main():
    ap=argparse.ArgumentParser(description='Prepare causal V4-001 multi-resolution stores from MT5 M1 CSVs')
    ap.add_argument('--data-map',type=Path,required=True)
    ap.add_argument('--config',type=Path,default=Path('config/v4_001_baseline.json'))
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    dm=json.loads(args.data_map.read_text(encoding='utf-8'));cfg=json.loads(args.config.read_text(encoding='utf-8'))
    args.out.mkdir(parents=True,exist_ok=True)
    manifest={'config':str(args.config),'symbols':{},'raw_files':[]}
    for sym,spec in dm.items():
        files=[Path(x) for x in spec['files']]
        for p in files:
            if not p.exists(): raise SystemExit(f'FAIL-CLOSED missing raw file: {p}')
            manifest['raw_files'].append({'symbol':sym,'path':str(p),'size':p.stat().st_size,'sha256':sha256(p)})
        meta=write_prepared_symbol(sym,files,float(spec['point']),args.out,cfg)
        manifest['symbols'][sym]=meta
        print(sym,meta['rows_m1'],'M1 rows',meta['decisions']['rows'],'decisions')
    (args.out/'prepared_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('PREPARE PASS',args.out)

if __name__=='__main__':main()
