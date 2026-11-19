# Pretraining Readiness Report

<badge color="warning">BLOCKED — NOT READY FOR TRAINING</badge>

Updated 2026-11-19. This report is not a test report from the user's Windows computer. No model training was started.

## Completed in this preparation update

- Pinned upstream MX-Font to immutable commit `9d2b6ace3e23199e2a896de329d4c16489b09a96`.
- Added an isolated single-codepoint crop builder: `scripts/build_isolated_glyph_crops.py`.
- Added a deterministic few-shot episode sampler: `scripts/build_mxfont_episodes.py`.
- Added unit tests for target/reference leakage, deterministic sampling, split preservation, and insufficient glyph counts.
- Added `data/arabic_character_system_v1.json`, a Unicode 17.0-based starter registry covering 31 core/common Arabic records, plus a standard-library validator and dedicated tests. Joining metadata is separated from provisional visual-family annotations; no component decomposition labels are claimed.
- Added registry validation and tests to GitHub Actions. [Run 44465453724](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44465453724) passed: registry validation, Python compilation, and all nine repository unit tests.
- Added a GitHub Actions validation workflow. <badge color="success">CI passed</badge> [Run 44463443539](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44463443539): both scripts compiled and all four episode sampler tests passed.
- Documented the intermediate data format and its limitations in `docs/GLYPH_CROP_AND_EPISODE_ADAPTER.md`.

## What the passing tests do and do not prove

The CI validates Python syntax and the episode sampler's unit tests. It does not run the crop builder on the user's font archive, visually review crops, validate every font's ML-training permission, or prove compatibility with the official MX-Font loader.

The crop builder re-renders isolated single Unicode codepoints directly from their font files with Pillow-RAQM. It intentionally does not crop connected words because trustworthy HarfBuzz cluster-to-pixel mapping is not yet implemented. These isolated crops do not provide joining-form, ligature, or combining-mark supervision.

The episode sampler groups by exact font hash and inherited family split, selects four distinct reference codepoints, and excludes the target codepoint from its own references. It is an intermediate project schema, not the upstream MX-Font native dataset format.

## Remaining blockers

- Run the crop builder on the local corpus and inspect actual output/contact sheets.
- Complete asset-by-asset training-rights and provenance review.
- Implement a tested adapter to the pinned upstream MX-Font native loader.
- MX-Font uses weak component supervision and decomposition/primals labels. The new Arabic character registry supplies joining metadata only; a defensible, expert-reviewed visual decomposition/component-label strategy is still not present.
- Complete upstream dependency/license clearance and reproduce the baseline in a supported environment. CUDA/NCCL Windows compatibility is not established.
- Populate paired prompt/geometry data and implement image, prompt, and hybrid paths sharing one generator.
- Pass model forward/backward, leakage, checkpoint save/reload/resume, and held-out-family evaluation tests.
- Run the actual local hardware preflight and produce a resource estimate.

## Current gate summary

| Area | Status |
|---|---|
| Upstream revision pin | PASS |
| Full upstream license/dependency audit and baseline reproduction | BLOCKED |
| Isolated crop/episode adapter code + CI tests | PASS (limited scope) |
| Published archive integrity audit (7,904 samples / 7,904 images) | PASS |
| Crop quality review on local corpus | UNKNOWN |
| Contextual joining/ligature/mark supervision | FAIL |
| Asset-level training permissions | BLOCKED |
| Arabic character/joining registry structure + CI | PASS (starter scope only) |
| Native MX-Font loader and audited Arabic component labels | FAIL |
| Prompt/geometry paired data and unified model paths | FAIL |
| Full model/checkpoint/evaluation tests | FAIL |
| Local hardware and resource estimate | UNKNOWN |

**Training remains disabled.** The next step is local data execution and audit, then native MX-Font compatibility and expert-reviewed Arabic visual decomposition labels. Even after every preparation gate passes, the first training run requires the user's explicit approval.

## Arabic linguistic and visual system expansion

