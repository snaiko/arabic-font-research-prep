# Arabic Font Style Description Schema

## Purpose

This schema connects human-readable style descriptions to measurable geometry and to the shared style representation used by both conditioning routes:

- **Prompt route:** structured text description -> prompt encoder -> shared style/geometry representation.
- **Reference route:** one or more reference images -> image encoder -> the same shared representation.
- **Hybrid route:** both inputs condition the same generator.

The schema is a training contract, not a claim that a single image uniquely determines an entire typeface. Missing glyph details must be inferred from learned Arabic structure and style priors, and uncertain predictions should remain measurable.

## Record structure

Each JSONL record represents one font/style sample and should include:

- `style_id`: stable identifier for the style, not a person's identity.
- `language_script`: normally `Arab`.
- `source`: provenance, source URL, license identifier, and permission status.
- `description`: concise natural-language description, preferably Arabic and optionally English.
- `attributes`: normalized categorical or numeric style attributes from `configs/style_attributes.yaml`.
- `geometry`: measurable properties extracted from vector outlines or glyphs, with units and extraction method.
- `glyphs`: glyph identifiers and availability; do not assume Unicode codepoints alone describe shaping behavior.
- `assets`: paths to licensed reference images, SVG outlines, or font files. Keep large binaries outside Git when appropriate and reference immutable dataset locations/checksums.
- `splits`: grouping key to prevent glyphs from the same font leaking across train/validation/test.

## Attribute rules

1. Use controlled values from the YAML configuration wherever possible.
2. Use `unknown` rather than guessing an attribute from an inadequate image.
3. Store continuous measurements as numbers with explicit units or normalized ranges.
4. Separate visual description from measured geometry. A label such as `bold` is not a substitute for measured stroke width.
5. Preserve uncertainty using `confidence` in the range 0..1 and record the measurement method.
6. Generate synthetic descriptions from known geometry parameters as additional supervision, but keep them marked as synthetic.

## Geometry targets

Useful targets include normalized glyph advance width, outline bounds, stroke-width estimates, curvature distribution, terminal angle, counter/negative-space ratio, connected-component count, baseline alignment, and inter-glyph joining behavior. These measurements are glyph- and context-dependent; store per-glyph values when possible rather than collapsing an entire font into one number.

## Arabic-specific requirements

- Model joining behavior and contextual forms (isolated, initial, medial, final) explicitly.
- Preserve dots, hamza, marks, ligatures, and mark positioning as separate structural concerns.
- Distinguish glyph identity from Unicode text and shaping output.
- Validate generated fonts with a shaping engine such as HarfBuzz and test representative Arabic words, not only isolated glyph images.

## Training stages

1. Parse licensed fonts/SVGs and build reliable glyph geometry targets.
2. Train Arabic structure and geometry representations alongside a pretrained Arabic-capable text encoder; do not train a large language model from scratch for this task.
3. Train the prompt encoder to map descriptions and attributes to the shared style representation.
4. Train the image encoder to map reference images to that same representation.
5. Align both encoders and fine-tune the shared Arabic-aware generator.
6. Evaluate on held-out fonts, styles, glyphs, and words. Split by source font/style family to avoid leakage.

## Minimum evaluation

- Attribute prediction accuracy and calibration.
- Geometry error for widths, bounds, curvature, and negative-space measures.
- Arabic shaping and joining correctness.
- Visual consistency across glyphs and across unseen words.
- Prompt/reference cross-route consistency for paired samples.
- Font compilation and rendering validity (TTF/OTF), including HarfBuzz shaping tests.
- Generalization to held-out style families and combinations of attributes.

## Data rights

Only ingest assets whose license or explicit permission allows the intended use, including machine-learning training and any redistribution. Record the exact asset-level license and provenance. A repository's code license does not automatically license its datasets, fonts, or third-party assets.