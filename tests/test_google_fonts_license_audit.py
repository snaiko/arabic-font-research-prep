import json, tempfile, unittest
from pathlib import Path
from scripts.audit_google_fonts_licenses import audit, raw_url

OFL="""Copyright 2020 Example Authors
This Font Software is licensed under the SIL Open Font License, Version 1.1.
SIL OPEN FONT LICENSE Version 1.1 - 26 February 2007
The OFL allows the licensed fonts to be used, studied, modified and redistributed freely.
The fonts cannot be sold by themselves. Reserved Font Name.
"""

class LicenseEvidenceTests(unittest.TestCase):
    def test_pinned_google_fonts_url_only(self):
        url="https://github.com/google/fonts/blob/"+"a"*40+"/ofl/example/OFL.txt"
        self.assertEqual(raw_url(url),"https://raw.githubusercontent.com/google/fonts/"+"a"*40+"/ofl/example/OFL.txt")
        with self.assertRaises(ValueError): raw_url("https://example.com/OFL.txt")

    def test_snapshots_text_but_never_approves_training(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); candidate=root/"candidates.json"
            url="https://github.com/google/fonts/blob/"+"a"*40+"/ofl/example/OFL.txt"
            data={"status":"REVIEW_REQUIRED","fonts":[
                {"family_id":"example","sha256":"b"*64,"license_name":"SIL Open Font License 1.1",
                 "license_url":url,"ml_training_allowed":False,"review_status":"pending"}]}
            candidate.write_text(json.dumps(data),encoding="utf-8")
            result=audit(candidate,root/"out",fetcher=lambda u:OFL.encode())
            self.assertEqual(result["status"],"PASS")
            self.assertEqual(result["unique_license_files"],1)
            self.assertEqual(result["rights_decision"]["approved_font_count"],0)
            self.assertFalse(result["rights_decision"]["ml_training_allowed"])
            self.assertTrue((root/"out/licenses/license-01-example.txt").is_file())

if __name__=="__main__": unittest.main()
