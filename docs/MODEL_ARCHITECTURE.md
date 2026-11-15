# Proposed Arabic Few-Shot Font Architecture

## 1. Task definition

Input: a target character/content glyph plus a small set of style-reference glyph images from one user-selected typeface.

Output: a raster glyph prediction for the target character in the reference style, followed—only after validation—by an optional vector outline and a usable OpenType font.

The model estimates a style-conditioned appearance. It does not infer a uniquely correct hidden font from one glyph. Return confidence/uncertainty and allow more references to improve the estimate.

## 2. Architecture: staged hybrid, not blind checkpoint merging

### Stage A — MX-Font baseline

Use the official MX-Font implementation as the first image-generation baseline:

- Content encoder represents the target glyph structure.
- Multi-head style encoder / localized experts capture different local style cues.
- Generator combines content and style features to predict a glyph image.
- Preserve the upstream checkpoint and implementation unchanged for reproducible baseline runs.

MX-Font's localized experts are already part of the original method. Do not describe the proposed system as a merger of two pretrained models. The Arabic modules below are new task-specific branches that must be trained and ablated.

### Stage B — Arabic context and joining branch

Inputs include the Unicode code point, script/language tag, joining properties, neighboring joining state, and requested contextual form. This branch supplies structural context to the generator; it does not replace HarfBuzz or OpenType shaping.

Represent forms as `isol`, `init`, `medi`, and `fina` only where the character and context support them. Do not fabricate four forms for every Arabic-script character. Right-joining letters, non-joining characters, combining marks, and extended-script letters have different behavior.

### Stage C — topology and detail refinement

A lightweight refinement head predicts features useful for preserving:

- connected-component count and connectivity,
- stroke continuity and endpoint placement,
- dot count, dot grouping, and dot-to-body relationships,
- counters/holes and their topology,
- hamza and other diacritic placement,
- baseline, advance width, and side bearings.

Use topology-aware losses only when reliable labels or robust derived targets exist. Otherwise begin with image/edge losses and report the limitation.

### Stage D — confidence-aware fusion

A learned gate combines the baseline generator output with the Arabic-context and refinement features. The gate must be trained and evaluated; do not assume that adding branches improves quality.

For each target, retain:
- prediction,
- confidence or calibrated uncertainty,
- reference glyph IDs used,
- model/checkpoint version,
- preprocessing/rendering configuration.

### Stage E — vector and font production (separate subsystem)

Raster prediction is not a font. Convert selected glyphs to vector outlines using a separately tested contour-reconstruction process, then construct tables with FontTools and shape text with HarfBuzz. Validate outlines and OpenType tables before exporting TTF/OTF. Preserve manual editing as an option; automatic vectorization may alter topology.

## 3. Data flow

1. Validate source font license and metadata.
2. Render reference and target glyphs with a pinned renderer.
3. Create episodes: style references and a held-out target from the same family/style.
4. Encode target content and reference style.
5. Predict raster glyph with MX-Font.
6. Add Arabic context and topology refinements in later ablations.
7. Estimate uncertainty and reject unsupported cases.
8. Optionally vectorize and compile; run shaping and font validation.

## 4. Training sequence and ablations

| Experiment | Trainable parts | Purpose |
|---|---|---|
| B0 | None; published checkpoint | Reproduce upstream baseline |
| B1 | MX-Font fine-tuning | Test domain adaptation on Arabic |
| B2 | Arabic context branch + gate | Test contextual information |
| B3 | Topology/detail head + gate | Test structural preservation |
| B4 | Full staged system | Test combined contribution |

Compare each experiment on identical held-out font families and identical episodes. Keep a frozen baseline checkpoint and save every config, seed, and split manifest.

## 5. Loss design

Start conservatively:

- `L_pixel`: L1 or Charbonnier reconstruction loss.
- `L_edge`: edge-map consistency for stroke boundaries.
- `L_structure`: structural similarity or feature consistency.
- `L_context`: classification/consistency loss for valid contextual-form labels, only where labels are valid.
- `L_topology`: connectivity, component, dot, and counter constraints where trustworthy annotations exist.
- `L_uncertainty`: calibration objective on prediction error/coverage.

A possible objective is:

`L = λp L_pixel + λe L_edge + λs L_structure + λc L_context + λt L_topology + λu L_uncertainty`

Do not enable every term from the first run. Add terms one at a time and report ablations.

## 6. Critical constraints

- Keep text shaping outside the image generator.
- Do not map Arabic presentation-form code points as a substitute for Unicode joining logic.
- Do not use the target font's held-out glyph image as a style reference in the same episode.
- Split by font family, not by image or glyph, to prevent leakage.
- A generated glyph must not be accepted solely because it looks plausible; check identity, joins, dots, and font validity.
