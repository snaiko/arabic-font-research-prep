import tempfile, unittest
try:
    import torch
except ModuleNotFoundError:
    torch = None

if torch is not None:
    from models.arabic_multimodal_glyph import ArabicMultimodalGlyphModel, encode_unicode_batch, save_training_checkpoint, restore_training_checkpoint

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

    def test_optimizer_checkpoint_can_resume(self):
        model=ArabicMultimodalGlyphModel(latent_dim=64)
        optimizer=torch.optim.AdamW(model.parameters(),lr=1e-3)
        tokens=encode_unicode_batch(["ب"],max_length=4)
        target=torch.rand(1,1,128,128)
        out=model("text",prompt_ids=tokens)["image"]
        loss=torch.nn.functional.l1_loss(out,target)
        loss.backward(); optimizer.step()
        with tempfile.NamedTemporaryFile(suffix=".pt") as f:
            save_training_checkpoint(f.name,model,optimizer,step=17,metadata={"route":"text"})
            clone=ArabicMultimodalGlyphModel(latent_dim=64)
            clone_optimizer=torch.optim.AdamW(clone.parameters(),lr=1e-3)
            state=restore_training_checkpoint(f.name,clone,clone_optimizer)
            self.assertEqual(state,{"step":17,"metadata":{"route":"text"}})
            self.assertEqual(len(clone_optimizer.state),len(optimizer.state))
            for a,b in zip(model.parameters(),clone.parameters()):
                self.assertTrue(torch.equal(a,b))

    def test_unicode_encoder_preserves_arabic_codepoints(self):
        ids=encode_unicode_batch(["بَ"],max_length=4)
        self.assertEqual(ids[0,:2].tolist(),[0x628,0x64e])
if __name__=="__main__": unittest.main()
