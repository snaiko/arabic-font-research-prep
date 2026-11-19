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
