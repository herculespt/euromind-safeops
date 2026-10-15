"""Real approved subprocess tests for opt-in directory targets; no API access."""

import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from euromind_safeops.cli import main
from euromind_safeops.core import SafeOpsError
from euromind_safeops.execution import approve, get_config, run
from euromind_safeops.planning import create_plan


class TargetTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--root", str(self.root), "init"]), 0)
        for name in ("selected", "checks", "outside"):
            (self.root / name).mkdir()
        (self.root / "selected" / "valid.py").write_text("value = 1\n", encoding="utf-8")
        self.test_source = self.root / "checks" / "test_selected.py"
        self.test_source.write_text(
            "import unittest\nclass T(unittest.TestCase):\n def test_selected(self): pass\n", encoding="utf-8")
        # Both would fail if selected by the adapters.
        (self.root / "outside" / "bad.py").write_text("this is invalid syntax ???\n", encoding="utf-8")
        (self.root / "outside" / "test_outside.py").write_text(
            "raise RuntimeError('outside discovery must not run')\n", encoding="utf-8")
        self.config = {"schema": 2, "checks": ["compile", "unit-tests"],
                       "targets": {"compile": ["selected"], "unit-tests": ["checks"]}}
        self.write_config()

    def write_config(self, config=None):
        (self.root / ".safeops" / "config.json").write_text(
            json.dumps(self.config if config is None else config), encoding="utf-8")

    def plan(self):
        return create_plan(self.root, "Review documentation", [], "offline", "offline")

    def approved(self):
        plan = self.plan()
        approve(self.root, plan["id"], "Reviewed directory targets", plan["id"])
        return plan["id"]

    def test_selected_checks_ignore_outside_sources_and_tests(self):
        result = run(self.root, self.approved())
        self.assertEqual(result["status"], "passed")
        self.assertIn("compiled 1 selected", result["checks"][0]["stdout"])
        self.assertIn("test_selected", result["checks"][1]["stderr"])
        self.assertFalse((self.root / "selected" / "__pycache__").exists())

    def test_doctor_reports_configured_targets_and_selected_test_count(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["--root", str(self.root), "doctor"]), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["config_schema"], 2)
        self.assertEqual(report["targets"], self.config["targets"])
        self.assertEqual(report["test_files"], 1)

    def test_invalid_config_shapes_and_roots(self):
        invalid_targets = [None, [], {}, {"compile": ["selected"]},
                           {"compile": ["selected"], "unit-tests": ["checks"], "extra": []}]
        for targets in invalid_targets:
            with self.subTest(targets=targets):
                self.write_config({**self.config, "targets": targets})
                with self.assertRaises(SafeOpsError):
                    get_config(self.root)
        for paths in (None, "selected", [], [None], [True], ["."], ["../outside"],
                      ["/absolute"], ["selected\\nested"], [".safeops"], ["missing"],
                      ["./selected"], ["selected/"], ["selected/valid.py"], ["selected"] * 21,
                      ["selected", "SELECTED"], ["selected", "selected/nested"]):
            with self.subTest(paths=paths):
                self.write_config({**self.config, "targets": {"compile": paths, "unit-tests": ["checks"]}})
                with self.assertRaises(SafeOpsError):
                    get_config(self.root)

    def test_multiple_test_roots_are_rejected(self):
        self.config["targets"]["unit-tests"] = ["checks", "selected"]
        self.write_config()
        with self.assertRaises(SafeOpsError):
            get_config(self.root)

    def test_multiple_nonoverlapping_compile_roots(self):
        extra = self.root / "extra"
        extra.mkdir()
        (extra / "other.py").write_text("value = 2\n", encoding="utf-8")
        self.config["targets"]["compile"].append("extra")
        self.write_config()
        result = run(self.root, self.approved())
        self.assertEqual(result["status"], "passed")
        self.assertIn("compiled 2 selected", result["checks"][0]["stdout"])

    def test_single_check_configurations_need_no_default_directories(self):
        for check in ("compile", "unit-tests"):
            with self.subTest(check=check):
                self.write_config({"schema": 2, "checks": [check],
                                   "targets": {check: self.config["targets"][check]}})
                result = run(self.root, self.approved())
                self.assertEqual(result["status"], "passed")
                self.assertEqual([entry["check"] for entry in result["checks"]], [check])

    def test_shared_root_with_nested_test_package(self):
        nested = self.root / "checks" / "nested"
        nested.mkdir()
        (nested / "__init__.py").write_text("", encoding="utf-8")
        self.test_source.rename(nested / "test_selected.py")
        self.config["targets"]["compile"] = ["checks"]
        self.write_config()
        result = run(self.root, self.approved())
        self.assertEqual(result["status"], "passed")
        self.assertIn("nested.test_selected", result["checks"][-1]["stderr"])

    def test_generated_test_cache_requires_fresh_approval(self):
        plan_id = self.approved()
        self.assertEqual(run(self.root, plan_id)["status"], "passed")
        # Test imports normally write bytecode. This is intentionally fingerprinted.
        cache = self.root / "checks" / "__pycache__"
        cache.mkdir(exist_ok=True)
        (cache / "extra.bin").write_bytes(b"generated")
        with self.assertRaisesRegex(SafeOpsError, "Selected targets changed"):
            run(self.root, plan_id)

    def test_empty_compile_selection_blocks_approval(self):
        (self.root / "selected" / "valid.py").unlink()
        plan = self.plan()
        with self.assertRaisesRegex(SafeOpsError, "No Python sources"):
            approve(self.root, plan["id"], "reviewed", plan["id"])

    def test_empty_tests_fail_in_child(self):
        self.test_source.unlink()
        result = run(self.root, self.approved())
        self.assertEqual(result["status"], "failed")
        self.assertIn("No tests discovered", result["checks"][-1]["stderr"])

    def test_all_skipped_tests_fail_in_child(self):
        self.test_source.write_text(
            "import unittest\n@unittest.skip('fixture')\nclass T(unittest.TestCase):\n def test_it(self): pass\n",
            encoding="utf-8")
        self.assertEqual(run(self.root, self.approved())["status"], "failed")

    def test_syntax_error_fails_without_test_execution(self):
        (self.root / "selected" / "valid.py").write_text("invalid ???\n", encoding="utf-8")
        result = run(self.root, self.approved())
        self.assertEqual(result["status"], "failed")
        self.assertEqual(len(result["checks"]), 1)
        self.assertIn("SyntaxError", result["checks"][0]["stderr"])

    def test_approval_does_not_import_tests(self):
        marker = self.root / "imported.flag"
        self.test_source.write_text(
            "from pathlib import Path\nPath('imported.flag').touch()\nimport unittest\n"
            "class T(unittest.TestCase):\n def test_it(self): pass\n", encoding="utf-8")
        plan_id = self.approved()
        self.assertFalse(marker.exists())
        self.assertEqual(run(self.root, plan_id)["status"], "passed")
        self.assertTrue(marker.exists())

    def test_outside_change_still_invalidates_approval(self):
        plan_id = self.approved()
        (self.root / "outside" / "bad.py").write_text("changed = True\n", encoding="utf-8")
        with patch("euromind_safeops.execution.subprocess.run") as child:
            with self.assertRaisesRegex(SafeOpsError, "Workspace changed"):
                run(self.root, plan_id)
            child.assert_not_called()

    def test_target_config_change_invalidates_approval(self):
        plan_id = self.approved()
        self.config["targets"]["compile"] = ["checks"]
        self.write_config()
        with patch("euromind_safeops.execution.subprocess.run") as child:
            with self.assertRaisesRegex(SafeOpsError, "stale approval"):
                run(self.root, plan_id)
            child.assert_not_called()

    def symlink(self, destination, target, directory=False):
        try:
            destination.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic link creation unavailable")

    def test_descendant_link_blocks_approval(self):
        self.symlink(self.root / "selected" / "link", self.root / "outside", True)
        plan = self.plan()
        with self.assertRaises(SafeOpsError):
            approve(self.root, plan["id"], "reviewed", plan["id"])

    def test_broken_link_blocks_run_before_child(self):
        plan_id = self.approved()
        self.symlink(self.root / "checks" / "broken", self.root / "missing")
        with patch("euromind_safeops.execution.subprocess.run") as child:
            with self.assertRaises(SafeOpsError):
                run(self.root, plan_id)
            child.assert_not_called()
        self.assertFalse((self.root / ".safeops" / "run.lock").exists())

    def test_child_rechecks_link_after_parent_preflight(self):
        self.symlink(self.root / "selected" / "link", self.root / "outside", True)
        result = subprocess.run([sys.executable, "-m", "euromind_safeops.target_runner", "compile", "selected"],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("links or reparse", result.stderr)

    def test_inspection_error_is_controlled(self):
        with patch("euromind_safeops.target_runner.os.scandir", side_effect=PermissionError):
            with self.assertRaisesRegex(SafeOpsError, "Cannot inspect"):
                get_config(self.root)

    def test_metadata_limit_is_enforced(self):
        with patch("euromind_safeops.target_runner.MAX_ENTRIES", 0):
            with self.assertRaisesRegex(SafeOpsError, "metadata limit"):
                get_config(self.root)

    def test_source_size_limit_is_enforced(self):
        with patch("euromind_safeops.target_runner.MAX_SOURCE_BYTES", 1):
            with self.assertRaisesRegex(SafeOpsError, "file exceeds"):
                get_config(self.root)

    def test_changed_generated_file_invalidates_selected_digest(self):
        generated = self.root / "selected" / "build"
        generated.mkdir()
        resource = generated / "resource.txt"
        resource.write_text("reviewed", encoding="utf-8")
        plan_id = self.approved()
        resource.write_text("changed", encoding="utf-8")
        with patch("euromind_safeops.execution.subprocess.run") as child:
            with self.assertRaisesRegex(SafeOpsError, "Selected targets changed"):
                run(self.root, plan_id)
            child.assert_not_called()

    def test_missing_selected_digest_cannot_authorize(self):
        plan_id = self.approved()
        path = self.root / ".safeops" / "approvals" / (plan_id + ".json")
        record = json.loads(path.read_text(encoding="utf-8"))
        record.pop("targets_digest")
        path.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(SafeOpsError, "Selected targets changed"):
            run(self.root, plan_id)

    def test_generated_descendants_are_not_silently_pruned(self):
        generated = self.root / "selected" / "build"
        generated.mkdir()
        (generated / "bad.py").write_text("invalid ???\n", encoding="utf-8")
        self.assertEqual(run(self.root, self.approved())["status"], "failed")

    def test_unicode_and_nested_test_root(self):
        nested = self.root / "validação" / "casos"
        nested.mkdir(parents=True)
        self.test_source.rename(nested / "test_selected.py")
        self.config["targets"]["unit-tests"] = ["validação/casos"]
        self.write_config()
        self.assertEqual(run(self.root, self.approved())["status"], "passed")

    def test_unknown_child_check_fails_closed(self):
        result = subprocess.run([sys.executable, "-m", "euromind_safeops.target_runner", "shell", "selected"],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX named pipe")
    def test_descendant_pipe_is_rejected(self):
        os.mkfifo(self.root / "checks" / "pipe")
        with self.assertRaises(SafeOpsError):
            get_config(self.root)

    @unittest.skipUnless(os.name == "nt", "Windows junction")
    def test_descendant_junction_is_rejected(self):
        link = self.root / "selected" / "junction"
        result = subprocess.run(["cmd", "/d", "/c", "mklink", "/J", str(link), str(self.root / "outside")],
                                capture_output=True)
        self.assertEqual(result.returncode, 0)
        try:
            self.assertTrue(link.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
            with self.assertRaises(SafeOpsError):
                get_config(self.root)
        finally:
            link.rmdir()


if __name__ == "__main__":
    unittest.main()
