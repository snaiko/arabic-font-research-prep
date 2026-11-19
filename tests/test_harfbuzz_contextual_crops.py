import tempfile
import unittest
from pathlib import Path

from PIL import Image

from scripts.build_harfbuzz_contextual_crops import clear_generated_images


class ContextualCropOutputTests(unittest.TestCase):
    def test_clear_generated_images_removes_stale_pngs_and_keeps_other_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            image_root = root / "images" / "font" / "case"
            image_root.mkdir(parents=True)
            stale = image_root / "stale.png"
            Image.new("RGB", (160, 160), "white").save(stale)
            note = image_root / "keep.txt"
            note.write_text("metadata", encoding="utf-8")

            clear_generated_images(root)

            self.assertFalse(stale.exists())
            self.assertTrue(note.exists())
            self.assertTrue(image_root.exists())


if __name__ == "__main__":
    unittest.main()
