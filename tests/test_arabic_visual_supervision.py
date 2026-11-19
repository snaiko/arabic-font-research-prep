import json, tempfile, unittest
from pathlib import Path
from PIL import Image, ImageDraw
from scripts.build_arabic_visual_supervision import build

class VisualSupervisionTests(unittest.TestCase):
    def test_builds_measurements_and_keeps_unapproved_data_ineligible(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/"images").mkdir()
            im=Image.new("L",(32,32),255); ImageDraw.Draw(im).rectangle((8,6,20,25),fill=0)
            im.save(root/"images/a.png")
            row={"image":"images/a.png","font_sha256":"a"*64,"family":"Family",
                 "split":"train","case_id":"isolated","cluster":0,
                 "logical_text":"ب","source_text":"ب","glyph_ids":[7],"glyph_count":1,
                 "nonrendering_source_codepoints":[],"direction":"rtl","script":"Arab",
                 "language":"ar","features":[]}
            manifest=root/"source.jsonl"; manifest.write_text(json.dumps(row,ensure_ascii=False)+"\n",encoding="utf-8")
            output=root/"out.jsonl"
            result=build(manifest,root,output)
            record=json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["records"],1)
            self.assertFalse(record["supervision_provenance"]["training_eligible"])
            self.assertEqual(len(record["raster_geometry"]["row_occupancy_16"]),16)
            self.assertEqual(record["logical_codepoints"],["U+0628"])
            self.assertEqual(record["raster_geometry"]["canvas_width"],32)

if __name__=="__main__": unittest.main()
