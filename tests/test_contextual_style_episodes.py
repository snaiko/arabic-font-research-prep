import unittest

from scripts.build_contextual_style_episodes import build_episodes


class ContextualStyleEpisodeTests(unittest.TestCase):
    def target(self, cluster, logical="ب"):
        return {
            "font_sha256": "a" * 64,
            "family": "family-a",
            "split": "train",
            "image": f"context/{cluster}.png",
            "logical_text": logical,
            "case_id": "join",
            "cluster": cluster,
        }

    def references(self):
        return [
            {
                "font_sha256": "a" * 64,
                "family": "family-a",
                "split": "train",
                "codepoint": f"U+{0x0621+i:04X}",
                "unicode_char": chr(0x0621+i),
                "image": f"isolated/{i}.png",
            }
            for i in range(1, 8)
        ]

    def test_excludes_all_target_codepoints_and_preserves_split(self):
        targets = [self.target(0, "بَ")]
        episodes, skipped = build_episodes(targets, self.references(), refs_per_episode=4)
        self.assertEqual(len(episodes), 1)
        self.assertEqual(skipped, {})
        episode = episodes[0]
        refs = {row["codepoint"] for row in episode["style_references"]}
        self.assertNotIn("U+0628", refs)
        self.assertNotIn("U+064E", refs)
        self.assertEqual(episode["split"], "train")
        self.assertEqual(episode["reference_count"], 4)

    def test_deterministic_sampling(self):
        target = [self.target(1, "لا")]
        first, _ = build_episodes(target, self.references(), refs_per_episode=3, seed=19)
        second, _ = build_episodes(target, self.references(), refs_per_episode=3, seed=19)
        self.assertEqual(
            [x["codepoint"] for x in first[0]["style_references"]],
            [x["codepoint"] for x in second[0]["style_references"]],
        )

    def test_requires_same_font_and_family_split(self):
        refs = self.references()
        for row in refs:
            row["family"] = "another-family"
            row["split"] = "validation"
        episodes, skipped = build_episodes([self.target(0)], refs, refs_per_episode=4)
        self.assertEqual(episodes, [])
        self.assertEqual(sum(skipped.values()), 1)

    def test_rejects_duplicate_target_identity(self):
        with self.assertRaisesRegex(ValueError, "duplicate contextual target identity"):
            build_episodes(
                [self.target(0), self.target(0, "م")],
                self.references(),
                refs_per_episode=2,
            )


if __name__ == "__main__":
    unittest.main()
