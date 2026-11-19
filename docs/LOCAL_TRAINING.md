# Local training handoff

## One-download data package

Download the GitHub Actions artifact named **arabic-font-training-handoff** from the latest successful [training-handoff workflow run](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44536155715). The verified archive is 9.95 MB with SHA-256:

`30cb94b9218ff0444dcf63c4910ea55d855cbc14c7064bf55908a11d8923c84e`

Extract the artifact contents into the root of a fresh clone of this repository. Do not rename or rearrange the folders. It provides:

- `data/contextual_style_episodes/` — train, validation, test and preflight JSON.
- `data/contextual_glyph_crops/` — contextual target metadata and images.
- `data/glyph_crops/` — isolated same-font reference metadata and images.
- `data/manifests/font_rights.json` — exact conditional OFL 1.1 rights manifest.

The ZIP was independently inspected: 1,732 episodes (1,134 train / 299 validation / 299 test), 20 font families, 52 approved font files, 1,732 target images, 6,928 reference images, zero missing image paths, and no family split leakage.

## Environment and hardware preflight

Use Python 3.10 or newer. Install a compatible PyTorch build for the machine and Pillow:

```powershell
python -m pip install torch Pillow
```

If an NVIDIA GPU is present, install the PyTorch build matching the installed CUDA driver from the official PyTorch installation selector; otherwise the CPU build is sufficient for the preflight, though training may be slow.

Run `START_LOCAL_TRAINING.bat` first. This does **not** train. It records CPU/GPU/VRAM/RAM/free disk, validates the complete 52-file/20-family rights manifest, validates exact episode counts (1,134/299/299), 20-family separation, 238 multi-codepoint targets, and exactly four same-font references per target. It then verifies all 1,732 target and 6,928 reference image SHA-256 values and performs one real 128×128 forward pass.

Read `reports/local/machine_preflight.json`. It reports blockers and a recommended batch size. The CI-runner hardware reading is not a substitute for this Windows preflight on the actual training computer.

## Explicit training launcher

Only after the local preflight reports `READY_FOR_EXPERIMENTAL_IMAGE_ROUTE`, and after the user explicitly decides to start, run:

`RUN_IMAGE_ROUTE_TRAINING.bat`

The launcher rechecks the required data folders and preflight status. It asks the user to type `TRAIN` before it starts a real training run. Defaults are 1,000 total steps, automatically selected batch size based on detected VRAM/RAM, latent dimension 64, Unicode embedding dimension 16, and automatic CUDA/CPU selection. You can override the batch size or other settings at the top of the batch file.

The equivalent PowerShell command is:

```powershell
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

## Model and training scope

The model shares one 16-dimensional full-Unicode embedding table between target codepoints and text-style prompt codepoints. Latest CPU preflight measured:

- 20,115,074 parameters.
- FP32 model weights: 80,460,296 bytes.
- Estimated weights + gradients + Adam state: 321,841,184 bytes (about 307 MiB).

This estimate excludes activations, batches, temporary workspaces, runtime allocations, and the operating system. Actual memory use depends on the local hardware and batch size.

The trainer learns only the **image-reference raster route**: target Unicode cluster + four same-font reference glyph images → target contextual raster. It uses pixel L1 loss plus an edge loss, evaluates on family-held-out validation and test splits, and saves model and optimizer state for resume.

It does not train the text-style route, because the corpus does not yet contain reviewed semantic style prompts. It does not convert raster predictions into TTF/OTF files. Vectorization, contour cleanup, font tables, naming, shaping and final font QA are separate stages. It does not replace HarfBuzz for arbitrary text shaping.

## License conditions

The exact 52 Google Fonts source files are conditionally approved for this training pipeline only if generated font software based on them is released under SIL OFL 1.1, copyright notices and acknowledgements are preserved, and recorded Reserved Font Names are not reused without written permission.

**OFL is not a NonCommercial license:** downstream commercial use is not prohibited by OFL. The project itself can distribute its outputs for free, but that does not prevent downstream commercial use. The model-weight license is separate and must be decided independently. Arabeyes GPL+Font Exception fonts are not included in the active rights manifest.

## Current status

- Data, rights and image integrity: automated and verified.
- Combined one-download data artifact: built and independently inspected.
- Model smoke and training-pipeline tests: 16/16 passed in dedicated CPU CI.
- Main repository CI: 80 tests; 64 passed and 16 optional PyTorch tests skipped in that job.
- Real-data no-training preflight: passed.
- User's actual Windows hardware preflight: still required.
- Full dataset training, tiny-subset overfit, convergence and held-out-family quality: not yet demonstrated.
- Production TTF/OTF font generation: not ready.

No model training has been started.
