# Intermediate Arabic Glyph Crop and Episode Adapter

This adapter creates a **safe, explicitly limited intermediate dataset** from the published contextual-render corpus.

## Step 1 — isolated crops

```bash
python -m pip install -r requirements-glyph-dataset.txt
python scripts/build_isolated_glyph_crops.py --samples data/training_samples/samples.jsonl --font-root data/raw_fonts --output data/glyph_crops
```

The script selects one existing isolated-context record per font/codepoint, then re-renders that one Unicode codepoint directly from the matching local font with Pillow-RAQM. It creates a centered 128×128 grayscale crop, verifies the font SHA-256, and records provenance. It does **not** attempt to crop a glyph out of a connected Arabic word image because that requires trustworthy HarfBuzz cluster-to-outline/pixel mapping.

## Step 2 — few-shot episodes

```bash
python scripts/build_mxfont_episodes.py --crops data/glyph_crops/glyph_crops.jsonl --output data/episodes --references 4 --episodes-per-font 64
```

Every episode selects one target and four distinct style-reference codepoints from the same exact font file. The target codepoint is excluded from references. Family split labels are inherited; no split is recomputed.

## Step 3 — tests

```bash
python -m unittest discover -s tests -v
```

## Critical limitations — not yet MX-Font-ready

- These crops are isolated single-codepoint examples. They do not supervise initial/medial/final joining, ligatures, or combining marks.
- The sampler is a project-side episode format, **not** the official MX-Font native dataset loader.
- The official MX-Font training method uses weak component supervision and a decomposition/primals vocabulary. This repository does not yet contain audited Arabic decomposition labels for that purpose.
- Asset-level permission for ML training must be confirmed for every font. A technically valid font is not automatically legally cleared for training.
- No MX-Font model code is vendored here; upstream license exceptions and its CUDA/NCCL training assumptions still need resolution.

Therefore this adapter is a reproducible data-preparation milestone, not authorization to start MX-Font training. The readiness report must remain blocked until native-loader compatibility, Arabic component supervision, rights, and tests are established.
