import json
import tempfile
import unittest
from pathlib import Path

from scripts.preflight_local_training import inspect_episodes, inspect_rights, recommended_batch_size


class LocalPreflightTests(unittest.TestCase):
    def episode(self, family, split, digest):
        return {
            "font_sha256": digest,
            "family": family,
            "split": split,
            "target": {"logical_text": "بَ", "split": split},
            "target_image_sha256": "d" * 64,
            "reference_count": 4,
            "style_references": [
                {
                    "font_sha256": digest,
                    "family": family,
                    "split": split,
                    "codepoint": f"U+{0x0621+i:04X}",
                    "image_sha256": f"{i+1:064x}",
                }
                for i in range(4)
            ],
        }

    def test_recommended_batch_size_uses_vram_and_ram(self):
        self.assertEqual(recommended_batch_size({"cuda_available": True, "vram_gb": 10}, 16), 8)
        self.assertEqual(recommended_batch_size({"cuda_available": True, "vram_gb": 5}, 16), 4)
        self.assertEqual(recommended_batch_size({"cuda_available": True, "vram_gb": 3}, 16), 2)
        self.assertEqual(recommended_batch_size({"cuda_available": False}, 32), 2)
        self.assertEqual(recommended_batch_size({"cuda_available": False}, 8), 1)

    def test_rights_manifest_requires_conditional_ofl_policy(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "rights.json"
            path.write_text(json.dumps({
                "policy": {
                    "status": "CONDITIONAL_OFL_1_1_APPROVAL",
                    "output_font_license": "SIL Open Font License 1.1",
                },
                "fonts": [
                    {"sha256": f"{i+1:064x}", "family_id": f"family-{i % 20}",
                     "ml_training_allowed": True, "review_status": "approved"}
                    for i in range(52)
                ],
            }), encoding="utf-8")
            result = inspect_rights(path)
            self.assertTrue(result["ok"])
            self.assertEqual(result["approved_font_files"], 52)
            self.assertEqual(result["families"], 20)

    def test_episode_splits_validate_font_rights_and_reference_leakage(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            episodes_dir = root / "episodes"
            episodes_dir.mkdir()
            rights = root / "rights.json"
            records = []
            for split, family, digest in (
                ("train", "train-family", "a" * 64),
                ("validation", "validation-family", "b" * 64),
                ("test", "test-family", "c" * 64),
            ):
                episode = self.episode(family, split, digest)
                (episodes_dir / f"{split}.jsonl").write_text(
                    json.dumps(episode) + "\n", encoding="utf-8"
                )
                records.append({
                    "sha256": digest, "family_id": family,
                    "ml_training_allowed": True, "review_status": "approved",
                })
            rights.write_text(json.dumps({
                "policy": {
                    "status": "CONDITIONAL_OFL_1_1_APPROVAL",
                    "output_font_license": "SIL Open Font License 1.1",
                },
                "fonts": records,
            }), encoding="utf-8")
            result = inspect_episodes(episodes_dir, rights)
            self.assertTrue(result["ok"])
            self.assertEqual(result["total_episodes"], 3)
            self.assertEqual(result["reference_images"], 12)

    def test_episode_audit_rejects_target_reference_codepoint_leak(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            episodes_dir = root / "episodes"
            episodes_dir.mkdir()
            rights = root / "rights.json"
            digest = "a" * 64
            rights.write_text(json.dumps({
                "policy": {
                    "status": "CONDITIONAL_OFL_1_1_APPROVAL",
                    "output_font_license": "SIL Open Font License 1.1",
                },
                "fonts": [{
                    "sha256": digest, "family_id": "family-a",
                    "ml_training_allowed": True, "review_status": "approved",
                }],
            }), encoding="utf-8")
            episode = self.episode("family-a", "train", digest)
            episode["style_references"][0]["codepoint"] = "U+0628"
            (episodes_dir / "train.jsonl").write_text(json.dumps(episode) + "\n", encoding="utf-8")
            for split in ("validation", "test"):
                (episodes_dir / f"{split}.jsonl").write_text(
                    json.dumps(self.episode(f"family-{split}", split, ("b" if split == "validation" else "c") * 64)) + "\n",
                    encoding="utf-8",
                )
            # Add the corresponding approved hashes for the other splits.
            data = json.loads(rights.read_text(encoding="utf-8"))
            data["fonts"].extend([
                {"sha256": "b" * 64, "family_id": "family-validation",
                 "ml_training_allowed": True, "review_status": "approved"},
                {"sha256": "c" * 64, "family_id": "family-test",
                 "ml_training_allowed": True, "review_status": "approved"},
            ])
            rights.write_text(json.dumps(data), encoding="utf-8")
            result = inspect_episodes(episodes_dir, rights)
            self.assertFalse(result["ok"])
            self.assertIn("leaked", result["reason"])


if __name__ == "__main__":
    unittest.main()
