#!/usr/bin/env python3
"""Validate the font-level JSONL manifest using only the Python standard library."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED = {
    "font_id", "family", "style", "file_name", "source_url",
    "license", "license_url", "version", "sha256", "split",
}
SPLITS = {"train", "validation", "test"}
SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    family_splits: dict[str, set[str]] = {}

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [f"Cannot read {path}: {exc}"]

    for line_no, line in enumerate(lines, 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_no}: invalid JSON: {exc}")
            continue
        if not isinstance(row, dict):
            errors.append(f"line {line_no}: each JSONL row must be an object")
            continue

        missing = sorted(REQUIRED - row.keys())
        if missing:
            errors.append(f"line {line_no}: missing fields: {', '.join(missing)}")
            continue

        font_id = str(row["font_id"]).strip()
        family = str(row["family"]).strip().casefold()
        split = row["split"]
        if not font_id:
            errors.append(f"line {line_no}: font_id is empty")
        elif font_id in seen_ids:
            errors.append(f"line {line_no}: duplicate font_id {font_id!r}")
        seen_ids.add(font_id)

        if not family:
            errors.append(f"line {line_no}: family is empty")
        if split not in SPLITS:
            errors.append(f"line {line_no}: split must be one of {sorted(SPLITS)}")
        else:
            family_splits.setdefault(family, set()).add(split)

        if not SHA256.fullmatch(str(row["sha256"])):
            errors.append(f"line {line_no}: sha256 must contain exactly 64 hexadecimal characters")
        for field in ("source_url", "license", "license_url", "file_name", "version"):
            value = str(row[field]).strip()
            if not value or value.startswith("REPLACE_"):
                errors.append(f"line {line_no}: {field} is still a placeholder or empty")

    for family, splits in family_splits.items():
        if len(splits) > 1:
            errors.append(
                f"family {family!r} appears in multiple splits: {', '.join(sorted(splits))}"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    errors = validate(args.manifest)
    if errors:
        print("\n".join(f"ERROR: {item}" for item in errors), file=sys.stderr)
        return 1
    print(f"Manifest structure OK: {args.manifest}")
    print("Note: this checks metadata structure, not license validity or font contents.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
