"""Scope preflight must precede remote advice and approval/execution boundaries."""

from __future__ import annotations

import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from euromind_safeops.cli import main
from euromind_safeops.core import SafeOpsError, sha256, tree_digest
from euromind_safeops.execution import approve, run
from euromind_safeops.planning import create_plan, load_plan
from euromind_safeops.scope import validate_scope_paths


class ScopeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root = self.base / "workspace"
        self.root.mkdir()
        self.outside = self.base / "outside"
        self.outside.mkdir()
        (self.outside / "private.py").write_text("answer = 42\n", encoding="utf-8")
        (self.root / "src").mkdir()
        (self.root / "src/main.py").write_text("answer = 42\n", encoding="utf-8")
        (self.root / "tests").mkdir()
        (self.root / "tests/test_example.py").write_text(
            "import unittest\nclass Example(unittest.TestCase):\n"
            " def test_example(self): self.assertEqual(6 * 7, 42)\n", encoding="utf-8")
        self.assertEqual(self.cli("init")[0], 0)

    def cli(self, *args):
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            code = main(["--root", str(self.root), *args])
        return code, output.getvalue()

    def plan(self, paths):
        return create_plan(self.root, "Review documentation", paths, "Fixture advice", "offline")

    def link(self, location, target, directory=False):
        try:
            location.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links are unavailable for this account")

    def test_invalid_scope_never_contacts_provider_or_saves_plan(self):
        invalid = ["../outside", "src/../tests", "/outside", "C:/outside", "C:relative",
                   "//server/share", "src\\main.py", "", ".safeops/config.json",
                   "./.safeops/config.json", "docs/.git/config", "dist/generated.py",
                   "src/main.py:stream", "NUL.txt", "COM¹.log", "src/name.", "src/name ",
                   "src/*.py", "src/bad\x00name", "src/bad\nname", "src/\ud800.py", "src/main.py/child"]
        for name in invalid:
            with self.subTest(path=name), patch("euromind_safeops.cli.remote_advice") as provider:
                code, _ = self.cli("plan", "Review documentation", "--path", name,
                                   "--provider", "anthropic", "--model", "fixture", "--allow-remote")
                self.assertEqual(code, 2)
                provider.assert_not_called()
                self.assertEqual(list((self.root / ".safeops/plans").glob("*.json")), [])

    def test_valid_scope_keeps_one_provider_call_and_normalized_plan(self):
        with patch("euromind_safeops.cli.remote_advice", return_value="Fixture advice") as provider:
            code, output = self.cli("plan", "Review documentation", "--path", "./src//main.py",
                                    "--path", "docs/new.md", "--provider", "anthropic",
                                    "--model", "fixture", "--allow-remote")
        self.assertEqual(code, 0)
        provider.assert_called_once()
        plan = json.loads(output)
        self.assertEqual(plan["paths"], ["src/main.py", "docs/new.md"])
        self.assertEqual(load_plan(self.root, plan["id"]), plan)

    def test_invalid_offline_scope_also_saves_nothing(self):
        self.assertEqual(self.cli("plan", "Review documentation", "--path", "../outside")[0], 2)
        self.assertEqual(list((self.root / ".safeops/plans").glob("*.json")), [])

    def test_scope_shape_and_count_are_controlled(self):
        for paths in (None, "src", {}, [None], [42], ["src"] * 21):
            with self.subTest(paths=paths), self.assertRaises(SafeOpsError):
                self.plan(paths)

    def test_duplicate_canonical_paths_are_rejected_before_provider(self):
        with patch("euromind_safeops.cli.remote_advice") as provider:
            code, _ = self.cli("plan", "Review documentation", "--path", "src/main.py",
                               "--path", "./src//main.py", "--provider", "anthropic",
                               "--model", "fixture", "--allow-remote")
        self.assertEqual(code, 2)
        provider.assert_not_called()

    def test_empty_scope_and_explicit_root_remain_advisory(self):
        self.assertEqual(validate_scope_paths(self.root, []), [])
        self.assertEqual(validate_scope_paths(self.root, ["."]), ["."])

    def test_future_paths_and_portuguese_names_are_preserved(self):
        paths = ["documentação/revisão.md", "src/novo.py"]
        self.assertEqual(self.plan(paths)["paths"], paths)
        self.assertFalse((self.root / "documentação").exists())

    def test_internal_component_case_alias_is_rejected(self):
        for name in (".SAFEOPS/config.json", "docs/.GiT/config", "Build/new.py"):
            with self.subTest(path=name), self.assertRaises(SafeOpsError):
                self.plan([name])

    def test_regular_noninternal_prefix_is_not_mistaken_for_state(self):
        self.assertEqual(self.plan([".safeops-guide.md"])["paths"], [".safeops-guide.md"])

    def test_existing_symlink_is_rejected_before_provider(self):
        self.link(self.root / "alias", self.outside, directory=True)
        with patch("euromind_safeops.cli.remote_advice") as provider:
            code, _ = self.cli("plan", "Review documentation", "--path", "alias/private.py",
                               "--provider", "anthropic", "--model", "fixture", "--allow-remote")
        self.assertEqual(code, 2)
        provider.assert_not_called()

    def test_broken_symlink_is_rejected(self):
        self.link(self.root / "future.py", self.outside / "missing.py")
        with self.assertRaisesRegex(SafeOpsError, "links or reparse"):
            self.plan(["future.py"])

    def test_scope_is_checked_again_after_provider_returns(self):
        def changed_scope(*args, **kwargs):
            self.link(self.root / "future.py", self.outside / "private.py")
            return "Fixture advice"
        with patch("euromind_safeops.cli.remote_advice", side_effect=changed_scope) as provider:
            code, _ = self.cli("plan", "Review documentation", "--path", "future.py",
                               "--provider", "anthropic", "--model", "fixture", "--allow-remote")
        self.assertEqual(code, 2)
        provider.assert_called_once()
        self.assertEqual(list((self.root / ".safeops/plans").glob("*.json")), [])

    def test_approval_rechecks_link_added_without_digest_change(self):
        plan = self.plan(["future.py"])
        self.link(self.root / "future.py", self.outside / "private.py")
        self.assertEqual(tree_digest(self.root), plan["workspace_digest"])
        self.assertEqual(load_plan(self.root, plan["id"]), plan)
        with self.assertRaisesRegex(SafeOpsError, "links or reparse"):
            approve(self.root, plan["id"], "Reviewed", plan["id"])
        self.assertEqual(list((self.root / ".safeops/approvals").glob("*.json")), [])

    def test_run_rechecks_link_before_any_subprocess(self):
        plan = self.plan(["future.py"])
        approve(self.root, plan["id"], "Reviewed", plan["id"])
        self.link(self.root / "future.py", self.outside / "private.py")
        self.assertEqual(tree_digest(self.root), plan["workspace_digest"])
        with patch("euromind_safeops.execution.run_check") as process:
            with self.assertRaisesRegex(SafeOpsError, "links or reparse"):
                run(self.root, plan["id"])
        process.assert_not_called()
        self.assertFalse((self.root / ".safeops/run.lock").exists())

    def test_old_unsafe_scope_remains_reviewable_but_cannot_be_approved(self):
        plan = self.plan([])
        plan["paths"] = ["../outside"]
        plan["fingerprint"] = sha256({k: v for k, v in plan.items() if k != "fingerprint"})
        path = self.root / ".safeops/plans" / (plan["id"] + ".json")
        path.write_text(json.dumps(plan), encoding="utf-8")
        self.assertEqual(load_plan(self.root, plan["id"]), plan)
        with self.assertRaises(SafeOpsError):
            approve(self.root, plan["id"], "Reviewed", plan["id"])

    def test_scope_inspection_error_never_reaches_provider(self):
        original = Path.lstat
        def inspect(path, *args, **kwargs):
            if path == self.root / "src/main.py":
                raise PermissionError
            return original(path, *args, **kwargs)
        with patch("euromind_safeops.scope.Path.lstat", autospec=True, side_effect=inspect), \
                patch("euromind_safeops.cli.remote_advice") as provider:
            code, _ = self.cli("plan", "Review documentation", "--path", "src/main.py",
                               "--provider", "anthropic", "--model", "fixture", "--allow-remote")
        self.assertEqual(code, 2)
        provider.assert_not_called()

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX named-pipe behavior")
    def test_nonregular_scope_never_reaches_provider(self):
        os.mkfifo(self.root / "pipe")
        with patch("euromind_safeops.cli.remote_advice") as provider:
            code, _ = self.cli("plan", "Review documentation", "--path", "pipe",
                               "--provider", "anthropic", "--model", "fixture", "--allow-remote")
        self.assertEqual(code, 2)
        provider.assert_not_called()

    def test_scope_does_not_narrow_whole_workspace_snapshot(self):
        plan = self.plan(["docs/new.md"])
        approve(self.root, plan["id"], "Reviewed", plan["id"])
        (self.root / "src/main.py").write_text("answer = 7\n", encoding="utf-8")
        with self.assertRaisesRegex(SafeOpsError, "Workspace changed"):
            run(self.root, plan["id"])

    def test_scope_does_not_narrow_fixed_check_targets(self):
        plan = self.plan(["docs/new.md"])
        approve(self.root, plan["id"], "Reviewed", plan["id"])
        result = run(self.root, plan["id"])
        self.assertEqual(result["status"], "passed")
        self.assertEqual([r["check"] for r in result["checks"]], ["compile", "unit-tests"])

    @unittest.skipUnless(os.name == "nt", "Windows junction behavior")
    def test_windows_junction_is_rejected(self):
        link = self.root / "junction"
        result = subprocess.run(["cmd", "/d", "/c", "mklink", "/J", str(link), str(self.outside)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        try:
            with self.assertRaisesRegex(SafeOpsError, "links or reparse"):
                self.plan(["junction/private.py"])
        finally:
            link.rmdir()


if __name__ == "__main__":
    unittest.main()
