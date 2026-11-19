#!/usr/bin/env python3
"""Build a conditional OFL-1.1 training-rights manifest from pinned evidence.

This does not grant permission to release generated fonts under a different
license. It maps the official SIL OFL FAQ's AI-font guidance to this project:
generated font software must remain OFL-1.1, copyright notices must be
preserved, and Reserved Font Names must not be reused without permission.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

OFL_FAQ_URL = "https://openfontlicense.org/ofl-faq/"
OFL_FAQ_VERSION = "1.1-update8 (November 2026)"
REVIEW_DATE = "2026-11-19"
REVIEWER = "Project policy mapping — SIL OFL-FAQ 1.1-update8 (not legal counsel)"


def build_manifest(candidates: dict, license_audit: dict) -> dict:
    if candidates.get("status") != "REVIEW_REQUIRED":
        raise ValueError("Candidate queue must be the pinned REVIEW_REQUIRED evidence queue.")
    if license_audit.get("status") != "PASS" or license_audit.get("errors"):
        raise ValueError("Pinned license evidence audit must have status PASS and no errors.")

    fonts = candidates.get("fonts")
    records = license_audit.get("license_records")
    if not isinstance(fonts, list) or not fonts:
        raise ValueError("Candidate queue contains no font records.")
    if not isinstance(records, list) or not records:
        raise ValueError("License audit contains no license records.")

    by_family = {r.get("family_id"): r for r in records}
    if len(by_family) != len(records):
        raise ValueError("Duplicate family records in pinned license evidence.")

    approved = []
    seen_paths = set()
    for index, font in enumerate(fonts):
        path = font.get("font_file", "")
        family = font.get("family_id", "")
        digest = font.get("sha256", "")
        if not path or path in seen_paths:
            raise ValueError(f"fonts[{index}]: missing or duplicate font path")
        seen_paths.add(path)
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"fonts[{index}]: invalid SHA-256")
        if font.get("ml_training_allowed") is not False or font.get("review_status") != "pending":
            raise ValueError(f"fonts[{index}]: candidate queue is not fail-closed")

        evidence = by_family.get(family)
        if not evidence:
            raise ValueError(f"fonts[{index}]: no pinned license evidence for family {family}")
        if evidence.get("license_identifier_detected") != "OFL-1.1":
            raise ValueError(f"fonts[{index}]: source license is not verified OFL-1.1")
        if evidence.get("pinned_blob_url") != font.get("license_url"):
            raise ValueError(f"fonts[{index}]: pinned license URL mismatch")
        checks = evidence.get("required_clause_presence", {})
        if not checks or not all(checks.values()):
            raise ValueError(f"fonts[{index}]: required OFL clauses were not verified")

        reserved = sorted(set(evidence.get("reserved_font_name_candidates", [])))
        copyright_lines = evidence.get("copyright_lines", [])
        snapshot_hash = evidence.get("license_text_sha256", "")
        if not re.fullmatch(r"[0-9a-f]{64}", snapshot_hash):
            raise ValueError(f"fonts[{index}]: invalid license snapshot SHA-256")

        conditions = [
            "Any generated font software based on these OFL sources must be released under SIL OFL 1.1.",
            "Do not use any Reserved Font Name in a generated font's primary family name without written permission.",
            "Preserve applicable copyright notices, author acknowledgements, and the full OFL 1.1 license text.",
            "This approval covers use of this exact pinned source font for the project's ML training pipeline; it does not authorize relicensing generated fonts under a different license.",
            "The model weights are not classified by this manifest as Font Software; their separate distribution license must be documented independently."
        ]
        approved.append({
            "font_file": path,
            "family_id": family,
            "sha256": digest,
            "license_name": "SIL Open Font License 1.1",
            "license_url": font["license_url"],
            "ml_training_allowed": True,
            "review_status": "approved",
            "reviewed_by": REVIEWER,
            "reviewed_date": REVIEW_DATE,
            "evidence": [
                font["license_url"],
                font["source_font_url"],
                OFL_FAQ_URL,
                f"pinned license snapshot SHA-256: {snapshot_hash}"
            ],
            "reserved_font_names": reserved,
            "source_copyright_lines": copyright_lines,
            "notes": "Conditional OFL approval. " + " ".join(conditions)
        })

    approved.sort(key=lambda x: (x["family_id"], x["font_file"]))
    return {
        "schema_version": 1,
        "policy": {
            "status": "CONDITIONAL_OFL_1_1_APPROVAL",
            "source_license": "SIL Open Font License 1.1",
            "output_font_license": "SIL Open Font License 1.1",
            "official_guidance": OFL_FAQ_URL,
            "official_guidance_version": OFL_FAQ_VERSION,
            "relevant_questions": ["1.25", "3.9"],
            "noncommercial_note": "OFL is not an NC license. This project will distribute its own model and generated fonts for free, but OFL does not prevent downstream commercial use of the generated fonts, subject to OFL terms.",
            "model_weights_note": "This manifest does not determine the license of model weights. Keep model-weight licensing separate and do not claim that the weights are Font Software solely from this review.",
            "reserved_font_names": "Generated fonts must use new names and must not use any listed RFN without explicit written permission.",
            "legal_scope": "Project-level conservative license mapping, not legal advice or a court determination."
        },
        "fonts": approved
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--license-audit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    candidates = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    audit = json.loads(Path(args.license_audit).read_text(encoding="utf-8"))
    manifest = build_manifest(candidates, audit)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "CONDITIONAL_PASS",
        "font_count": len(manifest["fonts"]),
        "family_count": len({f["family_id"] for f in manifest["fonts"]}),
        "output_font_license": manifest["policy"]["output_font_license"],
        "reserved_font_name_families": sum(bool(f["reserved_font_names"]) for f in manifest["fonts"])
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
