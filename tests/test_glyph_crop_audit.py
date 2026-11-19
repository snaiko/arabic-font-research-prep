import hashlib, json, tempfile, unittest
from pathlib import Path
from PIL import Image, ImageDraw
from scripts.audit_glyph_crops import audit


class GlyphCropAuditTests(unittest.TestCase):
    def fixture(self, root, *, blank=False, add_orphan=False, tamper_hash=False):
        images = root / "images"
        images.mkdir(parents=True)
        image_path = images / "sample.png"
        image = Image.new("L", (128, 128), 255)
        if not blank:
            ImageDraw.Draw(image).rectangle((40, 40, 80, 80), fill=0)
        image.save(image_path)
        font = root / "font.ttf"
        font.write_bytes(b"not-a-real-font")
        font_hash = hashlib.sha256(font.read_bytes()).hexdigest()
        image_hash = hashlib.sha256(image_path.read_bytes()).hexdigest()
        if tamper_hash:
            image_hash = "0" * 64
        row = {
            "image": "images/sample.png",
            "image_sha256": image_hash,
            "family": "f",
            "split": "train",
            "font_file": str(font),
            "font_sha256": font_hash,
            "codepoint": "U+0628",
            "unicode_char": "ب",
            "sample_type": "isolated_single_codepoint",
            "contextual_joining_supervision": False,
        }
        if add_orphan:
            Image.new("L", (128, 128), 255).save(images / "orphan.png")
        manifest = root / "glyph_crops.jsonl"
        manifest.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
        return manifest

    def test_rejects_blank_crop(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = audit(self.fixture(root, blank=True), root, root)
            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(any("blank crop" in error for error in report["errors"]))

    def test_rejects_image_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = audit(self.fixture(root, tamper_hash=True), root, root)
            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(any("image SHA-256 mismatch" in error for error in report["errors"]))

    def test_rejects_unreferenced_png(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = audit(self.fixture(root, add_orphan=True), root, root)
            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(report["unreferenced_image_files"], 1)


if __name__ == "__main__":
    unittest.main()
