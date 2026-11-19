# Arabic Script and Glyph Visual System v2

## 1. Scope and evidence hierarchy

This project now separates three independent layers:

1. **Unicode script metadata** — code point identity, general category, Script=Arabic, Joining_Type and Joining_Group. These are normative UCD facts.
2. **Shaping outcome** — the glyph ID, cluster mapping, substitutions, positioning, and actual contextual form produced by a specific shaping engine, font, language, direction, and feature set.
3. **Visual decomposition** — body, dots, hamza, marks, counters, joins, strokes, and ornaments on one specific rendered glyph instance. These are annotation observations, not universal facts about a letter.

Do not infer layer 2 from the character's index in a word. Do not infer layer 3 from Joining_Group or schematic names.

## 2. Complete Unicode registry generation

Generate the pinned Unicode 17.0 Arabic-script registry:

```bash
python scripts/import_unicode_arabic_registry.py --download
```

Inputs are downloaded from the official Unicode 17.0 UCD:
- `UnicodeData.txt` — names and General_Category.
- `Scripts.txt` — Script=Arabic membership.
- `DerivedJoiningType.txt` — complete Joining_Type including transparent marks.
- `ArabicShaping.txt` — explicit Joining_Group and descriptive schematic names.

The generated file is `data/arabic_script_registry_v2.json`. SHA-256 hashes of all four source files are embedded. The importer does not silently use the Python runtime's potentially older Unicode database.

The v1 hand-curated core registry remains a readable starter set; v2 is the comprehensive Unicode Script=Arabic registry. Persian, Urdu and other languages use Arabic script and are included as script characters, but language-specific orthographic inventories and fonts must be tagged separately in training examples.

## 3. Joining constraints are not actual glyph forms

Possible forms from Joining_Type:
- R: isolated, final.
- L: isolated, initial.
- D: isolated, initial, medial, final.
- U: isolated.
- C (Join_Causing) and T (Transparent): not ordinary base-letter form labels.

These are structural constraints only. The actual glyph form and cluster must be obtained by shaping the complete logical-order string with a pinned HarfBuzz version and exact font. Record font hash, glyph ID, cluster, script, language, direction, features, and renderer versions. Preserve the original Unicode sequence. Do not reverse the string manually.

Include shaping regression cases for:
- all four contextual forms of representative dual-joining letters;
- right-joining letters adjacent to dual-joining letters;
- transparent harakat between joining letters;
- lam-alef and hamza/maddah variants;
- ZWJ and ZWNJ;
- tatweel;
- shadda plus vowel marks and Qur'anic marks;
- mixed Arabic/Latin/digits and punctuation.

Ligatures are multi-codepoint clusters. Never label a lam-alef ligature as a single ordinary letter crop. Marks may be reordered for rendering according to UAX #53; never rewrite the stored source text to match display order.

## 4. Visual annotation ontology (per glyph instance)

Coordinates are normalized to [0,1] against the exact rendered image. Polygon regions may overlap. A component may consist of multiple polygons; do not force a disconnected body or dot cluster into one contiguous mask.

- `body`: main letter skeleton as visible in this font and context.
- `dot`: one visible dot region; annotate dots individually, even when grouped.
- `hamza`: visible hamza sign when it is an independently identifiable region.
- `diacritic`: vowel/tanwin/shadda/sukun/maddah and other combining marks.
- `other_mark`: Quranic, annotation, or script-specific marks not covered above.
- `counter`: enclosed negative-space region; geometry is the contour/area, not a filled ink component.
- `join_region`: connection/overlap zone between adjacent glyph bodies.
- `stroke_segment`: optional path segment for topology or stroke-level research.
- `ornament`: stylistic extension not needed for character identity.
- `uncertain`: ambiguous region; preserve uncertainty instead of guessing.

Relations describe topology (attached_to, inside, joins, overlaps, part_of, above, below). A dot pattern is not a universal letter skeleton: dot count, shape, placement, and even apparent merging vary by font and size. Body families are hypotheses for analysis only, not labels to train as if Unicode-defined.

## 5. Annotation protocol and quality gate

1. Render examples from multiple legally cleared font families with fixed renderer versions and recorded hashes.
2. Sample characters, contextual forms, language/script tags, mark combinations, and font families in a stratified design. Keep entire font families in one data split.
3. Two annotators independently label each pilot image without seeing each other's labels.
4. Compare component-kind agreement and geometry overlap (IoU); report per-kind agreement and adjudicate disagreements. Do not collapse all categories into one score.
5. A third reviewer adjudicates uncertain/high-disagreement cases. Keep the original independent annotations and adjudication trace.
6. Store annotator IDs as pseudonymous IDs, guideline version, tool version, source image hash, font hash, license reference, and confidence.
7. Exclude unresolved components from supervised loss or train them with explicit uncertainty masks.
8. Only promote a visual-family or decomposition claim after it is supported across fonts and reviewed. Never convert Unicode Joining_Group into an MX-Font primitive label automatically.

Suggested pilot acceptance gate (project policy, not a Unicode standard): at least 3 independent font families, two independent annotators, median per-kind polygon IoU >= 0.80 for body/dot regions, and documented adjudication for every sample below threshold. Revisit thresholds after a pilot; do not claim human-level correctness from CI.

## 6. Data split and training safety

Split by font family before rendering or annotation. No glyph from the same source family may leak across train/validation/test. Keep derived crops, annotations, contact sheets, and augmented images attached to the same family split. Record source and derivative hashes. A font must be cleared for ML training before its images or derived labels enter a training set.

## 7. Limits

The registry generator creates linguistic metadata, not a font-specific visual truth set. The annotation schema describes data; it does not validate the artistic correctness of labels. The shaping suite verifies rendering behavior only when run against named font files and pinned HarfBuzz builds. No training permission is implied by Unicode metadata or by a font being downloadable.
