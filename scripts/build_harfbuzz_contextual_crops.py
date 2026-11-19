#!/usr/bin/env python3
"""Build HarfBuzz-cluster-aware Arabic glyph crops from real shaped strings.

Each output image contains every output glyph belonging to one HarfBuzz cluster,
including attached marks. Multi-codepoint clusters (e.g. lam-alef) are retained
as clusters and never falsely labelled as single characters.
"""
from __future__ import annotations
import argparse, hashlib, json, unicodedata
from collections import defaultdict
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen

CANVAS = 160
PADDING = 12

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        for n,line in enumerate(f,1):
            if line.strip():
                try: yield json.loads(line)
                except json.JSONDecodeError as e: raise ValueError(f"{path}:{n}: {e}") from e

def clear_generated_images(out_dir: Path):
    """Remove stale PNGs from this generated dataset directory before rebuilding."""
    image_root = out_dir / "images"
    if not image_root.exists():
        return
    for path in image_root.rglob("*.png"):
        path.unlink()
    directories = sorted(
        (path for path in image_root.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for directory in directories:
        try:
            directory.rmdir()
        except OSError:
            pass

def shape_clusters(font_path: Path, text: str, case: dict, out_dir: Path, font_hash: str):
    import uharfbuzz as hb
    import cairosvg
    data=font_path.read_bytes()
    face=hb.Face(data); hbfont=hb.Font(face); hbfont.scale=(face.upem,face.upem)
    buf=hb.Buffer(); buf.add_str(text)
    buf.direction=case.get("direction","rtl")
    buf.script=case.get("script","Arab"); buf.language=case.get("language","ar")
    hb.shape(hbfont,buf,{feature:1 for feature in case.get("features",[])})
    infos=list(buf.glyph_infos); positions=list(buf.glyph_positions)
    clusters=sorted(set(info.cluster for info in infos))
    if not clusters: return []
    # HarfBuzz clusters cover rendered source spans. Explicitly preserve
    # whitespace/format controls that intentionally produce no glyph image.
    covered=set()
    for pos, cluster_start in enumerate(clusters):
        cluster_end=clusters[pos+1] if pos+1<len(clusters) else len(text)
        covered.update(range(cluster_start, cluster_end))
    nonrendering=[]
    for index, char in enumerate(text):
        if index in covered:
            continue
        category=unicodedata.category(char)
        if not (category.startswith("C") or category.startswith("Z")):
            raise ValueError(
                f"visible source character U+{ord(char):04X} at index {index} "
                "has no HarfBuzz glyph cluster"
            )
        nonrendering.append({
            "index": index, "char": char,
            "codepoint": f"U+{ord(char):04X}",
            "unicode_category": category
        })
    tt=TTFont(font_path)
    glyph_set=tt.getGlyphSet(); order=tt.getGlyphOrder()
    scale=1.0
    # Group shaped glyphs by HarfBuzz cluster while preserving visual glyph order.
    grouped=defaultdict(list); pen_x=0
    for info,pos in zip(infos,positions):
        grouped[info.cluster].append((info.codepoint,pen_x+pos.x_offset,pos.y_offset))
        pen_x += pos.x_advance
    results=[]
    pending_images=[]
    logical_starts=sorted(clusters)
    for cluster in clusters:
        glyphs=grouped[cluster]
        paths=[]; bounds=[]
        for gid,xpos,yoff in glyphs:
            if gid >= len(order): continue
            name=order[gid]; glyph=glyph_set[name]
            bp=BoundsPen(glyph_set); glyph.draw(bp)
            if bp.bounds is None: continue
            x0,y0,x1,y1=bp.bounds
            bounds.append((xpos+x0, -(yoff+y1), xpos+x1, -(yoff+y0)))
            pen=SVGPathPen(glyph_set); glyph.draw(pen)
            paths.append((pen.getCommands(),xpos,-yoff))
        if not bounds: continue
        minx=min(b[0] for b in bounds); miny=min(b[1] for b in bounds)
        maxx=max(b[2] for b in bounds); maxy=max(b[3] for b in bounds)
        w=max(1.0,maxx-minx); h=max(1.0,maxy-miny)
        factor=(CANVAS-2*PADDING)/max(w,h)
        tx=PADDING-minx*factor; ty=PADDING-miny*factor
        svg_paths=[]
        for d,xpos,baseline in paths:
            svg_paths.append(f'<path d="{d}" transform="translate({xpos:.4f},{baseline:.4f}) scale(1,-1)"/>')
        svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 {CANVAS} {CANVAS}">'
             f'<rect width="100%" height="100%" fill="white"/>'
             f'<g transform="translate({tx:.4f},{ty:.4f}) scale({factor:.8f})" fill="black" fill-rule="nonzero">'
             + "".join(svg_paths) + '</g></svg>')
        png=cairosvg.svg2png(bytestring=svg.encode(),output_width=CANVAS,output_height=CANVAS)
        start=cluster
        next_starts=[v for v in logical_starts if v>cluster]
        end=next_starts[0] if next_starts else len(text)
        logical=text[start:end]
        rel=Path("images")/font_hash[:12]/case["id"]/f"cluster_{cluster:04d}.png"
        target=out_dir/rel
        pending_images.append((target,png))
        results.append({
            "image":rel.as_posix(),"image_sha256":hashlib.sha256(png).hexdigest(),
            "font_file":str(font_path),"font_sha256":font_hash,
            "case_id":case["id"],"source_text":text,"cluster":cluster,
            "logical_start":start,"logical_end":end,"logical_text":logical,
            "logical_codepoints":[f"U+{ord(c):04X}" for c in logical],
            "nonrendering_source_codepoints":nonrendering,
            "glyph_ids":[g[0] for g in glyphs],
            "glyph_count":len(glyphs),"sample_type":"harfbuzz_shaped_cluster",
            "direction":case.get("direction","rtl"),"script":case.get("script","Arab"),
            "language":case.get("language","ar"),"features":case.get("features",[]),
            "canvas":[CANVAS,CANVAS],"renderer":"HarfBuzz+FontTools-outline+CairoSVG",
            "cluster_is_multi_codepoint":len(logical)>1,
            "font_units_per_em":face.upem
        })
    # Preserve every source control/separator that has no corresponding
    # rendered outline crop. This is context-level metadata copied to each
    # cluster row; it must not be silently lost between adjacent clusters.
    covered_rendered=set()
    for item in results:
        covered_rendered.update(range(item["logical_start"], item["logical_end"]))
    context_nonrendering=[]
    for index,char in enumerate(text):
        if index not in covered_rendered:
            category=unicodedata.category(char)
            if category.startswith("C") or category.startswith("Z"):
                context_nonrendering.append({
                    "index": index, "char": char,
                    "codepoint": f"U+{ord(char):04X}",
                    "unicode_category": category
                })
            else:
                raise ValueError(
                    f"visible source character U+{ord(char):04X} at index {index} "
                    "was not represented by a rendered cluster crop"
                )
    for item in results:
        item["nonrendering_source_codepoints"]=context_nonrendering
    # Commit the case's images only after every source character has been
    # accounted for. A failed shaping case must not leave orphan PNGs behind.
    for target,png in pending_images:
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(png)
    tt.close()
    return results

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--fonts",default="data/raw_fonts")
    p.add_argument("--collection",default="data/raw_fonts/fonts.jsonl")
    p.add_argument("--cases",default="data/shaping_regression_cases_v1.json")
    p.add_argument("--samples",default="data/training_samples/samples.jsonl")
    p.add_argument("--output",default="data/contextual_glyph_crops")
    a=p.parse_args()
    import uharfbuzz, cairosvg
    root=Path(a.fonts); out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    clear_generated_images(out)
    family_map={r["file"]:r.get("family","unknown") for r in read_jsonl(Path(a.collection))}
    split_by_hash={r["font_sha256"]:r.get("split") for r in read_jsonl(Path(a.samples))}
    cases=json.loads(Path(a.cases).read_text(encoding="utf-8"))["cases"]
    rows=[]; failures=[]
    for font_path in sorted(list(root.rglob("*.ttf"))+list(root.rglob("*.otf"))):
        digest=sha256(font_path)
        rel=font_path.as_posix()
        family=family_map.get(rel,family_map.get("data/raw_fonts/"+font_path.relative_to(root).as_posix(),font_path.parent.name))
        split=split_by_hash.get(digest)
        if split not in {"train","validation","test"}:
            failures.append({"font":rel,"case_id":"*","error":"font hash has no valid family-safe split in sample manifest"})
            continue
        for case in cases:
            try:
                made=shape_clusters(font_path,case["text"],case,out,digest)
                for row in made:
                    row["family"]=family
                    row["split"]=split
                    rows.append(row)
            except Exception as e:
                failures.append({"font":rel,"case_id":case["id"],"error":str(e)})
    manifest=out/"contextual_clusters.jsonl"
    manifest.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows),encoding="utf-8")
    summary={"schema_version":1,"status":"PASS" if rows and not failures else "PARTIAL" if rows else "FAIL",
             "cluster_samples":len(rows),"fonts":len({r["font_sha256"] for r in rows}),
             "families":len({r["family"] for r in rows}),"cases":len(cases),
             "multi_codepoint_clusters":sum(r["cluster_is_multi_codepoint"] for r in rows),
             "failures":failures,
             "scope":"Real shaped output clusters with glyph IDs, logical source spans, mark/ligature grouping and outline-derived raster crops. Not human visual validation, component decomposition, or legal training-rights approval."}
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    # A font may lack a visible glyph for one shaping case. Keep other
    # verified data, record the exclusion in summary.json, and fail only
    # when no usable clusters were produced.
    if not rows: raise SystemExit(2)

if __name__=="__main__": main()
