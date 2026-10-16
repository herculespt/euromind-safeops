"""Repository quality contracts, run offline in the CI matrix."""

from __future__ import annotations

import re
import importlib.metadata
import tomllib
import unittest
from pathlib import Path

from euromind_safeops import __version__
from euromind_safeops.cli import make_parser

ROOT = Path(__file__).resolve().parents[1]


class RepositoryHygieneTests(unittest.TestCase):
    def test_distribution_version_matches_python_package(self):
        package = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(package["project"]["version"], __version__)

    def test_installed_metadata_and_cli_help_match_source_version(self):
        self.assertEqual(importlib.metadata.version("euromind-safeops"), __version__)
        self.assertIn(__version__, make_parser().format_help())

    def test_current_versioned_documents_match_source_version(self):
        for name in (
            "README.md", "SECURITY.md", "docs/ARCHITECTURE.md", "docs/PROVIDERS.md",
            "docs/PROJECT_SCOPE.md", "docs/QUICKSTART.md", "docs/STATUS.md", "docs/EXECUTION.md",
            "docs/pt-PT/README.md", "docs/pt-PT/SECURITY.md", "docs/pt-PT/STATUS.md", "docs/pt-PT/EXECUTION.md",
            "docs/PROVIDER_TESTING.md", "docs/pt-PT/PROVIDER_TESTING.md", "docs/pt-PT/PROVIDERS.md",
            "docs/pt-PT/PROJECT_SCOPE.md",
            "docs/SCOPE.md", "docs/pt-PT/SCOPE.md",
            "docs/TARGETS.md", "docs/pt-PT/TARGETS.md",
            "docs/OUTPUT.md", "docs/pt-PT/OUTPUT.md",
            "docs/LOCKING.md", "docs/pt-PT/LOCKING.md",
            "docs/REPORTING.md", "docs/pt-PT/REPORTING.md",
            "docs/COVERAGE.md", "docs/pt-PT/COVERAGE.md",
            "docs/PREVIEW.md", "docs/pt-PT/PREVIEW.md",
            "docs/PROPOSALS.md", "docs/pt-PT/PROPOSALS.md",
            "docs/STAGING.md", "docs/pt-PT/STAGING.md",
            "docs/STAGE_REVIEW.md", "docs/pt-PT/STAGE_REVIEW.md",
            "docs/RUN_RECEIPTS.md", "docs/pt-PT/RUN_RECEIPTS.md",
            "docs/PACKAGE.md", "docs/RELEASING.md", "docs/pt-PT/RELEASING.md",
        ):
            with self.subTest(path=name):
                text = (ROOT / name).read_text(encoding="utf-8")
                marker = re.search(r"^<!-- safeops-version: ([^ ]+) -->$", text, re.MULTILINE)
                self.assertIsNotNone(marker, "Missing current-version marker")
                self.assertEqual(marker.group(1), __version__)
                visible = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
                first_version = re.search(r"\b\d+\.\d+\.\d+(?:a\d+)?\b", visible)
                self.assertIsNotNone(first_version, "Missing visible current source version")
                self.assertEqual(first_version.group(0), __version__)
                if name == "README.md":
                    self.assertIn(f"| Capability | {__version__} |", text)
                for sample_version in re.findall(r'"safeops_version":\s*"([^"]+)"', text):
                    self.assertEqual(sample_version, __version__, "Stale JSON example version")

    def test_roadmap_and_latest_changelog_match_source_version(self):
        for name in ("ROADMAP.md", "CHANGELOG.md"):
            with self.subTest(path=name):
                first_version = re.search(r"\b\d+\.\d+\.\d+(?:a\d+)?\b", (ROOT / name).read_text(encoding="utf-8"))
                self.assertIsNotNone(first_version)
                self.assertEqual(first_version.group(0), __version__)

    def test_required_community_and_maintainer_documents(self):
        for name in (
            "README.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md",
            "GOVERNANCE.md", "CODE_OF_CONDUCT.md", "CHANGELOG.md", "ROADMAP.md",
            "docs/ARCHITECTURE.md", "docs/PROVIDERS.md", "docs/MAINTAINER_GUIDE.md",
            "docs/RELEASING.md", "docs/pt-PT/README.md",
            "docs/STATUS.md", "docs/EXECUTION.md", "docs/pt-PT/STATUS.md", "docs/pt-PT/EXECUTION.md",
            "docs/adr/0002-versioned-check-contract.md", "docs/pt-PT/adr/0002-versioned-check-contract.md",
            "docs/PROVIDER_TESTING.md", "docs/pt-PT/PROVIDER_TESTING.md", "docs/pt-PT/PROVIDERS.md",
            "docs/pt-PT/PROJECT_SCOPE.md",
            "docs/SCOPE.md", "docs/pt-PT/SCOPE.md",
            "docs/TARGETS.md", "docs/pt-PT/TARGETS.md",
            "docs/OUTPUT.md", "docs/pt-PT/OUTPUT.md",
            "docs/LOCKING.md", "docs/pt-PT/LOCKING.md",
            "src/euromind_safeops/scope.py", "tests/test_scope.py",
            "src/euromind_safeops/target_runner.py", "tests/test_targets.py",
            "src/euromind_safeops/ci_runner.py", "tests/test_json_output.py", "tests/test_ci_reporting.py",
            "src/euromind_safeops/locking.py", "tests/test_locking.py",
            "src/euromind_safeops/junit.py", "docs/REPORTING.md", "docs/pt-PT/REPORTING.md",
            "docs/COVERAGE.md", "docs/pt-PT/COVERAGE.md",
            "docs/PREVIEW.md", "docs/pt-PT/PREVIEW.md",
            "docs/PROPOSALS.md", "docs/pt-PT/PROPOSALS.md",
            "docs/STAGING.md", "docs/pt-PT/STAGING.md",
            "docs/STAGE_REVIEW.md", "docs/pt-PT/STAGE_REVIEW.md",
            "docs/RUN_RECEIPTS.md", "docs/pt-PT/RUN_RECEIPTS.md",
            "src/euromind_safeops/proposals.py", "tests/test_proposals.py",
            "src/euromind_safeops/staging.py", "tests/test_staging.py",
            "src/euromind_safeops/stage_inspection.py", "tests/test_stage_inspection.py",
            "src/euromind_safeops/stage_review.py", "tests/test_stage_review.py",
            "src/euromind_safeops/run_receipts.py", "tests/test_run_receipts.py",
            "requirements-ci.txt", ".github/workflows/ci.yml", ".github/CODEOWNERS",
            "requirements-release.txt", ".github/workflows/publish.yml", ".secrets.baseline", "scripts/release_secrets.py", "tests/test_release_gate.py",
        ):
            with self.subTest(path=name):
                self.assertTrue((ROOT / name).is_file(), name)

    def test_registry_readme_matches_installed_metadata_and_uses_absolute_links(self):
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        contents = (ROOT / project["readme"]).read_text(encoding="utf-8")
        metadata = importlib.metadata.metadata("euromind-safeops")
        self.assertEqual(metadata["Description-Content-Type"], "text/markdown")
        self.assertEqual(metadata["Description"].strip(), contents.strip())
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", contents)
        self.assertTrue(links)
        self.assertTrue(all(link.startswith("https://") for link in links), "Registry links need absolute URLs")

    def test_relative_document_links_and_utf8(self):
        local_links = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for document in ROOT.rglob("*.md"):
            if any(x in (".safeops", ".venv", ".git", "build", "dist") for x in document.relative_to(ROOT).parts):
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
