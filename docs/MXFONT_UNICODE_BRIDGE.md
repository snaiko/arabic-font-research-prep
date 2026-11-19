# MX-Font Unicode conditioning bridge — controlled experiment

## Decision

Reuse only the Unicode content encoder idea from
`models/arabic_multimodal_glyph.py`. Do **not** transplant its image-style CNN
or raster decoder: the pinned MX-Font already has an image style encoder,
multiple localized experts, factorization blocks, and a decoder.

## Where the bridge attaches

At the pinned upstream MX-Font path, `Generator.factorize(feats, emb_dim=1)`
returns content-factor maps shaped `[batch, experts, channels, height, width]`.
The bridge encodes the target Unicode sequence and adds a learned, gated
per-channel residual to those content factors, before
`Generator.defactorize(style_factors, content_factors)`.

Expected default factor sizes from the pinned MX-Font implementation:
- `last`: 256 channels per expert;
- `skip`: 128 channels per expert.

The adapter does not import, copy, or modify MX-Font upstream source. It is an
optional project-side module. It starts as an exact identity because the
Unicode residual projections are zero-initialized. Thus an untrained bridge
cannot silently alter the baseline output.

## Why this is the useful part

- The target Unicode sequence provides explicit Arabic character identity,
  including multi-codepoint sequences and combining marks.
- MX-Font remains responsible for visual content/style synthesis and its
  localized experts remain intact.
- The new model's standalone image-style CNN duplicates a role MX-Font already
  performs; its independent raster decoder would replace rather than augment
  the selected baseline. Neither is used in this bridge.
- The confidence gate is retained in a narrower role: it gates the Unicode
  residual against pooled MX-Font content-factor statistics.

## Integration boundary

The adapter is **not yet wired into the MX-Font trainer**. Before wiring it,
the data loader must prove that each target batch has the exact Unicode
sequence corresponding to `trg_imgs`. Do not assume `trg_cids` are Unicode
codepoints: in MX-Font they may be dataset-local class IDs. The trainer must
also apply the bridge only to `char_facts_c` (content factors), never to
style factors.

## Required ablation

Run on identical family-held-out episodes and seeds:
1. B0: untouched MX-Font baseline.
2. B1: MX-Font + Unicode bridge, initially frozen/identity.
3. B2: train the bridge and compare reconstruction, edge, dot/component,
   contextual-cluster, and held-out-family metrics.

Keep B0 checkpoint and outputs immutable. Adopt B2 only if it improves held-out
Arabic quality without harming character identity or joining behavior.
No training, checkpoint merge, or baseline modification is performed by adding
this module. Unit tests only verify tensor contract, identity initialization,
shape preservation, and gradient flow.
