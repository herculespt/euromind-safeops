"""Real local Git worktrees, exact consent and unchanged authority gates."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from euromind_safeops import git_staging as git, staging
from euromind_safeops.cli import main
from euromind_safeops.core import SafeOpsError, json_bytes, sha256
from euromind_safeops.planning import create_plan
from euromind_safeops.proposals import create_proposal
from euromind_safeops.stage_inspection import inspect_stage
from euromind_safeops.stage_review import review_stage


@unittest.skipUnless(shutil.which("git"), "Native Git unavailable")
class GitStagingTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.base = Path(temp.name); self.root = self.base / "project"; self.root.mkdir()
        (self.root / "src").mkdir(); (self.root / "tests").mkdir()
        self.source = self.root / "src/main.py"; self.source.write_bytes('greeting = "Olá"\n'.encode())
        self.test = self.root / "tests/test_main.py"
        self.test.write_bytes(b"import unittest\nfrom pathlib import Path\nclass T(unittest.TestCase):\n def test_value(self): self.assertIn('greeting', Path('src/main.py').read_text(encoding='utf-8'))\n")
        (self.root / ".gitignore").write_bytes(b".safeops/\n__pycache__/\n.env*\n")
        (self.root / ".gitattributes").write_bytes(b"*.py filter=fixture\n")
        self.cmd("init", "--quiet")
        self.cmd("config", "core.autocrlf", "false")
        self.cmd("config", "user.name", "SafeOps fixture")
        self.cmd("config", "user.email", "fixture@example.invalid")
        self.cmd("add", "."); self.cmd("-c", "commit.gpgSign=false", "commit", "--quiet", "-m", "Public fixture")
        with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(main(["--root", str(self.root), "init"]), 0)
        self.prepare()

    def cmd(self, *args, root=None):
        return subprocess.check_output([shutil.which("git"), "-C", str(root or self.root), *args],
            env=git._environment(), stderr=subprocess.DEVNULL)

    def prepare(self):
        plan = create_plan(self.root, "Improve greeting docs", ["src/main.py"], "offline", "offline")
        candidate = self.base / "candidate.json"
        candidate.write_bytes(json_bytes({"schema": 1, "files": [{"path": "src/main.py",
            "base_sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(), "content": 'greeting = "Portugal"\n'}]}))
        self.proposal = create_proposal(self.root, plan["id"], candidate)

    def review(self): return git.review_git_stage(self.root, self.proposal["proposal_id"])

    def stage(self): return git.stage_git_proposal(self.root, self.proposal["proposal_id"], self.review()["fingerprint"])

    def test_review_is_stable_and_preserves_repository_and_state(self):
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        reviewed = self.review(); self.assertEqual(reviewed, self.review())
        after = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after); self.assertFalse((self.root / ".safeops/stages").exists())
        self.assertFalse(reviewed["policy"]["checkout"])

    def test_real_worktree_receipt_and_original_git_are_preserved(self):
        context = self.review()["git"]; result = self.stage(); copied = Path(result["workspace"])
        self.assertTrue((copied / ".git").is_file())
        self.assertEqual((copied / "src/main.py").read_bytes(), b'greeting = "Portugal"\n')
        self.assertEqual(self.source.read_bytes(), 'greeting = "Olá"\n'.encode())
        self.assertEqual(git._repository(self.root)[0], context)
        self.assertEqual(inspect_stage(self.root, result["stage_id"])["status"], "matching")
        self.assertEqual(review_stage(self.root, result["stage_id"])["status"], "current")
        receipt = json.loads((copied.parent / "receipt.json").read_bytes()); self.assertEqual(receipt["schema"], 2)
        self.assertEqual(list((self.root / ".safeops/approvals").iterdir()), [])
        self.assertIn(b"detached", self.cmd("worktree", "list", "--porcelain"))

    def test_copy_only_schema1_remains_provider_and_git_free(self):
        with patch.object(git, "_git", side_effect=AssertionError("Unexpected Git")):
            r = staging.stage_proposal(self.root, self.proposal["proposal_id"], self.proposal["fingerprint"])
            self.assertEqual(inspect_stage(self.root, r["stage_id"])["status"], "matching")
        self.assertFalse((Path(r["workspace"]) / ".git").exists())

    def test_proposal_fingerprint_does_not_authorize_git_mutation(self):
        with self.assertRaises(SafeOpsError): git.stage_git_proposal(self.root, self.proposal["proposal_id"], self.proposal["fingerprint"])
        self.assertFalse((self.root / ".git/worktrees").exists())

    def test_changed_configuration_or_index_invalidates_confirmation(self):
        confirm = self.review()["fingerprint"]
        self.cmd("config", "fixture.changed", "yes")
        with self.assertRaises(SafeOpsError): git.stage_git_proposal(self.root, self.proposal["proposal_id"], confirm)
        self.cmd("update-index", "--assume-unchanged", "src/main.py")
        with self.assertRaises(SafeOpsError): git.stage_git_proposal(self.root, self.proposal["proposal_id"], confirm)
        self.assertFalse((self.root / ".git/worktrees").exists())

    def test_dirty_literal_source_even_with_assume_unchanged_is_refused(self):
        self.cmd("update-index", "--assume-unchanged", "src/main.py")
        self.source.write_bytes(b"changed\n"); self.prepare()
        with self.assertRaises(SafeOpsError): self.review()

    def test_untracked_source_and_staged_index_changes_are_refused(self):
        extra = self.root / "untracked.txt"; extra.write_bytes(b"public fixture\n"); self.prepare()
        with self.assertRaises(SafeOpsError): self.review()
        extra.unlink(); self.source.write_bytes(b"greeting = 2\n"); self.cmd("add", "src/main.py"); self.prepare()
        with self.assertRaises(SafeOpsError): self.review()

    def test_unborn_and_non_git_projects_are_refused(self):
        with patch.object(git.shutil, "which", return_value=None), self.assertRaises(SafeOpsError): self.review()
        self.cmd("symbolic-ref", "HEAD", "refs/heads/unborn")
        with self.assertRaises(SafeOpsError): self.review()

    def test_hooks_filters_and_inherited_git_or_provider_environment_are_not_used(self):
        self.cmd("config", "filter.fixture.smudge", "false"); self.cmd("config", "filter.fixture.required", "true")
        hook = self.root / ".git/hooks/post-checkout"; hook.write_bytes(b"#!/bin/sh\nexit 77\n"); hook.chmod(0o700)
        with patch.dict(os.environ, {"GIT_DIR": str(self.base / "foreign"), "GIT_CONFIG_COUNT": "1",
                                   "GIT_CONFIG_KEY_0": "core.worktree", **dict.fromkeys(["OPENAI_API_KEY"], "fixture-value")}):
            self.assertNotIn("OPENAI_API_KEY", git._environment())
            result = self.stage()
        self.assertEqual(inspect_stage(self.root, result["stage_id"])["status"], "matching")

    def test_partial_git_failure_retains_locked_workspace_and_intent(self):
        original = git._git
        def failed(root, executable, *args):
            if args[0] == "read-tree": raise SafeOpsError("fixture")
            return original(root, executable, *args)
        with patch.object(git, "_git", side_effect=failed), self.assertRaisesRegex(SafeOpsError, "retained"):
            self.stage()
        owned = next((self.root / ".safeops/stages").iterdir())
        self.assertTrue((owned / "workspace/.git").is_file()); self.assertFalse((owned / "receipt.json").exists())
        self.assertEqual(inspect_stage(self.root, owned.name)["status"], "incomplete")
        self.assertIn(b"locked", self.cmd("worktree", "list", "--porcelain"))

    def test_foreign_pointer_is_rejected_before_git_execution(self):
        r = self.stage(); copied = Path(r["workspace"]); (copied / ".git").write_bytes(b"gitdir: /foreign/path\n")
        with patch.object(git, "_git") as command, self.assertRaises(SafeOpsError): inspect_stage(self.root, r["stage_id"])
        command.assert_not_called()

    def test_untrusted_record_cannot_choose_an_executable(self):
        r = self.stage(); owned = Path(r["workspace"]).parent
        for name in ("intent.json", "receipt.json"):
            p = owned / name; value = json.loads(p.read_bytes()); value["git"]["executable"] = sys.executable
            if "fingerprint" in value: value.pop("fingerprint"); value["fingerprint"] = sha256(value)
            p.write_bytes(json_bytes(value))
        with patch.object(git, "_git") as command, self.assertRaises(SafeOpsError): inspect_stage(self.root, r["stage_id"])
        command.assert_not_called()

    def test_worktree_index_or_branch_changes_are_rejected(self):
        r = self.stage(); copied = Path(r["workspace"])
        self.cmd("add", "src/main.py", root=copied)
        with self.assertRaises(SafeOpsError): inspect_stage(self.root, r["stage_id"])
        self.cmd("read-tree", "HEAD", root=copied)
        branch = self.cmd("symbolic-ref", "HEAD").decode().strip()
        self.cmd("symbolic-ref", "HEAD", branch, root=copied)
        with self.assertRaises(SafeOpsError): inspect_stage(self.root, r["stage_id"])

    def test_missing_lock_or_bad_backlink_is_rejected(self):
        r = self.stage(); copied = Path(r["workspace"])
        admin = Path((copied / ".git").read_text(encoding="utf-8")[8:].strip())
        locked = (admin / "locked").read_bytes(); (admin / "locked").unlink()
        with self.assertRaises(SafeOpsError): inspect_stage(self.root, r["stage_id"])
        (admin / "locked").write_bytes(locked); (admin / "gitdir").write_bytes(b"/foreign/path\n")
        with self.assertRaises(SafeOpsError): inspect_stage(self.root, r["stage_id"])

    def test_running_check_guard_blocks_git_stage_creation(self):
        from euromind_safeops.locking import execution_lock
        with execution_lock(self.root, "a" * 12), self.assertRaises(SafeOpsError): self.stage()
        self.assertFalse((self.root / ".git/worktrees").exists())

    def test_extended_config_and_unsafe_git_directory_are_refused(self):
        with (self.root / ".git/config").open("ab") as f: f.write(b"\n[include]\n path = missing\n")
        with self.assertRaises(SafeOpsError): self.review()

    def test_invalid_control_context_fields_are_refused(self):
        context = self.review()["git"]
        for value in (context | {"schema": True}, context | {"commit": "bad"}, context | {"extra": 1}, context | {"refs_sha256": "bad"}):
            with self.assertRaises((ValueError, TypeError)): git.validate_context(value, self.root)

    def test_malformed_or_unsupported_entries_are_refused(self):
        for raw in (b"", b"100644 blob " + b"a" * 40 + b"\t.env\0", b"160000 commit " + b"a" * 40 + b"\tsubmodule\0",
                    b"120000 blob " + b"a" * 40 + b"\tlink\0", b"100644 blob " + b"a" * 40 + b"\tsrc/main.py"):
            with self.assertRaises((ValueError, SafeOpsError)): git._entries(self.root, raw)

    def test_git_context_budget_is_rejected_before_stage_allocation(self):
        with patch.object(git, "MAX_CONTEXT_BYTES", 1), self.assertRaises(SafeOpsError): self.review()
        self.assertFalse((self.root / ".safeops/stages").exists())

    def test_git_timeout_and_excess_output_are_controlled(self):
        with patch.object(subprocess, "run", side_effect=subprocess.TimeoutExpired("sensitive-fixture", 1)), self.assertRaises(SafeOpsError) as error:
            git._git(self.root, shutil.which("git"), "ls-files")
        self.assertNotIn("sensitive-fixture", str(error.exception))
        with patch.object(git, "MAX_GIT_OUTPUT", 1), self.assertRaises(ValueError): git._git(self.root, shutil.which("git"), "ls-files")

    def test_cli_json_review_and_stage_require_separate_confirmation(self):
        args = ["--root", str(self.root), "--json"]; output = io.StringIO()
        with contextlib.redirect_stdout(output): self.assertEqual(main(args + ["review-git-stage", self.proposal["proposal_id"]]), 0)
        reviewed = json.loads(output.getvalue())["data"]; output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(args + ["stage-git-proposal", self.proposal["proposal_id"], "--confirm", reviewed["fingerprint"]]), 0)
        self.assertEqual(json.loads(output.getvalue())["data"]["status"], "staged")

    def test_git_stage_runs_existing_explicit_checks_application_and_rollback(self):
        from euromind_safeops.execution import approve, run
        from euromind_safeops.application import review_application, apply_stage, rollback_application
        from euromind_safeops.application_journal import inspect_application
        r = self.stage(); copied = Path(r["workspace"]); original_index = (self.root / ".git/index").read_bytes()
        with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(main(["--root", str(copied), "init"]), 0)
        plan = create_plan(copied, "Validate reviewed greeting", ["src/main.py"], "offline", "offline")
        approve(copied, plan["id"], "reviewed public fixture", plan["id"])
        outcome = run(copied, plan["id"]); self.assertEqual(outcome["status"], "passed")
        application = review_application(self.root, r["stage_id"], outcome["run_id"])
        applied = apply_stage(self.root, r["stage_id"], outcome["run_id"], application["fingerprint"])
        self.assertEqual(self.source.read_bytes(), b'greeting = "Portugal"\n')
        inspected = inspect_application(self.root, applied["application_id"])
        rollback_application(self.root, applied["application_id"], inspected["rollback_fingerprint"])
        self.assertEqual(self.source.read_bytes(), 'greeting = "Olá"\n'.encode())
        self.assertEqual((self.root / ".git/index").read_bytes(), original_index)
