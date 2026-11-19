# Contextual few-shot Arabic style episodes

## Data pairing

`scripts/build_contextual_style_episodes.py` pairs each HarfBuzz-shaped contextual cluster target with four isolated glyph reference images from the **same exact font file**.

Inputs:
- `contextual_clusters.jsonl` and its image root: target cluster raster, logical Unicode text, HarfBuzz glyph IDs, source font hash, family and split.
- `glyph_crops.jsonl` and its image root: isolated one-codepoint style references from the same font hash.

The builder:
1. Groups isolated references by exact font SHA-256, family and split.
2. Excludes every Unicode codepoint present in the target cluster from the style-reference pool.
3. Samples four distinct reference codepoints deterministically from the same font.
4. Preserves family-level train/validation/test splits.
5. Writes separate train/validation/test JSONL files and a summary.

The generated episodes can be used by `scripts/train_multimodal_glyph.py` with the contextual target image root and isolated reference image root supplied separately.

## Current verified result

The source artifacts used in the latest successful data run contain:
- 1,732 contextual target clusters;
- 1,872 isolated single-codepoint reference crops;
- 52 exact font files across 20 families;
- 1,732 contextual episodes can be formed with four same-font references each;
- 238 targets contain more than one Unicode codepoint;
- split counts inherit the existing family-safe partition: train 1,134, validation 299, test 299.

The latest workflow-run artifact is produced by `.github/workflows/build-contextual-style-episodes.yml` after a successful data-pipeline run. Artifact name: `arabic-contextual-style-episodes`.

## Leakage rules

- A target cluster's codepoints cannot appear among its style-reference codepoints.
- A reference must match the target's exact font SHA-256, family and split.
- A family may belong to only one of train, validation or test.
- The training script independently rechecks the rights manifest, source hashes, split isolation and target/reference leakage before it loads data.

## Scope

These episodes provide image-style supervision for the contextual cluster generator. They do not provide reviewed natural-language style prompts, semantic component labels, or proof that a predicted cluster is linguistically or artistically correct. HarfBuzz remains the deterministic text-shaping system for arbitrary text; the generator learns the appearance of recorded shaped clusters.
