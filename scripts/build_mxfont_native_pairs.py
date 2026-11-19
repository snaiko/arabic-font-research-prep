#!/usr/bin/env python3
"""Build deterministic native-style MX-Font image-pair records from isolated Arabic glyph crops.

This exporter prepares the image relationships required by MX-Font:
- style images: other codepoints from the target font file;
- content images: the same codepoint from other font files in the same family split.

It deliberately does NOT invent MX-Font decomposition/primals labels. The output
is a pairing manifest only and is not directly trainable by the full upstream
MX-Font trainer until reviewed decomposition labels are supplied.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path


def _stable_seed(seed: int, *parts: str) -> int:
    raw = "|".join([str(seed), *parts]).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def build_pairs(rows, *, styles_per_target=3, contents_per_target=3, seed=20261119):
    by_font = defaultdict(dict)
    by_split_codepoint = defaultdict(list)
    metadata = {}

    for row in rows:
        split = row["split"]
        font_sha = row["font_sha256"]
        cp = row["codepoint"].upper()
        key = (split, font_sha, cp)
        if key in metadata:
            raise ValueError(f"duplicate glyph record: {key}")
        metadata[key] = row
        by_font[(split, font_sha)][cp] = row
        by_split_codepoint[(split, cp)].append(row)

    output = []
    for key in sorted(metadata):
        split, font_sha, cp = key
        target = metadata[key]
        same_font = by_font[(split, font_sha)]
        style_pool = [r for c, r in same_font.items() if c != cp]
        content_pool = [r for r in by_split_codepoint[(split, cp)] if r["font_sha256"] != font_sha]

        if len(style_pool) < styles_per_target:
            continue
        if len(content_pool) < contents_per_target:
            continue

        rng = random.Random(_stable_seed(seed, split, font_sha, cp))
        styles = sorted(rng.sample(style_pool, styles_per_target), key=lambda r: r["codepoint"])
        contents = sorted(rng.sample(content_pool, contents_per_target),
                          key=lambda r: (r["font_sha256"], r["family"]))

        output.append({
            "schema_version": 1,
            "sample_id": hashlib.sha256(f"{split}|{font_sha}|{cp}".encode()).hexdigest()[:20],
            "split": split,
            "family": target["family"],
            "font_sha256": font_sha,
            "target": {
                "image": target["image"],
                "codepoint": cp,
                "unicode_char": target["unicode_char"],
            },
            "style_images": [
                {"image": r["image"], "codepoint": r["codepoint"], "font_sha256": r["font_sha256"]}
                for r in styles
            ],
            "content_images": [
                {"image": r["image"], "font_sha256": r["font_sha256"], "family": r["family"]}
                for r in contents
            ],
            "decomposition": None,
            "decomposition_status": "MISSING_REVIEWED_ARABIC_PRIMALS",
        })

    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, help="data/glyph_crops/glyph_crops.jsonl")
    parser.add_argument("--image-root", required=True, help="Root containing image paths in the manifest")
    parser.add_argument("--output", required=True)
    parser.add_argument("--styles-per-target", type=int, default=3)
    parser.add_argument("--contents-per-target", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20261119)
    args = parser.parse_args()

    rows = [json.loads(line) for line in Path(args.manifest).read_text(encoding="utf-8").splitlines() if line.strip()]
    records = build_pairs(rows, styles_per_target=args.styles_per_target,
                          contents_per_target=args.contents_per_target, seed=args.seed)

    root = Path(args.image_root)
    missing = []
    for record in records:
        paths = [record["target"]["image"]]
        paths += [r["image"] for r in record["style_images"]]
        paths += [r["image"] for r in record["content_images"]]
        missing.extend(str(root / p) for p in paths if not (root / p).is_file())
    if missing:
        raise SystemExit(f"missing {len(missing)} referenced images; first: {missing[0]}")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    counts = defaultdict(int)
    for record in records:
        counts[record["split"]] += 1
    summary = {
        "status": "PAIRING_MANIFEST_BUILT",
        "records": len(records),
        "split_counts": dict(sorted(counts.items())),
        "styles_per_target": args.styles_per_target,
        "contents_per_target": args.contents_per_target,
        "seed": args.seed,
        "decomposition_labels": "NOT_PROVIDED",
        "training_ready_for_full_upstream_mxfont": False,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
