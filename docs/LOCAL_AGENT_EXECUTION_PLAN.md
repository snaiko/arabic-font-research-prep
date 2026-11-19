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
