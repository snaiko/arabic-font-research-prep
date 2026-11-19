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

Run `START_LOCAL_TRAINING.bat` first. It records CPU/GPU/VRAM/RAM/disk, validates the 52-file/20-family rights manifest and episode splits, verifies all 1,732 target plus 6,928 reference image hashes, and performs one no-training model forward pass. It does not start training. Check `reports/local/machine_preflight.json` and its recommended batch size before proceeding. `--device auto` selects CUDA when PyTorch detects it; otherwise it uses CPU. The project has not yet verified the user's Windows GPU, VRAM, RAM, or runtime.

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
  --batch-size 2 `
  --latent-dim 64 `
  --embedding-dim 16 `
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


## Single-download data artifact

The workflow now packages all runtime data into one GitHub Actions artifact named **arabic-font-training-handoff**. Download that artifact from the latest successful “Build contextual few-shot Arabic style episodes” workflow run, extract its contents into the root of a fresh repository clone, and keep the included data folder structure unchanged. It supplies all four required paths:
- data/contextual_style_episodes/
- data/contextual_glyph_crops/
- data/glyph_crops/
- data/manifests/font_rights.json

The older individual artifacts remain available for audit/history, but the combined artifact is the recommended local handoff. It contains data only, not trained model weights.

## Windows one-click launcher

After extracting the four artifacts into the paths above, run `RUN_IMAGE_ROUTE_TRAINING.bat`. It checks the required manifests and folders, displays the step/batch/device settings, and requires typing `TRAIN` before it starts the actual run. Edit `MAX_STEPS`, `BATCH_SIZE`, `LATENT_DIM`, `EMBEDDING_DIM`, or `DEVICE` at the top of the batch file before starting.

The launcher also refuses to start unless `reports/local/machine_preflight.json` says `READY_FOR_EXPERIMENTAL_IMAGE_ROUTE` and `training_allowed=true`. It is provided for the later training handoff; it has not been run as part of this preparation work.


## Model memory estimate

The latest CPU preflight measured **73,604,738 parameters**. FP32 model weights occupy about **294 MB**. Weights + gradients + the two AdamW moment buffers have an estimated lower bound of about **1.18 GB**, excluding activations, temporary workspaces, the OS, and other processes. This is why the launcher defaults to batch size 4 and embedding width 32. The local hardware preflight recommends a batch size based on detected VRAM/RAM; use its recommendation rather than assuming the default fits every GPU.
