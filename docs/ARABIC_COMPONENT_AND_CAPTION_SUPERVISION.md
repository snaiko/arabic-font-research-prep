# Arabic component candidates and paired captions

The contextual-cluster pipeline now produces `arabic-component-caption-supervision`.

For every HarfBuzz cluster it stores:
- the exact logical Unicode sequence and codepoint list;
- Unicode 17.0 names, general categories, Arabic script roles, Joining_Type and Joining_Group where applicable;
- HarfBuzz glyph IDs and cluster cardinalities;
- 8-connected raster ink-component bounding boxes, area ratios, centroids and relative areas;
- factual Arabic and English template captions tied to the same source image and cluster.

## Critical limits

Raster connected components are not semantic labels. A detached component may be a dot, hamza, mark, decorative stroke, or rendering fragment. The dataset therefore labels all component identities as `unknown`; it does not assign dot/hamza/body identities.

The captions are `machine_generated_unreviewed` and use only source text, Unicode properties, HarfBuzz cardinalities, and measured component counts. They are not free-form descriptions of calligraphic style and must not be represented as human-written ground truth.

All records have `expert_visual_linguistic_approval: false` and `training_eligible: false`. The dataset is a research/pretraining-preparation asset, not a gold annotation set.

## Build

```bash
python scripts/build_arabic_component_supervision.py \
  --manifest data/contextual_glyph_crops/contextual_clusters.jsonl \
  --crop-root data/contextual_glyph_crops \
  --registry data/arabic_script_registry_v2.json \
  --output reports/arabic_component_supervision.jsonl
```
