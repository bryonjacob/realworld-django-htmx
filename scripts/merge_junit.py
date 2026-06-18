#!/usr/bin/env python3
"""Merge multiple JUnit XML reports into one <testsuites> document.

specdrive verify reads a single report file; this project produces two (the
Django suite and the pytest property suite). Usage:

    merge_junit.py <out.xml> <in1.xml> <in2.xml> ...
"""

import sys
import xml.dom.minidom as minidom
from pathlib import Path


def main() -> int:
    out_path = Path(sys.argv[1])
    inputs = sys.argv[2:]

    doc = minidom.Document()
    root = doc.createElement("testsuites")
    doc.appendChild(root)

    total = 0
    for inp in inputs:
        src = minidom.parse(inp)
        for suite in src.getElementsByTagName("testsuite"):
            root.appendChild(suite)
            total += len(suite.getElementsByTagName("testcase"))

    out_path.write_text(doc.toxml())
    print(f"merged {len(inputs)} report(s) -> {out_path} ({total} testcases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
