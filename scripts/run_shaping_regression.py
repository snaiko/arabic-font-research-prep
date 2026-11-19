#!/usr/bin/env python3
"""Capture HarfBuzz shaping results for the project's Arabic regression strings."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def run(font_path, cases_path, output_path):
    try:
        import uharfbuzz as hb
    except ImportError as exc:
        raise SystemExit("Missing dependency: install uharfbuzz before running shaping regression.") from exc
    font_bytes=Path(font_path).read_bytes()
    face=hb.Face(font_bytes)
    font=hb.Font(face)
    font.scale=(face.upem,face.upem)
    cases=json.loads(Path(cases_path).read_text(encoding="utf-8"))["cases"]
    results=[]
    for case in cases:
        buf=hb.Buffer()
        buf.add_str(case["text"])
        buf.direction=case["direction"]
        buf.script=case["script"]
        buf.language=case["language"]
        buf.guess_segment_properties()
        hb.shape(font,buf,features={feature:1 for feature in case.get("features",[])})
        glyphs=[]
        for info,pos in zip(buf.glyph_infos,buf.glyph_positions):
            glyphs.append({
                "glyph_id":info.codepoint,"cluster":info.cluster,
                "x_advance":pos.x_advance,"y_advance":pos.y_advance,
                "x_offset":pos.x_offset,"y_offset":pos.y_offset
            })
        results.append({
            "case_id":case["id"],"text":case["text"],"logical_codepoints":[f"U+{ord(ch):04X}" for ch in case["text"]],
            "direction":case["direction"],"script":case["script"],"language":case["language"],
            "features":case.get("features",[]),"glyphs":glyphs,
            "cluster_values":[g["cluster"] for g in glyphs]
        })
    result={
        "schema_version":1,"font_path_name":Path(font_path).name,
        "font_sha256":hashlib.sha256(font_bytes).hexdigest(),
        "harfbuzz_version":hb.version_string(),"upem":face.upem,
        "case_manifest":str(cases_path),"results":results,
        "warning":"This records the output of this exact font/shaper configuration. It does not prove universal contextual forms or visual correctness."
    }
    Path(output_path).parent.mkdir(parents=True,exist_ok=True)
    Path(output_path).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","cases":len(results),"font_sha256":result["font_sha256"],
                      "harfbuzz_version":result["harfbuzz_version"],"output":output_path},indent=2))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--font",required=True)
    p.add_argument("--cases",default="data/shaping_regression_cases_v1.json")
    p.add_argument("--output",default="reports/local/shaping_regression.json")
    a=p.parse_args(); run(a.font,a.cases,a.output)

if __name__=="__main__": main()
