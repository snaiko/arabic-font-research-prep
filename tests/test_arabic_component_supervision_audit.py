import json, tempfile, unittest, hashlib
from pathlib import Path
from PIL import Image, ImageDraw
from scripts.audit_arabic_component_supervision import audit

class ComponentCaptionAuditTests(unittest.TestCase):
    def fixture(self, root):
        (root/"images").mkdir()
        im=Image.new("L",(160,160),255); ImageDraw.Draw(im).rectangle((50,50,100,110),fill=0)
        im.save(root/"images/a.png")
        digest=hashlib.sha256((root/"images/a.png").read_bytes()).hexdigest()
        row={"sample_id":"a"*64+":case:0","font_sha256":"a"*64,"case_id":"case","cluster":0,
          "image":"images/a.png","image_sha256":digest,"family":"Family","split":"train",
          "logical_text":"ب","logical_codepoints":["U+0628"],"codepoint_count":1,
          "glyph_ids":[7],"glyph_count":1,
          "component_candidates":[{"bbox_normalized":[.3,.3,.7,.7],"centroid_normalized":[.5,.5],
            "area_ratio":.2,"semantic_identity":"unknown"}],"component_candidate_count":1,
          "captions":{"ar":{"text":"وصف","language":"ar","provenance":"machine_generated_unreviewed"},
            "en":{"text":"caption","language":"en","provenance":"machine_generated_unreviewed"}},
          "label_provenance":{"component_semantics":"unknown_not_annotated",
            "expert_visual_linguistic_approval":False,"training_eligible":False}}
        manifest=root/"records.jsonl"; manifest.write_text(json.dumps(row,ensure_ascii=False)+"\n",encoding="utf-8")
        return manifest
    def test_valid_machine_record_passes_but_is_not_training_eligible(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); manifest=self.fixture(root); result=audit(manifest,root)
            self.assertEqual(result["status"],"PASS")
            self.assertEqual(result["training_eligible_records"],0)
    def test_semantic_identity_cannot_be_promoted_automatically(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); manifest=self.fixture(root)
            row=json.loads(manifest.read_text(encoding="utf-8"))
            row["component_candidates"][0]["semantic_identity"]="dot"
            manifest.write_text(json.dumps(row,ensure_ascii=False)+"\n",encoding="utf-8")
            self.assertEqual(audit(manifest,root)["status"],"FAIL")
    def test_family_split_leakage_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); manifest=self.fixture(root)
            rows=[json.loads(manifest.read_text(encoding="utf-8"))]
            second=dict(rows[0]); second["sample_id"]="b"*64+":case:1"; second["split"]="test"
            rows.append(second)
            manifest.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in rows)+"\n",encoding="utf-8")
            self.assertEqual(audit(manifest,root)["status"],"FAIL")
if __name__=="__main__": unittest.main()
