import unittest

from scripts.build_ofl_training_rights_manifest import build_manifest


class OflTrainingRightsManifestTests(unittest.TestCase):
    def fixture(self):
        license_url = "https://github.com/google/fonts/blob/" + "a" * 40 + "/ofl/example/OFL.txt"
        source_url = "https://github.com/google/fonts/blob/" + "a" * 40 + "/ofl/example/Example-Regular.ttf"
        digest = "b" * 64
        snapshot = "c" * 64
        candidates = {
            "status": "REVIEW_REQUIRED",
            "fonts": [{
                "font_file": "data/raw_fonts/example/Example-Regular.ttf",
                "family_id": "example",
                "sha256": digest,
                "license_name": "SIL Open Font License 1.1",
                "license_url": license_url,
                "source_font_url": source_url,
                "ml_training_allowed": False,
                "review_status": "pending",
            }]
        }
        audit = {
            "status": "PASS",
            "errors": [],
            "license_records": [{
                "family_id": "example",
                "license_identifier_detected": "OFL-1.1",
                "pinned_blob_url": license_url,
                "required_clause_presence": {"permission": True, "reserved": True},
                "reserved_font_name_candidates": ["Example Reserved"],
                "copyright_lines": ["Copyright (c) Example Authors."],
                "license_text_sha256": snapshot,
            }]
        }
        return candidates, audit

    def test_builds_conditional_approved_record(self):
        candidates, audit = self.fixture()
        result = build_manifest(candidates, audit)
        self.assertEqual(len(result["fonts"]), 1)
        record = result["fonts"][0]
        self.assertEqual(record["font_file"], "example/Example-Regular.ttf")
        self.assertTrue(record["ml_training_allowed"])
        self.assertEqual(record["review_status"], "approved")
        self.assertEqual(record["reserved_font_names"], ["Example Reserved"])
        self.assertEqual(result["policy"]["output_font_license"], "SIL Open Font License 1.1")
        self.assertIn("OFL is not an NC license", result["policy"]["noncommercial_note"])

    def test_rejects_non_ofl_license(self):
        candidates, audit = self.fixture()
        audit["license_records"][0]["license_identifier_detected"] = "CC-BY-NC-4.0"
        with self.assertRaisesRegex(ValueError, "not verified OFL-1.1"):
            build_manifest(candidates, audit)

    def test_rejects_license_url_mismatch(self):
        candidates, audit = self.fixture()
        candidates["fonts"][0]["license_url"] += "?changed=1"
        with self.assertRaisesRegex(ValueError, "pinned license URL mismatch"):
            build_manifest(candidates, audit)

    def test_rejects_failed_license_audit(self):
        candidates, audit = self.fixture()
        audit["status"] = "FAIL"
        with self.assertRaisesRegex(ValueError, "must have status PASS"):
            build_manifest(candidates, audit)

    def test_rejects_candidate_not_fail_closed(self):
        candidates, audit = self.fixture()
        candidates["fonts"][0]["ml_training_allowed"] = True
        with self.assertRaisesRegex(ValueError, "not fail-closed"):
            build_manifest(candidates, audit)

    def test_rejects_unsafe_source_path(self):
        candidates, audit = self.fixture()
        candidates["fonts"][0]["font_file"] = "data/raw_fonts/../outside.ttf"
        with self.assertRaisesRegex(ValueError, "unsafe font path"):
            build_manifest(candidates, audit)


if __name__ == "__main__":
    unittest.main()
