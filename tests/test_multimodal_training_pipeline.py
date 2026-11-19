import hashlib
import json
import tempfile
import unittest
from pathlib import Path

try:
    import torch
    from PIL import Image, ImageDraw
except ModuleNotFoundError:
    torch = None

if torch is not None:
    from scripts.train_multimodal_glyph import (
        ContextualEpisodeDataset,
        collate_batch,
        edge_loss,
        validate_rights,
    )


@unittest.skipIf(torch is None, "PyTorch is installed only in the dedicated model workflow")
class MultimodalTrainingPipelineTests(unittest.TestCase):
    def make_image(self, path, offset=0):
        path.parent.mkdir(parents=True, exist_ok=True)
        image = Image.new("L", (128, 128), 255)
        draw = ImageDraw.Draw(image)
        draw.rectangle((20 + offset, 20, 70 + offset, 100), fill=0)
        image.save(path)

    def make_episode(self, target_root, ref_root, split="train"):
        target_path = target_root / "images/target.png"
        self.make_image(target_path)
        for index in range(4):
            self.make_image(ref_root / f"images/ref{index}.png", index * 3)
        target = {
            "image": "images/target.png",
            "logical_text": "بَ",
            "font_sha256": "a" * 64,
            "family": "family-a",
            "split": split,
        }
        refs = []
        for index in range(4):
            ref_path = ref_root / f"images/ref{index}.png"
            refs.append({
                "image": f"images/ref{index}.png",
                "image_sha256": hashlib.sha256(ref_path.read_bytes()).hexdigest(),
                "codepoint": f"U+{0x0621+index:04X}",
                "font_sha256": "a" * 64,
                "family": "family-a",
                "split": split,
            })
        return {
            "font_sha256": "a" * 64,
            "family": "family-a",
            "split": split,
            "target": target,
            "target_image_sha256": hashlib.sha256(target_path.read_bytes()).hexdigest(),
            "style_references": refs,
            "reference_count": 4,
        }

    def rights(self, digest="a" * 64, family="family-a"):
        return {
            "policy": {
                "status": "CONDITIONAL_OFL_1_1_APPROVAL",
                "output_font_license": "SIL Open Font License 1.1",
            },
            "fonts": [{
                "sha256": digest,
                "family_id": family,
                "ml_training_allowed": True,
                "review_status": "approved",
            }],
        }

    def test_rights_gate_rejects_unapproved_hash(self):
        episode = self.make_episode(Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp()))
        with self.assertRaisesRegex(ValueError, "not approved"):
            validate_rights([episode], self.rights(digest="b" * 64))

    def test_rights_gate_rejects_family_mismatch(self):
        episode = self.make_episode(Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp()))
        episode["family"] = "wrong-family"
        with self.assertRaisesRegex(ValueError, "family does not match"):
            validate_rights([episode], self.rights())

    def test_rights_gate_rejects_target_split_mismatch(self):
        episode = self.make_episode(Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp()))
        episode["target"]["split"] = "validation"
        with self.assertRaisesRegex(ValueError, "provenance or split"):
            validate_rights([episode], self.rights())

    def test_dataset_and_collate_shapes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target_root = root / "target"
            ref_root = root / "refs"
            episode = self.make_episode(target_root, ref_root)
            episode_path = root / "train.jsonl"
            episode_path.write_text(json.dumps(episode, ensure_ascii=False) + "\n", encoding="utf-8")
            dataset = ContextualEpisodeDataset(episode_path, target_root, ref_root)
            batch = collate_batch([dataset[0]])
            self.assertEqual(tuple(batch["target_images"].shape), (1, 1, 128, 128))
            self.assertEqual(tuple(batch["reference_images"].shape), (1, 4, 1, 128, 128))
            self.assertEqual(batch["target_ids"][0, :2].tolist(), [0x0628, 0x064E])

    def test_dataset_rejects_modified_target_image(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target_root, ref_root = root / "target", root / "refs"
            episode = self.make_episode(target_root, ref_root)
            Image.new("L", (128, 128), 0).save(target_root / "images/target.png")
            path = root / "train.jsonl"
            path.write_text(json.dumps(episode) + "\\n", encoding="utf-8")
            dataset = ContextualEpisodeDataset(path, target_root, ref_root)
            with self.assertRaisesRegex(ValueError, "target image hash mismatch"):
                dataset[0]

    def test_dataset_rejects_modified_style_reference(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target_root, ref_root = root / "target", root / "refs"
            episode = self.make_episode(target_root, ref_root)
            Image.new("L", (128, 128), 0).save(ref_root / "images/ref0.png")
            path = root / "train.jsonl"
            path.write_text(json.dumps(episode) + "\\n", encoding="utf-8")
            dataset = ContextualEpisodeDataset(path, target_root, ref_root)
            with self.assertRaisesRegex(ValueError, "style reference image hash mismatch"):
                dataset[0]

    def test_edge_loss_is_finite(self):
        prediction = torch.rand(2, 1, 128, 128)
        target = torch.rand(2, 1, 128, 128)
        value = edge_loss(prediction, target)
        self.assertTrue(torch.isfinite(value))


if __name__ == "__main__":
    unittest.main()
