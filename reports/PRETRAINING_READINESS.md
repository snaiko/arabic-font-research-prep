# Pretraining Readiness Report

<badge color="warning">BLOCKED — NOT READY FOR TRAINING</badge>

Updated 2026-11-19 after a read-only audit of the upstream MX-Font source. This report is not a test report from the user's Windows computer. No training was started.

## Work completed in this update

- Pinned upstream `clovaai/fewshot-font-generation` to immutable commit `9d2b6ace3e23199e2a896de329d4c16489b09a96`.
- Inspected the upstream README, root LICENSE, MX-Font training instructions, `train_MX.py`, and core MX-Font imports.
- Documented that upstream `train_MX.py` uses CUDA-specific calls and NCCL, so Windows/device compatibility is not established.
- Documented the upstream README's license exceptions for `FUNIT/` and `base/modules/modules.py`; the MX-Font dependency closure still needs file-by-file clearance.
- Updated the machine-readable readiness record without promoting any unverified gate to PASS.

## Confirmed remaining blockers

- The upstream source is pinned, but the complete dependency-closure license audit and baseline reproduction are not complete.
- Asset-by-asset training permissions are not fully audited.
- Existing raster samples are contextual full-line images, not audited isolated target-glyph crops with verified HarfBuzz cluster mapping.
- A populated, provenance-reviewed paired prompt/geometry dataset has not been demonstrated.
- Executable image, prompt, and hybrid model paths sharing one generator have not been implemented and verified.
- Required data/model tests, leakage checks, checkpoint recovery, and held-out-family evaluation have not been evidenced.
- The actual Windows hardware preflight has not been run; device, VRAM, RAM, free disk, backend support, and runtime remain unknown.

## Gate status

| Gate | Status |
|---|---|
| Upstream pin and license | BLOCKED — revision pinned; dependency audit and baseline run pending |
| Asset rights and provenance | BLOCKED |
| Family-safe data integrity | UNKNOWN — local archive verification pending |
| Arabic target-glyph crops | FAIL |
| Paired prompt/geometry supervision | FAIL |
| Image/prompt/hybrid model paths | FAIL |
| Tests and checkpoint recovery | FAIL |
| Hardware and resource plan | UNKNOWN |

## Required next action

The local AI agent must continue with `docs/AI_AGENT_EXECUTION_SPEC.md` and `docs/PRETRAINING_COMPLETION_PLAN.md`, preserving evidence for every command and test. In particular, it must resolve the MX-Font dependency/license boundary, build and audit the shaped target crops, implement and test the baseline adapter and unified conditioning paths, and run the local hardware preflight.

**Stop condition:** no long training run is authorized by this report. Even after every preparation gate passes, the agent must present a resource estimate and proposed run plan and wait for the user's explicit approval.
