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
