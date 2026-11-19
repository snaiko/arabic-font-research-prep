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

    def test_all_three_routes_forward_and_backward(self):
        routes = [
            ("image", {"reference_images": self.images}),
            ("text", {"style_prompt_ids": self.style_text}),
            ("hybrid", {
                "reference_images": self.images,
                "style_prompt_ids": self.style_text,
            }),
        ]
        for mode, kwargs in routes:
            self.model.zero_grad(set_to_none=True)
            out = self.model(mode, target_ids=self.targets, **kwargs)
            self.assertEqual(tuple(out["image"].shape), (2, 1, 128, 128))
            self.assertEqual(tuple(out["uncertainty"].shape), (2, 1))
            self.assertEqual(tuple(out["content_latent"].shape), (2, 64))
            self.assertEqual(tuple(out["style_latent"].shape), (2, 64))
            loss = out["image"].mean() + out["uncertainty"].mean()
            loss.backward()
            self.assertTrue(any(p.grad is not None for p in self.model.parameters()))

    def test_every_route_requires_target_identity(self):
        with self.assertRaisesRegex(ValueError, "target_ids are required"):
            self.model("image", reference_images=self.images)
        with self.assertRaisesRegex(ValueError, "target_ids are required"):
            self.model("text", style_prompt_ids=self.style_text)

    def test_target_identity_changes_content_condition(self):
        first = self.model(
            "image", target_ids=encode_unicode_batch(["ب"], 4),
            reference_images=self.images[:1]
        )["content_latent"]
        second = self.model(
            "image", target_ids=encode_unicode_batch(["م"], 4),
            reference_images=self.images[:1]
        )["content_latent"]
        self.assertFalse(torch.allclose(first, second))

    def test_checkpoint_round_trip(self):
        before = self.model(
            "hybrid", target_ids=self.targets, reference_images=self.images,
            style_prompt_ids=self.style_text
        )["image"].detach()
        with tempfile.NamedTemporaryFile(suffix=".pt") as f:
            torch.save({
                "model": self.model.state_dict(),
                "config": {"latent_dim": 64},
            }, f.name)
            payload = torch.load(f.name, map_location="cpu", weights_only=True)
            clone = ArabicMultimodalGlyphModel(latent_dim=payload["config"]["latent_dim"])
            clone.load_state_dict(payload["model"])
            clone.eval()
            after = clone(
                "hybrid", target_ids=self.targets, reference_images=self.images,
                style_prompt_ids=self.style_text
            )["image"].detach()
        self.assertTrue(torch.allclose(before, after, atol=1e-6))

    def test_optimizer_checkpoint_can_resume(self):
        model = ArabicMultimodalGlyphModel(latent_dim=64)
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
        target_ids = encode_unicode_batch(["ب"], max_length=4)
        style_ids = encode_unicode_batch(["خط نسخي"], max_length=16)
        target = torch.rand(1, 1, 128, 128)
        out = model("text", target_ids=target_ids, style_prompt_ids=style_ids)["image"]
        loss = torch.nn.functional.l1_loss(out, target)
        loss.backward()
        optimizer.step()
        with tempfile.NamedTemporaryFile(suffix=".pt") as f:
            save_training_checkpoint(
                f.name, model, optimizer, step=17, metadata={"route": "text"}
            )
            clone = ArabicMultimodalGlyphModel(latent_dim=64)
            clone_optimizer = torch.optim.AdamW(clone.parameters(), lr=1e-3)
            state = restore_training_checkpoint(f.name, clone, clone_optimizer)
            self.assertEqual(state, {"step": 17, "metadata": {"route": "text"}})
            self.assertEqual(len(clone_optimizer.state), len(optimizer.state))
            for left, right in zip(model.parameters(), clone.parameters()):
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
