"""Local native-lock regressions; all mutation is confined to temporary fixtures."""

import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from euromind_safeops.cli import main
from euromind_safeops.core import SafeOpsError, atomic_json_write
from euromind_safeops.execution import approve, run
from euromind_safeops.locking import GuardBusy, execution_lock, lock_status, recover_lock
from euromind_safeops.locking import _native_lock
from euromind_safeops.planning import create_plan


class LockingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.state = self.root / ".safeops"
        self.marker = self.state / "run.lock"
        self.guard = self.state / "run.guard"
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "src" / "demo.py").write_text("value = 1\n", encoding="utf-8")
        self.source = self.root / "tests" / "test_demo.py"
        self.source.write_text("import unittest\nclass T(unittest.TestCase):\n def test_it(self): pass\n", encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--root", str(self.root), "init"]), 0)

    def approved(self):
        plan = create_plan(self.root, "Review documentation", [], "offline", "offline")
        approve(self.root, plan["id"], "Reviewed trusted fixture", plan["id"])
        return plan["id"]

    def recover(self, **overrides):
        arguments = {"confirmation": lock_status(self.root)["marker_fingerprint"],
                     "reason": "Verifiquei que os processos de teste terminaram", "acknowledged": True}
        arguments.update(overrides)
        return recover_lock(self.root, **arguments)

    def child(self, arguments):
        process = subprocess.Popen([sys.executable, *arguments], cwd=self.root, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
                                   env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        def cleanup():
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=10)
        self.addCleanup(cleanup)
        return process

    def wait_ready(self, process, name):
        deadline = time.monotonic() + 15
        while not (self.state / name).exists():
            if process.poll() is not None:
                self.fail("Fixture process exited before readiness: " + process.communicate(timeout=5)[1])
            if time.monotonic() > deadline:
                self.fail("Fixture process did not become ready")
            time.sleep(0.02)

    def holder(self):
        script = ("from pathlib import Path\nimport sys\n"
                  "from euromind_safeops.locking import execution_lock\n"
                  "with execution_lock(Path.cwd(), 'aaaaaaaaaaaa'):\n"
                  " Path('.safeops/holder-ready').touch()\n"
                  " sys.stdin.read(1)\n")
        process = self.child(["-c", script])
        self.wait_ready(process, "holder-ready")
        return process

    def test_clear_diagnostics_create_no_files(self):
        before = sorted(path.name for path in self.state.iterdir())
        status = lock_status(self.root)
        self.assertEqual(status["guard"], "absent")
        self.assertFalse(status["marker_present"])
        self.assertEqual(before, sorted(path.name for path in self.state.iterdir()))

    def test_owned_marker_and_persistent_guard_lifecycle(self):
        with execution_lock(self.root, "aaaaaaaaaaaa"):
            record = json.loads(self.marker.read_text(encoding="utf-8"))
            self.assertEqual(record["pid"], os.getpid())
            self.assertEqual(record["schema"], 1)
            self.assertEqual(len(record["token"]), 32)
            identity = self.guard.stat().st_ino
        self.assertFalse(self.marker.exists())
        self.assertEqual(self.guard.stat().st_size, 0)
        self.assertEqual(lock_status(self.root)["guard"], "free")
        with execution_lock(self.root, "bbbbbbbbbbbb"):
            self.assertEqual(self.guard.stat().st_ino, identity)

    def test_body_error_releases_only_own_marker(self):
        with self.assertRaisesRegex(RuntimeError, "fixture"):
            with execution_lock(self.root, "aaaaaaaaaaaa"):
                raise RuntimeError("fixture")
        self.assertFalse(self.marker.exists())
        self.assertEqual(lock_status(self.root)["guard"], "free")

    def test_native_guard_descriptor_is_not_inheritable(self):
        observed = []
        def inspect_descriptor(fd, **arguments):
            observed.append(os.get_inheritable(fd))
            return _native_lock(fd, **arguments)
        with patch("euromind_safeops.locking._native_lock", side_effect=inspect_descriptor):
            with execution_lock(self.root, "aaaaaaaaaaaa"):
                pass
        self.assertEqual(observed, [False, False])

    def test_replaced_marker_is_retained(self):
        with self.assertRaisesRegex(SafeOpsError, "cleanup refused"):
            with execution_lock(self.root, "aaaaaaaaaaaa"):
                self.marker.write_bytes(b"replacement")
        self.assertEqual(self.marker.read_bytes(), b"replacement")
        self.assertEqual(lock_status(self.root)["guard"], "free")

    def test_missing_marker_is_not_silently_accepted(self):
        with self.assertRaisesRegex(SafeOpsError, "cleanup refused"):
            with execution_lock(self.root, "aaaaaaaaaaaa"):
                self.marker.unlink()
        self.assertTrue(self.guard.exists())

    def test_existing_legacy_marker_blocks_without_mutation(self):
        plan_id = self.approved()
        self.marker.write_bytes(b"123\n")
        with patch("euromind_safeops.execution.subprocess.run") as child:
            with self.assertRaisesRegex(SafeOpsError, "marker exists"):
                run(self.root, plan_id)
            child.assert_not_called()
        self.assertEqual(self.marker.read_bytes(), b"123\n")
        status = lock_status(self.root)
        self.assertEqual(status["marker_format"], "legacy-pid")
        self.assertEqual(status["owner_pid"], 123)

    def test_native_guard_and_recovery_reject_a_live_other_process(self):
        process = self.holder()
        original = self.marker.read_bytes()
        status = lock_status(self.root)
        self.assertEqual(status["guard"], "busy")
        self.assertEqual(status["marker_format"], "record-v1")
        with self.assertRaises(GuardBusy):
            with execution_lock(self.root, "bbbbbbbbbbbb"):
                self.fail("Concurrent operation entered")
        with self.assertRaises(GuardBusy):
            self.recover()
        self.assertEqual(self.marker.read_bytes(), original)
        self.assertEqual(process.communicate(input="x", timeout=10)[1], "")
        self.assertEqual(process.returncode, 0)
        self.assertFalse(self.marker.exists())

    def test_actual_approved_run_excludes_a_second_run(self):
        self.source.write_text(
            "import unittest,time\nfrom pathlib import Path\nclass T(unittest.TestCase):\n"
            " def test_it(self):\n  Path('.safeops/check-ready').touch()\n"
            "  deadline=time.monotonic()+15\n"
            "  while not Path('.safeops/release').exists() and time.monotonic()<deadline: time.sleep(0.02)\n"
            "  self.assertTrue(Path('.safeops/release').exists())\n", encoding="utf-8")
        plan_id = self.approved()
        arguments = ["-m", "euromind_safeops", "--json", "--root", str(self.root), "run", plan_id]
        first = self.child(arguments)
        self.addCleanup(lambda: (self.state / "release").touch())
        self.wait_ready(first, "check-ready")
        original = self.marker.read_bytes()
        second = subprocess.run([sys.executable, *arguments], cwd=self.root, capture_output=True,
                                text=True, encoding="utf-8", timeout=10)
        self.assertEqual(second.returncode, 2)
        self.assertIn("guard is busy", json.loads(second.stdout)["error"]["message"])
        self.assertEqual(self.marker.read_bytes(), original)
        (self.state / "release").touch()
        output, errors = first.communicate(timeout=10)
        self.assertEqual(first.returncode, 0, errors)
        self.assertEqual(json.loads(output)["data"]["status"], "passed")
        self.assertFalse(self.marker.exists())

    def test_abrupt_death_releases_native_guard_but_retains_marker(self):
        process = self.holder()
        original = self.marker.read_bytes()
        process.kill()
        process.communicate(timeout=10)
        status = lock_status(self.root)
        self.assertEqual(status["guard"], "free")
        self.assertTrue(status["marker_present"])
        with self.assertRaises(SafeOpsError):
            with execution_lock(self.root, "bbbbbbbbbbbb"):
                self.fail("Retained marker bypassed")
        result = self.recover()
        self.assertEqual((self.root / result["archive"]).read_bytes(), original)
        self.assertFalse(self.marker.exists())
        self.assertEqual(run(self.root, self.approved())["status"], "passed")

    def test_recovery_preserves_marker_receipt_and_plan_history(self):
        self.approved()
        history = {path.relative_to(self.state).as_posix(): path.read_bytes()
                   for group in ("plans", "approvals") for path in (self.state / group).iterdir()}
        self.marker.write_bytes(b"123\n")
        result = self.recover()
        self.assertEqual(result["status"], "recovered")
        self.assertEqual((self.root / result["archive"]).read_bytes(), b"123\n")
        receipt = json.loads((self.root / result["receipt"]).read_text(encoding="utf-8"))
        self.assertTrue(receipt["no_running_checks_confirmed"])
        self.assertIn("Verifiquei", receipt["reason"])
        self.assertEqual(receipt["marker_fingerprint"], hashlib.sha256(b"123\n").hexdigest())
        for name, contents in history.items():
            self.assertEqual((self.state / name).read_bytes(), contents)
        events = [json.loads(line) for line in (self.state / "audit.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(events[-1]["action"], "recover-lock")

    def test_recovery_requires_all_explicit_inputs(self):
        self.marker.write_bytes(b"123")
        for arguments in ({"acknowledged": False}, {"acknowledged": 1}, {"confirmation": "0" * 64},
                          {"confirmation": "bad"}, {"reason": " "}, {"reason": "x" * 501},
                          {"reason": "\ud800"}):
            with self.subTest(arguments=arguments):
                with self.assertRaises(SafeOpsError):
                    self.recover(**arguments)
                self.assertEqual(self.marker.read_bytes(), b"123")
        self.assertFalse((self.state / "recovered-locks").exists())

    def test_recovery_without_marker_cannot_grant_approval(self):
        with self.assertRaises(SafeOpsError):
            recover_lock(self.root, "0" * 64, "reviewed", True)
        self.assertFalse(list((self.state / "approvals").iterdir()))

    def test_unknown_marker_bytes_are_not_disclosed_and_can_be_archived(self):
        original = b"\xffprivate marker fixture"
        self.marker.write_bytes(original)
        status = lock_status(self.root)
        self.assertEqual(status["marker_format"], "unrecognized")
        self.assertNotIn("private", json.dumps(status))
        result = self.recover()
        self.assertEqual((self.root / result["archive"]).read_bytes(), original)

    def test_oversized_marker_is_not_read_or_recovered(self):
        self.marker.write_bytes(b"x" * 4097)
        for action in (lambda: lock_status(self.root),
                       lambda: recover_lock(self.root, "0" * 64, "reviewed", True)):
            with self.assertRaisesRegex(SafeOpsError, "4096"):
                action()
        self.assertEqual(self.marker.stat().st_size, 4097)

    def test_initialization_failure_leaves_inspectable_marker(self):
        with patch("euromind_safeops.locking.os.fsync", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                with execution_lock(self.root, "aaaaaaaaaaaa"):
                    self.fail("Initialization failure entered body")
        self.assertTrue(self.marker.exists())
        self.assertEqual(lock_status(self.root)["guard"], "free")

    def test_receipt_failure_does_not_remove_marker(self):
        self.marker.write_bytes(b"123")
        with patch("euromind_safeops.locking.atomic_json_write", side_effect=SafeOpsError("fixture")):
            with self.assertRaises(SafeOpsError):
                self.recover()
        self.assertEqual(self.marker.read_bytes(), b"123")

    def test_audit_failure_after_archive_preserves_evidence(self):
        self.marker.write_bytes(b"123")
        with patch("euromind_safeops.locking.audit", side_effect=SafeOpsError("fixture")):
            with self.assertRaises(SafeOpsError):
                self.recover()
        self.assertFalse(self.marker.exists())
        archives = list((self.state / "recovered-locks").glob("*/run.lock"))
        self.assertEqual(len(archives), 1)
        self.assertEqual(archives[0].read_bytes(), b"123")
        self.assertTrue(archives[0].with_name("receipt.json").is_file())

    def test_changed_marker_during_recovery_is_not_archived(self):
        self.marker.write_bytes(b"123")
        def change_after_receipt(path, data):
            atomic_json_write(path, data)
            self.marker.write_bytes(b"changed")
        with patch("euromind_safeops.locking.atomic_json_write", side_effect=change_after_receipt):
            with self.assertRaisesRegex(SafeOpsError, "changed during recovery"):
                self.recover()
        self.assertEqual(self.marker.read_bytes(), b"changed")
        self.assertFalse(list((self.state / "recovered-locks").glob("*/run.lock")))

    def test_cleanup_failure_cannot_record_a_passed_run(self):
        self.source.write_text(
            "import unittest\nfrom pathlib import Path\nclass T(unittest.TestCase):\n"
            " def test_it(self): Path('.safeops/run.lock').write_bytes(b'replaced')\n", encoding="utf-8")
        with self.assertRaisesRegex(SafeOpsError, "cleanup refused"):
            run(self.root, self.approved())
        self.assertEqual(self.marker.read_bytes(), b"replaced")
        events = [json.loads(line) for line in (self.state / "audit.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertFalse(any(event["action"] == "run" and event["status"] == "passed" for event in events))

    def test_native_failure_never_falls_back_to_unprotected_execution(self):
        plan_id = self.approved()
        with patch("euromind_safeops.locking._native_lock", side_effect=SafeOpsError("unavailable")), \
                patch("euromind_safeops.execution.subprocess.run") as child:
            with self.assertRaises(SafeOpsError):
                run(self.root, plan_id)
            child.assert_not_called()
        self.assertFalse(self.marker.exists())

    def symlink(self, path, target, directory=False):
        try:
            path.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic link creation unavailable")

    def test_symbolic_marker_link_is_rejected(self):
        target = self.root / "outside.txt"
        target.write_bytes(b"untouched")
        self.symlink(self.marker, target)
        with self.assertRaises(SafeOpsError):
            lock_status(self.root)
        self.assertEqual(target.read_bytes(), b"untouched")

    def test_broken_guard_link_is_rejected(self):
        self.symlink(self.guard, self.root / "missing")
        with self.assertRaises(SafeOpsError):
            with execution_lock(self.root, "aaaaaaaaaaaa"):
                self.fail("Broken guard link accepted")

    def test_hard_link_alias_is_rejected(self):
        target = self.root / "outside.txt"
        target.write_bytes(b"untouched")
        try:
            os.link(target, self.marker)
        except OSError:
            self.skipTest("Hard links unavailable")
        with self.assertRaises(SafeOpsError):
            lock_status(self.root)
        self.assertEqual(target.read_bytes(), b"untouched")

    def test_linked_recovery_directory_is_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        self.marker.write_bytes(b"123")
        self.symlink(self.state / "recovered-locks", outside, True)
        with self.assertRaises(SafeOpsError):
            self.recover()
        self.assertFalse(list(outside.iterdir()))
        self.assertTrue(self.marker.exists())

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX named pipe")
    def test_pipe_marker_is_rejected_without_blocking(self):
        os.mkfifo(self.marker)
        with self.assertRaises(SafeOpsError):
            lock_status(self.root)

    @unittest.skipUnless(os.name == "nt", "Windows junction")
    def test_junction_state_directory_is_rejected(self):
        moved = self.root / "original-state"
        self.state.rename(moved)
        completed = subprocess.run(["cmd", "/d", "/c", "mklink", "/J", str(self.state), str(moved)],
                                   capture_output=True)
        self.assertEqual(completed.returncode, 0)
        try:
            with self.assertRaises(SafeOpsError):
                lock_status(self.root)
        finally:
            self.state.rmdir()
            moved.rename(self.state)
