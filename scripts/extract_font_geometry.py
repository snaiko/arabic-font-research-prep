#!/usr/bin/env python3
"""Extract reproducible, approximate geometry metadata from SVG or TTF/OTF.

Examples:
  python scripts/extract_font_geometry.py path/to/font.ttf --output font_geometry.json
  python scripts/extract_font_geometry.py path/to/glyph.svg --output glyph_geometry.json

SVG path measurements require svgpathtools. Font outline bounds and advance
widths use FontTools. This script does not infer a complete calligraphic style.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def extract_font(path: Path) -> dict:
    try:
        from fontTools.ttLib import TTFont
        from fontTools.pens.boundsPen import BoundsPen
    except ImportError as exc:
        raise RuntimeError("Install dependencies: pip install -r requirements-geometry.txt") from exc
    font = TTFont(str(path))
    glyph_set = font.getGlyphSet()
    cmap = {}
    for table in font['cmap'].tables:
        if table.isUnicode():
            cmap.update(table.cmap)
    glyphs = {}
    for codepoint, glyph_name in sorted(cmap.items()):
        if glyph_name not in glyph_set:
            continue
        glyph = glyph_set[glyph_name]
        pen = BoundsPen(glyph_set)
        glyph.draw(pen)
        bounds = list(pen.bounds) if pen.bounds else None
        glyphs[f"U+{codepoint:04X}"] = {
            "glyph_name": glyph_name,
            "advance_width": float(glyph.width),
            "bounds": bounds,
            "width": float(bounds[2] - bounds[0]) if bounds else 0.0,
            "height": float(bounds[3] - bounds[1]) if bounds else 0.0,
        }
    head = font['head']
    hhea = font['hhea']
    return {
        "kind": "font",
        "file": path.name,
        "units_per_em": int(head.unitsPerEm),
        "ascent": int(hhea.ascent),
        "descent": int(hhea.descent),
        "glyph_count_mapped": len(glyphs),
        "glyphs": glyphs,
        "notes": ["Bounds are outline bounds in font units.", "This is cmap-based inventory, not a substitute for Arabic shaping tests."],
    }


def extract_svg(path: Path) -> dict:
    try:
        from svgpathtools import parse_path
    except ImportError as exc:
        raise RuntimeError("Install dependencies: pip install -r requirements-geometry.txt") from exc
    root = ET.parse(path).getroot()
    view_box = root.attrib.get("viewBox")
    paths = []
    for element in root.iter():
        if element.tag.split('}')[-1] != 'path':
            continue
        d = element.attrib.get('d', '')
        if not d.strip():
            continue
        parsed = parse_path(d)
        xmin, xmax, ymin, ymax = parsed.bbox() if len(parsed) else (0, 0, 0, 0)
        lengths = [segment.length(error=1e-3) for segment in parsed]
        paths.append({
            "id": element.attrib.get('id'),
            "segment_count": len(parsed),
            "path_length": float(sum(lengths)),
            "bounds": [float(xmin), float(ymin), float(xmax), float(ymax)],
            "width": float(xmax - xmin),
            "height": float(ymax - ymin),
            "command_counts": {command: len(re.findall(r'[MmZzLlHhVvCcSsQqTtAa]', d)) for command in 'MmZzLlHhVvCcSsQqTtAa'},
        })
    return {"kind": "svg", "file": path.name, "viewBox": view_box, "path_count": len(paths), "paths": paths,
            "notes": ["Path bounds and lengths are calculated geometrically; transforms and inherited styles are not applied by this first version."]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.input.is_file():
        parser.error(f"Input file not found: {args.input}")
    suffix = args.input.suffix.lower()
    if suffix in {'.ttf', '.otf', '.ttc'}:
        result = extract_font(args.input)
    elif suffix == '.svg':
        result = extract_svg(args.input)
    else:
        parser.error('Supported inputs: .ttf, .otf, .ttc, .svg')
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + '\n', encoding='utf-8')
    else:
        print(rendered)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
