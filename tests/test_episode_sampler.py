import unittest
from scripts.build_mxfont_episodes import make_episodes

def row(cp):
    return {"font_sha256":"a"*64,"family":"FamilyA","split":"train",
            "codepoint":f"U+{cp:04X}","image":f"images/{cp}.png"}

class EpisodeTests(unittest.TestCase):
    def test_target_never_in_references(self):
        eps=make_episodes([row(x) for x in range(0x0621,0x0628)],4,12,7)
        self.assertTrue(eps)
        for ep in eps:
            target=ep["target"]["codepoint"]
            refs=[x["codepoint"] for x in ep["style_references"]]
            self.assertNotIn(target,refs)
            self.assertEqual(len(refs),4)
            self.assertEqual(len(set(refs)),4)
    def test_deterministic(self):
        rows=[row(x) for x in range(0x0621,0x0628)]
        self.assertEqual(make_episodes(rows,3,8,99),make_episodes(rows,3,8,99))
    def test_split_preserved(self):
        rows=[{**row(x),"split":"test"} for x in range(0x0621,0x0628)]
        eps=make_episodes(rows,4,2,1)
        self.assertTrue(all(x["split"]=="test" for x in eps))
    def test_too_few_glyphs_yields_no_episode(self):
        self.assertEqual(make_episodes([row(0x0627)],4,5,1),[])

if __name__ == "__main__":
    unittest.main()
