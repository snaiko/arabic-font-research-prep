#!/usr/bin/env python3
"""Build a fail-closed, per-font rights evidence queue from the collected corpus.

This records provenance and license-file locations only. It never grants ML
permission or marks a font approved.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from urllib.parse import quote

def build(fonts_jsonl, font_root):
    root=Path(font_root).resolve()
    rows=[]
    seen=set()
    for line_no,line in enumerate(Path(fonts_jsonl).read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        row=json.loads(line)
        rel=Path(row["file"])
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"line {line_no}: unsafe font path")
        path=(root/rel).resolve()
        try: path.relative_to(root)
        except ValueError: raise ValueError(f"line {line_no}: font path escapes root")
        if not path.is_file(): raise ValueError(f"line {line_no}: missing font file {rel}")
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != row.get("sha256"):
            raise ValueError(f"line {line_no}: SHA-256 mismatch for {rel}")
        key=str(rel)
        if key in seen: raise ValueError(f"line {line_no}: duplicate font path {key}")
        seen.add(key)
        revision=row["source_revision"]
        repo=row["source_repository"].rstrip("/")
        source_path=row["source_path"]
        license_path=row["license_file"]
        license_url=f"https://github.com/google/fonts/blob/{revision}/ofl/{Path(source_path).parts[1]}/{Path(license_path).name}"
        source_url=f"{repo}/blob/{revision}/{source_path}"
        rows.append({
          "font_file":str(rel).replace("\\","/"),
          "family_id":row["family"],
          "sha256":digest,
          "license_name":row.get("license","UNVERIFIED"),
          "license_url":license_url,
          "source_font_url":source_url,
          "source_repository":repo,
          "source_revision":revision,
          "ml_training_allowed":False,
          "review_status":"pending",
          "reviewed_by":"",
          "reviewed_date":"",
          "evidence":[license_url,source_url],
          "notes":"Evidence candidate only. Human/legal review required; no ML permission is granted."
        })
    rows.sort(key=lambda x:(x["family_id"],x["font_file"]))
    return {
      "schema_version":1,
      "status":"REVIEW_REQUIRED",
      "source_manifest":str(fonts_jsonl),
      "font_count":len(rows),
      "family_count":len({x["family_id"] for x in rows}),
      "approved_count":0,
      "fonts":rows,
      "warning":"This candidate queue is not the approved font_rights.json manifest. Do not change pending/false fields without an authorized rights review."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--fonts-jsonl",required=True)
    p.add_argument("--font-root",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    result=build(a.fonts_jsonl,a.font_root)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("status","font_count","family_count","approved_count")},indent=2))
if __name__=="__main__": main()
