#!/usr/bin/env python3
"""Windows/local readiness preflight for the experimental image-reference raster trainer.

This script only inspects hardware/data and runs the no-training forward preflight.
It never creates an optimizer, calls backward(), updates weights, or starts training.
"""
from __future__ import annotations

import ctypes
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RIGHTS = ROOT / "data" / "manifests" / "font_rights.json"
EPISODES = ROOT / "data" / "contextual_style_episodes"
TARGET_ROOT = ROOT / "data" / "contextual_glyph_crops"
REFERENCE_ROOT = ROOT / "data" / "glyph_crops"
REPORT = ROOT / "reports" / "local" / "machine_preflight.json"


def command(args):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=15, cwd=ROOT)
        return (result.stdout or result.stderr).strip() if result.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def ram_gb():
    if os.name == "nt":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.c_ulong), ("memory_load", ctypes.c_ulong),
                ("total_phys", ctypes.c_ulonglong), ("avail_phys", ctypes.c_ulonglong),
                ("total_page", ctypes.c_ulonglong), ("avail_page", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong), ("avail_virtual", ctypes.c_ulonglong),
                ("avail_extended", ctypes.c_ulonglong),
            ]
        status = MemoryStatus()
        status.length = ctypes.sizeof(MemoryStatus)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return round(status.total_phys / 1024**3, 2)
        return None
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        return round(pages * page_size / 1024**3, 2)
    except (ValueError, OSError, AttributeError):
        return None


