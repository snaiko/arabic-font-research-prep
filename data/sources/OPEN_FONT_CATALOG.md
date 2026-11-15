# Arabic Font Corpus — Curated OFL Sources

This is a source catalogue, not a claim that binaries have already been downloaded. The collector downloads font files and per-family license/metadata from the official Google Fonts repository, then records SHA-256 hashes.

## Pilot families

| Family slug | Style coverage | Official source |
|---|---|---|
| amiri | Classical Naskh | https://github.com/google/fonts/tree/main/ofl/amiri |
| noto-naskh-arabic | Naskh | https://github.com/google/fonts/tree/main/ofl/noto-naskh-arabic |
| noto-sans-arabic | Sans | https://github.com/google/fonts/tree/main/ofl/noto-sans-arabic |
| noto-kufi-arabic | Kufi / sans | https://github.com/google/fonts/tree/main/ofl/noto-kufi-arabic |
| scheherazade-new | Naskh, extended Arabic-script coverage | https://github.com/google/fonts/tree/main/ofl/scheherazade-new |
| lateef | Arabic-script text | https://github.com/google/fonts/tree/main/ofl/lateef |
| cairo | Sans / display | https://github.com/google/fonts/tree/main/ofl/cairo |
| tajawal | Geometric sans | https://github.com/google/fonts/tree/main/ofl/tajawal |
| almarai | Sans | https://github.com/google/fonts/tree/main/ofl/almarai |
| ibm-plex-sans-arabic | Sans | https://github.com/google/fonts/tree/main/ofl/ibm-plex-sans-arabic |
| mada | Sans | https://github.com/google/fonts/tree/main/ofl/mada |
| readex-pro | Sans | https://github.com/google/fonts/tree/main/ofl/readex-pro |
| reem-kufi | Kufi / display | https://github.com/google/fonts/tree/main/ofl/reem-kufi |
| el-messiri | Display / sans | https://github.com/google/fonts/tree/main/ofl/el-messiri |
| changa | Display | https://github.com/google/fonts/tree/main/ofl/changa |
| baloo-bhaijaan-2 | Rounded display | https://github.com/google/fonts/tree/main/ofl/baloo-bhaijaan-2 |
| harmattan | Naskh / text | https://github.com/google/fonts/tree/main/ofl/harmattan |
| aref-ruqaa | Ruqaa-inspired display | https://github.com/google/fonts/tree/main/ofl/aref-ruqaa |
| markazi-text | Text serif | https://github.com/google/fonts/tree/main/ofl/markazi-text |
| rubik | Sans; Arabic subset included | https://github.com/google/fonts/tree/main/ofl/rubik |

## License policy

The SIL Open Font License 1.1 generally permits use, modification, and redistribution of font software subject to its conditions, including reserved font names and license retention. Keep each family's license file with its files and review it before redistribution or model release.

Official references:
- Google Fonts repository and per-family license files: https://github.com/google/fonts
- Google Fonts repository guide: https://googlefonts.github.io/gf-guide/googlefonts.html
- Noto Arabic project license: https://github.com/notofonts/arabic
- Amiri project: https://github.com/aliftype/amiri

## Admission gates

A downloaded file remains a candidate until its exact family license is checked, upstream commit and SHA-256 are recorded, cmap coverage is inspected, and HarfBuzz shaping tests pass. Keep all files from one family in a single dataset split to prevent leakage. The collector refuses missing/non-OFL licenses.