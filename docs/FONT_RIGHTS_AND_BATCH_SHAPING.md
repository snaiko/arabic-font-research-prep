# Font rights gate and batch HarfBuzz regression

## Why this gate exists
A font being downloadable, present in Google Fonts, or labelled with an open-source license does not by itself document the project's decision that this exact file/version may be used for ML training. This workflow requires a human-reviewed, per-file record. It is a project control, not legal advice.

## 1. Automatically generated evidence candidates
The CI workflow creates a `font-rights-evidence-candidates` artifact from the collected font corpus. It records, for every exact font file:
- the local relative path, family ID, and verified SHA-256;
- the pinned Google Fonts source revision and source-file URL;
- the corresponding family-level license-file URL at that exact revision;
- a pending review state and `ml_training_allowed: false`.

The artifact is an evidence queue, **not** an approval manifest. The builder verifies every local font hash and rejects missing files, duplicate paths, unsafe paths, or hash mismatches. It deliberately cannot infer that a license permits the intended ML use. An authorized reviewer must inspect the actual license text and any applicable reserved-name/other terms, then make the per-file decision. Never copy the candidate queue into the active approval manifest unchanged.

## 2. Prepare an approved manifest
Only after review, create `data/manifests/font_rights.json` with one record per approved exact file. Include:
- path relative to the font directory;
- stable family ID and SHA-256 of the exact file;
- exact license name and authoritative license URL;
- `ml_training_allowed: true` only after the rights review;
- `review_status: "approved"`, reviewer, review date, and evidence references.

Keep pending or unclear files out of the manifest used for shaping.

## 3. Validate the manifest and files
Install the existing project font-validation dependencies plus `uharfbuzz`, then run:

```powershell
python scripts/validate_font_rights_manifest.py --manifest data/manifests/font_rights.json --font-root "D:\\ArabicFonts"
```

Every listed file must exist under the supplied root and match its recorded SHA-256. The validator rejects unapproved entries, duplicate paths, malformed hashes, and path traversal.

## 4. Run the regression suite across approved fonts

```powershell
python scripts/run_batch_shaping_regression.py --manifest data/manifests/font_rights.json --font-root "D:\\ArabicFonts" --output-dir reports/local/shaping
```

The runner stops before shaping if any manifest entry fails the rights/hash gate. It writes one HarfBuzz report per font plus `batch_summary.json`.

## 5. Interpretation
A successful technical run does not prove the license interpretation is legally correct or that shaping is visually correct. Keep all unapproved font-derived data excluded from training. The rights gate remains blocked until authorized per-file review is complete.


## 6. Pinned license text evidence (automated)

The CI pipeline now fetches and snapshots the exact license text at the immutable Google Fonts revision for every distinct family license. It verifies the OFL 1.1 marker and selected redistribution/reserved-name clauses, records each snapshot SHA-256, copyright header, and possible Reserved Font Names, and retains all 20 license snapshots for the 52-file corpus.

Run:

```bash
python scripts/audit_google_fonts_licenses.py \
  --candidates reports/font_rights_evidence_candidates.json \
  --output-dir reports/font_license_evidence
```

A successful evidence audit means source and text retrieval/integrity passed. It does **not** make a legal determination that the proposed machine-learning training use is permitted. The snapshot report therefore remains `REVIEW_REQUIRED`, `approved_font_count: 0`, and `ml_training_allowed: false`. The workflow artifact is named `pinned-font-license-evidence`.
