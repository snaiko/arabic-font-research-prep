#!/usr/bin/env python3
"""Run the Arabic HarfBuzz regression suite only on rights-approved, hash-matched fonts."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from validate_font_rights_manifest import validate
from run_shaping_regression import run

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",default="data/manifests/font_rights.json")
    p.add_argument("--font-root",required=True)
    p.add_argument("--cases",default="data/shaping_regression_cases_v1.json")
    p.add_argument("--output-dir",default="reports/local/shaping")
    p.add_argument("--minimum-families",type=int,default=3)
    a=p.parse_args()
    root=Path(a.font_root).resolve()
    manifest=json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    gate=validate(manifest,root,True)
    family_ids={item["family_id"] for item in manifest["fonts"]}
    if len(family_ids) < a.minimum_families:
        raise SystemExit(f"BLOCKED: need at least {a.minimum_families} distinct approved font families; found {len(family_ids)}.")
    out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    results=[]
    for item in manifest["fonts"]:
        target=(root/item["font_file"]).resolve()
        try: target.relative_to(root)
        except ValueError: raise SystemExit(f"BLOCKED: unsafe font path: {item['font_file']}")
        report=out/(Path(item["font_file"]).stem+"_"+item["sha256"][:8]+".json")
        run(str(target),a.cases,str(report))
        results.append({"family_id":item["family_id"],"font_file":item["font_file"],
                        "font_sha256":item["sha256"],"report":str(report)})
    summary={"schema_version":1,"status":"PASS","rights_manifest":str(a.manifest),
             "font_count":len(results),"distinct_family_count":len(family_ids),"results":results,
             "note":"PASS means rights fields and file hashes passed the project's explicit gate and shaping ran. It is not legal advice or a visual-quality approval."}
    (out/"batch_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
