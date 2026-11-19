import json, tempfile, unittest
from pathlib import Path
from PIL import Image
from scripts.build_arabic_cluster_review_pack import build
from scripts.validate_arabic_cluster_annotation import validate

class ClusterReviewTests(unittest.TestCase):
 def test_preserves_ligature_and_multiglyph_metadata(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); crops=root/"crops"; (crops/"images").mkdir(parents=True)
   Image.new("L",(160,160),100).save(crops/"images"/"c.png")
   row={"image":"images/c.png","font_file":"font.ttf","font_sha256":"a"*64,"family":"Family","split":"train","case_id":"lam_alef","cluster":0,"logical_start":0,"logical_end":2,"source_text":"لا","logical_text":"لا","logical_codepoints":["U+0644","U+0627"],"glyph_ids":[44,45],"glyph_count":2,"nonrendering_source_codepoints":[],"direction":"rtl","script":"Arab","language":"ar","features":[],"canvas":[160,160]}
   manifest=root/"source.jsonl"; manifest.write_text(json.dumps(row)+"\n",encoding="utf-8")
   out=root/"out"; build(manifest,crops,out,1,7)
   records=out/"cluster_annotations.jsonl"
   rec=json.loads(records.read_text(encoding="utf-8"))
   self.assertEqual(rec["cluster"]["logical_codepoints"],["U+0644","U+0627"])
   self.assertEqual(rec["cluster"]["glyph_ids"],[44,45])
   self.assertEqual(rec["status"],"draft")
   self.assertEqual(validate(records,manifest,out)["status"],"PASS")
 def test_rejects_tampered_image(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); crops=root/"crops"; (crops/"images").mkdir(parents=True)
   Image.new("L",(160,160),100).save(crops/"images"/"c.png")
   row={"image":"images/c.png","font_file":"f.ttf","font_sha256":"b"*64,"family":"F","split":"test","case_id":"zwnj","cluster":0,"logical_start":0,"logical_end":1,"source_text":"ب","logical_text":"ب","logical_codepoints":["U+0628"],"glyph_ids":[1],"glyph_count":1,"nonrendering_source_codepoints":[],"direction":"rtl","script":"Arab","language":"ar","features":[],"canvas":[160,160]}
   m=root/"m.jsonl"; m.write_text(json.dumps(row)+"\n")
   out=root/"o"; build(m,crops,out,1,1)
   image=next((out/"images").iterdir()); image.write_bytes(b"broken")
   self.assertEqual(validate(out/"cluster_annotations.jsonl",m,out)["status"],"FAIL")
