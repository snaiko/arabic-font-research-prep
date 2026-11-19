# Component/caption dataset independent audit

Run after `build_arabic_component_supervision.py`:

```bash
python scripts/audit_arabic_component_supervision.py --manifest reports/arabic_component_supervision.jsonl --image-root data/contextual_glyph_crops --output reports/arabic_component_caption_audit.json
```

The audit checks source-derived sample identities, Unicode codepoint lists, HarfBuzz glyph counts, image SHA-256 and dimensions, nonblank rasters, safe paths, component geometry bounds, paired Arabic/English caption provenance, family-safe split isolation, and fail-closed flags. It counts ink touching the crop boundary as a clipping-risk warning.

A PASS means the generated machine records are internally consistent. It does not establish that a caption is linguistically correct, that a detached component is a dot/hamza/diacritic, that the glyph is visually beautiful/readable, or that the font may legally be used for ML training. The audit deliberately reports zero training-eligible records until a separate rights and review gate is satisfied.
