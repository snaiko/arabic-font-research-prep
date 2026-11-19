#!/usr/bin/env python3
"""Build cluster-level Arabic annotation drafts without collapsing ligatures to glyphs."""
from __future__ import annotations
import argparse, hashlib, json, random, shutil
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone

def read_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def select(rows, per_case, seed):
    rng=random.Random(seed); groups=defaultdict(lambda:defaultdict(list))
    for row in rows: groups[row["case_id"]][row.get("family") or "unknown"].append(row)
    out=[]
    for case in sorted(groups):
        fams=groups[case]
        for values in fams.values(): rng.shuffle(values)
        names=sorted(fams); count=0
        while count<per_case and any(fams.values()):
            for name in names:
                if fams[name] and count<per_case:
                    out.append(fams[name].pop()); count+=1
    return out

def build(manifest, crop_root, output, per_case=10, seed=20261119):
    rows=read_jsonl(manifest)
    if not rows: raise ValueError("empty contextual cluster manifest")
    source=Path(crop_root).resolve(); out=Path(output)
    if out.exists(): shutil.rmtree(out)
    (out/"images").mkdir(parents=True)
    created=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    records=[]
    for n,row in enumerate(select(rows,per_case,seed),1):
        src=(source/row["image"]).resolve()
        if source not in src.parents or not src.is_file(): raise ValueError(f"unsafe/missing source image: {row['image']}")
        digest=sha(src); image=f"images/CL-{n:04d}_{digest[:12]}.png"
        shutil.copyfile(src,out/image)
        records.append({
          "schema_version":1,"annotation_id":f"CL-{n:04d}","status":"draft",
          "cluster":{"font_file":row["font_file"],"font_sha256":row["font_sha256"],
            "family":row.get("family"),"split":row.get("split"),"case_id":row["case_id"],
            "cluster_index":row["cluster"],"logical_start":row["logical_start"],
            "logical_end":row["logical_end"],"source_text":row["source_text"],
            "logical_text":row["logical_text"],"logical_codepoints":row["logical_codepoints"],
            "glyph_ids":row["glyph_ids"],"glyph_count":row["glyph_count"],
            "nonrendering_source_codepoints":row.get("nonrendering_source_codepoints",[]),
            "direction":row["direction"],"script":row["script"],"language":row["language"],
            "features":row["features"],"canvas":row["canvas"]},
          "image":image,"image_sha256":digest,
          "assessment":{"cluster_readable":"pending","text_mapping":"pending",
            "joining_continuity":"pending","ligature_formation":"pending",
            "mark_attachment":"pending","dot_completeness":"pending",
            "bidi_order":"pending","clipping_or_render_defect":"pending",
            "issue_tags":[],"notes":""},
          "annotator":{"id":"UNASSIGNED","tool_version":"cluster-review-v1"},
          "provenance":{"dataset_id":"arabic-harfbuzz-contextual-clusters-v1",
            "source_image":row["image"],"created_at":created}
        })
    (out/"cluster_annotations.jsonl").write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in records),encoding="utf-8")
    counts=defaultdict(int)
    for r in records: counts[r["cluster"]["case_id"]]+=1
    summary={"schema_version":1,"status":"DRAFTS_ONLY","source_rows":len(rows),
      "annotation_count":len(records),"per_case":dict(sorted(counts.items())),
      "seed":seed,"note":"Cluster-level drafts preserve many-codepoint/many-glyph clusters. Generation is not visual or linguistic approval."}
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return summary

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",required=True); p.add_argument("--crop-root",required=True)
    p.add_argument("--output",required=True); p.add_argument("--per-case",type=int,default=10)
    p.add_argument("--seed",type=int,default=20261119); a=p.parse_args()
    if a.per_case<1: p.error("--per-case must be >=1")
    print(json.dumps(build(a.manifest,a.crop_root,a.output,a.per_case,a.seed),ensure_ascii=False,indent=2))
if __name__=="__main__": main()
