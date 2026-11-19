#!/usr/bin/env python3
"""Validate the versioned Arabic character registry without external dependencies."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

HEX = re.compile(r"^U\+[0-9A-F]{4,6}$")
JOINING = {"R", "L", "D", "C", "U", "T"}
FORMS = {"isol", "init", "medi", "fina"}
EXPECTED = {"R": {"isol", "fina"}, "L": {"isol", "init"}, "D": FORMS,
            "C": {"isol"}, "U": {"isol"}, "T": {"isol"}}

def validate(payload):
    errors = []
    if payload.get("schema_version") != 1:
        errors.append("unsupported schema_version")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        return ["records must be a non-empty list"]
    seen = set()
    for i, row in enumerate(records):
        prefix = f"records[{i}]"
        cp = row.get("codepoint")
        if not isinstance(cp, str) or not HEX.fullmatch(cp):
            errors.append(f"{prefix}: invalid codepoint")
            continue
        if cp in seen:
            errors.append(f"{prefix}: duplicate codepoint {cp}")
        seen.add(cp)
        try:
            actual = ord(row["character"])
            declared = int(cp[2:], 16)
            if actual != declared:
                errors.append(f"{prefix}: character/codepoint mismatch")
        except (KeyError, TypeError):
            errors.append(f"{prefix}: character must be one Unicode scalar")
        jt = row.get("joining_type")
        if jt not in JOINING:
            errors.append(f"{prefix}: invalid joining_type")
            continue
        forms = row.get("forms_supported_by_joining_type")
        if not isinstance(forms, list) or not forms or len(forms) != len(set(forms)):
            errors.append(f"{prefix}: forms must be a non-empty unique list")
        elif not set(forms) <= EXPECTED[jt]:
            errors.append(f"{prefix}: forms conflict with joining_type {jt}")
        if row.get("visual_family_status") != "provisional_human_grouping_not_unicode_property":
            errors.append(f"{prefix}: visual-family provenance must remain explicit")
        if row.get("component_annotation_status") != "not_annotated":
            errors.append(f"{prefix}: component labels require a separate audited annotation set")
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/arabic_character_system_v1.json")
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    errors = validate(payload)
    if errors:
        print(json.dumps({"status":"FAIL","errors":errors}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"status":"PASS","records":len(payload["records"]),
                      "unicode_version":payload["unicode_version"],
                      "scope_counts":{scope:sum(r["scope"]==scope for r in payload["records"])
                                      for scope in sorted({r["scope"] for r in payload["records"]})}},
                     ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
