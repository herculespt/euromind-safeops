"""Confirmed original replacements, retained failure journals and safe rollback."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from euromind_safeops import application as app, application_journal as journal
from euromind_safeops.cli import main
from euromind_safeops.core import SafeOpsError, json_bytes, sha256
from euromind_safeops.execution import approve, run
from euromind_safeops.locking import _guard, lock_status
from euromind_safeops.planning import create_plan
from euromind_safeops.proposals import create_proposal
from euromind_safeops.staging import stage_proposal


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = (Path(self.temp.name) / "private" / "project").resolve()
        (self.root / "src").mkdir(parents=True)
        (self.root / "tests").mkdir()
        self.originals = {"src/a.py": b"value = 1\n", "src/b.py": b"value = 10\n"}
        self.replacements = {"src/a.py": b"value = 2\n", "src/b.py": b"value = 20\n"}
        for name, raw in self.originals.items():
            (self.root / name).write_bytes(raw)
        (self.root / "tests/test_demo.py").write_bytes(
            b"import unittest\nclass T(unittest.TestCase):\n def test_it(self): pass\n")
        (self.root / "notes.txt").write_bytes("Revisão original — Português\n".encode())
        (self.root / ".git").mkdir()
        (self.root / ".git/HEAD").write_bytes(b"ref: refs/heads/main\n")
        (self.root / ".git/index").write_bytes(b"preserved Git fixture")
        self.init(self.root)
        self.state = self.root / ".safeops"
        self.prepare()

    def init(self, root):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--root", str(root), "init"]), 0)

    def prepare(self, config=None):
        if config is not None:
            (self.state / "config.json").write_bytes(json_bytes(config))
        config = json.loads((self.state / "config.json").read_bytes())
        plan = create_plan(self.root, "Improve documentation", list(self.originals), "private local advice", "offline")
        self.plan_id = plan["id"]
        approve(self.root, self.plan_id, "private human reason", self.plan_id)
        candidate = self.state / "candidate.json"
        candidate.write_bytes(json_bytes({"schema": 1, "files": [
            {"path": name, "base_sha256": hashlib.sha256(raw).hexdigest(),
             "content": self.replacements[name].decode()} for name, raw in self.originals.items()]}))
        proposal = create_proposal(self.root, self.plan_id, candidate)
        stage = stage_proposal(self.root, proposal["proposal_id"], proposal["fingerprint"])
        self.stage_id = stage["stage_id"]
        self.copied = Path(stage["workspace"])
        self.init(self.copied)
        (self.copied / ".safeops/config.json").write_bytes(json_bytes(config))
        self.staged_plan = create_plan(self.copied, "Check staged documentation", [], "Local", "offline")["id"]
        approve(self.copied, self.staged_plan, "Reviewed trusted tests", self.staged_plan)
        self.staged_run()

    def staged_run(self, returncode=0):
        with patch("euromind_safeops.execution.run_check",
                   return_value=subprocess.CompletedProcess([], returncode, "", "")):
            self.run_id = run(self.copied, self.staged_plan)["run_id"]

    def review(self):
        return app.review_application(self.root, self.stage_id, self.run_id)

    def apply(self):
        return app.apply_stage(self.root, self.stage_id, self.run_id, self.review()["fingerprint"])

    def inspect(self, application_id):
        return journal.inspect_application(self.root, application_id)

    def rollback(self, application_id):
        return app.rollback_application(self.root, application_id, self.inspect(application_id)["rollback_fingerprint"])

    def source_bytes(self):
        return {name: (self.root / name).read_bytes() for name in self.originals}

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes()
                for p in self.root.rglob("*") if p.is_file() and not p.is_symlink()}

    def owned(self, application_id):
        return self.state / "applications" / application_id

    def only_application(self):
        owned, = (self.state / "applications").iterdir()
        return owned.name

    def rewrite(self, path, value):
        value.pop("fingerprint", None)
        value["fingerprint"] = sha256(value)
        path.write_bytes(json_bytes(value) + b"\n")

    def cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["--json", "--root", str(self.root), *args])
        return code, json.loads(out.getvalue())

    def test_review_is_stable_private_and_has_no_writes_or_execution(self):
        before = self.snapshot()
        with patch("subprocess.run") as child, patch("euromind_safeops.cli.remote_advice") as provider, patch.object(app, "audit") as audit:
            reviewed = self.review()
            self.assertEqual(self.review(), reviewed)
            child.assert_not_called()
            provider.assert_not_called()
            audit.assert_not_called()
        self.assertEqual(before, self.snapshot())
        for text in ("value =", "private local advice", "private human reason", str(self.root)):
            self.assertNotIn(text, json.dumps(reviewed))
        self.assertFalse((self.state / "applications").exists())
        self.assertFalse((self.state / "run.guard").exists())

    def test_real_staged_checks_apply_and_rollback_preserve_all_history(self):
        self.run_id = run(self.copied, self.staged_plan)["run_id"]
        before = self.snapshot()
        reviewed = self.review()
        with patch("subprocess.run") as child, patch("euromind_safeops.cli.remote_advice") as provider:
            code, applied = self.cli("apply-stage", self.stage_id, "--run", self.run_id, "--confirm", reviewed["fingerprint"])
            child.assert_not_called()
            provider.assert_not_called()
        self.assertEqual(code, 0)
        result = applied["data"]
        self.assertEqual(result["status"], "applied")
        self.assertEqual(self.source_bytes(), self.replacements)
        self.assertFalse((self.state / "application.pending").exists())
        for name, raw in before.items():
            if name in self.originals or name == ".safeops/audit.jsonl":
                continue
            self.assertEqual((self.root / name).read_bytes(), raw, name)
        code, inspected = self.cli("inspect-application", result["application_id"])
        self.assertEqual(code, 0)
        self.assertEqual(inspected["data"], self.inspect(result["application_id"]))
        code, restored = self.cli("rollback-application", result["application_id"], "--confirm", result["rollback_fingerprint"])
        self.assertEqual(code, 0)
        self.assertEqual(restored["data"]["status"], "rolled-back")
        self.assertEqual(self.source_bytes(), self.originals)
        self.assertTrue((self.owned(result["application_id"]) / "applied.json").is_file())
        self.assertTrue((self.owned(result["application_id"]) / "rolled-back.json").is_file())

    def test_basic_mode_is_preserved(self):
        if os.name == "posix":
            (self.root / "src/a.py").chmod(0o755)
        before = {name: stat.S_IMODE((self.root / name).stat().st_mode) for name in self.originals}
        result = self.apply()
        self.assertEqual({name: stat.S_IMODE((self.root / name).stat().st_mode) for name in before}, before)
        self.rollback(result["application_id"])
        self.assertEqual({name: stat.S_IMODE((self.root / name).stat().st_mode) for name in before}, before)

    def test_exact_application_confirmation_is_required_before_allocation(self):
        with self.assertRaises(SafeOpsError):
            app.apply_stage(self.root, self.stage_id, self.run_id, "0" * 64)
        with self.assertRaises(SafeOpsError):
            app.apply_stage(self.root, self.stage_id, self.run_id, "private invalid confirmation")
        self.assertFalse((self.state / "applications").exists())
        self.assertEqual(self.source_bytes(), self.originals)

    def test_original_change_after_review_is_preserved_and_refused(self):
        reviewed = self.review()
        (self.root / "src/a.py").write_bytes(b"human edit\n")
        with self.assertRaises(SafeOpsError):
            app.apply_stage(self.root, self.stage_id, self.run_id, reviewed["fingerprint"])
        self.assertEqual((self.root / "src/a.py").read_bytes(), b"human edit\n")
        self.assertFalse((self.state / "applications").exists())

    def test_staged_source_change_after_passed_run_is_refused(self):
        (self.copied / "src/a.py").write_bytes(b"changed staged source\n")
        with self.assertRaises(SafeOpsError):
            self.review()

    def test_staged_configuration_and_approval_changes_are_refused(self):
        path = self.copied / ".safeops/config.json"
        old = path.read_bytes()
        path.write_bytes(json_bytes({"schema": 1, "checks": ["unit-tests", "compile"]}))
        with self.assertRaises(SafeOpsError):
            self.review()
        path.write_bytes(old)
        path = self.copied / ".safeops/approvals" / (self.staged_plan + ".json")
        value = json.loads(path.read_bytes())
        value["reason"] = "changed reason"
        path.write_bytes(json_bytes(value))
        with self.assertRaises(SafeOpsError):
            self.review()

    def test_compile_only_receipt_cannot_authorize_application(self):
        self.prepare({"schema": 1, "checks": ["compile"]})
        with self.assertRaises(SafeOpsError):
            self.review()

    def test_failed_and_incomplete_staged_results_are_refused(self):
        self.staged_run(1)
        with self.assertRaises(SafeOpsError):
            self.review()
        (self.copied / ".safeops/runs" / self.run_id / "receipt.json").unlink()
        with self.assertRaises(SafeOpsError):
            self.review()

    def test_filtered_environment_addition_does_not_masquerade_as_tested_stage(self):
        (self.copied / ".env.local").write_bytes(b"unreviewed environment fixture")
        with self.assertRaises(SafeOpsError):
            self.review()

    def test_same_policy_with_changed_bytes_requires_new_confirmation(self):
        reviewed = self.review()
        path = self.state / "config.json"
        path.write_bytes(path.read_bytes() + b"\n")
        self.assertNotEqual(self.review()["fingerprint"], reviewed["fingerprint"])
        with self.assertRaises(SafeOpsError):
            app.apply_stage(self.root, self.stage_id, self.run_id, reviewed["fingerprint"])

    def test_selected_generated_data_change_is_refused(self):
        self.prepare({"schema": 2, "checks": ["compile", "unit-tests"],
                      "targets": {"compile": ["src"], "unit-tests": ["tests"]}})
        generated = self.copied / "src/build"
        generated.mkdir()
        (generated / "data.bin").write_bytes(b"new selected data")
        with self.assertRaises(SafeOpsError):
            self.review()

    def test_schema_two_selected_targets_apply_and_rollback(self):
        self.prepare({"schema": 2, "checks": ["compile", "unit-tests"],
                      "targets": {"compile": ["src"], "unit-tests": ["tests"]}})
        result = self.apply()
        self.assertEqual(result["status"], "applied")
        self.assertEqual(self.rollback(result["application_id"])["status"], "rolled-back")

    def test_retained_run_markers_and_busy_native_guards_refuse_application(self):
        for root in (self.root, self.copied):
            marker = root / ".safeops/run.lock"
            marker.write_bytes(b"123")
            with self.assertRaises(SafeOpsError):
                self.review()
            marker.unlink()
            with _guard(root / ".safeops"), self.assertRaises(SafeOpsError):
                self.review()

    def test_pending_entry_blocks_runs_and_applications_without_following_it(self):
        path = self.state / "application.pending"
        path.mkdir()
        with self.assertRaises(SafeOpsError):
            self.review()
        with self.assertRaisesRegex(SafeOpsError, "Application journal pending"):
            run(self.root, self.plan_id)
        self.assertTrue(lock_status(self.root)["application_pending"])
        self.assertTrue(path.is_dir())

    def test_readonly_source_is_refused_without_chmod_side_effect(self):
        path = self.root / "src/a.py"
        before = stat.S_IMODE(path.stat().st_mode)
        path.chmod(0o444)
        try:
            with self.assertRaises(SafeOpsError):
                self.review()
            self.assertFalse(path.stat().st_mode & stat.S_IWUSR)
        finally:
            path.chmod(before)

    def test_guarded_revalidation_detects_new_human_edits(self):
        reviewed = self.review()
        original = app._stable_review
        def change(*args, **kwargs):
            if kwargs.get("guarded"):
                (self.root / "src/a.py").write_bytes(b"concurrent human edit\n")
            return original(*args, **kwargs)
        with patch.object(app, "_stable_review", side_effect=change), self.assertRaises(SafeOpsError):
            app.apply_stage(self.root, self.stage_id, self.run_id, reviewed["fingerprint"])
        self.assertFalse((self.state / "applications").exists())
        self.assertEqual((self.root / "src/a.py").read_bytes(), b"concurrent human edit\n")

    def interrupt_apply(self):
        original = app._install
        calls = 0
        def fail(*args):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("private write failure")
            return original(*args)
        with patch.object(app, "_install", side_effect=fail), self.assertRaises(SafeOpsError) as error:
            self.apply()
        application_id = self.only_application()
        self.assertIn(application_id, str(error.exception))
        self.assertNotIn("private write failure", str(error.exception))
        return application_id

    def test_mid_write_failure_retains_backups_pending_and_explicit_rollback(self):
        application_id = self.interrupt_apply()
        result = self.inspect(application_id)
        self.assertEqual(result["status"], "pending")
        self.assertEqual([f["state"] for f in result["files"]], ["applied", "original"])
        self.assertEqual(self.cli("inspect-application", application_id)[0], 1)
        with self.assertRaisesRegex(SafeOpsError, "Application journal pending"):
            run(self.root, self.plan_id)
        with self.assertRaises(SafeOpsError):
            self.apply()
        self.assertEqual(self.rollback(application_id)["status"], "rolled-back")
        self.assertEqual(self.source_bytes(), self.originals)
        self.assertFalse((self.state / "application.pending").exists())

    def test_human_edit_between_writes_is_never_forced_back(self):
        original = app._install
        calls = 0
        def change(*args):
            nonlocal calls
            calls += 1
            if calls == 2:
                (self.root / "src/b.py").write_bytes(b"concurrent human edit\n")
            return original(*args)
        with patch.object(app, "_install", side_effect=change), self.assertRaises(SafeOpsError):
            self.apply()
        application_id = self.only_application()
        result = self.inspect(application_id)
        self.assertEqual(result["status"], "conflicted")
        self.assertFalse(result["rollback_candidate"])
        before = self.source_bytes()
        with self.assertRaises(SafeOpsError):
            self.rollback(application_id)
        self.assertEqual(self.source_bytes(), before)

    def test_unrelated_source_change_during_progress_stops_writes(self):
        original = app._progress
        calls = 0
        def change(*args):
            nonlocal calls
            calls += 1
            if calls == 2:
                (self.root / "notes.txt").write_bytes(b"unrelated concurrent edit")
            return original(*args)
        with patch.object(app, "_progress", side_effect=change), self.assertRaises(SafeOpsError):
            self.apply()
        application_id = self.only_application()
        self.rollback(application_id)
        self.assertEqual((self.root / "notes.txt").read_bytes(), b"unrelated concurrent edit")
        self.assertEqual(self.source_bytes(), self.originals)

    def test_audit_failure_leaves_recoverable_applied_files_without_completion(self):
        with patch.object(app, "audit", side_effect=OSError("private audit failure")), self.assertRaises(SafeOpsError):
            self.apply()
        application_id = self.only_application()
        self.assertEqual(self.source_bytes(), self.replacements)
        self.assertIsNone(self.inspect(application_id)["completion"])
        self.assertTrue((self.state / "application.pending").is_file())
        self.assertEqual(self.rollback(application_id)["status"], "rolled-back")

    def test_final_record_failure_retains_pending_and_backups(self):
        original = journal.write_record
        def fail(root, path, value):
            if path.name == "applied.json":
                raise OSError("private persistence error")
            return original(root, path, value)
        with patch.object(journal, "write_record", side_effect=fail), self.assertRaises(SafeOpsError):
            self.apply()
        self.assertEqual(self.rollback(self.only_application())["status"], "rolled-back")

    def test_marker_release_failure_is_visible_and_can_be_rolled_back(self):
        with patch.object(app, "_clear_pending", side_effect=OSError("cannot release")), self.assertRaises(SafeOpsError):
            self.apply()
        application_id = self.only_application()
        result = self.inspect(application_id)
        self.assertEqual((result["status"], result["completion"]), ("pending", "applied"))
        self.assertEqual(self.rollback(application_id)["status"], "rolled-back")

    def test_partial_preparation_never_changes_original_files(self):
        original = journal.write_bytes
        def fail(root, path, raw, **kwargs):
            if path.name == "new-001.bin":
                raise OSError("preparation failed")
            return original(root, path, raw, **kwargs)
        with patch.object(journal, "write_bytes", side_effect=fail), self.assertRaises(SafeOpsError):
            self.apply()
        self.assertEqual(self.source_bytes(), self.originals)
        self.assertFalse((self.state / "application.pending").exists())
        self.assertTrue((self.owned(self.only_application()) / "backup-000.bin").exists())

    def test_rollback_requires_fresh_fingerprint_and_preserves_human_edit(self):
        result = self.apply()
        with self.assertRaises(SafeOpsError):
            app.rollback_application(self.root, result["application_id"], "0" * 64)
        (self.root / "src/a.py").write_bytes(b"post-application human edit\n")
        before = self.source_bytes()
        with self.assertRaises(SafeOpsError):
            app.rollback_application(self.root, result["application_id"], result["rollback_fingerprint"])
        self.assertEqual(self.source_bytes(), before)

    def test_same_bytes_with_new_inode_are_not_owned_for_rollback(self):
        result = self.apply()
        replacement = self.state / "human-file"
        replacement.write_bytes(self.replacements["src/a.py"])
        os.replace(replacement, self.root / "src/a.py")
        self.assertFalse(self.inspect(result["application_id"])["rollback_candidate"])
        with self.assertRaises(SafeOpsError):
            self.rollback(result["application_id"])

    def test_partial_rollback_can_resume_from_bound_prepared_files(self):
        result = self.apply()
        original = app._install
        calls = 0
        def fail(*args):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("interrupted restore")
            return original(*args)
        with patch.object(app, "_install", side_effect=fail), self.assertRaises(SafeOpsError):
            self.rollback(result["application_id"])
        inspected = self.inspect(result["application_id"])
        self.assertEqual([f["state"] for f in inspected["files"]], ["applied", "restored"])
        self.assertEqual(self.rollback(result["application_id"])["status"], "rolled-back")
        self.assertEqual(self.source_bytes(), self.originals)

    def test_rollback_preserves_unrelated_edits_and_needs_no_current_config(self):
        result = self.apply()
        (self.root / "notes.txt").write_bytes(b"keep this later edit")
        (self.state / "config.json").unlink()
        (self.state / "plans" / (self.plan_id + ".json")).unlink()
        result = self.rollback(result["application_id"])
        self.assertEqual(result["status"], "rolled-back")
        self.assertEqual((self.root / "notes.txt").read_bytes(), b"keep this later edit")

    def test_rollback_is_idempotent_after_completion_and_retains_history(self):
        application_id = self.apply()["application_id"]
        self.rollback(application_id)
        before = self.snapshot()
        result = self.rollback(application_id)
        self.assertEqual(result["status"], "rolled-back")
        self.assertEqual(before, self.snapshot())

    def test_prepared_or_backup_tampering_blocks_without_writes(self):
        original = app._progress
        def change(root, manifest, *args):
            (self.owned(manifest["id"]) / "backup-000.bin").write_bytes(b"tampered backup")
            return original(root, manifest, *args)
        with patch.object(app, "_progress", side_effect=change), self.assertRaises(SafeOpsError):
            self.apply()
        self.assertEqual(self.source_bytes(), self.originals)
        with self.assertRaises(SafeOpsError):
            self.inspect(self.only_application())

    def test_journal_inspection_rejects_malformed_and_oversized_json(self):
        application_id = self.apply()["application_id"]
        path = self.owned(application_id) / "intent.json"
        for raw in (b'{"schema":1,"schema":1}', b'{"schema":NaN}', b'\xff', b'[]', b' ' * 64_001):
            path.write_bytes(raw)
            with self.assertRaisesRegex(SafeOpsError, "Application inspection failed"):
                self.inspect(application_id)

    def test_manifest_fields_types_paths_and_linkage_are_strict(self):
        application_id = self.apply()["application_id"]
        path = self.owned(application_id) / "intent.json"
        original = json.loads(path.read_bytes())
        changes = [("schema", True), ("id", "0" * 12), ("stage_id", "../escape"),
                   ("created_at", "bad"), ("safeops_version", ""), ("safeops_version", "private text"),
                   ("files", []), ("extra", 1)]
        for key, value in changes:
            changed = copy.deepcopy(original)
            changed[key] = value
            self.rewrite(path, changed)
            with self.assertRaises(SafeOpsError):
                self.inspect(application_id)
        for key, value in (("path", "../escape"), ("path", ".env.local"), ("before", {})):
            changed = copy.deepcopy(original)
            changed["files"][0][key] = value
            self.rewrite(path, changed)
            with self.assertRaises(SafeOpsError):
                self.inspect(application_id)

    def test_unknown_artifacts_and_artifact_budget_fail_closed(self):
        application_id = self.apply()["application_id"]
        extra = self.owned(application_id) / "unknown"
        extra.write_bytes(b"private content")
        with self.assertRaises(SafeOpsError):
            self.inspect(application_id)
        extra.unlink()
        with patch.object(journal, "MAX_ARTIFACTS", 1), self.assertRaises(SafeOpsError):
            self.inspect(application_id)

    def test_inspection_detects_concurrent_candidate_or_control_changes(self):
        application_id = self.apply()["application_id"]
        original = journal.read_journal
        calls = 0
        def change(*args):
            nonlocal calls
            value = original(*args)
            calls += 1
            if calls == 1:
                (self.root / "src/a.py").write_bytes(b"changed during inspection")
            return value
        with patch.object(journal, "read_journal", side_effect=change), self.assertRaises(SafeOpsError):
            self.inspect(application_id)

    def test_invalid_ids_have_sanitized_cli_errors(self):
        for command in ("inspect-application", "review-application"):
            args = [command, "../private argument"]
            if command == "review-application":
                args += ["--run", self.run_id]
            code, payload = self.cli(*args)
            self.assertEqual(code, 2)
            self.assertIsNone(payload["data"])
            self.assertNotIn("private argument", payload["error"]["message"])

    def test_journal_or_source_hardlinks_are_refused(self):
        alias = Path(self.temp.name) / "alias"
        try:
            os.link(self.root / "src/a.py", alias)
        except OSError:
            self.skipTest("Hardlinks unavailable")
        try:
            with self.assertRaises(SafeOpsError):
                self.review()
        finally:
            alias.unlink()
        application_id = self.apply()["application_id"]
        os.link(self.owned(application_id) / "backup-000.bin", alias)
        try:
            with self.assertRaises(SafeOpsError):
                self.rollback(application_id)
        finally:
            alias.unlink()

    def test_journal_directory_symlink_is_refused_without_external_write(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        try:
            (self.state / "applications").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Symlinks unavailable")
        with self.assertRaises(SafeOpsError):
            self.apply()
        self.assertEqual(list(outside.iterdir()), [])

    def test_abrupt_process_death_retains_pending_and_releases_native_guards(self):
        reviewed = self.review()
        script = """
