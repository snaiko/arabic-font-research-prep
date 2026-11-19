import hashlib, tempfile, unittest
from pathlib import Path
from scripts.validate_font_rights_manifest import validate
from scripts.run_batch_shaping_regression import require_minimum_families

def entry(path="font.otf", allowed=True, status="approved", evidence=None):
    return {"font_file":path,"family_id":"family-a","sha256":"a"*64,"license_name":"Example License",
            "license_url":"https://example.org/license","ml_training_allowed":allowed,"review_status":status,
            "reviewed_by":"reviewer-1","reviewed_date":"2026-11-19","evidence":evidence or ["https://example.org/terms"]}

class FontRightsTests(unittest.TestCase):
    def test_explicit_approval_passes_without_file_check(self):
        self.assertEqual(validate({"schema_version":1,"fonts":[entry()]},require_files=False)["status"],"PASS")
    def test_downloadability_or_license_name_is_not_approval(self):
        with self.assertRaisesRegex(ValueError,"not explicitly approved"):
            validate({"schema_version":1,"fonts":[entry(allowed=False)]},require_files=False)
    def test_pending_review_is_blocked(self):
        with self.assertRaisesRegex(ValueError,"not explicitly approved"):
            validate({"schema_version":1,"fonts":[entry(status="pending")]},require_files=False)
    def test_path_traversal_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"safe relative path"):
            validate({"schema_version":1,"fonts":[entry("../secret.otf")]},require_files=False)
    def test_batch_requires_three_distinct_families(self):
        manifest={"fonts":[entry("a.otf"),entry("b.otf"),entry("c.otf")]}
        with self.assertRaisesRegex(ValueError,"at least 3 distinct"):
            require_minimum_families(manifest)
        manifest["fonts"][1]["family_id"]="family-b"
        manifest["fonts"][2]["family_id"]="family-c"
        self.assertEqual(len(require_minimum_families(manifest)),3)
    def test_file_hash_must_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"font.otf"; path.write_bytes(b"font bytes")
            item=entry(); item["sha256"]=hashlib.sha256(b"different").hexdigest()
            with self.assertRaisesRegex(ValueError,"SHA-256 mismatch"):
                validate({"schema_version":1,"fonts":[item]},tmp,True)
if __name__=="__main__": unittest.main()
