# Expanded candidate execution log — 2026-11-19

## Result of the next research pass

A substantially larger Arabic font source was identified: the Arabeyes font project. Debian's maintained source package is `fonts-arabeyes 2.1-7`, described as Arabeyes GPL TrueType Arabic fonts. The package source includes the font binaries and licensing files. The upstream project history records that a GPL font exception was added to COPYING, and the source package README states the exception for documents embedding the font.

Sources:
- Debian source package and downloadable source archive: https://packages.debian.org/source/trixie/armel/fonts/fonts-arabeyes
- Debian source package details: https://packages.debian.org/bookworm/i386/fonts-arabeyes
- Debian source listing and COPYING/README/font files: https://codegraph.jelmer.uk/fonts-arabeyes/2.1-7/
- Upstream changelog documenting addition of GPL font exception: https://sources.debian.org/src/ttf-arabeyes/2.0-2/ChangeLog
- SourceForge upstream archive listing: https://sourceforge.net/projects/arabeyes/files/Fonts/ae_fonts/

## Twenty distinct Arabeyes design candidates

The following 20 distinct font designs are listed in the Arabeyes 2.1 source package (one design per font file; styles/weights are not inflated into extra families):

1. ae_AlArabiya
2. ae_AlBattar
3. ae_AlManzomah
4. ae_AlMateen
5. ae_AlMohanad
6. ae_AlMothnna
7. ae_Arab
8. ae_Cortoba
9. ae_Dimnah
10. ae_Electron
11. ae_Furat
12. ae_Granada
13. ae_Graph
14. ae_Hani
15. ae_Haramain
16. ae_Hor
17. ae_Japan
18. ae_Jet
19. ae_Kayrawan
20. ae_Khalid

The package also lists additional distinct designs (e.g. Mashq, Metal, Nada, Nagham, Nice, Ostorah, Petra, Rehan, Salem, Shado, Sharjah, Sindibad, Tarablus, Tholoth), so the source is not limited to exactly 20.

## Critical rights interpretation — NOT CLEARED FOR AI TRAINING

The source package uses GPL with a font exception. The documented exception says that embedding the font (or unaltered portions) in a document does not by itself make that document GPL. This is a narrow document-embedding exception. It does not expressly address:
- training an ML model on font files or rendered glyph images;
- whether model weights or generated font files are derivative works;
- distribution of the trained model or generated fonts.

Therefore, these 20 are **license-documented technical candidates**, not training-approved assets. The user's noncommercial intent does not by itself remove GPL obligations. Do not set `ml_training_allowed=true` for them without a specific legal basis or written permission.

The previous 13 candidates also remain unverified at binary level. Arabixel Basic/Adventure/Antique are three separate CC BY 4.0 releases by one creator, not automatically one family; their exact font files still need inspection. Ghoulam is incomplete and should not be used as full-script coverage. The CC0 candidates likewise need exact binary inspection.

## Download and technical validation attempt

The Debian source archive was identified:
`https://deb.debian.org/debian/pool/main/f/fonts-arabeyes/fonts-arabeyes_2.1.orig.tar.xz`

Debian lists its size as 672.5 kB and MD5 as `abc5f9628f4df02c8c5fdec210e9f628`.

A direct binary download was attempted in this execution environment but failed. Consequently:
- no archive was downloaded into the working environment;
- no font binaries were extracted;
- no SHA-256 hashes were computed;
- no cmap, HarfBuzz, raster rendering, or duplicate-outline checks were run;
- no fonts were added to the corpus or training manifest.

Do not claim that the 20 candidates passed technical or ML-rights validation.

## Current project decision

- Candidate designs surfaced: at least 20 distinct Arabeyes designs, plus 13 earlier independent candidates across other license groups.
- AI-training-cleared fonts from this pass: 0.
- Technically inspected binaries from this pass: 0.
- Existing 20-family OFL corpus: preserved and still excluded by the fail-closed rights gate.
- Training remains disabled.

## Next required operation

Obtain the Debian source archive in an environment with working binary download access, verify its MD5 against Debian's published value, extract and preserve COPYING/README and source files, then:
1. identify exact font file names and hashes;
2. validate Arabic cmap coverage and shaping/rendering;
3. deduplicate by outline/source lineage;
4. obtain an explicit written AI/ML training permission or authoritative license interpretation for GPL+Font Exception assets;
5. only then add cleared assets to the candidate corpus and update the rights manifest.
