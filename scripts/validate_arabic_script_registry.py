#!/usr/bin/env python3
"""Validate the generated Unicode 17 Arabic-script registry."""
import argparse, json, re
from pathlib import Path
SHA=re.compile(r"^[0-9a-f]{64}$")
HEX=re.compile(r"^U\+[0-9A-F]{4,6}$")
JOIN={"R":{"isol","fina"},"L":{"isol","init"},"D":{"isol","init","medi","fina"},"U":{"isol"},"C":set(),"T":set()}
def validate(data):
    errors=[]
    if data.get("schema_version")!=2 or data.get("unicode_version")!="17.0.0": errors.append("registry must be schema v2 / Unicode 17.0.0")
    hashes=data.get("source_files_sha256",{})
    for name in ("UnicodeData.txt","Scripts.txt","ArabicShaping.txt"):
        if not SHA.fullmatch(hashes.get(name,"")): errors.append(f"missing or invalid source hash: {name}")
    seen=set()
    for i,r in enumerate(data.get("records",[])):
        p=f"records[{i}]"; cp=r.get("codepoint","")
        if not HEX.fullmatch(cp): errors.append(f"{p}: invalid codepoint"); continue
        if cp in seen: errors.append(f"{p}: duplicate {cp}")
        seen.add(cp)
        if len(r.get("character",""))!=1 or ord(r["character"])!=int(cp[2:],16): errors.append(f"{p}: character/codepoint mismatch")
        jt=r.get("joining_type")
        if jt not in JOIN: errors.append(f"{p}: invalid joining type")
        elif set(r.get("possible_forms_by_joining_type",[]))!=JOIN[jt]: errors.append(f"{p}: invalid possible forms for {jt}")
        if r.get("visual_annotation_status")!="not_annotated": errors.append(f"{p}: generated registry must not invent visual annotations")
    if not seen: errors.append("registry has no records")
    return errors
def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",default="data/arabic_script_registry_v2.json"); a=p.parse_args()
    data=json.loads(Path(a.input).read_text(encoding="utf-8")); errors=validate(data)
    if errors: print(json.dumps({"status":"FAIL","errors":errors},ensure_ascii=False,indent=2)); return 1
    print(json.dumps({"status":"PASS","records":len(data["records"]),"unicode_version":data["unicode_version"]},indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
