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
codepoints: in the pinned MX-Font dataset they are dataset-local class IDs.
The bridge must be applied only to the batch-aggregated content factors
(`mean_char_facts`, after averaging the `n_c` cross-font content samples),
not to raw `char_facts_c` and never to style factors.

## Required ablation

Run on identical family-held-out episodes and seeds:
1. B0: untouched MX-Font baseline.
2. B1: MX-Font + Unicode bridge, initially frozen/identity.
3. B2: train the bridge and compare reconstruction, edge, dot/component,
   contextual-cluster, and held-out-family metrics.

Keep B0 checkpoint and outputs immutable. Adopt B2 only if it improves held-out
Arabic quality without harming character identity or joining behavior.
No training, checkpoint merge, or baseline modification is performed by adding
this module. Unit tests verify the synthetic factor tensor contract, identity
initialization, shape preservation, and construction of an autograd graph.
They do not call backward, create an optimizer, update weights, or train.


## Current validation boundary

- Unit tests use synthetic factor tensors with the expected channel/spatial shapes; they do not load the pinned upstream MX-Font checkpoint or execute its real Generator.
- The adapter remains optional and is not connected to MX-Font's training loop or dataset loader.
- Unicode sequences must be recovered from the original target string through a verified character-to-codepoint mapping; passing dataset-local trg_cids directly would be incorrect.
- No backward pass, optimizer step, weight update, checkpoint merge or training is part of this branch's validation.
