import unittest

from scripts.build_mxfont_native_pairs import build_pairs


def row(split, family, font_sha, codepoint):
    return {
        "split": split,
        "family": family,
        "font_sha256": font_sha,
        "codepoint": codepoint,
        "unicode_char": chr(int(codepoint[2:], 16)),
        "image": f"images/{font_sha[:8]}/{codepoint}.png",
    }


class MXFontNativePairsTests(unittest.TestCase):
    def setUp(self):
        self.rows = []
        for split, families in (("train", ("A", "B", "C", "D")),
                                ("validation", ("E", "F", "G")),
                                ("test", ("H", "I", "J"))):
            for family in families:
                font_sha = family.lower() * 64
                for cp in ("U+0627", "U+0628", "U+062A", "U+062B", "U+062C"):
                    self.rows.append(row(split, family, font_sha, cp))

    def test_builds_same_font_style_and_cross_font_content_pairs(self):
        records = build_pairs(self.rows, styles_per_target=3, contents_per_target=2)
        self.assertEqual(len(records), len(self.rows))
        for record in records:
            target_cp = record["target"]["codepoint"]
            self.assertEqual(len(record["style_images"]), 3)
            self.assertEqual(len(record["content_images"]), 2)
            self.assertTrue(all(x["font_sha256"] == record["font_sha256"]
                                for x in record["style_images"]))
            self.assertTrue(all(x["codepoint"] != target_cp
                                for x in record["style_images"]))
            self.assertTrue(all(x["font_sha256"] != record["font_sha256"]
                                for x in record["content_images"]))
            self.assertIsNone(record["decomposition"])

    def test_never_crosses_family_splits(self):
        records = build_pairs(self.rows, styles_per_target=3, contents_per_target=2)
        by_sha = {r["font_sha256"]: r["split"] for r in self.rows}
        for record in records:
            self.assertTrue(all(by_sha[x["font_sha256"]] == record["split"]
                                for x in record["content_images"]))

    def test_deterministic_for_same_seed(self):
        a = build_pairs(self.rows, styles_per_target=3, contents_per_target=2, seed=77)
        b = build_pairs(self.rows, styles_per_target=3, contents_per_target=2, seed=77)
        self.assertEqual(a, b)

    def test_skips_target_without_enough_cross_font_examples(self):
        rows = [r for r in self.rows if not (r["split"] == "test" and r["family"] != "H")]
        records = build_pairs(rows, styles_per_target=3, contents_per_target=2)
        self.assertFalse(any(r["split"] == "test" for r in records))

    def test_rejects_duplicate_font_codepoint(self):
        with self.assertRaises(ValueError):
            build_pairs(self.rows + [self.rows[0]], styles_per_target=3, contents_per_target=2)


if __name__ == "__main__":
    unittest.main()
