#!/usr/bin/env python3
import json,torch
from pathlib import Path
from v4_001_model import CausalPatchPolicy,multitask_loss
from v4_001_common import FEATURE_NAMES

def main():
    cfg=json.loads(Path('config/v4_001_baseline.json').read_text());B=2;M=4;batch={'streams':{},'masks':{},'ages':{},'target_mask':torch.zeros(B,M,dtype=torch.bool),'y_norm':torch.randn(B,3)};batch['target_mask'][:,0]=True
    for tf,s in cfg['timeframes'].items():
        L=s['history'];batch['streams'][tf]=torch.randn(B,M,L,len(FEATURE_NAMES));batch['masks'][tf]=torch.ones(B,M,L,dtype=torch.bool);batch['ages'][tf]=torch.zeros(B,M)
    m=CausalPatchPolicy(cfg,len(FEATURE_NAMES));o=m(batch);loss,_=multitask_loss(o,batch,cfg);loss.backward()
    assert o['mu'].shape==(B,3) and torch.isfinite(loss);print('SMOKE PASS params=',sum(p.numel() for p in m.parameters()),'loss=',float(loss.detach()))
if __name__=='__main__':main()
