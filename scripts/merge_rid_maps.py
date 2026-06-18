#!/usr/bin/env python3
"""Merge per-context RID map files into one.

The per-context docs/specs/rid_map.<context>.yaml files are the single source
of truth (one per bounded context, owned alongside that context's tests). This
merges them into the combined map that scripts/inject_rids.py consumes, so the
combined map is never a committed, drift-prone artifact.

Usage: merge_rid_maps.py <out.yaml> <in1.yaml> <in2.yaml> ...
"""

import sys
from pathlib import Path

import yaml


def main() -> int:
    out_path = Path(sys.argv[1])
    merged: dict = {}
    for inp in sys.argv[2:]:
        data = yaml.safe_load(Path(inp).read_text()) or {}
        overlap = merged.keys() & data.keys()
        if overlap:
            raise SystemExit(f"duplicate test key(s) across maps: {sorted(overlap)}")
        merged.update(data)
    out_path.write_text(yaml.safe_dump(merged, default_flow_style=False, sort_keys=True))
    print(f"merged {len(sys.argv) - 2} map(s) -> {out_path} ({len(merged)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
