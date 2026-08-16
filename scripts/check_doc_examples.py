#!/usr/bin/env python3
"""Execute every python block in docs/ the way a reader following along would.

Each document's blocks run in one shared namespace, in order, so a snippet that
depends on an earlier one works — and a snippet that silently depends on
something never shown fails here rather than in a reader's terminal.

    python scripts/check_doc_examples.py

Exits non-zero if any block raises.
"""

from __future__ import annotations

import pathlib
import re
import sys
import traceback

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    failures = 0
    for doc in sorted((ROOT / "docs").glob("*.md")):
        blocks = re.findall(r"```python\n(.*?)```", doc.read_text(), re.S)
        if not blocks:
            continue
        namespace: dict = {}
        doc_failures = 0
        for index, block in enumerate(blocks, 1):
            try:
                exec(compile(block, f"{doc.name}#block{index}", "exec"), namespace)
            except Exception:  # noqa: BLE001 - report and continue
                doc_failures += 1
                print(f"FAIL {doc.name} block {index}", file=sys.stderr)
                traceback.print_exc(limit=2)
                print("---- block ----", file=sys.stderr)
                print(block, file=sys.stderr)
        failures += doc_failures
        status = "ok  " if not doc_failures else "FAIL"
        print(f"{status} {doc.name}: {len(blocks)} blocks")
    print(f"\n{failures} failing block(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
