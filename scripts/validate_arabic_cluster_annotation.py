#!/usr/bin/env python3
"""Validate cluster-level annotation drafts against source metadata and pixels."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from PIL import Image

HEX64=re.compile(r"^[0-9a-f]{64}$")
CP=re.compile(r"^U\\+[0-9A-F]{4,6}$")
PENDING={"pending","pass","fail","uncertain"}

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()

def load(path):
 return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]

def validate(annotation_path, source_manifest, output_root):
 root=Path(output_root).resolve()
 source={}
 for row in load(source_manifest):
  key=(row.get("font_sha256"),row.get("case_id"),row.get("cluster"))
  if key in source: raise ValueError(f"duplicate source key: {key}")
  source[key]=row
 errors=[]; records=load(annotation_path); seen=set()
 required=("font_file","font_sha256","family","split","case_id","cluster_index","logical_start","logical_end","source_text","logical_text","logical_codepoints","glyph_ids","glyph_count","nonrendering_source_codepoints","direction","script","language","features","canvas")
 assessment_fields=("cluster_readable","text_mapping","joining_continuity","ligature_formation","mark_attachment","dot_completeness","bidi_order","clipping_or_render_defect")
 for i,r in enumerate(records,1):
  p=f"record {i}"
  if r.get("schema_version")!=1 or r.get("status")!="draft": errors.append(f"{p}: invalid version or non-draft status")
  c=r.get("cluster")
  if not isinstance(c,dict): errors.append(f"{p}: cluster object missing"); continue
  missing=[k for k in required if k not in c]
  if missing: errors.append(f"{p}: missing cluster fields {missing}"); continue
  key=(c["font_sha256"],c["case_id"],c["cluster_index"])
  if key in seen: errors.append(f"{p}: duplicate source cluster")
  seen.add(key); src=source.get(key)
  if src is None: errors.append(f"{p}: source cluster not found"); continue
  mapping={"font_file":"font_file","font_sha256":"font_sha256","family":"family","split":"split","logical_start":"logical_start","logical_end":"logical_end","source_text":"source_text","logical_text":"logical_text","logical_codepoints":"logical_codepoints","glyph_ids":"glyph_ids","glyph_count":"glyph_count","nonrendering_source_codepoints":"nonrendering_source_codepoints","direction":"direction","script":"script","language":"language","features":"features","canvas":"canvas"}
  for field,source_field in mapping.items():
   if c.get(field)!=src.get(source_field): errors.append(f"{p}: {field} differs from source")
  if not HEX64.fullmatch(str(c["font_sha256"])): errors.append(f"{p}: invalid font SHA-256")
  cps=c["logical_codepoints"]; gids=c["glyph_ids"]
  if not isinstance(cps,list) or not cps or any(not isinstance(x,str) or not CP.fullmatch(x) for x in cps): errors.append(f"{p}: invalid logical codepoints")
  if not isinstance(gids,list) or not gids or any(not isinstance(x,int) or x<0 for x in gids): errors.append(f"{p}: invalid glyph IDs")
  if isinstance(gids,list) and c["glyph_count"]!=len(gids): errors.append(f"{p}: glyph_count does not match glyph_ids")
  if not isinstance(c["logical_start"],int) or not isinstance(c["logical_end"],int) or c["logical_start"]<0 or c["logical_end"]<=c["logical_start"]: errors.append(f"{p}: invalid logical span")
  if not isinstance(c["nonrendering_source_codepoints"],list): errors.append(f"{p}: invalid nonrendering source codepoints")
  a=r.get("assessment",{})
  if not isinstance(a,dict) or any(a.get(k) not in PENDING for k in assessment_fields): errors.append(f"{p}: invalid assessment fields")
  if not HEX64.fullmatch(str(r.get("image_sha256",""))): errors.append(f"{p}: invalid image SHA-256")
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
 return {"status":"PASS" if records and not errors else "FAIL","annotation_count":len(records),"source_cluster_matches":sum(1 for r in records if (r.get("cluster",{}).get("font_sha256"),r.get("cluster",{}).get("case_id"),r.get("cluster",{}).get("cluster_index")) in source),"errors":errors,"scope":"Validates schema-critical fields, exact source identity including non-rendering controls, cluster/codepoint/glyph cardinalities, image integrity and draft status; does not validate visual or linguistic correctness."}

def main():
 p=argparse.ArgumentParser(); p.add_argument("--annotations",required=True); p.add_argument("--source-manifest",required=True); p.add_argument("--output-root",required=True); p.add_argument("--report")
 a=p.parse_args(); result=validate(a.annotations,a.source_manifest,a.output_root)
 print(json.dumps(result,ensure_ascii=False,indent=2))
 if a.report: Path(a.report).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 raise SystemExit(0 if result["status"]=="PASS" else 2)
if __name__=="__main__": main()
