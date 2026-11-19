#!/usr/bin/env python3
"""Fail-closed audit for dataset family splits, raster provenance, and source rights."""
from __future__ import annotations
import argparse, hashlib, json
from collections import defaultdict
from pathlib import Path

SPLITS={"train","validation","test"}
def read_jsonl(path):
    rows=[]
    with Path(path).open(encoding="utf-8") as f:
        for n,line in enumerate(f,1):
            if line.strip():
                try: rows.append(json.loads(line))
                except json.JSONDecodeError as e: raise ValueError(f"{path}:{n}: {e}") from e
    return rows

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def audit(samples_path, font_root=None, image_root=None, source_assets_path=None):
    rows=read_jsonl(samples_path)
    if not rows: raise ValueError("samples manifest is empty")
    family_splits=defaultdict(set); font_family=defaultdict(set); errors=[]
    seen=set(); image_count=0
    root=Path(font_root).resolve() if font_root else None
    imgroot=Path(image_root).resolve() if image_root else None
    for i,row in enumerate(rows,1):
        family=row.get("family"); split=row.get("split"); font_hash=row.get("font_sha256")
        if not family or split not in SPLITS or not font_hash:
            errors.append(f"row {i}: missing family, valid split, or font_sha256"); continue
        family_splits[family].add(split); font_family[font_hash].add(family)
        key=(font_hash,row.get("sample_type"),row.get("target_char"),row.get("text"),row.get("target_index_logical", row.get("target_index")))
        if key in seen: errors.append(f"row {i}: duplicate sample identity")
        seen.add(key)
        if root:
            raw=row.get("font_file")
            if not raw: errors.append(f"row {i}: missing font_file"); continue
            p=Path(raw)
            candidates=[p,root/p,root/p.name]
            found=next((x.resolve() for x in candidates if x.is_file()),None)
            if not found: errors.append(f"row {i}: font file not found: {raw}")
            elif sha256(found)!=font_hash: errors.append(f"row {i}: font SHA-256 mismatch: {raw}")
        if imgroot:
            raw=row.get("image")
            if not raw: errors.append(f"row {i}: missing image path"); continue
            p=(imgroot/raw).resolve()
            try: p.relative_to(imgroot)
            except ValueError: errors.append(f"row {i}: image path escapes image root"); continue
            if not p.is_file(): errors.append(f"row {i}: image missing: {raw}")
            else: image_count+=1
    for family,splits in family_splits.items():
        if len(splits)>1: errors.append(f"family leakage: {family} occurs in {sorted(splits)}")
    for digest,families in font_family.items():
        if len(families)>1: errors.append(f"font hash maps to multiple family IDs: {digest}")
    source_asset_count=None
    if source_assets_path:
        assets=read_jsonl(source_assets_path); source_asset_count=len(assets)
        ids=set()
        for i,a in enumerate(assets,1):
            if not a.get("asset_id") or a["asset_id"] in ids: errors.append(f"source asset row {i}: missing/duplicate asset_id")
            ids.add(a.get("asset_id"))
            if a.get("training_permission")!="approved":
                errors.append(f"source asset {a.get('asset_id')}: training permission is not approved")
            if not a.get("sha256") or len(a["sha256"])!=64:
                errors.append(f"source asset {a.get('asset_id')}: missing/invalid SHA-256")
            if not a.get("evidence_url") or not a.get("reviewed_by") or not a.get("review_date"):
                errors.append(f"source asset {a.get('asset_id')}: missing rights evidence/reviewer/date")
    report={"schema_version":1,"status":"PASS" if not errors else "FAIL",
      "sample_count":len(rows),"font_file_count":len(font_family),
      "family_count":len(family_splits),"family_split_counts":{s:sum(s in v for v in family_splits.values()) for s in sorted(SPLITS)},
      "image_files_verified":image_count if imgroot else None,
      "source_asset_records":source_asset_count,"errors":errors,
      "note":"PASS verifies the supplied manifests/files and split invariants only; it does not certify legal interpretation, visual quality, or annotation correctness."}
    if errors: raise AuditFailure(report)
    return report

class AuditFailure(ValueError):
    def __init__(self,report): self.report=report; super().__init__("\n".join(report["errors"]))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--samples",default="data/training_samples/samples.jsonl")
    p.add_argument("--font-root",default=None)
    p.add_argument("--image-root",default=None)
    p.add_argument("--source-assets",default=None)
    p.add_argument("--output",default="reports/local/dataset_audit.json")
    a=p.parse_args()
    try: report=audit(a.samples,a.font_root,a.image_root,a.source_assets)
    except (OSError,ValueError) as e:
        report=e.report if isinstance(e,AuditFailure) else {"status":"BLOCKED","error":str(e)}
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report["status"]=="PASS" else 2
if __name__=="__main__": raise SystemExit(main())
