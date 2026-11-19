#!/usr/bin/env python3
"""Compare two independent polygon annotation JSONL files using per-kind IoU matching."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from validate_glyph_visual_annotation import validate

KINDS=("body","dot","hamza","diacritic","other_mark","counter","join_region","stroke_segment","ornament","uncertain")

def inside(x,y,poly):
    hit=False
    j=len(poly)-1
    for i,(xi,yi) in enumerate(poly):
        xj,yj=poly[j]
        if ((yi>y)!=(yj>y)) and x < (xj-xi)*(y-yi)/(yj-yi+1e-15)+xi: hit=not hit
        j=i
    return hit

def raster(poly,resolution):
    points=poly["geometry"]["points"]
    occupied=set()
    for yy in range(resolution):
        y=(yy+0.5)/resolution
        for xx in range(resolution):
            x=(xx+0.5)/resolution
            if inside(x,y,points): occupied.add((xx,yy))
    return occupied

def iou(a,b,resolution):
    aa,bb=raster(a,resolution),raster(b,resolution)
    union=len(aa|bb)
    return len(aa&bb)/union if union else 1.0

def compare_records(left,right,threshold=0.5,resolution=256):
    errors=validate(left)+validate(right)
    if errors: raise ValueError("Invalid annotation record: "+"; ".join(errors))
    for key in ("font_sha256","render_sha256","codepoint","glyph_id"):
        if left["glyph_instance"].get(key)!=right["glyph_instance"].get(key):
            raise ValueError(f"Annotators do not refer to the same glyph instance: {key}")
    per_kind={}
    for kind in KINDS:
        a=[x for x in left["components"] if x["kind"]==kind]
        b=[x for x in right["components"] if x["kind"]==kind]
        candidates=[]
        for i,ca in enumerate(a):
            for j,cb in enumerate(b):
                candidates.append((iou(ca,cb,resolution),i,j))
        candidates.sort(reverse=True)
        used_a,used_b,matched=set(),set(),[]
        for score,i,j in candidates:
            if score<threshold: break
            if i not in used_a and j not in used_b:
                used_a.add(i); used_b.add(j); matched.append(score)
        tp=len(matched); fp=len(b)-tp; fn=len(a)-tp
        precision=tp/(tp+fp) if tp+fp else 1.0
        recall=tp/(tp+fn) if tp+fn else 1.0
        f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
        per_kind[kind]={
            "annotator_a_count":len(a),"annotator_b_count":len(b),
            "matched_count":tp,"unmatched_a":fn,"unmatched_b":fp,
            "precision":round(precision,4),"recall":round(recall,4),"f1":round(f1,4),
            "mean_matched_iou":round(sum(matched)/tp,4) if tp else None
        }
    return {
        "sample":{"render_sha256":left["glyph_instance"]["render_sha256"],
                  "font_sha256":left["glyph_instance"]["font_sha256"],
                  "codepoint":left["glyph_instance"]["codepoint"],
                  "glyph_id":left["glyph_instance"]["glyph_id"]},
        "matching":{"method":"greedy one-to-one maximum-IoU matching per component kind",
                    "iou_threshold":threshold,"raster_resolution":resolution},
        "per_kind":per_kind,
        "warning":"Raster IoU is an approximate geometry agreement measure, not a measure of linguistic correctness or artistic quality."
    }

def load_jsonl(path):
    rows={}
    for n,line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        obj=json.loads(line); key=obj["glyph_instance"]["render_sha256"]
        if key in rows: raise ValueError(f"{path}:{n}: duplicate render_sha256")
        rows[key]=obj
    return rows

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--annotator-a",required=True); p.add_argument("--annotator-b",required=True)
    p.add_argument("--output",default="reports/local/annotation_agreement.json")
    p.add_argument("--iou-threshold",type=float,default=0.5)
    p.add_argument("--resolution",type=int,default=256)
    a=p.parse_args()
    if not 0<a.iou_threshold<=1 or a.resolution<16: p.error("threshold must be in (0,1] and resolution >= 16")
    aa,bb=load_jsonl(a.annotator_a),load_jsonl(a.annotator_b)
    if set(aa)!=set(bb): raise SystemExit("Annotator files must contain the same render_sha256 sample set.")
    results=[compare_records(aa[k],bb[k],a.iou_threshold,a.resolution) for k in sorted(aa)]
    aggregate={}
    for kind in KINDS:
        rows=[r["per_kind"][kind] for r in results]
        n=sum(x["matched_count"] for x in rows)
        aggregate[kind]={
            "samples":len(rows),
            "mean_f1":round(sum(x["f1"] for x in rows)/len(rows),4) if rows else None,
            "micro_precision":round(sum(x["matched_count"] for x in rows)/sum(x["matched_count"]+x["unmatched_b"] for x in rows),4) if rows and sum(x["matched_count"]+x["unmatched_b"] for x in rows) else 1.0,
            "micro_recall":round(sum(x["matched_count"] for x in rows)/sum(x["matched_count"]+x["unmatched_a"] for x in rows),4) if rows and sum(x["matched_count"]+x["unmatched_a"] for x in rows) else 1.0,
            "mean_matched_iou":round(sum(x["mean_matched_iou"] for x in rows if x["mean_matched_iou"] is not None)/sum(x["mean_matched_iou"] is not None for x in rows),4) if any(x["mean_matched_iou"] is not None for x in rows) else None
        }
    output={"schema_version":1,"samples_compared":len(results),"aggregate":aggregate,"samples":results}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","samples_compared":len(results),"output":a.output},indent=2))

if __name__=="__main__": main()
