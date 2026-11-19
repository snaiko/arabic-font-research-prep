import unittest
from scripts.validate_arabic_character_system import validate

def payload():
    return {"schema_version":1,"records":[{
        "codepoint":"U+0628","character":"ب","joining_type":"D",
        "forms_supported_by_joining_type":["isol","init","medi","fina"],
        "visual_family_status":"provisional_human_grouping_not_unicode_property",
        "component_annotation_status":"not_annotated"}]}

class ArabicCharacterSystemTests(unittest.TestCase):
    def test_valid_record(self):
        self.assertEqual(validate(payload()), [])
    def test_rejects_mismatched_codepoint(self):
        p=payload(); p["records"][0]["character"]="ت"
        self.assertTrue(any("mismatch" in e for e in validate(p)))
    def test_rejects_impossible_form(self):
        p=payload(); p["records"][0]["joining_type"]="R"; p["records"][0]["forms_supported_by_joining_type"]=["isol","fina","medi"]
        self.assertTrue(any("conflict" in e for e in validate(p)))
    def test_rejects_duplicate_codepoint(self):
        p=payload(); p["records"].append(dict(p["records"][0]))
        self.assertTrue(any("duplicate" in e for e in validate(p)))
    def test_visual_family_cannot_claim_unicode_status(self):
        p=payload(); p["records"][0]["visual_family_status"]="unicode"
        self.assertTrue(any("provenance" in e for e in validate(p)))

if __name__ == "__main__":
    unittest.main()
