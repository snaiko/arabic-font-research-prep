import copy, unittest
from scripts.validate_glyph_visual_annotation import validate
from scripts.compare_glyph_annotations import compare_records
from test_glyph_visual_annotation import record

class AnnotationAgreementTests(unittest.TestCase):
    def test_identical_annotations_have_full_agreement(self):
        a=record(); b=copy.deepcopy(a); b["annotator"]["id"]="ann-02"
        result=compare_records(a,b,resolution=64)
        self.assertEqual(result["per_kind"]["body"]["mean_matched_iou"],1.0)
        self.assertEqual(result["per_kind"]["body"]["f1"],1.0)
    def test_different_render_is_rejected(self):
        a=record(); b=copy.deepcopy(a); b["glyph_instance"]["render_sha256"]="d"*64
        with self.assertRaises(ValueError): compare_records(a,b,resolution=64)
    def test_moved_polygon_reduces_iou(self):
        a=record(); b=copy.deepcopy(a); b["annotator"]["id"]="ann-02"
        b["components"][0]["geometry"]["points"]=[[0.6,0.2],[0.95,0.2],[0.9,0.6]]
        result=compare_records(a,b,threshold=0.5,resolution=64)
        self.assertLess(result["per_kind"]["body"]["mean_matched_iou"] or 0,1.0)

if __name__=="__main__": unittest.main()
