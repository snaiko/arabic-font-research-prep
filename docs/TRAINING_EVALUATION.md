# Training and Evaluation Plan

## 1. Reproducibility record

Every run must save:
- git commit and upstream MX-Font commit,
- checkpoint source/license/hash,
- dataset manifest version and font-family split,
- renderer and shaping-engine versions,
- config, seed, device, dependency lockfile,
- training curves and per-family/per-character metrics.

## 2. Episode construction

For each episode, choose one target font family/style. Sample K reference glyphs from that same target style and a different target character as the prediction target. Use content glyphs from a neutral, licensed anchor font or a separately defined content source. Ensure the target glyph image from the target font is used only as supervision, never as an input reference.

Evaluate several K values (for example 1, 2, 4, 8) and several reference-selection policies. Include references that are structurally diverse rather than always the same four letters.

## 3. Baselines

- B0: upstream MX-Font checkpoint without Arabic fine-tuning.
- B1: fine-tuned MX-Font.
- B2: simple single-style-encoder baseline, if implemented.
- B3: proposed Arabic-context branch.
- B4: proposed topology/detail branch.
- B5: full gated model.

Do not claim improvement unless the same held-out families, episodes, and rendering settings show it.

## 4. Metrics

### Raster appearance
- L1/Charbonnier, SSIM, and edge distance.
- Per-character and per-family breakdown.
- Stroke width and baseline/advance consistency.

### Arabic structure
- Character identity and component count.
- Dot count and dot placement.
- Counter/hole preservation.
- Connectivity and stroke continuity.
- Contextual-form correctness and joining continuity.
- Mark/hamza placement.

### Font output
- Outline validity and self-intersection checks.
- TTF/OTF table validation.
- HarfBuzz shaping tests for isolated, initial, medial, final, ligature, and mark cases.
- Rendering comparisons across at least two independent rasterization paths.

### Uncertainty
- Calibration error, risk-coverage curve, and error by reference count.
- Flag unsupported characters or low-confidence predictions instead of silently emitting a glyph.

## 5. Acceptance gates

1. Dataset gate: licenses, hashes, family splits, and renderer metadata pass.
2. Baseline gate: reproduce a stable MX-Font baseline.
3. Arabic gate: contextual forms and joining tests pass independently of visual-style metrics.
4. Vector gate: raster-to-outline output passes geometry and font checks.
5. Release gate: held-out-family results and known limitations are published.

## 6. Do not do

- Do not mix checkpoints by averaging weights without a validated method.
- Do not call an image-generation result a working font.
- Do not report training as complete when only configs or manifests exist.
- Do not tune on the test families.
