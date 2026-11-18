# Unified Dual-Mode Arabic Font Intelligence

## Product objective

Build one Arabic font-design model with two input modes and one shared generative core:

1. Reference-image mode: receive one image (ideally one glyph or a short sample) and infer a reusable style representation, then generate the remaining glyphs and words in that style.
2. Text-prompt mode: receive a natural-language description of a desired style and generate a coherent Arabic typeface without a reference image.

These are not two separate products or unrelated models. Both modes must map into a shared style-and-geometry representation and use the same Arabic-aware generator and vector/font output pipeline.

## Proposed architecture

### A. Input encoders

- Image Style Encoder: extracts visual style cues from one or a few reference samples: stroke contrast, width, curvature, terminals, proportions, slant, texture, and ornament tendencies. Use few-shot conditioning / MX-Font-like ideas as a starting point, not as the complete system.
- Prompt Style Encoder: maps natural-language descriptions into the same style representation. It should understand attributes such as geometric/organic, angular/rounded, thin/bold, high/low contrast, compact/extended, ornamental/minimal, and controlled combinations.
- Arabic Structure Encoder: represents Unicode text, letter identity, joining classes, contextual forms, ligatures, dots, diacritics, and shaping constraints.

### B. Shared style-and-geometry latent space

Both the image encoder and prompt encoder should be trained to produce compatible representations. When an image and a description refer to the same or similar style, their embeddings should be aligned using paired supervision and contrastive/alignment objectives.

This shared representation should encode interpretable geometric attributes where possible, not only an opaque visual embedding:
- centerlines and Bézier/control points;
- curvature and tangent continuity;
- stroke-width profiles and tapering;
- terminals, joins, and component topology;
- glyph proportions and spacing;
- word silhouette, balance, and negative space;
- ornament and composition parameters.

### C. Shared Arabic-aware generator

A single conditional generator receives:
- Arabic text/character structure;
- shared style representation from either input route;
- geometric constraints and optional composition controls.

It generates a coherent glyph set, contextual forms, ligatures, and word-level compositions. The image-conditioned and prompt-conditioned modes must use the same decoder and geometry representation so improvements in one mode can benefit the other.

### D. Vector reconstruction and font compiler

Generate editable vector paths (SVG or an internal path representation), then build OpenType tables and TTF/OTF files. Validate with FontTools and HarfBuzz. Raster previews alone are not a finished font.

## Training curriculum

1. Pretrain Arabic structure and shaping representations using properly licensed fonts and Arabic text/shape data.
2. Train geometry representations using vector paths, pen trajectories, and procedurally generated curves and ornaments with documented provenance.
3. Train image-conditioned style inference using font/reference samples; randomly hold out glyphs and words so the model must infer unseen forms.
4. Train prompt-conditioned style inference using carefully written attribute descriptions paired with style examples and geometric parameter labels. Avoid relying only on vague captions.
5. Align image and text style encoders in the shared latent space using paired and synthetic descriptions.
6. Jointly fine-tune both routes through the same generator and vector decoder.
7. Evaluate both routes independently and jointly on unseen words, unseen glyph combinations, and unseen style combinations.

## Important data requirement for prompt mode

A collection of font files alone does not teach reliable natural-language control. Create a structured style-description dataset: each style/sample should have geometric labels and multiple human-readable descriptions. Some descriptions can be generated from known measured attributes, then reviewed. Include controlled counterfactual descriptions to test whether changing one attribute changes the output as expected.

## Important limitation of one-image inference

One reference image does not uniquely determine every glyph in a typeface. A single glyph may not reveal how the style handles all letter families, dots, joins, ligatures, or diacritics. The model must combine the observed evidence with learned Arabic typography priors, expose uncertainty, and allow optional extra references or user corrections. Do not claim exact recovery of the original font from one sample.

## Evaluation criteria

- Image route: style consistency with the reference and quality of unseen glyphs.
- Prompt route: compliance with described attributes and coherence across the full glyph set.
- Cross-route consistency: a prompt describing a reference style should produce a similar style embedding/output.
- Arabic correctness: readable letters, correct joining, ligatures, dots, and diacritics.
- Geometry: topology, curvature continuity, stroke width, spacing, balance, and negative space.
- Generalization: test words and glyph combinations absent from training; compare against nearest-neighbor copying baselines.
- Font validity: successful shaping and rendering in HarfBuzz and real applications.

## Product modes

- Reference mode: image -> infer style -> generate font.
- Prompt mode: description -> infer style -> generate font.
- Optional hybrid mode: image + description -> refine or disambiguate the inferred style.

The hybrid mode is optional, but useful when a single image leaves stylistic properties ambiguous.
