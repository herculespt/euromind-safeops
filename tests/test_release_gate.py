"""Exercise the release scanner CLI policy without a runtime scanner dependency."""

import contextlib
import io
import json
import runpy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
gate = runpy.run_path(str(ROOT / "scripts/release_secrets.py"))["main"]


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.policy = self.root / "policy.json"
        self.hit = {"type": "Secret Keyword", "line_number": 1,
                    "hashed_secret": "a" * 40, "is_secret": False}
        self.baseline = {"schema": 1, "results": {"tests/test_fixture.py": [self.hit]}}

    def invoke(self, results, *, tracked=False):
        self.policy.write_text(json.dumps(self.baseline), encoding="utf-8")
        args = ["release_secrets.py", "--root", str(self.root), "--baseline", str(self.policy)]
        if tracked:
            args.append("--tracked")
        with patch("sys.argv", args), patch("subprocess.run", return_value=SimpleNamespace(
                stdout=json.dumps({"results": results}))) as scanner, contextlib.redirect_stdout(io.StringIO()) as output:
            code = gate()
            return code, output.getvalue(), scanner.call_args

    def test_reviewed_hash_passes_without_network_verification(self):
        code, output, call = self.invoke({"tests/test_fixture.py": [self.hit]}, tracked=True)
        self.assertEqual(code, 0)
        self.assertIn("1 reviewed synthetic findings; 0 unreviewed", output)
        command = call.args[0]
        self.assertIn("--no-verify", command)
        self.assertNotIn("--all-files", command)
        self.assertEqual(command[-1], r"(^|/)\.secrets\.baseline$")

    def test_changed_hash_is_rejected(self):
        changed = {**self.hit, "hashed_secret": "b" * 40}
        code, output, _ = self.invoke({"tests/test_fixture.py": [changed]})
        self.assertEqual(code, 1)
        self.assertIn("Unreviewed scanner finding: tests/test_fixture.py:1", output)
        self.assertNotIn("b" * 40, output)

    def test_same_hash_in_a_different_file_is_rejected(self):
        code, _, _ = self.invoke({"tests/test_other.py": [self.hit]})
        self.assertEqual(code, 1)

    def test_same_hash_with_a_different_detector_is_rejected(self):
        code, _, _ = self.invoke({"tests/test_fixture.py": [{**self.hit, "type": "Other Detector"}]})
        self.assertEqual(code, 1)

    def test_unreviewed_baseline_identity_is_invalid(self):
        self.hit["is_secret"] = True
        with self.assertRaisesRegex(ValueError, "Invalid reviewed-fixture identity"):
            self.invoke({})

    def test_boolean_schema_is_invalid(self):
        self.baseline["schema"] = True
        with self.assertRaisesRegex(ValueError, "Invalid reviewed-fixture baseline structure"):
            self.invoke({})

    def test_extra_baseline_field_is_invalid(self):
        self.baseline["extra"] = "synthetic metadata"
        with self.assertRaisesRegex(ValueError, "Invalid reviewed-fixture baseline structure"):
            self.invoke({})

    def test_packaged_baseline_must_match_reviewed_bytes(self):
        (self.root / ".secrets.baseline").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Packaged fixture baseline differs"):
            self.invoke({})

    def test_standalone_archive_scan_needs_no_git_metadata(self):
        code, _, call = self.invoke({})
        self.assertEqual(code, 0)
        self.assertIn("--all-files", call.args[0])
        self.assertEqual(call.kwargs["cwd"], self.root.resolve())
