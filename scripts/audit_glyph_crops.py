#!/usr/bin/env python3
"""Audit generated isolated Arabic glyph crops and their font/image provenance."""
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter, defaultdict
from pathlib import Path
from PIL import Image

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def audit(manifest: Path, crop_root: Path, font_root: Path) -> dict:
    rows = []
    with manifest.open(encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                try: rows.append(json.loads(line))
                except json.JSONDecodeError as e: raise ValueError(f"{manifest}:{n}: {e}") from e
    errors, seen, fonts, family_splits = [], set(), {}, defaultdict(set)
    for n, row in enumerate(rows, 1):
        cp = row.get("codepoint", "")
        char = row.get("unicode_char", "")
        digest = row.get("font_sha256", "")
        family, split, image = row.get("family"), row.get("split"), row.get("image")
        if not (isinstance(digest, str) and len(digest) == 64):
            errors.append(f"row {n}: invalid font SHA-256"); continue
        try:
            if not cp.startswith("U+") or int(cp[2:], 16) != ord(char) or len(char) != 1:
                errors.append(f"row {n}: codepoint/unicode_char mismatch")
        except (ValueError, TypeError, AttributeError):
            errors.append(f"row {n}: invalid codepoint/unicode_char")
        if row.get("sample_type") != "isolated_single_codepoint" or row.get("contextual_joining_supervision") is not False:
            errors.append(f"row {n}: crop is mislabeled as contextual supervision")
        if not family or split not in {"train", "validation", "test"}:
            errors.append(f"row {n}: missing family or invalid split")
        else: family_splits[family].add(split)
        key = (digest, cp)
        if key in seen: errors.append(f"row {n}: duplicate font/codepoint crop")
        seen.add(key)
        font_value = row.get("font_file")
        if font_value:
            p = Path(font_value)
            candidates = [p, font_root / p, font_root / p.name]
            actual = next((x.resolve() for x in candidates if x.is_file()), None)
            if actual is None: errors.append(f"row {n}: source font missing")
            elif sha256(actual) != digest: errors.append(f"row {n}: source font hash mismatch")
            fonts[digest] = actual
        if not image:
            errors.append(f"row {n}: missing image path"); continue
        root = crop_root.resolve()
        target = (root / image).resolve()
        try: target.relative_to(root)
        except ValueError:
            errors.append(f"row {n}: image path escapes crop root"); continue
        if not target.is_file():
            errors.append(f"row {n}: crop image missing: {image}"); continue
        try:
            with Image.open(target) as im:
                im.load()
                if im.mode != "L" or im.size != (128, 128):
                    errors.append(f"row {n}: expected 128x128 grayscale PNG")
                if im.point(lambda p: 255 if p < 245 else 0).getbbox() is None:
                    errors.append(f"row {n}: blank crop")
        except Exception as e:
            errors.append(f"row {n}: unreadable image: {e}")
    for family, splits in family_splits.items():
        if len(splits) != 1: errors.append(f"family split leakage in crop manifest: {family}")
    counts = Counter(r.get("split") for r in rows)
    return {"schema_version": 1, "status": "PASS" if rows and not errors else "FAIL",
            "crop_count": len(rows), "distinct_font_hashes": len(fonts),
            "distinct_families": len(family_splits), "split_crop_counts": dict(counts),
            "errors": errors,
            "scope": "Verifies crop file integrity, provenance, uniqueness and split consistency; does not verify visual correctness or training rights."}

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", default="data/glyph_crops/glyph_crops.jsonl")
    p.add_argument("--crop-root", default="data/glyph_crops")
    p.add_argument("--font-root", default="data/raw_fonts")
    p.add_argument("--output", default="reports/local/glyph_crop_audit.json")
    a = p.parse_args()
    report = audit(Path(a.manifest), Path(a.crop_root), Path(a.font_root))
    out = Path(a.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2

if __name__ == "__main__":
    raise SystemExit(main())
