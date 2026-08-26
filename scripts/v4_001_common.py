#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable
import json
import math
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

FEATURE_NAMES = [
    "ret_z","body_z","range_z","upper_wick_z","lower_wick_z","close_location",
    "tickvol_z","spread_return","spread_over_vol","log_gap","tod_sin","tod_cos","dow_sin","dow_cos",
]


def read_mt5_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t")
    need = ["<DATE>","<TIME>","<OPEN>","<HIGH>","<LOW>","<CLOSE>","<TICKVOL>","<SPREAD>"]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise ValueError(f"{path}: missing columns {miss}")
    ts = pd.to_datetime(df["<DATE>"].astype(str)+" "+df["<TIME>"].astype(str), format="%Y.%m.%d %H:%M:%S")
    out = pd.DataFrame(index=pd.DatetimeIndex(ts))
    out["open"] = pd.to_numeric(df["<OPEN>"], errors="raise").to_numpy(float)
    out["high"] = pd.to_numeric(df["<HIGH>"], errors="raise").to_numpy(float)
    out["low"] = pd.to_numeric(df["<LOW>"], errors="raise").to_numpy(float)
    out["close"] = pd.to_numeric(df["<CLOSE>"], errors="raise").to_numpy(float)
    out["tickvol"] = pd.to_numeric(df["<TICKVOL>"], errors="raise").to_numpy(float)
    out["spread_points"] = pd.to_numeric(df["<SPREAD>"], errors="raise").to_numpy(float)
    if not out.index.is_monotonic_increasing:
        raise ValueError(f"{path}: timestamps are not monotonic")
    if out.index.has_duplicates:
        raise ValueError(f"{path}: duplicate timestamps")
    bad = (out.high < out[["open","close"]].max(axis=1)) | (out.low > out[["open","close"]].min(axis=1)) | (out.high < out.low)
    if bad.any():
        raise ValueError(f"{path}: invalid OHLC rows={int(bad.sum())}")
    return out


def load_symbol(files: Iterable[Path]) -> pd.DataFrame:
    parts=[read_mt5_csv(Path(p)) for p in files]
    q=pd.concat(parts).sort_index()
    if q.index.has_duplicates:
        dup=q.index[q.index.duplicated()].unique()[:5]
        raise ValueError(f"combined symbol has duplicate timestamps e.g. {list(dup)}")
    return q


def resample_bars(m1: pd.DataFrame, rule: str) -> pd.DataFrame:
    if rule in ("1min","1m","1T"):
        return m1.copy()
    agg={"open":"first","high":"max","low":"min","close":"last","tickvol":"sum","spread_points":"last"}
    q=m1.resample(rule, label="left", closed="left").agg(agg).dropna(subset=["open","high","low","close"])
    return q


