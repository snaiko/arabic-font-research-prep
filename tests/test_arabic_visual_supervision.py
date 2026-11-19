import json, tempfile, unittest
from pathlib import Path
from PIL import Image, ImageDraw
from scripts.build_arabic_visual_supervision import build

class VisualSupervisionTests(unittest.TestCase):
    def make_source(self, root):
        (root/"images").mkdir()
        im=Image.new("L",(32,32),255); ImageDraw.Draw(im).rectangle((8,6,20,25),fill=0)
        im.save(root/"images/a.png")
        row={"image":"images/a.png","font_sha256":"a"*64,"family":"Family",
             "split":"train","case_id":"isolated","cluster":0,
             "logical_text":"ب","source_text":"ب","glyph_ids":[7],"glyph_count":1,
             "nonrendering_source_codepoints":[],"direction":"rtl","script":"Arab",
             "language":"ar","features":[]}
        row2=dict(row,case_id="isolated_variant",cluster=1)
        manifest=root/"source.jsonl"
        manifest.write_text(json.dumps(row,ensure_ascii=False)+"\n"+json.dumps(row2,ensure_ascii=False)+"\n",encoding="utf-8")
        return manifest

    def test_builds_measurements_and_keeps_unapproved_data_ineligible(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); manifest=self.make_source(root); output=root/"out.jsonl"
            result=build(manifest,root,output)
            records=[json.loads(x) for x in output.read_text(encoding="utf-8").splitlines()]
            record=records[0]
            self.assertEqual(result["records"],2)
            self.assertEqual(result["unique_images"],1)
            self.assertEqual(len(records),2)
            self.assertFalse(record["supervision_provenance"]["training_eligible"])
            self.assertEqual(len(record["raster_geometry"]["row_occupancy_16"]),16)
            self.assertEqual(record["logical_codepoints"],["U+0628"])
            self.assertEqual(record["raster_geometry"]["canvas_width"],32)

    def test_approved_manifest_uses_sha256_field(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); manifest=self.make_source(root); output=root/"out.jsonl"
            rights=root/"rights.json"
            rights.write_text(json.dumps({"fonts":[{
                "sha256":"a"*64,"ml_training_allowed":True,"review_status":"approved"
            }]}),encoding="utf-8")
            result=build(manifest,root,output,rights)
            records=[json.loads(x) for x in output.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(result["rights_approved_records"],2)
            self.assertTrue(records[0]["supervision_provenance"]["training_eligible"])

    def test_pending_manifest_does_not_enable_training(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); manifest=self.make_source(root); output=root/"out.jsonl"
            rights=root/"rights.json"
            rights.write_text(json.dumps({"fonts":[{
                "sha256":"a"*64,"ml_training_allowed":False,"review_status":"pending"
            }]}),encoding="utf-8")
            result=build(manifest,root,output,rights)
            self.assertEqual(result["rights_approved_records"],0)

if __name__=="__main__": unittest.main()
