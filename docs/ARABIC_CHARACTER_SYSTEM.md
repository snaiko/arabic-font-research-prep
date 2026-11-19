# Arabic Character System v1

## Purpose

A versioned, machine-readable registry for Arabic character identity and joining behavior. It is the common linguistic metadata layer for dataset construction, model conditioning, and evaluation. It is deliberately **not** a claim that every glyph can be decomposed into universal visual parts.

## Sources and authority

- Unicode 17.0 defines joining types and joining groups in the Arabic shaping data. The registry records those as `joining_type` and `joining_group`.
- W3C Arabic Layout Requirements describes Arabic cursive joining and transparent marks.
- `visual_family` and `dot_pattern` are provisional project annotations. They are not Unicode properties and must not be used as MX-Font component labels without a separate expert-reviewed annotation protocol.

## Record semantics

| Field | Meaning |
|---|---|
| `codepoint`, `character`, `unicode_name` | Stable Unicode identity |
| `joining_type` | Unicode joining type: R, L, D, C, U, T |
| `joining_group` | Unicode joining group |
| `visual_family` | Provisional broad visual relation, not a component decomposition |
| `dot_pattern` | Provisional visible dot description |
| `forms_supported_by_joining_type` | Structural possibilities only; not a label for a rendered sample |
| `component_annotation_status` | Explicitly remains `not_annotated` in v1 |

## Actual contextual form labels

The registry must never infer a sample's actual form from its position in a string. A dataset record must be labeled `isol`, `init`, `medi`, or `fina` only after a pinned shaping engine has shaped the exact logical Unicode sequence and its glyph-cluster mapping has been verified. Marks and ligatures need their own sample types and multi-codepoint cluster representation.

Joining-type constraints used by the validator:
- R: isolated/final only.
- D: isolated/initial/medial/final.
- U: isolated only.
- C and T: joining-causing/transparent behavior is contextual; they are not ordinary letter-body form targets. The registry conservatively lists isolated as a placeholder, not a generated shape label.

The right/left wording follows Unicode's cursive-joining model; do not reverse Arabic strings manually. Keep text in logical Unicode order and let HarfBuzz/Pango/RAQM handle shaping and bidi layout.

## Coverage and limits

v1 includes the basic Arabic letters plus common TEH MARBUTA and ALEF MAKSURA records. It is not a complete Arabic-script ontology. Persian/Urdu extensions, Quranic marks, combining marks, ligatures, ZWJ/ZWNJ cases, and extended Arabic blocks must be added in separately reviewed versions. Do not silently fold Persian/Urdu characters into Arabic core.

## Run validation

```bash
python scripts/validate_arabic_character_system.py
python -m unittest tests.test_arabic_character_system -v
```

A PASS validates registry structure and internal consistency only. It does not certify calligraphic correctness, visual decomposition, glyph quality, licensing, or MX-Font training readiness.

## Next annotation gate

Before any component-supervised MX-Font training:
1. Define a versioned visual decomposition ontology with explicit annotation instructions.
2. Annotate a stratified sample of glyphs/forms across multiple licensed font families.
3. Have two independent annotators label body, dots, hamza/marks, counters, joins, and stroke topology.
4. Measure agreement and adjudicate disagreements.
5. Store evidence, annotator IDs (pseudonymous), confidence, and provenance.
6. Keep uncertain/ambiguous decompositions unlabeled; do not fabricate a label.
