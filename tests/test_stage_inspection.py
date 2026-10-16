"""Retained stage lifecycle, historical linkage, bounded reads and no writes."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from euromind_safeops import stage_inspection as inspection, staging
from euromind_safeops.cli import main
from euromind_safeops.core import SafeOpsError, json_bytes, sha256
from euromind_safeops.planning import create_plan
from euromind_safeops.proposals import create_proposal


class StageInspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "private" / "project"
        (self.root / "src").mkdir(parents=True)
        (self.root / "src/demo.py").write_bytes(b"value = 1\n")
        (self.root / "notes.txt").write_bytes(b"Original notes\n")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--root", str(self.root), "init"]), 0)
        plan = create_plan(self.root, "Improve documentation", ["src/demo.py"], "Local", "offline")
        candidate = Path(self.temp.name) / "candidate.json"
        candidate.write_bytes(json_bytes({"schema": 1, "files": [{"path": "src/demo.py",
            "base_sha256": hashlib.sha256(b"value = 1\n").hexdigest(), "content": "value = 2\n"}]}))
        proposal = create_proposal(self.root, plan["id"], candidate)
        self.stage = staging.stage_proposal(self.root, proposal["proposal_id"], proposal["fingerprint"])
        self.stage_id = self.stage["stage_id"]
        self.copied = Path(self.stage["workspace"])
        self.owned = self.copied.parent
        self.receipt = self.owned / "receipt.json"
        self.intent = self.owned / "intent.json"
        self.proposal = self.root / ".safeops/proposals" / (proposal["proposal_id"] + ".json")

    def call(self, stage_id=None):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["--json", "--root", str(self.root), "inspect-stage", stage_id or self.stage_id])
        return code, json.loads(out.getvalue())

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes()
                for p in self.root.rglob("*") if p.is_file() and not p.is_symlink()}

    def write_receipt(self, value):
        value.pop("fingerprint", None)
        value["fingerprint"] = sha256(value)
        self.receipt.write_bytes(json_bytes(value))

    def assert_rejected(self):
        code, payload = self.call()
        self.assertEqual(code, 2)
        self.assertEqual(payload["error"]["message"], inspection._ERROR)
        self.assertIsNone(payload["data"])

    def test_matching_cli_has_no_writes_execution_or_file_text(self):
        before = self.snapshot()
        with patch("euromind_safeops.cli.remote_advice") as remote, patch("subprocess.run") as run, \
                patch("euromind_safeops.staging.audit") as audit:
            code, payload = self.call()
            remote.assert_not_called()
            run.assert_not_called()
            audit.assert_not_called()
        self.assertEqual(code, 0)
        self.assertEqual(payload["command"], "inspect-stage")
        self.assertTrue(payload["ok"])
        data = payload["data"]
        self.assertEqual(data["status"], "matching")
        self.assertEqual(data["recorded_files"], data["observed_files"])
        self.assertEqual(data["recorded_workspace_digest"], data["observed_workspace_digest"])
        self.assertEqual(data["receipt_fingerprint"], self.stage["receipt_fingerprint"])
        self.assertEqual(data["source_context"], "historical-binding-only")
        self.assertNotIn("value =", json.dumps(payload))
        self.assertEqual(self.snapshot(), before)

    def test_changed_missing_and_extra_are_exit_one_without_mutation(self):
        (self.copied / "src/demo.py").write_bytes(b"private changed text\n")
        (self.copied / "notes.txt").unlink()
        (self.copied / "new.bin").write_bytes(b"\x00\xffprivate binary")
        before = self.snapshot()
        code, payload = self.call()
        self.assertEqual(code, 1)
        self.assertFalse(payload["ok"])
        self.assertIsNone(payload["error"])
        data = payload["data"]
        self.assertEqual(data["status"], "changed")
        self.assertEqual(data["missing"], ["notes.txt"])
        self.assertEqual(data["extra"], ["new.bin"])
        self.assertEqual(data["changed"], ["src/demo.py"])
        # Absolute workspace paths are part of the documented result, including
        # macOS /private/ paths. Test the actual file contents, not one path word.
        self.assertNotIn("private changed text", json.dumps(payload))
        self.assertNotIn("private binary", json.dumps(payload))
        self.assertEqual(before, self.snapshot())

    def test_generated_environment_and_safeops_state_are_omitted(self):
        for directory in (".safeops", "__pycache__", ".venv", "build"):
            path = self.copied / directory
            path.mkdir()
            (path / "ignored").write_bytes(b"generated")
        (self.copied / ".ENV.sample").write_bytes(b"local environment")
        (self.copied / ".git").write_bytes(b"gitdir: local")
        self.assertEqual(self.call()[1]["data"]["status"], "matching")

    def test_original_and_configuration_changes_do_not_renew_authority(self):
        (self.root / "src/demo.py").write_bytes(b"changed original\n")
        (self.root / ".safeops/config.json").write_bytes(b"invalid current config")
        before = self.snapshot()
        data = self.call()[1]["data"]
        self.assertEqual(data["status"], "matching")
        self.assertEqual(data["source_context"], "historical-binding-only")
        self.assertEqual(before, self.snapshot())

    def test_historical_version_is_observed_without_rewriting_records(self):
        with patch.object(inspection, "__version__", "9.0.0a1"):
            data = self.call()[1]["data"]
        self.assertEqual(data["status"], "matching")
        self.assertFalse(data["version_matches"])
        self.assertNotEqual(data["recorded_safeops_version"], "9.0.0a1")

    def test_missing_receipt_reports_incomplete_and_keeps_partial_copy(self):
        self.receipt.unlink()
        before = self.snapshot()
        code, payload = self.call()
        self.assertEqual(code, 1)
        self.assertEqual(payload["data"]["status"], "incomplete")
        self.assertNotIn("observed_files", payload["data"])
        self.assertEqual(before, self.snapshot())

    def test_absent_or_invalid_stage_ids_are_sanitized(self):
        for value in ("../outside", "a" * 11, "A" * 12, "0" * 12):
            with self.subTest(value=value):
                code, result = self.call(value)
                self.assertEqual(code, 2)
                self.assertEqual(result["error"]["message"], inspection._ERROR)

    def test_missing_proposal_and_intent_are_controlled_failures(self):
        for path in (self.proposal, self.intent):
            before = path.read_bytes()
            path.unlink()
            self.assert_rejected()
            path.write_bytes(before)

    def test_strict_bounded_json_errors_do_not_echo_content(self):
        original = self.receipt.read_bytes()
        for raw in (b'{"schema":1,"schema":1,"private":"value"}', b'{"schema":NaN}',
                    b'[]', b'"private"', b'{"x":"\xff"}', b"{" * 1100):
            with self.subTest(raw=raw[:20]):
                self.receipt.write_bytes(raw)
                self.assert_rejected()
        self.receipt.write_bytes(original)
        for name, limit in (("MAX_RECEIPT_BYTES", 5),):
            with patch.object(inspection, name, limit): self.assert_rejected()
        self.intent.write_bytes(b" " * 4097)
        self.assert_rejected()

    def test_receipt_schema_hash_counts_and_entry_types_are_strict(self):
        original = json.loads(self.receipt.read_bytes())
        cases = []
        for key, value in (("schema", True), ("schema", 1.0), ("status", "ready"),
                           ("copied_bytes", True), ("copied_bytes", 1), ("unexpected", 1),
                           ("staged_workspace_digest", "BAD")):
            changed = copy.deepcopy(original)
            changed[key] = value
            cases.append(changed)
        for field, value in (("bytes", True), ("replaced", 1), ("source_sha256", None)):
            changed = copy.deepcopy(original)
            changed["files"][0][field] = value
            cases.append(changed)
        for changed in cases:
            with self.subTest(changed=changed):
                self.write_receipt(changed)
                self.assert_rejected()
        self.receipt.write_bytes(json_bytes(original))
        changed = copy.deepcopy(original)
        changed["fingerprint"] = "0" * 64
        self.receipt.write_bytes(json_bytes(changed))
        self.assert_rejected()

    def test_intent_shape_time_schema_and_linkage_are_strict(self):
        original = json.loads(self.intent.read_bytes())
        for key, value in (("schema", True), ("created_at", "2026-99-99T00:00:00+00:00"),
                           ("stage_id", "a" * 12), ("safeops_version", []),
                           ("proposal_fingerprint", "0" * 64), ("source_workspace_digest", "0" * 64)):
            with self.subTest(key=key):
                changed = copy.deepcopy(original)
                changed[key] = value
                self.intent.write_bytes(json_bytes(changed))
                self.assert_rejected()
        self.intent.write_bytes(json_bytes(original))

    def test_manifest_paths_duplicates_and_environment_are_rejected(self):
        original = json.loads(self.receipt.read_bytes())
        for value in (".", "../outside", "/outside", "a//b", "a\\b", ".env.sample", "src/CON", "bad\nname"):
            with self.subTest(value=value):
                changed = copy.deepcopy(original)
                changed["files"][0]["path"] = value
                self.write_receipt(changed)
                self.assert_rejected()
        changed = copy.deepcopy(original)
        changed["files"].append(copy.deepcopy(changed["files"][0]))
        self.write_receipt(changed)
        self.assert_rejected()

    def test_manifest_replacement_hash_and_set_must_match_proposal(self):
        original = json.loads(self.receipt.read_bytes())
        for value in ("0" * 64, "1" * 64):
            changed = copy.deepcopy(original)
            entry = next(x for x in changed["files"] if x["replaced"])
            entry["staged_sha256"] = value
            self.write_receipt(changed)
            self.assert_rejected()
        changed = copy.deepcopy(original)
        changed["files"] = [x for x in changed["files"] if not x["replaced"]]
        changed["copied_bytes"] = sum(x["bytes"] for x in changed["files"])
        self.write_receipt(changed)
        self.assert_rejected()

    def test_manifest_digest_inconsistency_is_not_matching(self):
        changed = json.loads(self.receipt.read_bytes())
        changed["staged_workspace_digest"] = "0" * 64
        self.write_receipt(changed)
        self.assert_rejected()

    def test_proposal_corruption_is_rejected_without_echoing_candidate(self):
        record = json.loads(self.proposal.read_bytes())
        record["candidate"]["files"][0]["content"] = "private replacement\n"
        self.proposal.write_bytes(json_bytes(record))
        self.assert_rejected()

    def test_budgets_bound_actual_files_entries_depth_and_total_bytes(self):
        for name, limit in (("MAX_FILES", 1), ("MAX_ENTRIES", 1), ("MAX_DEPTH", 0),
                            ("MAX_COPY_BYTES", 1), ("MAX_FILE_BYTES", 1)):
            with self.subTest(name=name), patch.object(inspection, name, limit):
                self.assert_rejected()

    def test_storage_and_included_links_never_read_external_content(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        private = outside / "private.txt"
        private.write_bytes(b"never disclosed")
        link = self.copied / "external"
        try: link.symlink_to(private)
        except OSError: self.skipTest("Symlinks unavailable")
        self.assert_rejected()
        link.unlink()
        self.receipt.rename(self.owned / "saved.json")
        self.receipt.symlink_to(private)
        self.assert_rejected()
        self.assertEqual(private.read_bytes(), b"never disclosed")

    def test_stage_directory_link_is_rejected(self):
        saved = self.owned.with_name("saved-stage")
        self.owned.rename(saved)
        try: self.owned.symlink_to(saved, target_is_directory=True)
        except OSError: self.skipTest("Symlinks unavailable")
        self.assert_rejected()

    def test_hard_linked_included_file_is_rejected(self):
        try: os.link(self.root / "notes.txt", self.copied / "extra-link.txt")
        except OSError: self.skipTest("Hard links unavailable")
        self.assert_rejected()

    def test_hard_linked_control_evidence_is_rejected(self):
        for index, path in enumerate((self.receipt, self.intent, self.proposal)):
            link = Path(self.temp.name) / ("control-link-" + str(index))
            try: os.link(path, link)
            except OSError: self.skipTest("Hard links unavailable")
            self.assert_rejected()
            link.unlink()

    def test_workspace_directory_link_is_rejected(self):
        saved = self.owned / "saved-workspace"
        self.copied.rename(saved)
        try: self.copied.symlink_to(saved, target_is_directory=True)
        except OSError: self.skipTest("Symlinks unavailable")
        self.assert_rejected()

    def test_case_colliding_extra_file_is_rejected_when_supported(self):
        extra = self.copied / "NOTES.TXT"
        extra.write_bytes(b"extra\n")
        if len([p for p in self.copied.iterdir() if p.name.casefold() == "notes.txt"]) < 2:
            self.skipTest("Case-sensitive filesystem required")
        self.assert_rejected()

    @unittest.skipIf(os.name == "nt", "POSIX FIFO required")
    def test_fifo_is_rejected_without_blocking(self):
        os.mkfifo(self.copied / "pipe")
        self.assert_rejected()

    def test_unreadable_tree_fails_instead_of_silently_omitting_files(self):
        with patch.object(inspection.os, "scandir", side_effect=PermissionError("private filesystem detail")):
            self.assert_rejected()

    def test_concurrent_copy_change_between_scans_is_rejected(self):
        scan = inspection._scan
        calls = 0
        def changing(root):
            nonlocal calls
            result = scan(root)
            calls += 1
            if calls == 1: (root / "notes.txt").write_bytes(b"later change\n")
            return result
        with patch.object(inspection, "_scan", side_effect=changing): self.assert_rejected()

    def test_concurrent_control_change_is_rejected(self):
        scan = inspection._scan
        def changing(root):
            result = scan(root)
            self.intent.write_bytes(self.intent.read_bytes() + b" ")
            return result
        with patch.object(inspection, "_scan", side_effect=changing): self.assert_rejected()

    def test_concurrent_receipt_change_is_rejected(self):
        scan = inspection._scan
        def changing(root):
            result = scan(root)
            self.receipt.write_bytes(self.receipt.read_bytes() + b" ")
            return result
        with patch.object(inspection, "_scan", side_effect=changing): self.assert_rejected()

    def test_included_subdirectory_identity_change_is_rejected(self):
        original = inspection._directory
        calls = 0
        def changing(path):
            nonlocal calls
            result = original(path)
            if path == self.copied / "src":
                calls += 1
                if calls == 2: return result[0], result[1] + 1
            return result
        with patch.object(inspection, "_directory", side_effect=changing): self.assert_rejected()

    def test_receipt_appearing_during_incomplete_inspection_is_rejected(self):
        raw = self.receipt.read_bytes()
        self.receipt.unlink()
        original = inspection._proposal
        calls = 0
        def appearing(*args):
            nonlocal calls
            record = original(*args)
            calls += 1
            if calls == 2: self.receipt.write_bytes(raw)
            return record
        with patch.object(inspection, "_proposal", side_effect=appearing): self.assert_rejected()


if __name__ == "__main__":
    unittest.main()
