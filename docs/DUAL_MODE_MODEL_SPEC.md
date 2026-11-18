# Unified Dual-Mode Model Specification

## 1. Required product behavior

One model must support two independent entry routes and one optional combined route:

- **Reference-image route:** one reference image is accepted as the minimum input; additional references are optional and should improve confidence. The encoder estimates a style representation from visible evidence and learned priors.
- **Text-prompt route:** a natural-language description, preferably Arabic or English, controls the style without requiring a reference image.
- **Hybrid route:** image and text jointly condition the same style representation when both are supplied.

All routes must converge on one shared style representation and one Arabic-aware generator. Do not build two unrelated generators or treat the prompt route as a separate product.

## 2. Conditioning contract

`style_condition` is a structured object containing:

- a continuous shared style embedding;
- normalized categorical style attributes;
- measured or predicted geometric parameters;
- confidence/uncertainty per attribute;
- provenance describing which input routes contributed.

The shared generator receives `content_condition` (Arabic character/glyph identity and contextual structural data) plus `style_condition`. Text shaping remains a separate, deterministic subsystem; the generator must not guess Unicode order or replace HarfBuzz.

## 3. Encoders

### Image style encoder

Start with the verified MX-Font style pathway as a baseline for few-shot glyph appearance. Preserve an unmodified upstream baseline and record its exact commit and license. The reference encoder must accept K reference images, including K=1, with masks/metadata for missing or low-quality references. Do not claim the upstream model already solves Arabic shaping, vector generation, or prompt conditioning.

### Prompt style encoder

Use a pretrained Arabic-capable text encoder as the starting point; do not train a large language model from scratch for this project. Add a small projection head that maps its pooled representation into the shared style space. The encoder must process both free-form text and the structured attributes in `configs/style_attributes.yaml`.

Train the prompt route from paired descriptions and style targets. Synthetic descriptions generated from known parameter settings are useful, but must be marked synthetic and balanced. Human-reviewed descriptions should be included where available. Avoid training only on vague captions such as "beautiful Arabic font".

### Geometry encoder/decoder

Use explicit geometric targets where available: normalized advance width, outline bounds, stroke-width profile, curvature statistics, terminal angle, component topology, counter/negative-space ratio, baseline, and joining behavior. Keep per-glyph measurements separate from global style properties. A single global scalar cannot represent all glyph geometry.

## 4. Shared latent alignment

The image and prompt encoders must map paired samples to compatible representations. Candidate objectives:

- supervised attribute prediction from each route;
- regression to measured geometric targets;
- paired image-text contrastive/alignment loss;
- consistency loss when both routes are supplied;
- generator reconstruction losses for the target glyph.

Begin with each route independently, then align them, then jointly fine-tune. Do not add every loss at once. Log each loss separately and run ablations.

## 5. Shared Arabic-aware generator

The generator receives content identity/structure and the shared style condition. It should generate glyph images first. Vector reconstruction and OpenType compilation are later, separately validated stages. Include Arabic joining class, contextual form only when valid, dots, marks, ligatures, and language/script tags as structural inputs. Keep unsupported or uncertain cases explicit.

## 6. Training curriculum

1. Audit and normalize licensed sources and font-family splits.
2. Build Arabic glyph/style examples and trustworthy geometry labels.
3. Train or adapt the content/geometry representation and image-conditioned baseline.
4. Train the prompt projection against structured attributes and measured geometry.
5. Train paired image-prompt alignment.
6. Jointly fine-tune the shared generator with image, prompt, and optional hybrid batches.
7. Evaluate both routes on held-out families and unseen word/glyph combinations.
8. Only after raster generation passes, build vector reconstruction and TTF/OTF compilation as a separate milestone.

## 7. Evaluation matrix

Evaluate reference K=1, K=2, K=4, K=8; prompt-only; and hybrid separately. For each route measure style compliance, Arabic identity, dots/marks, geometry, unseen-glyph generalization, confidence calibration, and failure rate. Cross-route evaluation must compare an image and its paired description. Report results by held-out font family and style category.

## 8. Limitations that must be reported

- One reference image is underdetermined: unseen letters are inferred, not recovered uniquely.
- A prompt may be ambiguous; the model should expose uncertain attributes.
- A font corpus alone does not provide natural-language supervision. Paired and measured labels are required.
- Raster quality does not prove vector/font quality.
- A model that memorizes or retrieves training glyphs has not demonstrated generalization.
