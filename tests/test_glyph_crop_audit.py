import json, tempfile, unittest
from pathlib import Path
from PIL import Image
from scripts.audit_glyph_crops import audit

class GlyphCropAuditTests(unittest.TestCase):
    def test_rejects_blank_crop(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "images").mkdir()
            Image.new("L", (128, 128), 255).save(root / "images" / "blank.png")
            font = root / "font.ttf"; font.write_bytes(b"not-a-real-font")
            import hashlib
            digest = hashlib.sha256(font.read_bytes()).hexdigest()
            row = {"image":"images/blank.png","family":"f","split":"train",
                   "font_file":str(font),"font_sha256":digest,"codepoint":"U+0628",
                   "unicode_char":"ب","sample_type":"isolated_single_codepoint",
                   "contextual_joining_supervision":False}
            manifest = root / "glyph_crops.jsonl"
            manifest.write_text(json.dumps(row, ensure_ascii=False)+"\n", encoding="utf-8")
            report = audit(manifest, root, root)
            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(any("blank crop" in e for e in report["errors"]))

if __name__ == "__main__": unittest.main()
