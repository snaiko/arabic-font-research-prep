# Arabic font replacement scan — 2026-11-19

## Request and acceptance rule

The requested replacement target is 20 distinct Arabic-capable font families with no copyright restrictions for model training. For the strict interpretation of "without rights", this scan prioritizes an explicit CC0 1.0 / public-domain dedication attached by the creator to the actual downloadable font. A page saying only "free download" or "free for commercial use" is not sufficient.

A font family is counted once. Clones, revisions, weights, and alternate formats are not counted as independent families. Arabic coverage must be checked from the actual font cmap and shaping tests before corpus admission.

## Verified candidates found

| Candidate | Creator / source | Published license evidence | Arabic evidence | Decision |
|---|---|---|---|---|
| MatrixType | GGBotNet, itch.io | CC0 1.0 explicitly stated on the font page | Explicitly lists Arabic among 16 supported languages; 291 glyphs; 4 styles | Candidate; download and technical validation still required |
| Bitsy Font With Arabic | AlexClay, FontStruct | CC0 1.0 explicitly stated on the download page | FontStruct entry is specifically named "With Arabic" | Candidate; download and technical validation still required |
| Arabic Pixel 1 | AlexClay, FontStruct | Listed in FontStruct's CC0-filtered Arabic results | Explicit Arabic tag | Candidate; download and technical validation still required |

## Duplicate / derivative entries — not counted

- Arabic Pixel 2 is explicitly described by FontStruct as a clone of Arabic Pixel 1.
- "Arabic pixel font" by O_Roxo is explicitly described as a clone of Bitsy Font With Arabic.
- These are not counted as independent source families.

## Additional permissive candidates — not CC0

The following Arabic-only pixel fonts by ArabianDev are published under CC BY 4.0, not CC0:
- Arabixel Basic
- Arabixel Adventure
- Arabixel Antique

They permit sharing and adaptation, including commercial use, with attribution. They are not counted toward the strict CC0 target and must retain attribution/license metadata if considered for a separate CC-BY corpus.

## Important license finding

The SIL Open Font License FAQ states that when OFL font source files are included in AI/ML training to create a font, the resulting font should be considered derivative and remain under OFL; it distinguishes ordinary AI graphic output from generating a font. This is why simply replacing the existing Google Fonts families with other OFL families would not satisfy a strict no-rights-restrictions requirement for a model intended to generate fonts.

## Current result

- Target: 20 distinct CC0/public-domain Arabic font families.
- Independently identifiable CC0 candidates from the sources checked: 3.
- Confirmed independent candidates downloaded, cmap-checked, HarfBuzz-tested, and added to the corpus: 0.
- CC-BY alternatives identified separately: 3 family members/styles from one creator.
- Replacement corpus readiness: NOT READY.

## Repository safety decision

The existing 20-family corpus has NOT been deleted. Deleting the current source corpus before a verified replacement exists would leave the project with no validated baseline, while still failing to produce 20 lawful replacements. The existing corpus remains excluded from ML training by the fail-closed rights manifest (zero approved font files).

Next automated step: obtain the candidate font archives from their creator-controlled pages, preserve the license/attribution files and exact source URLs, deduplicate by design lineage, then run cmap coverage, Unicode shaping, image generation, integrity audits, and per-file license manifest generation. Do not promote a candidate to training-eligible merely because its download page labels it CC0.
