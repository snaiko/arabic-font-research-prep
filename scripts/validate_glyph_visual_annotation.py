#!/usr/bin/env python3
"""Small dependency-free checks for glyph visual annotation records."""
from __future__ import annotations
import re

HEX = re.compile(r"^U\+[0-9A-F]{4,6}$")
SHA = re.compile(r"^[0-9a-f]{64}$")

def _orientation(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])

def _segments_intersect(a, b, c, d, eps=1e-12):
    o1, o2 = _orientation(a,b,c), _orientation(a,b,d)
    o3, o4 = _orientation(c,d,a), _orientation(c,d,b)
    return ((o1 > eps and o2 < -eps or o1 < -eps and o2 > eps) and
            (o3 > eps and o4 < -eps or o3 < -eps and o4 > eps))

def _polygon_errors(points):
    errors=[]
    if len(set(tuple(p) for p in points if isinstance(p,list))) != len(points):
        errors.append("polygon contains duplicate vertices")
    area=sum(points[i][0]*points[(i+1)%len(points)][1]-
              points[(i+1)%len(points)][0]*points[i][1]
              for i in range(len(points)))/2
    if abs(area) < 1e-10:
        errors.append("polygon has zero/near-zero area")
    n=len(points)
    for i in range(n):
        a,b=points[i],points[(i+1)%n]
        for j in range(i+1,n):
            if j==i or j==(i+1)%n or (j+1)%n==i:
                continue
            if _segments_intersect(a,b,points[j],points[(j+1)%n]):
                errors.append("polygon self-intersects")
                return errors
    return errors

KINDS = {"body","dot","hamza","diacritic","other_mark","counter","join_region","stroke_segment","ornament","uncertain"}
RELATIONS = {"attached_to","above","below","inside","overlaps","joins","part_of","ambiguous_with"}

def validate(record):
    errors=[]
    def need(obj,key,path):
        if not isinstance(obj,dict) or key not in obj: errors.append(f"{path}.{key}: required")
    for k in ("schema_version","annotation_id","glyph_instance","annotator","status","components","relations","provenance"): need(record,k,"record")
    if errors: return errors
    if record["schema_version"] != 1: errors.append("schema_version must be 1")
    if record["status"] not in {"draft","independently_reviewed","adjudicated","rejected","uncertain"}: errors.append("invalid status")
    g=record["glyph_instance"]
    for k in ("codepoint","font_sha256","glyph_id","shaping_engine","direction","script","language","features","render_sha256","canvas"): need(g,k,"glyph_instance")
    if "codepoint" in g and not HEX.fullmatch(g["codepoint"]): errors.append("invalid glyph_instance.codepoint")
    for k in ("font_sha256","render_sha256"):
        if k in g and not SHA.fullmatch(g[k]): errors.append(f"invalid glyph_instance.{k}")
    if g.get("direction") not in {"rtl","ltr","ttb"}: errors.append("invalid direction")
    canvas=g.get("canvas",{})
    if not isinstance(canvas,dict) or not all(isinstance(canvas.get(k),int) and canvas[k]>0 for k in ("width","height")): errors.append("canvas width/height must be positive integers")
    a=record["annotator"]
    if not isinstance(a,dict) or not a.get("id") or not a.get("tool_version"): errors.append("annotator id and tool_version are required")
    ids=set()
    component_rows=[]
    for i,c in enumerate(record["components"]):
        p=f"components[{i}]"
        if not isinstance(c,dict): errors.append(f"{p} must be an object"); continue
        for k in ("component_id","kind","geometry","confidence"): need(c,k,p)
        cid=c.get("component_id")
        if not isinstance(cid,str) or not cid or cid in ids: errors.append(f"{p}: component_id must be unique and non-empty")
        ids.add(cid)
        component_rows.append(c)
        if c.get("kind") not in KINDS: errors.append(f"{p}: invalid kind")
        conf=c.get("confidence")
        if not isinstance(conf,(int,float)) or not 0<=conf<=1: errors.append(f"{p}: confidence outside [0,1]")
        geom=c.get("geometry",{})
        pts=geom.get("points",[]) if isinstance(geom,dict) else []
        if not isinstance(pts,list) or len(pts)<3: errors.append(f"{p}: polygon needs at least 3 points")
        else:
            valid_points=all(isinstance(xy,list) and len(xy)==2 and
                all(isinstance(v,(int,float)) and not isinstance(v,bool) and 0<=v<=1 for v in xy)
                for xy in pts)
            if not valid_points:
                errors.append(f"{p}: polygon coordinates must be normalized numeric pairs in [0,1]")
            else:
                for issue in _polygon_errors(pts):
                    errors.append(f"{p}: {issue}")
    for i,c in enumerate(component_rows):
        parent=c.get("parent_component_id")
        if parent is not None and (parent not in ids or parent==c.get("component_id")):
            errors.append(f"components[{i}]: invalid parent_component_id")
    for i,r in enumerate(record["relations"]):
        if not isinstance(r,dict):
            errors.append(f"relations[{i}]: relation must be an object"); continue
        if r.get("type") not in RELATIONS: errors.append(f"relations[{i}]: invalid relation type")
        if r.get("source") not in ids or r.get("target") not in ids: errors.append(f"relations[{i}]: unknown component reference")
        if r.get("source")==r.get("target"): errors.append(f"relations[{i}]: self-relation is not allowed")
    prov=record["provenance"]
    for k in ("dataset_id","source_image_sha256","annotation_guideline_version","created_at"): need(prov,k,"provenance")
    if isinstance(prov,dict) and "source_image_sha256" in prov and not SHA.fullmatch(prov["source_image_sha256"]): errors.append("invalid provenance.source_image_sha256")
    return errors
