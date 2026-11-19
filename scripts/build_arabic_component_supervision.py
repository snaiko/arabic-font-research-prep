#!/usr/bin/env python3
"""Create machine-derived Arabic component candidates and paired factual captions.

Connected components and caption templates are observations/candidates only.
They do not identify dots/hamza semantically or certify artistic correctness.
"""
from __future__ import annotations
import argparse, hashlib, json, unicodedata
from collections import deque
from pathlib import Path
from PIL import Image

def load_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def components(image_path, threshold=245):
    with Image.open(image_path) as im:
        gray=im.convert("L"); w,h=gray.size
        pixels=[1 if p<threshold else 0 for p in gray.getdata()]
    visited=bytearray(w*h); found=[]
    for start,value in enumerate(pixels):
        if not value or visited[start]: continue
        q=deque([start]); visited[start]=1; xs=[]; ys=[]
        while q:
            idx=q.popleft(); x=idx%w; y=idx//w; xs.append(x); ys.append(y)
            for ny in range(max(0,y-1),min(h,y+2)):
                base=ny*w
                for nx in range(max(0,x-1),min(w,x+2)):
                    ni=base+nx
                    if pixels[ni] and not visited[ni]:
                        visited[ni]=1; q.append(ni)
        count=len(xs); x0=min(xs); x1=max(xs)+1; y0=min(ys); y1=max(ys)+1
        found.append({"bbox_xyxy":[x0,y0,x1,y1],"area_pixels":count,
          "area_ratio":round(count/(w*h),8),
          "centroid_normalized":[round(sum(xs)/count/w,6),round(sum(ys)/count/h,6)],
          "bbox_normalized":[round(x0/w,6),round(y0/h,6),round(x1/w,6),round(y1/h,6)]})
    found.sort(key=lambda c:(c["bbox_xyxy"][1],c["bbox_xyxy"][0],-c["area_pixels"]))
    total=sum(x["area_pixels"] for x in found)
    for i,item in enumerate(found):
        item["component_index"]=i
        item["relative_area"]=round(item["area_pixels"]/max(1,total),8)
        item["role_candidate"]="largest_ink_component_candidate" if item["area_pixels"]==max(x["area_pixels"] for x in found) else "detached_ink_component_candidate"
        item["semantic_identity"]="unknown"
    return found

def build(manifest,crop_root,registry_path,output):
    rows=load_jsonl(manifest)
    registry=json.loads(Path(registry_path).read_text(encoding="utf-8"))
    lookup={r["codepoint"]:r for r in registry["records"]}\n    context_lookup={r["codepoint"]:r for r in registry.get("contextual_joining_properties",[])}
    root=Path(crop_root).resolve(); out=Path(output); out.parent.mkdir(parents=True,exist_ok=True)
    seen=set(); count=0; caption_rows=0; component_total=0
    with out.open("w",encoding="utf-8") as dst:
        for row in rows:
            key=(row["font_sha256"],row["case_id"],row["cluster"])
            if key in seen: raise ValueError(f"duplicate cluster identity: {key}")
            seen.add(key)
            image=(root/row["image"]).resolve()
            try: image.relative_to(root)
            except ValueError: raise ValueError(f"unsafe image path: {row['image']}")
            if not image.is_file(): raise FileNotFoundError(image)
            logical=row["logical_text"]; cps=[f"U+{ord(ch):04X}" for ch in logical]
            semantic=[]
            for ch,cp in zip(logical,cps):
                record=lookup.get(cp) or context_lookup.get(cp)
                semantic.append({
                  "codepoint":cp,"character":ch,
                  "unicode_name":record["unicode_name"] if record else unicodedata.name(ch,"UNKNOWN"),
                  "general_category":record["general_category"] if record else unicodedata.category(ch),
                  "script_registry_role":record["role"] if record else "not_in_arabic_script_registry",
                  "joining_type":record["joining_type"] if record else ("T" if unicodedata.category(ch) in {"Mn","Me","Cf"} else "U"),
                  "joining_group":record["joining_group"] if record else "No_Joining_Group",
                  "is_combining_mark":bool(record["is_combining_mark"]) if record else unicodedata.category(ch).startswith("M")
                })
            marks=sum(1 for x in semantic if x["is_combining_mark"])
            comps=components(image); component_total+=len(comps)
            glyph_count=row["glyph_count"]; cp_count=len(cps)
            mapping_hint=("possible_ligature_or_substitution" if cp_count>1 and glyph_count==1 else
                          "multi_glyph_cluster" if glyph_count>1 else "single_codepoint_single_glyph_candidate")
            caption_ar=(f"عينة خط عربي من النص «{logical}»: تتكون من {cp_count} محارف Unicode و{glyph_count} معرّفات محارف مرسومة، "
                        f"وتحتوي على {marks} علامات مركبة و{len(comps)} مكونات حبر منفصلة قابلة للقياس. "
                        f"تصنيف العلاقة بين النص والمحارف: {mapping_hint}. هذه أوصاف آلية ولا تحدد هوية النقاط أو الهمزات بصرياً.")
            caption_en=(f"Arabic text cluster {logical!r}: {cp_count} Unicode code points, {glyph_count} shaped glyph IDs, "
                        f"{marks} combining marks, and {len(comps)} disconnected raster ink components. "
                        f"Mapping hint: {mapping_hint}. Machine-generated factual caption; detached components are not semantically identified.")
            record={
              "schema_version":1,"sample_id":f"{row['font_sha256']}:{row['case_id']}:{row['cluster']}",
              "image":row["image"],"image_sha256":digest(image),
              "font_sha256":row["font_sha256"],"family":row.get("family"),"split":row.get("split"),
              "case_id":row["case_id"],"source_text":row["source_text"],"logical_text":logical,
              "logical_codepoints":cps,"unicode_character_metadata":semantic,
              "codepoint_count":cp_count,"glyph_ids":row["glyph_ids"],"glyph_count":glyph_count,
              "combining_mark_count":marks,"mapping_hint":mapping_hint,
              "component_candidates":comps,
              "component_candidate_count":len(comps),
              "captions":{
                "ar":{"text":caption_ar,"language":"ar","provenance":"machine_generated_unreviewed","template_version":"ar-factual-v1"},
                "en":{"text":caption_en,"language":"en","provenance":"machine_generated_unreviewed","template_version":"en-factual-v1"}
              },
              "label_provenance":{
                "unicode_metadata":"Unicode 17.0 Arabic script registry and Python Unicode categories",
                "glyph_mapping":"independently audited HarfBuzz cluster metadata",
                "components":"8-connected components at grayscale threshold <245",
                "component_semantics":"unknown_not_annotated",
                "caption_truth":"deterministic_template_from_source_metadata",
                "expert_visual_linguistic_approval":False,
                "training_eligible":False
              }
            }
            dst.write(json.dumps(record,ensure_ascii=False,sort_keys=True)+"\n")
            count+=1; caption_rows+=2
    return {"status":"PASS" if count else "FAIL","records":count,"paired_captions":caption_rows,
      "component_candidates":component_total,"unicode_registry_version":registry.get("unicode_version"),
      "note":"All component identities remain unknown. Captions are synthetic factual templates; no semantic dot/hamza segmentation or expert approval is claimed."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",required=True); p.add_argument("--crop-root",required=True)
    p.add_argument("--registry",required=True); p.add_argument("--output",required=True)
    a=p.parse_args(); result=build(a.manifest,a.crop_root,a.registry,a.output)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result["status"]=="PASS" else 2)
if __name__=="__main__": main()
