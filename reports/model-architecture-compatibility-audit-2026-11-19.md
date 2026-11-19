# Model Architecture Compatibility Audit — 2026-11-19

## Scope

This is a source-level architecture and data-contract inspection of:

1. The selected upstream MX-Font implementation pinned in `docs/UPSTREAM_BASELINE.md` at `clovaai/fewshot-font-generation@9d2b6ace3e23199e2a896de329d4c16489b09a96`.
2. The separately added experimental model `models/arabic_multimodal_glyph.py`.
3. The current episode/training contract documented by this repository.

No training was started. No model weights were merged, converted, overwritten, or deleted. This audit does not establish output quality.

## Finding 1 — These are materially different architectures

### Upstream MX-Font

Inspected upstream source files:

- `MX/models/style_encoder.py`
- `MX/models/experts.py`
- `MX/models/generator.py`
- `MX/models/decoder.py`
- `MX/dataset.py`
- `MX/trainer.py`

The generator uses a convolutional style encoder, then multiple parallel localized experts (the standard config sets six). Each expert produces feature maps at two scales (32×32 skip features and 16×16 final features). MX-Font factorizes expert features into learned factors, combines style factors with character-content factors, reconstructs feature maps, and decodes them with expert-aware skip integration to a 128×128 raster.

The training objective is not just pixel reconstruction. The trainer includes adversarial/discriminator and feature-matching terms, pixel loss, expert/factor independence objectives, and auxiliary classification objectives.

MX-Font's content input is an image of the *same character* rendered in another font. Its style references are other characters from the target font. During training, `MXTrainDataset` selects:
- target glyph image from a target font;
- style reference glyphs from that same target font, excluding the target character;
- same-character content glyphs from other fonts, excluding the target font;
- decomposition/primitive labels for the character.

The model's standard inference interface accepts `style_imgs` and `char_imgs`, not a Unicode codepoint sequence.

### Experimental repository model

`models/arabic_multimodal_glyph.py` instead has:
- a bidirectional GRU over Unicode codepoints for target identity;
- a CNN that averages image-reference embeddings;
- another Unicode GRU for a textual style prompt;
- an optional confidence-gated fusion of image and text style vectors;
- a single dense/convolutional raster decoder and an uncertainty head.

It does not implement MX-Font's localized expert bank, feature factorization/defactorization, expert-specific skip fusion, discriminator, or MX-Font's decomposition/auxiliary objectives. Its Unicode GRU is a trainable codepoint encoder, not a pretrained Arabic language model.

## Finding 2 — The data contracts do not match

The current experimental episode trainer supplies a target Unicode cluster and four same-font reference images. That matches the experimental model's image route.

MX-Font training requires more than that: it needs same-character content images from other fonts, same-font style references, and character decomposition into the configured primitive inventory. The current episode package does not provide MX-Font's complete native sample contract or audited Arabic decomposition labels.

Therefore the existing 1,732-episode handoff cannot simply be passed to the upstream MX-Font trainer. A separate MX-Font Arabic adapter and defensible decomposition/primitive supervision would be required.

## Finding 3 — Direct weight merging is not supported

The two models have different module graphs, tensor names, shapes, and latent semantics. There is no demonstrated one-to-one mapping for loading the experimental model's parameters into MX-Font, or vice versa. Their checkpoints are not directly merge-compatible.

A technically plausible research direction is to preserve MX-Font as the baseline and add a *new, separately tested Arabic conditioning branch* at a carefully chosen feature/factor interface. The Unicode encoder or selected ideas from the experimental model could be evaluated as a conditioning branch, but its decoder and existing weights should not be assumed reusable. Any such integration would require an explicit adapter, controlled ablations, and tests against the unchanged MX-Font baseline.

## Recommendation

1. Keep the pinned MX-Font source and checkpoint path as the primary architecture for the original plan.
2. Keep `arabic_multimodal_glyph.py` quarantined as an independent research prototype; do not treat it as the merged model or as a replacement for MX-Font.
3. Do not train either model yet on the assumption that the current dataset is native MX-Font-ready.
4. Next architecture task should be a native MX-Font compatibility design: document the exact target/style/content image construction, Arabic primitive/decomposition requirements, and insertion point for Unicode/joining metadata. Only then implement an adapter and run baseline-vs-branch ablations.

## Audit status

- Upstream MX-Font source inspected: PASS (source-level).
- Experimental model source inspected: PASS.
- Direct checkpoint/weight compatibility: FAIL (no compatible mapping established).
- Current dataset directly compatible with native MX-Font loader: FAIL (required content-image/decomposition contract is absent).
- A safe, testable branch-integration design: NOT YET IMPLEMENTED.
- Training started: NO.

This report is a technical source inspection, not a legal opinion or a claim of model-quality validation.
