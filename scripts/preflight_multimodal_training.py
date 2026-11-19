#!/usr/bin/env python3
"""No-training preflight for the real contextual few-shot Arabic dataset.

Validates episode provenance and the conditional OFL rights manifest, loads one
real batch, and runs one forward pass under torch.no_grad(). No optimizer,
backward pass, weight update, or checkpoint is created.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import torch

from models.arabic_multimodal_glyph import ArabicMultimodalGlyphModel
from scripts.train_multimodal_glyph import (
    ContextualEpisodeDataset,
    collate_batch,
    read_jsonl,
    validate_rights,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes-dir", required=True)
    parser.add_argument("--target-root", required=True)
    parser.add_argument("--reference-root", required=True)
    parser.add_argument("--rights-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    episodes_dir = Path(args.episodes_dir)
    paths = {name: episodes_dir / f"{name}.jsonl" for name in ("train", "validation", "test")}
    rows = {name: read_jsonl(path) for name, path in paths.items()}
    all_rows = [row for split_rows in rows.values() for row in split_rows]
    rights = json.loads(Path(args.rights_manifest).read_text(encoding="utf-8"))
    approved_hashes = validate_rights(all_rows, rights)

    counts = {name: len(split_rows) for name, split_rows in rows.items()}
    if not counts["train"] or not counts["validation"] or not counts["test"]:
        raise ValueError(f"all three episode splits are required: {counts}")

    # Iterate every episode in every split once. Dataset loading verifies each
    # target and each reference image SHA-256 against the episode manifest.
    image_integrity = {}
    datasets = {}
    for split in ("train", "validation", "test"):
        dataset = ContextualEpisodeDataset(paths[split], args.target_root, args.reference_root)
        datasets[split] = dataset
        reference_count = 0
        for index in range(len(dataset)):
            sample = dataset[index]
            reference_count += sample["reference_images"].shape[0]
        image_integrity[split] = {
            "targets_verified": len(dataset),
            "references_verified": reference_count,
        }

    dataset = datasets["train"]
    batch = collate_batch([dataset[0]])
    model = ArabicMultimodalGlyphModel(latent_dim=64).eval()
    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    parameter_bytes = sum(parameter.numel() * parameter.element_size() for parameter in model.parameters())
    with torch.no_grad():
        output = model(
            "image",
            target_ids=batch["target_ids"],
            reference_images=batch["reference_images"],
        )
    image = output["image"]
    if tuple(image.shape) != (1, 1, 128, 128):
        raise ValueError(f"unexpected generated raster shape: {tuple(image.shape)}")
    if not torch.isfinite(image).all():
        raise ValueError("model produced non-finite values during no-training preflight")

    summary = {
        "status": "PASS",
        "training_performed": False,
        "optimizer_created": False,
        "backward_pass_performed": False,
        "weights_updated": False,
        "checkpoint_created": False,
        "episode_counts": counts,
        "total_episodes": len(all_rows),
        "families": len({row["family"] for row in all_rows}),
        "approved_font_hashes": len(approved_hashes),
        "image_integrity": image_integrity,
        "total_target_images_sha256_verified": sum(x["targets_verified"] for x in image_integrity.values()),
        "total_reference_images_sha256_verified": sum(x["references_verified"] for x in image_integrity.values()),
        "rights_policy": rights.get("policy", {}).get("status"),
        "required_generated_font_license": rights.get("policy", {}).get("output_font_license"),
        "real_batch_loaded": True,
        "forward_output_shape": list(image.shape),
        "model_parameter_count": parameter_count,
        "model_parameter_bytes_fp32": parameter_bytes,
        "estimated_weights_gradients_adam_state_bytes": parameter_bytes * 4,
        "output_min": float(image.min()),
        "output_max": float(image.max()),
        "notes": [
            "This is a data/forward preflight only; it is not a training run.",
            "Only the image-reference route is exercised.",
            "The text-style route still needs reviewed semantic style prompts."
        ]
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
