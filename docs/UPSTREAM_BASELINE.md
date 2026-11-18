# Upstream Few-Shot Font Baseline

## Selected baseline

Use the official unified repository:

- Repository: https://github.com/clovaai/fewshot-font-generation
- MX-Font method documentation: `docs/models/MX-Font.md`
- MX-Font training entry point in that repository: `train_MX.py`
- Repository license statement: MIT except the FUNIT and `base/modules/modules.py` portions identified in its README as adopted from NVlabs/FUNIT.

The standalone `clovaai/mxfont` repository itself states that the unified repository should be used for the implementation. The local agent must inspect the current upstream tree and exact notices before copying or vendoring code.

## Mandatory pinning procedure

Before implementation, the local AI agent must:

1. Resolve the upstream default branch to an immutable commit SHA.
2. Record the SHA, retrieval date, repository URL, and the exact files copied or adapted.
3. Preserve the upstream LICENSE and NOTICE files and any third-party license notices.
4. Audit each imported module; do not assume the top-level MIT statement covers third-party code or pretrained weights.
5. Keep the upstream baseline untouched in its own directory and put Arabic/prompt changes in separate project modules.
6. Reproduce a small baseline inference or training smoke test using the upstream documented configuration before adaptation.

## Important limits

MX-Font is the image-conditioned few-shot glyph-generation baseline. It does not provide this project's natural-language prompt encoder, shared image/text latent alignment, Arabic shaping system, or vector/font compiler. Those are project-specific modules and must be implemented and tested separately.

Do not commit a placeholder string such as `PINNED_BY_AGENT_BEFORE_IMPLEMENTATION` as if it were a real commit SHA. Do not train until the pin, license audit, data adapter, and tests are complete.
