"""Real owned worker/descendant lifecycles and fail-closed cleanup contracts."""

from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from euromind_safeops import check_bootstrap as bootstrap
from euromind_safeops import supervision as supervision
from euromind_safeops.cli import main
from euromind_safeops.core import SafeOpsError, json_bytes, tree_digest
from euromind_safeops.execution import approve, run
from euromind_safeops.locking import RetainRunMarker, _native_lock, lock_status, recover_lock
from euromind_safeops.planning import create_plan
from euromind_safeops.run_receipts import inspect_run


class SupervisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "src").mkdir()
        (self.root / "src/demo.py").write_text("value = 1\n", encoding="utf-8")
        (self.root / "tests").mkdir()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--root", str(self.root), "init"]), 0)
        self.state = self.root / ".safeops"
        self.source = self.root / "tests/test_case.py"
        self.source.write_text("import unittest\nclass T(unittest.TestCase):\n def test_it(self): pass\n")

    def approved(self):
        (self.state / "config.json").write_bytes(json_bytes({"schema": 1, "checks": ["unit-tests"]}))
        plan = create_plan(self.root, "Review temporary fixture", [], "offline", "offline")
        approve(self.root, plan["id"], "Reviewed trusted temporary test", plan["id"])
        return plan["id"]

    def only_run(self):
        owned, = (self.state / "runs").iterdir()
        return owned.name

    def wait_for(self, predicate, seconds=8):
        deadline = time.monotonic() + seconds
        while not predicate():
            if time.monotonic() >= deadline:
                self.fail("Temporary process fixture did not reach its bounded state")
            time.sleep(0.02)

    def lease_free(self, path):
        if not path.exists():
            return True
        with path.open("r+b", buffering=0) as handle:
            try:
                _native_lock(handle.fileno())
            except SafeOpsError:
                return False
            _native_lock(handle.fileno(), release=True)
        return True

    def descendant_fixture(self, *, parent_stays=False):
        lease, ready = self.state / "descendant.lease", self.state / "descendant.ready"
        lease.write_bytes(b"x")
        # Self-limited even if native supervision is broken; never kill a PID read from a file.
        self.addCleanup(lambda: self.wait_for(lambda: self.lease_free(lease), seconds=10))
        grandchild = (
            "import os,time\nfrom pathlib import Path\n"
            "f=open('.safeops/descendant.lease','r+b',buffering=0)\n"
            "if os.name=='nt':\n import msvcrt\n msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)\n"
            "else:\n import fcntl\n fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)\n"
            "Path('.safeops/descendant.ready').write_bytes(b'ready')\ntime.sleep(6)\n")
        child = "import subprocess,sys\nsubprocess.Popen([sys.executable,'-c'," + repr(grandchild) + "])\n"
        self.source.write_text(
            "import subprocess,sys,time,unittest\nfrom pathlib import Path\n"
            "class T(unittest.TestCase):\n def test_descendant(self):\n"
            f"  p=subprocess.Popen([sys.executable,'-c',{child!r}])\n"
            "  p.wait(timeout=4)\n  end=time.monotonic()+4\n"
            "  while not Path('.safeops/descendant.ready').exists() and time.monotonic()<end: time.sleep(.01)\n"
            "  self.assertTrue(Path('.safeops/descendant.ready').exists())\n" +
            ("  time.sleep(6)\n" if parent_stays else ""), encoding="utf-8")
        return lease, ready

    def test_success_preserves_history_and_releases_native_ownership(self):
        plan = self.approved()
        before = {p: p.read_bytes() for kind in ("plans", "approvals") for p in (self.state / kind).iterdir()}
        digest = tree_digest(self.root)
        result = run(self.root, plan)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(inspect_run(self.root, result["run_id"])["status"], "passed")
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertEqual(tree_digest(self.root), digest)
        self.assertFalse((self.state / "run.lock").exists())

    def test_completed_worker_with_live_grandchild_cannot_pass_or_hold_pipe_forever(self):
        lease, ready = self.descendant_fixture()
        plan = self.approved()
        started = time.monotonic()
        result = run(self.root, plan, timeout=2)
        self.assertTrue(ready.exists())
        self.assertEqual(result["status"], "timed-out")
        self.assertLess(time.monotonic() - started, 7)
        self.assertTrue(self.lease_free(lease))
        self.assertFalse((self.state / "run.lock").exists())

    def test_timeout_stops_live_worker_and_grandchild_without_signaling_unrelated_child(self):
        unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"], stdin=subprocess.DEVNULL)
        self.addCleanup(lambda: unrelated.wait(timeout=5))
        self.addCleanup(lambda: unrelated.terminate() if unrelated.poll() is None else None)
        lease, ready = self.descendant_fixture(parent_stays=True)
        result = run(self.root, self.approved(), timeout=2)
        self.assertTrue(ready.exists())
        self.assertEqual(result["status"], "timed-out")
        self.assertTrue(self.lease_free(lease))
        self.assertIsNone(unrelated.poll())

    def test_abrupt_parent_death_retains_marker_and_intent_with_owned_descendants_stopped(self):
        lease, ready = self.descendant_fixture(parent_stays=True)
        plan = self.approved()
        parent = subprocess.Popen([sys.executable, "-m", "euromind_safeops", "--json", "--root", str(self.root),
                                   "run", plan, "--timeout", "30"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(lambda: parent.kill() if parent.poll() is None else None)
        self.wait_for(ready.exists)
        parent.kill()
        parent.communicate(timeout=5)
        self.wait_for(lambda: self.lease_free(lease), seconds=4)
        status = lock_status(self.root)
        self.assertEqual(status["guard"], "free")
        self.assertTrue(status["marker_present"])
        self.assertEqual(inspect_run(self.root, self.only_run())["status"], "incomplete")
        with self.assertRaises(SafeOpsError):
            run(self.root, plan)
        # Fixture recovery only after independent owned lease/process verification.
        recover_lock(self.root, status["marker_fingerprint"], "Verified temporary parent/descendants stopped", True)
        self.assertFalse((self.state / "run.lock").exists())

    def test_large_utf8_streams_keep_bounded_tails_and_no_output_receipt(self):
        ending = "Revisão, execução e aprovação — Português\n"
        self.source.write_text(
            "import sys,unittest\nclass T(unittest.TestCase):\n def test_output(self):\n"
            f"  print('x'*200000+{ending!r})\n  print('y'*200000+{ending!r},file=sys.stderr)\n", encoding="utf-8")
        result = run(self.root, self.approved())
        check = result["checks"][0]
        for stream in ("stdout", "stderr"):
            self.assertLessEqual(len(check[stream]), 12000)
            self.assertIn(ending, check[stream])
        receipt = (self.state / "runs" / result["run_id"] / "receipt.json").read_text()
        self.assertNotIn(ending.strip(), receipt)
        tail = supervision._Tail(io.BytesIO(b"x" * 200000))
        tail._read()
        self.assertEqual(len(tail.data), supervision.TAIL_BYTES)

    def test_keyboard_interrupt_cleans_owned_processes_before_propagation(self):
        plan = self.approved()
        with patch.object(supervision, "_completion", side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            run(self.root, plan)
        self.assertFalse((self.state / "run.lock").exists())
        self.assertEqual(inspect_run(self.root, self.only_run())["status"], "incomplete")

    def test_uncertain_cleanup_retains_marker_and_does_not_finalize_or_run_again(self):
        original = supervision._stop
        def uncertain(*args, **kwargs):
            self.assertTrue(original(*args, **kwargs))  # Real cleanup still performed in this fixture.
            return False
        plan = self.approved()
        with patch.object(supervision, "_completion", side_effect=ValueError("private fixture detail")), \
                patch.object(supervision, "_stop", side_effect=uncertain), self.assertRaises(SafeOpsError) as error:
            run(self.root, plan)
        self.assertNotIn("private fixture detail", str(error.exception))
        self.assertTrue((self.state / "run.lock").exists())
        self.assertEqual(inspect_run(self.root, self.only_run())["status"], "incomplete")
        with patch("euromind_safeops.execution.run_check") as child, self.assertRaises(SafeOpsError):
            run(self.root, plan)
        child.assert_not_called()

    def test_partial_completion_protocol_is_sanitized_and_owned_cleanup_confirmed(self):
        with patch.object(supervision, "_completion", side_effect=ValueError("private completion bytes")), \
                self.assertRaises(SafeOpsError) as error:
            run(self.root, self.approved())
        self.assertNotIn("private completion bytes", str(error.exception))
        self.assertFalse((self.state / "run.lock").exists())

    def test_completion_schema_linkage_and_bytes_are_strict(self):
        path = self.state / "completion.json"
        process = SimpleNamespace(pid=123)
        token = "a" * 32
        good = {"schema": 1, "pid": 123, "token": token, "exit_code": 0}
        self.assertIsNone(supervision._completion(path, process, token))
        path.write_bytes(json_bytes(good))
        self.assertEqual(supervision._completion(path, process, token), 0)
        for key, value in (("schema", True), ("pid", 124), ("token", "other"), ("exit_code", True), ("extra", 1)):
            with self.subTest(key=key):
                path.write_bytes(json_bytes({**good, key: value}))
                with self.assertRaises(ValueError):
                    supervision._completion(path, process, token)
        for raw in (b"x" * 1025, b'{"schema":1,"schema":1}', b'[]', b'\xff'):
            path.write_bytes(raw)
            with self.assertRaises((ValueError, UnicodeError)):
                supervision._completion(path, process, token)

    def test_tail_reader_error_is_not_eof_success(self):
        stream = SimpleNamespace(read=lambda n: (_ for _ in ()).throw(OSError("private output")), close=lambda: None)
        tail = supervision._Tail(stream)
        tail._read()
        self.assertTrue(tail.failed)
        self.assertTrue(tail.eof.is_set())

    def test_naturally_finishing_grandchild_is_observed_before_success(self):
        child = "import time; from pathlib import Path; time.sleep(.3); Path('.safeops/descendant-finished').touch()"
        self.source.write_text(
            "import subprocess,sys,unittest\nclass T(unittest.TestCase):\n def test_child(self):\n"
            f"  subprocess.Popen([sys.executable,'-c',{child!r}])\n", encoding="utf-8")
        result = run(self.root, self.approved())
        self.assertEqual(result["status"], "passed")
        self.assertTrue((self.state / "descendant-finished").exists())

    def test_eof_before_start_gate_never_runs_project_code(self):
        marker = self.state / "should-not-start"
        self.source.write_text("from pathlib import Path\nPath('.safeops/should-not-start').touch()\n")
        startup = self.state / "startup-before-gate"
        (self.root / "sitecustomize.py").write_text("from pathlib import Path\nPath('.safeops/startup-before-gate').touch()\n")
        flags = {"process_group": 0} if os.name == "posix" else {}
        command = [sys.executable, "-m", "euromind_safeops.check_runner"]
        completed = subprocess.run([sys.executable, "-I", "-m", "euromind_safeops.check_bootstrap", str(self.state / "done"),
                                    "a" * 32, str(os.getpgrp() if os.name == "posix" else 0), *command],
                                   cwd=self.root, input=b"", capture_output=True, timeout=5,
                                   env={**os.environ, "PYTHONPATH": str(self.root)}, **flags)
        self.assertEqual(completed.returncode, 2)
        self.assertFalse(marker.exists())
        self.assertFalse(startup.exists())

    @unittest.skipUnless(os.name == "posix", "POSIX PID ownership")
    def test_no_group_signals_after_launcher_release_or_reaping(self):
        original = subprocess.Popen
        def start(*args, **kwargs):
            process = original(*args, **kwargs)
            wait = process.wait
            first = True
            def interrupted(*args, **kwargs):
                nonlocal first
                result = wait(*args, **kwargs)
                if first:
                    first = False
                    raise KeyboardInterrupt
                return result
            process.wait = interrupted
            return process
        with patch.object(supervision.subprocess, "Popen", side_effect=start), \
                patch.object(supervision, "_signal_group") as signals, self.assertRaises(KeyboardInterrupt):
            run(self.root, self.approved())
        signals.assert_not_called()
        self.assertFalse((self.state / "run.lock").exists())

    @unittest.skipUnless(os.name == "posix", "POSIX deliberate group escape")
    def test_escaped_pipe_holder_is_incomplete_with_retained_marker(self):
        child = "import time; time.sleep(5)"
        self.source.write_text(
            "import subprocess,sys,unittest\nclass T(unittest.TestCase):\n def test_escape(self):\n"
            f"  subprocess.Popen([sys.executable,'-c',{child!r}],start_new_session=True)\n", encoding="utf-8")
        # This deliberately escaped child is self-limited; no PID discovery/signaling.
        started = time.monotonic()
        with self.assertRaises(SafeOpsError):
            run(self.root, self.approved())
        self.assertLess(time.monotonic() - started, 4.8)
        self.assertTrue((self.state / "run.lock").exists())
        self.assertEqual(inspect_run(self.root, self.only_run())["status"], "incomplete")
        # Allow the bounded independent escape fixture to finish before temp cleanup.
        self.wait_for(lambda: time.monotonic() - started > 5.5)

    def test_bootstrap_rejects_arbitrary_commands_and_bad_gates(self):
        for command in ([sys.executable, "-c", "raise SystemExit(0)"], ["other", "-m", "compileall"]):
            with self.assertRaises(ValueError):
                bootstrap._fixed(command)
        self.assertEqual(bootstrap.main([]), 2)
        with patch.object(bootstrap.subprocess, "Popen") as child:
            self.assertEqual(bootstrap.main(["unused", "bad", "1", sys.executable, "-m", "compileall", "-q", "src", "tests"]), 2)
            child.assert_not_called()

    @unittest.skipUnless(os.name == "posix", "POSIX disposition")
    def test_nondefault_sigchld_refuses_before_starting_project_code(self):
        plan = self.approved()
        with patch.object(supervision.signal, "getsignal", return_value=signal.SIG_IGN), \
                patch.object(supervision.subprocess, "Popen") as child, self.assertRaises(SafeOpsError):
            run(self.root, plan)
        child.assert_not_called()
        self.assertFalse((self.state / "run.lock").exists())

    @unittest.skipUnless(os.name == "nt", "Windows native jobs")
    def test_assignment_failure_never_releases_gated_project_code(self):
        marker = self.state / "should-not-start"
        self.source.write_text("from pathlib import Path\nPath('.safeops/should-not-start').touch()\n")
        with patch.object(supervision.Job, "assign", side_effect=OSError("private assignment")), self.assertRaises(SafeOpsError):
            run(self.root, self.approved())
        self.assertFalse(marker.exists())
        self.assertFalse((self.state / "run.lock").exists())

    @unittest.skipUnless(os.name == "nt", "Windows native job accounting")
    def test_unavailable_job_accounting_retains_marker_after_best_effort_termination(self):
        with patch.object(supervision.Job, "active", side_effect=OSError("private query")), self.assertRaises(SafeOpsError):
            run(self.root, self.approved())
        self.assertTrue((self.state / "run.lock").exists())
        self.assertEqual(inspect_run(self.root, self.only_run())["status"], "incomplete")


if __name__ == "__main__":
    unittest.main()
