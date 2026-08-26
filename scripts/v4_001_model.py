#!/usr/bin/env python3
from __future__ import annotations
import math
import torch
from torch import nn


class PatchStreamEncoder(nn.Module):
    def __init__(self, feature_dim:int, history:int, patch:int, d_model:int=64, nhead:int=4,
                 layers:int=2, ff:int=128, dropout:float=0.1):
        super().__init__(); self.history=history; self.patch=patch
        self.npatch=math.ceil(history/patch)
        self.proj=nn.Sequential(nn.Linear(feature_dim*patch,d_model),nn.LayerNorm(d_model))
        self.pos=nn.Parameter(torch.zeros(1,self.npatch,d_model));nn.init.normal_(self.pos,std=0.02)
        layer=nn.TransformerEncoderLayer(d_model,nhead,ff,dropout,activation='gelu',batch_first=True,norm_first=True)
        self.enc=nn.TransformerEncoder(layer,layers)

    def forward(self,x,mask):
        # x [B,M,L,F], mask [B,M,L]
        B,M,L,F=x.shape; P=self.patch
        pad=(-L)%P
        if pad:
            x=torch.nn.functional.pad(x,(0,0,pad,0));mask=torch.nn.functional.pad(mask,(pad,0),value=False);L=x.shape[2]
        npatch=L//P
        q=x.reshape(B*M,npatch,P*F); pm=mask.reshape(B*M,npatch,P).all(-1)
        z=self.proj(q)+self.pos[:,:npatch]
        valid=pm.any(1)
        # PyTorch attention can produce NaN when every token in one stream is masked.
        # Give empty streams one zero-valued dummy token for numerical safety, then
        # restore their pooled representation to exact zero and mark them invalid.
        safe_pm=pm.clone()
        empty=~valid
        if empty.any():
            safe_pm[empty,0]=True
            z=z.clone(); z[empty,0]=0.0
        z=self.enc(z,src_key_padding_mask=~safe_pm)
        den=pm.sum(1,keepdim=True).clamp_min(1)
        pooled=(z*pm.unsqueeze(-1)).sum(1)/den
        pooled=torch.where(valid.unsqueeze(-1),pooled,torch.zeros_like(pooled))
        return pooled.reshape(B,M,-1),valid.reshape(B,M)


class CausalPatchPolicy(nn.Module):
    def __init__(self,cfg:dict,feature_dim:int):
        super().__init__();d=cfg['d_model'];self.tf_order=list(cfg['timeframes'].keys());self.horizons=cfg['horizons_minutes']
        self.local=nn.ModuleDict()
        for tf,s in cfg['timeframes'].items():
            self.local[tf]=PatchStreamEncoder(feature_dim,int(s['history']),int(s['patch']),d,cfg['nhead'],cfg['local_layers'],cfg['dim_feedforward'],cfg['dropout'])
        self.tf_emb=nn.Parameter(torch.randn(len(self.tf_order),d)*0.02)
        self.target_emb=nn.Embedding(2,d)
        self.age=nn.Sequential(nn.Linear(1,d),nn.GELU(),nn.Linear(d,d))
        layer=nn.TransformerEncoderLayer(d,cfg['nhead'],cfg['dim_feedforward'],cfg['dropout'],activation='gelu',batch_first=True,norm_first=True)
        self.fusion=nn.TransformerEncoder(layer,cfg['fusion_layers'])
        self.to_latent=nn.Sequential(nn.Linear(d*2,cfg['latent_dim']),nn.GELU(),nn.LayerNorm(cfg['latent_dim']))
        H=len(self.horizons);L=cfg['latent_dim']
        self.mu=nn.Linear(L,H);self.logscale=nn.Linear(L,H);self.dir=nn.Linear(L,H);self.absret=nn.Linear(L,H)

    def forward(self,batch):
        toks=[];valids=[];target_flags=[]
        tm=batch['target_mask']
        for j,tf in enumerate(self.tf_order):
            z,v=self.local[tf](batch['streams'][tf].float(),batch['masks'][tf].bool())
            B,M,D=z.shape
            age=batch['ages'][tf].float().unsqueeze(-1)
            z=z+self.tf_emb[j].view(1,1,-1)+self.target_emb(tm.long())+self.age(age)
            toks.append(z);valids.append(v);target_flags.append(tm&v)
        z=torch.cat(toks,1);valid=torch.cat(valids,1);tf_target=torch.cat(target_flags,1)
        z=self.fusion(z,src_key_padding_mask=~valid)
        global_mean=(z*valid.unsqueeze(-1)).sum(1)/valid.sum(1,keepdim=True).clamp_min(1)
        target_mean=(z*tf_target.unsqueeze(-1)).sum(1)/tf_target.sum(1,keepdim=True).clamp_min(1)
        lat=self.to_latent(torch.cat([target_mean,global_mean],-1))
        return {'latent':lat,'mu':self.mu(lat),'logscale':self.logscale(lat).clamp(-5,4),'direction_logit':self.dir(lat),'absret':self.absret(lat)}


def multitask_loss(out,batch,cfg):
    y=batch['y_norm'].float();scale=torch.exp(out['logscale']).clamp_min(1e-4)
    nll=(0.5*((y-out['mu'])/scale)**2+out['logscale']).mean()
    direction=(y>0).float();bce=torch.nn.functional.binary_cross_entropy_with_logits(out['direction_logit'],direction)
    abs_loss=torch.nn.functional.smooth_l1_loss(out['absret'],y.abs())
    w=cfg['loss_weights'];loss=w['gaussian_nll']*nll+w['direction_bce']*bce+w['abs_smooth_l1']*abs_loss
    return loss,{'nll':float(nll.detach()),'bce':float(bce.detach()),'abs':float(abs_loss.detach())}
