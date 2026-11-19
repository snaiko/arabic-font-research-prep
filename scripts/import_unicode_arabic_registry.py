#!/usr/bin/env python3
"""Build a complete Arabic-script metadata registry from pinned Unicode 17.0 UCD files."""
from __future__ import annotations
import argparse, hashlib, json, urllib.request
from pathlib import Path

VERSION = "17.0.0"
BASE = f"https://www.unicode.org/Public/{VERSION}/ucd/"
FILES = ("UnicodeData.txt", "Scripts.txt", "ArabicShaping.txt")
JOINING = {"R", "L", "D", "C", "U", "T"}
FORM_MAP = {"R": ["isol", "fina"], "L": ["isol", "init"],
            "D": ["isol", "init", "medi", "fina"], "U": ["isol"],
            "C": [], "T": []}

def expand_range(token):
    parts = token.strip().split("..")
    return range(int(parts[0], 16), int(parts[-1], 16) + 1)

def parse_property_file(path, wanted=None):
    result = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line: continue
        fields = [x.strip() for x in line.split(";")]
        if len(fields) < 2: continue
        if wanted is not None and fields[1] != wanted: continue
        for cp in expand_range(fields[0]): result[cp] = fields[1]
    return result

def parse_unicode_data(path):
    result, pending = {}, None
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        f = raw.split(";")
        cp, name, category = int(f[0], 16), f[1], f[2]
        if name.endswith(", First>"):
            pending = (cp, category)
        elif name.endswith(", Last>") and pending:
            start, first_category = pending
            for n in range(start, cp + 1): result[n] = (f"<range U+{n:04X}>", first_category)
            pending = None
        else:
            result[cp] = (name, category)
    return result

def download_ucd(directory):
    directory.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        target = directory / name
        if not target.exists():
            request = urllib.request.Request(BASE + name, headers={"User-Agent": "arabic-font-research-prep/1.0"})
            with urllib.request.urlopen(request, timeout=60) as response: target.write_bytes(response.read())

def build(data_dir):
    names = parse_unicode_data(data_dir / "UnicodeData.txt")
    scripts = parse_property_file(data_dir / "Scripts.txt", "Arabic")
    groups, schematic, joining_types = {}, {}, {}
    for raw in (data_dir / "ArabicShaping.txt").read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line: continue
        f = [x.strip() for x in line.split(";")]
        if len(f) < 4: continue
        cp = int(f[0], 16)
        if cp in scripts:
            schematic[cp] = f[1]
            joining_types[cp] = f[2]
            groups[cp] = f[3].replace(" ", "_")
    records = []
    for cp in sorted(scripts):
        if cp not in names: continue
        name, category = names[cp]
        # Per ArabicShaping.txt: unlisted Mn/Me/Cf are Transparent; all other unlisted code points are Non_Joining.
        jt = joining_types.get(cp, "T" if category in {"Mn", "Me", "Cf"} else "U")
        if jt not in JOINING: raise ValueError(f"Unexpected Joining_Type {jt} at U+{cp:04X}")
        role = ("letter" if category.startswith("L") else "mark" if category.startswith("M") else
                "number" if category.startswith("N") else "punctuation" if category.startswith("P") else
                "symbol" if category.startswith("S") else "other")
        records.append({
            "codepoint": f"U+{cp:04X}", "character": chr(cp), "unicode_name": name,
            "general_category": category, "role": role, "joining_type": jt,
            "joining_group": groups.get(cp, "No_Joining_Group"), "schematic_name": schematic.get(cp),
            "possible_forms_by_joining_type": FORM_MAP[jt], "is_combining_mark": category.startswith("M"),
            "visual_annotation_status": "not_annotated"
        })
    hashes = {name: hashlib.sha256((data_dir / name).read_bytes()).hexdigest() for name in FILES}
    return {
        "schema_version": 2, "system_id": "arabic-script-registry-unicode-17.0.0",
        "unicode_version": VERSION, "coverage": "all assigned code points with Script=Arabic in Unicode 17.0",
        "source_files_sha256": hashes, "records": records,
        "policy": {
            "joining_type_and_group": "Normative UCD properties. ArabicShaping.txt defines explicit non-default types; unlisted Mn/Me/Cf default to T and all other unlisted code points to U.",
            "schematic_name": "Descriptive comment only; not a formal Unicode property.",
            "visual_decomposition": "Not supplied; requires separately reviewed glyph-instance annotations.",
            "contextual_forms": "Possible forms by Joining_Type are constraints, not the actual form of a rendered glyph.",
            "presentation_forms": "Compatibility presentation-form code points are not added unless Script=Arabic."
        }
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ucd-dir",default="data/unicode/17.0.0")
    p.add_argument("--download",action="store_true")
    p.add_argument("--output",default="data/arabic_script_registry_v2.json")
    a=p.parse_args(); directory=Path(a.ucd_dir)
    if a.download: download_ucd(directory)
    missing=[n for n in FILES if not (directory/n).is_file()]
    if missing: p.error("Missing UCD files: "+", ".join(missing)+"; use --download or supply --ucd-dir")
    payload=build(directory); Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","unicode_version":VERSION,"records":len(payload["records"]),
                      "source_files_sha256":payload["source_files_sha256"],"output":a.output},indent=2))

if __name__=="__main__": main()
