# Arabic glyph training dataset

## Build

The `Build Arabic glyph training dataset` GitHub Actions workflow downloads the existing
`arabic-font-corpus-v1` release asset. It does not recollect or duplicate the original font
files in Git history.

Run locally after extracting the corpus ZIP into the repository root:

```bash
python -m pip install -r requirements-glyph-dataset.txt
python scripts/build_arabic_glyph_dataset.py \
  --fonts data/raw_fonts \
  --validation data/validation/font_validation.jsonl \
  --output data/training_samples \
  --seed 42
```

Pillow must have libraqm enabled. The script refuses to render if RAQM is unavailable,
because Arabic right-to-left shaping must not be approximated by reversing strings.

## Output

- `images/`: grayscale PNG renders, grouped by family and font-file SHA-256.
- `samples.jsonl`: complete sample metadata.
- `splits/train.jsonl`, `validation.jsonl`, `test.jsonl`: manifests for each split.
- `family_splits.json`: deterministic family-to-split assignment.
- `dataset_summary.json`: renderer settings, counts, and known limitations.

Only fonts whose matching technical-validation record has status `pass` are used.
Splits are assigned by font family, not by image, to prevent the same family from
appearing in both training and evaluation.

## Sample types

Each accepted font produces four contextual sequences for every core Arabic codepoint:
isolated, initial-context, medial-context, and final-context. Eight common Arabic phrases
are also rendered per font. The contextual labels describe the sequence supplied to
RAQM; they do not claim that every letter supports all four joining forms. HarfBuzz/RAQM
applies the font's actual OpenType shaping behavior.

## Important limitations

This is the first reproducible raster-data milestone, not a trained model. Images are
full-line contextual renders with a logical target index; they are not yet isolated
target-glyph crops. The output has not undergone human visual-quality review, and
ligature-, diacritic-, and style-specific annotation still needs dedicated evaluation.
The source font licenses and validation records remain in the original corpus release.
