"""Experimental content-and-style conditioned Arabic glyph raster generator.

Every route receives an explicit target Unicode sequence. Style is conditioned
by reference glyph images, a textual style description, or both. The text
encoder is a trainable codepoint GRU, not a pretrained semantic language model.
"""
from __future__ import annotations

import torch
from torch import nn


class UnicodeSequenceEncoder(nn.Module):
    """Character-level Unicode encoder; no pretrained linguistic semantics."""
    def __init__(self, vocab_size: int, embedding_dim: int, latent_dim: int):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.gru = nn.GRU(
            embedding_dim, latent_dim, batch_first=True, bidirectional=True
        )
        self.projection = nn.Linear(latent_dim * 2, latent_dim)

    def forward(self, token_ids, attention_mask=None):
        embedded = self.embedding(token_ids)
        outputs, _ = self.gru(embedded)
        if attention_mask is None:
            mask = (token_ids != 0).unsqueeze(-1)
        else:
            mask = attention_mask.bool().unsqueeze(-1)
        pooled = (outputs * mask).sum(1) / mask.sum(1).clamp_min(1)
        return self.projection(pooled)


class ImageStyleEncoder(nn.Module):
    def __init__(self, latent_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1, 32, 4, 2, 1), nn.GroupNorm(4, 32), nn.GELU(),
            nn.Conv2d(32, 64, 4, 2, 1), nn.GroupNorm(8, 64), nn.GELU(),
            nn.Conv2d(64, 128, 4, 2, 1), nn.GroupNorm(8, 128), nn.GELU(),
            nn.Conv2d(128, 192, 4, 2, 1), nn.GroupNorm(8, 192), nn.GELU(),
            nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(192, latent_dim),
        )

    def forward(self, images):
        # [batch, references, 1, 128, 128]
        batch, count, channels, height, width = images.shape
        encoded = self.net(
            images.reshape(batch * count, channels, height, width)
        ).reshape(batch, count, -1)
        return encoded.mean(dim=1)


class SharedGlyphDecoder(nn.Module):
    def __init__(self, latent_dim=256):
        super().__init__()
        self.project = nn.Linear(latent_dim, 256 * 4 * 4)
        self.net = nn.Sequential(
            nn.ConvTranspose2d(256, 192, 4, 2, 1), nn.GroupNorm(8, 192), nn.GELU(),
            nn.ConvTranspose2d(192, 128, 4, 2, 1), nn.GroupNorm(8, 128), nn.GELU(),
            nn.ConvTranspose2d(128, 64, 4, 2, 1), nn.GroupNorm(8, 64), nn.GELU(),
            nn.ConvTranspose2d(64, 32, 4, 2, 1), nn.GroupNorm(4, 32), nn.GELU(),
            nn.ConvTranspose2d(32, 1, 4, 2, 1), nn.Sigmoid(),
        )

    def forward(self, latent):
        return self.net(self.project(latent).reshape(-1, 256, 4, 4))


class ArabicMultimodalGlyphModel(nn.Module):
    """One target-content encoder, two style encoders, and one shared decoder.

    Modes:
      image: target_ids + reference_images
      text: target_ids + style_prompt_ids
      hybrid: target_ids + reference_images + style_prompt_ids
    """
    def __init__(self, latent_dim=256, vocab_size=0x110000, embedding_dim=32):
        super().__init__()
        self.content_encoder = UnicodeSequenceEncoder(
            vocab_size, embedding_dim, latent_dim
        )
        self.image_style_encoder = ImageStyleEncoder(latent_dim)
        self.text_style_encoder = UnicodeSequenceEncoder(
            vocab_size, embedding_dim, latent_dim
        )
        self.confidence_gate = nn.Sequential(
            nn.Linear(latent_dim * 2, latent_dim), nn.Sigmoid()
        )
        self.style_fusion = nn.Sequential(
            nn.Linear(latent_dim * 2, latent_dim), nn.LayerNorm(latent_dim), nn.GELU()
        )
        self.content_style_fusion = nn.Sequential(
            nn.Linear(latent_dim * 2, latent_dim), nn.LayerNorm(latent_dim), nn.GELU()
        )
        self.decoder = SharedGlyphDecoder(latent_dim)
        self.uncertainty_head = nn.Sequential(
            nn.Linear(latent_dim, latent_dim // 2), nn.GELU(),
            nn.Linear(latent_dim // 2, 1), nn.Sigmoid()
        )

    def forward(
        self,
        mode,
        target_ids=None,
        reference_images=None,
        style_prompt_ids=None,
        target_attention_mask=None,
        style_attention_mask=None,
    ):
        if mode not in {"image", "text", "hybrid"}:
            raise ValueError("mode must be image, text, or hybrid")
        if target_ids is None:
            raise ValueError("target_ids are required for every conditioning mode")
        content_latent = self.content_encoder(target_ids, target_attention_mask)

        image_style = None
        text_style = None
        if mode in {"image", "hybrid"}:
            if reference_images is None:
                raise ValueError("reference_images required for image/hybrid mode")
            image_style = self.image_style_encoder(reference_images)
        if mode in {"text", "hybrid"}:
            if style_prompt_ids is None:
                raise ValueError("style_prompt_ids required for text/hybrid mode")
            text_style = self.text_style_encoder(style_prompt_ids, style_attention_mask)

        if mode == "image":
            style_latent = image_style
        elif mode == "text":
            style_latent = text_style
        else:
            gate = self.confidence_gate(torch.cat([image_style, text_style], dim=-1))
            style_latent = self.style_fusion(torch.cat([
                gate * image_style, (1 - gate) * text_style
            ], dim=-1))

        latent = self.content_style_fusion(
            torch.cat([content_latent, style_latent], dim=-1)
        )
        return {
            "image": self.decoder(latent),
            "latent": latent,
            "style_latent": style_latent,
            "content_latent": content_latent,
            "uncertainty": self.uncertainty_head(latent),
        }


def encode_unicode_batch(texts, max_length=64, device=None):
    """Convert strings to Unicode scalar values; truncates and pads with zero."""
    ids = torch.zeros((len(texts), max_length), dtype=torch.long, device=device)
    for index, text in enumerate(texts):
        values = [ord(char) for char in text[:max_length]]
        if values:
            ids[index, :len(values)] = torch.tensor(
                values, dtype=torch.long, device=device
            )
    return ids


def save_training_checkpoint(path, model, optimizer=None, step=0, metadata=None):
    """Atomically save model/optimizer state for resumable experiments."""
    import os
    import tempfile
    from pathlib import Path

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"model": model.state_dict(), "step": int(step), "metadata": metadata or {}}
    if optimizer is not None:
        payload["optimizer"] = optimizer.state_dict()
    fd, temp_path = tempfile.mkstemp(
        prefix=target.name + ".", suffix=".tmp", dir=str(target.parent)
    )
    os.close(fd)
    try:
        torch.save(payload, temp_path)
        os.replace(temp_path, target)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def restore_training_checkpoint(path, model, optimizer=None, map_location="cpu"):
    """Restore model and optional optimizer; return saved step and metadata."""
    payload = torch.load(path, map_location=map_location, weights_only=True)
    model.load_state_dict(payload["model"])
    if optimizer is not None:
        if "optimizer" not in payload:
            raise ValueError("checkpoint has no optimizer state; cannot resume optimizer")
        optimizer.load_state_dict(payload["optimizer"])
    return {"step": int(payload.get("step", 0)), "metadata": payload.get("metadata", {})}
