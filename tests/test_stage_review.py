"""Current original context, historical copies, bounded reads and no authority."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from euromind_safeops import stage_review as review
from euromind_safeops.cli import main
from euromind_safeops.core import SafeOpsError, json_bytes, sha256, tree_digest
from euromind_safeops.execution import targets_digest
from euromind_safeops.planning import create_plan
from euromind_safeops.proposals import create_proposal
from euromind_safeops.staging import stage_proposal


class StageReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = (Path(self.temp.name) / "private" / "project").resolve()
        (self.root / "src").mkdir(parents=True)
        (self.root / "src/demo.py").write_bytes(b"value = 1\n")
        (self.root / "notes.txt").write_bytes(b"Original notes\n")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--root", str(self.root), "init"]), 0)
        self.config = self.root / ".safeops/config.json"
        self.prepare()

    def prepare(self):
        plan = create_plan(self.root, "Improve documentation", ["src/demo.py"], "Local", "offline")
        self.plan_path = self.root / ".safeops/plans" / (plan["id"] + ".json")
        candidate = Path(self.temp.name) / "candidate.json"
        candidate.write_bytes(json_bytes({"schema": 1, "files": [{"path": "src/demo.py",
            "base_sha256": hashlib.sha256(b"value = 1\n").hexdigest(), "content": "value = 2\n"}]}))
        proposal = create_proposal(self.root, plan["id"], candidate)
        self.stage = stage_proposal(self.root, proposal["proposal_id"], proposal["fingerprint"])
        self.stage_id = self.stage["stage_id"]
        self.copied = Path(self.stage["workspace"])

    def call(self, stage_id=None):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["--json", "--root", str(self.root), "review-stage", stage_id or self.stage_id])
        return code, json.loads(out.getvalue())

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes()
                for p in self.root.rglob("*") if p.is_file() and not p.is_symlink()}

    def assert_rejected(self):
        code, payload = self.call()
        self.assertEqual(code, 2)
        self.assertIsNone(payload["data"])
        self.assertEqual(payload["error"]["message"], review._ERROR)

    def test_current_has_no_writes_execution_provider_or_content(self):
        (self.root / ".git").mkdir()
        (self.root / ".git/HEAD").write_bytes(b"ref: refs/heads/main\n")
        (self.root / ".safeops/approvals/retained.json").write_bytes(b"retained human approval")
        before = self.snapshot()
        with patch("subprocess.run") as run, patch("euromind_safeops.cli.remote_advice") as remote, \
                patch("euromind_safeops.staging.audit") as audit:
            code, payload = self.call()
            run.assert_not_called()
            remote.assert_not_called()
            audit.assert_not_called()
        self.assertEqual(code, 0)
        data = payload["data"]
        self.assertEqual(data["status"], "current")
        self.assertTrue(all(data["checks"].values()))
        self.assertEqual(data["source_context"], "revalidated")
        self.assertEqual(data["reasons"], [])
        self.assertEqual(data["receipt_fingerprint"], self.stage["receipt_fingerprint"])
        self.assertNotIn("value =", json.dumps(payload))
        self.assertEqual(before, self.snapshot())

    def test_changed_original_candidate_is_stale_without_writes(self):
        (self.root / "src/demo.py").write_bytes(b"private original text\n")
        before = self.snapshot()
        code, payload = self.call()
        self.assertEqual(code, 1)
        self.assertFalse(payload["ok"])
        self.assertIsNone(payload["error"])
        self.assertEqual(payload["data"]["status"], "stale")
        self.assertEqual(payload["data"]["reasons"], ["source-changed", "candidate-bases-changed"])
        self.assertNotIn("private original text", json.dumps(payload))
        self.assertEqual(before, self.snapshot())

    def test_changes_outside_candidate_are_stale(self):
        (self.root / "notes.txt").write_bytes(b"changed notes\n")
        data = self.call()[1]["data"]
        self.assertEqual(data["reasons"], ["source-changed"])
        self.assertTrue(data["checks"]["candidate_bases"])

    def test_missing_original_candidate_is_stale(self):
        (self.root / "src/demo.py").unlink()
        self.assertEqual(self.call()[1]["data"]["reasons"], ["source-changed", "candidate-bases-changed"])

    def test_valid_changed_config_is_stale(self):
        self.config.write_bytes(json_bytes({"schema": 1, "checks": ["compile"]}))
        self.assertEqual(self.call()[1]["data"]["reasons"], ["configuration-changed"])

    def test_changed_version_and_contract_do_not_renew_approval(self):
        before = self.snapshot()
        with patch.object(review, "__version__", "9.0.0"), \
                patch.object(review, "execution_contract_digest", return_value="0" * 64):
            data = self.call()[1]["data"]
        self.assertEqual(data["reasons"], ["version-changed", "execution-contract-changed"])
        self.assertFalse(data["version_matches"])
        self.assertEqual(before, self.snapshot())

    def test_valid_changed_bound_plan_is_stale(self):
        plan = json.loads(self.plan_path.read_bytes())
        plan["task"] = "Changed advisory description"
        plan.pop("fingerprint")
        plan["fingerprint"] = sha256(plan)
        self.plan_path.write_bytes(json_bytes(plan))
        self.assertEqual(self.call()[1]["data"]["reasons"], ["plan-changed"])

    def test_schema_two_targets_include_snapshot_exclusions(self):
        cache = self.root / "src/__pycache__"
        cache.mkdir()
        selected = cache / "fixture.dat"
        selected.write_bytes(b"before")
        config = {"schema": 2, "checks": ["compile"], "targets": {"compile": ["src"]}}
        self.config.write_bytes(json_bytes(config))
        self.prepare()
        self.assertEqual(review._targets(self.root, config), targets_digest(self.root, config))
        self.assertEqual(self.call()[0], 0)
        selected.write_bytes(b"after")
        self.assertEqual(self.call()[1]["data"]["reasons"], ["selected-targets-changed"])

    def test_original_environment_and_generated_named_files_remain_in_snapshot(self):
        for name in (".env.local", ".git", "build"):
            (self.root / name).write_bytes(b"original local bytes\n")
        self.prepare()
        files, digest = review._source_snapshot(self.root)
        self.assertEqual(digest, tree_digest(self.root))
        self.assertTrue({".env.local", "build"}.issubset(files))
        self.assertNotIn(".git", files)  # Linked metadata is inspected separately in schema-2 Git stages.
        self.assertEqual(self.call()[0], 0)
        (self.root / ".env.local").write_bytes(b"changed local bytes\n")
        code, payload = self.call()
        self.assertEqual(code, 1)
        self.assertNotIn("changed local bytes", json.dumps(payload))

    def test_generated_directories_are_excluded_from_original_snapshot(self):
        (self.root / "build").mkdir()
        (self.root / "build/generated").write_bytes(b"ignored")
        self.assertEqual(self.call()[0], 0)
        self.assertEqual(review._source_snapshot(self.root)[1], tree_digest(self.root))

    def test_source_snapshot_retains_nested_sorted_traversal(self):
        for name in ("aaa/file.txt", "aaa/nested/demo.txt", "zzz/first.txt"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(name.encode("utf-8"))
        self.prepare()
        self.assertEqual(review._source_snapshot(self.root)[1], tree_digest(self.root))
        self.assertEqual(self.call()[0], 0)

    def test_changed_copy_is_incompatible_and_does_not_read_original(self):
        (self.copied / "notes.txt").write_bytes(b"changed staged notes")
        with patch.object(review, "_observe") as observe:
            code, payload = self.call()
            observe.assert_not_called()
        self.assertEqual(code, 1)
        self.assertEqual(payload["data"]["status"], "incompatible")
        self.assertEqual(payload["data"]["source_context"], "not-reviewed")

    def test_incomplete_copy_is_incompatible_without_cleanup(self):
        (self.copied.parent / "receipt.json").unlink()
        before = self.snapshot()
        code, payload = self.call()
        self.assertEqual(code, 1)
        self.assertEqual(payload["data"]["stage_status"], "incomplete")
        self.assertEqual(payload["data"]["reasons"], ["stage-not-matching"])
        self.assertEqual(before, self.snapshot())

    def test_malformed_evidence_is_sanitized(self):
        for raw in (b'{"schema":1,"schema":1}', b'{"schema":NaN}', b'private broken text', b'\xff'):
            with self.subTest(raw=raw):
                self.plan_path.write_bytes(raw)
                self.assert_rejected()

    def test_invalid_or_missing_config_is_sanitized(self):
        for raw in (b'{}', b'{"schema":true,"checks":["compile"]}', b'bad local configuration'):
            self.config.write_bytes(raw)
            self.assert_rejected()
        self.config.unlink()
        self.assert_rejected()

    def test_malformed_plan_policy_scope_and_fingerprint_are_rejected(self):
        original = self.plan_path.read_bytes()
        for key, value in (("schema", True), ("risk", "critical"), ("paths", ["../escape"]),
                           ("paths", []), ("fingerprint", "0" * 64), ("extra", 1)):
            plan = json.loads(original)
            plan[key] = value
            if key != "fingerprint":
                plan.pop("fingerprint")
                plan["fingerprint"] = sha256(plan)
            self.plan_path.write_bytes(json_bytes(plan))
            self.assert_rejected()

    def test_missing_plan_and_invalid_stage_id_are_rejected(self):
        self.plan_path.unlink()
        self.assert_rejected()
        self.assertEqual(self.call("../private-value")[0], 2)

    def test_source_file_and_total_byte_budgets(self):
        for name in ("MAX_FILE_BYTES", "MAX_COPY_BYTES"):
            with self.subTest(limit=name), patch.object(review, name, 1):
                self.assert_rejected()

    def test_source_file_entry_and_depth_budgets(self):
        for name, value in (("MAX_FILES", 1), ("MAX_ENTRIES", 1), ("MAX_DEPTH", 0)):
            with self.subTest(limit=name), patch.object(review, name, value):
                self.assert_rejected()

    def test_plan_and_config_control_read_limits(self):
        for path in (self.plan_path, self.config):
            before = path.read_bytes()
            path.write_bytes(b" " * 256_001)
            self.assert_rejected()
            path.write_bytes(before)

    def test_selected_file_and_total_budgets(self):
        config = {"schema": 2, "checks": ["compile"], "targets": {"compile": ["src"]}}
        for name in ("MAX_FILES", "MAX_FILE_BYTES", "MAX_COPY_BYTES"):
            with self.subTest(limit=name), patch.object(review, name, 0), self.assertRaises((ValueError, SafeOpsError)):
                review._targets(self.root, config)

    def test_selected_paths_changing_are_rejected(self):
        config = {"schema": 2, "checks": ["compile"], "targets": {"compile": ["src"]}}
        with patch.object(review, "validate_targets", side_effect=[[self.root / "src/demo.py"], []]), \
                self.assertRaises(ValueError):
            review._targets(self.root, config)

    def test_source_changes_between_observations_are_rejected(self):
        original = review._observe
        count = 0
        def change(*args):
            nonlocal count
            value = original(*args)
            count += 1
            if count == 1:
                (self.root / "notes.txt").write_bytes(b"concurrent local text")
            return value
        with patch.object(review, "_observe", side_effect=change):
            self.assert_rejected()

    def test_config_changes_during_observation_are_rejected(self):
        original = review._source_snapshot
        def change(*args):
            value = original(*args)
            self.config.write_bytes(json_bytes({"schema": 1, "checks": ["compile"]}))
            return value
        with patch.object(review, "_source_snapshot", side_effect=change):
            self.assert_rejected()

    def test_stage_changes_before_final_inspection_are_rejected(self):
        original = review._observe
        count = 0
        def change(*args):
            nonlocal count
            value = original(*args)
            count += 1
            if count == 2:
                (self.copied / "notes.txt").write_bytes(b"concurrent staged text")
            return value
        with patch.object(review, "_observe", side_effect=change):
            self.assert_rejected()

    def test_source_directory_identity_change_is_rejected(self):
        original = review._directory
        count = 0
        def change(path):
            nonlocal count
            identity = original(path)
            if path == self.root:
                count += 1
                if count > 1:
                    return (identity[0], identity[1] + count)
            return identity
        with patch.object(review, "_directory", side_effect=change):
            self.assert_rejected()

    def test_ambiguous_source_name_is_rejected(self):
        (self.root / "control\u0085name").write_bytes(b"ambiguous")
        self.assert_rejected()

    def test_source_case_collision_is_rejected(self):
        path = self.root / "NOTES.TXT"
        if path.exists():
            self.skipTest("Case-insensitive filesystem")
        path.write_bytes(b"collision")
        self.assert_rejected()

    def test_unreadable_source_is_sanitized(self):
        with patch.object(review, "_read", side_effect=PermissionError("private path and text")):
            self.assert_rejected()

    def test_proposal_change_before_context_read_is_rejected(self):
        original = review._proposal
        def change(*args):
            value = original(*args)
            return {**value, "fingerprint": "0" * 64}
        with patch.object(review, "_proposal", side_effect=change):
            self.assert_rejected()

    def test_selected_generated_links_are_rejected_without_source_change(self):
        self.config.write_bytes(json_bytes({"schema": 2, "checks": ["compile"],
                                           "targets": {"compile": ["src"]}}))
        self.prepare()
        cache = self.root / "src/__pycache__"
        cache.mkdir()
        try:
            (cache / "alias").symlink_to(self.root / "notes.txt")
        except OSError:
            self.skipTest("Symlinks unavailable")
        self.assert_rejected()

    def test_source_directory_and_excluded_name_links_are_rejected(self):
        for name in ("linked", "build"):
            link = self.root / name
            try:
                link.symlink_to(self.root / "src", target_is_directory=True)
            except OSError:
                self.skipTest("Directory symlinks unavailable")
            try:
                self.assert_rejected()
            finally:
                link.unlink()

    def test_source_and_control_hardlinks_are_rejected(self):
        for target in (self.root / "notes.txt", self.plan_path):
            outside = Path(self.temp.name) / "alias"
            try:
                os.link(target, outside)
            except OSError:
                self.skipTest("Hardlinks unavailable")
            try:
                self.assert_rejected()
            finally:
                outside.unlink()

    def test_source_and_control_symlinks_are_rejected(self):
        outside = Path(self.temp.name) / "outside"
        outside.write_bytes(b"private external text")
        for target in (self.root / "notes.txt", self.plan_path):
            before = target.read_bytes()
            target.unlink()
            try:
                target.symlink_to(outside)
            except OSError:
                target.write_bytes(before)
                self.skipTest("Symlinks unavailable")
            try:
                self.assert_rejected()
            finally:
                target.unlink()
                target.write_bytes(before)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX FIFO")
    def test_source_and_config_fifos_do_not_block(self):
        for target in (self.root / "notes.txt", self.config):
            before = target.read_bytes()
            target.unlink()
            os.mkfifo(target)
            try:
                self.assert_rejected()
            finally:
                target.unlink()
                target.write_bytes(before)


if __name__ == "__main__":
    unittest.main()
