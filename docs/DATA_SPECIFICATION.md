# Arabic Font Corpus and Glyph Data Specification

## 1. Two linked datasets

### Font-level manifest

One JSON object per source font file. Required fields:

- `font_id`: stable unique identifier.
- `family`, `style`, `weight`: names/metadata as supplied by the font.
- `file_name`: local filename; do not commit the font binary by default.
- `source_url`: direct project/source page, not an invented download URL.
- `license`: exact license identifier/text reference for this version.
- `license_url`: license text location.
- `version`: font version when available.
- `sha256`: checksum of the exact file.
- `split`: `train`, `validation`, or `test`; assign by family.
- `script_coverage`: scripts/code-point ranges actually verified.
- `notes`: optional caveats.

### Glyph-level manifest

One record per rendered glyph sample/context. Include `font_id`, Unicode scalar `codepoint`, `character`, `form`, `language`, `joining_type`, `sample_path`, `sample_sha256`, `renderer`, `renderer_version`, `render_size`, `baseline`, `advance_width`, `left_side_bearing`, and the shaping text/context used to obtain the sample.

Use one of `isol`, `init`, `medi`, `fina`, `mark`, `ligature`, or `not_applicable` for the form label. The label must reflect the actual shaped glyph, not a guess from the character's word position.

## 2. Contextual forms are not four mandatory images per letter

Arabic contextual forms are determined by joining behavior and neighboring characters. Some letters connect only to the preceding side; some are dual-joining; some are non-joining; marks are not ordinary base letters. Generate contexts with a shaping engine and store the exact input sequence and resulting glyph mapping.

At minimum, test:
- isolated character,
- join to a dual-joining character on the right,
- join to a dual-joining character on the left,
- joins on both sides,
- blocked joins around right-joining/non-joining characters,
- ZWJ and ZWNJ behavior where relevant,
- combining marks and mark attachment,
- Arabic and any additional supported language/script separately.

The renderer/shaper must be pinned (HarfBuzz + FreeType versions, font file checksum, direction, script, language, features, ppem, and raster settings).

## 3. Split policy

Split by normalized font family. Every weight/style file from a family must stay in one split. A recommended first split is 80/10/10 by family, but use deterministic grouped splitting and inspect balance. If the corpus is small, use grouped cross-validation and state that results are preliminary.

Never split individual glyph images randomly across train and test: this leaks the same design system into evaluation.

## 4. Quality controls

Reject or quarantine samples when:
- the code point is unsupported or rendered as .notdef,
- shaping output does not match the expected Unicode sequence,
- the glyph is clipped or empty,
- baseline/advance metadata is missing,
- the font license/source cannot be verified,
- duplicate files have conflicting metadata,
- the rasterization settings differ without being recorded.

Deduplicate by SHA-256. Keep original font binaries outside Git unless the license and repository policy explicitly allow redistribution.

## 5. Coverage phases

1. Arabic core letters and common combining marks.
2. Arabic-Indic digits, punctuation, and common symbols.
3. Persian, Urdu, and other Arabic-script language coverage as separate language-specific evaluations.
4. Ligatures, mark combinations, and stylistic alternates only after the basic pipeline is stable.

Do not assume Arabic-language support automatically means support for all Arabic-script languages.

## 6. Suggested first pilot

Begin with at least 8–12 distinct, permissively licensed families if available, with multiple design categories (Naskh, Naskh-like, Kufi/geometric, sans, display). This is a pilot target, not a claim that such a corpus is already collected. Expand only after the renderer, manifests, and family split pass validation.
