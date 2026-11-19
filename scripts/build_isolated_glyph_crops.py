#!/usr/bin/env python3
"""Create isolated, single-codepoint Arabic glyph crops from licensed local fonts.

This deliberately does NOT crop a character out of a contextual word image:
Pillow's public drawing API does not expose reliable HarfBuzz cluster-to-pixel
mapping for that operation. Each codepoint is shaped/rendered on its own using
RAQM, then tightly cropped and padded. Joining-context supervision remains a
separate, not-yet-implemented data path.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, features

CANVAS = 128
MARGIN = 8
INK = 0
PAPER = 255

def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_no}: {exc}") from exc

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def resolve_font(value: str, root: Path) -> Path:
    p = Path(value)
    candidates = [p, root / p, root / p.name]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(f"Cannot resolve font_file={value!r} under {root}")

def render_crop(char: str, font_path: Path, size: int) -> Image.Image:
    font = ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
    scratch = Image.new("L", (size * 4, size * 4), PAPER)
    draw = ImageDraw.Draw(scratch)
    bbox = draw.textbbox((0, 0), char, font=font, direction="rtl", language="ar")
    if bbox is None:
        raise ValueError("empty_text_bbox")
    draw.text((size, size), char, fill=INK, font=font, direction="rtl", language="ar")
    # Use actual ink bounds rather than logical advance width.
    ink_bbox = scratch.point(lambda p: 255 if p < 250 else 0).getbbox()
    if ink_bbox is None:
        raise ValueError("blank_render")
    glyph = scratch.crop(ink_bbox)
    if glyph.width < 1 or glyph.height < 1:
        raise ValueError("empty_ink_bounds")
    available = CANVAS - 2 * MARGIN
    scale = min(available / glyph.width, available / glyph.height)
    new_size = (max(1, round(glyph.width * scale)), max(1, round(glyph.height * scale)))
    glyph = glyph.resize(new_size, Image.Resampling.LANCZOS)
    out = Image.new("L", (CANVAS, CANVAS), PAPER)
    out.paste(glyph, ((CANVAS - glyph.width) // 2, (CANVAS - glyph.height) // 2))
    # A valid crop must contain visible ink after normalization.
    if out.point(lambda p: 255 if p < 245 else 0).getbbox() is None:
        raise ValueError("blank_after_resize")
    return out

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--samples", default="data/training_samples/samples.jsonl")
    ap.add_argument("--font-root", default="data/raw_fonts")
    ap.add_argument("--output", default="data/glyph_crops")
    ap.add_argument("--font-size", type=int, default=96)
    args = ap.parse_args()
    if not features.check("raqm"):
        ap.error("Pillow libraqm is required; refusing unsafe Arabic rendering.")
    samples_path, font_root, out = Path(args.samples), Path(args.font_root), Path(args.output)
    if not samples_path.is_file():
        ap.error(f"Missing sample manifest: {samples_path}")
    if args.font_size < 16:
        ap.error("--font-size must be >= 16")
    out.mkdir(parents=True, exist_ok=True)
    manifest = out / "glyph_crops.jsonl"
    rejected = []
    seen = set()
    accepted = 0
    with manifest.open("w", encoding="utf-8") as dst:
        for row in read_jsonl(samples_path):
            if row.get("sample_type") != "glyph_context" or row.get("context_label") != "isolated":
                continue
            char = row.get("target_char")
            if not isinstance(char, str) or len(char) != 1:
                rejected.append({"font_sha256": row.get("font_sha256"), "reason": "invalid_target_char"})
                continue
            font_hash = row.get("font_sha256")
            cp = ord(char)
            key = (font_hash, cp)
            if key in seen:
                continue
            seen.add(key)
            try:
                font_path = resolve_font(str(row["font_file"]), font_root)
                actual_hash = digest(font_path)
                if font_hash and actual_hash != font_hash:
                    raise ValueError("font_sha256_mismatch")
                image = render_crop(char, font_path, args.font_size)
                rel = Path("images") / str(row.get("family", "unknown")) / actual_hash[:12] / f"U{cp:04X}.png"
                target = out / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                image.save(target, format="PNG", optimize=True)
                record = {
                    "image": rel.as_posix(), "family": row.get("family"),
                    "split": row.get("split"), "font_file": str(font_path),
                    "font_sha256": actual_hash, "codepoint": f"U+{cp:04X}",
                    "unicode_char": char, "sample_type": "isolated_single_codepoint",
                    "renderer": "Pillow-RAQM", "direction": "rtl", "language": "ar",
                    "canvas": [CANVAS, CANVAS], "font_size_px": args.font_size,
                    "contextual_joining_supervision": False
                }
                dst.write(json.dumps(record, ensure_ascii=False) + "\n")
                accepted += 1
            except Exception as exc:
                rejected.append({"font_sha256": font_hash, "codepoint": f"U+{cp:04X}", "reason": str(exc)})
    summary = {
        "schema_version": 1, "accepted_crops": accepted, "rejected": rejected,
        "canvas": [CANVAS, CANVAS], "renderer": "Pillow-RAQM",
        "limitations": [
            "Only isolated single-codepoint crops are produced.",
            "This is not contextual-form, ligature, or combining-mark supervision.",
            "The output is not yet the native MX-Font dataset format and has no MX-Font component labels."
        ]
    }
    (out / "crop_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"accepted_crops": accepted, "rejected": len(rejected), "manifest": str(manifest)}, ensure_ascii=False))
    return 0 if accepted else 2

if __name__ == "__main__":
    raise SystemExit(main())
