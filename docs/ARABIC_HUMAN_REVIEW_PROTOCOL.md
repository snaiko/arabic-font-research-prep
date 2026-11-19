# Arabic visual, linguistic, and component review pack

## Purpose and status

This workflow creates a reproducible human-review package from the HarfBuzz contextual cluster dataset. It does **not** perform expert review, approve labels, or grant legal training permission. Generated records remain drafts.

The pack is deliberately split into two tasks:

1. **Visual/linguistic review:** inspect representative shaped clusters across all shaping cases and font families.
2. **Geometry pilot:** independently annotate the geometry of a smaller subset containing exactly one source codepoint and one HarfBuzz glyph. Multi-codepoint ligatures and multi-glyph clusters are excluded from this first geometry pilot because the current annotation schema describes one glyph instance.

## Build

The GitHub Actions workflow runs:

```bash
python scripts/build_arabic_review_pack.py \
  --manifest data/contextual_glyph_crops/contextual_clusters.jsonl \
  --crop-root data/contextual_glyph_crops \
  --output reports/review_pack \
  --per-case 10 --geometry-count 40 --seed 20261119
```

It uploads the `arabic-human-review-pack` artifact. The selection is deterministic for a fixed manifest and seed, takes samples from every shaping case, and round-robins font families within each case. The summary records the actual counts; if a case has fewer eligible samples, the output reports fewer rather than fabricating examples.

## Visual and linguistic review rubric

For each row in `visual_linguistic_review.jsonl`, reviewers must set each field to `pass`, `fail`, or `uncertain`, and provide notes for every fail/uncertain result:

- `text_mapping`: does the displayed logical text and Unicode sequence match the source span?
- `orthography`: is the Arabic spelling/sequence valid for the intended test case? Do not silently normalize the supplied test string.
- `joining_or_ligature`: is the observed connection/ligature consistent with the shaping context and font?
- `marks_and_dots`: are dots, hamza, and combining marks present, positioned, and attached plausibly?
- `visual_shape`: is the rendered cluster complete, unclipped, nonblank, and visually plausible compared with an independent reference rendering?
- Record the reviewer ID, review date, reference renderer/version, and issue details in reviewer notes or the accompanying review log.

At least two reviewers should independently inspect the same stratified sample before disagreements are adjudicated. A fail or uncertain item must not enter the approved training subset. The review set is a quality-control sample, not proof that every unreviewed record is correct. Expand the sample if any systematic issue is found.

## Geometry pilot protocol

The two files under `geometry_annotations/` are independent blank templates. Assign them to two different qualified annotators; do not let either see the other's polygons before submission. Replace the placeholder annotator ID, then annotate:

- `body`: main connected body region;
- `dot`: each distinct dot;
- `hamza`, `diacritic`, `other_mark`: separate visible marks;
- `counter`: enclosed negative-space region where relevant;
- `join_region`: visible joining/connection area only where defensible;
- `stroke_segment`: use only when the segmentation guideline defines a reproducible segment;
- `uncertain`: explicit uncertainty, never guess.

Use normalized image coordinates in [0,1], polygons around visible regions, confidence values, and relations only when visually supported. Do not infer stroke order, centerlines, or hidden construction from a raster outline. If a boundary is ambiguous, mark it uncertain and explain why.

After both annotators finish:
1. Run `scripts/validate_glyph_visual_annotation.py` on each annotation record.
2. Run `scripts/compare_glyph_annotations.py --annotator-a ... --annotator-b ...` to calculate per-class approximate agreement.
3. A human adjudicator reviews every unmatched component and low-IoU pair, creates the adjudicated record, sets status to `adjudicated`, and documents the decision.
4. Do not treat agreement scores alone as correctness. The adjudicator must check component meaning, missing dots/marks, parent-child relations, and the visual source image.
5. Freeze a guideline version and repeat a calibration round if a component class has systematic disagreement.

The generated `adjudication.jsonl` is a tracking template, not a completed decision. No annotation is promoted automatically.

## Rights boundary

This pack inherits the source font files and their provenance. It is for controlled review only. It does not make any font legally cleared for ML training. Keep font-derived samples excluded from training until an authorized reviewer completes the per-file rights manifest with authoritative license evidence and confirms the scope permits the intended model training. Do not publish private legal correspondence or reviewer personal data.

## Acceptance gate

The pack can support a future review decision only after:
- all visual/linguistic review rows have two independent reviews and adjudication for conflicts;
- all geometry pilot samples have two independent annotations, validated records, per-class agreement analysis, and adjudicated final records;
- the pilot demonstrates the guidelines are understandable and reproducible;
- font rights are separately approved per exact file/hash.

Passing Python tests or creating this pack does not satisfy any of those human gates. Training remains blocked until the readiness report explicitly records evidence for each gate.

## Cluster-level annotation data

The glyph-instance schema remains reserved for a defensible one-codepoint/one-glyph instance. A separate cluster-level schema and pack preserve the complete HarfBuzz cluster: logical source span, all source codepoints, all glyph IDs, non-rendering controls/separators, shaping case, font identity, and rendered crop. This is required for lam-alef ligatures, mark-bearing clusters, and other many-to-many mappings.

The workflow generates a deterministic stratified draft pack (10 examples per available shaping case by default) and validates each record against the source manifest and image SHA-256. Every generated assessment remains `pending` and every record remains `draft`. Automated validation establishes structural/provenance integrity only; it cannot certify Arabic orthography or artistic correctness. This pack is not a request for the project owner to perform manual review, and it does not unlock training by itself.
