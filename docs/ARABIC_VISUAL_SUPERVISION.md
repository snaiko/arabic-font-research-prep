# Deterministic Arabic Visual Supervision

The workflow emits `arabic-visual-supervision` from every generated HarfBuzz cluster crop.

Each record pairs:
- canonical logical Unicode text and code points;
- Unicode general categories and combining-mark count;
- HarfBuzz glyph IDs and cluster cardinality;
- case, script, language, direction, feature, family, split, and font hash;
- image hash and deterministic raster measurements (ink bounding box, normalized centroid, ink ratio, and fixed 16-bin row/column occupancy profiles).

## Important interpretation

The raster fields are measurable machine observations. They are not body/dot/hamza segmentation, calligraphic style descriptions, linguistic correctness judgments, or expert annotations. The workflow does not convert these measurements into gold component labels.

Every record has an explicit `supervision_provenance` object. A record is marked `training_eligible: true` only if its exact font SHA-256 appears in the rights manifest with `ml_training_allowed: true` and `review_status: approved`. The committed rights template is empty, so the current generated records remain ineligible for training. This is intentional fail-closed behavior.

## Rebuild

```bash
python scripts/build_arabic_visual_supervision.py \
  --manifest data/contextual_glyph_crops/contextual_clusters.jsonl \
  --crop-root data/contextual_glyph_crops \
  --output reports/arabic_visual_supervision.jsonl \
  --rights-manifest data/manifests/font_rights.template.json
```

The output is an intermediate structured supervision export, not a claim that the corpus is ready for model training.
