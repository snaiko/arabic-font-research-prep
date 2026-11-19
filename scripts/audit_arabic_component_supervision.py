#!/usr/bin/env python3
"""Independent integrity and geometric QA for paired Arabic component/caption records.

This verifies provenance, deterministic captions, hashes, split isolation and
measurable raster geometry. It does NOT certify spelling, calligraphic quality,
semantic component identity, legal permission, or expert visual correctness.
"""
from __future__ import annotations
import argparse, hashlib, json
from collections import defaultdict
from pathlib import Path
from PIL import Image

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def audit(manifest, image_root, expected_size=160):
    root=Path(image_root).resolve()
    errors=[]; warnings=[]; seen=set(); family_splits=defaultdict(set)
    count=component_count=caption_count=0; edge_touch=0; split_counts=defaultdict(int)
    for n,line in enumerate(Path(manifest).read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        try: row=json.loads(line)
        except Exception as exc:
            errors.append(f"line {n}: invalid JSON: {exc}"); continue
        ident=row.get("sample_id")
        if not ident or ident in seen: errors.append(f"line {n}: missing/duplicate sample_id")
        seen.add(ident)
        logical=row.get("logical_text","")
        cps=[f"U+{ord(ch):04X}" for ch in logical]
        if not logical or row.get("logical_codepoints")!=cps or row.get("codepoint_count")!=len(cps):
            errors.append(f"line {n}: logical text/codepoint metadata mismatch")
        gids=row.get("glyph_ids")
        if not isinstance(gids,list) or not gids or row.get("glyph_count")!=len(gids):
            errors.append(f"line {n}: glyph ID/count mismatch")
        if row.get("sample_id") != f'{row.get("font_sha256")}:{row.get("case_id")}:{row.get("cluster")}':
            errors.append(f"line {n}: sample identity is not source-derived")
        split=row.get("split"); family=row.get("family")
        if split not in {"train","validation","test"} or not family:
            errors.append(f"line {n}: missing family-safe split metadata")
        else:
            family_splits[family].add(split); split_counts[split]+=1
        image_rel=row.get("image",""); image=(root/image_rel).resolve()
        try: image.relative_to(root)
        except ValueError:
            errors.append(f"line {n}: image path escapes image root"); continue
        if not image.is_file():
            errors.append(f"line {n}: image missing"); continue
        if sha256(image)!=row.get("image_sha256"):
            errors.append(f"line {n}: image SHA-256 mismatch")
        try:
            with Image.open(image) as im:
                im.load()
                if im.size!=(expected_size,expected_size):
                    errors.append(f"line {n}: unexpected image dimensions {im.size}")
                gray=im.convert("L")
                ink=gray.point(lambda p:255 if p<245 else 0).getbbox()
                if ink is None: errors.append(f"line {n}: blank image")
                elif ink[0]==0 or ink[1]==0 or ink[2]>=im.width or ink[3]>=im.height:
                    edge_touch+=1
                    warnings.append(f"line {n}: ink touches crop boundary; inspect clipping risk")
        except Exception as exc: errors.append(f"line {n}: unreadable image: {exc}")
        comps=row.get("component_candidates")
        if not isinstance(comps,list) or row.get("component_candidate_count")!=len(comps):
            errors.append(f"line {n}: component candidate count mismatch"); comps=[]
        for k,c in enumerate(comps):
            box=c.get("bbox_normalized",[])
            centroid=c.get("centroid_normalized",[])
            area=c.get("area_ratio")
            if len(box)!=4 or not all(isinstance(x,(int,float)) and 0<=x<=1 for x in box) or box[0]>=box[2] or box[1]>=box[3]:
                errors.append(f"line {n}: component {k} has invalid normalized box")
            if len(centroid)!=2 or not all(isinstance(x,(int,float)) and 0<=x<=1 for x in centroid):
                errors.append(f"line {n}: component {k} has invalid centroid")
            if not isinstance(area,(int,float)) or not 0<area<=1:
                errors.append(f"line {n}: component {k} has invalid area ratio")
            if c.get("semantic_identity")!="unknown":
                errors.append(f"line {n}: unreviewed component must remain semantically unknown")
        captions=row.get("captions",{})
        for lang in ("ar","en"):
            cap=captions.get(lang,{})
            if not cap.get("text") or cap.get("language")!=lang or cap.get("provenance")!="machine_generated_unreviewed":
                errors.append(f"line {n}: {lang} caption missing or falsely marked reviewed")
            else: caption_count+=1
        prov=row.get("label_provenance",{})
        if prov.get("component_semantics")!="unknown_not_annotated" or prov.get("expert_visual_linguistic_approval") is not False or prov.get("training_eligible") is not False:
            errors.append(f"line {n}: unsafe promotion of machine labels")
        count+=1; component_count+=len(comps)
    for family,splits in family_splits.items():
        if len(splits)>1: errors.append(f"family split leakage: {family}")
    return {
      "schema_version":1,"status":"FAIL" if errors else ("PASS_WITH_GEOMETRY_WARNINGS" if warnings else "PASS"),
      "records":count,"components":component_count,"paired_caption_count":caption_count,
      "split_counts":dict(split_counts),"families":len(family_splits),
      "ink_touching_crop_boundary":edge_touch,"warnings":warnings,"errors":errors,
      "training_eligible_records":0,
      "scope":"Checks deterministic source identity, Unicode/codepoint and glyph counts, exact image hashes and dimensions, nonblank images, safe paths, normalized component geometry, caption language/provenance, family split isolation, and fail-closed semantic/approval flags. Boundary contact is a clipping-risk warning. This is not expert visual/linguistic review or legal clearance."
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",required=True); p.add_argument("--image-root",required=True)
    p.add_argument("--output",required=True); p.add_argument("--expected-size",type=int,default=160)
    a=p.parse_args(); report=audit(a.manifest,a.image_root,a.expected_size)
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(0 if report["status"] in {"PASS","PASS_WITH_GEOMETRY_WARNINGS"} else 2)
if __name__=="__main__": main()
