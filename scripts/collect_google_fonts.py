#!/usr/bin/env python3
"""Collect a curated Arabic-font pilot corpus from Google Fonts OFL folders.
Python 3.10+, standard library only. Run:
  python scripts/collect_google_fonts.py --output data/raw_fonts
"""
import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = "google/fonts"
BRANCH = "main"
FAMILIES = [
    "amiri", "noto-naskh-arabic", "noto-sans-arabic", "noto-kufi-arabic",
    "scheherazade-new", "lateef", "cairo", "tajawal", "almarai",
    "ibm-plex-sans-arabic", "mada", "readex-pro", "reem-kufi",
    "el-messiri", "changa", "baloo-bhaijaan-2", "harmattan",
    "aref-ruqaa", "markazi-text", "rubik",
]
API = "https://api.github.com/repos/" + REPO
# Google Fonts directory slugs are compact; the human-readable IDs above stay stable.
REMOTE_FAMILY_DIRS = {
    "noto-naskh-arabic": "notonaskharabic",
    "noto-sans-arabic": "notosansarabic",
    "noto-kufi-arabic": "notokufiarabic",
    "scheherazade-new": "scheherazadenew",
    "ibm-plex-sans-arabic": "ibmplexsansarabic",
    "readex-pro": "readexpro",
    "reem-kufi": "reemkufi",
    "el-messiri": "elmessiri",
    "baloo-bhaijaan-2": "baloobhaijaan2",
    "aref-ruqaa": "arefruqaa",
    "markazi-text": "markazitext",
}
REVISION = None

def get_bytes(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "arabic-font-research-prep/0.1",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()

def api_json(url):
    return json.loads(get_bytes(url))

def resolve_revision():
    return api_json(API + "/commits/" + BRANCH)["sha"]

def api_dir(path):
    url = API + "/contents/" + urllib.parse.quote(path, safe="/") + "?ref=" + REVISION
    data = api_json(url)
    if not isinstance(data, list):
        raise RuntimeError("Expected directory listing: " + path)
    return data

def walk_fonts(path):
    found = []
    for item in api_dir(path):
        if item["type"] == "dir":
            found.extend(walk_fonts(item["path"]))
        elif item["type"] == "file" and Path(item["name"]).suffix.lower() in {".ttf", ".otf"}:
            found.append(item["path"])
    return sorted(found)

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def main():
    global REVISION
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/raw_fonts")
    parser.add_argument("--families", help="Comma-separated subset of curated family slugs")
    args = parser.parse_args()
    families = [x.strip().lower() for x in args.families.split(",")] if args.families else FAMILIES
    unknown = sorted(set(families) - set(FAMILIES))
    if unknown:
        parser.error("Not in curated allowlist: " + ", ".join(unknown))

    REVISION = resolve_revision()
    root = Path(args.output)
    root.mkdir(parents=True, exist_ok=True)
    rows, errors = [], []

    for slug in families:
        family_path = "ofl/" + REMOTE_FAMILY_DIRS.get(slug, slug)
        try:
            entries = api_dir(family_path)
            top_files = {x["name"]: x for x in entries if x["type"] == "file"}
            license_name = next((n for n in ("OFL.txt", "OFL-1.1.txt") if n in top_files), None)
            if not license_name:
                raise RuntimeError("No family-level OFL file; refusing download")
            license_data = get_bytes(top_files[license_name]["download_url"])
            license_text = license_data.decode("utf-8", errors="replace")
            if not re.search(r"SIL OPEN FONT LICENSE Version 1\.1", license_text, re.I):
                raise RuntimeError("License is not identified as SIL OFL 1.1; refusing download")

            family_dir = root / slug
            family_dir.mkdir(parents=True, exist_ok=True)
            (family_dir / license_name).write_bytes(license_data)
            metadata_file = None
            if "METADATA.pb" in top_files:
                metadata_data = get_bytes(top_files["METADATA.pb"]["download_url"])
                (family_dir / "METADATA.pb").write_bytes(metadata_data)
                metadata_file = slug + "/METADATA.pb"

            font_paths = walk_fonts(family_path)
            if not font_paths:
                raise RuntimeError("No TTF/OTF files found")
            for remote_path in font_paths:
                relative = remote_path[len(family_path) + 1:]
                target = family_dir / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                url = "https://raw.githubusercontent.com/" + REPO + "/" + REVISION + "/" + urllib.parse.quote(remote_path, safe="/")
                data = get_bytes(url)
                target.write_bytes(data)
                rows.append({
                    "family": slug,
                    "source_repository": "https://github.com/" + REPO,
                    "source_path": remote_path,
                    "source_revision": REVISION,
                    "license": "SIL Open Font License 1.1",
                    "license_file": slug + "/" + license_name,
                    "metadata_file": metadata_file,
                    "file": target.as_posix(),
                    "filename": target.name,
                    "bytes": len(data),
                    "sha256": sha256(data),
                    "status": "downloaded_unvalidated",
                })
            print("[OK] " + slug + ": " + str(len(font_paths)) + " font file(s)")
            time.sleep(0.15)
        except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError, KeyError) as exc:
            errors.append({"family": slug, "error": str(exc)})
            print("[SKIP] " + slug + ": " + str(exc), file=sys.stderr)

    with (root / "fonts.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    report = {
        "source": "https://github.com/" + REPO,
        "source_revision": REVISION,
        "families_requested": families,
        "files_downloaded": len(rows),
        "families_with_errors": errors,
        "warning": "Downloaded files are not yet cmap- or shaping-validated.",
    }
    (root / "collection_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if rows else 2

if __name__ == "__main__":
    raise SystemExit(main())
