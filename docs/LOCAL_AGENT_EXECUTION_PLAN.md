# Local Agent Execution Plan — MX-Font Unicode Bridge

## Mission

Run the verification of the MX-Font Unicode bridge locally on this Windows computer, using the computer's available CPU/GPU/RAM. You are GitHub Copilot Agent operating inside VS Code with access to the checked-out repository and its terminal.

Repository: `snaiko/arabic-font-research-prep`
Required branch: `experiment/mxfont-unicode-bridge`
Related PR: #1 (Draft; do not merge it).

The purpose is to establish what is actually verified, not to claim success prematurely.

## Non-negotiable boundaries

1. Do not switch to or modify `main`.
2. Do not merge PR #1, close it, publish a release, or push changes.
3. Do not start full training.
4. Do not download large datasets or model checkpoints without first reporting the expected size and asking the user.
5. Do not overwrite, delete, or regenerate existing datasets, checkpoints, or user files.
6. Do not silently change model architecture, training objectives, data splits, or test expectations to make tests pass.
7. Do not claim that a test passed unless you ran it and captured its exit status/output.
8. If a dependency installation is needed, inspect the environment first. Prefer a project-local virtual environment. Do not change global Python installations.
9. Do not expose credentials, tokens, environment variables containing secrets, or personal files in logs/reports.
10. Keep the existing branch history intact. Do not rebase, force-push, or create commits.

## Phase 1 — Verify repository and branch

In the VS Code terminal:

- Print the current directory and repository root.
- Run `git status --short --branch`.
- Run `git branch --show-current`.
- Confirm the current branch is exactly `experiment/mxfont-unicode-bridge`.
- Record the current HEAD SHA with `git rev-parse HEAD`.
- Confirm the worktree is clean before testing.

If the branch is not the required branch, or there are uncommitted user changes, STOP and report the situation. Do not discard changes or switch branches automatically.

Inspect these files before running tests:

- `models/mxfont_unicode_adapter.py`
- `tests/test_mxfont_unicode_adapter.py`
- `scripts/build_mxfont_native_pairs.py`
- `tests/test_mxfont_native_pairs.py`
- `docs/MXFONT_UNICODE_BRIDGE.md`
- repository dependency/configuration files and CI workflow files relevant to model tests.

## Phase 2 — Hardware and runtime inventory

Collect and report:

- Windows version/build.
- Python version and executable path.
- Available system RAM (total and currently available).
- CPU model and logical core count.
- NVIDIA GPU model, driver version, and VRAM if present.
- Whether PyTorch imports successfully.
- PyTorch version.
- `torch.cuda.is_available()`, CUDA runtime version, and visible GPU names.
- Available disk space on the repository drive.

Use safe read-only commands first. Do not install CUDA, drivers, WSL, or large frameworks automatically.

If NVIDIA tooling exists, use `nvidia-smi`. For PyTorch, run a short diagnostic script that prints only the fields above. Do not dump the complete environment.

## Phase 3 — Reproducible test environment

Inspect the repository's actual dependency declarations and CI workflow. Do not invent a new dependency list.

- If a suitable project virtual environment already exists, use it.
- Otherwise, create a repository-local `.venv` only if it will not overwrite an existing directory.
- Install only the dependencies required by the relevant tests, following the repository's declared versions where possible.
- If dependency resolution would require a large download or a system-level change, stop and report the proposed action first.

Record exact commands and package versions.

## Phase 4 — Run existing tests before changing anything

Run the repository's relevant tests without modifying source code:

1. `python -m compileall models scripts tests`
2. `python -m pytest -q tests/test_mxfont_unicode_adapter.py`
3. `python -m pytest -q tests/test_mxfont_native_pairs.py`
4. Run the existing multimodal baseline tests only if their dependencies are available and doing so does not trigger model downloads or training.

Capture each command's exit code and concise output. Distinguish:
- PASS
- FAIL
- BLOCKED (missing dependency, unavailable hardware, missing data, etc.)
- NOT RUN

Do not report a test as passed merely because collection succeeded.

## Phase 5 — Inspect and verify adapter behavior

Read the adapter and tests. Verify these properties with executable tests:

1. **Shape compatibility:** the adapter accepts the documented MX-Font content-factor shape and Unicode ID batch shape.
2. **Zero-init identity:** with freshly initialized zero residual weights, the adapter output is numerically identical to the original content factors within a documented floating-point tolerance.
3. **Style isolation:** style factors and skip tensors are not modified; verify the actual API's intended pass-through behavior.
4. **Gradient path:** after deliberately opening the zero-initialized residual projection with small non-zero weights, a backward pass produces finite, non-zero gradients in the Unicode embedding and trainable adapter projection.
5. **Batch and device behavior:** test CPU first; test CUDA only if CUDA is genuinely available.
6. **Invalid inputs:** wrong dimensions, invalid IDs, and incompatible batch sizes fail clearly rather than silently producing corrupted output.

