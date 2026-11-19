#!/usr/bin/env python3
"""Strict normalized-coordinate screen for duplicate Arabic glyph outlines.

This detects exact normalized point/contour/metric matches. It is not a
perceptual similarity or independent-design-lineage certification.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

ARABIC_RANGES = (
    (0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF),
    (0xFB50, 0xFDFF), (0xFE70, 0xFEFF),
)


def glyph_fingerprints(font_path: Path) -> dict:
    from fontTools.ttLib import TTFont

    font = TTFont(font_path, lazy=False)
    if "glyf" not in font or "head" not in font or "hmtx" not in font:
        raise ValueError(f"unsupported outline table format: {font_path.name}")
    cmap = {}
    for table in font["cmap"].tables:
        if table.isUnicode():
            cmap.update(table.cmap)
    arabic = {
        cp: name for cp, name in cmap.items()
        if any(start <= cp <= end for start, end in ARABIC_RANGES)
    }
    upem = font["head"].unitsPerEm
    result = {}
    for cp, name in arabic.items():
        glyph = font["glyf"][name]
        coordinates, endpoints, _flags = glyph.getCoordinates(font["glyf"])
        points = [(round(x / upem, 5), round(y / upem, 5)) for x, y in coordinates]
        advance, lsb = font["hmtx"][name]
        payload = json.dumps(
            [points, list(endpoints), round(advance / upem, 5), round(lsb / upem, 5)],
            separators=(",", ":"),
        )
        result[cp] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    font.close()
    return result


def audit(font_root: Path) -> dict:
    fonts = []
    for path in sorted(font_root.rglob("*.ttf")):
        glyphs = glyph_fingerprints(path)
        payload = "".join(f"{cp:04X}:{digest};" for cp, digest in sorted(glyphs.items()))
        fonts.append({
            "file": path.relative_to(font_root).as_posix(),
            "arabic_codepoint_count": len(glyphs),
            "whole_font_arabic_outline_sha256": hashlib.sha256(payload.encode()).hexdigest(),
            "glyph_fingerprints": glyphs,
        })

    pairs = []
    for left, right in itertools.combinations(fonts, 2):
        common = set(left["glyph_fingerprints"]) & set(right["glyph_fingerprints"])
        same = sorted(
            cp for cp in common
            if left["glyph_fingerprints"][cp] == right["glyph_fingerprints"][cp]
        )
        if same:
            pairs.append({
                "font_a": left["file"],
                "font_b": right["file"],
                "common_codepoints": len(common),
                "identical_outline_count": len(same),
                "identical_outline_ratio": round(len(same) / len(common), 6) if common else 0,
                "identical_codepoints": [f"U+{cp:04X}" for cp in same],
            })

    whole_counts = Counter(x["whole_font_arabic_outline_sha256"] for x in fonts)
    duplicates = [
        sorted(x["file"] for x in fonts if x["whole_font_arabic_outline_sha256"] == digest)
        for digest, count in whole_counts.items() if count > 1
    ]
    return {
        "schema_version": 1,
        "fonts_inspected": len(fonts),
        "unique_whole_font_fingerprints": len(whole_counts),
        "exact_whole_font_duplicate_groups": duplicates,
        "font_pairs_with_shared_exact_glyph_outlines": len(pairs),
        "max_shared_outline_pair": max(pairs, key=lambda x: x["identical_outline_count"], default=None),
        "pairs": sorted(pairs, key=lambda x: (-x["identical_outline_count"], x["font_a"], x["font_b"])),
        "method": "Unicode Arabic cmap; TrueType glyf outlines decomposed to coordinates; point coordinates and horizontal metrics normalized by unitsPerEm; exact SHA-256 comparison per codepoint and whole font.",
        "limitations": [
            "Not perceptual similarity or calligraphic-style similarity.",
            "Different contour start points, point order, direction, or equivalent decompositions may evade exact matching.",
            "A few shared glyph outlines do not establish that two fonts are duplicate families.",
            "Does not establish independent design lineage or copyright ownership."
        ]
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = audit(Path(args.font_root))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "fonts_inspected": report["fonts_inspected"],
        "unique_whole_font_fingerprints": report["unique_whole_font_fingerprints"],
        "exact_whole_font_duplicate_groups": len(report["exact_whole_font_duplicate_groups"]),
        "font_pairs_with_shared_exact_glyph_outlines": report["font_pairs_with_shared_exact_glyph_outlines"],
        "max_shared_outline_pair": report["max_shared_outline_pair"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