- Added a reproducible Unicode 17.0 importer that downloads the official UCD inputs, builds all assigned `Script=Arabic` records (CI generated 1,413 records), and embeds SHA-256 hashes for its three source files.
- Added a registry validator and CI artifact. The latest successful complete-registry run generated 1,413 records, validated the registry, and passed all 19 tests in the latest CI run: [Run 44466347309](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44466093346).
- Added a per-component agreement analyzer: it pairs annotations for the same rendered glyph and reports precision, recall, F1, and polygon IoU per component class. Its unit tests cover identical, mismatched, and displaced annotations.
- Added a per-glyph-instance visual annotation schema and validator for body, individual dots, hamza, marks, counters, join regions, strokes, ornaments, uncertainty, and component relations. This is a schema/protocol, not an annotated dataset.
- Added Arabic shaping regression strings and a HarfBuzz runner to capture font-specific glyph IDs, clusters, and advances. It has not yet been run against a cleared font file, so no shaping results are claimed.
- The full system and annotation policy are documented in `docs/ARABIC_SCRIPT_AND_VISUAL_SYSTEM_V2.md`.


## Latest readiness work — 2026-11-19

- Added a fail-closed local corpus audit: `scripts/audit_training_corpus.py`. It checks family-level split leakage, duplicate sample identities, font SHA-256 consistency, optional local font/image existence and path safety, and optional source-asset rights evidence.
- Added tests for clean data, family leakage, duplicate samples, and unapproved source assets.
- Added a separate per-font rights gate and batch HarfBuzz runner; the batch runner requires at least three distinct approved families and exact file-hash matches.
- GitHub Actions run [44469089468](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44469089468) passed script compilation, Unicode registry generation/validation, and all 29 unit tests.

**Published corpus audit completed:** GitHub Actions run [44476157196](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44476157196) downloaded both published release archives and audited their actual contents. It verified 7,904 samples, 52 font files, 20 families, family splits of 14 train / 3 validation / 3 test families, and all 7,904 referenced images; the audit returned `errors: []`. All 30 unit tests passed. The earlier duplicate-sample failure was a false positive in the audit script: it used `target_index` instead of the dataset's `target_index_logical`. That bug is fixed and covered by a regression test.

This PASS verifies corpus structure and file integrity only. It does not approve font ML-training rights or establish visual quality, contextual crop correctness, or Arabic shaping supervision. No font rights approvals, real HarfBuzz reports, visual crop review, two-person annotation pilot, paired prompt/geometry corpus, executable unified model paths, upstream baseline reproduction, or local hardware report have been supplied. Those gates remain BLOCKED/UNKNOWN/FAIL as recorded in `reports/pretraining_readiness.json`. Training remains disabled.


## Human review package — 2026-11-19

- Added `scripts/build_arabic_review_pack.py` to select samples deterministically across all HarfBuzz shaping cases while spreading selections across font families.
- The CI job is configured to produce an offline HTML gallery and a machine-readable visual/linguistic review ledger (target: 10 examples per shaping case).
- The geometry pilot is restricted to samples with exactly one source codepoint and one shaped glyph, because the current component schema models one glyph instance. It creates separate blank annotation ledgers for two independent annotators and an adjudication tracker (target: up to 40 samples).
- Added `docs/ARABIC_HUMAN_REVIEW_PROTOCOL.md` with review criteria, double-annotation procedure, disagreement analysis, and explicit acceptance gates.
- Added tests for deterministic family-stratified selection and valid draft annotation templates.

**Important:** the package is a review instrument, not evidence that a human has reviewed the samples. No visual/linguistic labels or geometry labels are approved by the build process. Human visual review, independent geometry annotation/adjudication, and exact-font legal approvals remain BLOCKED. The review-pack CI run must pass before its artifact can be used.


