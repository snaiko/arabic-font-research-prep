#!/usr/bin/env python3
"""Train the image-reference route on leakage-safe contextual Arabic episodes.

This is an explicit local training entry point. It requires a validated
conditional OFL rights manifest and an explicit --max-steps value. It does not
train the text-style route, which still needs reviewed semantic style prompts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

import torch
import torch.nn.functional as F
from PIL import Image
from torch.utils.data import DataLoader, Dataset

from models.arabic_multimodal_glyph import (
    ArabicMultimodalGlyphModel,
    encode_unicode_batch,
    save_training_checkpoint,
    restore_training_checkpoint,
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path):
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc
    return rows


def validate_rights(episodes, rights_manifest, require_complete_manifest=False):
    policy = rights_manifest.get("policy", {})
    if policy.get("status") != "CONDITIONAL_OFL_1_1_APPROVAL":
        raise ValueError("rights manifest is not the conditional OFL-1.1 approved manifest")
    if policy.get("output_font_license") != "SIL Open Font License 1.1":
        raise ValueError("generated font output policy must be SIL OFL 1.1")
    approved = {
        item["sha256"]: item.get("family_id")
        for item in rights_manifest.get("fonts", [])
        if item.get("ml_training_allowed") is True and item.get("review_status") == "approved"
    }
    if not approved:
        raise ValueError("rights manifest contains no approved font hashes")
    if require_complete_manifest:
        family_count = len(set(approved.values()))
        if len(approved) != 52 or family_count != 20:
            raise ValueError(
                f"expected the complete 52-file/20-family rights manifest; "
                f"found {len(approved)} files across {family_count} families"
            )

    families_by_split = {}
    for episode in episodes:
        font_hash = episode.get("font_sha256")
        if font_hash not in approved:
            raise ValueError(f"episode uses a font hash not approved by the rights manifest: {font_hash}")
        family = episode.get("family")
        if approved[font_hash] != family:
            raise ValueError(f"episode family does not match rights manifest for {font_hash}")
        split = episode.get("split")
        if split not in {"train", "validation", "test"} or not family:
            raise ValueError("episode is missing a valid family split")
        previous = families_by_split.setdefault(family, split)
        if previous != split:
            raise ValueError(f"family split leakage detected for {family}")
        target = episode["target"]
        if target.get("font_sha256") != font_hash or target.get("family") != family or target.get("split") != split:
            raise ValueError("target font provenance or split does not match episode")
        logical_text = target.get("logical_text")
        if not isinstance(logical_text, str) or not logical_text:
            raise ValueError("target logical_text must be a non-empty Unicode string")
        target_codepoints = {f"U+{ord(char):04X}" for char in logical_text}
        target_image_hash = episode.get("target_image_sha256")
        if (
            not isinstance(target_image_hash, str) or len(target_image_hash) != 64
            or any(char not in "0123456789abcdef" for char in target_image_hash.lower())
        ):
            raise ValueError("target image SHA-256 is missing or malformed")
        refs = episode.get("style_references", [])
        if len(refs) != 4 or episode.get("reference_count") != 4:
            raise ValueError("every episode must contain exactly four style references")
        ref_cps = []
        for ref in refs:
            if ref.get("font_sha256") != font_hash or ref.get("family") != family or ref.get("split") != split:
                raise ValueError("style reference is not from the exact target font and split")
            ref_hash = ref.get("image_sha256")
            if (
                not isinstance(ref_hash, str) or len(ref_hash) != 64
                or any(char not in "0123456789abcdef" for char in ref_hash.lower())
            ):
                raise ValueError("style reference image SHA-256 is missing or malformed")
            ref_cps.append(ref.get("codepoint"))
        if len(ref_cps) != len(set(ref_cps)):
            raise ValueError("duplicate codepoints in style references")
        if target_codepoints.intersection(ref_cps):
            raise ValueError("target codepoint leaked into style references")
    return set(approved)


class ContextualEpisodeDataset(Dataset):
    def __init__(self, episodes_path, target_root, reference_root):
        self.episodes = read_jsonl(Path(episodes_path))
        self.target_root = Path(target_root).resolve()
        self.reference_root = Path(reference_root).resolve()

    @staticmethod
    def load_gray(path: Path):
        with Image.open(path) as image:
            image = image.convert("L").resize((128, 128), Image.Resampling.LANCZOS)
            values = torch.frombuffer(bytearray(image.tobytes()), dtype=torch.uint8)
            return values.reshape(1, 128, 128).float().div_(255.0)

    @staticmethod
    def safe_path(root: Path, relative: str):
        path = (root / relative).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"image path escapes dataset root: {relative}") from exc
        if not path.is_file():
            raise FileNotFoundError(path)
        return path

    def __len__(self):
        return len(self.episodes)

    def __getitem__(self, index):
        episode = self.episodes[index]
        target = episode["target"]
        target_path = self.safe_path(self.target_root, target["image"])
        if file_sha256(target_path) != episode.get("target_image_sha256"):
            raise ValueError(f"target image hash mismatch: {target['image']}")
        target_image = self.load_gray(target_path)
        refs = []
        for ref in episode["style_references"]:
            ref_path = self.safe_path(self.reference_root, ref["image"])
            if file_sha256(ref_path) != ref.get("image_sha256"):
                raise ValueError(f"style reference image hash mismatch: {ref['image']}")
            refs.append(self.load_gray(ref_path))
        return {
            "target_image": target_image,
            "reference_images": torch.stack(refs),
            "logical_text": target["logical_text"],
            "font_sha256": episode["font_sha256"],
            "family": episode["family"],
            "split": episode["split"],
        }


def collate_batch(rows):
    return {
        "target_images": torch.stack([row["target_image"] for row in rows]),
        "reference_images": torch.stack([row["reference_images"] for row in rows]),
        "target_ids": encode_unicode_batch([row["logical_text"] for row in rows], max_length=64),
        "families": [row["family"] for row in rows],
    }


def edge_loss(prediction, target):
    pred_dx = prediction[..., :, 1:] - prediction[..., :, :-1]
    targ_dx = target[..., :, 1:] - target[..., :, :-1]
    pred_dy = prediction[..., 1:, :] - prediction[..., :-1, :]
    targ_dy = target[..., 1:, :] - target[..., :-1, :]
    return F.l1_loss(pred_dx, targ_dx) + F.l1_loss(pred_dy, targ_dy)


def evaluate(model, loader, device, max_batches=20, edge_weight=0.2):
    model.eval()
    pixel_losses = []
    edge_losses = []
    with torch.no_grad():
        for index, batch in enumerate(loader):
            if index >= max_batches:
                break
            target = batch["target_images"].to(device)
            refs = batch["reference_images"].to(device)
            target_ids = batch["target_ids"].to(device)
            output = model("image", target_ids=target_ids, reference_images=refs)["image"]
            pixel_losses.append(F.l1_loss(output, target).item())
            edge_losses.append(edge_loss(output, target).item())
    if not pixel_losses:
        return {"batches": 0, "pixel_l1": None, "edge_l1": None, "total_loss": None}
    pixel = sum(pixel_losses) / len(pixel_losses)
    edge = sum(edge_losses) / len(edge_losses)
    return {
        "batches": len(pixel_losses),
        "pixel_l1": pixel,
        "edge_l1": edge,
        "total_loss": pixel + edge_weight * edge,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes-dir", required=True)
    parser.add_argument("--target-root", required=True, help="root containing contextual cluster images")
    parser.add_argument("--reference-root", required=True, help="root containing isolated glyph images")
    parser.add_argument("--rights-manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-steps", type=int, required=True, help="explicit step count; no implicit long run")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--latent-dim", type=int, default=64)
    parser.add_argument("--embedding-dim", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--edge-weight", type=float, default=0.2)
    parser.add_argument("--eval-batches", type=int, default=20)
    parser.add_argument("--save-every", type=int, default=250)
    parser.add_argument("--seed", type=int, default=20261119)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--resume", default=None, help="optional checkpoint path; --max-steps remains the total target step count")
    args = parser.parse_args()

    if args.max_steps < 1 or args.batch_size < 1:
        parser.error("--max-steps and --batch-size must be positive")
    random.seed(args.seed)
    torch.manual_seed(args.seed)

    episodes_dir = Path(args.episodes_dir)
    split_paths = {name: episodes_dir / f"{name}.jsonl" for name in ("train", "validation", "test")}
    split_rows = {name: read_jsonl(path) for name, path in split_paths.items()}
    all_rows = [row for rows in split_rows.values() for row in rows]
    rights_path = Path(args.rights_manifest)
    rights = json.loads(rights_path.read_text(encoding="utf-8"))
    approved_hashes = validate_rights(all_rows, rights, require_complete_manifest=True)

    if not split_rows["train"]:
        raise SystemExit("No training episodes are available")
    if not split_rows["validation"]:
        raise SystemExit("No validation episodes are available")

    device = (
        torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if args.device == "auto" else torch.device(args.device)
    )
    train_dataset = ContextualEpisodeDataset(
        split_paths["train"], args.target_root, args.reference_root
    )
    val_dataset = ContextualEpisodeDataset(
        split_paths["validation"], args.target_root, args.reference_root
    )
    test_dataset = ContextualEpisodeDataset(
        split_paths["test"], args.target_root, args.reference_root
    )
    train_loader = DataLoader(
        train_dataset, batch_size=args.batch_size, shuffle=True,
        num_workers=0, collate_fn=collate_batch, drop_last=False
    )
    val_loader = DataLoader(
        val_dataset, batch_size=args.batch_size, shuffle=False,
        num_workers=0, collate_fn=collate_batch
    )
    test_loader = DataLoader(
        test_dataset, batch_size=args.batch_size, shuffle=False,
        num_workers=0, collate_fn=collate_batch
    )

    model = ArabicMultimodalGlyphModel(latent_dim=args.latent_dim, embedding_dim=args.embedding_dim).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    output_dir = Path(args.output_dir)
    checkpoints = output_dir / "checkpoints"
    checkpoints.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoints / "last.pt"

    step = 0
    resumed_from = None
    if args.resume:
        state = restore_training_checkpoint(args.resume, model, optimizer, map_location=device)
        saved_metadata = state.get("metadata", {})
        if saved_metadata.get("latent_dim", args.latent_dim) != args.latent_dim or saved_metadata.get("embedding_dim", args.embedding_dim) != args.embedding_dim:
            raise ValueError("checkpoint model dimensions do not match the requested latent/embedding dimensions")
        step = state["step"]
        resumed_from = str(Path(args.resume))
        if step >= args.max_steps:
            raise ValueError(f"checkpoint step {step} is already at or beyond --max-steps {args.max_steps}")
    start_step = step
    train_losses = []
    while step < args.max_steps:
        for batch in train_loader:
            if step >= args.max_steps:
                break
            model.train()
            target = batch["target_images"].to(device)
            refs = batch["reference_images"].to(device)
            target_ids = batch["target_ids"].to(device)
            optimizer.zero_grad(set_to_none=True)
            prediction = model(
                "image", target_ids=target_ids, reference_images=refs
            )["image"]
            pixel = F.l1_loss(prediction, target)
            edge = edge_loss(prediction, target)
            loss = pixel + args.edge_weight * edge
            if not torch.isfinite(loss):
                raise FloatingPointError(f"non-finite loss at step {step + 1}")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            step += 1
            train_losses.append(loss.item())

            if args.save_every and step % args.save_every == 0:
                save_training_checkpoint(
                    checkpoint_path, model, optimizer, step,
                    metadata={"route": "image", "latent_dim": args.latent_dim, "embedding_dim": args.embedding_dim, "seed": args.seed}
                )
        if not len(train_loader):
            raise SystemExit("Training DataLoader is empty")

    save_training_checkpoint(
        checkpoint_path, model, optimizer, step,
        metadata={"route": "image", "latent_dim": args.latent_dim, "embedding_dim": args.embedding_dim, "seed": args.seed}
    )
    validation = evaluate(model, val_loader, device, args.eval_batches, args.edge_weight)
    testing = evaluate(model, test_loader, device, args.eval_batches, args.edge_weight)

    summary = {
        "status": "COMPLETED",
        "training_started_explicitly": True,
        "steps": step,
        "start_step": start_step,
        "resumed_from": resumed_from,
        "device": str(device),
        "latent_dim": args.latent_dim,
        "embedding_dim": args.embedding_dim,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "edge_weight": args.edge_weight,
        "episode_counts": {name: len(rows) for name, rows in split_rows.items()},
        "approved_font_hashes": len(approved_hashes),
        "rights_policy": rights.get("policy", {}).get("status"),
        "required_generated_font_license": rights.get("policy", {}).get("output_font_license"),
        "rights_manifest_sha256": file_sha256(rights_path),
        "episode_manifest_sha256": {name: file_sha256(path) for name, path in split_paths.items()},
        "training_loss_first_10_mean": sum(train_losses[:10]) / max(1, len(train_losses[:10])),
        "training_loss_last_10_mean": sum(train_losses[-10:]) / max(1, len(train_losses[-10:])),
        "validation": validation,
        "test": testing,
        "checkpoint": str(checkpoint_path),
        "git_sha": __import__("os").environ.get("GITHUB_SHA", "local-unrecorded"),
        "limitations": [
            "This script trains the image-reference route only.",
            "The text-style route is not trained because the corpus does not yet contain reviewed semantic style prompts.",
            "A raster checkpoint is not a TTF/OTF font; vectorization and font compilation are separate stages.",
            "The model does not replace HarfBuzz for arbitrary text shaping.",
            "Generated font files based on OFL sources must be released under SIL OFL 1.1 and avoid Reserved Font Names."
        ]
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "training_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
