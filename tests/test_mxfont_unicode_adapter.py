import unittest

try:
    import torch
except ModuleNotFoundError:
    torch = None

if torch is not None:
    from models.mxfont_unicode_adapter import MXFontUnicodeFactorAdapter
    from models.arabic_multimodal_glyph import encode_unicode_batch


@unittest.skipIf(torch is None, "PyTorch is installed in the dedicated model-smoke workflow")
class MXFontUnicodeAdapterTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(19)
        self.adapter = MXFontUnicodeFactorAdapter(latent_dim=32, embedding_dim=8)
        self.factors = {
            "last": torch.randn(2, 3, 256, 4, 4),
            "skip": torch.randn(2, 3, 128, 8, 8),
        }
        self.ids = encode_unicode_batch(["ب", "م"], max_length=8)

    def test_fresh_adapter_is_exact_identity_for_mxfont(self):
        result = self.adapter(self.factors, self.ids)
        for key in self.factors:
            self.assertTrue(torch.equal(result[key], self.factors[key]))

    def test_unicode_branch_changes_factors_after_nonzero_projection(self):
        with torch.no_grad():
            for block in self.adapter.adapters.values():
                block["residual"].weight.normal_(0, 0.01)
                block["residual"].bias.normal_(0, 0.01)
        result = self.adapter(self.factors, self.ids)
        self.assertFalse(torch.allclose(result["last"], self.factors["last"]))
        self.assertEqual(result["last"].shape, self.factors["last"].shape)
        self.assertEqual(result["skip"].shape, self.factors["skip"].shape)

    def test_unicode_ids_receive_gradients(self):
        self.adapter.train()
        result = self.adapter(self.factors, self.ids)
        loss = sum(value.square().mean() for value in result.values())
        loss.backward()
        self.assertIsNotNone(self.adapter.content_encoder.embedding.weight.grad)

    def test_rejects_wrong_factor_channels_and_batch(self):
        with self.assertRaisesRegex(ValueError, "channel mismatch"):
            self.adapter({"last": torch.randn(2, 3, 12, 4, 4), "skip": self.factors["skip"]}, self.ids)
        with self.assertRaisesRegex(ValueError, "batch size"):
            self.adapter(self.factors, self.ids[:1])


if __name__ == "__main__":
    unittest.main()
