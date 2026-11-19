# Experimental content-and-style conditioned glyph baseline

`models/arabic_multimodal_glyph.py` now separates **what character to draw** from **what style to draw it in**. Every route requires a target Unicode sequence, and all routes share one raster decoder.

- **Image-style route:** target codepoints + one or more reference glyph images.
- **Text-style route:** target codepoints + an Arabic/English textual style description.
- **Hybrid route:** target codepoints + reference images + textual style description; the two style latents are confidence-gated before fusion.

This corrects the earlier prototype's missing target-identity input on the image route. Without target codepoints, a reference-only model cannot know which glyph it is expected to generate.

## Current limitations

The target-character encoder and text-style encoder are trainable Unicode-codepoint GRUs. The text-style encoder is **not** a pretrained Arabic language model and does not yet understand style semantics. The current dataset has factual synthetic captions, not human-reviewed calligraphic style descriptions. Therefore the text-only and hybrid style-prompt routes are executable architecture paths, not validated style-following systems.

The image style encoder is a small experimental CNN, not the upstream MX-Font architecture or a verified native MX-Font adapter. No generation-quality claim is made.

The model returns a 128×128 grayscale glyph raster, content/style/combined latents, and an uncertainty scalar. Unit tests cover all three routes, required target identity, target-condition differentiation, forward/backward gradient flow, and checkpoint/optimizer resume.

Run on CPU:

```bash
python -m pip install torch
python -m unittest tests.test_multimodal_model_smoke -v
```

Full training remains disabled until the upstream dependency/native-loader work, data review, tiny-subset overfit, held-out-family evaluation, and hardware preflight are complete. The conditional OFL rights manifest separately requires generated font files based on the 52 approved source files to remain under SIL OFL 1.1.


## Local memory footprint

The default Unicode embedding width is 32 rather than 128 to keep the full-Unicode lookup tables practical on a consumer PC. The local trainer exposes `--embedding-dim` so the user can trade memory for capacity. This is still a codepoint embedding, not semantic language understanding.
