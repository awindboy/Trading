#!/usr/bin/env python3
"""V4-001 MarketJEPA model.

This module adapts the *research idea* of joint-embedding predictive representation
learning to the project's causal multi-market/multi-resolution dataset.  It does not
copy the external Fin-JEPA implementation and does not claim architectural parity.

The encoder topology deliberately matches the representation body of the frozen
V4_001_CausalPatchPolicy so the tournament compares training objectives rather than
silently changing both objective and capacity at once.
"""
from __future__ import annotations
import torch
from torch import nn
import torch.nn.functional as F

from v4_001_model import PatchStreamEncoder


class CausalPatchEncoder(nn.Module):
    def __init__(self, cfg: dict, feature_dim: int):
        super().__init__()
        d = int(cfg["d_model"])
        self.tf_order = list(cfg["timeframes"].keys())
        self.local = nn.ModuleDict()
        for tf, s in cfg["timeframes"].items():
            self.local[tf] = PatchStreamEncoder(
                feature_dim,
                int(s["history"]),
                int(s["patch"]),
                d,
                int(cfg["nhead"]),
                int(cfg["local_layers"]),
                int(cfg["dim_feedforward"]),
                float(cfg["dropout"]),
            )
        self.tf_emb = nn.Parameter(torch.randn(len(self.tf_order), d) * 0.02)
        self.target_emb = nn.Embedding(2, d)
        self.age = nn.Sequential(nn.Linear(1, d), nn.GELU(), nn.Linear(d, d))
        layer = nn.TransformerEncoderLayer(
            d,
            int(cfg["nhead"]),
            int(cfg["dim_feedforward"]),
            float(cfg["dropout"]),
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.fusion = nn.TransformerEncoder(layer, int(cfg["fusion_layers"]))
        self.to_latent = nn.Sequential(
            nn.Linear(d * 2, int(cfg["latent_dim"])),
            nn.GELU(),
            nn.LayerNorm(int(cfg["latent_dim"])),
        )

    def forward(self, batch):
        toks, valids, target_flags = [], [], []
        tm = batch["target_mask"]
        for j, tf in enumerate(self.tf_order):
            z, v = self.local[tf](batch["streams"][tf].float(), batch["masks"][tf].bool())
            age = batch["ages"][tf].float().unsqueeze(-1)
            z = z + self.tf_emb[j].view(1, 1, -1) + self.target_emb(tm.long()) + self.age(age)
            toks.append(z)
            valids.append(v)
            target_flags.append(tm & v)
        z = torch.cat(toks, 1)
        valid = torch.cat(valids, 1)
        tf_target = torch.cat(target_flags, 1)
        z = self.fusion(z, src_key_padding_mask=~valid)
        global_mean = (z * valid.unsqueeze(-1)).sum(1) / valid.sum(1, keepdim=True).clamp_min(1)
        target_mean = (z * tf_target.unsqueeze(-1)).sum(1) / tf_target.sum(1, keepdim=True).clamp_min(1)
        return self.to_latent(torch.cat([target_mean, global_mean], -1))


class LatentPredictor(nn.Module):
    def __init__(self, dim: int = 128, hidden: int = 256):
        super().__init__()
        self.net = nn.Sequential(
            nn.LayerNorm(dim),
            nn.Linear(dim, hidden),
            nn.GELU(),
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Linear(hidden, dim),
        )

    def forward(self, z):
        return self.net(z)


def _off_diagonal(x: torch.Tensor) -> torch.Tensor:
    n, m = x.shape
    if n != m:
        raise ValueError("covariance matrix must be square")
    return x.flatten()[:-1].view(n - 1, n + 1)[:, 1:].flatten()


def isotropy_regularizer(z: torch.Tensor):
    """Small-batch anti-collapse regularizer inspired by SIGReg/VICReg ideas.

    We keep this implementation explicit and auditable: each latent coordinate is
    encouraged to retain non-zero batch variance and off-diagonal batch covariance is
    discouraged.  It is not claimed to be the exact SIGReg estimator from Fin-JEPA.
    """
    if z.shape[0] < 2:
        zero = z.sum() * 0.0
        return zero, zero
    zc = z - z.mean(0, keepdim=True)
    std = torch.sqrt(zc.var(0, unbiased=False) + 1e-4)
    var_loss = F.relu(1.0 - std).mean()
    cov = (zc.T @ zc) / max(1, z.shape[0] - 1)
    cov_loss = _off_diagonal(cov).pow(2).sum() / z.shape[1]
    return var_loss, cov_loss


class MarketJEPA(nn.Module):
    def __init__(self, base_cfg: dict, jepa_cfg: dict, feature_dim: int):
        super().__init__()
        self.encoder = CausalPatchEncoder(base_cfg, feature_dim)
        self.predictor = LatentPredictor(int(base_cfg["latent_dim"]), int(jepa_cfg["predictor_hidden"]))
        self.weights = jepa_cfg["loss_weights"]

    def encode(self, batch):
        return self.encoder(batch)

    def forward(self, context_batch, future_batch):
        z0 = self.encoder(context_batch)
        z1 = self.encoder(future_batch)
        pred = self.predictor(z0)
        # Normalize only for the predictive term.  Scale/isotropy is controlled separately.
        pred_loss = F.smooth_l1_loss(F.normalize(pred, dim=-1), F.normalize(z1.detach(), dim=-1))
        v0, c0 = isotropy_regularizer(z0)
        v1, c1 = isotropy_regularizer(z1)
        var_loss = 0.5 * (v0 + v1)
        cov_loss = 0.5 * (c0 + c1)
        total = (
            float(self.weights["latent_prediction"]) * pred_loss
            + float(self.weights["variance"]) * var_loss
            + float(self.weights["covariance"]) * cov_loss
        )
        return total, {
            "pred": float(pred_loss.detach()),
            "var": float(var_loss.detach()),
            "cov": float(cov_loss.detach()),
        }