def ewm_z(s: pd.Series, span: int=256) -> pd.Series:
    mean=s.ewm(span=span, adjust=False, min_periods=max(16,span//8)).mean()
    var=((s-mean)**2).ewm(span=span, adjust=False, min_periods=max(16,span//8)).mean()
    return (s-mean)/np.sqrt(var.clip(lower=1e-12))


def make_features(b: pd.DataFrame, point: float, timeframe_minutes: int) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    prev_close=b.close.shift(1)
    logret=np.log(b.close/prev_close)
    vol=logret.ewm(span=256, adjust=False, min_periods=32).std(bias=False).clip(lower=1e-8)
    body=(b.close-b.open)/prev_close
    rng=(b.high-b.low)/prev_close
    upper=(b.high-b[["open","close"]].max(axis=1))/prev_close
    lower=(b[["open","close"]].min(axis=1)-b.low)/prev_close
    loc=((b.close-b.low)/(b.high-b.low).replace(0,np.nan)).clip(0,1).fillna(0.5)-0.5
    spread_ret=(b.spread_points*point/b.close).clip(lower=0)
    tvz=ewm_z(np.log1p(b.tickvol))
    gaps=b.index.to_series().diff().dt.total_seconds().div(60.0).fillna(timeframe_minutes)
    tod=(b.index.hour*60+b.index.minute).to_numpy()/1440.0
    dow=b.index.dayofweek.to_numpy()/7.0
    x=np.column_stack([
        (logret/vol).clip(-20,20), (body/vol).clip(-20,20), (rng/vol).clip(0,30),
        (upper/vol).clip(0,30), (lower/vol).clip(0,30), loc,
        tvz.clip(-10,10), spread_ret.clip(0,0.1), (spread_ret/vol).clip(0,30),
        np.log1p(gaps.to_numpy()/max(1,timeframe_minutes)).clip(0,10),
        np.sin(2*np.pi*tod), np.cos(2*np.pi*tod), np.sin(2*np.pi*dow), np.cos(2*np.pi*dow),
    ]).astype(np.float32)
    valid=np.isfinite(x).all(axis=1)
    x[~valid]=0.0
    # A bar becomes observable only after the whole bar has completed.
    available=(b.index + pd.Timedelta(minutes=timeframe_minutes)).view("i8")
    return x, available.astype(np.int64), valid.astype(np.uint8)


def write_prepared_symbol(symbol: str, files: list[Path], point: float, out: Path, config: dict) -> dict:
    raw=load_symbol(files)
    symdir=out/safe_symbol(symbol); symdir.mkdir(parents=True,exist_ok=True)
    meta={"symbol":symbol,"point":point,"rows_m1":int(len(raw)),"first":str(raw.index[0]),"last":str(raw.index[-1]),"streams":{}}
    tf_minutes={"M1":1,"M5":5,"M30":30,"H4":240}
    for tf,spec in config["timeframes"].items():
        bars=resample_bars(raw,spec["rule"])
        x,av,valid=make_features(bars,point,tf_minutes[tf])
        np.save(symdir/f"{tf}_x.npy",x)
        np.save(symdir/f"{tf}_available_ns.npy",av)
        np.save(symdir/f"{tf}_valid.npy",valid)
        meta["streams"][tf]={"rows":int(len(x)),"valid":int(valid.sum()),"feature_dim":int(x.shape[1])}

    # Decision at the target M1 open. Observations use bars available <= t, which excludes this starting M1 bar.
    idx=raw.index
    decision_mask=(idx.minute%config["decision_minutes"]==0)&(idx.second==0)
    dt=idx[decision_mask]
    base_open=pd.Series(raw.open.to_numpy(float),index=idx)
    base_spread=pd.Series((raw.spread_points*point/raw.open).to_numpy(float),index=idx)
    # trailing 1m volatility available before decision t
    lr=np.log(base_open/base_open.shift(1))
    sig=lr.ewm(span=256,adjust=False,min_periods=64).std(bias=False).shift(1)
    rows=[]
    retcols=[]; normcols=[]; abscols=[]; dircols=[]
    entry=base_open.reindex(dt).to_numpy(float)
    sigma1=sig.reindex(dt).to_numpy(float)
    spread=base_spread.reindex(dt).to_numpy(float)
    valid_label=np.isfinite(entry)&np.isfinite(sigma1)&(sigma1>1e-8)&np.isfinite(spread)
    rets=[]; norms=[]
    for h in config["horizons_minutes"]:
        fut=base_open.reindex(dt+pd.Timedelta(minutes=h)).to_numpy(float)
        r=np.log(fut/entry)
        scale=sigma1*np.sqrt(h)
        rn=r/scale
        valid_label &= np.isfinite(r)&np.isfinite(rn)
        rets.append(r); norms.append(rn)
    if len(dt):
        ret_arr=np.column_stack(rets).astype(np.float32)
        norm_arr=np.column_stack(norms).astype(np.float32)
    else:
        ret_arr=np.empty((0,len(config["horizons_minutes"])),np.float32); norm_arr=ret_arr.copy()
    keep=np.where(valid_label)[0]
    np.save(symdir/"decision_ns.npy",dt.view("i8")[keep].astype(np.int64))
    np.save(symdir/"future_logret.npy",ret_arr[keep])
    np.save(symdir/"future_normret.npy",norm_arr[keep])
    np.save(symdir/"decision_sigma1m.npy",sigma1[keep].astype(np.float32))
    np.save(symdir/"decision_spread_return.npy",spread[keep].astype(np.float32))
    meta["decisions"]={"rows":int(len(keep)),"first":str(dt[keep[0]]) if len(keep) else None,"last":str(dt[keep[-1]]) if len(keep) else None}
    (symdir/"meta.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    return meta


def safe_symbol(s: str) -> str:
    return s.replace("#","_HASH").replace("/","_")


@dataclass
class PreparedMarket:
    symbol: str
    root: Path
    streams: Dict[str, tuple[np.ndarray,np.ndarray,np.ndarray]]
    decision_ns: np.ndarray
    future_logret: np.ndarray
    future_normret: np.ndarray
    sigma1m: np.ndarray
    spread_return: np.ndarray

    @classmethod
    def open(cls, prepared_root: Path, symbol: str, mmap: bool=True):
        d=prepared_root/safe_symbol(symbol); mode="r" if mmap else None
        streams={}
        for tf in ["M1","M5","M30","H4"]:
            streams[tf]=(
                np.load(d/f"{tf}_x.npy",mmap_mode=mode),
                np.load(d/f"{tf}_available_ns.npy",mmap_mode=mode),
                np.load(d/f"{tf}_valid.npy",mmap_mode=mode),
            )
        return cls(symbol,d,streams,
                   np.load(d/"decision_ns.npy",mmap_mode=mode),
                   np.load(d/"future_logret.npy",mmap_mode=mode),
                   np.load(d/"future_normret.npy",mmap_mode=mode),
                   np.load(d/"decision_sigma1m.npy",mmap_mode=mode),
                   np.load(d/"decision_spread_return.npy",mmap_mode=mode))


class CausalWindowDataset(Dataset):
    def __init__(self, prepared_root: Path, config: dict, symbols: list[str], target_symbols: list[str]|None=None,
                 years: list[int]|None=None):
        self.root=Path(prepared_root); self.cfg=config; self.symbols=list(symbols)
        self.tf_order=list(config["timeframes"].keys())
        self.markets={s:PreparedMarket.open(self.root,s) for s in self.symbols}
        targets=target_symbols or symbols
        samples=[]
        for s in targets:
            m=self.markets[s]
            # Require enough *causally valid* target history for at least one full
            # patch in every base timeframe. This removes only initialization warmup;
            # it is not an outcome- or P/L-based sample filter.
            warm=[]
            for tf in self.tf_order:
                _,av,v=m.streams[tf]; need=int(config["timeframes"][tf]["patch"])
                vi=np.flatnonzero(np.asarray(v,dtype=np.uint8)>0)
                if len(vi)<need:
                    warm.append(np.iinfo(np.int64).max)
                else:
                    warm.append(int(av[vi[need-1]]))
            warmup=max(warm)
            for i,t in enumerate(m.decision_ns):
                if int(t)<warmup: continue
                y=pd.Timestamp(int(t)).year
                if years is None or y in years:
                    samples.append((s,i,int(t)))
        self.samples=samples

    def __len__(self): return len(self.samples)

    def _window(self, market: PreparedMarket, tf: str, t: int):
        x,av,v=market.streams[tf]; L=int(self.cfg["timeframes"][tf]["history"])
        end=int(np.searchsorted(av,t,side="right"))
        start=max(0,end-L); q=np.array(x[start:end],dtype=np.float32,copy=True); vv=np.asarray(v[start:end],dtype=np.uint8).astype(bool)
        if len(q): q[~vv]=0.0
        out=np.zeros((L,x.shape[1]),np.float32); mask=np.zeros(L,np.bool_)
        n=len(q)
        if n:
            out[-n:]=q; mask[-n:]=vv
            age=max(0.0,(t-int(av[end-1]))/60e9)
        else: age=1e6
        return out,mask,np.float32(np.log1p(age))

    def __getitem__(self, idx):
        target,di,t=self.samples[idx]
        streams={tf:[] for tf in self.tf_order}; masks={tf:[] for tf in self.tf_order}; ages={tf:[] for tf in self.tf_order}
        target_mask=[]
        for s in self.symbols:
            m=self.markets[s]
            target_mask.append(s==target)
            for tf in self.tf_order:
                x,ma,ag=self._window(m,tf,t);streams[tf].append(x);masks[tf].append(ma);ages[tf].append(ag)
        tm=self.markets[target]
        y_norm=np.array(tm.future_normret[di],dtype=np.float32,copy=True); y_raw=np.array(tm.future_logret[di],dtype=np.float32,copy=True)
        return {
            "streams":{tf:torch.from_numpy(np.stack(streams[tf])) for tf in self.tf_order},
            "masks":{tf:torch.from_numpy(np.stack(masks[tf])) for tf in self.tf_order},
            "ages":{tf:torch.from_numpy(np.asarray(ages[tf],np.float32)) for tf in self.tf_order},
            "target_mask":torch.tensor(target_mask,dtype=torch.bool),
            "y_norm":torch.from_numpy(y_norm),
            "y_raw":torch.from_numpy(y_raw),
            "sigma1m":torch.tensor(float(tm.sigma1m[di]),dtype=torch.float32),
            "spread_return":torch.tensor(float(tm.spread_return[di]),dtype=torch.float32),
            "decision_ns":torch.tensor(t,dtype=torch.int64),
        }
