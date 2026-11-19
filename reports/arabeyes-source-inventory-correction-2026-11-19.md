# Arabeyes source inventory correction and rights note — 2026-11-19

## Why this correction exists

The earlier `arabeyes-20-font-candidates-review-2026-11-19.md` is a shortlist of names, not a complete inventory. Its list should not be read as a verified count of distinct families or exact binary filenames. The Debian Sources listing for the older upstream source package `ttf-arabeyes 2.0-5` exposes **39 TTF files** under `fonts/`. This is a concrete file-level inventory, but it is not yet a binary audit and should not be conflated with the Debian `fonts-arabeyes 2.1-7` source archive targeted by the new GitHub Actions workflow.

## File inventory visible in Debian Sources (ttf-arabeyes 2.0-5)

1. ae_AlArabiya.ttf
2. ae_AlBattar.ttf
3. ae_AlHor.ttf
4. ae_AlManzomah.ttf
5. ae_AlMateen-Bold.ttf
6. ae_AlMohanad.ttf
7. ae_AlMothnna-Bold.ttf
8. ae_AlYarmook.ttf
9. ae_Arab.ttf
10. ae_Cortoba.ttf
11. ae_Dimnah.ttf
12. ae_Electron.ttf
13. ae_Furat.ttf
14. ae_Granada.ttf
15. ae_Graph.ttf
16. ae_Hani.ttf
17. ae_Haramain.ttf
18. ae_Hor.ttf
19. ae_Japan.ttf
20. ae_Jet.ttf
21. ae_Kayrawan.ttf
22. ae_Khalid.ttf
23. ae_Mashq-Bold.ttf
24. ae_Mashq.ttf
25. ae_Metal.ttf
26. ae_Nada.ttf
27. ae_Nagham.ttf
28. ae_Nice.ttf
29. ae_Ostorah.ttf
30. ae_Ouhod-Bold.ttf
31. ae_Petra.ttf
32. ae_Rasheeq-Bold.ttf
33. ae_Rehan.ttf
34. ae_Salem.ttf
35. ae_Shado.ttf
36. ae_Sharjah.ttf
37. ae_Sindbad.ttf
38. ae_Tarablus.ttf
39. ae_Tholoth.ttf

These are **39 file entries**, not 39 proven distinct typeface families. Some are bold styles or related designs. The exact filenames also correct earlier shorthand candidates: e.g. `ae_AlMateen-Bold.ttf` and `ae_AlMothnna-Bold.ttf`.

## License and upstream provenance

The Arabeyes README says the typefaces are under GPL version 2 and includes the narrow font exception for embedding the font or unaltered portions into a document. It also states that Latin glyph ranges are based on Free UCS Outline Fonts, credited to the Free Software Foundation. The Debian copyright file likewise labels the package GPL-2 with Font exception.

Sources:
- Debian Sources font directory: https://sources.debian.org/src/ttf-arabeyes/2.0-5/fonts
- Debian Sources README: https://sources.debian.org/src/ttf-arabeyes/2.0-5/README
- Debian copyright file for current package lineage: https://sources.debian.org/src/fonts-arabeyes/2.1%2Bgit20080901.63a70a7%2Bdfsg-2/debian/copyright
- Debian changelog showing the font-exception addition and source design names: https://sources.debian.org/src/ttf-arabeyes/2.0-2/ChangeLog
- SPDX Font exception 2.0 text: https://spdx.org/licenses/Font-exception-2.0.html

The exception is explicitly about documents embedding the font; it does not expressly mention ML training, learned model parameters, or redistribution of model weights. The Latin glyph provenance adds another reason to preserve per-file notices and source attribution rather than treating the font package as one undifferentiated work.

## Current execution status

- The new workflow `.github/workflows/arabeyes-candidate-audit.yml` was committed to `main` in commit `724f46c45fc12d3203a79578faff836edb569f37`.
- It downloads the Debian 2.1 source archive, checks its published MD5, calculates SHA-256, extracts TTFs and license notices, audits cmap/HarfBuzz shaping, and saves raster previews plus JSON evidence as a workflow artifact.
- The workflow has **not yet been independently confirmed as completed** in this report.
- No binary from this inventory is approved for ML training.
- No Arabeyes font is added to the active training corpus or rights manifest.
- Overall training authorization remains BLOCKED.

This report corrects the inventory count and filenames; it does not claim binary inspection, visual approval, legal clearance, or training readiness.
