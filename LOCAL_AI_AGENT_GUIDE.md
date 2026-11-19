# Handoff guide for the local AI training agent

## Mission
Prepare this repository into a reproducible unified Arabic font-generation system. The local AI agent runs on the user's Windows computer, inspects its resources, implements missing code, audits data, and tests every path. It must stop after producing the readiness report; the user will separately authorize training.

**Current state is preparation, not a trained model.** The repository has a published 20-family font corpus and a 7,904-image raster dataset release. No Arabic-trained checkpoint is included.

## First actions
1. Read README.md, docs/PRETRAINING_COMPLETION_PLAN.md, docs/AI_AGENT_EXECUTION_SPEC.md, docs/DUAL_MODE_MODEL_SPEC.md, docs/PROMPT_AND_GEOMETRY_DATASET.md, docs/MODEL_ARCHITECTURE.md, docs/TRAINING_EVALUATION.md, docs/DATA_SPECIFICATION.md, and docs/ARABIC_GLYPH_DATASET.md.
2. Run START_LOCAL_TRAINING.bat (or python scripts/preflight_local_training.py).
3. Read reports/local/machine_preflight.json for OS, Python, CPU, RAM, detected PyTorch/CUDA GPU details, dataset status, and blockers.
4. Do not start training while training_allowed is false. Do not guess the GPU or silently install CPU-only PyTorch.

## Required work before training

### 1. Inspect upstream MX-Font
- Use the official implementation linked in docs/MODEL_ARCHITECTURE.md, pinned at `9d2b6ace3e23199e2a896de329d4c16489b09a96` as recorded in `docs/UPSTREAM_BASELINE.md`.
- Audit the complete MX-Font import/dependency closure. The upstream README explicitly excludes `FUNIT/` and `base/modules/modules.py` from its top-level MIT statement; do not copy either under the assumption that it is MIT.
- Reproduce the documented baseline in a supported environment. The upstream `train_MX.py` uses CUDA-specific APIs and NCCL; prove the exact Windows/device path works or implement and test a documented adaptation before proceeding.
- Preserve an untouched upstream baseline path. Do not claim this repository merged two pretrained models.
- Confirm upstream data format, training command, checkpoint format, and evaluation protocol from source code. Do not invent APIs or flags.

### 2. Make the dataset model-ready
The current release contains full-line contextual renders with logical target indices. It is not a set of isolated glyph crops. Build a deterministic converter that:
- uses target index and RAQM/HarfBuzz logical-to-visual mapping correctly; never guess visual position by reversing Arabic strings;
- produces target-glyph crops with padding and consistent normalization;
- records crop coordinates, code point, context, font hash/family, renderer, and source image;
- keeps family-level train/validation/test separation unchanged;
- handles unsupported glyphs, combining marks, ligatures, and non-joining letters explicitly;
- writes an audit with previews and rejects malformed or blank crops.

Do not treat four context labels as proof that every letter has four valid joining forms. Use Unicode joining properties and actual shaping results.

### 3. Convert isolated crops and implement native MX-Font data adapter
- Run `scripts/build_isolated_glyph_crops.py` and inspect `data/glyph_crops/crop_summary.json` plus contact sheets created for review. These are isolated single-codepoint crops only, not contextual word crops.
- Run `scripts/build_mxfont_episodes.py`; verify target exclusion, family split inheritance, and exact font-file grouping.
- Treat these episodes as an intermediate project format. Implement and test a separate adapter to the pinned upstream MX-Font native loader only after confirming its required fields.
- MX-Font's weak component supervision requires decomposition/primals labels. Do not invent Arabic decomposition labels. Research, define, and manually audit a defensible Arabic component ontology or stop and report that the upstream objective cannot be reproduced as-is.

### 4. Implement episodes and training
- Implement style-reference/target episodes matching the upstream MX-Font protocol.
- Target glyph pixels are supervision only and must never appear among that episode's style references.
- Establish a baseline before adding Arabic-specific branches.
- Add Arabic context/topology branches as separate ablations only after baseline works.
- Save config, seed, family split, upstream commit, dataset hashes, environment, metrics, and checkpoints.
- Add resume-from-checkpoint and graceful interruption.
- Add a small CPU/GPU smoke-test mode that verifies loss, checkpoint saving, and reload.

### 5. Hardware-aware safety
Use the preflight report to choose device and conservative batch size. For NVIDIA, verify PyTorch CUDA availability and wheel/runtime compatibility. For AMD/Intel, verify exact backend support on this Windows installation; do not assume CUDA or ROCm support. If no supported accelerator exists, offer only a small CPU smoke test and explain expected slowness.

Never launch a long run automatically. Show device, VRAM/RAM estimate, batch size, image size, disk estimate, and expected runtime, then ask the user for explicit approval.

