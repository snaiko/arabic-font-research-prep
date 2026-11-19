#!/usr/bin/env python3
"""Build deterministic few-shot episodes from isolated glyph crops.

Each target and all style references come from the same exact font file. The
target codepoint is excluded from its own references. Family-level splits are
inherited from the crop manifest and are never reassigned here.
"""
from __future__ import annotations
import argparse, hashlib, json, random
from collections import defaultdict
from pathlib import Path

def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                try: yield json.loads(line)
                except json.JSONDecodeError as exc: raise ValueError(f"{path}:{n}: {exc}") from exc

def make_episodes(rows, refs_per_episode=4, episodes_per_font=64, seed=2026):
    groups = defaultdict(list)
    for row in rows:
        required = ("font_sha256", "family", "split", "codepoint", "image")
        if any(not row.get(k) for k in required):
            raise ValueError(f"crop record missing one of {required}: {row}")
        groups[(row["font_sha256"], row["family"], row["split"])].append(row)
    result = []
    for (font_hash, family, split), items in sorted(groups.items()):
        unique = {x["codepoint"]: x for x in items}
        items = [unique[k] for k in sorted(unique)]
        if len(items) < refs_per_episode + 1:
            continue
        rng = random.Random(f"{seed}:{font_hash}")
        for episode_index in range(episodes_per_font):
            target = items[episode_index % len(items)]
            candidates = [x for x in items if x["codepoint"] != target["codepoint"]]
            refs = rng.sample(candidates, refs_per_episode)
            episode_id = hashlib.sha256(
                f"{seed}:{font_hash}:{episode_index}:{target['codepoint']}".encode()
            ).hexdigest()[:16]
            result.append({
                "episode_id": episode_id, "font_sha256": font_hash,
                "family": family, "split": split, "target": target,
                "style_references": refs,
                "target_excluded_from_references": True,
                "reference_count": len(refs),
                "supervision_scope": "isolated_single_codepoint_only"
            })
    return result

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--crops", default="data/glyph_crops/glyph_crops.jsonl")
    ap.add_argument("--output", default="data/episodes")
    ap.add_argument("--references", type=int, default=4)
    ap.add_argument("--episodes-per-font", type=int, default=64)
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()
    if args.references < 1 or args.episodes_per_font < 1:
        ap.error("references and episodes-per-font must be positive")
    rows = list(read_jsonl(args.crops))
    episodes = make_episodes(rows, args.references, args.episodes_per_font, args.seed)
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    handles = {s: (out / f"{s}.jsonl").open("w", encoding="utf-8") for s in ("train", "validation", "test")}
    counts = defaultdict(int)
    try:
        for episode in episodes:
            split = episode["split"]
            if split not in handles:
                raise ValueError(f"Unexpected split {split!r}")
            target_cp = episode["target"]["codepoint"]
            ref_cps = [x["codepoint"] for x in episode["style_references"]]
            if target_cp in ref_cps or len(ref_cps) != len(set(ref_cps)):
                raise AssertionError("Target leakage or duplicate style reference detected")
            handles[split].write(json.dumps(episode, ensure_ascii=False) + "\n")
            counts[split] += 1
    finally:
        for handle in handles.values(): handle.close()
    summary = {
        "schema_version": 1, "seed": args.seed, "references_per_episode": args.references,
        "episodes_per_font": args.episodes_per_font, "total_episodes": len(episodes),
        "split_counts": dict(counts),
        "limitations": [
            "Episodes use isolated single-codepoint crops only.",
            "No MX-Font component/decomposition labels are supplied by this sampler.",
            "This is an intermediate adapter format, not yet the upstream MX-Font native loader format."
        ]
    }
    (out / "episode_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if episodes else 2

if __name__ == "__main__":
    raise SystemExit(main())
