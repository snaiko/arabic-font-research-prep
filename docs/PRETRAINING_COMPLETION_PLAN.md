# Pretraining Completion Plan

## Objective

Prepare the repository and local Windows environment so a separate AI coding/training agent can complete implementation, data preparation, tests, and reproducibility work before any long training run. This plan does not authorize training by itself.

## Current known state

- Research architecture and data specifications exist.
- A Google Fonts collection/validation pipeline and raster dataset release workflow exist.
- A Windows preflight launcher exists.
- The current raster dataset contains contextual full-line renders with logical target indices; it is not yet a verified isolated-glyph episode dataset.
- An immutable MX-Font source pin is recorded. A project-side isolated single-codepoint crop builder and target-excluded few-shot episode sampler now exist, but they are an intermediate format only; the official native MX-Font adapter, Arabic component/decomposition supervision, and executable training integration are not implemented.
- The dual-mode image + text prompt model is specified conceptually, but its prompt encoder, shared-latent alignment, paired data, and tests must still be implemented by the local AI agent.
- The SVG/font geometry extractor is an initial metadata utility, not a complete vectorization or calligraphy understanding system.

## Work packages — complete in order

### WP0 — Repository and upstream audit

- Inspect all existing code, workflows, releases, data manifests, and local machine state before modifying anything.
- Pin the official upstream implementation to an immutable commit. Record repository URL, commit SHA, license, notices, and any excluded third-party modules.
- Reproduce upstream dependency installation and a tiny baseline inference/smoke test before adapting code.
- Keep upstream code and checkpoint provenance separate from project modifications. Do not average unrelated checkpoints or claim model merging without a validated method.

### WP1 — Data rights and provenance

- Audit every font and geometry asset individually for exact license, author, source URL, version/revision, and checksum.
- Record whether the rights holder/license permits the intended ML training, modification, and any planned redistribution. If ambiguous, quarantine the asset and seek permission; do not infer permission from a repository-level code license.
- Preserve license files and attribution notices in the dataset archive.
- Keep raw font files, private user fonts, checkpoints, and machine reports out of public Git unless explicitly authorized.
- Maintain separate manifests for fonts, Arabic trajectories, SVG calligraphy, geometric ornaments, and procedural synthetic data.

### WP2 — Dataset integrity and Arabic shaping

- Verify each font file checksum, cmap, core Arabic coverage, and shaping output.
- Pin and record Pillow/RAQM, FreeType, HarfBuzz, fontTools, and OS/runtime versions.
- Build samples from logical Unicode text through a shaping engine. Never reverse Arabic strings manually or infer visual order from string indices.
- Correctly map HarfBuzz glyph clusters/positions to source character spans. Handle ligatures and combining marks as multi-codepoint clusters.
- Build auditable target-glyph crops with source coordinates, padding, target cluster, codepoints, glyph ID, context, font hash, and renderer metadata.
- Reject blank, clipped, unsupported, ambiguous, or .notdef samples. Generate visual contact sheets and an audit report.
- Keep font families disjoint across train/validation/test. Check duplicates and near-duplicates across splits.
- Do not claim that the four context strings automatically produce four valid forms for every letter; derive joining properties and inspect actual shaped glyph output.

### WP2A — Isolated glyph crops and few-shot episodes

- Run `scripts/build_isolated_glyph_crops.py` to render each isolated Arabic codepoint directly from its source font with RAQM. Do not crop connected word images without a tested HarfBuzz cluster-to-pixel mapping.
- Run `scripts/build_mxfont_episodes.py` to create same-font episodes with target codepoints excluded from style references and family splits inherited unchanged.
- Treat this as an intermediate format. Implement a separate adapter to the pinned upstream MX-Font loader after inspecting its actual schema.
- MX-Font uses weak component supervision and decomposition/primals labels. Arabic decomposition labels must be linguistically and visually defensible and manually audited; do not synthesize arbitrary component labels to satisfy the loader.
- Isolated crops do not provide joining-form, ligature, or mark supervision.

### WP3 — Geometry and prompt supervision

- Extract glyph-level vector geometry from licensed TTF/OTF/SVG sources where technically reliable.
- Treat SVG transforms, units, fill rules, compound paths, and path parsing carefully; do not treat the first-pass extractor as ground truth without tests.
- Store global style attributes separately from per-glyph geometric measurements.
- Create multiple Arabic and English descriptions paired with measured style attributes. Mark synthetic, machine-generated, and human-reviewed descriptions distinctly.
- Add controlled counterfactual pairs (for example, same description except weight or terminal shape) to test whether the prompt route responds to the intended attribute.
- Preserve uncertainty when an image or source does not reveal an attribute.

### WP4 — Model implementation

- Implement an image style encoder based on a pinned MX-Font baseline, retaining the untouched baseline for comparison.
- Implement an Arabic-capable prompt text encoder using a pretrained model plus a trainable projection head; do not train a large language model from scratch.
- Implement a shared style/geometry latent contract and one shared Arabic-aware glyph generator.
- Add image-only, prompt-only, and hybrid conditioning paths.
- Implement paired alignment and attribute/geometry supervision as separate loss terms with configurable weights.
- Keep text shaping separate from glyph appearance generation. Implement vectorization/font compilation only as a separately gated stage.

### WP5 — Tests and reproducibility

- Unit tests: manifests, source hashes, Unicode/joining metadata, cluster-to-crop mapping, blank/clipped crop detection, split leakage, prompt parsing, and geometry extraction.
- Model tests: forward pass for image-only, prompt-only, and hybrid; shape checks; finite losses; gradient flow; checkpoint save/reload.
- Data tests: target glyph must not leak into style references in the same episode.
- Tiny-subset overfit test and short smoke test; inspect saved sample grids manually.
- Save config, seed, git SHA, upstream SHA, data manifest hashes, environment lock, device details, logs, metrics, and checkpoints.
- Support resume and graceful interruption. Do not overwrite previous runs.

### WP6 — Hardware and run plan

- Run the Windows preflight and verify actual GPU backend/device, VRAM, RAM, free disk, and package compatibility.
- Do not assume CUDA for AMD/Intel hardware. Verify the exact supported PyTorch backend on that machine.
- Produce a resource estimate and staged schedule: CPU data tests, device smoke test, tiny overfit, short experiment, then proposed full run.
- Full training must remain disabled until all acceptance gates pass and the user explicitly approves the proposed run.

## Hard acceptance gates before training

A readiness report must show PASS for all of the following:

1. Upstream source pinned and license/notice audit complete.
2. Data licenses and provenance audited for every included asset.
3. Family-level splits disjoint and data hashes verified.
4. Target crops and Arabic shaping mappings audited with sample contact sheets.
5. Prompt-description pairs and geometric targets exist with clear provenance.
6. Image, prompt, and hybrid model paths all pass forward/backward smoke tests.
7. Episode leakage tests pass.
8. Checkpoint save/reload and resume tests pass.
9. Evaluation scripts produce route-separated metrics on held-out families.
10. Hardware, storage, runtime estimate, and recovery plan are documented.

Any FAIL or UNKNOWN means `training_allowed: false`. The readiness report must name the blocker; it must not silently downgrade a gate.

## Final handoff artifact

Create `reports/pretraining_readiness.json` and a human-readable `reports/PRETRAINING_READINESS.md` containing gate status, evidence paths, dataset counts, split counts, licenses, upstream commit, tests, device, estimated resources, and unresolved risks. No training run is started by this plan.
