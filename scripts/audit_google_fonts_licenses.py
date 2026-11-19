#!/usr/bin/env python3
"""Snapshot pinned upstream font licenses and audit provenance without granting rights."""
from __future__ import annotations
import argparse, hashlib, json, re, urllib.request
from pathlib import Path
from urllib.parse import urlparse

OFL_MARKER = "SIL OPEN FONT LICENSE Version 1.1"
REQUIRED_TERMS = (
    "used, studied, modified and",
    "redistributed freely",
    "not sold by themselves",
    "Reserved Font Name",
)

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def fetch(url: str) -> bytes:
    parsed=urlparse(url)
    if parsed.scheme!="https" or parsed.netloc!="raw.githubusercontent.com":
        raise ValueError(f"license URL is not pinned raw.githubusercontent.com HTTPS: {url}")
    req=urllib.request.Request(url,headers={"User-Agent":"arabic-font-research-prep/1.0"})
    with urllib.request.urlopen(req,timeout=45) as response:
        return response.read()

def raw_url(blob_url: str) -> str:
    match=re.fullmatch(r"https://github[.]com/google/fonts/blob/([0-9a-f]{40})/(ofl/[A-Za-z0-9._/-]+/OFL[.]txt)",blob_url)
    if not match: raise ValueError(f"unexpected or unpinned Google Fonts license URL: {blob_url}")
    return f"https://raw.githubusercontent.com/google/fonts/{match.group(1)}/{match.group(2)}"

def audit(candidate_path, output_dir, fetcher=fetch):
    candidates=json.loads(Path(candidate_path).read_text(encoding="utf-8"))
    if candidates.get("status")!="REVIEW_REQUIRED": raise ValueError("candidate queue is not in REVIEW_REQUIRED state")
    fonts=candidates.get("fonts",[])
    if not fonts: raise ValueError("no candidate fonts")
    by_url={}
    for font in fonts:
        if font.get("ml_training_allowed") is not False or font.get("review_status")!="pending":
            raise ValueError("candidate queue must remain fail-closed")
        url=font["license_url"]
        by_url.setdefault(url,[]).append(font)
    out=Path(output_dir); licenses_dir=out/"licenses"; licenses_dir.mkdir(parents=True,exist_ok=True)
    license_records=[]; errors=[]
    for index,(blob_url,assets) in enumerate(sorted(by_url.items()),1):
        url=raw_url(blob_url)
        body=fetcher(url)
        try: text=body.decode("utf-8-sig")
        except UnicodeDecodeError as exc: raise ValueError(f"license is not UTF-8: {blob_url}") from exc
        normalized=" ".join(text.split())
        is_ofl=OFL_MARKER in text
        term_checks={term:term.lower() in normalized.lower() for term in REQUIRED_TERMS}
        if not is_ofl: errors.append(f"license marker missing: {blob_url}")
        if not all(term_checks.values()): errors.append(f"expected OFL clause missing: {blob_url}")
        digest=sha256(body)
        filename=f"license-{index:02d}-{assets[0]['family_id']}.txt"
        (licenses_dir/filename).write_bytes(body)
        header=text.split(OFL_MARKER,1)[0]
        copyright_lines=[line.strip() for line in header.splitlines() if line.strip().lower().startswith('copyright')]
        reserved=[]
        for line in header.splitlines():
            if 'Reserved Font Name' not in line: continue
            tail=line.split('Reserved Font Name',1)[1].strip()
            quoted=re.findall(r"[\"“']([^\"”']+)[\"”']",tail)
            if quoted: reserved.extend(name.strip() for name in quoted if name.strip())
            else:
                value=(tail[2:] if tail.lower().startswith('s ') else tail).strip().rstrip('.,;')
                if value: reserved.append(value)
        reserved=sorted(set(reserved))
        license_records.append({
            "family_id":assets[0]["family_id"],"asset_count":len(assets),
            "license_name_claimed":assets[0].get("license_name"),
            "license_identifier_detected":"OFL-1.1" if is_ofl else "UNRECOGNIZED",
            "pinned_blob_url":blob_url,"raw_snapshot_url":url,
            "snapshot_file":f"licenses/{filename}","license_text_sha256":digest,
            "copyright_lines":copyright_lines,"reserved_font_name_candidates":reserved,
            "required_clause_presence":term_checks,
            "ml_training_permission_explicitly_addressed":bool(re.search(r"machine learning|machine-learning|training data|model training",text,re.I)),
            "decision":"SOURCE_AND_TEXT_VERIFIED_REVIEW_REQUIRED",
            "decision_note":"The snapshot verifies the pinned upstream license text and selected clauses only. It does not interpret whether ML training is permitted, waive other rights, or grant approval."
        })
    report={
        "schema_version":1,"status":"PASS" if not errors else "FAIL",
        "source_repository":"google/fonts","candidate_font_count":len(fonts),
        "unique_license_files":len(license_records),
        "font_files_sha256_verified_by_candidate_builder":len({f["sha256"] for f in fonts}),
        "license_records":license_records,"errors":errors,
        "rights_decision":{"approved_font_count":0,"ml_training_allowed":False,
            "status":"REVIEW_REQUIRED",
            "reason":"A machine can verify the pinned license text, but cannot issue a legal interpretation or approval for the proposed model-training use."}
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/"license_evidence_audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidates",required=True); p.add_argument("--output-dir",required=True)
    a=p.parse_args(); result=audit(a.candidates,a.output_dir)
    print(json.dumps({k:result[k] for k in ("status","candidate_font_count","unique_license_files","rights_decision","errors")},ensure_ascii=False,indent=2))
    raise SystemExit(0 if result["status"]=="PASS" else 2)
if __name__=="__main__": main()