**Review-pack CI verified:** GitHub Actions runs [44506507595](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44506507595) and [44506521255](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44506521255) completed successfully. The uploaded `arabic-human-review-pack` artifact contains 100 visual/linguistic samples (10 from each of the 10 shaping cases, with 10 font families represented per case) and 40 geometry-pilot samples selected from the full eligible corpus, balanced across eight cases with eligible single-codepoint/single-glyph examples. It includes separate 40-record draft annotation ledgers for annotators A and B, an adjudication tracker, source images, and an offline HTML gallery.

The package-generation gate is PASS. **The human review and component-annotation gates remain BLOCKED** until qualified reviewers complete the work and adjudication records are returned. The font-rights manifest remains empty and training remains disabled.


## Verified update — 2026-11-19 (supersedes earlier crop-status statements)

GitHub Actions run [44515674785](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44515674785) completed successfully on the current preparation code. It passed **40 repository unit tests** and ran the complete published-corpus pipeline:

- Published corpus audit: 7,904 samples, 52 font files, 20 families, 7,904 images verified, zero audit errors.
- Isolated crop generation: 1,872 single-codepoint crops; zero rejected; crop audit passed. These are isolated forms, not connected-form or ligature labels.
- Contextual cluster generation: 1,732 clusters; independent HarfBuzz mapping checks passed with zero integrity errors; 518/520 font-case pairs observed. The two missing pairs are Aref Ruqaa tatweel cases where no renderable tatweel crop was produced.
- Machine-derived visual supervision: 1,732 records generated, 1,135 unique raster hashes. Records contain canonical Unicode/HarfBuzz metadata and deterministic raster measurements (ink bounds, centroid, ink ratio, and row/column occupancy profiles). These are measurements, not expert component segmentation or linguistic/artistic approval.
- Cluster review pack: 100 draft records validated; package generation is not a review result.
- Font-rights candidate scan: 52 files across 20 families; **0 ML-training approvals**. The rights manifest remains empty.

### Current gate correction

| Area | Current status |
|---|---|
| Published corpus integrity | PASS |
| Isolated single-codepoint crop generation and audit | PASS |
| Contextual HarfBuzz cluster coverage | PARTIAL (518/520 pairs) |
| Machine-derived raster measurement supervision | PASS (1,732 records; not expert labels) |
| Expert visual/linguistic review | BLOCKED |
| Human component geometry annotations/adjudication | BLOCKED |
| Font-level ML-training rights | BLOCKED (0 approved) |
| Prompt/geometry paired corpus and executable model paths | FAIL / not verified |
| Training authorization | BLOCKED |

The visual-supervision artifact is available from run [44515674785](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44515674785) as `arabic-visual-supervision` (artifact ID `14525941407`).

**Final decision: training is still not allowed.** No model training has been started. Automated checks can verify file integrity, shaping mappings, and measurable raster geometry, but they cannot manufacture expert visual/linguistic approval or legal permission to use each font for ML training. All 1,732 machine-supervision records are currently marked `training_eligible=false` because zero font rights have been approved.


## Verified three-part data update — 2026-11-19

GitHub Actions run [44517742747](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44517742747) completed successfully. Python compilation and all **44 unit tests** passed. The pipeline generated and uploaded the following evidence:

### 1. Arabic visual and linguistic consistency

- The Unicode 17 / ArabicShaping audit passed on all **1,732 contextual clusters and 2,022 codepoints**, with **zero errors**.
- It checked canonical source spans, codepoint/category mapping, Joining_Type, combining-mark flags, and glyph cardinalities. The independent HarfBuzz audit also reproduced the glyph-ID mappings for all generated rows with zero integrity errors.
- This is an automated metadata/shaping-integrity pass, not proof of correct spelling in arbitrary text, readable glyph appearance, or calligraphic/artistic quality. Expert visual and linguistic review remains BLOCKED.

### 2. Exact font license evidence

- All **52 font files** were matched to their exact SHA-256 and pinned Google Fonts source revision.
- CI retrieved and preserved all **20 family-level license texts**, verified the SIL Open Font License 1.1 marker and selected clauses, hashed the snapshots, and extracted copyright headers and Reserved Font Name candidates.
- None of the 20 license texts explicitly addresses machine-learning training. This does not itself prove training is prohibited or permitted; it means the proposed use has not been legally resolved.
- **Approved fonts: 0.** The rights manifest remains empty and training remains disabled.

