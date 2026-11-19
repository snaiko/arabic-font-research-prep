#!/usr/bin/env python3
"""Build leakage-safe few-shot style episodes for contextual Arabic clusters.

Each target is a HarfBuzz-shaped cluster. Its K style references are isolated
glyph crops from the exact same font file, excluding every codepoint present
in the target cluster. Family-level train/validation/test splits are inherited.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


def read_jsonl(path):
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc


def image_sha256(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"image path escapes root: {relative}") from exc
    if not path.is_file():
        raise FileNotFoundError(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_episodes(target_rows, reference_rows, refs_per_episode=4, seed=20261119,
                   target_root=None, reference_root=None):
    if refs_per_episode < 1:
        raise ValueError("refs_per_episode must be positive")
    if (target_root is None) != (reference_root is None):
        raise ValueError("target_root and reference_root must be supplied together")
    references = defaultdict(list)
    for row in reference_rows:
        required = ("font_sha256", "family", "split", "codepoint", "image")
        if any(not row.get(key) for key in required):
            raise ValueError(f"reference row missing required fields {required}")
        references[row["font_sha256"]].append(row)

    episodes = []
    skipped = Counter()
    seen = set()
    for target in target_rows:
        required = ("font_sha256", "family", "split", "image", "logical_text", "case_id", "cluster")
        if any(target.get(key) is None for key in required):
            raise ValueError(f"target row missing required fields {required}")
        identity = (target["font_sha256"], target["case_id"], target["cluster"])
        if identity in seen:
            raise ValueError(f"duplicate contextual target identity: {identity}")
        seen.add(identity)

        target_codepoints = {f"U+{ord(char):04X}" for char in target["logical_text"]}
        pool = [
            row for row in references.get(target["font_sha256"], [])
            if row["family"] == target["family"]
            and row["split"] == target["split"]
            and row["codepoint"] not in target_codepoints
        ]
        if len(pool) < refs_per_episode:
            skipped[target["font_sha256"]] += 1
            continue

        stable_seed = f"{seed}:{target['font_sha256']}:{target['case_id']}:{target['cluster']}"
        rng = random.Random(stable_seed)
        style_refs = rng.sample(pool, refs_per_episode)
        ref_codepoints = [row["codepoint"] for row in style_refs]
        if len(ref_codepoints) != len(set(ref_codepoints)):
            raise AssertionError("duplicate style reference codepoints")
        if target_codepoints.intersection(ref_codepoints):
            raise AssertionError("target codepoint leaked into style references")

        episode_id = hashlib.sha256(
            f"{stable_seed}:{'|'.join(ref_codepoints)}".encode("utf-8")
        ).hexdigest()[:20]
        target_hash = image_sha256(target_root, target["image"]) if target_root else None
        refs_with_hashes = []
        for ref in style_refs:
            item = dict(ref)
            if reference_root:
                item["image_sha256"] = image_sha256(reference_root, ref["image"])
            refs_with_hashes.append(item)

        episodes.append({
            "schema_version": 1,
            "episode_id": episode_id,
            "font_sha256": target["font_sha256"],
            "family": target["family"],
            "split": target["split"],
            "target": target,
            "target_image_sha256": target_hash,
            "style_references": refs_with_hashes,
            "reference_count": len(style_refs),
            "target_codepoints_excluded_from_references": sorted(target_codepoints),
            "target_excluded_from_references": True,
            "supervision_scope": "harfbuzz_contextual_cluster_target_with_isolated_same_font_style_references",
        })

    return episodes, dict(skipped)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", required=True)
    parser.add_argument("--references", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--refs-per-episode", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20261119)
    parser.add_argument("--target-root", required=True)
    parser.add_argument("--reference-root", required=True)
    args = parser.parse_args()

    targets = list(read_jsonl(args.targets))
    references = list(read_jsonl(args.references))
    episodes, skipped = build_episodes(
        targets, references, args.refs_per_episode, args.seed,
        args.target_root, args.reference_root
    )
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    handles = {
        split: (out / f"{split}.jsonl").open("w", encoding="utf-8")
        for split in ("train", "validation", "test")
    }
    split_counts = Counter()
    try:
        for episode in episodes:
            split = episode["split"]
            if split not in handles:
                raise ValueError(f"unexpected split {split!r}")
            handles[split].write(json.dumps(episode, ensure_ascii=False) + "\n")
            split_counts[split] += 1
    finally:
        for handle in handles.values():
            handle.close()

    families_by_split = defaultdict(set)
    for episode in episodes:
        families_by_split[episode["family"]].add(episode["split"])
    leakage = sorted(family for family, splits in families_by_split.items() if len(splits) > 1)
    if leakage:
        raise ValueError(f"family split leakage: {leakage}")

    summary = {
        "schema_version": 1,
        "status": "PASS" if episodes and not skipped else ("PARTIAL" if episodes else "FAIL"),
        "seed": args.seed,
        "references_per_episode": args.refs_per_episode,
        "target_rows": len(targets),
        "episodes": len(episodes),
        "skipped_targets": sum(skipped.values()),
        "skipped_by_font_sha256": skipped,
        "split_counts": dict(split_counts),
        "families": len({episode["family"] for episode in episodes}),
        "multicodepoint_targets": sum(len(episode["target"]["logical_text"]) > 1 for episode in episodes),
        "family_split_leakage": leakage,
        "limitations": [
            "Style references are isolated glyph crops from the same exact font file.",
            "Targets are contextual HarfBuzz clusters; target codepoints are excluded from references.",
            "This provides image-style supervision only; no reviewed natural-language style prompts or semantic component labels are supplied.",
            "Contextual cluster targets preserve the recorded shaped output; the model does not replace HarfBuzz for arbitrary text layout."
        ]
    }
    (out / "episode_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    raise SystemExit(0 if summary["status"] == "PASS" else 2)


if __name__ == "__main__":
    main()
