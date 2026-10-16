"""Maintainer-only scanner gate; allow only reviewed path/type/hash triples."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path, PurePosixPath


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--tracked", action="store_true")
    args = parser.parse_args()
    raw = args.baseline.resolve().read_bytes()
    baseline = json.loads(raw.decode("utf-8"))
    if (set(baseline) != {"schema", "results"}
            or type(baseline["schema"]) is not int or baseline["schema"] != 1):
        raise ValueError("Invalid reviewed-fixture baseline structure")
    for name, hits in baseline["results"].items():
        if not re.fullmatch(r"tests/test_[A-Za-z0-9_]+\.py", name) or not isinstance(hits, list):
            raise ValueError("Invalid reviewed-fixture path")
        for hit in hits:
            if (set(hit) != {"type", "line_number", "hashed_secret", "is_secret"}
                    or hit["type"] not in {"Secret Keyword", "Basic Auth Credentials"}
                    or type(hit["line_number"]) is not int or hit["line_number"] < 1
                    or not re.fullmatch(r"[0-9a-f]{40}", hit["hashed_secret"])
                    or hit["is_secret"] is not False):
                raise ValueError("Invalid reviewed-fixture identity")
    packaged = args.root.resolve() / ".secrets.baseline"
    if packaged.exists() and packaged.read_bytes() != raw:
        raise ValueError("Packaged fixture baseline differs from reviewed source")
    allowed = {(PurePosixPath(name).as_posix(), hit["type"], hit["hashed_secret"])
               for name, hits in baseline["results"].items() for hit in hits
               if hit.get("is_secret") is False}
    # The control file contains only validated hashes/metadata. Do not scan its
    # hashes as if they were credential literals; no test source is excluded.
    command = ["detect-secrets", "scan", "--no-verify",
               "--exclude-files", r"(^|/)\.secrets\.baseline$"]
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