The license evidence package is the [pinned-font-license-evidence artifact](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44517742747/artifacts/14525643961).

### 3. Component candidates and paired captions

- Generated **1,732** cluster-level records.
- Extracted **2,987** 8-connected raster component candidates with bounding boxes, area, relative area, and normalized centroids.
- Added **1,732 Arabic and 1,732 English factual template captions**, each tied to the source text, Unicode metadata, HarfBuzz glyph mapping, and image.
- Detached components are not semantically identified as dots, hamza, marks, or ornaments: every component's semantic identity remains `unknown`.
- Captions are `machine_generated_unreviewed`, not expert-authored style descriptions. These records are useful auxiliary machine-derived supervision, not gold component labels or a completed style-prompt dataset.

The generated data is available in the [Arabic component/caption supervision artifact](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44517742747/artifacts/14525149976).

### Updated decision

| Gate | Status |
|---|---|
| Unicode/ArabicShaping metadata audit | PASS |
| Pinned license text evidence retrieval | PASS |
| Component candidate and caption generation | PASS |
| Expert visual/spelling/calligraphic validation | BLOCKED |
| Semantic body/dot/hamza/mark decomposition labels | PARTIAL — candidates only |
| Per-file ML-training rights | BLOCKED — 0 approved |
| Overall training authorization | BLOCKED |

**No model training has been started.** The automation has strengthened the dataset and made the remaining uncertainties explicit; it has not fabricated legal approvals or human visual ground truth.


## Verified implementation update — 2026-11-19

GitHub Actions run [44520251086](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44520251086) passed the full data pipeline and unit suite. A separate CPU PyTorch run [44520250916](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44520250916) passed all four model smoke tests.

### 1. Contextual Arabic clusters

- **1,732** cluster crops and metadata records were regenerated and independently checked.
- HarfBuzz mapping was reproduced for all 1,732 records.
- Coverage remains **518/520 font-case pairs**. Two Aref Ruqaa font files do not render the tatweel case; those omissions remain explicit rather than being fabricated.
- **238** multi-codepoint clusters are retained.

Status: **PARTIAL** — data integrity passes; coverage is not complete.

### 2. Paired Arabic/English captions

Added an independent audit at `scripts/audit_arabic_component_supervision.py`. It verifies source-derived identities, Unicode text/codepoint consistency, glyph IDs/counts, image hashes and dimensions, nonblank crops, safe image paths, component geometry bounds, caption language/provenance, and family-level split isolation.

Latest audit result:

| Measure | Result |
|---|---:|
| Source-bound records | 1,732 |
| Raster component candidates | 2,987 |
| Paired Arabic/English captions | 3,464 |
| Font families | 20 |
| Boundary-touching crops | 0 |
| Audit errors | 0 |
| Training-eligible records | 0 |

Status: **PASS for integrity and measurable geometry; NOT APPROVED as linguistic/style descriptions.** Captions remain deterministic machine-generated factual descriptions. They do not claim that a detached component is a dot, hamza, or mark.

Audit artifact: [arabic-component-caption-audit](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44520251086/artifacts/14527697540).

### 3. Visual and technical validation

The new independent raster audit found no blank images, path escapes, hash mismatches, out-of-range component geometry, family split leakage, or ink touching the 160×160 crop boundary.

Status: **PASS for automated geometric/integrity QA.** Human-level spelling, readability, calligraphic quality, and semantic decomposition are still not established. Review packs are generated drafts, not completed reviews.

### 4. Font rights

The pinned license evidence still covers all 52 exact font files across 20 families. The license audit does not explicitly settle ML-training permission.

Status: **BLOCKED — zero approved font files.** No automated script can legitimately turn ambiguous license text into legal approval. The active manifest remains fail-closed.

### 5. Executable model paths

Added `models/arabic_multimodal_glyph.py`, a small experimental model with one shared raster decoder and three executable conditioning routes:

