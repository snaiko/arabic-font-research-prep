# OFL 1.1 AI font-training policy for this project

## Decision

The project may use the exact Google Fonts assets listed in the pinned evidence queue as **conditional ML training inputs** under SIL Open Font License 1.1, provided every generated font software output based on those sources is released under SIL OFL 1.1 and all normal OFL conditions are followed.

This policy is based on the official SIL OFL FAQ version 1.1-update8 (November 2026):
- Q1.25 says a font produced by an AI/ML system whose input or training data contains a source file from an OFL font project must be treated as a derivative font and may not be released under a different license without explicit permission from the corresponding authors.
- Q3.9 says AI-based font design tools may modify OFL sources, but any resulting font released based on that OFL source must remain under the OFL and include normal derivative-font notices and acknowledgements.

Official source: https://openfontlicense.org/ofl-faq/

## What this permits

- Use of the exact, hash-pinned SIL OFL 1.1 font files in the project training pipeline.
- Rendering and training on glyph images generated from those exact fonts, under this project's conservative interpretation that generated font outputs remain OFL.
- Publishing generated font files under SIL OFL 1.1, with source copyright notices, acknowledgements and license text preserved.
- Free distribution of the generated fonts by this project.

## Mandatory conditions

1. **Generated font files:** release every generated font based on these sources under SIL OFL 1.1. Do not release those font files under CC BY-NC, proprietary, or another license unless the relevant copyright holders give explicit written permission.
2. **Reserved Font Names:** generated fonts must use new primary family names and must not use any Reserved Font Name recorded in the per-family license evidence unless the corresponding copyright holder grants written permission.
3. **Notices:** preserve all applicable copyright statements and acknowledgements, and include the full OFL 1.1 license text with distributed generated font packages.
4. **Provenance:** retain exact source-file SHA-256, immutable source revision, license URL, license snapshot SHA-256, and family-level reserved-name/copyright evidence.
5. **Model weights:** this policy does not determine whether model weights are themselves Font Software or what license should govern them. Keep model-weight licensing separate. The project must not claim that this review settles the legal status of model weights.
6. **Other source families:** this approval does not cover Arabeyes GPL+Font Exception fonts, CC BY/CC BY-NC candidates, or any source not present in the pinned 52-file/20-family evidence queue.

## Important non-commercial distinction

SIL OFL 1.1 is **not** a NonCommercial license. The project may choose to distribute its own model and generated fonts for free and not sell them, but OFL does not prevent downstream users from using the generated fonts commercially, subject to OFL terms. OFL also prevents selling the font software by itself; it may be redistributed with software or in a larger bundle.

If the requirement is that **nobody** may use the generated fonts commercially, OFL is not suitable. The project would need explicit written permission from the source font copyright holders to apply a different license. This policy assumes the user's stated intention is that the project itself will remain free and will not sell the generated fonts.

## Current source evidence

- 52 exact font files across 20 families.
- 20 pinned family-level license snapshots.
- All 20 snapshots identify SIL OFL 1.1 and pass the automated clause-presence checks.
- The license audit found no text retrieval or integrity errors.
- Several families declare Reserved Font Names; these are recorded per file in the generated rights manifest.

## What this decision does not certify

- It is a project-level interpretation of official SIL guidance, not a court ruling or individualized legal advice.
- It does not certify visual quality, Arabic spelling, readability, calligraphic quality, or semantic glyph decomposition.
- It does not approve Arabeyes, CC BY-NC leads, or other external candidate fonts.
- It does not authorize model training on any source whose exact hash and license evidence do not match the active rights manifest.

## Reproducible manifest build

The CI workflow `.github/workflows/build-ofl-rights-manifest.yml` creates `data/manifests/font_rights.json` from:
- the exact published font corpus and per-file SHA-256 evidence;
- the immutable Google Fonts license URLs;
- the pinned OFL license text snapshots;
- this output-license policy.

It then runs `scripts/validate_font_rights_manifest.py` against the actual font binaries. The workflow artifact `conditional-ofl-font-rights-manifest` is the output to use for training once the workflow completes successfully.
