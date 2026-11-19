# Training corpus audit

Run this on the local extracted corpus before building crops or training:

```powershell
python scripts/audit_training_corpus.py --samples data/training_samples/samples.jsonl --font-root data/raw_fonts --image-root data/training_samples --output reports/local/dataset_audit.json
```

To include the separately reviewed source-asset manifest:

```powershell
python scripts/audit_training_corpus.py --samples data/training_samples/samples.jsonl --font-root data/raw_fonts --image-root data/training_samples --source-assets data/manifests/source_assets.jsonl
```

The audit checks required sample metadata, duplicate sample identities, normalized family split leakage, font-hash-to-family consistency, optional exact local font hashes, optional image-file existence/path safety, and explicit approval/evidence for every supplied source-asset record.

A PASS is limited to those checks. It is not legal advice, visual-quality approval, human annotation agreement, or proof of model readiness. Run it locally because this repository does not contain the user's private extracted font files or render archive.