import sys
from pathlib import Path
from euromind_safeops import application as app
root=Path(sys.argv[1])
original=app._install
count=0
def pause(*args):
    global count
    value=original(*args)
    count+=1
    if count==1:
        (root/'.safeops/application-ready').write_bytes(b'ready')
        sys.stdin.read(1)
    return value
app._install=pause
app.apply_stage(root,sys.argv[2],sys.argv[3],sys.argv[4])
"""
        process = subprocess.Popen([sys.executable, "-c", script, str(self.root), self.stage_id,
                                    self.run_id, reviewed["fingerprint"]], cwd=self.root,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(lambda: process.kill() if process.poll() is None else None)
        deadline = time.monotonic() + 15
        while not (self.state / "application-ready").exists() and time.monotonic() < deadline:
            if process.poll() is not None:
                self.fail("Application child stopped before crash boundary: " + process.communicate()[1].decode())
            time.sleep(0.02)
        self.assertTrue((self.state / "application-ready").exists())
        process.kill()
        process.communicate(timeout=10)
        self.assertEqual(lock_status(self.root)["guard"], "free")
        self.assertEqual(lock_status(self.copied)["guard"], "free")
        application_id = self.only_application()
        self.assertEqual([f["state"] for f in self.inspect(application_id)["files"]], ["applied", "original"])
        self.assertEqual(self.rollback(application_id)["status"], "rolled-back")
        self.assertEqual(self.source_bytes(), self.originals)

    def test_cross_filesystem_preparation_is_refused_before_original_writes(self):
        original = journal.write_bytes
        def change(*args, **kwargs):
            info = original(*args, **kwargs)
            if args[1].name.startswith("new-"):
                info["identity"][0] += 1
            return info
        with patch.object(journal, "write_bytes", side_effect=change), self.assertRaises(SafeOpsError):
            self.apply()
        self.assertEqual(self.source_bytes(), self.originals)
        self.assertFalse((self.state / "application.pending").exists())

    def test_rollback_after_rename_before_return_uses_owned_file_identity(self):
        result = self.apply()
        original = app._install
        def fail(*args):
            original(*args)
            raise OSError("interrupted after replacement")
        with patch.object(app, "_install", side_effect=fail), self.assertRaises(SafeOpsError):
            self.rollback(result["application_id"])
        self.assertEqual(self.rollback(result["application_id"])["status"], "rolled-back")

    def test_partial_restore_preparation_is_retained_and_refused(self):
        result = self.apply()
        original = journal.write_record
        def fail(root, path, value):
            if path.name.startswith("restore-"):
                raise OSError("partial restore evidence")
            return original(root, path, value)
        with patch.object(journal, "write_record", side_effect=fail), self.assertRaises(SafeOpsError):
            self.rollback(result["application_id"])
        self.assertEqual(self.source_bytes(), self.replacements)
        self.assertTrue((self.owned(result["application_id"]) / "restore-001.bin").exists())
        with self.assertRaises(SafeOpsError):
            self.inspect(result["application_id"])

    def test_foreign_pending_marker_cannot_be_cleared_by_old_rollback(self):
        result = self.apply()
        marker = self.state / "application.pending"
        marker.write_bytes(json_bytes({"schema": 1, "id": "0" * 12, "intent_fingerprint": "0" * 64}) + b"\n")
        inspected = self.inspect(result["application_id"])
        self.assertEqual(inspected["pending_owner"], "other")
        self.assertFalse(inspected["rollback_candidate"])
        before = marker.read_bytes()
        with self.assertRaises(SafeOpsError):
            self.rollback(result["application_id"])
        self.assertEqual(marker.read_bytes(), before)

    def test_bad_completion_and_restore_metadata_fail_closed(self):
        result = self.apply()
        application_id = result["application_id"]
        path = self.owned(application_id) / "applied.json"
        raw = path.read_bytes()
        original = json.loads(raw)
        for key, value in (("schema", True), ("status", "rolled-back"), ("files", []), ("intent_fingerprint", "0" * 64)):
            changed = copy.deepcopy(original)
            changed[key] = value
            self.rewrite(path, changed)
            with self.assertRaises(SafeOpsError):
                self.inspect(application_id)
        path.write_bytes(raw)
        self.rollback(application_id)
        path = self.owned(application_id) / "restore-000.json"
        value = json.loads(path.read_bytes())
        value["prepared"]["sha256"] = "0" * 64
        self.rewrite(path, value)
        with self.assertRaises(SafeOpsError):
            self.inspect(application_id)

    def test_file_count_byte_budget_and_metadata_bounds_are_enforced(self):
        result = self.apply()
        path = self.owned(result["application_id"]) / "intent.json"
        original = json.loads(path.read_bytes())
        for key, value in (("mode", True), ("mode", 0o4755), ("uid", -1), ("identity", [1]),
                           ("identity", [-1, 1]), ("stamp", [False, 1])):
            changed = copy.deepcopy(original)
            changed["files"][0]["before"][key] = value
            self.rewrite(path, changed)
            with self.assertRaises(SafeOpsError):
                self.inspect(result["application_id"])
        self.rewrite(path, original)
        with patch.object(journal, "MAX_TOTAL_BYTES", 1), self.assertRaises(SafeOpsError):
            self.inspect(result["application_id"])

    def test_completed_rollback_marker_release_can_be_retried_explicitly(self):
        application_id = self.apply()["application_id"]
        with patch.object(app, "_clear_pending", side_effect=OSError("release interrupted")), self.assertRaises(SafeOpsError):
            self.rollback(application_id)
        result = self.inspect(application_id)
        self.assertEqual((result["status"], result["completion"]), ("pending", "rolled-back"))
        self.assertEqual(self.rollback(application_id)["status"], "rolled-back")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX FIFO")
    def test_journal_fifo_never_blocks_inspection(self):
        application_id = self.apply()["application_id"]
        path = self.owned(application_id) / "applied.json"
        path.unlink()
        os.mkfifo(path)
        with self.assertRaises(SafeOpsError):
            self.inspect(application_id)


if __name__ == "__main__":
    unittest.main()