### 6. Validation gates
- Unit-test data indexing, crops, episode leakage, and checkpoint round-trip.
- Verify train/validation/test family IDs are disjoint.
- Overfit a tiny fixed subset as a pipeline sanity check.
- Run a short smoke test and inspect generated samples.
- Report limitations and failures honestly.

### 7. Implement the prompt and shared-style route (mandatory)
- Implement an Arabic-capable pretrained text encoder plus a trainable projection head; do not train a large language model from scratch.
- Consume `configs/style_attributes.yaml` and the style-description manifest schema. Preserve Arabic and English descriptions, normalized attributes, confidence, measured geometry, and source provenance.
- Build prompt-to-style and image-to-style encoders that produce compatible vectors in one shared style/geometry latent space.
- Use one shared Arabic-aware generator for reference-image, prompt-only, and hybrid modes. Do not create disconnected generators.
- Train attribute and geometric supervision separately from image reconstruction. Add paired image/prompt alignment only when reliable paired labels exist.
- Include controlled counterfactual prompt pairs to test that changing one attribute changes the intended output without damaging unrelated attributes.
- Test all three modes with forward/backward smoke tests and checkpoint round-trip before any long run.

### 8. Finish readiness, then stop
- Follow every work package and hard acceptance gate in `docs/PRETRAINING_COMPLETION_PLAN.md`.
- Create the required JSON and Markdown readiness reports using `schemas/pretraining_readiness.schema.json`, with evidence, not assumptions.
- If any gate is FAIL or UNKNOWN, set `training_allowed` to false and list the blocker.
- Even if every gate passes, do not start the full training run. Present the report, resource estimate, and proposed run schedule and wait for explicit user approval.

## Required outputs
Pinned upstream metadata/license; platform-specific environment files; dataset conversion/audit scripts; model adapter and episode sampler; prompt encoder and shared latent/generator paths; route-specific train/evaluate/sample commands; Windows preflight; tests; readiness reports; and a proposed run plan. Do not create a trained checkpoint in this preparation phase.

## Truthfulness and safety
- Never say training completed unless a real checkpoint and evaluation report exist.
- A generated raster image is not a valid TTF/OTF font.
- Never tune on test families.
- Never upload private user fonts, checkpoints, or machine reports to a public repository without explicit permission.
- Do not overwrite or delete existing user data or checkpoints.


## Arabic character-system v2 handoff

Before training, complete the following on the local machine using only fonts whose exact files have documented permission for ML training:

1. Generate/refresh the complete Unicode 17 Arabic-script registry:
   `python scripts/import_unicode_arabic_registry.py --download`
2. For at least three distinct cleared font families, run:
   `python scripts/run_shaping_regression.py --font "PATH_TO_FONT.otf" --output "reports/local/SHAPING_FONT_NAME.json"`
   Preserve each font SHA-256 and HarfBuzz version. Review dual/right joining, transparent marks, lam-alef clusters, ZWJ/ZWNJ, tatweel, and mark attachment. Do not claim a universal glyph form from one font.
3. Build a stratified glyph-instance pilot from those fonts. Keep all derivatives of each font family in the same split. Each glyph image must record the exact render hash, font hash, glyph ID, cluster/context, shaper version, script, language, direction, and feature set.
4. Have two annotators independently label the exact same images using `schemas/glyph_visual_annotation.schema.json`. Do not share their labels before the independent pass is complete. Keep uncertainty explicit.
5. Compare the two JSONL files:
   `python scripts/compare_glyph_annotations.py --annotator-a data/annotations/annotator_a.jsonl --annotator-b data/annotations/annotator_b.jsonl --output reports/local/annotation_agreement.json`
   Review per-kind precision/recall/F1 and mean polygon IoU; adjudicate disagreements. Raster IoU is approximate and is not a correctness score.
6. Update readiness evidence only after artifacts exist and are inspected. The registry and comparison-tool CI tests passing do not mean fonts were shaped or human annotations were completed.

Do not upload raw font files, private renderings, annotator identity information, or local machine reports to the public repository without explicit user permission. Do not start training while any rights, data, model, hardware, or evaluation gate is blocked.


## Font rights manifest and batch shaping handoff

Before running HarfBuzz against any local font, create `data/manifests/font_rights.json` from `data/manifests/font_rights.template.json`. Record the exact file SHA-256, family ID, authoritative license URL/name, explicit `ml_training_allowed: true`, `review_status: approved`, reviewer/date, and evidence references for every file. Do not infer permission from downloadability or a family-level label.

Run:
```powershell
python scripts/validate_font_rights_manifest.py --manifest data/manifests/font_rights.json --font-root "D:\ArabicFonts"
python scripts/run_batch_shaping_regression.py --manifest data/manifests/font_rights.json --font-root "D:\ArabicFonts" --output-dir reports/local/shaping
```
The second command checks every file hash and rights record before shaping any font. It creates one report per approved file and a batch summary. Keep local font files and reports private unless publication is explicitly authorized. A successful technical gate is not legal advice or visual-quality approval.
