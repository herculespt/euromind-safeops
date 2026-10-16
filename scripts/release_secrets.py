"""Maintainer-only scanner gate; allow only reviewed path/type/hash triples."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path, PurePosixPath


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--tracked", action="store_true")
    args = parser.parse_args()
    baseline = json.loads(args.baseline.resolve().read_text(encoding="utf-8"))
    allowed = {(PurePosixPath(name).as_posix(), hit["type"], hit["hashed_secret"])
               for name, hits in baseline["results"].items() for hit in hits
               if hit.get("is_secret") is False}
    command = ["detect-secrets", "scan", "--no-verify"]
    if not args.tracked:
        command.extend(["--all-files", "."])
    result = subprocess.run(command, cwd=args.root.resolve(), capture_output=True,
                            text=True, encoding="utf-8", check=True)
    data = json.loads(result.stdout)
    unexpected = []
    reviewed = 0
    for name, hits in data["results"].items():
        for hit in hits:
            identity = (PurePosixPath(name).as_posix(), hit["type"], hit["hashed_secret"])
            if identity in allowed:
                reviewed += 1
            else:
                unexpected.append((name, hit["line_number"], hit["type"]))
    for name, line, kind in unexpected:
        print(f"Unreviewed scanner finding: {name}:{line} ({kind})")
    print(f"Independent scan: {reviewed} reviewed synthetic findings; {len(unexpected)} unreviewed findings")
    return 1 if unexpected else 0


if __name__ == "__main__":
    raise SystemExit(main())