- reference-image conditioning;
- Unicode-codepoint text conditioning;
- confidence-gated hybrid conditioning.

The text branch is a trainable codepoint-level GRU, **not** a pretrained Arabic language model or semantic natural-language encoder. This baseline is not the pinned MX-Font implementation or its native data adapter.

Status: **PASS for executable smoke paths; PARTIAL for project architecture readiness.** Image/text/hybrid forward and backward tests all passed on CPU.

### 6. Checkpoint and training smoke tests

The dedicated model workflow passed four tests covering all three conditioning routes, model checkpoint round-trip, optimizer-state restoration/resume, and Arabic Unicode codepoint encoding.

The main data workflow ran **51 tests: 47 passed and 4 optional PyTorch tests were skipped** in that job. Those four tests were run separately and all passed in the dedicated model workflow.

Status: **PASS for smoke tests and checkpoint/optimizer-state resume.** A real dataset training run, tiny-subset overfit, convergence, held-out-family evaluation, and the user's hardware-specific training/resume remain unverified.

### Final decision

**Overall: BLOCKED. Training remains disabled and no model training has been started.**

The remaining hard blockers are legal permission for exact font assets, trustworthy visual/linguistic ground truth or a justified alternative objective, complete contextual coverage, the MX-Font native adapter/dependency audit, and real dataset-level training/evaluation. The new experimental baseline makes the three conditioning paths executable, but does not by itself establish generation quality or readiness for full training.


---

## Verified update — 2026-11-19 (conditional OFL clearance and renewed data pipeline)

This section supersedes the earlier statements in this report that all 52 Google Fonts files had zero ML-training approvals.

### Rights interpretation and manifest

The official SIL OFL FAQ version 1.1-update8 (November 2026) now explicitly addresses AI font generation:
- Q1.25 states that fonts generated by AI/ML systems using OFL source data must remain under OFL; a different license requires explicit permission from the corresponding authors.
- Q3.9 confirms that AI-based font design tools may modify OFL sources, with resulting released font software subject to the normal OFL derivative-font conditions.

Official source: https://openfontlicense.org/ofl-faq/

The project now uses a conservative conditional policy: all generated font files based on the 52 exact OFL sources must be released under SIL OFL 1.1, preserve source copyright notices and acknowledgements, and avoid every recorded Reserved Font Name unless written permission is obtained. The OFL is not a NonCommercial license; downstream commercial use is not prohibited by OFL terms. The project's own distribution can remain free. Model-weight licensing is separate and not resolved by the font manifest.

### Verified rights manifest

GitHub Actions run [44527370231](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44527370231) completed successfully:
- 52 exact font files across 20 families.
- All 20 pinned license snapshots passed source/text integrity checks.
- 52 per-file rights records generated.
- Every file path and SHA-256 validated against the actual downloaded font corpus.
- The artifact [conditional-ofl-font-rights-manifest](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44527370231/artifacts/14532290911) contains the manifest and its full license/provenance evidence.

### Rights eligibility propagated into visual supervision

GitHub Actions run [44527604462](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44527604462) completed successfully and regenerated the visual-supervision dataset using the conditional rights manifest:
- 1,732 records now pass the per-file rights gate.
- Split counts: 1,134 train / 299 validation / 299 test.
- All 20 families represented.
- This is rights eligibility only; the raster geometry remains machine-derived and visual/linguistic truth is not approved.
- The component/caption dataset remains auxiliary and unreviewed; semantic identities are still unknown.

### Arabeyes binary audit completed

