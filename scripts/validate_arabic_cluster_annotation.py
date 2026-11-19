#!/usr/bin/env python3
"""Validate cluster-level annotation drafts against their source manifest and pixels."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from PIL import Image

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()

def load(path):
 return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]

def validate(annotation_path, source_manifest, output_root):
 root=Path(output_root).resolve(); source={ (r["font_sha256"],r["case_id"],r["cluster"]):r for r in load(source_manifest) }
 errors=[]; records=load(annotation_path); seen=set()
 for i,r in enumerate(records,1):
  p=f"record {i}"; c=r.get("cluster",{}); key=(c.get("font_sha256"),c.get("case_id"),c.get("cluster_index"))
  if key in seen: errors.append(f"{p}: duplicate source cluster")
  seen.add(key); src=source.get(key)
  if src is None: errors.append(f"{p}: source cluster not found"); continue
  for field in ("font_file","logical_start","logical_end","source_text","logical_text","logical_codepoints","glyph_ids","glyph_count","direction","script","language","features","canvas"):
   if c.get(field)!=src.get(field): errors.append(f"{p}: {field} differs from source")
  if c.get("font_sha256")!=src.get("font_sha256"): errors.append(f"{p}: font hash mismatch")
  image=r.get("image",""); target=(root/image).resolve()
  try: target.relative_to(root)
  except ValueError: errors.append(f"{p}: image escapes output root"); continue
  if not target.is_file(): errors.append(f"{p}: image missing"); continue
  if sha(target)!=r.get("image_sha256"): errors.append(f"{p}: image hash mismatch")
  try:
   with Image.open(target) as im:
    im.load()
    if im.size!=(160,160): errors.append(f"{p}: image dimensions mismatch")
  except Exception as e: errors.append(f"{p}: unreadable image: {e}")
  if r.get("status")!="draft": errors.append(f"{p}: generated record must remain draft")
 return {"status":"PASS" if records and not errors else "FAIL","annotation_count":len(records),"source_cluster_matches":len(records)-len([e for e in errors if "source cluster not found" in e]),"errors":errors,
 "scope":"Validates source identity, multi-codepoint/multi-glyph metadata, image integrity and draft status; does not validate visual/linguistic correctness."}

def main():
 p=argparse.ArgumentParser(); p.add_argument("--annotations",required=True); p.add_argument("--source-manifest",required=True); p.add_argument("--output-root",required=True); p.add_argument("--report")
 a=p.parse_args(); result=validate(a.annotations,a.source_manifest,a.output_root)
 print(json.dumps(result,ensure_ascii=False,indent=2))
 if a.report: Path(a.report).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 raise SystemExit(0 if result["status"]=="PASS" else 2)
if __name__=="__main__": main()
