# Arabic Few-Shot Font Research

Research preparation for an Arabic font-generation system that learns a visual style from reference glyphs and predicts Arabic glyphs and shaped clusters.

> **Current status (2026-11-19):** A separate experimental image-reference raster prototype has a passing data/forward preflight and a downloadable data handoff. It is **not MX-Font, not merged with MX-Font, and not a replacement for the selected upstream architecture**. The source-level compatibility audit found no direct checkpoint/weight mapping and confirmed that the current episode data is not native MX-Font-ready. No training has been started. Production TTF/OTF generation is not ready.

## Verified preparation

- **Source rights:** 52 exact Google Fonts files across 20 families are conditionally approved for this training pipeline under SIL OFL 1.1. Generated font software based on these sources must remain OFL 1.1, preserve notices, and avoid recorded Reserved Font Names. See [OFL AI-training policy](docs/OFL_AI_TRAINING_POLICY.md). OFL is not a NonCommercial license; downstream commercial use is not prohibited by its terms.
- **Raster data:** 7,904 published samples from 52 font files and 20 families; family-safe split of 14 train / 3 validation / 3 test families; published corpus integrity audit passed.
- **Isolated crops:** 1,872 single-codepoint glyph crops.
- **Contextual targets:** 1,732 HarfBuzz-shaped cluster crops; 238 multi-codepoint clusters; independent glyph-ID mapping audit passed. Coverage is partial at 518/520 font-case pairs because two Aref Ruqaa tatweel cases do not render.
- **Few-shot episodes:** 1,732 episodes, each pairing a contextual target with four isolated reference glyphs from the same exact font; target codepoints are excluded from references; 1,134 train / 299 validation / 299 test across 20 families. The combined handoff contains 1,732 target PNGs and 1,872 reference PNGs; all 3,604 images were decoded and SHA-256 verified. The 6,928 episode reference uses draw from 1,831 distinct reference PNGs; 41 valid reference crops are not sampled by this episode set. The real-data preflight passed without training ([latest handoff run](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44539170273)).
- **Shaping regression:** 52 conditionally approved fonts × 10 cases = 520 HarfBuzz regression reports; CI passed.
- **Separate experimental model:** models/arabic_multimodal_glyph.py is a 20.1M-parameter raster prototype with image, codepoint-text and hybrid conditioning. It is not MX-Font and has no demonstrated weight/checkpoint compatibility with it. The image-reference route alone has a prepared trainer. The dedicated CPU workflow passed 16/16 tests; this is not evidence of training quality.
- **Arabeyes research:** 36 binaries downloaded and checksum-verified; all passed one shaping smoke phrase and rendered previews. They remain excluded from training because GPL+Font Exception does not expressly settle ML training or model/output distribution.

## Architecture boundary — read before using the handoff

- The selected upstream architecture remains [MX-Font](docs/UPSTREAM_BASELINE.md), pinned to 9d2b6ace3e23199e2a896de329d4c16489b09a96.
- models/arabic_multimodal_glyph.py is a separate experimental raster prototype. It does not implement MX-Font's localized expert bank, factorization, expert skip fusion, discriminator or decomposition objectives.
- The two model graphs and checkpoint tensors are not directly merge-compatible. The current 1,732-episode handoff supplies a target Unicode cluster plus four same-font style references; native MX-Font additionally needs same-character content images from other fonts and audited character primitive/decomposition labels.
- Do not describe this prototype as the merged model or pass this handoff to the native MX-Font trainer. See [Model Architecture Compatibility Audit](reports/model-architecture-compatibility-audit-2026-11-19.md).

## Training handoff

The complete data package for the separate raster prototype is available as [arabic-font-training-handoff (workflow run 44539170273)](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44539170273). The artifact is 10,070,054 bytes with SHA-256 5569fbfdf056438bbc712d01e2b6e604f1a6583783f215e02716d2289c1f90b9. See [Local Training Handoff](docs/LOCAL_TRAINING.md) for the data package, Windows preflight, checkpoint interface, and license conditions. This package is not an MX-Font-native dataset. The optional Windows launcher is [RUN_IMAGE_ROUTE_TRAINING.bat](RUN_IMAGE_ROUTE_TRAINING.bat); it requires typing TRAIN before starting.

The trainer `scripts/train_multimodal_glyph.py` uses the image-reference route only:
- target Unicode cluster + four same-font reference glyphs → 128×128 grayscale target raster;
- pixel L1 plus edge loss;
- family-held-out validation and test;
- per-font rights and data-leakage checks before loading.

A separate workflow builds [contextual few-shot episodes](docs/CONTEXTUAL_EPISODE_DATASET.md) and runs a no-training real-data preflight. The latest run [44539170273](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44539170273) passed; it verified 1,732 target and 6,928 reference uses, loaded a real batch, and produced a finite 128×128 raster. It recorded no optimizer creation, backward pass, weight update, checkpoint creation or training.

## Remaining blockers for a complete production font generator

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

Before starting the experimental run, perform the Windows hardware preflight and obtain the user's explicit go-ahead. Do not describe the system as a finished font generator until vectorization/OpenType and production visual-quality gates are complete.


## Independent verification refresh — 2026-11-19

- Reviewed the job summaries for all **28 workflow-run IDs referenced by the current readiness report**. All 28 returned completed/success jobs; no failed job was found in that inspected set. The latest main data CI [44538878182](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44538878182) completed 83 tests (67 passed, 16 optional PyTorch tests skipped); the dedicated CPU model run [44538121400](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44538121400) passed 16/16; the real-data episode/handoff run [44539170273](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44539170273) passed.
- Independently downloaded the combined handoff and verified its SHA-256 against the Actions artifact digest. All 1,732 target and 1,872 reference PNGs were decoded and checked against their manifests: **3,604/3,604 hashes matched**, with zero missing, unlisted, corrupt, or mismatched files. All 1,732 target PNGs are 160×160 RGB files whose R/G/B channels are identical (grayscale encoded); the 1,872 references are 128×128 grayscale PNGs. The training loader converts targets to grayscale before resizing to 128×128.
- Independently checked all 52 per-file rights records, 20 font families, 20 pinned OFL license snapshots, and all 20 snapshot hashes (zero mismatches). The policy remains conditional: released font software based on these sources must remain SIL OFL 1.1, preserve notices/acknowledgements, and respect Reserved Font Names. [The official OFL FAQ](https://openfontlicense.org/ofl-faq/) 1.1-update8 Q1.25/Q3.9 provides the AI-font guidance. OFL is **not** a NonCommercial license; downstream commercial use is not prohibited by its terms. Model-weight licensing is separate.
- Checkpoint save/restore and optimizer-state payload round-trip are unit-tested with a no-op probe. The trainer source has a resume option and periodic/final checkpoint saving, but there is no training-produced checkpoint or verified end-to-end real-optimizer resume. No optimizer, backward pass, weight update, checkpoint, or training was run in this verification.
- GitHub's connected Actions interface exposed job/artifact details for known run IDs but not a repository-wide run listing. Therefore the 28-run review is the complete evidence-linked set from the current readiness report, **not** a claim that every run or the latest 100 runs was enumerated. The earlier aggregate of 259 runs / 9 failures in the latest 100 remains a historical report value, not independently reverified in this refresh.

The original MX-Font plan remains blocked by its native data contract and missing audited Arabic decomposition labels. The separate experimental model still produces raster output only; TTF/OTF generation is not ready.


The later documentation commit that updated docs/LOCAL_TRAINING.md matches the main data-CI push path filter. Its resulting push run could not be listed or inspected through the available GitHub interface, so that post-update run status remains unknown.