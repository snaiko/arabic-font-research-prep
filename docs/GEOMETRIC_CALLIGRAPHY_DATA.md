# Geometric Arabic Calligraphy Learning

## Purpose

The project must learn to construct new Arabic calligraphic compositions, not merely retrieve or imitate complete training images. The target capability is generative: infer reusable geometric and structural principles, then apply them to unseen words and compositions.

## Reference: Andalusi calligraphy gallery

- Page: https://andalusi.app/calligraphy
- Use in this project: visual and taxonomy reference for the kinds of decorative Arabic word compositions the model should eventually support.
- The page describes decorative Arabic calligraphy assets and styles including Thuluth, Diwani, and Ruq'ah, with PNG export.
- This reference is not currently an approved training-data source.

### Rights restriction

Andalusi's published terms state that designs, templates, stickers, and Arabic fonts are intellectual property of Andalusi or its licensors, and prohibit redistribution or derivative works without express written permission. Therefore:

- Do not scrape, bulk-download, redistribute, or train on gallery images unless written permission or a suitable license is obtained.
- If permission is obtained, record its scope, allowed purposes, attribution requirements, redistribution conditions, and expiry/territory if any before ingestion.
- Until then, use the page only as a high-level visual reference; do not copy its artwork into the corpus.

## What the model should learn

Train explicit geometric and structural representations alongside raster appearance:

1. **Stroke geometry:** centerlines, width profiles, curvature, joins, terminals, tapering, and pressure-like modulation.
2. **Composition geometry:** baselines, word silhouette, balance, scale, spacing, overlap, and negative-space distribution.
3. **Transformations:** rotation, reflection where stylistically valid, scaling, translation, controlled deformation, and ornament placement.
4. **Structural constraints:** Arabic letter identity, contextual forms, joining rules, ligatures, dot placement, and diacritic placement.
5. **Style-conditioned generation:** style descriptors should control geometry without requiring the target word or complete composition to have appeared in training.

## Recommended dataset design

Keep separate, linked data layers:

- glyphs/: licensed glyph examples and contextual forms.
- words/: licensed word-level samples with text/transcription and shaping metadata.
- vectors/: original or licensed SVG/path representations, where available.
- geometry/: derived non-image measurements such as contours, skeletons, curvature samples, bounding boxes, stroke-width profiles, component graphs, and negative-space descriptors.
- synthetic/: procedurally generated training examples created from documented geometric rules.
- provenance/: source URL, creator, license/permission evidence, retrieval date, file hash, and allowed uses for every asset.

Every sample must carry provenance and a rights status. Exclude assets with unknown or incompatible permissions from training and redistribution.

## Training strategy

1. Build a geometry extraction pipeline from fonts and independently licensed vector artwork.
2. Generate synthetic Arabic compositions using controllable curve and layout primitives, while enforcing Arabic shaping and letter connectivity.
3. Train a geometry-aware representation or auxiliary losses for topology, curvature, stroke width, layout, and negative space.
4. Train the image generator to render from both text/Arabic structure and geometric/style conditions.
5. Evaluate on held-out words and combinations, not only held-out images. Measure legibility, letter topology, connectivity, curvature continuity, composition balance, and style consistency.
6. Reconstruct vector paths and validate shaping before exporting TTF/OTF.

## Important distinction

A large image collection alone encourages memorization. The intended system must learn reusable construction rules and demonstrate generalization to words and layouts absent from the training set. MX-Font-style reference conditioning can remain one component, but it is not by itself a complete geometric reasoning or vector-font generation system.
