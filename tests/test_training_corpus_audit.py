import json, tempfile, unittest
from pathlib import Path
from scripts.audit_training_corpus import audit, AuditFailure

class CorpusAuditTests(unittest.TestCase):
    def write(self,p,rows):
        p.write_text("".join(json.dumps(x)+"\n" for x in rows),encoding="utf-8")
    def row(self,family="A",split="train",digest="a"*64):
        return {"family":family,"split":split,"font_sha256":digest,"sample_type":"glyph_context",
                "target_char":"ب","text":"ب","target_index":0}
    def test_clean_family_split_passes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"samples.jsonl"; self.write(p,[self.row("A","train"),self.row("B","test","b"*64)])
            self.assertEqual(audit(p)["status"],"PASS")
    def test_family_leakage_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"samples.jsonl"; self.write(p,[self.row("A","train"),self.row("A","test","b"*64)])
            with self.assertRaises(AuditFailure): audit(p)
    def test_duplicate_sample_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"samples.jsonl"; row=self.row()
            self.write(p,[row,row])
            with self.assertRaises(AuditFailure): audit(p)
    def test_unapproved_source_asset_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"samples.jsonl"; a=Path(d)/"assets.jsonl"
            self.write(p,[self.row()])
            self.write(a,[{"asset_id":"x","training_permission":"unclear","sha256":"a"*64,
                           "evidence_url":"https://example.org","reviewed_by":"r","review_date":"2026-11-19"}])
            with self.assertRaises(AuditFailure): audit(p,source_assets_path=a)
if __name__=="__main__": unittest.main()
