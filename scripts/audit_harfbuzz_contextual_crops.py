#!/usr/bin/env python3
"""Strict integrity audit for HarfBuzz-shaped Arabic cluster crop datasets."""
from __future__ import annotations
import argparse, hashlib, json, unicodedata
from collections import defaultdict
from pathlib import Path
from PIL import Image
import uharfbuzz as hb

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def load_jsonl(path):
    with Path(path).open(encoding="utf-8") as f:
        for n,line in enumerate(f,1):
            if line.strip():
                try: yield json.loads(line)
                except Exception as e: raise ValueError(f"{path}:{n}: {e}")

def resolve_font(value, root):
    p=Path(value)
    for q in (p,Path(root)/p,Path(root)/p.name):
        if q.is_file(): return q.resolve()
    return None

def shape(font_path, case):
    data=Path(font_path).read_bytes()
    face=hb.Face(data); font=hb.Font(face); font.scale=(face.upem,face.upem)
    buf=hb.Buffer(); buf.add_str(case["text"])
    buf.direction=case.get("direction","rtl"); buf.script=case.get("script","Arab"); buf.language=case.get("language","ar")
    hb.shape(font,buf,{f:1 for f in case.get("features",[])})
    grouped=defaultdict(list)
    for info in buf.glyph_infos: grouped[info.cluster].append(info.codepoint)
    return {int(k):v for k,v in grouped.items()}

def audit(manifest, crop_root, font_root, cases_path, samples_path):
    cases={c["id"]:c for c in json.loads(Path(cases_path).read_text(encoding="utf-8"))["cases"]}
    split_by_hash={r.get("font_sha256"):r.get("split") for r in load_jsonl(samples_path)}
    rows=list(load_jsonl(manifest)); errors=[]; seen=set(); cache={}; family_splits=defaultdict(set)
    for n,row in enumerate(rows,1):
        case_id=row.get("case_id"); case=cases.get(case_id)
        if case is None:
            errors.append(f"row {n}: unknown shaping case {case_id}"); continue
        if row.get("source_text") != case["text"]:
            errors.append(f"row {n}: source text differs from canonical case")
        start=row.get("logical_start"); end=row.get("logical_end"); cluster=row.get("cluster")
        text=case["text"]
        if not isinstance(start,int) or not isinstance(end,int) or not isinstance(cluster,int) or not (0<=start<end<=len(text)) or start!=cluster:
            errors.append(f"row {n}: invalid logical source span/cluster index")
            continue
        logical=text[start:end]
        if row.get("logical_text")!=logical or row.get("logical_codepoints")!=[f"U+{ord(c):04X}" for c in logical]:
            errors.append(f"row {n}: logical text/codepoint mapping mismatch")
        digest=row.get("font_sha256","")
        if len(digest)!=64 or split_by_hash.get(digest) not in {"train","validation","test"}:
            errors.append(f"row {n}: font hash absent from source split manifest")
        elif row.get("split")!=split_by_hash[digest]:
            errors.append(f"row {n}: family-safe split does not match source manifest")
        family=row.get("family")
        if family and row.get("split"): family_splits[family].add(row["split"])
        font=resolve_font(row.get("font_file",""),font_root)
        if font is None:
            errors.append(f"row {n}: source font not found"); continue
        if digest and sha256(font)!=digest:
            errors.append(f"row {n}: source font SHA-256 mismatch")
        key=(str(font),case_id)
        if key not in cache:
            try: cache[key]=shape(font,case)
            except Exception as e:
                errors.append(f"row {n}: HarfBuzz re-shaping failed: {e}"); continue
        expected=cache[key].get(cluster)
        if expected is None or row.get("glyph_ids")!=expected:
            errors.append(f"row {n}: glyph IDs do not match independent HarfBuzz re-shape")
        if expected is not None:
            ordered=sorted(cache[key])
            covered=set()
            for pos,cidx in enumerate(ordered):
                cend=ordered[pos+1] if pos+1<len(ordered) else len(text)
                covered.update(range(cidx,cend))
            expected_nonrendered=[]
            for idx,char in enumerate(text):
                if idx not in covered:
                    cat=unicodedata.category(char)
                    if not (cat.startswith("C") or cat.startswith("Z")):
                        errors.append(f"row {n}: visible source character U+{ord(char):04X} has no shaped glyph cluster")
                    expected_nonrendered.append({"index":idx,"char":char,"codepoint":f"U+{ord(char):04X}","unicode_category":cat})
            if row.get("nonrendering_source_codepoints") != expected_nonrendered:
                errors.append(f"row {n}: non-rendering controls/separators are missing or incorrectly mapped")
        if row.get("glyph_count")!=len(row.get("glyph_ids",[])) or not row.get("glyph_ids"):
            errors.append(f"row {n}: glyph count mismatch/empty glyph list")
        if row.get("renderer")!="HarfBuzz+FontTools-outline+CairoSVG":
            errors.append(f"row {n}: unexpected renderer provenance")
        image=row.get("image",""); root=Path(crop_root).resolve(); target=(root/image).resolve()
        try: target.relative_to(root)
        except ValueError:
            errors.append(f"row {n}: image path escapes crop root"); continue
        if not target.is_file():
            errors.append(f"row {n}: image missing"); continue
        try:
            with Image.open(target) as im:
                im.load()
                if im.size!=(160,160): errors.append(f"row {n}: image is not 160x160")
                gray=im.convert("L")
                if gray.point(lambda p:255 if p<245 else 0).getbbox() is None:
                    errors.append(f"row {n}: blank image")
                if gray.getbbox() is None: errors.append(f"row {n}: fully blank image")
        except Exception as e: errors.append(f"row {n}: unreadable image: {e}")
        ident=(digest,case_id,cluster)
        if ident in seen: errors.append(f"row {n}: duplicate font/case/cluster")
        seen.add(ident)
    for family,splits in family_splits.items():
        if len(splits)>1: errors.append(f"family split leakage: {family}")
    return {"schema_version":1,"status":"PASS" if rows and not errors else "FAIL",
            "cluster_samples":len(rows),"font_case_pairs_reshaped":len(cache),
            "independent_harfbuzz_mapping_checks":sum(1 for r in rows if (str(resolve_font(r.get("font_file",""),font_root)),r.get("case_id")) in cache),
            "multi_codepoint_clusters":sum(1 for r in rows if len(r.get("logical_text",""))>1),
            "errors":errors,
            "scope":"Checks canonical source spans, Unicode mapping, independent HarfBuzz glyph-ID reproduction, source-font hashes, split provenance, image readability/dimensions/nonblank status and duplicate clusters. Does not establish artistic/visual correctness or legal training permission."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",default="data/contextual_glyph_crops/contextual_clusters.jsonl")
    p.add_argument("--crop-root",default="data/contextual_glyph_crops")
    p.add_argument("--font-root",default="data/raw_fonts")
    p.add_argument("--cases",default="data/shaping_regression_cases_v1.json")
    p.add_argument("--samples",default="data/training_samples/samples.jsonl")
    p.add_argument("--output",default="reports/local/contextual_cluster_audit.json")
    a=p.parse_args()
    report=audit(a.manifest,a.crop_root,a.font_root,a.cases,a.samples)
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(0 if report["status"]=="PASS" else 2)
if __name__=="__main__": main()
