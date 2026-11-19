# Expanded Arabic font licensing scan — 2026-11-19

## Updated project target

The user confirms that the model and resulting font work are intended to remain free and noncommercial. The search is therefore no longer restricted to CC0/public-domain fonts.

The practical target is 20 distinct Arabic font families whose actual license permits the planned noncommercial research/training use, with redistribution/attribution/share-alike conditions recorded and followed. A free download label alone is not evidence of permission.

## Important Creative Commons guidance

Creative Commons' current AI-training guidance says:
- CC BY: preserve attribution.
- CC BY-SA: if adaptations/models or outputs are based on SA material and publicly shared, the guidance recommends applying the same or compatible CC license.
- CC BY-NC / CC BY-NC-SA: the copying/training stages and subsequent sharing of the trained model must remain noncommercial when the NC restriction applies.
- CC BY-ND / CC BY-NC-ND: exclude from a conservative training corpus.
- CC licenses apply only where copyright permission is required; copyright exceptions vary by jurisdiction.

Official sources:
- https://creativecommons.org/using-cc-licensed-works-for-ai-training-2/
- https://creativecommons.org/cc-license-guidance/
- https://creativecommons.org/licenses/by-nc/4.0/

This is guidance, not a legal determination for every jurisdiction or for every generated font. In particular, do not assume a noncommercial project automatically satisfies every license condition. Preserve attribution and license provenance for every asset.

## Candidate discovery — not yet admitted to corpus

### CC0 / public-domain candidates from the earlier scan
1. MatrixType — GGBotNet; creator page states CC0 1.0 and lists Arabic support.
2. Bitsy Font With Arabic — AlexClay; creator page states CC0 1.0.
3. Arabic Pixel 1 — AlexClay; listed in FontStruct's CC0 Arabic results.

Earlier duplicate exclusions remain:
- Arabic Pixel 2 is a clone of Arabic Pixel 1.
- O_Roxo's Arabic pixel font is a clone of Bitsy Font With Arabic.

### Explicit CC BY 4.0 candidates
4. Arabixel Basic — ArabianDev; Arabic pixel font; CC BY 4.0.
5. Arabixel Adventure — ArabianDev; Arabic pixel font; CC BY 4.0.
6. Arabixel Antique — ArabianDev; Arabic pixel font; CC BY 4.0.
7. Ghoulam Regular 1.0 — Imad AlFil / mloukhiyye; CC BY 4.0; creator says it is incomplete and lacks diacritics and most symbols.

Sources:
- https://arabiandev.itch.io/arabixel-basic-font
- https://arabiandev.itch.io/arabixel-adventure-font
- https://arabiandev.itch.io/arabixel-antique-font
- https://mloukhiyye.itch.io/ghoulam-arabic-pixel-art-font-version-1

### CC BY-SA candidate
8. arabic lite — ChiefCommander; Font Library lists CC-BY-SA. Its page reports only 89% Arabic coverage and missing several letters/marks, so it is a low-coverage candidate pending binary inspection.
Source: https://fontlibrary.org/font/arabic-lite

### GNU GPL candidates — legal compatibility requires checking the exact packaged license and any font exception
The Font Library Arabic-language catalog identifies the following families as Arabic-capable and lists GNU GPL:
9. KacstDigital — KACST.
10. Hor — Alawi Hashim Bafageeh / Arabeyes.
11. Shado — Future Soft Egypt / Arabeyes.
12. AlYarmook — Fazlur Rahman Quraishi / Arabeyes.
13. Nada — MAK Alagha / Arabeyes.

Sources:
- https://fontlibrary.org/en/font/kacstdigital
- https://fontlibrary.org/en/font/hor
- https://fontlibrary.org/en/font/shado
- https://fontlibrary.org/en/font/alyarmook
- https://fontlibrary.org/en/font/nada

Caution: the Font Library listing for UKIJ Bom says GNU GPL, while its description says the Uyghur Computer Science Association releases its fonts under OFL and LGPL. Because of this metadata conflict, UKIJ Bom is not counted as a qualified candidate until the original archive's license is inspected:
- https://fontlibrary.org/en/font/ukij-bom

Other Arabic catalog entries (e.g. KacstBook, UKIJ families, Nada variants) are not counted until each exact page and downloadable archive license is checked. Multiple styles/weights within one family count once.

## Count and status

- 13 distinct family/product names currently surfaced across the candidate groups above (3 CC0, 4 CC BY, 1 CC BY-SA, 5 GPL-listed).
- 0 candidates downloaded and verified by actual binary hash, cmap, shaping, rendering, duplicate-lineage, and archived license evidence in this expanded scan.
- Target: 20 qualified families.
- Replacement corpus: NOT READY.
- Existing 20-family OFL corpus: NOT deleted and remains excluded from training under the fail-closed rights manifest.

## Required admission gates

A discovered name is not a verified training asset. Before admission:
1. Download only from creator-controlled or authoritative upstream sources.
2. Archive the exact font binary, source URL, retrieval date, license text/URL, copyright/attribution text, and SHA-256.
3. Inspect the exact package license; resolve conflicting catalog metadata and font-specific exceptions.
4. Inspect cmap coverage for Arabic letters, marks, numerals, and required codepoints.
5. Run HarfBuzz contextual shaping tests and raster rendering tests.
6. Compare outlines/hashes and source lineage to detect clones and duplicate families.
7. Record license obligations for dataset distribution, model release, and generated-font release. Do not combine license categories into a single output license without a compatibility review.
8. Keep all unverified assets out of the training-eligible manifest.

No training was started. No old corpus assets were deleted.
