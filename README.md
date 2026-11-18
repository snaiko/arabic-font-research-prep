# Arabic Few-Shot Font Research

Research preparation for an Arabic font-generation system that learns a visual style from a small set of reference glyphs and predicts other glyphs while preserving Arabic character identity, joining behavior, and font validity.

> **Status:** research specification plus reproducible font-corpus and raster-dataset preparation. No trained Arabic checkpoint or verified generation results are included.

## Research principle

A single reference glyph does not uniquely determine a typeface. The system must accept multiple references when available, estimate uncertainty, and avoid claiming exact recovery of an original font.

## What is included

- [Model architecture](docs/MODEL_ARCHITECTURE.md): staged MX-Font-based design and Arabic-specific modules.
- [Unified dual-mode specification](docs/DUAL_MODE_MODEL_SPEC.md): image, prompt, and hybrid routes sharing one generator.
- [Prompt and geometry dataset plan](docs/PROMPT_AND_GEOMETRY_DATASET.md): paired descriptions, measurable attributes, and leakage controls.
- [Pretraining completion plan](docs/PRETRAINING_COMPLETION_PLAN.md), [AI agent execution contract](docs/AI_AGENT_EXECUTION_SPEC.md), and [initial readiness report](reports/PRETRAINING_READINESS.md): mandatory work packages, current blockers, and stop conditions.
- JSON Schemas under `schemas/` for style records, source licensing, and readiness reports.
- [Data specification](docs/DATA_SPECIFICATION.md): corpus schema, glyph labels, contextual forms, and quality controls.
- [Open-font sources](data/sources/OPEN_FONT_CATALOG.md): candidate families and licensing checks.
- [Training and evaluation](docs/TRAINING_EVALUATION.md): split policy, losses, baselines, and acceptance gates.
- [Model configuration](configs/model.yaml) and [data configuration](configs/data.yaml).
- JSONL manifest templates under `data/manifests/`.
- A standard-library manifest validator: `python scripts/validate_manifest.py data/manifests/fonts.template.jsonl`.
- Arabic font technical validator: `python scripts/validate_arabic_fonts.py --input data/raw_fonts --output data/validation` (requires FontTools and uharfbuzz; see [validation guide](docs/FONT_VALIDATION.md)).
- A GitHub Actions workflow to collect, validate, and publish the binary font corpus as a GitHub Release asset (see [publishing guide](docs/FONT_CORPUS_RELEASE.md)).
- Reproducible Arabic raster-sample builder: `python scripts/build_arabic_glyph_dataset.py --fonts data/raw_fonts --validation data/validation/font_validation.jsonl --output data/training_samples` (requires Pillow with RAQM; see [dataset guide](docs/ARABIC_GLYPH_DATASET.md)).
- Automated GitHub Actions workflow downloads the existing font-corpus Release, renders contextual Arabic glyph and phrase samples, creates family-safe train/validation/test splits, and publishes a separate dataset Release.

## Recommended first milestone

1. Collect a small, legally usable pilot corpus from distinct font families.
2. Record source, exact license, version, SHA-256, metadata, and character coverage for every file.
3. Run the cmap/OpenType/HarfBuzz screening described in [FONT_VALIDATION.md](docs/FONT_VALIDATION.md), then render glyphs through a pinned HarfBuzz/FreeType pipeline and preserve the renderer configuration.
4. Establish a baseline with the upstream MX-Font implementation before adding Arabic-specific modules.
5. Evaluate on font families never seen during training.

## Important distinction

MX-Font is a few-shot **glyph-image generation** model. It is not by itself an Arabic text shaper, SVG editor, or TTF/OTF compiler. Arabic shaping and font packaging are separate stages and must be tested independently.

## License and data policy

Do not commit commercial fonts, unlicensed fonts, or raw font binaries to this repository. Keep source font files in storage whose access and license terms are known. Commit manifests and derived metadata only when their licenses permit it. Check the exact license attached to every downloaded font version; a family name alone is not proof of permission.

## Unified image + prompt model

The intended model has reference-image, text-prompt, and optional hybrid conditioning routes. All routes must share one style/geometry latent space and one Arabic-aware generator. See [the dual-mode model specification](docs/DUAL_MODE_MODEL_SPEC.md), [the structured style schema](docs/STYLE_DESCRIPTION_SCHEMA.md), and [the pretraining completion plan](docs/PRETRAINING_COMPLETION_PLAN.md).

## Pretraining is deliberately gated

The repository is not yet training-ready. The local AI agent must complete the data adapter, Arabic cluster-aware crops, prompt/geometry supervision, both conditioning encoders, shared generator paths, tests, and the readiness report. Follow [the AI agent execution contract](docs/AI_AGENT_EXECUTION_SPEC.md). Do not begin a long training run until every gate passes and the user explicitly approves it.

## Windows local AI-agent handoff

This repository now includes a Windows preflight launcher and a handoff specification for a separate local AI agent:

- Run `START_LOCAL_TRAINING.bat` on the Windows computer.
- It invokes `scripts/preflight_local_training.py`, detects available system memory and (when installed) PyTorch/CUDA GPU details, downloads the published raster dataset if needed, and writes `reports/local/machine_preflight.json`.
- Follow `LOCAL_AI_AGENT_GUIDE.md` for the required implementation and validation work before training.

**Important:** the launcher does not start training. The current dataset consists of full-line contextual renders, not verified target-glyph crops, and this repository does not yet include an executable MX-Font training implementation. The preflight therefore marks training as blocked. The local AI agent must implement and test the dataset adapter and baseline first, inspect the detected hardware, then request approval before a long training run. Machine reports and private checkpoints must not be uploaded publicly without permission.

