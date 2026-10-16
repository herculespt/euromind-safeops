"""Staging copies: exact confirmation, independent bytes and retained failures."""
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

from euromind_safeops import staging
from euromind_safeops.cli import main
from euromind_safeops.core import SafeOpsError, json_bytes, sha256, tree_digest
from euromind_safeops.planning import create_plan
from euromind_safeops.proposals import create_proposal


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "project"
        (self.root / "src").mkdir(parents=True)
        self.source = self.root / "src" / "hello.py"
        self.source.write_bytes('greeting = "Olá"\n'.encode())
        self.other = self.root / "notes.txt"
        self.other.write_bytes(b"Unchanged\n")
        self.init(self.root)
        self.prepare()

    def init(self, root):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--root", str(root), "init"]), 0)

    def prepare(self):
        self.plan = create_plan(self.root, "Improve greeting documentation", ["src/hello.py"], "Local", "offline")
        self.candidate = self.base / "candidate.json"
        self.candidate.write_bytes(json_bytes({"schema": 1, "files": [{"path": "src/hello.py",
            "base_sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
            "content": 'greeting = "Portugal"\n'}]}))
        self.proposal = create_proposal(self.root, self.plan["id"], self.candidate)

    def stage(self):
        return staging.stage_proposal(self.root, self.proposal["proposal_id"], self.proposal["fingerprint"])

    def stages(self):
        return self.root / ".safeops" / "stages"

    def test_stage_changes_only_new_copy_and_binds_receipt(self):
        before = tree_digest(self.root)
        original = self.source.read_bytes()
        result = self.stage()
        copied = Path(result["workspace"])
        self.assertEqual(result["status"], "staged")
        self.assertEqual((copied / "src/hello.py").read_bytes(), b'greeting = "Portugal"\n')
        self.assertEqual((copied / "notes.txt").read_bytes(), self.other.read_bytes())
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(tree_digest(self.root), before)
        self.assertFalse((copied / ".safeops").exists())
        record = json.loads((copied.parent / "receipt.json").read_bytes())
        fingerprint = record.pop("fingerprint")
        self.assertEqual(fingerprint, sha256(record))
        self.assertEqual(result["receipt_fingerprint"], fingerprint)
        self.assertEqual(record["staged_workspace_digest"], tree_digest(copied))
        self.assertEqual(record["source_workspace_digest"], before)
        self.assertEqual(record["proposal_fingerprint"], self.proposal["fingerprint"])
        self.assertEqual(sum(x["bytes"] for x in record["files"]), result["copied_bytes"])
        self.assertEqual([x["path"] for x in record["files"] if x["replaced"]], ["src/hello.py"])
        events = [json.loads(x) for x in (self.root / ".safeops/audit.jsonl").read_text().splitlines()]
        self.assertEqual(events[-1]["action"], "stage-proposal")
        self.assertEqual(list((self.root / ".safeops/approvals").iterdir()), [])

    def test_copied_files_are_independent_from_original(self):
        copied = Path(self.stage()["workspace"])
        (copied / "notes.txt").write_bytes(b"Changed in copy\n")
        self.assertEqual(self.other.read_bytes(), b"Unchanged\n")
        self.other.write_bytes(b"Changed in original\n")
        self.assertEqual((copied / "notes.txt").read_bytes(), b"Changed in copy\n")

    def test_cli_json_has_no_provider_or_execution_call(self):
        out = io.StringIO()
        with patch("euromind_safeops.cli.remote_advice") as remote, patch("subprocess.run") as run:
            with contextlib.redirect_stdout(out):
                code = main(["--root", str(self.root), "--json", "stage-proposal", self.proposal["proposal_id"], "--confirm", self.proposal["fingerprint"]])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out.getvalue())["command"], "stage-proposal")
            self.assertNotIn('greeting =', out.getvalue())
            remote.assert_not_called()
            run.assert_not_called()

    def test_wrong_confirmation_creates_no_stage(self):
        for value in (self.proposal["proposal_id"], "0" * 64, ""):
            with self.assertRaisesRegex(SafeOpsError, "exact reviewed"):
                staging.stage_proposal(self.root, self.proposal["proposal_id"], value)
        self.assertFalse(self.stages().exists())

    def test_source_change_rejected_before_creation(self):
        self.other.write_bytes(b"Changed\n")
        with self.assertRaisesRegex(SafeOpsError, "Workspace changed"): self.stage()
        self.assertFalse(self.stages().exists())

    def test_environment_generated_git_and_original_state_omitted(self):
        (self.root / ".env").write_bytes(b"LOCAL_VALUE=example\n")
        (self.root / "src/.env.sample").write_bytes(b"VALUE=example\n")
        (self.root / "src/.ENV.sample").write_bytes(b"VALUE=example\n")
        (self.root / ".git").write_bytes(b"gitdir: local-metadata\n")
        (self.root / "build").mkdir()
        (self.root / "build/output").write_bytes(b"generated")
        (self.root / ".venv").mkdir()
        (self.root / ".venv/tool").write_bytes(b"environment")
        self.prepare()
        copied = Path(self.stage()["workspace"])
        for name in (".env", "src/.env.sample", "src/.ENV.sample", ".git", "build", ".venv", ".safeops"):
            self.assertFalse((copied / name).exists(), name)

    def test_existing_stage_collision_preserves_contents(self):
        result = self.stage()
        receipt = self.stages() / result["stage_id"] / "receipt.json"
        before = receipt.read_bytes()
        with patch.object(staging.secrets, "token_hex", return_value=result["stage_id"]):
            with self.assertRaises(FileExistsError): self.stage()
        self.assertEqual(receipt.read_bytes(), before)

    def test_non_directory_storage_rejected(self):
        self.stages().write_bytes(b"blocked")
        with self.assertRaises(OSError): self.stage()
        self.assertEqual(self.stages().read_bytes(), b"blocked")

    def test_symlink_storage_rejected_without_external_writes(self):
        external = self.base / "external"
        external.mkdir()
        try: self.stages().symlink_to(external, target_is_directory=True)
        except OSError: self.skipTest("Symlinks unavailable")
        with self.assertRaisesRegex(SafeOpsError, "directories"): self.stage()
        self.assertEqual(list(external.iterdir()), [])

    def test_output_budget_failure_retains_incomplete_stage_and_original(self):
        before = self.source.read_bytes()
        with patch.object(staging, "MAX_COPY_BYTES", 1):
            with self.assertRaisesRegex(SafeOpsError, "retained local stage"): self.stage()
        stage, = self.stages().iterdir()
        self.assertTrue((stage / "intent.json").is_file())
        self.assertFalse((stage / "receipt.json").exists())
        self.assertEqual(self.source.read_bytes(), before)

    def test_receipt_budget_failure_never_marks_ready(self):
        with patch.object(staging, "MAX_RECEIPT_BYTES", 1):
            with self.assertRaises(SafeOpsError): self.stage()
        stage, = self.stages().iterdir()
        self.assertFalse((stage / "receipt.json").exists())
        self.assertTrue((stage / "workspace/src/hello.py").is_file())

    def test_copy_io_failure_is_sanitized_in_cli_and_retained(self):
        out = io.StringIO()
        with patch.object(staging, "_write_new", side_effect=OSError("PRIVATE-DETAIL")):
            with contextlib.redirect_stdout(out):
                code = main(["--root", str(self.root), "--json", "stage-proposal", self.proposal["proposal_id"], "--confirm", self.proposal["fingerprint"]])
        self.assertEqual(code, 2)
        self.assertNotIn("PRIVATE-DETAIL", out.getvalue())
        self.assertIsNone(json.loads(out.getvalue())["data"])
        self.assertEqual(len(list(self.stages().iterdir())), 1)

    def test_source_changed_during_copy_fails_final_review(self):
        original = staging._write_new
        def changing(*args):
            original(*args)
            self.other.write_bytes(b"Concurrent change\n")
        with patch.object(staging, "_write_new", side_effect=changing):
            with self.assertRaises(SafeOpsError): self.stage()
        stage, = self.stages().iterdir()
        self.assertFalse((stage / "receipt.json").exists())

    def test_changed_copy_detected_before_receipt(self):
        original = staging._write_new
        def changing(root, relative, raw):
            original(root, relative, raw)
            (root / relative).write_bytes(b"Concurrent change\n")
        with patch.object(staging, "_write_new", side_effect=changing):
            with self.assertRaises(SafeOpsError): self.stage()
        stage, = self.stages().iterdir()
        self.assertFalse((stage / "receipt.json").exists())

    def test_proposal_changed_after_review_rejected(self):
        original = staging._load
        def changed(*args):
            record = original(*args)
            record["fingerprint"] = "0" * 64
            return record
        with patch.object(staging, "_load", side_effect=changed):
            with self.assertRaisesRegex(SafeOpsError, "changed since review"): self.stage()
        self.assertFalse(self.stages().exists())

    def test_missing_proposed_file_never_creates_receipt(self):
        original = staging.source_files
        def missing(root):
            return (p for p in original(root) if p.name != "hello.py")
        with patch.object(staging, "source_files", side_effect=missing):
            with self.assertRaises(SafeOpsError): self.stage()
        stage, = self.stages().iterdir()
        self.assertFalse((stage / "receipt.json").exists())

    def test_audit_failure_retains_ready_receipt_but_returns_failure(self):
        with patch.object(staging, "audit", side_effect=OSError("audit unavailable")):
            with self.assertRaises(SafeOpsError): self.stage()
        stage, = self.stages().iterdir()
        self.assertEqual(json.loads((stage / "receipt.json").read_bytes())["status"], "staged")
        self.assertEqual(list((self.root / ".safeops/approvals").iterdir()), [])

    def test_empty_replacement_is_materialized_as_existing_empty_file(self):
        doc = json.loads(self.candidate.read_bytes())
        doc["files"][0]["content"] = ""
        self.candidate.write_bytes(json_bytes(doc))
        self.proposal = create_proposal(self.root, self.plan["id"], self.candidate)
        copied = Path(self.stage()["workspace"])
        self.assertTrue((copied / "src/hello.py").is_file())
        self.assertEqual((copied / "src/hello.py").read_bytes(), b"")

    def test_staged_code_requires_and_passes_independent_fresh_check_approval(self):
        tests = self.root / "tests"
        tests.mkdir()
        (tests / "test_greeting.py").write_text(
            "import unittest\nfrom pathlib import Path\n"
            "class Greeting(unittest.TestCase):\n"
            " def test_candidate(self):\n"
            "  text = (Path(__file__).resolve().parents[1] / 'src/hello.py').read_text(encoding='utf-8')\n"
            "  self.assertIn('Portugal', text)\n", encoding="utf-8")
        self.prepare()
        before = tree_digest(self.root)
        copied = Path(self.stage()["workspace"])
        def call(*args):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main(["--root", str(copied), "--json", *args])
            return code, json.loads(out.getvalue())["data"]
        self.assertEqual(call("init")[0], 0)
        code, plan = call("plan", "Validate trusted candidate checks")
        self.assertEqual(code, 0)
        self.assertEqual(call("run", plan["id"])[0], 2)
        self.assertEqual(call("review", plan["id"])[0], 0)
        self.assertEqual(call("approve", plan["id"], "--confirm", plan["id"], "--reason", "Reviewed staged code and trusted tests")[0], 0)
        code, result = call("run", plan["id"])
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "passed")
        self.assertEqual([x["check"] for x in result["checks"]], ["compile", "unit-tests"])
        self.assertEqual(tree_digest(self.root), before)
        self.assertEqual(list((self.root / ".safeops/approvals").iterdir()), [])

    def test_changed_final_proposal_fingerprint_leaves_no_receipt(self):
        original = staging.review_proposal
        calls = 0
        def changed(*args):
            nonlocal calls
            calls += 1
            result = original(*args)
            if calls == 2:
                result["fingerprint"] = "0" * 64
            return result
        with patch.object(staging, "review_proposal", side_effect=changed):
            with self.assertRaises(SafeOpsError): self.stage()
        stage, = self.stages().iterdir()
        self.assertFalse((stage / "receipt.json").exists())

    @unittest.skipIf(os.name == "nt", "POSIX permission modes required")
    def test_private_modes_and_no_hard_link(self):
        copied = Path(self.stage()["workspace"])
        self.assertEqual(stat.S_IMODE(copied.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((copied / "notes.txt").stat().st_mode), 0o600)
        self.assertNotEqual((copied / "notes.txt").stat().st_ino, self.other.stat().st_ino)


if __name__ == "__main__":
    unittest.main()
