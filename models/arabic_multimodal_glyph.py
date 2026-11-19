"""Experimental multimodal Arabic glyph raster baseline.

This is a small, executable research baseline, not MX-Font, not an LLM, and
not a semantically pretrained Arabic text encoder. Prompt input is encoded at
Unicode codepoint level. All three conditioning routes share one decoder.
"""
from __future__ import annotations
import torch
from torch import nn

class ImageReferenceEncoder(nn.Module):
    def __init__(self, latent_dim: int):
        super().__init__()
        self.net=nn.Sequential(
            nn.Conv2d(1,32,4,2,1),nn.GroupNorm(4,32),nn.GELU(),
            nn.Conv2d(32,64,4,2,1),nn.GroupNorm(8,64),nn.GELU(),
            nn.Conv2d(64,128,4,2,1),nn.GroupNorm(8,128),nn.GELU(),
            nn.Conv2d(128,192,4,2,1),nn.GroupNorm(8,192),nn.GELU(),
            nn.AdaptiveAvgPool2d(1),nn.Flatten(),nn.Linear(192,latent_dim))
    def forward(self, images):
        # [batch, references, 1, 128, 128]
        b,n,c,h,w=images.shape
        encoded=self.net(images.reshape(b*n,c,h,w)).reshape(b,n,-1)
        return encoded.mean(dim=1)

class UnicodePromptEncoder(nn.Module):
    def __init__(self, vocab_size=0x110000, embedding_dim=128, latent_dim=256):
        super().__init__()
        self.embedding=nn.Embedding(vocab_size,embedding_dim,padding_idx=0)
        self.gru=nn.GRU(embedding_dim,latent_dim,batch_first=True,bidirectional=True)
        self.projection=nn.Linear(latent_dim*2,latent_dim)
    def forward(self, token_ids, attention_mask=None):
        embedded=self.embedding(token_ids)
        outputs,_=self.gru(embedded)
        if attention_mask is None:
            mask=(token_ids!=0).unsqueeze(-1)
        else:
            mask=attention_mask.bool().unsqueeze(-1)
        pooled=(outputs*mask).sum(1)/mask.sum(1).clamp_min(1)
        return self.projection(pooled)

class SharedGlyphDecoder(nn.Module):
    def __init__(self, latent_dim=256):
        super().__init__()
        self.project=nn.Linear(latent_dim,256*4*4)
        self.net=nn.Sequential(
            nn.ConvTranspose2d(256,192,4,2,1),nn.GroupNorm(8,192),nn.GELU(),
            nn.ConvTranspose2d(192,128,4,2,1),nn.GroupNorm(8,128),nn.GELU(),
            nn.ConvTranspose2d(128,64,4,2,1),nn.GroupNorm(8,64),nn.GELU(),
            nn.ConvTranspose2d(64,32,4,2,1),nn.GroupNorm(4,32),nn.GELU(),
            nn.ConvTranspose2d(32,1,4,2,1),nn.Sigmoid())
    def forward(self, latent):
        return self.net(self.project(latent).reshape(-1,256,4,4))

class ArabicMultimodalGlyphModel(nn.Module):
    """Shared image/text/hybrid conditional glyph raster generator."""
    def __init__(self, latent_dim=256, vocab_size=0x110000):
        super().__init__()
        self.image_encoder=ImageReferenceEncoder(latent_dim)
        self.prompt_encoder=UnicodePromptEncoder(vocab_size=vocab_size,latent_dim=latent_dim)
        self.image_projection=nn.Linear(latent_dim,latent_dim)
        self.prompt_projection=nn.Linear(latent_dim,latent_dim)
        self.confidence_gate=nn.Sequential(nn.Linear(latent_dim*2,latent_dim),nn.Sigmoid())
        self.shared_fusion=nn.Sequential(nn.Linear(latent_dim*2,latent_dim),nn.LayerNorm(latent_dim),nn.GELU())
        self.decoder=SharedGlyphDecoder(latent_dim)
        self.uncertainty_head=nn.Sequential(nn.Linear(latent_dim,latent_dim//2),nn.GELU(),nn.Linear(latent_dim//2,1),nn.Sigmoid())
    def forward(self, mode, reference_images=None, prompt_ids=None, attention_mask=None):
        if mode not in {"image","text","hybrid"}:
            raise ValueError("mode must be image, text, or hybrid")
        image_latent=None; prompt_latent=None
        if mode in {"image","hybrid"}:
            if reference_images is None: raise ValueError("reference_images required for image/hybrid mode")
            image_latent=self.image_projection(self.image_encoder(reference_images))
        if mode in {"text","hybrid"}:
            if prompt_ids is None: raise ValueError("prompt_ids required for text/hybrid mode")
            prompt_latent=self.prompt_projection(self.prompt_encoder(prompt_ids,attention_mask))
        if mode=="image": latent=image_latent
        elif mode=="text": latent=prompt_latent
        else:
            gate=self.confidence_gate(torch.cat([image_latent,prompt_latent],dim=-1))
            latent=self.shared_fusion(torch.cat([gate*image_latent,(1-gate)*prompt_latent],dim=-1))
        return {"image":self.decoder(latent),"latent":latent,"uncertainty":self.uncertainty_head(latent)}

def encode_unicode_batch(texts, max_length=64, device=None):
    """Convert strings to Unicode scalar values; truncates and pads with zero."""
    ids=torch.zeros((len(texts),max_length),dtype=torch.long,device=device)
    for i,text in enumerate(texts):
        values=[ord(ch) for ch in text[:max_length]]
        if values: ids[i,:len(values)]=torch.tensor(values,dtype=torch.long,device=device)
    return ids


def save_training_checkpoint(path, model, optimizer=None, step=0, metadata=None):
    """Atomically save model/optimizer state for resumable experiments."""
    import os, tempfile
    from pathlib import Path
    target=Path(path); target.parent.mkdir(parents=True,exist_ok=True)
    payload={"model":model.state_dict(),"step":int(step),"metadata":metadata or {}}
    if optimizer is not None: payload["optimizer"]=optimizer.state_dict()
    fd,tmp=tempfile.mkstemp(prefix=target.name+".",suffix=".tmp",dir=str(target.parent))
    os.close(fd)
    try:
        torch.save(payload,tmp)
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def restore_training_checkpoint(path, model, optimizer=None, map_location="cpu"):
    """Restore model and optional optimizer; return the saved step/metadata."""
    payload=torch.load(path,map_location=map_location,weights_only=True)
    model.load_state_dict(payload["model"])
    if optimizer is not None:
        if "optimizer" not in payload:
            raise ValueError("checkpoint has no optimizer state; cannot resume optimizer")
        optimizer.load_state_dict(payload["optimizer"])
    return {"step":int(payload.get("step",0)),"metadata":payload.get("metadata",{})}
