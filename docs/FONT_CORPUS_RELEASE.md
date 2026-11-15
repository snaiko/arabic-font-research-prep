# Publishing the font corpus to GitHub

The repository Contents API is text-only, so font binaries are published by GitHub Actions as a **GitHub Release asset**, not committed into ordinary Git history.

## Run the upload

1. Open the repository's **Actions** tab.
2. Select **Build and publish Arabic font corpus**.
3. Click **Run workflow** on branch `main`.
4. Keep the default release tag `arabic-font-corpus-v1` for the first run, then click **Run workflow**.

The workflow:
- downloads only allowlisted Google Fonts family folders that contain a family-level SIL OFL 1.1 license file;
- includes the license and source metadata alongside the font binaries;
- runs the cmap and HarfBuzz screening;
- creates `arabic-font-corpus.zip` and publishes it as a GitHub Release asset.

## Training gate

The archive is an auditable corpus snapshot, not a claim that every included font is training-ready. Use only entries whose `status` is `pass` in `data/validation/font_validation.jsonl`. Files marked `fail` or `needs_shaping_test` must be excluded from training until corrected and revalidated. Review each license and the rendered glyph quality separately.

The workflow does not commit binary fonts to the Git repository history. It attaches the corpus archive to a release, which keeps large binary data out of normal source commits.
