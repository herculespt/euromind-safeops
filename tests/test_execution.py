import json
import tempfile
import unittest
from pathlib import Path

from euromind_safeops.core import SafeOpsError
from euromind_safeops.execution import approve, run
from euromind_safeops.planning import create_plan
from euromind_safeops.cli import main


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "src" / "main.py").write_text("x = 1\n")
        (self.root / "tests" / "test_smoke.py").write_text("import unittest\nclass TestSmoke(unittest.TestCase):\n def test_smoke(self):\n  self.assertEqual(2+2, 4)\n")
        self.assertEqual(main(["--root", str(self.root), "init"]), 0)

    def plan(self, task="update documentation"):
        return create_plan(self.root, task, [], "offline", "offline")

    def test_run_requires_approval(self):
        plan = self.plan()
        with self.assertRaises(SafeOpsError):
            run(self.root, plan["id"])

    def test_approval_requires_confirmation(self):
        plan = self.plan()
        with self.assertRaises(SafeOpsError):
            approve(self.root, plan["id"], "reviewed", "no")

    def test_critical_plan_is_blocked(self):
        plan = self.plan("deploy production")
        with self.assertRaises(SafeOpsError):
            approve(self.root, plan["id"], "reviewed", plan["id"])

    def test_approved_checks_pass(self):
        plan = self.plan()
        approve(self.root, plan["id"], "verified code", plan["id"])
        response = run(self.root, plan["id"])
        self.assertEqual(response["status"], "passed")
        self.assertEqual(len(response["checks"]), 2)

    def test_changed_source_invalidates_approval(self):
        plan = self.plan()
        approve(self.root, plan["id"], "reviewed", plan["id"])
        (self.root / "src" / "main.py").write_text("x = 2\n")
        with self.assertRaises(SafeOpsError):
            run(self.root, plan["id"])

    def test_changed_config_invalidates_approval(self):
        plan = self.plan()
        approve(self.root, plan["id"], "reviewed", plan["id"])
        config = self.root / ".safeops" / "config.json"
        config.write_text(json.dumps({"schema": 1, "checks": ["compile"]}))
        with self.assertRaises(SafeOpsError):
            run(self.root, plan["id"])

    def test_no_tests_fails_closed(self):
        (self.root / "tests" / "test_smoke.py").unlink()
        plan = self.plan()
        approve(self.root, plan["id"], "reviewed", plan["id"])
        with self.assertRaises(SafeOpsError):
            run(self.root, plan["id"])

    def test_bad_timeout(self):
        plan = self.plan()
        approve(self.root, plan["id"], "reviewed", plan["id"])
        with self.assertRaises(SafeOpsError):
            run(self.root, plan["id"], timeout=0)

    def test_lock_prevents_concurrent_run(self):
        plan = self.plan()
        approve(self.root, plan["id"], "reviewed", plan["id"])
        (self.root / ".safeops" / "run.lock").write_text("123")
        with self.assertRaises(SafeOpsError):
            run(self.root, plan["id"])

    def test_failure_is_reported(self):
        (self.root / "tests" / "test_smoke.py").write_text("import unittest\nclass TestSmoke(unittest.TestCase):\n def test_smoke(self):\n  self.assertTrue(False)\n")
        plan = self.plan()
        approve(self.root, plan["id"], "reviewed", plan["id"])
        response = run(self.root, plan["id"])
        self.assertEqual(response["status"], "failed")


if __name__ == "__main__":
    unittest.main()