def gpu_info():
    info = {
        "torch_available": False, "cuda_available": False, "torch_version": None,
        "cuda_version": None, "device_name": None, "vram_gb": None,
        "nvidia_smi": command(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"]),
    }
    try:
        import torch
        info.update(
            torch_available=True,
            cuda_available=torch.cuda.is_available(),
            torch_version=torch.__version__,
            cuda_version=torch.version.cuda,
        )
        if torch.cuda.is_available():
            properties = torch.cuda.get_device_properties(0)
            info.update(device_name=properties.name, vram_gb=round(properties.total_memory / 1024**3, 2))
    except Exception as exc:
        info["torch_error"] = str(exc)
    return info


def read_jsonl(path):
    rows = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc
    return rows


def inspect_rights(path=RIGHTS):
    if not path.is_file():
        return {"ok": False, "reason": f"missing rights manifest: {path.relative_to(ROOT)}"}
    data = json.loads(path.read_text(encoding="utf-8"))
    policy = data.get("policy", {})
    if policy.get("status") != "CONDITIONAL_OFL_1_1_APPROVAL":
        return {"ok": False, "reason": "rights manifest is not conditionally approved under OFL-1.1"}
    if policy.get("output_font_license") != "SIL Open Font License 1.1":
        return {"ok": False, "reason": "generated font output license must be SIL OFL 1.1"}
    records = data.get("fonts", [])
    approved = {
        row.get("sha256"): row.get("family_id")
        for row in records
        if row.get("ml_training_allowed") is True and row.get("review_status") == "approved"
    }
    family_count = len(set(approved.values()))
    if len(approved) != 52 or family_count != 20:
        return {"ok": False, "reason": f"expected 52 approved files across 20 families; found {len(approved)} files across {family_count} families"}
    return {
        "ok": True, "approved_font_files": len(approved),
        "families": family_count,
        "output_font_license": policy["output_font_license"],
        "noncommercial_note": policy.get("noncommercial_note"),
    }


def inspect_episodes(episodes_dir=EPISODES, rights_path=RIGHTS):
    paths = {split: episodes_dir / f"{split}.jsonl" for split in ("train", "validation", "test")}
    missing = [str(path.relative_to(ROOT)) for path in paths.values() if not path.is_file()]
    if missing:
        return {"ok": False, "reason": "missing episode split files", "missing": missing}
    rights_data = json.loads(rights_path.read_text(encoding="utf-8"))
    approved = {
        row["sha256"]: row.get("family_id")
        for row in rights_data.get("fonts", [])
        if row.get("ml_training_allowed") is True and row.get("review_status") == "approved"
    }
    counts = {}
    families = {}
    total_refs = 0
    multicodepoint = 0
    for split, path in paths.items():
        rows = read_jsonl(path)
        counts[split] = len(rows)
        if not rows:
            return {"ok": False, "reason": f"empty {split} episode split"}
        for episode in rows:
            font_hash = episode.get("font_sha256")
            family = episode.get("family")
            if font_hash not in approved or approved[font_hash] != family:
                return {"ok": False, "reason": "episode font/family not approved by rights manifest"}
            if episode.get("split") != split:
                return {"ok": False, "reason": f"episode split mismatch in {split}"}
            prior = families.setdefault(family, split)
            if prior != split:
                return {"ok": False, "reason": f"family split leakage: {family}"}
            target = episode.get("target", {})
            text = target.get("logical_text", "")
            if not text:
                return {"ok": False, "reason": "empty target logical_text"}
            target_cps = {f"U+{ord(char):04X}" for char in text}
            if len(text) > 1:
                multicodepoint += 1
            target_hash = episode.get("target_image_sha256")
            if not isinstance(target_hash, str) or len(target_hash) != 64:
                return {"ok": False, "reason": "missing target image SHA-256"}
            refs = episode.get("style_references", [])
            if len(refs) != 4 or episode.get("reference_count") != 4:
                return {"ok": False, "reason": "every episode must contain exactly four style references"}
            ref_cps = []
            for ref in refs:
                if ref.get("font_sha256") != font_hash or ref.get("family") != family or ref.get("split") != split:
                    return {"ok": False, "reason": "style reference font/family/split mismatch"}
                if not isinstance(ref.get("image_sha256"), str) or len(ref["image_sha256"]) != 64:
                    return {"ok": False, "reason": "missing style-reference image SHA-256"}
                ref_cps.append(ref.get("codepoint"))
            if target_cps.intersection(ref_cps):
                return {"ok": False, "reason": "target codepoint leaked into style references"}
            total_refs += len(refs)
    return {
        "ok": True, "split_counts": counts, "total_episodes": sum(counts.values()),
        "families": len(families), "multicodepoint_targets": multicodepoint,
        "reference_images": total_refs, "family_split_leakage": False,
    }


def recommended_batch_size(gpu, ram):
    if gpu.get("cuda_available") and gpu.get("vram_gb") is not None:
        vram = gpu["vram_gb"]
        if vram >= 8: return 8
        if vram >= 4: return 4
        if vram >= 2: return 2
        return 1
    if ram is not None and ram >= 24: return 2
    return 1


def run_model_preflight():
    command_line = [
        sys.executable, "-m", "scripts.preflight_multimodal_training",
        "--episodes-dir", str(EPISODES),
        "--target-root", str(TARGET_ROOT),
        "--reference-root", str(REFERENCE_ROOT),
        "--rights-manifest", str(RIGHTS),
        "--output", str(REPORT.parent / "real_data_model_preflight.json"),
    ]
    try:
        result = subprocess.run(
            command_line, cwd=ROOT, capture_output=True, text=True, timeout=900
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status": "FAIL", "error": str(exc)}
    if result.returncode != 0:
        return {
            "status": "FAIL",
            "returncode": result.returncode,
            "stdout_tail": (result.stdout or "")[-3000:],
            "stderr_tail": (result.stderr or "")[-3000:],
        }
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"status": "FAIL", "reason": "preflight output was not valid JSON", "stdout_tail": result.stdout[-3000:]}


def main():
    gpu = gpu_info()
    ram = ram_gb()
    disk = shutil.disk_usage(ROOT)
    rights = inspect_rights()
    episodes = inspect_episodes() if rights.get("ok") else {"ok": False, "reason": "rights manifest not ready"}
    image_roots = {
        "target_root_exists": (TARGET_ROOT / "contextual_clusters.jsonl").is_file(),
        "reference_root_exists": (REFERENCE_ROOT / "glyph_crops.jsonl").is_file(),
    }
    image_roots["ok"] = all(image_roots.values())

    model_preflight = {"status": "SKIPPED"}
    if rights.get("ok") and episodes.get("ok") and image_roots["ok"] and gpu["torch_available"]:
        model_preflight = run_model_preflight()

    blocking_reasons = []
    if not rights.get("ok"):
        blocking_reasons.append(rights.get("reason", "rights manifest is not ready"))
    if not episodes.get("ok"):
        blocking_reasons.append(episodes.get("reason", "episode dataset is not ready"))
    if not image_roots["ok"]:
        blocking_reasons.append("contextual or isolated image dataset root is missing")
    if not gpu["torch_available"]:
        blocking_reasons.append("PyTorch is not installed in this Python environment")
    elif model_preflight.get("status") != "PASS":
        blocking_reasons.append("real-data no-training model preflight failed")
    if disk.free < 2 * 1024**3:
        blocking_reasons.append("less than 2 GB of free disk space")
    warnings = []
    if not gpu["cuda_available"]:
        warnings.append("CUDA is unavailable; training will use CPU and may be slow.")
    if ram is not None and ram < 12:
        warnings.append("System RAM is below 12 GB; use a smaller batch size.")
    ready = not blocking_reasons
    report = {
        "status": "READY_FOR_EXPERIMENTAL_IMAGE_ROUTE" if ready else "BLOCKED",
        "training_allowed": ready,
        "training_started": False,
        "training_performed": False,
        "optimizer_created": False,
        "backward_pass_performed": False,
        "weights_updated": False,
        "checkpoint_created": False,
        "os": platform.platform(),
        "python": sys.version,
        "python_executable": sys.executable,
        "architecture": platform.machine(),
        "cpu": platform.processor() or None,
        "ram_total_gb": ram,
        "disk_free_gb": round(disk.free / 1024**3, 2),
        "gpu": gpu,
        "recommended_batch_size": recommended_batch_size(gpu, ram),
        "recommended_latent_dim": 64,
        "recommended_embedding_dim": 16,
        "blocking_reasons": blocking_reasons,
        "warnings": warnings,
        "rights": rights,
        "episodes": episodes,
        "image_roots": image_roots,
        "real_data_model_preflight": model_preflight,
        "scope": "Experimental image-reference raster baseline only; not native MX-Font, not semantic text-style generation, and not TTF/OTF output.",
        "license_note": "Generated font files based on the approved OFL sources must remain SIL OFL 1.1. OFL is not a NonCommercial license; downstream commercial use is not prohibited.",
        "next_steps": (
            ["If the user approves, run RUN_IMAGE_ROUTE_TRAINING.bat for a controlled experiment."]
            if ready else
            ["Resolve the blocking_reasons listed above, then rerun START_LOCAL_TRAINING.bat."]
        ),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("\nPreflight finished. No training was started. Report: " + str(REPORT.relative_to(ROOT)))
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
