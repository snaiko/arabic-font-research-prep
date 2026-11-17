#!/usr/bin/env python3
"""Windows local preflight for the Arabic font research project; never starts training."""
from __future__ import annotations
import ctypes, json, os, platform, shutil, subprocess, sys, urllib.request, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "https://github.com/snaiko/arabic-font-research-prep/releases/download/arabic-glyph-dataset-v1/arabic-glyph-training-dataset.zip"
DATA = ROOT / "data" / "training_samples"
ARCHIVE = ROOT / "data" / "arabic-glyph-training-dataset.zip"
REPORT = ROOT / "reports" / "local" / "machine_preflight.json"

def command(args):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=15)
        return (p.stdout or p.stderr).strip() if p.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None

def ram_gb():
    if os.name != "nt": return None
    class M(ctypes.Structure):
        _fields_ = [("length",ctypes.c_ulong),("load",ctypes.c_ulong),("total",ctypes.c_ulonglong),
                    ("avail",ctypes.c_ulonglong),("page",ctypes.c_ulonglong),("availpage",ctypes.c_ulonglong),
                    ("virt",ctypes.c_ulonglong),("availvirt",ctypes.c_ulonglong),("extended",ctypes.c_ulonglong)]
    m=M(); m.length=ctypes.sizeof(M)
    return round(m.total/1024**3,2) if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)) else None

def gpu():
    d={"torch_available":False,"cuda_available":False,"torch_version":None,"cuda_version":None,
       "device_name":None,"vram_gb":None,"nvidia_smi":command(["nvidia-smi","--query-gpu=name,memory.total","--format=csv,noheader"])}
    try:
        import torch
        d.update(torch_available=True,cuda_available=torch.cuda.is_available(),torch_version=torch.__version__,cuda_version=torch.version.cuda)
        if torch.cuda.is_available():
            p=torch.cuda.get_device_properties(0); d.update(device_name=p.name,vram_gb=round(p.total_memory/1024**3,2))
    except Exception as e: d["torch_error"]=str(e)
    return d

def extract_safe(zfile,dest):
    root=dest.resolve()
    with zipfile.ZipFile(zfile) as z:
        for item in z.infolist():
            target=(dest/item.filename).resolve()
            if target != root and root not in target.parents: raise RuntimeError("Unsafe archive path: "+item.filename)
        z.extractall(dest)

def prepare_dataset():
    DATA.mkdir(parents=True,exist_ok=True)
    manifest=DATA/"samples.jsonl"
    if manifest.exists(): return {"available":True,"source":"existing","manifest":str(manifest.relative_to(ROOT))}
    ARCHIVE.parent.mkdir(parents=True,exist_ok=True)
    if not ARCHIVE.exists():
        req=urllib.request.Request(URL,headers={"User-Agent":"arabic-font-research-preflight"})
        with urllib.request.urlopen(req,timeout=90) as src, ARCHIVE.open("wb") as out: shutil.copyfileobj(src,out)
    extract_safe(ARCHIVE,DATA)
    matches=list(DATA.rglob("samples.jsonl"))
    if not matches: return {"available":False,"reason":"samples.jsonl missing after extraction"}
    source=matches[0].parent
    if source != DATA:
        for item in source.iterdir():
            target=DATA/item.name
            if not target.exists(): shutil.move(str(item),str(target))
    return {"available":manifest.exists(),"source":"GitHub Release","manifest":str(manifest.relative_to(ROOT)) if manifest.exists() else None}

def main():
    report={"os":platform.platform(),"python":sys.version,"python_executable":sys.executable,
      "architecture":platform.machine(),"cpu":platform.processor() or None,"ram_total_gb":ram_gb(),
      "gpu":gpu(),"dataset":None,"training_allowed":False,
      "training_status":"BLOCKED_PENDING_MODEL_IMPLEMENTATION_AND_DATASET_ADAPTER",
      "blocking_reasons":[
       "No executable MX-Font training implementation is included in this repository yet.",
       "The published 7,904 samples are full-line contextual renders, not verified target-glyph crops in the required model format.",
       "A dataset adapter, episode sampler, baseline reproduction, and smoke tests are required before training."],
      "next_steps":["Read LOCAL_AI_AGENT_GUIDE.md.","Implement and test a pinned MX-Font adapter.",
       "Convert and audit target-glyph crops while preserving family-safe splits.",
       "Choose batch size from detected hardware and run a short smoke test before full training."]}
    try:
        report["dataset"]=prepare_dataset()
        if not report["dataset"]["available"]: report["blocking_reasons"].append("Dataset preparation did not produce samples.jsonl.")
    except Exception as e:
        report["dataset"]={"available":False,"error":str(e)}
        report["blocking_reasons"].append("Dataset preparation failed: "+str(e))
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    print("\nPreflight complete. Training was NOT started. Report: "+str(REPORT.relative_to(ROOT)))
    return 0 if report["dataset"] and report["dataset"].get("available") else 2

if __name__=="__main__": raise SystemExit(main())
