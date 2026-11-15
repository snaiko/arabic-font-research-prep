# Local font corpus

Run from the repository root:

    python scripts/collect_google_fonts.py --output data/raw_fonts

Small pilot:

    python scripts/collect_google_fonts.py --families amiri,noto-naskh-arabic,cairo,tajawal --output data/raw_fonts

The collector pins the current Google Fonts commit, downloads TTF/OTF files plus each family license and metadata, and writes SHA-256 records to fonts.jsonl. It also writes collection_report.json.

**Downloaded does not mean validated.** Files are marked downloaded_unvalidated; cmap coverage and HarfBuzz shaping must pass before training. Raw binaries are not committed to this Git repository. Keep them in controlled dataset storage and commit only manifests/reports allowed by the applicable terms.
