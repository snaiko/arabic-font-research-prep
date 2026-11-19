import hashlib, json, tempfile, unittest
from pathlib import Path
from scripts.build_font_rights_candidates import build

class FontRightsCandidateTests(unittest.TestCase):
    def test_builds_pending_candidates_with_exact_hash_and_pinned_urls(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); font=root/"family"/"font.ttf"
            font.parent.mkdir(); font.write_bytes(b"font bytes")
            digest=hashlib.sha256(b"font bytes").hexdigest()
            source=root/"fonts.jsonl"
            row={"file":"family/font.ttf","sha256":digest,"family":"family",
              "license":"SIL Open Font License 1.1","license_file":"family/OFL.txt",
              "source_repository":"https://github.com/google/fonts",
              "source_revision":"a"*40,"source_path":"ofl/family/font.ttf"}
            source.write_text(json.dumps(row)+"\n",encoding="utf-8")
            result=build(source,root)
            self.assertEqual(result["font_count"],1)
            item=result["fonts"][0]
            self.assertFalse(item["ml_training_allowed"])
            self.assertEqual(item["review_status"],"pending")
            self.assertEqual(item["sha256"],digest)
            self.assertIn("a"*40,item["license_url"])
            self.assertEqual(result["approved_count"],0)

    def test_rejects_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/"font.ttf").write_bytes(b"actual")
            source=root/"fonts.jsonl"
            source.write_text(json.dumps({"file":"font.ttf","sha256":"0"*64,
              "family":"f","license":"OFL","license_file":"f/OFL.txt",
              "source_repository":"https://github.com/google/fonts",
              "source_revision":"a"*40,"source_path":"ofl/f/font.ttf"})+"\n")
            with self.assertRaisesRegex(ValueError,"SHA-256 mismatch"): build(source,root)

if __name__=="__main__": unittest.main()