GitHub Actions run [44525849649](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44525849649) successfully downloaded and checksum-verified the Debian Arabeyes source archive:
- 36 TTF binaries inspected, 36 unique SHA-256 values.
- All 36 have Arabic-range cmap entries.
- All 36 passed one fixed HarfBuzz phrase smoke test with zero missing glyph IDs.
- All 36 previews rendered.
- The archive README documents GPL v2 with a narrow document-embedding font exception and Latin glyph provenance from Free UCS Outline Fonts. This does not explicitly settle ML training or model-weight distribution; **0 Arabeyes files are approved for training**.
- Artifact: [arabeyes-font-binaries-and-audit](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44525849649/artifacts/14529888093).
- Full results: [arabeyes-binary-audit-results-2026-11-19.md](https://github.com/snaiko/arabic-font-research-prep/blob/main/reports/arabeyes-binary-audit-results-2026-11-19.md).

### Remaining readiness blockers

Overall status remains **BLOCKED** and `training_allowed=false`. Rights are conditionally cleared for the 52 OFL source files, but the following are still open:
1. Batch HarfBuzz regression across all 52 approved files is now in CI but must complete successfully before claiming the gate passed.
2. The pinned MX-Font dependency closure and native data-loader adapter are not fully audited/reproduced.
3. Contextual cluster coverage remains 518/520 font-case pairs; two Aref Ruqaa tatweel pairs are explicitly absent.
4. Expert visual/spelling/calligraphic review and semantic component labels remain unapproved.
5. The experimental multimodal baseline has smoke tests only; no tiny-subset overfit, convergence, held-out-family evaluation, or full dataset training has been run.
6. Local Windows GPU/VRAM/RAM/disk preflight and hardware-specific resume remain unknown.
7. The model-weight distribution license must be chosen separately.

No model training has started.


## Verified update — 2026-11-19 (batch HarfBuzz regression)

GitHub Actions run [44527935025](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44527935025) ran the new batch HarfBuzz regression after generating and validating the conditional OFL rights manifest.

- **52/52** exact font files passed path and SHA-256 validation.
- **20** distinct font families.
- **10** shaping regression cases per font.
- **520** font-case reports generated.
- The batch summary status is **PASS**.
- Evidence artifact: [approved-font-harfbuzz-regression](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44527935025/artifacts/14532261639).

This verifies that the pinned HarfBuzz runner executed and captured outputs for the complete approved font set. It does not prove that every shaping result is visually correct, that all Arabic text is covered, or that every cluster is linguistically/artistically correct.

The overall readiness status remains **BLOCKED**. The remaining major blockers are expert visual/linguistic validation, the two missing contextual tatweel font-case pairs, the upstream MX-Font dependency/native-loader audit, dataset-level overfit/convergence and held-out-family evaluation, and local hardware/resource preflight. No model training has started.


## Final preparation update — 2026-11-19 (experimental image-route handoff)

This update supersedes earlier overall readiness statements for the **standalone experimental image-reference raster baseline**. It does not declare the complete production font generator ready.

### Current decision

<badge color="success">Ready for a controlled experimental image-route training run</badge>

- `training_allowed=true` for the limited image-reference raster baseline under the conditional OFL source-font policy.
- `training_started=false`; no model weights have been updated by training.
- `overall_status=PARTIAL_READY_FOR_EXPERIMENTAL_IMAGE_ROUTE`.
- Native MX-Font integration, semantic text-style generation, vectorization, OpenType font compilation, and production visual QA remain outside this limited readiness decision.

### Verified data and rights

1. **Rights:** 52 exact font files across 20 families have a hash-validated conditional SIL OFL 1.1 rights manifest. Any generated font software based on these sources must remain OFL 1.1, preserve copyright notices/acknowledgements, and avoid recorded Reserved Font Names without written permission.
2. **HarfBuzz:** 52 fonts × 10 cases = 520 batch regression reports; CI passed.
3. **Contextual few-shot episodes:** 1,732 episodes, four isolated references from the same exact font per target, zero skipped targets, 238 multi-codepoint targets, 1,134 train / 299 validation / 299 test, 20 families, and no family split leakage.
4. **Image integrity:** the no-training preflight verified SHA-256 for all **1,732 target images** and **6,928 reference images** across all three splits.
5. **Real model preflight:** a real batch loaded and the image-reference model produced a finite 128×128 output. The preflight explicitly recorded `training_performed=false`, `optimizer_created=false`, `backward_pass_performed=false`, `weights_updated=false`, and `checkpoint_created=false`.
6. **Tests:** main data CI run [44530248721](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44530248721) passed 73 tests (60 passed, 13 optional PyTorch tests skipped in that job). Dedicated CPU model/training pipeline run [44530248539](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44530248539) passed 13/13 tests.
7. **Episode/preflight artifact:** [arabic-contextual-style-episodes](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44530432867/artifacts/14533013474).

### Windows training handoff

- `START_LOCAL_TRAINING.bat` runs the machine/hardware preflight only; it does not train.
- `RUN_IMAGE_ROUTE_TRAINING.bat` checks the required artifacts and asks the user to type `TRAIN` before starting a real run.
- `scripts/train_multimodal_glyph.py` supports explicit step counts, validation/test evaluation, checkpoint saving, and optimizer-state resume.
- Full instructions: [docs/LOCAL_TRAINING.md](../blob/main/docs/LOCAL_TRAINING.md).

### What this ready status does and does not mean

**Ready:** a controlled experiment that learns to predict a contextual Arabic raster from the target Unicode sequence and four same-font reference glyphs.

**Not ready:** a semantic natural-language style generator, native MX-Font model, or production TTF/OTF font generator. The text-style route is a character-level GRU, not semantic Arabic NLP. The output is a raster image; vectorization, OpenType tables, GSUB/GPOS and final font QA are not implemented.

### Remaining work after the first controlled experiment

- Run the Windows hardware preflight and choose realistic batch/step settings.
- After the user/local agent starts training, measure tiny-subset overfit, convergence, validation/test loss, and held-out-family visual quality.
- Decide a separate distribution license for model weights.
- Finish native MX-Font integration only if that upstream architecture remains required.
- Complete vectorization/OpenType and production visual/linguistic validation before calling the system a finished font generator.

### Non-commercial license caveat

SIL OFL 1.1 is not an NC license. The project itself can publish its model and fonts for free, but the OFL does not prohibit downstream commercial use of generated fonts. If the user requires a strict prohibition on commercial use by everyone, the OFL-based source set cannot meet that requirement without explicit written permissions for a different output license.


## Local handoff hardening — 2026-11-19

The Windows preflight has been updated to match the new experimental image-route trainer rather than the older blocked MX-Font workflow.

- `scripts/preflight_local_training.py` now checks the exact 52-file/20-family OFL manifest, all episode splits, same-font references, target/reference non-leakage, image-hash metadata, CPU/GPU/VRAM/RAM/disk, and runs the no-training real-data model preflight when the artifacts and PyTorch are present.
- It recommends a batch size from actual detected VRAM/RAM and writes `reports/local/machine_preflight.json`.
- `START_LOCAL_TRAINING.bat` reports PASS/BLOCKED and never trains.
- `RUN_IMAGE_ROUTE_TRAINING.bat` requires typing `TRAIN` before a real training run.
- The trainer now defaults to embedding width 32 and batch size 4, supports optimizer-state checkpoint resume, and validates the exact font family mapping plus image hashes before training.

### Updated CI evidence

- Main data CI [44531266058](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44531266058): **78 tests, 64 passed, 14 optional PyTorch tests skipped** in that job.
- Dedicated CPU model workflow [44531024750](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44531024750): **14/14 tests passed**.
- Real-data preflight [44531243357](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44531243357): all **1,732 target** and **6,928 reference** image hashes verified; 52 approved font hashes; one real 128×128 forward pass; no training.

### Memory estimate

The compact model has **73,604,738 parameters**. FP32 weights occupy approximately **294 MB**. Weights + gradients + AdamW moments have a lower-bound estimate of **1.18 GB**, excluding activations and runtime overhead. This is a model-side estimate only; the user's actual Windows hardware still needs inspection.

**Current handoff:** the experimental image-reference raster route is prepared for a controlled run. The user's Windows preflight and explicit go-ahead are still required before training starts. Production TTF/OTF generation remains incomplete.
