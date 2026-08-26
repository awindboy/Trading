#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,zipfile

def sha256(p:Path):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--stage-a',type=Path,required=True);ap.add_argument('--out',type=Path,default=Path('V4_001A_STAGE_A_RESULT_BUNDLE.zip'));args=ap.parse_args()
 root=args.stage_a.resolve()
 for n in ['run_manifest.json','stage_a_summary.json','stage_a_verdict.json']:
  if not (root/n).exists():raise SystemExit(f'FAIL-CLOSED missing {root/n}')
 hashes={}
 for p in root.rglob('*.pt'):hashes[str(p.relative_to(root))]={'size':p.stat().st_size,'sha256':sha256(p)}
 hashfile=root/'checkpoint_hashes.json';hashfile.write_text(json.dumps(hashes,indent=2),encoding='utf-8')
 include=[]
 for p in root.rglob('*.json'):
  include.append(p)
 with zipfile.ZipFile(args.out,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(set(include)):z.write(p,p.relative_to(root))
 print('RESULT BUNDLE',args.out.resolve());print('SHA256',sha256(args.out));print('checkpoint binaries and prediction NPZ files intentionally excluded; hashes retained')
if __name__=='__main__':main()
