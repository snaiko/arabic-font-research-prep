import tempfile, unittest
from pathlib import Path
from scripts.import_unicode_arabic_registry import build, parse_property_file

class UnicodeImporterTests(unittest.TestCase):
    def test_property_parser_expands_ranges(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"props.txt"; p.write_text("0627..0629 ; Arabic # comment\n")
            self.assertEqual(parse_property_file(p,"Arabic"),{0x627:"Arabic",0x628:"Arabic",0x629:"Arabic"})
    def test_build_preserves_joining_and_transparent_marks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"UnicodeData.txt").write_text(
                "0627;ARABIC LETTER ALEF;Lo;0;R;;;;;N;;;;;\n"
                "0628;ARABIC LETTER BEH;Lo;0;R;;;;;N;;;;;\n"
                "064B;ARABIC FATHATAN;Mn;27;NSM;;;;;N;;;;;\n")
            (root/"Scripts.txt").write_text("0627..0628 ; Arabic\n064B ; Arabic\n")
            (root/"ArabicShaping.txt").write_text("0627; ALEF; R; ALEF\n0628; BEH; D; BEH\n")
            data=build(root); rows={r["codepoint"]:r for r in data["records"]}
            self.assertEqual(rows["U+0627"]["possible_forms_by_joining_type"],["isol","fina"])
            self.assertEqual(rows["U+0628"]["possible_forms_by_joining_type"],["isol","init","medi","fina"])
            self.assertEqual(rows["U+064B"]["joining_type"],"T")
            self.assertEqual(rows["U+064B"]["role"],"mark")
            self.assertEqual(rows["U+064B"]["joining_group"],"No_Joining_Group")

if __name__=="__main__": unittest.main()
