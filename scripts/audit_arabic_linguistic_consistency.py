#!/usr/bin/env python3
"""Audit Arabic cluster metadata against Unicode 17 ArabicShaping registry."""
from __future__ import annotations
import argparse, json, unicodedata
from pathlib import Path

def load_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]

def audit(manifest,cases_path,registry_path):
    rows=load_jsonl(manifest)
    cases={x["id"]:x for x in json.loads(Path(cases_path).read_text(encoding="utf-8"))["cases"]}
    registry=json.loads(Path(registry_path).read_text(encoding="utf-8"))
    lookup={x["codepoint"]:x for x in registry["records"]}
    errors=[]; stats={"clusters":len(rows),"codepoints":0,"marks":0,"transparent_joining_chars":0,
      "multi_codepoint_clusters":0,"multi_glyph_clusters":0,"possible_ligature_or_substitution_candidates":0}
    seen=set()
    for n,row in enumerate(rows,1):
        p=f"row {n}"; case=cases.get(row.get("case_id"))
        if case is None: errors.append(f"{p}: unknown shaping case"); continue
        text=case["text"]; start=row.get("logical_start"); end=row.get("logical_end")
        if not isinstance(start,int) or not isinstance(end,int) or not (0<=start<end<=len(text)):
            errors.append(f"{p}: invalid source span"); continue
        logical=text[start:end]
        cps=[f"U+{ord(c):04X}" for c in logical]
        if row.get("source_text")!=text or row.get("logical_text")!=logical or row.get("logical_codepoints")!=cps:
            errors.append(f"{p}: canonical logical text/codepoint mismatch")
        key=(row.get("font_sha256"),row.get("case_id"),row.get("cluster"))
        if key in seen: errors.append(f"{p}: duplicate font/case/cluster")
        seen.add(key)
        for ch,cp in zip(logical,cps):
            stats["codepoints"]+=1
            record=lookup.get(cp)
            if record:
                if record["character"]!=ch or record["general_category"]!=unicodedata.category(ch):
                    errors.append(f"{p}: Unicode registry/category mismatch at {cp}")
                if record["joining_type"] not in {"R","L","D","C","U","T"}:
                    errors.append(f"{p}: invalid Joining_Type at {cp}")
                if record["is_combining_mark"]!=unicodedata.category(ch).startswith("M"):
                    errors.append(f"{p}: combining-mark classification mismatch at {cp}")
                if record["joining_type"]=="T": stats["transparent_joining_chars"]+=1
            elif unicodedata.name(ch,"").startswith("ARABIC"):
                errors.append(f"{p}: Arabic codepoint missing from Unicode 17 registry: {cp}")
            if unicodedata.category(ch).startswith("M"): stats["marks"]+=1
        if len(cps)>1: stats["multi_codepoint_clusters"]+=1
        if row.get("glyph_count",0)>1: stats["multi_glyph_clusters"]+=1
        if len(cps)>1 and row.get("glyph_count")==1: stats["possible_ligature_or_substitution_candidates"]+=1
        if row.get("glyph_count")!=len(row.get("glyph_ids",[])): errors.append(f"{p}: glyph_count mismatch")
    return {"status":"PASS" if rows and not errors else "FAIL","stats":stats,
      "errors":errors,"unicode_version":registry.get("unicode_version"),
      "scope":"Verifies canonical source spans, codepoint/category consistency, ArabicShaping Joining_Type metadata, combining-mark flags, and glyph cardinalities. It cannot judge spelling, calligraphic form, visual readability, or semantic correctness of a rendered glyph."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",required=True); p.add_argument("--cases",required=True)
    p.add_argument("--registry",required=True); p.add_argument("--output",required=True)
    a=p.parse_args(); result=audit(a.manifest,a.cases,a.registry)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result["status"]=="PASS" else 2)
if __name__=="__main__": main()
