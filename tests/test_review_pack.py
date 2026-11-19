import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from scripts.build_arabic_review_pack import pick_stratified, main
from scripts.validate_glyph_visual_annotation import validate

class ReviewPackTests(unittest.TestCase):
    def test_stratified_selection_is_deterministic_and_spreads_families(self):
        rows=[]
        for case in ("a","b"):
            for family in ("F1","F2","F3"):
                for i in range(3):
                    rows.append({"case_id":case,"family":family,"i":i})
        first=pick_stratified(rows,6,42)
        second=pick_stratified(rows,6,42)
        self.assertEqual(first,second)
        for case in ("a","b"):
            chosen=[r for r in first if r["case_id"]==case]
            self.assertEqual(len(chosen),6)
            self.assertEqual(len({r["family"] for r in chosen}),3)

    def test_pack_contains_review_images_and_two_draft_annotations(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); crops=root/"crops"; (crops/"images").mkdir(parents=True)
            Image.new("L",(160,160),128).save(crops/"images"/"one.png")
            row={"image":"images/one.png","font_file":"font.ttf","font_sha256":"a"*64,
              "family":"FamilyA","split":"train","case_id":"dual_joining_chain",
              "source_text":"ب","logical_start":0,"logical_end":1,"logical_text":"ب",
              "logical_codepoints":["U+0628"],"glyph_ids":[17],"glyph_count":1,
              "cluster_is_multi_codepoint":False,"nonrendering_source_codepoints":[],
              "direction":"rtl","script":"Arab","language":"ar","features":[],
              "canvas":[160,160]}
            manifest=root/"manifest.jsonl"
            manifest.write_text(json.dumps(row,ensure_ascii=False)+"\n",encoding="utf-8")
            out=root/"pack"
            import sys
            old=sys.argv
            try:
                sys.argv=["build_arabic_review_pack","--manifest",str(manifest),
                  "--crop-root",str(crops),"--output",str(out),"--per-case","1","--geometry-count","1"]
                main()
            finally: sys.argv=old
            a=json.loads((out/"geometry_annotations"/"annotator_a.jsonl").read_text().splitlines()[0])
            b=json.loads((out/"geometry_annotations"/"annotator_b.jsonl").read_text().splitlines()[0])
            self.assertEqual(validate(a),[])
            self.assertEqual(validate(b),[])
            self.assertEqual(a["glyph_instance"]["render_sha256"],b["glyph_instance"]["render_sha256"])
            self.assertTrue((out/"index.html").is_file())
            self.assertEqual(len(list((out/"images").glob("*.png"))),1)
            self.assertEqual(len((out/"visual_linguistic_review.jsonl").read_text().splitlines()),1)
            self.assertEqual(len(list((out/"geometry_annotations"/"images").glob("*.png"))),1)

if __name__=="__main__": unittest.main()
