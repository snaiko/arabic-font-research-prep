# Font rights gate and batch HarfBuzz regression

## Why this gate exists
A font being downloadable, present in Google Fonts, or labelled with an open-source license does not by itself document the project's decision that this exact file/version may be used for ML training. This workflow requires a human-reviewed, per-file record. It is a project control, not legal advice.

## 1. Prepare a local manifest
Copy `data/manifests/font_rights.template.json` to `data/manifests/font_rights.json`. Add one object per exact font file with:
- a path relative to the font directory;
- stable family ID and SHA-256 of the exact file;
- exact license name and authoritative license URL;
- `ml_training_allowed: true` only after the rights review;
- `review_status: "approved"`, reviewer, review date, and evidence references.

Keep pending or unclear files out of the manifest used for shaping. Do not infer rights from the font family name. The manifest intentionally starts empty.

## 2. Validate the manifest and files
Install the existing project font-validation dependencies plus `uharfbuzz`, then run:

```powershell
python scripts/validate_font_rights_manifest.py --manifest data/manifests/font_rights.json --font-root "D:\ArabicFonts"
```

Every listed file must exist under the supplied root and match its recorded SHA-256. The validator rejects unapproved entries, duplicate paths, malformed hashes, and path traversal.

## 3. Run the regression suite across all approved fonts

```powershell
python scripts/run_batch_shaping_regression.py --manifest data/manifests/font_rights.json --font-root "D:\ArabicFonts" --output-dir reports/local/shaping
```

The runner stops before shaping if any manifest entry fails the rights/hash gate. It writes one HarfBuzz report per font plus `batch_summary.json`. Reports preserve font hashes, HarfBuzz version, glyph IDs, clusters, advances, and offsets for the versioned regression cases.

## 4. Interpretation
- A successful run means the explicit project gate passed and HarfBuzz produced outputs for those exact files.
- It does not prove the license interpretation is legally correct, that every use or redistribution is permitted, or that shaping is visually correct.
- Review the results for right/dual joining, transparent marks, lam-alef clusters, ZWJ/ZWNJ, tatweel, and mark attachment.
- Keep source font files, local reports, and any private licensing evidence off public GitHub unless the user explicitly authorizes publication.

## 5. Current state
No per-file rights approvals are assumed. The template is empty by design. Until the user/local reviewer fills it with evidence, the batch runner is expected to stop. Training remains blocked independently by the other readiness gates.
