"""Plan-bound local proposals: lifecycle, privacy and fail-closed bindings."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from euromind_safeops import proposals
from euromind_safeops.cli import main
from euromind_safeops.core import SafeOpsError, json_bytes, sha256
from euromind_safeops.planning import create_plan


class ProposalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "project"
        self.root.mkdir()
        self.source = self.root / "hello.txt"
        self.source.write_bytes("Olá\nworld\n".encode())
        self.doc = {"schema": 1, "files": [{"path": "hello.txt",
                    "base_sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
                    "content": "Olá\nPortugal\n"}]}
        self.candidate = self.base / "candidate.json"
        self.candidate.write_bytes(json_bytes(self.doc))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--root", str(self.root), "init"]), 0)
        self.plan = self.plan_for(["hello.txt"])

    def plan_for(self, paths, task="Improve documentation"):
        return create_plan(self.root, task, paths, "Local advice", "offline")

    def create(self):
        return proposals.create_proposal(self.root, self.plan["id"], self.candidate)

    def location(self, result):
        return self.root / ".safeops" / "proposals" / (result["proposal_id"] + ".json")

    def mutate(self, result, change, *, rehash=False):
        path = self.location(result)
        record = json.loads(path.read_bytes())
        change(record)
        if rehash:
            record.pop("fingerprint")
            record["fingerprint"] = sha256(record)
        path.write_bytes(json_bytes(record))

    def test_create_and_review_exact_diff_without_source_or_approval_writes(self):
        original = self.source.read_bytes()
        result = self.create()
        self.assertEqual(result["status"], "proposal-recorded")
        self.assertNotIn("Portugal", json.dumps(result))
        audit = self.root / ".safeops" / "audit.jsonl"
        before_review = audit.read_bytes()
        record_before = self.location(result).read_bytes()
        reviewed = proposals.review_proposal(self.root, result["proposal_id"])
        self.assertEqual(reviewed["status"], "proposal-reviewed")
        self.assertEqual(reviewed["fingerprint"], result["fingerprint"])
        self.assertEqual(reviewed["candidate_sha256"], sha256(self.doc))
        self.assertIn("-world\n+Portugal\n", reviewed["files"][0]["diff"])
        self.assertEqual(audit.read_bytes(), before_review)
        self.assertEqual(self.location(result).read_bytes(), record_before)
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(list((self.root / ".safeops" / "approvals").iterdir()), [])
        self.assertEqual(json.loads(before_review)["action"], "propose")

    def test_cli_json_lifecycle_has_no_provider_or_command_execution(self):
        out = io.StringIO()
        with patch("euromind_safeops.cli.remote_advice") as remote, patch("subprocess.run") as run:
            with contextlib.redirect_stdout(out):
                self.assertEqual(main(["--root", str(self.root), "--json", "propose", self.plan["id"], str(self.candidate)]), 0)
            created = json.loads(out.getvalue())
            self.assertEqual(created["command"], "propose")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(main(["--root", str(self.root), "--json", "review-proposal", created["data"]["proposal_id"]]), 0)
            self.assertEqual(json.loads(out.getvalue())["command"], "review-proposal")
            remote.assert_not_called()
            run.assert_not_called()

    def test_external_candidate_is_not_needed_after_creation(self):
        result = self.create()
        self.candidate.unlink()
        self.assertEqual(proposals.review_proposal(self.root, result["proposal_id"])["candidate_sha256"], sha256(self.doc))

    def test_unrelated_source_edit_invalidates_create_and_review(self):
        result = self.create()
        (self.root / "unrelated.txt").write_bytes(b"new\n")
        for call in (self.create, lambda: proposals.review_proposal(self.root, result["proposal_id"])):
            with self.assertRaisesRegex(SafeOpsError, "Workspace changed"): call()
        self.assertEqual(len(list(self.location(result).parent.iterdir())), 1)

    def test_missing_or_directory_only_plan_scope_is_not_implicit_authority(self):
        for paths in ([], ["folder"]):
            self.plan = self.plan_for(paths)
            with self.assertRaises(SafeOpsError): self.create()
        self.assertFalse((self.root / ".safeops" / "proposals").exists())

    def test_out_of_plan_candidate_is_rejected(self):
        self.plan = self.plan_for(["other.txt"])
        with self.assertRaisesRegex(SafeOpsError, "exactly match"): self.create()

    def test_critical_plan_is_rejected(self):
        self.plan = self.plan_for(["hello.txt"], "Deploy production")
        with self.assertRaisesRegex(SafeOpsError, "Critical"): self.create()

    def test_configuration_change_invalidates_record(self):
        result = self.create()
        (self.root / ".safeops" / "config.json").write_bytes(json_bytes({"schema": 1, "checks": ["unit-tests"]}))
        with self.assertRaisesRegex(SafeOpsError, "bindings are stale"):
            proposals.review_proposal(self.root, result["proposal_id"])

    def test_selected_generated_files_are_bound_in_schema_two(self):
        (self.root / "src" / "build").mkdir(parents=True)
        generated = self.root / "src" / "build" / "generated.py"
        generated.write_bytes(b"x = 1\n")
        (self.root / ".safeops" / "config.json").write_bytes(json_bytes({"schema": 2, "checks": ["compile"], "targets": {"compile": ["src"]}}))
        self.plan = self.plan_for(["hello.txt"])
        result = self.create()
        generated.write_bytes(b"x = 2\n")
        with self.assertRaisesRegex(SafeOpsError, "bindings are stale"):
            proposals.review_proposal(self.root, result["proposal_id"])

    def test_execution_contract_change_invalidates_record(self):
        result = self.create()
        with patch.object(proposals, "execution_contract_digest", return_value="f" * 64):
            with self.assertRaisesRegex(SafeOpsError, "bindings are stale"):
                proposals.review_proposal(self.root, result["proposal_id"])

    def test_package_version_change_invalidates_record(self):
        result = self.create()
        with patch.object(proposals, "__version__", "99.0.0"):
            with self.assertRaisesRegex(SafeOpsError, "bindings are stale"):
                proposals.review_proposal(self.root, result["proposal_id"])

    def test_changed_plan_fingerprint_invalidates_record(self):
        result = self.create()
        path = self.root / ".safeops" / "plans" / (self.plan["id"] + ".json")
        plan = json.loads(path.read_bytes())
        plan.pop("fingerprint")
        plan["advice"] = "Updated local advice"
        plan["fingerprint"] = sha256(plan)
        path.write_bytes(json_bytes(plan))
        with self.assertRaisesRegex(SafeOpsError, "bindings are stale"):
            proposals.review_proposal(self.root, result["proposal_id"])

    def test_tampering_candidate_or_fingerprint_fails(self):
        for change in (lambda r: r["candidate"]["files"][0].update(content="tampered\n"),
                       lambda r: r.update(fingerprint="0" * 64), lambda r: r.update(candidate_sha256="0" * 64)):
            result = self.create()
            self.mutate(result, change)
            with self.assertRaisesRegex(SafeOpsError, "integrity"):
                proposals.review_proposal(self.root, result["proposal_id"])

    def test_rehashed_invalid_schema_and_record_fields_fail(self):
        for key, value in (("schema", True), ("schema", 2), ("id", "0" * 12), ("created_at", "bad"),
                           ("created_at", "2026-99-99T00:00:00+00:00"), ("candidate", []), ("bindings", [])):
            result = self.create()
            self.mutate(result, lambda r: r.update({key: value}), rehash=True)
            with self.assertRaisesRegex(SafeOpsError, "integrity"):
                proposals.review_proposal(self.root, result["proposal_id"])

    def test_unknown_record_or_binding_keys_fail(self):
        result = self.create()
        self.mutate(result, lambda r: r.update(extra=True), rehash=True)
        with self.assertRaisesRegex(SafeOpsError, "integrity"):
            proposals.review_proposal(self.root, result["proposal_id"])
        result = self.create()
        self.mutate(result, lambda r: r["bindings"].update(extra=True), rehash=True)
        with self.assertRaisesRegex(SafeOpsError, "stale"):
            proposals.review_proposal(self.root, result["proposal_id"])

    def test_invalid_plan_binding_is_controlled(self):
        for value in (None, [], "../private"):
            result = self.create()
            self.mutate(result, lambda r: r["bindings"].update(plan_id=value), rehash=True)
            with self.assertRaisesRegex(SafeOpsError, "plan binding"):
                proposals.review_proposal(self.root, result["proposal_id"])

    def test_bad_record_json_and_oversize_fail_without_echoing_content(self):
        result = self.create()
        for raw in (b'PRIVATE-INVALID', b'{"schema":1,"schema":1}', b'[]', b'\xff', b" " * (proposals.MAX_RECORD_BYTES + 1)):
            self.location(result).write_bytes(raw)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(main(["--root", str(self.root), "--json", "review-proposal", result["proposal_id"]]), 2)
            self.assertIsNone(json.loads(out.getvalue())["data"])
            self.assertNotIn("PRIVATE-INVALID", out.getvalue())

    def test_invalid_or_missing_proposal_id_is_controlled(self):
        for value in ("../x", "UPPERCASE123", "0" * 12):
            with self.assertRaises(SafeOpsError): proposals.review_proposal(self.root, value)

    def test_storage_directory_and_record_symlinks_rejected(self):
        result = self.create()
        location = self.location(result)
        external = self.base / "record.json"
        location.rename(external)
        try: location.symlink_to(external)
        except OSError: self.skipTest("Symlinks unavailable")
        with self.assertRaises(SafeOpsError): proposals.review_proposal(self.root, result["proposal_id"])
        location.unlink()
        location.parent.rmdir()
        location.parent.symlink_to(self.base, target_is_directory=True)
        with self.assertRaises(SafeOpsError): self.create()
        self.assertFalse((self.base / (result["proposal_id"] + ".json")).exists())

    def test_non_directory_storage_rejected(self):
        (self.root / ".safeops" / "proposals").write_bytes(b"blocked")
        with self.assertRaisesRegex(SafeOpsError, "storage"): self.create()

    def test_concurrent_configuration_change_before_persistence_is_rejected(self):
        original = proposals._validate_candidate
        def changing(*args):
            result = original(*args)
            (self.root / ".safeops" / "config.json").write_bytes(json_bytes({"schema": 1, "checks": ["compile"]}))
            return result
        with patch.object(proposals, "_validate_candidate", side_effect=changing):
            with self.assertRaisesRegex(SafeOpsError, "context changed"): self.create()
        self.assertFalse((self.root / ".safeops" / "proposals").exists())

    def test_concurrent_configuration_change_during_review_is_rejected(self):
        result = self.create()
        original = proposals._validate_candidate
        def changing(*args):
            value = original(*args)
            (self.root / ".safeops" / "config.json").write_bytes(json_bytes({"schema": 1, "checks": ["compile"]}))
            return value
        with patch.object(proposals, "_validate_candidate", side_effect=changing):
            with self.assertRaisesRegex(SafeOpsError, "context changed"):
                proposals.review_proposal(self.root, result["proposal_id"])

    def test_candidate_size_budget_prevents_record_creation(self):
        with patch.object(proposals, "MAX_BYTES", 1):
            with self.assertRaisesRegex(SafeOpsError, "Canonical candidate"): self.create()
        self.assertFalse((self.root / ".safeops" / "proposals").exists())

    def test_record_collision_preserves_existing_bytes(self):
        result = self.create()
        before = self.location(result).read_bytes()
        with patch.object(proposals.secrets, "token_hex", return_value=result["proposal_id"]):
            with self.assertRaisesRegex(SafeOpsError, "Already exists"): self.create()
        self.assertEqual(self.location(result).read_bytes(), before)

    def test_rehashed_candidate_still_requires_full_preview_validation(self):
        result = self.create()
        def invalidate(record):
            record["candidate"]["files"][0]["content"] = "not LF terminated"
            record["candidate_sha256"] = sha256(record["candidate"])
        self.mutate(result, invalidate, rehash=True)
        with self.assertRaisesRegex(SafeOpsError, "final newline"):
            proposals.review_proposal(self.root, result["proposal_id"])

    def test_audit_failure_retains_record_without_granting_approval(self):
        with patch.object(proposals, "audit", side_effect=OSError("unavailable")):
            with self.assertRaises(OSError): self.create()
        records = list((self.root / ".safeops" / "proposals").glob("*.json"))
        self.assertEqual(len(records), 1)
        self.assertEqual(proposals.review_proposal(self.root, records[0].stem)["status"], "proposal-reviewed")
        self.assertEqual(list((self.root / ".safeops" / "approvals").iterdir()), [])

    @unittest.skipIf(os.name == "nt", "POSIX permission modes required")
    def test_private_record_permissions(self):
        result = self.create()
        self.assertEqual(stat.S_IMODE(self.location(result).stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.location(result).parent.stat().st_mode), 0o700)


if __name__ == "__main__":
    unittest.main()
