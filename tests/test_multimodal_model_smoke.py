import tempfile, unittest

try:
    import torch
except ModuleNotFoundError:
    torch = None

if torch is not None:
    from models.arabic_multimodal_glyph import (
        ArabicMultimodalGlyphModel,
        encode_unicode_batch,
        save_training_checkpoint,
        restore_training_checkpoint,
    )


class OptimizerStateProbe:
    """Checkpoint payload stand-in; deliberately does not create or run an optimizer."""

    def __init__(self, payload=None):
        self.payload = payload or {
            "state": {"parameter-slot-0": {"step": 17, "exp_avg": [0.0, 0.1]}},
            "param_groups": [{"lr": 0.001, "params": [0]}],
        }

    def state_dict(self):
        return self.payload

    def load_state_dict(self, payload):
        self.payload = payload


@unittest.skipIf(torch is None, "PyTorch is installed only in the dedicated model-smoke workflow")
class MultimodalModelSmokeTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(7)
        self.model = ArabicMultimodalGlyphModel(latent_dim=64).eval()
        self.images = torch.rand(2, 2, 1, 128, 128)
        self.targets = encode_unicode_batch(["بِسْمِ", "سلام"], max_length=16)
        self.style_text = encode_unicode_batch(
            ["خط نسخي ناعم", "elegant kufic"], max_length=32
        )

    def test_all_three_routes_forward_only_without_gradients(self):
        routes = [
            ("image", {"reference_images": self.images}),
            ("text", {"style_prompt_ids": self.style_text}),
            ("hybrid", {
                "reference_images": self.images,
                "style_prompt_ids": self.style_text,
            }),
        ]
        for mode, kwargs in routes:
            with torch.no_grad():
                out = self.model(mode, target_ids=self.targets, **kwargs)
            self.assertEqual(tuple(out["image"].shape), (2, 1, 128, 128))
            self.assertEqual(tuple(out["uncertainty"].shape), (2, 1))
            self.assertEqual(tuple(out["content_latent"].shape), (2, 64))
            self.assertEqual(tuple(out["style_latent"].shape), (2, 64))
            self.assertTrue(all(parameter.grad is None for parameter in self.model.parameters()))

    def test_every_route_requires_target_identity(self):
        with self.assertRaisesRegex(ValueError, "target_ids are required"):
            self.model("image", reference_images=self.images)
        with self.assertRaisesRegex(ValueError, "target_ids are required"):
            self.model("text", style_prompt_ids=self.style_text)

    def test_target_identity_changes_content_condition(self):
        with torch.no_grad():
            first = self.model(
                "image", target_ids=encode_unicode_batch(["ب"], 4),
                reference_images=self.images[:1]
            )["content_latent"]
            second = self.model(
                "image", target_ids=encode_unicode_batch(["م"], 4),
                reference_images=self.images[:1]
            )["content_latent"]
        self.assertFalse(torch.allclose(first, second))

    def test_checkpoint_round_trip_without_optimizer_execution(self):
        with torch.no_grad():
            before = self.model(
                "hybrid", target_ids=self.targets, reference_images=self.images,
                style_prompt_ids=self.style_text
            )["image"].detach()
        with tempfile.NamedTemporaryFile(suffix=".pt") as f:
            save_training_checkpoint(
                f.name, self.model, step=17, metadata={"route": "image", "latent_dim": 64}
            )
            clone = ArabicMultimodalGlyphModel(latent_dim=64)
            state = restore_training_checkpoint(f.name, clone)
            clone.eval()
            with torch.no_grad():
                after = clone(
                    "hybrid", target_ids=self.targets, reference_images=self.images,
                    style_prompt_ids=self.style_text
                )["image"].detach()
        self.assertEqual(state, {"step": 17, "metadata": {"route": "image", "latent_dim": 64}})
        self.assertTrue(torch.allclose(before, after, atol=1e-6))

    def test_checkpoint_restores_optimizer_state_payload_without_running_optimizer(self):
        source_state = OptimizerStateProbe()
        restored_state = OptimizerStateProbe({"state": {}, "param_groups": []})
        with tempfile.NamedTemporaryFile(suffix=".pt") as f:
            save_training_checkpoint(
                f.name, self.model, source_state, step=17, metadata={"route": "image"}
            )
            clone = ArabicMultimodalGlyphModel(latent_dim=64)
            state = restore_training_checkpoint(f.name, clone, restored_state)
        self.assertEqual(state, {"step": 17, "metadata": {"route": "image"}})
        self.assertEqual(restored_state.payload, source_state.payload)
        for left, right in zip(self.model.parameters(), clone.parameters()):
            self.assertTrue(torch.equal(left, right))

    def test_default_model_parameter_budget_is_consumer_scale(self):
        parameter_count = sum(parameter.numel() for parameter in self.model.parameters())
        self.assertLess(parameter_count, 25_000_000)
        self.assertIs(self.model.content_encoder.embedding, self.model.text_style_encoder.embedding)
        self.assertIs(self.model.content_encoder.embedding, self.model.unicode_embedding)

    def test_unicode_encoder_preserves_arabic_codepoints(self):
        ids = encode_unicode_batch(["بَ"], max_length=4)
        self.assertEqual(ids[0, :2].tolist(), [0x628, 0x64E])


if __name__ == "__main__":
    unittest.main()
