import unittest
from scripts.validate_glyph_visual_annotation import validate

def record():
    return {
      "schema_version":1,"annotation_id":"a1",
      "glyph_instance":{"codepoint":"U+0628","font_sha256":"a"*64,"glyph_id":12,"shaping_engine":"HarfBuzz 10","direction":"rtl","script":"Arab","language":"ar","features":["rlig","calt"],"render_sha256":"b"*64,"canvas":{"width":128,"height":128}},
      "annotator":{"id":"ann-01","tool_version":"1.0"},
      "status":"draft",
      "components":[{"component_id":"body-1","kind":"body","geometry":{"type":"polygon","points":[[0.1,0.2],[0.8,0.2],[0.7,0.8]]},"confidence":0.95}],
      "relations":[],
      "provenance":{"dataset_id":"pilot","source_image_sha256":"c"*64,"annotation_guideline_version":"1.0","created_at":"2026-11-19T00:00:00Z"}
    }

class VisualAnnotationTests(unittest.TestCase):
    def test_valid_record(self): self.assertEqual(validate(record()),[])
    def test_rejects_out_of_bounds_geometry(self):
        r=record(); r["components"][0]["geometry"]["points"][0]=[1.2,0.2]
        self.assertTrue(any("normalized" in e for e in validate(r)))
    def test_rejects_unknown_relation_reference(self):
        r=record(); r["relations"]=[{"source":"missing","target":"body-1","type":"joins"}]
        self.assertTrue(any("unknown component" in e for e in validate(r)))
    def test_rejects_invalid_hash(self):
        r=record(); r["glyph_instance"]["font_sha256"]="bad"
        self.assertTrue(any("font_sha256" in e for e in validate(r)))
    def test_rejects_duplicate_component_id(self):
        r=record(); r["components"].append(dict(r["components"][0]))
        self.assertTrue(any("unique" in e for e in validate(r)))

if __name__ == "__main__": unittest.main()
