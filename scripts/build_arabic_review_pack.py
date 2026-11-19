#!/usr/bin/env python3
"""Build a deterministic, stratified human review pack from contextual cluster crops."""
from __future__ import annotations
import argparse, csv, hashlib, html, json, random, shutil
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone

def read_jsonl(path):
    rows=[]
    for n,line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(),1):
        if line.strip():
            try: rows.append(json.loads(line))
            except Exception as e: raise ValueError(f"{path}:{n}: {e}") from e
    return rows

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def pick_stratified(rows, per_case, seed):
    rng=random.Random(seed)
    groups=defaultdict(list)
    for row in rows: groups[row["case_id"]].append(row)
    selected=[]
    for case in sorted(groups):
        pool=groups[case][:]
        rng.shuffle(pool)
        # Round-robin families to avoid letting large families dominate a case.
        by_family=defaultdict(list)
        for row in pool: by_family[row.get("family","unknown")].append(row)
        family_names=sorted(by_family)
        for name in family_names: rng.shuffle(by_family[name])
        count=0
        while count<per_case and any(by_family.values()):
            for name in family_names:
                if by_family[name] and count<per_case:
                    selected.append(by_family[name].pop())
                    count+=1
    return selected

def annotation_template(row, image_hash, reviewer, annotation_id, created):
    codepoints=row["logical_codepoints"]
    return {
      "schema_version":1,
      "annotation_id":annotation_id,
      "glyph_instance":{
        "codepoint":codepoints[0],
        "context_codepoints":codepoints,
        "actual_form":"unknown",
        "font_sha256":row["font_sha256"],
        "glyph_id":row["glyph_ids"][0],
        "shaping_engine":"HarfBuzz",
        "direction":row["direction"],
        "script":row["script"],
        "language":row["language"],
        "features":row["features"],
        "render_sha256":image_hash,
        "canvas":{"width":row["canvas"][0],"height":row["canvas"][1]}
      },
      "annotator":{"id":reviewer,"tool_version":"manual-json-v1"},
      "status":"draft","components":[],"relations":[],
      "provenance":{
        "dataset_id":"arabic-harfbuzz-contextual-clusters-v1",
        "source_image_sha256":image_hash,
        "annotation_guideline_version":"arabic-visual-review-v1",
        "created_at":created
      }
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",required=True)
    p.add_argument("--crop-root",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--per-case",type=int,default=10)
    p.add_argument("--geometry-count",type=int,default=40)
    p.add_argument("--seed",type=int,default=20261119)
    a=p.parse_args()
    if a.per_case<1 or a.geometry_count<0: p.error("per-case must be >=1 and geometry-count >=0")
    source=Path(a.crop_root).resolve(); out=Path(a.output); images=out/"images"
    if out.exists(): shutil.rmtree(out)
    images.mkdir(parents=True)
    rows=read_jsonl(a.manifest)
    if not rows: raise SystemExit("Contextual cluster manifest is empty")
    selected=pick_stratified(rows,a.per_case,a.seed)
    created=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    review_rows=[]; copied={}
    for index,row in enumerate(selected,1):
        src=(source/row["image"]).resolve()
        if source not in src.parents or not src.is_file(): raise ValueError(f"Unsafe/missing image: {row['image']}")
        digest=sha(src); rel=f"images/{index:04d}_{digest[:12]}.png"
        shutil.copyfile(src,out/rel); copied[row["image"]]=rel
        review_rows.append({
          "review_id":f"VIS-{index:04d}","image":rel,"image_sha256":digest,
          "source_image":row["image"],"font_file":row["font_file"],
          "font_sha256":row["font_sha256"],"family":row.get("family"),
          "split":row.get("split"),"case_id":row["case_id"],
          "source_text":row["source_text"],"logical_start":row["logical_start"],
          "logical_end":row["logical_end"],"logical_text":row["logical_text"],
          "logical_codepoints":row["logical_codepoints"],"glyph_ids":row["glyph_ids"],
          "glyph_count":row["glyph_count"],"multi_codepoint":row["cluster_is_multi_codepoint"],
          "nonrendering_source_codepoints":row.get("nonrendering_source_codepoints",[]),
          "language_review":{"text_mapping":"pending","orthography":"pending",
            "joining_or_ligature":"pending","marks_and_dots":"pending",
            "visual_shape":"pending","reviewer_notes":""}
        })
    (out/"visual_linguistic_review.jsonl").write_text(
      "".join(json.dumps(r,ensure_ascii=False)+"\n" for r in review_rows),encoding="utf-8")
    eligible=[(r,review_rows[i]) for i,r in enumerate(selected)
      if len(r["logical_codepoints"])==1 and len(r["glyph_ids"])==1]
    geometry=pick_stratified([x[0] for x in eligible],max(1,a.geometry_count//max(1,len(set(x[0]["case_id"] for x in eligible)))),a.seed+1) if a.geometry_count and eligible else []
    # Cap exactly, maintaining the case/family-balanced order from pick_stratified.
    geometry=geometry[:a.geometry_count]
    by_key={(r["image"],r["font_sha256"],r["case_id"]):v for r,v in eligible}
    gdir=out/"geometry_annotations"; gdir.mkdir()
    ann_a=[]; ann_b=[]; adjud=[]
    for n,row in enumerate(geometry,1):
        review=by_key[(row["image"],row["font_sha256"],row["case_id"])]
        image_hash=review["image_sha256"]
        for ann,reviewer in ((ann_a,"REPLACE_WITH_ANNOTATOR_A"),(ann_b,"REPLACE_WITH_ANNOTATOR_B")):
            ann.append(annotation_template(row,image_hash,reviewer,f"GEO-{n:03d}-{reviewer[-1]}",created))
        adjud.append({"review_id":f"GEO-{n:03d}","image":review["image"],
          "image_sha256":image_hash,"annotator_a_annotation_id":ann_a[-1]["annotation_id"],
          "annotator_b_annotation_id":ann_b[-1]["annotation_id"],
          "adjudicated_annotation":None,"decision":"pending","adjudicator_notes":""})
    for name,data in (("annotator_a.jsonl",ann_a),("annotator_b.jsonl",ann_b)):
        (gdir/name).write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in data),encoding="utf-8")
    (gdir/"adjudication.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in adjud),encoding="utf-8")
    cases=defaultdict(int); families=defaultdict(set)
    for r in review_rows: cases[r["case_id"]]+=1; families[r["case_id"]].add(r["family"])
    summary={"schema_version":1,"status":"REVIEW_REQUIRED","seed":a.seed,
      "source_rows":len(rows),"visual_review_samples":len(review_rows),
      "geometry_pilot_samples":len(geometry),"case_counts":dict(sorted(cases.items())),
      "families_per_case":{k:len(v) for k,v in sorted(families.items())},
      "single_codepoint_single_glyph_geometry_only":True,
      "created_at":created,
      "note":"A review pack is not a review result. No annotations are approved by generation."}
    (out/"review_pack_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    cards=[]
    for r in review_rows:
        cards.append(f'<article><h3>{html.escape(r["review_id"])} · {html.escape(r["case_id"])}</h3><img src="{html.escape(r["image"])}"><p>النص: <b>{html.escape(r["source_text"])}</b> — المقطع: <b>{html.escape(r["logical_text"])}</b></p><p>العائلة: {html.escape(str(r["family"]))} | Glyph IDs: {html.escape(str(r["glyph_ids"]))} | split: {html.escape(str(r["split"]))}</p><p>Codepoints: {html.escape(", ".join(r["logical_codepoints"]))}</p></article>')
    page='<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><title>Arabic visual review pack</title><style>body{font:16px system-ui;margin:2rem;background:#f5f5f5}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:1rem}article{background:white;padding:1rem;border:1px solid #ddd;border-radius:8px}img{width:160px;height:160px;object-fit:contain;background:white;border:1px solid #aaa}p{overflow-wrap:anywhere}</style><h1>حزمة مراجعة الأشكال العربية</h1><p>عينات للمراجعة البشرية فقط؛ لا تعني الاعتماد.</p><main>'+''.join(cards)+'</main></html>'
    (out/"index.html").write_text(page,encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
