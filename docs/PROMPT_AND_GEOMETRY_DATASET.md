# Prompt and Geometry Dataset Construction

## Purpose

The prompt route needs more than font names or generic captions. Every usable training example should connect a human-readable style description to measured style/geometry attributes and to one or more licensed visual/vector samples. The same style identifier links the image and prompt routes into shared supervision.

## Required record relationship

For each `style_id`, keep linked records for:

1. Source font or artwork asset and its asset-level rights record.
2. Reference image(s) rendered with a pinned renderer.
3. Per-glyph vector/raster geometry measurements.
4. Structured attributes from `configs/style_attributes.yaml`.
5. One or more Arabic descriptions and, when available, English equivalents.
6. Description provenance: `human_reviewed`, `synthetic_from_parameters`, or `machine_generated_unreviewed`.
7. Family-level split identifier shared by every sample from the same normalized font family.

## Description generation

- Start with controlled attribute phrases, not unconstrained generic captions.
- Create several paraphrases per style while preserving the same attribute values.
- Create counterfactual pairs that change one attribute at a time (e.g. bold vs regular, sharp vs rounded terminals) while keeping other attributes fixed.
- Include Arabic and English phrasing where reliable.
- Mark every synthetic description as synthetic and store the generator/template version.
- Human-review a representative sample and all ambiguous/contradictory descriptions.
- Never infer hidden attributes from a single glyph when the evidence is insufficient; use `unknown` and confidence values.

## Geometry extraction

Extract measurements per glyph wherever possible. Suggested fields:

- advance width and outline bounds in font units;
- stroke-width profile or robust estimate;
- curvature distribution and tangent continuity;
- terminal angles and tapering;
- contour/component counts and connectivity;
- counter/negative-space ratio;
- baseline offset and side bearings;
- dots, marks, and their relative positions;
- joining behavior and ligature/shaping metadata.

The current `scripts/extract_font_geometry.py` is an initial utility. It does not yet fully resolve SVG transforms, compound path fill rules, variable-font instances, or Arabic shaping. The agent must add tests and correct those limitations before treating its output as trusted labels.

## Split and leakage controls

- Split by normalized font family, never by individual glyph or description row.
- Keep all weights/instances and paraphrases from one family in the same split.
- Do not place near-duplicate font files or derived artwork from the same source family across splits.
- Use validation for prompt wording/model selection; reserve test families for final reporting.
- Keep a separate challenge set of controlled attribute combinations not seen together during training.

## Minimum prompt-route tests

1. Same style, different paraphrases -> similar style embedding and stable generated output.
2. One attribute changed -> the corresponding measurable geometry changes in the expected direction.
3. Contradictory description -> uncertainty or conflict warning, not arbitrary silent resolution.
4. Arabic and English equivalent descriptions -> comparable outputs within measured tolerance.
5. Unseen attribute combinations -> report generalization separately from seen combinations.
6. Prompt-only, image-only, and hybrid modes -> same shared generator and compatible style representation.

## Data quality rule

A font file is not automatically a paired prompt dataset. If a style has no reliable description or geometric measurements, it may still contribute to image-only training but must not be counted as paired prompt supervision. Never fabricate a pairing merely to increase dataset size.
