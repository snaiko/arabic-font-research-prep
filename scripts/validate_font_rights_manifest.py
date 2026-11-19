#!/usr/bin/env python3
"""Validate explicit, per-file permission before fonts enter ML workflows."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def validate(manifest, font_root=None, require_files=True):
    errors=[]
    if manifest.get("schema_version") != 1 or not isinstance(manifest.get("fonts"),list):
        raise ValueError("Manifest must contain schema_version=1 and a fonts array.")
    seen=set()
    root=Path(font_root) if font_root else None
    for i,item in enumerate(manifest["fonts"]):
        prefix=f"fonts[{i}]"
        required=("font_file","family_id","sha256","license_name","license_url","ml_training_allowed",
                  "review_status","reviewed_by","reviewed_date","evidence")
        for key in required:
            if key not in item: errors.append(f"{prefix}: missing {key}")
        if any(key not in item for key in required): continue
        rel=Path(item["font_file"])
        if rel.is_absolute() or ".." in rel.parts: errors.append(f"{prefix}: font_file must be a safe relative path")
        if item["font_file"] in seen: errors.append(f"{prefix}: duplicate font_file")
        seen.add(item["font_file"])
        digest=str(item["sha256"]).lower()
        if len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest): errors.append(f"{prefix}: invalid SHA-256")
        if item["review_status"] not in ("approved","pending","rejected"): errors.append(f"{prefix}: invalid review_status")
        if item["ml_training_allowed"] is not True or item["review_status"]!="approved":
            errors.append(f"{prefix}: not explicitly approved for ML training")
        if not all(isinstance(item[k],str) and item[k].strip() for k in ("family_id","license_name","license_url","reviewed_by","reviewed_date")):
            errors.append(f"{prefix}: license, family, reviewer, date and URL must be non-empty strings")
        if not isinstance(item["evidence"],list) or not item["evidence"] or not all(isinstance(x,str) and x.strip() for x in item["evidence"]):
            errors.append(f"{prefix}: evidence must contain at least one non-empty reference")
        if root and require_files:
            path=(root/rel).resolve()
            try: path.relative_to(root.resolve())
            except ValueError: errors.append(f"{prefix}: font path escapes font_root"); continue
            if not path.is_file(): errors.append(f"{prefix}: font file not found: {path}"); continue
            actual=hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != digest: errors.append(f"{prefix}: SHA-256 mismatch for {item['font_file']}")
    if errors: raise ValueError("\n".join(errors))
    return {"status":"PASS","font_count":len(manifest["fonts"]),"approved_font_count":len(manifest["fonts"])}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",default="data/manifests/font_rights.json")
    p.add_argument("--font-root",default=None)
    p.add_argument("--allow-missing-files",action="store_true")
    a=p.parse_args()
    try:
        result=validate(json.loads(Path(a.manifest).read_text(encoding="utf-8")),a.font_root,not a.allow_missing_files)
    except (OSError,json.JSONDecodeError,ValueError) as exc: raise SystemExit(f"BLOCKED: {exc}")
    print(json.dumps(result,indent=2))
if __name__=="__main__": main()
