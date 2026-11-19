# Pinned Google Fonts license evidence audit

The workflow now fetches each unique license file from the exact immutable Google Fonts revision recorded in the font collection manifest. It stores the complete text snapshot, SHA-256, pinned source URL, copyright lines, possible Reserved Font Name strings, and presence/absence of selected OFL 1.1 clauses.

The current source corpus reports 52 font files across 20 families. The audit deduplicates the 20 family-level license files, while retaining the per-font exact SHA-256 and pinned font-source evidence in the candidate queue.

## What a PASS means

A PASS means the pinned license text was retrieved from `raw.githubusercontent.com/google/fonts`, decoded, hashed, and checked for the SIL Open Font License 1.1 marker and selected expected clauses. It does not decide whether machine-learning training is legally permitted, whether third-party upstream rights apply, or whether every intended use complies with all license terms.

The output deliberately keeps:
- `approved_font_count: 0`
- `ml_training_allowed: false`
- `status: REVIEW_REQUIRED`

The license text itself is preserved in the workflow artifact `pinned-font-license-evidence`. Do not copy the candidate queue into the approved manifest or change its pending flags automatically.
