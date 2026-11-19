# Experimental multimodal glyph baseline

`models/arabic_multimodal_glyph.py` implements one shared raster decoder with three executable conditioning routes:

- **Image:** encode one or more reference glyph images.
- **Text:** encode a Unicode codepoint sequence with a bidirectional GRU.
- **Hybrid:** confidence-gated fusion of the image and Unicode-prompt latents.

The prompt encoder is a trainable character/codepoint encoder, **not** a pretrained Arabic language model and not a semantic natural-language understanding system. The model is an experimental baseline and is not the upstream MX-Font implementation or a verified MX-Font adapter.

The model returns a 128×128 grayscale glyph raster, latent representation, and a learned uncertainty scalar. Unit tests exercise forward/backward on all three routes and checkpoint save/load. These smoke tests prove executable tensor paths only; they do not establish generation quality, convergence, font-style fidelity, or safe training data.

Run on CPU:

```bash
python -m pip install torch
python -m unittest tests.test_multimodal_model_smoke -v
```

Full training remains disabled until the data-rights manifest contains approved exact assets, data review gates pass, and a separate training run is explicitly authorized.
