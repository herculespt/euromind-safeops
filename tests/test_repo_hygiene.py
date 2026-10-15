"""Repository quality contracts, run offline in the CI matrix."""

from __future__ import annotations

import re
import tomllib
import unittest
from pathlib import Path

from euromind_safeops import __version__

ROOT = Path(__file__).resolve().parents[1]


class RepositoryHygieneTests(unittest.TestCase):
    def test_distribution_version_matches_python_package(self):
        package = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(package["project"]["version"], __version__)

    def test_required_community_and_maintainer_documents(self):
        for name in (
            "README.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md",
            "GOVERNANCE.md", "CODE_OF_CONDUCT.md", "CHANGELOG.md", "ROADMAP.md",
            "docs/ARCHITECTURE.md", "docs/PROVIDERS.md", "docs/MAINTAINER_GUIDE.md",
            "docs/RELEASING.md", "docs/pt-PT/README.md",
            ".github/workflows/ci.yml", ".github/CODEOWNERS",
        ):
            with self.subTest(path=name):
                self.assertTrue((ROOT / name).is_file(), name)

    def test_relative_document_links_and_utf8(self):
        local_links = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for document in ROOT.rglob("*.md"):
            if any(x in (".safeops", ".venv", ".git", "build", "dist") for x in document.parts):
                continue
            contents = document.read_text(encoding="utf-8", errors="strict")
            with self.subTest(document=document.relative_to(ROOT).as_posix()):
                self.assertNotIn("\ufffd", contents, "Unicode replacement character found")
            for target in local_links.findall(contents):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                link = target.split("#", 1)[0]
                if link:
                    with self.subTest(document=document.relative_to(ROOT).as_posix(), link=link):
                        self.assertTrue((document.parent / link).exists(), f"Broken relative Markdown link: {target}")


if __name__ == "__main__":
    unittest.main()
