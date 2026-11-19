# Arabeyes binary audit results — 2026-11-19

## Verified acquisition

GitHub Actions run 44525849649 completed successfully:
https://github.com/snaiko/arabic-font-research-prep/actions/runs/44525849649

The workflow downloaded the Debian `fonts-arabeyes 2.1.orig.tar.xz` source archive and verified the published Debian MD5:
`abc5f9628f4df02c8c5fdec210e9f628`.

Computed archive SHA-256:
`8dae6ec07ab286dfb90bcc06fadc371112d2d7ea06f905668ef747b17a712135`.

The preserved artifact is `arabeyes-font-binaries-and-audit`:
https://github.com/snaiko/arabic-font-research-prep/actions/runs/44525849649/artifacts/14529888093

It contains the original verified archive, COPYING, README, 36 extracted TTF files, SHA-256 records, JSON audit, and 36 raster previews.

## Actual binary results

| Check | Result |
|---|---:|
| Font binaries inspected | 36 |
| Unique exact binary SHA-256 values | 36 |
| Fonts with Arabic-range Unicode cmap entries | 36 |
| Fonts with zero missing glyphs in the fixed Arabic HarfBuzz probe | 36 |
| Raster previews rendered | 36 |
| Archive published MD5 verified | Yes |

Arabic cmap coverage in these files ranged from 187 to 194 codepoints in the tested Arabic and presentation-form ranges. The fixed HarfBuzz probe was `سلام عليكم لا إله إلا الله`, shaped RTL with script Arab and language ar. All 36 fonts produced nonzero glyph IDs for that one probe.

**Important:** passing one shaping phrase is only a smoke test. It does not establish complete Arabic alphabet/diacritic coverage, correct spelling across the language, visual readability, calligraphic quality, or suitability for training.

## Strict normalized outline duplicate screen

A second local screen compared Arabic cmap glyph outlines across the 36 extracted binaries. It normalized point coordinates by each font's units-per-em, included contour endpoints and normalized horizontal metrics, and compared the resulting per-codepoint fingerprints.

Results:
- 36 distinct whole-font normalized Arabic-outline fingerprints.
- No pair was an exact whole-font outline duplicate under this strict fingerprint.
- 288 font pairs shared at least one exact normalized glyph outline.
- The largest shared-glyph count was 18 of 188 common Arabic codepoints (9.6%) for ae_Mashq-Bold and ae_Mashq.
- Most shared-outline overlap was only 1–3 glyphs per pair.

This is a strict exact-coordinate screen, not perceptual similarity or proof of independent design lineage. It can miss geometrically equivalent outlines whose point order, contour start point, decomposition, or drawing commands differ. It is sufficient to say that no exact whole-font duplicate was detected by this screen; it is not sufficient to certify every design as wholly independent.

## License evidence and training decision

The extracted upstream README states:
- GPL version 2;
- a special exception for embedding the font or unaltered portions in a document;
- Latin glyph ranges based on Free UCS Outline Fonts / FreeFont and credited to the Free Software Foundation.

The documented exception is specifically about embedding fonts in documents. It does not expressly grant ML training permission, and it does not expressly settle the status of trained model weights or generated fonts. The Latin glyph provenance also requires retaining the package's copyright and source notices.

Therefore:
- Technical candidate files: 36.
- Exact binary hashes verified: 36.
- AI/ML training-cleared Arabeyes files: **0**.
- Added to active training manifest: **0**.
- The OFL conditional manifest for the separate 52 Google Fonts files does not apply to these GPL+Font Exception assets.

## Corrected inventory distinction

A separate Debian Sources listing for the older `ttf-arabeyes 2.0-5` source exposed 39 TTF entries. The actually downloaded `fonts-arabeyes 2.1.orig.tar.xz` archive audited here contains 36 TTF binaries. These are different source revisions; do not treat the older 39-entry listing as the binary count of the 2.1 archive.

## Conclusion

The Arabeyes archive has now been downloaded, checksum-verified, extracted, and technically screened. This replaces the previous status of “download failed / no binary inspection.” It does **not** clear the GPL assets for ML training. Keep them in the candidate-only evidence artifact until explicit written permission or a reliable license interpretation covers training and distribution of the resulting model and fonts.


## Reproducible outline audit added

The exact-outline screen is now implemented as `scripts/audit_font_outline_duplicates.py` and integrated into `.github/workflows/arabeyes-candidate-audit.yml`. The workflow was rerun successfully in [run 44527813202](https://github.com/snaiko/arabic-font-research-prep/actions/runs/44527813202). Its refreshed artifact includes `outline_duplicate_audit.json` and the updated summary. The reproduced result is 36 unique whole-font fingerprints, zero exact whole-font duplicate groups, and 288 font pairs sharing at least one exact normalized glyph outline.
