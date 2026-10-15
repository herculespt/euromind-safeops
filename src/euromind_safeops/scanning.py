"""Best-effort content checks for common credential patterns (not a guarantee)."""

from __future__ import annotations

import re
from pathlib import Path

from .core import source_files

PATTERNS = {
    "private-key-header": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github-classic-token": re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    "github-fine-grained-token": re.compile(r"github_pat_[A-Za-z0-9_]{30,}"),
    "aws-access-key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "generic-secret-assignment": re.compile(r"(?:api[_-]?key|secret[_-]?key|password)\s*[:=]\s*['\"][^'\"]{12,}['\"]", re.IGNORECASE),
}


def scan(root: Path) -> list[dict]:
    findings = []
    for path in source_files(root):
        if path.stat().st_size > 750_000:
            continue
        data = path.read_bytes()
        if b"\x00" in data[:8192]:
            continue
        try:
            content = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(content.splitlines(), 1):
            for label, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append({"file": path.relative_to(root).as_posix(), "line": i, "rule": label})
    return findings
