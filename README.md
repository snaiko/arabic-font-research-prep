# Arabic Few-Shot Font Research

Research preparation for an Arabic font-generation system that learns a visual style from a small set of reference glyphs and predicts other glyphs while preserving Arabic character identity, joining behavior, and font validity.

> **Status:** research specification and data-preparation scaffolding. This repository does not yet contain a collected font corpus, trained Arabic checkpoint, or verified generation results.

## Research principle

A single reference glyph does not uniquely determine a typeface. The system must accept multiple references when available, estimate uncertainty, and avoid claiming exact recovery of an original font.

## What is included

- [Model architecture](docs/MODEL_ARCHITECTURE.md): staged MX-Font-based design and Arabic-specific modules.
- [Data specification](docs/DATA_SPECIFICATION.md): corpus schema, glyph labels, contextual forms, and quality controls.
- [Open-font sources](data/sources/OPEN_FONT_CATALOG.md): candidate families and licensing checks.
- [Training and evaluation](docs/TRAINING_EVALUATION.md): split policy, losses, baselines, and acceptance gates.
- [Model configuration](configs/model.yaml) and [data configuration](configs/data.yaml).
- JSONL manifest templates under `data/manifests/`.
- A standard-library manifest validator: `python scripts/validate_manifest.py data/manifests/fonts.template.jsonl`.
- Arabic font technical validator: `python scripts/validate_arabic_fonts.py --input data/raw_fonts --output data/validation` (requires FontTools and uharfbuzz; see [validation guide](docs/FONT_VALIDATION.md)).

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
