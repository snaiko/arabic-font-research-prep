#!/usr/bin/env python3
"""Inspect local TTF/OTF files for Arabic cmap coverage and HarfBuzz shaping.

Install: python -m pip install -r requirements-font-validation.txt
Run:     python scripts/validate_arabic_fonts.py --input data/raw_fonts --output data/validation
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

try:
    from fontTools.ttLib import TTFont
except ImportError:
    print("Missing dependency: fonttools. Install requirements-font-validation.txt", file=sys.stderr)
    raise SystemExit(2)

try:
    import uharfbuzz as hb
except ImportError:
    hb = None

# Arabic core letters plus common Arabic-script extensions used in Persian/Urdu.
CORE_ARABIC = set(range(0x0621, 0x063B)) | set(range(0x0641, 0x064B))  # Arabic letters; U+0640 tatweel is not a letter
EXTENDED_ARABIC = set(
    list(range(0x066E, 0x0671)) + list(range(0x0671, 0x06D4))
    + list(range(0x06FA, 0x06FE)) + list(range(0x0750, 0x0780))
)
TEST_STRINGS = [
    ("basic_joining", "سلام"),
    ("mixed_joining", "ببب"),
    ("lam_alef", "لا"),
    ("diacritics", "بِسْمِ"),
    ("arabic_sentence", "مرحبا بالعالم"),
]
EXTENSION_TEST_STRINGS = [("persian_extension", "پچژگ")]

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def name_value(font: TTFont, name_id: int) -> str | None:
    if "name" not in font:
        return None
    values = []
    for record in font["name"].names:
        if record.nameID == name_id:
            try:
                value = record.toUnicode().strip()
            except Exception:
                continue
            if value and value not in values:
                values.append(value)
    return values[0] if values else None

def license_near(path: Path) -> str | None:
    candidates = [
        path.parent / "OFL.txt", path.parent / "OFL-1.1.txt",
        path.parent.parent / "OFL.txt", path.parent.parent / "OFL-1.1.txt",
        path.parent / "LICENSE", path.parent.parent / "LICENSE",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return None

def shape_tests(path: Path) -> dict:
    if hb is None:
        return {"status": "not_run", "reason": "uharfbuzz_not_installed", "tests": []}
    blob = path.read_bytes()
    face = hb.Face(blob)
    font = hb.Font(face)
    font.scale = (face.upem, face.upem)
    tests = []
    all_pass = True
    for label, sample in TEST_STRINGS:
        buffer = hb.Buffer()
        buffer.add_str(sample)
        buffer.direction = "rtl"
        buffer.language = "ar"
        buffer.script = "Arab"
        hb.shape(font, buffer)
        infos = buffer.glyph_infos
        gids = [info.codepoint for info in infos]
        missing = sum(1 for gid in gids if gid == 0)
        # A valid result must produce glyphs and no .notdef glyphs.
        passed = bool(gids) and missing == 0
        all_pass = all_pass and passed
        tests.append({
            "name": label,
            "text": sample,
            "glyph_count": len(gids),
            "missing_glyph_count": missing,
            "glyph_ids": gids,
            "clusters": [info.cluster for info in infos],
            "passed": passed,
        })
    extension_tests = []
    extension_pass = True
    for label, sample in EXTENSION_TEST_STRINGS:
        buffer = hb.Buffer()
        buffer.add_str(sample)
        buffer.direction = "rtl"
        buffer.language = "fa"
        buffer.script = "Arab"
        hb.shape(font, buffer)
        gids = [info.codepoint for info in buffer.glyph_infos]
        missing = sum(1 for gid in gids if gid == 0)
        passed = bool(gids) and missing == 0
        extension_pass = extension_pass and passed
        extension_tests.append({
            "name": label, "text": sample, "glyph_count": len(gids),
            "missing_glyph_count": missing, "glyph_ids": gids,
            "passed": passed,
        })
    return {
        "status": "pass" if all_pass else "fail",
        "tests": tests,
        "extended_script_status": "pass" if extension_pass else "not_supported_or_incomplete",
        "extended_script_tests": extension_tests,
    }

def inspect_font(path: Path) -> dict:
    result = {
        "file": str(path.as_posix()),
        "filename": path.name,
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "status": "fail",
        "errors": [],
    }
    font = None
    try:
        font = TTFont(path, lazy=False, recalcBBoxes=False, recalcTimestamp=False)
        cmap = set()
        for table in font["cmap"].tables:
            if table.isUnicode():
                cmap.update(table.cmap.keys())
        missing_core = sorted(CORE_ARABIC - cmap)
        missing_extended = sorted(EXTENDED_ARABIC - cmap)
        tables = sorted(font.keys())
        axes = []
        if "fvar" in font:
            axes = [
                {"tag": axis.axisTag, "min": axis.minValue,
                 "default": axis.defaultValue, "max": axis.maxValue}
                for axis in font["fvar"].axes
            ]
        result.update({
            "family_name": name_value(font, 1),
            "subfamily_name": name_value(font, 2),
            "full_name": name_value(font, 4),
            "units_per_em": font["head"].unitsPerEm if "head" in font else None,
            "glyph_count": len(font.getGlyphOrder()),
            "unicode_codepoint_count": len(cmap),
            "arabic_core_coverage": round(
                1.0 - (len(missing_core) / max(1, len(CORE_ARABIC))), 4
            ),
            "missing_arabic_core_codepoints": [f"U+{cp:04X}" for cp in missing_core],
            "missing_arabic_extended_codepoints": [f"U+{cp:04X}" for cp in missing_extended],
            "has_gsub": "GSUB" in font,
            "has_gpos": "GPOS" in font,
            "tables": tables,
            "variation_axes": axes,
            "license_file_nearby": license_near(path),
        })
        result["shaping"] = shape_tests(path)
        cmap_ok = not missing_core
        shaping_ok = result["shaping"]["status"] == "pass"
        if cmap_ok and shaping_ok:
            result["status"] = "pass"
        elif not cmap_ok:
            result["status"] = "fail"
            result["errors"].append("missing one or more core Arabic codepoints")
        elif result["shaping"]["status"] == "not_run":
            result["status"] = "needs_shaping_test"
            result["errors"].append("HarfBuzz shaping was not run")
        else:
            result["status"] = "fail"
            result["errors"].append("one or more HarfBuzz samples produced missing glyphs")
    except Exception as exc:
        result["errors"].append(f"{type(exc).__name__}: {exc}")
    finally:
        if font is not None:
            font.close()
    return result

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw_fonts", help="Folder containing collected TTF/OTF files")
    parser.add_argument("--output", default="data/validation", help="Output folder for JSONL and summary")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero unless every file passes cmap and shaping checks")
    args = parser.parse_args()
    source = Path(args.input)
    output = Path(args.output)
    if not source.exists():
        parser.error(f"Input folder does not exist: {source}")
    files = sorted(p for p in source.rglob("*") if p.is_file() and p.suffix.lower() in {".ttf", ".otf"})
    if not files:
        parser.error(f"No TTF/OTF files found under: {source}")
    output.mkdir(parents=True, exist_ok=True)
    results = [inspect_font(path) for path in files]
    jsonl_path = output / "font_validation.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in results:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    counts = {}
    for row in results:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    report = {
        "input_directory": str(source),
        "files_examined": len(results),
        "status_counts": counts,
        "harfbuzz_available": hb is not None,
        "pass_criteria": "All U+0621..U+064A codepoints present and all HarfBuzz RTL samples produce no .notdef glyphs.",
        "warning": "A passing cmap/shaping check is technical screening, not proof of license compliance or visual quality.",
    }
    (output / "validation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Detailed results: {jsonl_path}")
    if args.strict and counts.get("pass", 0) != len(results):
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
