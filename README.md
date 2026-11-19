# Arabic Few-Shot Font Research

Research preparation for an Arabic font-generation system that learns a visual style from reference glyphs and predicts Arabic glyphs and shaped clusters.

> **Current status (2026-11-19):** The image-reference raster baseline now has a conditional OFL rights manifest, audited contextual episodes, a local training entry point, and a no-training data/model preflight. **No model training has been started.** Full project readiness remains BLOCKED pending the gates listed below.

## Verified preparation

- **Source rights:** 52 exact Google Fonts files across 20 families are conditionally approved for this training pipeline under SIL OFL 1.1. Generated font software based on these sources must remain OFL 1.1, preserve notices, and avoid recorded Reserved Font Names. See [OFL AI-training policy](docs/OFL_AI_TRAINING_POLICY.md). OFL is not a NonCommercial license; downstream commercial use is not prohibited by its terms.
- **Raster data:** 7,904 published samples from 52 font files and 20 families; family-safe split of 14 train / 3 validation / 3 test families; published corpus integrity audit passed.
- **Isolated crops:** 1,872 single-codepoint glyph crops.
- **Contextual targets:** 1,732 HarfBuzz-shaped cluster crops; 238 multi-codepoint clusters; independent glyph-ID mapping audit passed. Coverage is partial at 518/520 font-case pairs because two Aref Ruqaa tatweel cases do not render.
- **Few-shot episodes:** 1,732 episodes, each pairing a contextual target with four isolated reference glyphs from the same exact font; target codepoints are excluded from references; 1,134 train / 299 validation / 299 test episodes across 20 families.
- **Shaping regression:** 52 conditionally approved fonts × 10 cases = 520 HarfBuzz regression reports; CI passed.
- **Experimental model:** target Unicode content is now separate from image-style and text-style conditioning. Image, text and hybrid routes share one raster decoder. Six CPU PyTorch smoke tests passed; nine model/training-pipeline tests passed in the dedicated CPU workflow.
- **Arabeyes research:** 36 binaries downloaded and checksum-verified; all passed one shaping smoke phrase and rendered previews. They remain excluded from training because GPL+Font Exception does not expressly settle ML training or model/output distribution.

## Training handoff

See [Local Training Handoff](docs/LOCAL_TRAINING.md) for artifact paths, Windows command syntax, explicit step-count requirements, checkpoint resume, and license conditions.

The trainer `scripts/train_multimodal_glyph.py` uses the image-reference route only:
- target Unicode cluster + four same-font reference glyphs → 128×128 grayscale target raster;
- pixel L1 plus edge loss;
- family-held-out validation and test;
- per-font rights and data-leakage checks before loading.

A separate workflow builds [contextual few-shot episodes](docs/CONTEXTUAL_EPISODE_DATASET.md) and runs a no-training real-data preflight. This preflight must report that no optimizer/backward/checkpoint operation occurred.

## Remaining blockers

Overall readiness is still **BLOCKED**:
1. Expert visual, spelling, readability and calligraphic validation is not complete. Machine geometry and HarfBuzz mapping are not a substitute for human ground truth.
2. Two contextual tatweel font-case pairs remain absent.
3. The pinned upstream MX-Font dependency closure and native Arabic data-loader adapter are not complete. The current executable trainer is a separate experimental raster baseline, not native MX-Font.
4. The text-style route lacks reviewed semantic style prompts and a pretrained semantic Arabic text encoder.
5. No tiny-subset overfit, convergence, held-out-family quality evaluation or full dataset training has been run.
6. Raster output is not a TTF/OTF font. Vectorization, OpenType tables, GSUB/GPOS shaping, font compilation and final font QA remain separate work.
7. The model-weight distribution license is separate from the font rights manifest.
8. The user's Windows GPU/VRAM/RAM/disk preflight has not been run.

## Important license distinction

The project can distribute its own model and generated fonts for free, but SIL OFL 1.1 is not an NC license. It does not prohibit downstream commercial use of generated fonts, subject to OFL terms. If downstream non-commercial-only use is required, obtain explicit permission from the source font copyright holders to use a different license.

## Core documentation

- [OFL AI-training policy](docs/OFL_AI_TRAINING_POLICY.md)
- [Local training handoff](docs/LOCAL_TRAINING.md)
- [Contextual episode dataset](docs/CONTEXTUAL_EPISODE_DATASET.md)
- [Pretraining readiness report](reports/PRETRAINING_READINESS.md)
- [Model architecture](docs/MODEL_ARCHITECTURE.md)
- [Experimental multimodal baseline](docs/EXECUTABLE_MULTIMODAL_BASELINE.md)
- [Upstream baseline and dependency pin](docs/UPSTREAM_BASELINE.md)
- [Font rights and batch shaping](docs/FONT_RIGHTS_AND_BATCH_SHAPING.md)

**Do not start a long training run until the remaining gates are resolved and the user explicitly approves training.**
