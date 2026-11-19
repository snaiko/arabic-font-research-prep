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


## Image integrity

The episode builder also pins SHA-256 for each target raster and each of its four style-reference rasters. The local trainer recomputes and verifies those hashes immediately before loading the images. A modified or corrupted target/reference image therefore fails closed rather than silently entering training.


## Verified CI result and no-training preflight

GitHub Actions run [44529785828](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44529785828) completed the episode build and real-data preflight successfully. Artifact: [arabic-contextual-style-episodes](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44529785828/artifacts/14531943917).

Verified result:
- 1,732 episodes, zero skipped targets.
- Four same-font references per target.
- 1,134 train / 299 validation / 299 test.
- 20 families; no family split leakage.
- 238 multi-codepoint targets.
- SHA-256 pinned for every target raster and all four reference rasters per episode.
- The preflight loaded a real batch, verified all 52 approved font hashes, and produced a finite 128×128 forward output.

The preflight report explicitly records:
- `training_performed=false`
- `optimizer_created=false`
- `backward_pass_performed=false`
- `weights_updated=false`
- `checkpoint_created=false`

This proves the real data and image-reference forward path can be loaded together under the conditional OFL rights gate. It is not a training run and does not establish generation quality.


## Latest full-image integrity pass

The later run [44530432867](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44530432867) repeated the build with image hashes pinned and then iterated every split through the training dataset loader.

- Target images verified by SHA-256: **1,732 / 1,732**.
- Style-reference images verified by SHA-256: **6,928 / 6,928**.
- All 52 conditional OFL font hashes validated.
- One real batch passed the model's 128×128 forward path.
- No optimizer, backward pass, weight update, checkpoint, or training occurred.

Artifact: [arabic-contextual-style-episodes](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44530432867/artifacts/14533013474).
