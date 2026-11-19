# Local training handoff

## Training inputs

Use the GitHub Actions artifacts from a successful data-pipeline run:

1. `conditional-ofl-font-rights-manifest` — exact 52-file/20-family conditional OFL rights manifest.
2. `arabic-contextual-style-episodes` — train/validation/test few-shot episodes and a no-training preflight report.
3. `arabic-harfbuzz-contextual-clusters` — contextual target images.
4. `isolated-arabic-glyph-crops` — same-font isolated style-reference images.

Extract the artifacts so the local paths are:

- `data/manifests/font_rights.json`
- `data/contextual_style_episodes/train.jsonl`, `validation.jsonl`, `test.jsonl`
- `data/contextual_glyph_crops/contextual_clusters.jsonl` and `images/`
- `data/glyph_crops/glyph_crops.jsonl` and `images/`

The episode builder creates four reference glyphs from the exact same font as each target, excludes all target codepoints from the references, and preserves family-level splits.

## Environment

Install a compatible PyTorch build for the machine and Pillow:

```bash
python -m pip install torch Pillow
```

Check available hardware before selecting a device. `--device auto` selects CUDA when PyTorch detects it; otherwise it uses CPU. The project has not yet verified the user's Windows GPU, VRAM, RAM, or runtime.

## Explicit training command

The trainer requires an explicit `--max-steps`; it will not start an unbounded run by default.

```bash
python -m scripts.train_multimodal_glyph `
  --episodes-dir data/contextual_style_episodes `
  --target-root data/contextual_glyph_crops `
  --reference-root data/glyph_crops `
  --rights-manifest data/manifests/font_rights.json `
  --output-dir runs/arabic-contextual-baseline `
  --max-steps 1000 `
  --batch-size 8 `
  --latent-dim 64 `
  --device auto
```

The backticks shown above are PowerShell line-continuation characters.

To resume from a saved checkpoint, pass `--resume runs/arabic-contextual-baseline/checkpoints/last.pt` and set `--max-steps` to the desired total step count, not the number of additional steps.

## What this trainer actually learns

- It trains the **image-reference route**: target Unicode cluster + four same-font reference glyph images → target contextual raster.
- It uses a pixel L1 loss plus a raster edge loss.
- It evaluates on family-held-out validation and test splits and saves optimizer/model state.
- It does not train the text-style route; the current captions are not reviewed semantic style prompts.
- It does not convert raster predictions into TTF/OTF files. Vectorization, contour cleanup, font tables, naming, shaping, and final font QA are separate stages.
- It does not replace HarfBuzz for arbitrary text shaping.

## License conditions

The exact 52 Google Fonts source files are conditionally approved for this training pipeline only if generated font software based on them is released under SIL OFL 1.1, copyright notices and acknowledgements are preserved, and recorded Reserved Font Names are not reused without written permission. OFL is not a NonCommercial license: downstream commercial use is not prohibited by OFL. The project itself can distribute its own outputs for free.

The model-weight license is separate and must be decided independently. Arabeyes GPL+Font Exception fonts are not included in the active rights manifest.

## Current status

The data/rights preflight is automated. The project has not started this training script on the full dataset. Tiny-subset overfit, convergence, held-out-family quality, font vectorization, and local hardware preflight still need to be demonstrated before claiming the generator is ready for production use.
