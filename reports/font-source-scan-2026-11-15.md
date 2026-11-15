# Official Arabic Font Source Scan — 2026-11-15

Scope: official upstream project repositories and release pages. This report records licensing evidence and technical caveats; it does not claim that font binaries were downloaded, inspected, or admitted to the training corpus.

## Verified license evidence (source-level; binaries still require validation)

| Family | Official source | License evidence | Revision/version evidence | Arabic coverage / formats | Notes |
|---|---|---|---|---|---|
| Noto Arabic family (Noto Naskh Arabic, Noto Sans Arabic, Noto Kufi Arabic and UI variants) | https://github.com/notofonts/arabic | Repository states SIL OFL 1.1; OFL.txt present | Release page lists NotoNaskhArabic-v2.021; other family tags listed there | Arabic-script family; TTF/OTF build outputs must be checked per release | Strong candidate. Preserve repo license and release-specific notices. |
| Scheherazade New | https://github.com/silnrsi/font-scheherazade | OFL.txt and OFL-FAQ.txt in official repository | Release page lists v4.500 (commit shown as 056c6cc) | General-purpose Naskh; aims to cover most Unicode 14 Arabic blocks except Presentation Forms; source/build and release font files | Strong candidate. Check exact release assets and license file in the downloaded release. |
| Lateef | https://github.com/silnrsi/font-lateef | OFL.txt and OFL-FAQ.txt in official repository | Official project repository; pin release/tag at collection time | Extended Arabic script, designed for Sindhi and related languages; TTF/OTF release assets to inspect | Strong candidate, but language coverage differs from standard Arabic-only fonts. |
| Harmattan | https://github.com/silnrsi/font-harmattan | Official Google Fonts OFL.txt explicitly identifies SIL OFL 1.1 | Google Fonts OFL file latest commit shown as 2025-09-05; version 4.400 | Arabic script for West African languages; inspect release formats | Strong candidate. Reserved Font Names include Harmattan and SIL; modified font must not retain reserved primary name. |
| Amiri | https://github.com/aliftype/amiri | Official README says Open Font License; repository contains OFL.txt | README says v1 reached mature status in 2022; pin current commit/tag during collection | Classical Arabic Naskh; TTF build target documented | Strong candidate. Confirm exact checked-out OFL.txt and font binary version. |
| Cairo | https://github.com/Gue3bara/Cairo | Official OFL.txt explicitly identifies SIL OFL 1.1 | Google Fonts metadata records upstream commit 73d16933c6a0f341c27a69e401da83dcb0d53114 | Google Fonts metadata identifies Arabic, Latin and Latin-ext subsets; variable TTF | Strong candidate. Pin upstream commit, not only branch name. |
| Tajawal | https://github.com/googlefonts/tajawal | Official OFL.txt explicitly identifies SIL OFL 1.1 | Upstream repository archived 2026-04-19 | Modern Arabic sans; repo includes font files and source | License evidence is clear; archive status means maintenance is inactive. Check exact files and reserved names. |

## Candidates requiring an additional license/technical pass

| Family | Official source | What is known | What remains |
|---|---|---|---|
| Alkalami | https://github.com/silnrsi/font-alkalami | Official SIL project for Kano-region Arabic-based writing; repository contains OFL.txt | Verify exact license version and inspect target release assets; limited regional character coverage. |
| Ruwudu | https://github.com/silnrsi/font-ruwudu | Official SIL project for Rubutun Kano; repository contains OFL.txt | Verify exact license version and inspect target release assets; limited regional character coverage. |
| Awami Nastaliq | https://github.com/silnrsi/font-awami | Official SIL project; repository contains OFL.txt; Nastaliq design | Do not add to standard OpenType training pool yet: project documentation describes Graphite-only behavior, while a newer OpenType tech-preview release is explicitly experimental. Decide on a separate Nastaliq/Graphite track after renderer tests. |
| IBM Plex Sans Arabic | https://github.com/IBM/plex | Official IBM repository lists a dedicated Arabic package and OFL resources | Verify the exact Arabic package's own license file, Arabic cmap, release version and formats before admission. |

## Excluded from the verified corpus

No family was rejected solely for being unfamiliar. Any download without its own matching upstream license, exact version and traceable source remains excluded from training until resolved. Do not treat third-party font mirrors, CSS subsets or repackaged binaries as the authoritative licensing source.

## Important license conditions

OFL 1.1 permits use, study, modification and redistribution subject to its conditions. Do not sell the font software by itself; preserve copyright and license notices; respect Reserved Font Names; modified font software must remain under OFL 1.1. These font-software conditions do not automatically determine the license of model weights or generated outputs; assess those separately.

## Dataset admission checklist

For every downloaded file, preserve the exact license and copyright notices; record upstream repository, tag/commit, filename, format, file size and SHA-256; inspect name table and cmap; render the target Arabic code-point inventory; test shaping with HarfBuzz for isolated/initial/medial/final forms, lam-alef, marks, ligatures and mixed direction; then split by font family so variants from one family cannot leak across train/validation/test.

## Sources consulted

- https://github.com/notofonts/arabic
- https://github.com/notofonts/arabic/releases
- https://github.com/silnrsi/font-scheherazade
- https://github.com/silnrsi/font-scheherazade/releases
- https://github.com/silnrsi/font-lateef
- https://github.com/silnrsi/font-harmattan
- https://github.com/aliftype/amiri
- https://github.com/Gue3bara/Cairo
- https://github.com/googlefonts/tajawal
- https://github.com/silnrsi/font-alkalami
- https://github.com/silnrsi/font-ruwudu
- https://github.com/silnrsi/font-awami
- https://github.com/IBM/plex
