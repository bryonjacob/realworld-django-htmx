#!/usr/bin/env python3
"""Inject specdrive RID <property> elements into a JUnit XML report.

specdrive verify reads RIDs from each <testcase> via
`<property name="rid" value="RID-...">`. unittest-xml-reporting emits only
testsuite-level properties, so this post-processor adds per-testcase rid
properties from a mapping file.

Mapping file (docs/specs/rid_map.yaml) is the single source of truth:
    "<classname>::<test_name>": [RID-..., RID-...]
A test mapped to an empty list / "@NOSPEC" is treated as deliberately unspecced.

Usage: inject_rids.py <junit.xml> <rid_map.yaml>
"""

import sys
import xml.dom.minidom as minidom
from pathlib import Path

import yaml


def main() -> int:
    report_path, map_path = Path(sys.argv[1]), Path(sys.argv[2])
    rid_map = yaml.safe_load(map_path.read_text()) or {}

    doc = minidom.parse(str(report_path))
    injected = 0
    unmapped: list[str] = []

    for tc in doc.getElementsByTagName("testcase"):
        name = tc.getAttribute("name")
        key = f"{tc.getAttribute('classname')}::{name}"
        rids = rid_map.get(key)
        # pytest parametrized cases carry a [param] suffix; one map entry per
        # base scenario covers all its examples.
        if rids is None and "[" in name:
            base = f"{tc.getAttribute('classname')}::{name.split('[', 1)[0]}"
            rids = rid_map.get(base)
        if rids is None:
            unmapped.append(key)
            continue
        if isinstance(rids, str):
            rids = [rids]
        props = doc.createElement("properties")
        for rid in rids:
            p = doc.createElement("property")
            p.setAttribute("name", "rid")
            p.setAttribute("value", rid)
            props.appendChild(p)
        tc.insertBefore(props, tc.firstChild)
        injected += 1

    report_path.write_text(doc.toxml())
    print(f"injected rid properties into {injected} testcase(s)")
    if unmapped:
        print(f"WARNING: {len(unmapped)} testcase(s) absent from {map_path.name}:")
        for k in unmapped:
            print(f"  - {k}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
