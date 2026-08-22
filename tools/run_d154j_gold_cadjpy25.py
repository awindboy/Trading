from __future__ import annotations
import csv, io, re, zipfile, datetime as dt
from pathlib import Path
import mt5_batch_runner as runner
from mt5_batch_runner import TestCase, BatchError

SYMBOLS=("GOLD","CADJPY")
BASE_SETTINGS={
    "InpExitManagementMode":9,
    "InpEpisodeManagementMode":0,
    "InpV2D151CausalAudit":True,
    "InpV2D154EntrySurvivalAudit":False,
    "InpV2D154BConfirmationAudit":False,
    "InpV2D154CReaccelerationFvgAudit":False,
    "InpV2D154FCausalLineageAudit":False,
    "InpV2D154GHTFRootLineageAudit":False,
    "InpV2D154HHTFNestedReplayAudit":True,
}

PARITY_CASES=[
    TestCase("D154J_OFF",{**BASE_SETTINGS,"InpV2D154JHTFDeliveryGeometryAudit":False},"D154H replay ON, D154J OFF parity control"),
    TestCase("D154J_ON", {**BASE_SETTINGS,"InpV2D154JHTFDeliveryGeometryAudit":True}, "D154J shadow ON"),
]
FULL_CASES=[
    TestCase("D154J_GEOMETRY",{**BASE_SETTINGS,"InpV2D154JHTFDeliveryGeometryAudit":True},"GOLD25 vs CADJPY25 contrastive HTF geometry discovery"),
]

def rows_from_zip(zp:Path)->dict[str,list[dict[str,str]]]:
    out={}
    with zipfile.ZipFile(zp) as z:
        for n in z.namelist():
            if not n.endswith('.csv'): continue
            text=z.read(n).decode('utf-8-sig',errors='replace')
            out[n]=list(csv.DictReader(io.StringIO(text)))
    return out

def canonical(rows:list[dict[str,str]]):
    out=[]
    for r in rows:
        if r.get('event','').startswith('D154J_'): continue
        x=dict(r)
        x['detail']=re.sub(r'csv_rows_written=\d+','csv_rows_written=<NORMALIZED>',x.get('detail',''))
        out.append(tuple(x.get(k,'') for k in ('observed_at','event','timeframe','available_at','object_id','detail')))
    return out

def parity_check(zp:Path)->None:
    files=rows_from_zip(zp)
    for sym in SYMBOLS:
        off=[(n,r) for n,r in files.items() if '__D154J_OFF__'+sym+'__' in n]
        on=[(n,r) for n,r in files.items() if '__D154J_ON__'+sym+'__' in n]
        if len(off)!=1 or len(on)!=1:
            raise BatchError(f'{sym}: parity CSV discovery failed OFF={len(off)} ON={len(on)}')
        offn,offr=off[0]; onn,onr=on[0]
        off_j=sum(1 for r in offr if r.get('event','').startswith('D154J_'))
        on_j=sum(1 for r in onr if r.get('event','').startswith('D154J_'))
        if off_j!=0: raise BatchError(f'{sym}: D154J rows present in OFF run ({off_j})')
        a,b=canonical(offr),canonical(onr)
        if a!=b:
            msg=f'{sym}: D154J NON-INTERFERENCE PARITY FAIL canonical OFF={len(a)} ON={len(b)}'
            for i,(x,y) in enumerate(zip(a,b)):
                if x!=y:
                    msg+=f' first_diff_index={i} OFF={x} ON={y}'
                    break
            raise BatchError(msg)
        print(f'{sym}: D154J NON-INTERFERENCE PARITY PASS | canonical_rows={len(a)} | d154j_on_rows={on_j}')

def main():
    # One user command. First dual-symbol parity, then full dual-symbol run only on PASS.
    runner.FIXED_SYMBOLS=SYMBOLS
    runner.FIXED_FROM_DATE='2025.01.01'; runner.FIXED_TO_DATE='2025.03.31'
    parity=runner.run_fixed_2025_batch('D154J_PARITY_GOLD_CADJPY25_Q1',PARITY_CASES,symbols=SYMBOLS,dry_run=False)
    if parity is None: raise BatchError('parity batch returned no ZIP')
    parity=Path(parity)
    parity_check(parity)

    runner.FIXED_SYMBOLS=SYMBOLS
    runner.FIXED_FROM_DATE='2025.01.01'; runner.FIXED_TO_DATE='2025.12.31'
    full=runner.run_fixed_2025_batch('D154J_GEOMETRY_GOLD_CADJPY25',FULL_CASES,symbols=SYMBOLS,dry_run=False)
    if full is None: raise BatchError('full geometry batch returned no ZIP')
    full=Path(full)

    desktop=runner.get_desktop_dir(); stamp=dt.datetime.now().strftime('%Y%m%d_%H%M%S')
    master=desktop/f'Trading_D154J_GOLD_CADJPY25_{stamp}.zip'
    with zipfile.ZipFile(master,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.write(parity,'parity/'+parity.name)
        z.write(full,'geometry/'+full.name)
    print('\nD154J GOLD25 + CADJPY25 COMPLETE')
    print('MASTER ZIP:',master)
    print('Send this ZIP to ChatGPT.')

if __name__=='__main__':
    try: main()
    except BatchError as e: raise SystemExit(f'ERROR: {e}')
