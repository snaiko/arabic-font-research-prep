#!/usr/bin/env python3
"""Render Arabic glyph/context samples from a validated font corpus.

The renderer preserves the logical Arabic string and asks Pillow/RAQM to perform
RTL shaping. Context labels describe the surrounding sequence, not a guarantee
that every letter has all four joining forms.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, features

WIDTH = 320
HEIGHT = 144
FONT_SIZE = 78
BACKGROUND = 255
INK = 0
CORE_ARABIC = list(range(0x0621, 0x063B)) + list(range(0x0641, 0x064B))
CONNECTOR = "\u0628"  # beh, used only to create reproducible joining contexts
PHRASES = [
    "سلام",
    "بسم الله",
    "مرحبا بالعالم",
    "اللغة العربية",
    "النجم المقنع",
    "خط عربي جميل",
    "قلم وحبر",
    "هذا اختبار لتشكيل الحروف العربية",
]

def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]

def read_validation(path: Path) -> dict[str, dict]:
    return {row["file"]: row for row in read_jsonl(path)}

def read_family_map(path: Path) -> dict[str, str]:
    # The validator records a path but not the collection family. Use the
    # collector manifest so fonts stored in nested "static/" folders do not
    # all collapse into a single split named "static".
    return {row["file"]: row["family"] for row in read_jsonl(path)}

def render(text: str, font_path: Path, target: Path) -> None:
    font = ImageFont.truetype(
        str(font_path), FONT_SIZE, layout_engine=ImageFont.Layout.RAQM
    )
    image = Image.new("L", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    bbox = draw.textbbox((0, 0), text, font=font, direction="rtl", language="ar")
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (WIDTH - text_width) / 2 - bbox[0]
    y = (HEIGHT - text_height) / 2 - bbox[1]
    draw.text((round(x), round(y)), text, fill=INK, font=font,
              direction="rtl", language="ar")
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format="PNG", optimize=True)

def contexts(char: str) -> list[tuple[str, str, int]]:
    # Strings are in logical Unicode order; RAQM/HarfBuzz performs visual ordering
    # and OpenType joining. target_index points into the logical string.
    return [
        ("isolated", char, 0),
        ("initial_context", char + CONNECTOR, 0),
        ("medial_context", CONNECTOR + char + CONNECTOR, 1),
        ("final_context", CONNECTOR + char, 1),
    ]

def family_splits(families: list[str], seed: int) -> dict[str, str]:
    ordered = sorted(set(families))
    random.Random(seed).shuffle(ordered)
    n = len(ordered)
    if n < 3:
        raise RuntimeError("At least three distinct font families are required for family-safe splits")
    n_test = max(1, round(n * 0.15))
    n_val = max(1, round(n * 0.15))
    while n_test + n_val >= n:
        if n_val > 1:
            n_val -= 1
        else:
            n_test -= 1
    test = set(ordered[:n_test])
    val = set(ordered[n_test:n_test + n_val])
    return {
        family: ("test" if family in test else "validation" if family in val else "train")
        for family in ordered
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fonts", default="data/raw_fonts")
    parser.add_argument("--validation", default="data/validation/font_validation.jsonl")
    parser.add_argument("--collection", default="data/raw_fonts/fonts.jsonl")
    parser.add_argument("--output", default="data/training_samples")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if not features.check("raqm"):
        parser.error("Pillow was built without libraqm; Arabic RTL shaping cannot be rendered safely")
    fonts_root = Path(args.fonts)
    validation_path = Path(args.validation)
    output = Path(args.output)
    if not fonts_root.is_dir():
        parser.error(f"Font directory not found: {fonts_root}")
    if not validation_path.is_file():
        parser.error(f"Validation manifest not found: {validation_path}")

    validation = read_validation(validation_path)
    collection_path = Path(args.collection)
    if not collection_path.is_file():
        parser.error(f"Collection manifest not found: {collection_path}")
    family_map = read_family_map(collection_path)
    font_paths = sorted(
        p for p in fonts_root.rglob("*")
        if p.is_file() and p.suffix.lower() in {".ttf", ".otf"}
    )
    accepted = []
    rejected = []
    for path in font_paths:
        key = path.as_posix()
        row = validation.get(key)
        if row and row.get("status") == "pass":
            row = dict(row)
            relative_path = path.relative_to(fonts_root).as_posix()
            row["family"] = family_map.get(key, family_map.get("data/raw_fonts/" + relative_path, relative_path.split("/")[0]))
            accepted.append((path, row))
        else:
            rejected.append({
                "file": key,
                "reason": "missing_validation_record" if row is None else row.get("status", "unknown"),
            })
    if not accepted:
        parser.error("No fonts have a matching validation record with status=pass")

    families = [row.get("family") or path.parent.name for path, row in accepted]
    splits = family_splits(families, args.seed)
    metadata_path = output / "samples.jsonl"
    split_handles = {}
    counts = Counter()
    family_counts = Counter()
    output.mkdir(parents=True, exist_ok=True)
    try:
        split_handles = {
            name: (output / "splits" / f"{name}.jsonl").open("w", encoding="utf-8")
            for name in ("train", "validation", "test")
        }
        with metadata_path.open("w", encoding="utf-8") as manifest:
            for font_path, validation_row in accepted:
                family = validation_row.get("family") or font_path.parent.name
                split = splits[family]
                font_hash = digest_file(font_path)
                font_id = font_hash[:12]
                base = Path("images") / family / font_id
                common = {
                    "family": family,
                    "font_file": font_path.as_posix(),
                    "font_sha256": font_hash,
                    "font_name": validation_row.get("full_name") or validation_row.get("family_name"),
                    "split": split,
                    "renderer": "Pillow-RAQM",
                    "canvas": [WIDTH, HEIGHT],
                    "font_size_px": FONT_SIZE,
                    "direction": "rtl",
                    "language": "ar",
                }

                def record(sample_type: str, text: str, image_rel: Path,
                           target_char: str | None = None, target_index: int | None = None,
                           context_label: str | None = None) -> None:
                    render(text, font_path, output / image_rel)
                    item = dict(common)
                    item.update({
                        "sample_type": sample_type,
                        "text": text,
                        "image": image_rel.as_posix(),
                        "target_char": target_char,
                        "target_codepoint": f"U+{ord(target_char):04X}" if target_char else None,
                        "target_index_logical": target_index,
                        "context_label": context_label,
                    })
                    line = json.dumps(item, ensure_ascii=False)
                    manifest.write(line + "\n")
                    split_handles[split].write(line + "\n")
                    counts[sample_type] += 1
                    family_counts[family] += 1

                for codepoint in CORE_ARABIC:
                    char = chr(codepoint)
                    for variant, sample_text, target_index in contexts(char):
                        image_rel = base / f"U{codepoint:04X}" / f"{variant}.png"
                        record("glyph_context", sample_text, image_rel,
                               char, target_index, variant)

                for index, phrase in enumerate(PHRASES):
                    image_rel = base / "phrases" / f"phrase_{index:02d}.png"
                    record("phrase", phrase, image_rel)

                print(f"[OK] {family}/{font_path.name}: {split}")
    finally:
        for handle in split_handles.values():
            handle.close()

    summary = {
        "dataset_version": 1,
        "source_corpus": "arabic-font-corpus-v1",
        "renderer": {
            "name": "Pillow-RAQM",
            "pillow_version": __import__("PIL").__version__,
            "layout_engine": "RAQM",
            "direction": "rtl",
            "language": "ar",
            "canvas": [WIDTH, HEIGHT],
            "font_size_px": FONT_SIZE,
            "foreground": "black",
            "background": "white",
        },
        "seed": args.seed,
        "font_files_accepted": len(accepted),
        "font_files_rejected": rejected,
        "families": {
            family: {"split": splits[family], "samples": family_counts[family]}
            for family in sorted(splits)
        },
        "split_family_counts": dict(Counter(splits.values())),
        "sample_counts": dict(counts),
        "total_samples": sum(counts.values()),
        "limitations": [
            "Context labels identify rendered logical sequences; they do not assert that every Arabic letter supports every joining form.",
            "This first raster dataset is not manually visually audited and is not yet a model-ready quality-certified corpus.",
            "Phrase samples are full-line renders; target glyph crops and ligature-level annotations are future extensions.",
        ],
    }
    (output / "dataset_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "family_splits.json").write_text(
        json.dumps(splits, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "font_files_accepted": len(accepted),
        "families": len(splits),
        "total_samples": summary["total_samples"],
        "sample_counts": dict(counts),
        "split_family_counts": summary["split_family_counts"],
    }, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
