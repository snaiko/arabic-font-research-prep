import json, tempfile, unittest
from pathlib import Path
from PIL import Image, ImageDraw
from scripts.build_arabic_component_supervision import build, components
from scripts.audit_arabic_linguistic_consistency import audit

class ArabicComponentSupervisionTests(unittest.TestCase):
    def test_components_and_captions_are_explicitly_unreviewed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/"images").mkdir()
            im=Image.new("L",(32,32),255); d=ImageDraw.Draw(im); d.rectangle((10,12,20,25),fill=0); d.ellipse((14,3,17,6),fill=0)
            im.save(root/"images/a.png")
            manifest=root/"source.jsonl"
            row={"image":"images/a.png","font_sha256":"a"*64,"family":"F","split":"train",
              "case_id":"mark","cluster":0,"source_text":"بَ","logical_text":"بَ",
              "logical_start":0,"logical_end":2,"logical_codepoints":["U+0628","U+064E"],
              "glyph_ids":[7,8],"glyph_count":2}
            manifest.write_text(json.dumps(row,ensure_ascii=False)+"\n",encoding="utf-8")
            registry={"unicode_version":"17.0.0","records":[
              {"codepoint":"U+0628","character":"ب","unicode_name":"ARABIC LETTER BEH","general_category":"Lo","role":"letter","joining_type":"D","joining_group":"Beh","is_combining_mark":False},
              {"codepoint":"U+064E","character":"َ","unicode_name":"ARABIC FATHA","general_category":"Mn","role":"mark","joining_type":"T","joining_group":"No_Joining_Group","is_combining_mark":True}]}
            reg=root/"registry.json"; reg.write_text(json.dumps(registry,ensure_ascii=False),encoding="utf-8")
            out=root/"out.jsonl"; result=build(manifest,root,reg,out)
            record=json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(result["records"],1); self.assertEqual(record["combining_mark_count"],1); self.assertEqual(record["cluster"],0)
            self.assertEqual(record["unicode_character_metadata"][1]["joining_type"],"T")
            self.assertFalse(record["label_provenance"]["expert_visual_linguistic_approval"])
            self.assertTrue(all(x["semantic_identity"]=="unknown" for x in record["component_candidates"]))
            self.assertEqual(record["captions"]["ar"]["provenance"],"machine_generated_unreviewed")

class ArabicLinguisticAuditTests(unittest.TestCase):
    def test_unicode_metadata_matches_canonical_cluster(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            row={"case_id":"case","source_text":"بَ","logical_start":0,"logical_end":2,
              "logical_text":"بَ","logical_codepoints":["U+0628","U+064E"],"font_sha256":"a"*64,
              "cluster":0,"glyph_ids":[7,8],"glyph_count":2}
            m=root/"m.jsonl"; m.write_text(json.dumps(row,ensure_ascii=False)+"\n",encoding="utf-8")
            cases=root/"cases.json"; cases.write_text(json.dumps({"cases":[{"id":"case","text":"بَ"}]},ensure_ascii=False),encoding="utf-8")
            registry={"unicode_version":"17.0.0","records":[
              {"codepoint":"U+0628","character":"ب","general_category":"Lo","joining_type":"D","is_combining_mark":False},
              {"codepoint":"U+064E","character":"َ","general_category":"Mn","joining_type":"T","is_combining_mark":True}]}
            r=root/"r.json"; r.write_text(json.dumps(registry,ensure_ascii=False),encoding="utf-8")
            result=audit(m,cases,r)
            self.assertEqual(result["status"],"PASS")
            self.assertEqual(result["stats"]["transparent_joining_chars"],1)

if __name__=="__main__": unittest.main()
