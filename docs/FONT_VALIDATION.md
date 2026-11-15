# Arabic font technical validation

This stage validates **local font binaries** after collection. It does not download fonts and does not upload font binaries.

## 1. Install

From the repository root:

```bash
python -m pip install -r requirements-font-validation.txt
```

Python 3.10 or newer is recommended. HarfBuzz shaping is performed through `uharfbuzz`; FontTools inspects OpenType tables and Unicode cmaps.

## 2. Collect a small pilot

```bash
python scripts/collect_google_fonts.py --families amiri,noto-naskh-arabic,cairo,tajawal --output data/raw_fonts
```

The collector pins the Google Fonts source revision and records source/license metadata and SHA-256. It labels downloads `downloaded_unvalidated`.

## 3. Run technical validation

```bash
python scripts/validate_arabic_fonts.py --input data/raw_fonts --output data/validation
```

For a strict CI/local gate:

```bash
python scripts/validate_arabic_fonts.py --input data/raw_fonts --output data/validation --strict
```

Outputs:
- `font_validation.jsonl`: one detailed record per font file.
- `validation_report.json`: aggregate counts and pass criteria.

The validator checks:
- font parsing and basic metadata;
- Unicode cmap coverage for the core Arabic codepoints U+0621–U+064A;
- extended Arabic-script coverage separately (reported, not required for the core pass);
- presence of GSUB and GPOS tables;
- variable-font axes from fvar;
- right-to-left HarfBuzz shaping for basic joining, lam-alef, diacritics, sentence, and Persian-extension samples;
- SHA-256 and nearby license-file path.

## 4. Interpret statuses

- `pass`: core Arabic cmap is complete and every HarfBuzz sample produced glyphs without .notdef.
- `fail`: a font is malformed, lacks core Arabic characters, or produced .notdef in a shaping sample.
- `needs_shaping_test`: cmap passed but HarfBuzz was unavailable, so shaping remains unverified.

A pass is only a technical screening result. It does **not** certify the font's license, visual quality, glyph correctness, or suitability for a specific script/style. License review remains a separate gate. Do not mix Naskh, Nastaliq, Kufi, and regional Arabic-script styles into one undifferentiated evaluation pool.

## 5. Dataset handling

Do not commit raw TTF/OTF files or generated glyph images to this repository. Keep binaries in local or controlled storage. Share only metadata/manifests/reports whose redistribution is permitted by the exact font license. Preserve each font's license file alongside the local binary.
