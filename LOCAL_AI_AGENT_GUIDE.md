# Handoff guide for the local AI training agent

## Mission
Continue this repository into a reproducible Arabic few-shot font-generation research system. The local AI agent runs on the user's Windows computer, inspects its resources, implements missing code, tests it, and only then launches training.

**Current state is preparation, not a trained model.** The repository has a published 20-family font corpus and a 7,904-image raster dataset release. No Arabic-trained checkpoint is included.

## First actions
1. Read README.md, docs/MODEL_ARCHITECTURE.md, docs/TRAINING_EVALUATION.md, and docs/ARABIC_GLYPH_DATASET.md.
2. Run START_LOCAL_TRAINING.bat (or python scripts/preflight_local_training.py).
3. Read reports/local/machine_preflight.json for OS, Python, CPU, RAM, detected PyTorch/CUDA GPU details, dataset status, and blockers.
4. Do not start training while training_allowed is false. Do not guess the GPU or silently install CPU-only PyTorch.

## Required work before training

### 1. Inspect upstream MX-Font
- Use the official implementation linked in docs/MODEL_ARCHITECTURE.md.
- Pin an exact upstream commit and record its license and commit hash.
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

### 3. Implement episodes and training
- Implement style-reference/target episodes matching the upstream MX-Font protocol.
- Target glyph pixels are supervision only and must never appear among that episode's style references.
- Establish a baseline before adding Arabic-specific branches.
- Add Arabic context/topology branches as separate ablations only after baseline works.
- Save config, seed, family split, upstream commit, dataset hashes, environment, metrics, and checkpoints.
- Add resume-from-checkpoint and graceful interruption.
- Add a small CPU/GPU smoke-test mode that verifies loss, checkpoint saving, and reload.

### 4. Hardware-aware safety
Use the preflight report to choose device and conservative batch size. For NVIDIA, verify PyTorch CUDA availability and wheel/runtime compatibility. For AMD/Intel, verify exact backend support on this Windows installation; do not assume CUDA or ROCm support. If no supported accelerator exists, offer only a small CPU smoke test and explain expected slowness.

Never launch a long run automatically. Show device, VRAM/RAM estimate, batch size, image size, disk estimate, and expected runtime, then ask the user for explicit approval.

### 5. Validation gates
- Unit-test data indexing, crops, episode leakage, and checkpoint round-trip.
- Verify train/validation/test family IDs are disjoint.
- Overfit a tiny fixed subset as a pipeline sanity check.
- Run a short smoke test and inspect generated samples.
- Report limitations and failures honestly.

## Required outputs
Pinned upstream metadata/license; platform-specific environment files; dataset conversion/audit scripts; model adapter and episode sampler; train/evaluate/sample commands; Windows launcher with confirmation before long training; checkpoint, metrics, sample gallery, and run manifest.

## Truthfulness and safety
- Never say training completed unless a real checkpoint and evaluation report exist.
- A generated raster image is not a valid TTF/OTF font.
- Never tune on test families.
- Never upload private user fonts, checkpoints, or machine reports to a public repository without explicit permission.
- Do not overwrite or delete existing user data or checkpoints.
