#!/usr/bin/env python3
"""Build deterministic, explicitly machine-derived Arabic cluster supervision.

These records pair canonical Unicode/HarfBuzz metadata with measurable raster
geometry. They are machine observations, NOT expert visual or linguistic labels.
"""
from __future__ import annotations
import argparse, hashlib, json, unicodedata
from pathlib import Path
from PIL import Image

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def read_jsonl(path):
    for n,line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(),1):
        if line.strip():
            try: yield json.loads(line)
            except json.JSONDecodeError as e: raise ValueError(f"{path}:{n}: {e}") from e

def rights_index(path):
    if path is None: return {}
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    return {x.get("font_sha256"):x for x in data.get("fonts",[]) if x.get("font_sha256")}

def measure(image_path: Path):
    with Image.open(image_path) as im:
        im.load()
        gray=im.convert("L")
        mask=gray.point(lambda p:255 if p<245 else 0)
        bbox=mask.getbbox()
        if bbox is None: raise ValueError("blank_image")
        w,h=mask.size
        pixels=list(mask.getdata())
        ink=[1 if p else 0 for p in pixels]
        count=sum(ink)
        xs=[]; ys=[]
        for y in range(h):
            for x in range(w):
                if ink[y*w+x]: xs.append(x); ys.append(y)
        x0,y0,x1,y1=bbox
        # Fixed-length normalized row/column occupancy profiles.
        row=[]; col=[]
        for i in range(16):
            ya=i*h//16; yb=(i+1)*h//16
            row.append(round(sum(ink[yy*w+x] for yy in range(ya,yb) for x in range(w))/max(1,(yb-ya)*w),6))
        for i in range(16):
            xa=i*w//16; xb=(i+1)*w//16
            col.append(round(sum(ink[y*w+x] for y in range(h) for x in range(xa,xb))/max(1,h*(xb-xa)),6))
        return {
            "canvas_width":w,"canvas_height":h,
            "ink_bbox_xyxy":[x0,y0,x1,y1],
            "ink_bbox_normalized":[round(x0/w,6),round(y0/h,6),round(x1/w,6),round(y1/h,6)],
            "ink_pixel_ratio":round(count/(w*h),8),
            "ink_centroid_normalized":[round(sum(xs)/count/w,6),round(sum(ys)/count/h,6)],
            "row_occupancy_16":row,"column_occupancy_16":col
        }

def build(manifest, crop_root, output, rights_path=None):
    root=Path(crop_root).resolve(); rights=rights_index(rights_path)
    out=Path(output); out.parent.mkdir(parents=True,exist_ok=True)
    count=0; eligible=0; seen=set()
    with out.open("w",encoding="utf-8") as dst:
        for row in read_jsonl(manifest):
            image=(root/row["image"]).resolve()
            try: image.relative_to(root)
            except ValueError: raise ValueError(f"unsafe image path: {row['image']}")
            if not image.is_file(): raise FileNotFoundError(image)
            digest=sha256(image)
            if digest in seen: raise ValueError(f"duplicate image hash: {digest}")
            seen.add(digest)
            logical=row["logical_text"]
            chars=list(logical)
            cps=[f"U+{ord(c):04X}" for c in chars]
            categories=[unicodedata.category(c) for c in chars]
            right=rights.get(row.get("font_sha256"),{})
            allowed=bool(right.get("ml_training_allowed") is True and right.get("review_status")=="approved")
            record={
                "schema_version":1,
                "sample_id":f"{row['font_sha256']}:{row['case_id']}:{row['cluster']}",
                "image":row["image"],"image_sha256":digest,
                "font_sha256":row["font_sha256"],"family":row.get("family"),
                "split":row.get("split"),"case_id":row["case_id"],
                "source_text":row["source_text"],"logical_text":logical,
                "logical_codepoints":cps,"unicode_categories":categories,
                "codepoint_count":len(chars),"glyph_ids":row["glyph_ids"],
                "glyph_count":row["glyph_count"],
                "is_multicodepoint_cluster":len(chars)>1,
                "combining_mark_count":sum(1 for c in chars if unicodedata.category(c).startswith("M")),
                "nonrendering_source_codepoints":row.get("nonrendering_source_codepoints",[]),
                "direction":row["direction"],"script":row["script"],
                "language":row["language"],"features":row["features"],
                "raster_geometry":measure(image),
                "supervision_provenance":{
                    "text_and_shaping":"canonical_source_plus_harfbuzz",
                    "geometry":"deterministic_thresholded_raster_measurements",
                    "semantic_or_artistic_truth":"not_assessed",
                    "rights_status":"approved" if allowed else "not_approved",
                    "training_eligible":allowed
                }
            }
            dst.write(json.dumps(record,ensure_ascii=False,sort_keys=True)+"\n")
            count+=1; eligible+=int(allowed)
    return {"status":"PASS" if count else "FAIL","records":count,
            "unique_images":len(seen),"rights_approved_records":eligible,
            "not_rights_approved_records":count-eligible,
            "note":"Geometry fields are deterministic raster measurements, not human-verified component labels. Unapproved assets remain in the research export but are explicitly ineligible for training."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",required=True); p.add_argument("--crop-root",required=True)
    p.add_argument("--output",required=True); p.add_argument("--rights-manifest")
    a=p.parse_args()
    result=build(a.manifest,a.crop_root,a.output,a.rights_manifest)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result["status"]=="PASS" else 2)
if __name__=="__main__": main()
