# Upstream Few-Shot Font Baseline

## Selected baseline and immutable source pin

- Repository: https://github.com/clovaai/fewshot-font-generation
- Selected model: MX-Font (not a checkpoint merge).
- Pinned commit: `9d2b6ace3e23199e2a896de329d4c16489b09a96`
- Pinned source tree: https://github.com/clovaai/fewshot-font-generation/tree/9d2b6ace3e23199e2a896de329d4c16489b09a96
- Pin verified against the upstream `main` branch API on 2026-11-19.
- Training entry point at this pin: `train_MX.py`
- MX-Font training instructions: `docs/models/MX-Font.md`

## License boundary — do not treat the whole repository as uniformly MIT

The upstream README states that the repository is MIT **except** the `FUNIT/` directory and `base/modules/modules.py`, which are adopted from NVlabs/FUNIT. The MX-Font model files identify themselves as NAVER Corp. MIT-licensed, but MX-Font imports shared modules from `base.modules`; the exact dependency closure must be audited before copying any shared implementation.

The upstream root LICENSE and README were inspected at the pinned revision. Preserve the upstream LICENSE and README notices with any permitted copied/adapted code. Do not copy `FUNIT/` or `base/modules/modules.py` under the assumption that the NAVER MIT notice covers them. Obtain and follow the applicable upstream FUNIT license/notice before using those excluded files. This record is a source-level audit, not legal advice and not a completed file-by-file vendoring clearance.

## Compatibility findings

The upstream `train_MX.py` calls `torch.cuda.set_device`, uses CUDA tensors, and initializes distributed training with the `nccl` backend. It is therefore not a verified Windows/CPU/AMD/Intel training path as-is. The local implementation must either establish a supported environment (for example, a compatible Linux + NVIDIA CUDA environment) or make and test a narrowly scoped device/backend adaptation. Do not silently assume the upstream script runs on the user's Windows computer.

The upstream documented command is:

```bash
python train_MX.py cfgs/MX/train.yaml cfgs/data/train/custom.yaml
```

Do not run this command until a compatible dataset adapter/configuration exists and the user has approved a training run.

## Mandatory implementation procedure

Before implementation, the local AI agent must:

1. Fetch this exact commit, not a moving branch.
2. Record the exact upstream files imported or adapted and their individual notices.
3. Audit the dependency closure of the MX-Font model, including shared `base/` modules.
4. Preserve the upstream baseline unchanged in its own directory; put Arabic and prompt changes in separate project modules.
5. Reproduce a small baseline inference or training smoke test using the upstream documented configuration, in a supported environment, and save logs.
6. Keep upstream source, project-specific modifications, and all pretrained-weight provenance distinct.

## Important limits

MX-Font is the image-conditioned few-shot glyph-generation baseline. It does not provide this project's natural-language prompt encoder, shared image/text latent alignment, Arabic shaping system, or vector/font compiler. The current Arabic raster release is not yet in MX-Font's native dataset format.

Do not claim that this source pin means the baseline has been installed, reproduced, adapted, or trained. Those remain separate acceptance gates.
