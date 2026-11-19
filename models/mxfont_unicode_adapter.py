"""Optional Arabic Unicode conditioning bridge for the pinned MX-Font factors.

This module does not replace MX-Font's image encoder, localized experts, or
decoder. It injects a zero-initialized, gated Unicode residual into the
content-factor tensors returned by MX-Font Generator.factorize(..., emb_dim=1).
With the adapter freshly initialized, outputs are exactly unchanged.
"""
from __future__ import annotations

from typing import Mapping

import torch
from torch import nn

from models.arabic_multimodal_glyph import UnicodeSequenceEncoder


class MXFontUnicodeFactorAdapter(nn.Module):
    """Add target-codepoint information to MX-Font content factors.

    Expected MX-Font factor shapes:
      last: [batch, experts, 256, 16, 16]
      skip: [batch, experts, 128, 32, 32]

    Channel counts are configurable for compatible MX-Font variants.
    The adapter is deliberately opt-in and starts as an exact identity.
    """

    def __init__(
        self,
        factor_channels: Mapping[str, int] | None = None,
        latent_dim: int = 256,
        vocab_size: int = 0x110000,
        embedding_dim: int = 16,
    ):
        super().__init__()
        channels = dict(factor_channels or {"last": 256, "skip": 128})
        if not channels or any(not key or int(value) <= 0 for key, value in channels.items()):
            raise ValueError("factor_channels must map factor names to positive channel counts")
        self.content_encoder = UnicodeSequenceEncoder(
            vocab_size=vocab_size,
            embedding_dim=embedding_dim,
            latent_dim=latent_dim,
        )
        self.adapters = nn.ModuleDict()
        for name, count in channels.items():
            block = nn.ModuleDict({
                "residual": nn.Linear(latent_dim, int(count)),
                "gate": nn.Linear(latent_dim + int(count), int(count)),
            })
            # Preserve the pretrained MX-Font function at initialization.
            nn.init.zeros_(block["residual"].weight)
            nn.init.zeros_(block["residual"].bias)
            self.adapters[name] = block

    def forward(self, content_factors, target_ids, attention_mask=None):
        if not isinstance(content_factors, Mapping) or not content_factors:
            raise ValueError("content_factors must be a non-empty MX-Font factor mapping")
        unicode_latent = self.content_encoder(target_ids, attention_mask)
        adapted = dict(content_factors)
        for name, block in self.adapters.items():
            if name not in content_factors:
                raise ValueError(f"missing MX-Font content factor: {name}")
            factor = content_factors[name]
            if factor.ndim != 5:
                raise ValueError(f"{name} must have shape [batch, experts, channels, height, width]")
            batch, experts, channels, height, width = factor.shape
            expected = block["residual"].out_features
            if channels != expected:
                raise ValueError(f"{name} channel mismatch: expected {expected}, got {channels}")
            if batch != unicode_latent.shape[0]:
                raise ValueError("target_ids batch size must match MX-Font factors")
            pooled = factor.mean(dim=(1, 3, 4))
            gate = torch.sigmoid(block["gate"](torch.cat([unicode_latent, pooled], dim=-1)))
            residual = block["residual"](unicode_latent) * gate
            adapted[name] = factor + residual[:, None, :, None, None]
        return adapted
