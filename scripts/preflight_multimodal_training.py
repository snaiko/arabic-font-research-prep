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

    dataset = ContextualEpisodeDataset(
        paths["train"], args.target_root, args.reference_root
    )
    batch = collate_batch([dataset[0]])
    model = ArabicMultimodalGlyphModel(latent_dim=64).eval()
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
        "rights_policy": rights.get("policy", {}).get("status"),
        "required_generated_font_license": rights.get("policy", {}).get("output_font_license"),
        "real_batch_loaded": True,
        "forward_output_shape": list(image.shape),
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
