# Automated Arabic linguistic metadata audit

`scripts/audit_arabic_linguistic_consistency.py` cross-checks every contextual cluster against the canonical shaping-case text and the generated Unicode 17.0 Arabic-script registry.

It checks source spans, logical text/codepoint correspondence, Unicode general categories, Joining_Type, combining-mark classification, duplicate cluster identities, and HarfBuzz glyph cardinalities. The independent contextual audit separately re-shapes the font/case pairs with HarfBuzz and verifies glyph-ID mappings.

This is a deterministic metadata/shaping-integrity check. It does **not** verify Arabic spelling in arbitrary prose, calligraphic quality, whether a glyph looks correct to a reader, or whether a ligature is aesthetically correct. Those remain outside the claims of automated validation.

## Build

```bash
python scripts/audit_arabic_linguistic_consistency.py \
  --manifest data/contextual_glyph_crops/contextual_clusters.jsonl \
  --cases data/shaping_regression_cases_v1.json \
  --registry data/arabic_script_registry_v2.json \
  --output reports/arabic_linguistic_audit.json
```