Do not change the model to force these properties. If the current API does not expose a property, report that limitation rather than inventing an interface.

## Phase 6 — Native-pair data checks

Run the existing native-pair tests. Then inspect the pair-building script and available small/local fixtures.

Check, where fixtures permit:

- Style examples come from the same font file but different character IDs.
- Content examples come from different font files but the same character ID.
- No pair crosses the declared train/validation/test split.
- Pair generation is deterministic for a fixed seed.
- Missing glyphs and duplicate samples are handled explicitly.
- The script does not fabricate component-decomposition labels.

Do not download a font corpus. If no suitable local fixture exists, report the exact missing input and leave this phase partially blocked.

## Phase 7 — Resource-bounded micro-test (only if safe)

Only after Phases 1–6 pass, determine whether a tiny local forward/backward or micro-training test is feasible.

Before running it, estimate and report:
- model and batch dimensions,
- expected memory use as far as it can be estimated,
- dataset source and size,
- expected duration.

Do not begin if it risks exhausting system memory/VRAM, requires downloading data, or needs unapproved system changes.

If safe, run only a minimal smoke test sufficient to establish that:
- a batch reaches the adapter,
- forward output is finite,
- loss is finite,
- backward completes,
- gradients are finite,
- one optimizer step completes if the existing training code supports it.

This is an integration smoke test, not evidence of improved glyph quality and not a full training run.

## Phase 8 — Comparative experiment readiness

Do not claim that Unicode conditioning improves MX-Font unless a valid controlled experiment has been run.

First inspect whether the repository has the required MX-Font upstream implementation, compatible weights, dataset, and component-decomposition labels. The upstream MX-Font training path may require decomposition supervision; do not replace it with invented labels.

If prerequisites are absent, write a precise blocker report. Do not improvise a new objective or start the three-way experiment.

The intended later comparison, once prerequisites are genuinely available, is:

A. Original MX-Font baseline.
B. MX-Font with the Unicode adapter frozen.
C. MX-Font with the Unicode adapter trainable.

All three must use identical data splits, evaluation samples, and comparable training budgets. Evaluate both glyph/content quality and preservation of font style. Report metrics and examples; training loss alone is insufficient.

## Phase 9 — Report

Create a local report at:

`reports/local-agent-verification-YYYY-MM-DD.md`

Also create a machine-readable summary:

`reports/local-agent-verification-YYYY-MM-DD.json`

Use the actual local date in the filenames. Do not commit or push these files.

The report must include:

- branch name and tested HEAD SHA,
- hardware/runtime inventory,
- exact commands executed,
- each test's PASS/FAIL/BLOCKED/NOT RUN status,
- key output and error excerpts,
- whether CUDA was used,
- whether any micro-test ran,
- any files changed (ideally none except the two reports),
- unresolved blockers,
- a clear conclusion separating code-level correctness from training/quality evidence.

The JSON should contain structured fields for branch, commit, hardware, environment, test results, micro-test status, blockers, and conclusion.

## Final response format

When finished, tell the user:

1. What ran successfully.
2. What failed or was blocked, with the actual reason.
3. Whether the local GPU was used.
4. Whether any training occurred (normally: no full training).
5. Where the two reports were saved.
6. The exact next prerequisite, if any.

Never describe the project as 100% training-ready unless the evidence actually supports that conclusion.


# Training-first execution addendum

This addendum supersedes the earlier test-only framing. The user's goal is to reach a genuine local training run, not to stop after unit tests. However, a real training run is permitted only when the actual model, training objective, and correctly paired training data exist.

## Verified starting facts from the repository at the time this plan was updated

- `models/mxfont_unicode_adapter.py` is an optional adapter, not a complete MX-Font training system.
- `docs/MXFONT_UNICODE_BRIDGE.md` explicitly states that the adapter is not wired into the MX-Font trainer.
- The native-pair builder produces pairing manifests only. It explicitly marks decomposition as missing and says its output is not directly trainable by the full upstream MX-Font trainer until reviewed Arabic decomposition/primals labels are supplied.
- Existing adapter tests use synthetic tensors. Even the gradient test only proves gradients can flow after manually opening zero-initialized projections; it does not train on real glyph images or demonstrate improved font generation.
- The pinned upstream MX-Font Generator/checkpoint/data pipeline must be located and verified before claiming end-to-end integration. Do not assume it exists in this repository or that a similarly named package is compatible.

