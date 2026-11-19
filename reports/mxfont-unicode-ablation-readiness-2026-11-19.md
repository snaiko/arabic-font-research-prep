# MX-Font vs MX-Font + Unicode: ablation readiness

Date: 2026-11-19

## Decision

**The quality ablation has not been run.** The repository currently does not contain a native MX-Font Arabic training dataset or an executable native MX-Font experiment configuration. Reporting a baseline/Unicode score now would be fabricated.

The Unicode bridge remains an isolated prototype on `experiment/mxfont-unicode-bridge`. It is not merged into `main`, not connected to the trainer, and has not been trained.

## What the pinned MX-Font implementation actually requires

At upstream revision `9d2b6ace3e23199e2a896de329d4c16489b09a96`, `MXTrainDataset.__getitem__` constructs each sample from:

1. `trg_img`: target glyph image from one font;
2. `style_imgs`: other characters from that same target font;
3. `char_imgs`: the same target character rendered by other fonts;
4. `trg_decs` and `char_decs`: decomposition/primitive IDs for the target character;
5. font and character class IDs used by auxiliary/discriminator objectives.

The upstream trainer factorizes content features from `char_imgs` using `factorize(..., emb_dim=1)`, then reconstructs them with style factors from `style_imgs`. The `trg_cids` field is a dataset-local class index, not a Unicode scalar value; the bridge must receive the actual target Unicode sequence from the dataset record.

## Current blockers confirmed in this repository

- The current 1,732 contextual episodes pair a target cluster with four same-font style references. They do **not** include the MX-Font same-character cross-font `char_imgs` contract.
- The 1,872 isolated crops are a useful raw source for a future cross-font pairing builder, but the native MX-Font loader/config and a validated paired-sample export have not been produced.
- MX-Font's decomposition/primals supervision is not available as reviewed Arabic labels. Existing component geometry candidates are explicitly marked identity-unknown, machine-generated/unreviewed, and `training_eligible=false`. Raster connected components cannot safely be relabelled as dots, hamza, or body without evidence.
- The current contextual-cluster targets include multi-codepoint sequences. The pinned MX-Font training dataset is character-keyed and does not by itself solve contextual shaping/cluster generation.
- The pinned upstream trainer is CUDA/NCCL-oriented. A supported runtime and a reproducible baseline execution have not yet been established.
- No native MX-Font checkpoint trained on this corpus is available in the repository. Both B0 and B2 therefore need the same initialization and training budget once the data/runtime gates are solved.

These are blockers to a meaningful comparison, not merely missing unit tests.

## Exact experiment to run once the blockers are cleared

Use a single immutable dataset manifest, family-level split, image preprocessing, batch order, seed set, training-step budget, optimizer/scheduler, and validation schedule for every arm.

| Arm | Model | Purpose |
|---|---|---|
| B0 | Untouched pinned MX-Font | Baseline |
| B1 | MX-Font + zero-initialized/frozen Unicode bridge | Verify identity path does not change baseline |
| B2 | Same MX-Font + trainable Unicode bridge | Measure the contribution of Unicode conditioning |

For each seed, initialize B0 and B2 from the same MX-Font weights. Keep the discriminator, auxiliary classifier, and all upstream losses identical. The bridge may modify only the content factors produced from `char_imgs`; the target Unicode sequence must be repeated/aligned with the corresponding cross-font content images. It must never modify style factors.

Report on the exact same held-out font families and target set:
- pixel MAE/L1 and edge error;
- character identity / codepoint-conditioned correctness;
- connected-component and dot-count consistency only where reviewed labels exist;
- contextual joining and multi-codepoint cluster quality on a separately valid cluster test set;
- per-family results, mean and standard deviation across seeds;
- parameter count, peak VRAM, throughput, and wall-clock training budget.

Adoption rule: keep B2 only if its improvement is repeatable across seeds and held-out families, and it does not regress identity, joins, or structural fidelity. If the confidence interval overlaps no improvement or critical Arabic errors increase, reject the bridge. B1 must reproduce B0 within numerical tolerance.

## CI correction

The previous workflow run `44542514944` reported success, but its test-discovery pattern only matched `test_multimodal*.py`; it did not select `test_mxfont_unicode_adapter.py`. The workflow has now been corrected to compile the adapter test and run a separate `test_mxfont*.py` discovery step. The new commit will trigger CI. A green result will establish adapter unit-test status only, not image-quality improvement.

## Current result

- B0 score: **not measured**.
- B1 equivalence: **not measured against a real MX-Font run**.
- B2 score: **not measured**.
- Adoption decision: **deferred; no evidence to keep or reject the bridge yet**.
- Training started: **no**.

## Next implementation gate

Build and validate the native MX-Font sample exporter from the approved isolated glyph corpus, including same-character cross-font content images, same-font style references, explicit Unicode strings, family-safe splits, and a defensible Arabic primitive/decomposition source. Until the decomposition and runtime gates pass, do not launch the ablation or merge the bridge.
