# Local AI Agent Execution Specification

This file is the task contract for the separate AI agent operating on the user's Windows computer. The agent is responsible for implementation and dataset preparation; the user is not expected to manually code or train the model.

## Required behavior

1. Clone or update this repository without deleting user files or overwriting existing checkpoints.
2. Read `LOCAL_AI_AGENT_GUIDE.md`, `docs/PRETRAINING_COMPLETION_PLAN.md`, `docs/DUAL_MODE_MODEL_SPEC.md`, `docs/MODEL_ARCHITECTURE.md`, `docs/DATA_SPECIFICATION.md`, and `docs/TRAINING_EVALUATION.md` before editing.
3. Inspect the actual Windows machine and repository state. Never invent GPU, memory, disk, dataset, or package information.
4. Work through WP0-WP5 in `docs/PRETRAINING_COMPLETION_PLAN.md`, in order. Make small, reviewable commits and preserve logs.
5. Do not start a long training run. Finish the implementation, data audit, tests, and readiness report first.
6. Stop and report any license ambiguity, missing source, unsupported device, failed test, or data-mapping uncertainty rather than fabricating a pass.
7. Do not upload private fonts, user data, machine reports, or model checkpoints to a public repository unless the user explicitly authorizes the specific upload.

## Implementation deliverables

- Immutable upstream MX-Font source pin, license/notice record, and untouched baseline.
- Deterministic, tested dataset adapter and episode sampler with correct HarfBuzz cluster handling.
- Audited isolated target-glyph crops and family-safe split manifests.
- Style-description dataset builder with Arabic/English descriptions, structured attributes, geometric labels, provenance, and synthetic/human-reviewed flags.
- Prompt encoder, image encoder, shared latent interface, one shared generator, and image/prompt/hybrid forward paths.
- Separate loss configuration for pixel, edge, structure, attribute, geometry, and cross-modal alignment objectives.
- Route-specific evaluation scripts and held-out-family metrics.
- Unit tests, smoke tests, checkpoint round-trip, tiny-subset overfit report, and sample contact sheets.
- Environment/dependency lock and Windows instructions.
- `reports/pretraining_readiness.json` and `reports/PRETRAINING_READINESS.md`.

## Exact stop condition

After all preparation is complete, present the readiness report and stop. Do not call `train.py`, launch a multi-hour process, or download/start a large pretrained model as an implicit side effect. The user must review the report and explicitly authorize the first training run.

## Reporting format

For each work package report:

- status: `PASS`, `FAIL`, or `BLOCKED`;
- files created/changed;
- commands actually run;
- test outputs and evidence paths;
- data counts and source/license caveats;
- remaining blockers.

Never mark a package PASS based only on writing code. Run the tests that establish the claim.