## Required objective: advance toward actual training

After the initial machine inventory and repository inspection, do not spend the session merely expanding unit tests. Build a concrete training-readiness decision and proceed as follows:

### A. Locate the real MX-Font implementation

- Identify the exact upstream source revision used by this project.
- Determine whether the real Generator, factorization/defactorization path, dataset loader, training loop, loss functions, and checkpoint-loading code are available locally.
- If not present, report the exact missing source components and propose the smallest reproducible way to obtain the pinned upstream source. Do not silently clone arbitrary forks or use an unpinned latest version.
- Verify real tensor shapes by executing the real Generator on a real compatible batch, not only synthetic tensors.

### B. Audit training data

- Inventory available glyph images, font files, manifests, labels, splits, and licensing metadata.
- Verify Arabic coverage: isolated/initial/medial/final forms where applicable, ligatures such as lam-alef, combining marks/diacritics, and multi-codepoint sequences. Do not equate Unicode codepoint coverage with correct Arabic shaping.
- Verify every training sample's image, text/Unicode sequence, font identity, family identity, and split mapping.
- Ensure no family/font leakage between train, validation, and test.
- Determine whether the upstream decomposition/primals supervision is available and correct. Never synthesize or guess decomposition labels.
- Report actual counts and missing categories. Do not claim completeness from filenames alone.

### C. Decide whether a scientifically valid training objective exists

Preferred route: reproduce the pinned MX-Font objective with its required supervision and integrate the Unicode adapter at the documented content-factor location.

If the required decomposition labels or upstream trainer are missing:
- Do not run a fake MX-Font training job.
- Investigate whether a documented, technically valid alternative objective can train the adapter against real target glyph rasters while retaining MX-Font's style/content separation.
- Any alternative must specify exactly how style references, content references, target glyph, Unicode IDs, and held-out families are used; how leakage is prevented; and how style preservation and Arabic correctness are evaluated.
- Do not invent an objective ad hoc merely to produce a checkpoint. If no defensible objective can be justified from the actual available code/data, stop and report the precise blocker.

### D. Implement integration before training

If and only if A–C establish a valid route:
- Implement the smallest end-to-end integration on the experiment branch only.
- Recover Unicode IDs from the actual target text/codepoint mapping; never pass MX-Font dataset-local `trg_cids` as Unicode.
- Apply the adapter only to the intended batch-aggregated content factors, not style factors.
- Keep original MX-Font baseline code and checkpoint immutable.
- Add an executable end-to-end smoke test using a real batch and the actual Generator.
- Add a deterministic training configuration with explicit seeds, split manifests, batch size, checkpoint cadence, validation cadence, and early stopping.
- Add resume-from-checkpoint support and save optimizer/scheduler/RNG state.
- Record all configuration and data hashes with each run.

### E. Run a real but bounded training experiment

If hardware, real data, and objective are ready:
1. Run a baseline forward/validation pass with the unmodified MX-Font checkpoint.
2. Run a short genuine adapter-training experiment on the local machine using actual glyph images and the approved objective. This must perform optimizer steps and update adapter weights; a forward/backward smoke test alone is not training.
3. Evaluate on a held-out font-family validation set after each configured interval.
4. Save the best adapter checkpoint separately from the baseline.
5. Save loss curves, validation metrics, representative generated glyph images, and run metadata.
6. Confirm the saved checkpoint differs from initialization and that the weights actually changed.
7. Do not start a long/full run automatically. The bounded experiment should be sized to available VRAM/RAM and stop cleanly on resource pressure.

The first run should be a pilot, not a claim of model success. Report step count, wall time, peak memory, loss trends, validation results, and failure cases.

### F. If actual training cannot start

Do not substitute more synthetic tests and call the task complete. Produce a short blocker report that names the exact missing item(s), for example:
- pinned upstream MX-Font implementation,
- compatible pretrained baseline checkpoint,
- real glyph image corpus,
- reviewed decomposition labels,
- verified Unicode-to-target mapping,
- valid training objective,
- sufficient local compute.

Where possible, complete safe preparatory implementation work that does not fabricate data or labels. Then stop at the first hard blocker and clearly state what must be supplied or built before training can genuinely begin.

## Definition of success

This task is successful only if the local agent either:

1. completes a real bounded training run on actual glyph data with optimizer updates and produces a verifiable checkpoint plus held-out validation evidence; OR
2. proves training cannot honestly begin and provides a precise, evidence-backed blocker report plus the minimum concrete next action.

Passing unit tests, compiling files, building synthetic pairs, or creating a checkpoint with unchanged weights does NOT count as training.
