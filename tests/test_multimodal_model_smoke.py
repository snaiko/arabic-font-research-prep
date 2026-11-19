import tempfile, unittest
try:
    import torch
except ModuleNotFoundError:
    torch = None

if torch is not None:
    from models.arabic_multimodal_glyph import ArabicMultimodalGlyphModel, encode_unicode_batch

@unittest.skipIf(torch is None, "PyTorch is installed only in the dedicated model-smoke workflow")
class MultimodalModelSmokeTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(7)
        self.model=ArabicMultimodalGlyphModel(latent_dim=64).eval()
        self.images=torch.rand(2,2,1,128,128)
        self.tokens=encode_unicode_batch(["بِسْمِ","Arabic"],max_length=16)
    def test_all_three_routes_forward_and_backward(self):
        for mode,kwargs in [
            ("image",{"reference_images":self.images}),
            ("text",{"prompt_ids":self.tokens}),
            ("hybrid",{"reference_images":self.images,"prompt_ids":self.tokens})]:
            self.model.zero_grad(set_to_none=True)
            out=self.model(mode,**kwargs)
            self.assertEqual(tuple(out["image"].shape),(2,1,128,128))
            self.assertEqual(tuple(out["uncertainty"].shape),(2,1))
            loss=out["image"].mean()+out["uncertainty"].mean()
            loss.backward()
            self.assertTrue(any(p.grad is not None for p in self.model.parameters()))
    def test_checkpoint_round_trip(self):
        before=self.model("hybrid",reference_images=self.images,prompt_ids=self.tokens)["image"].detach()
        with tempfile.NamedTemporaryFile(suffix=".pt") as f:
            torch.save({"model":self.model.state_dict(),"config":{"latent_dim":64}},f.name)
            payload=torch.load(f.name,map_location="cpu",weights_only=True)
            clone=ArabicMultimodalGlyphModel(latent_dim=payload["config"]["latent_dim"])
            clone.load_state_dict(payload["model"]); clone.eval()
            after=clone("hybrid",reference_images=self.images,prompt_ids=self.tokens)["image"].detach()
        self.assertTrue(torch.allclose(before,after,atol=1e-6))
    def test_unicode_encoder_preserves_arabic_codepoints(self):
        ids=encode_unicode_batch(["بَ"],max_length=4)
        self.assertEqual(ids[0,:2].tolist(),[0x628,0x64e])
if __name__=="__main__": unittest.main()
