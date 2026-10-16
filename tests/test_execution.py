import json
import os
import io
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

from euromind_safeops.core import SafeOpsError
from euromind_safeops.execution import CHECKS, approve, get_config, run
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

    def test_check_output_preserves_portuguese_under_inherited_ascii(self):
        text = "Aprovação, execução e revisão — Português (Portugal)"
        (self.root / "tests" / "test_smoke.py").write_text(
            "import sys\nimport unittest\n"
            "class TestSmoke(unittest.TestCase):\n"
            " def test_smoke(self):\n"
            f"  print({text!r})\n"
            f"  print({text!r}, file=sys.stderr)\n",
            encoding="utf-8",
        )
        plan = self.plan()
        approve(self.root, plan["id"], "reviewed", plan["id"])
        with patch.dict(os.environ, {"PYTHONIOENCODING": "ascii"}):
            response = run(self.root, plan["id"])
            self.assertEqual(os.environ["PYTHONIOENCODING"], "ascii")
        self.assertEqual(response["status"], "passed")
        unit_result = response["checks"][-1]
        self.assertIn(text, unit_result["stdout"])
        self.assertIn(text, unit_result["stderr"])

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
        response = run(self.root, plan["id"])
        self.assertEqual(response["status"], "failed")
        self.assertNotEqual(response["checks"][-1]["exit_code"], 0)

    def test_test_file_without_cases_fails_closed(self):
        (self.root / "tests" / "test_smoke.py").write_text("answer = 42\n", encoding="utf-8")
        plan = self.plan()
        approve(self.root, plan["id"], "reviewed", plan["id"])
        response = run(self.root, plan["id"])
        self.assertEqual(response["status"], "failed")
        self.assertIn("No tests discovered", response["checks"][-1]["stderr"])
        self.assertFalse((self.root / ".safeops" / "run.lock").exists())

    def test_only_skipped_cases_fail_closed(self):
        (self.root / "tests" / "test_smoke.py").write_text(
            "import unittest\n@unittest.skip('not exercised')\n"
            "class T(unittest.TestCase):\n def test_it(self): pass\n", encoding="utf-8")
        plan = self.plan()
        approve(self.root, plan["id"], "reviewed", plan["id"])
        response = run(self.root, plan["id"])
        self.assertEqual(response["status"], "failed")
        self.assertIn("No non-skipped tests executed", response["checks"][-1]["stderr"])

    def test_nested_test_package_is_discovered(self):
        tests = self.root / "tests"
        (tests / "test_smoke.py").unlink()
        nested = tests / "nested"
        nested.mkdir()
        (nested / "__init__.py").write_text("", encoding="utf-8")
        (nested / "test_nested.py").write_text(
            "import unittest\nclass T(unittest.TestCase):\n"
            " def test_nested(self): self.assertEqual(2+2, 4)\n", encoding="utf-8")
        plan = self.plan()
        approve(self.root, plan["id"], "reviewed", plan["id"])
        response = run(self.root, plan["id"])
        self.assertEqual(response["status"], "passed")
        self.assertIn("test_nested", response["checks"][-1]["stderr"])

    def test_discovery_does_not_execute_before_approved_run(self):
        marker = self.root / "discovered.flag"
        (self.root / "tests" / "test_smoke.py").write_text(
            "from pathlib import Path\nimport unittest\n"
            "Path('discovered.flag').write_text('discovered', encoding='utf-8')\n"
            "class T(unittest.TestCase):\n def test_it(self): self.assertTrue(True)\n",
            encoding="utf-8")
        plan = self.plan()
        approve(self.root, plan["id"], "reviewed", plan["id"])
        self.assertFalse(marker.exists())
        self.assertEqual(run(self.root, plan["id"])["status"], "changed-inputs")
        self.assertTrue(marker.exists())

    def test_discovery_import_error_is_failure(self):
        (self.root / "tests" / "test_smoke.py").write_text(
            "raise RuntimeError('discovery failed')\n", encoding="utf-8")
        plan = self.plan()
        approve(self.root, plan["id"], "reviewed", plan["id"])
        response = run(self.root, plan["id"])
        self.assertEqual(response["status"], "failed")
        self.assertIn("discovery failed", response["checks"][-1]["stderr"])

    def test_timeout_reports_failure_and_releases_lock(self):
        (self.root / "tests" / "test_smoke.py").write_text(
            "import time\nimport unittest\nclass T(unittest.TestCase):\n"
            " def test_slow(self): time.sleep(5)\n", encoding="utf-8")
        plan = self.plan()
        approve(self.root, plan["id"], "reviewed", plan["id"])
        response = run(self.root, plan["id"], timeout=1)
        self.assertEqual(response["status"], "timed-out")
        self.assertEqual(response["checks"][-1]["exit_code"], -1)
        self.assertFalse((self.root / ".safeops" / "run.lock").exists())

    def test_invalid_configurations_raise_controlled_errors(self):
        invalid = [
            {}, {"schema": 1}, {"checks": ["compile"]},
            {"schema": True, "checks": ["compile"]},
            {"schema": 1.0, "checks": ["compile"]},
            {"schema": 2, "checks": ["compile"]},
            {"schema": 1, "checks": ["compile"], "extra": True},
        ]
        for checks in ([], None, "compile", {}, [None], [True], [1], [[]], [{}],
                       ["unknown"], ["compile", "compile"]):
            invalid.append({"schema": 1, "checks": checks})
        for config in invalid:
            with self.subTest(config=config):
                (self.root / ".safeops" / "config.json").write_text(json.dumps(config), encoding="utf-8")
                with self.assertRaises(SafeOpsError):
                    get_config(self.root)

    def test_invalid_config_cli_has_no_traceback(self):
        (self.root / ".safeops" / "config.json").write_text(
            '{"schema":1,"checks":[{}]}', encoding="utf-8")
        error = io.StringIO()
        with redirect_stderr(error):
            self.assertEqual(main(["--root", str(self.root), "doctor"]), 2)
        self.assertIn("Invalid config", error.getvalue())
        self.assertNotIn("Traceback", error.getvalue())

    def test_compile_only_configuration_still_works(self):
        (self.root / ".safeops" / "config.json").write_text(
            '{"schema":1,"checks":["compile"]}', encoding="utf-8")
        plan = self.plan()
        approve(self.root, plan["id"], "reviewed", plan["id"])
        response = run(self.root, plan["id"])
        self.assertEqual(response["status"], "passed")
        self.assertEqual([r["check"] for r in response["checks"]], ["compile"])

    def test_legacy_approval_is_rejected_before_execution(self):
        plan = self.plan()
        record = approve(self.root, plan["id"], "reviewed", plan["id"])
        record["schema"] = 1
        record.pop("execution_contract", None)
        path = self.root / ".safeops" / "approvals" / (plan["id"] + ".json")
        path.write_text(json.dumps(record), encoding="utf-8")
        with patch("euromind_safeops.execution.run_check") as process:
            with self.assertRaises(SafeOpsError):
                run(self.root, plan["id"])
            process.assert_not_called()

    def test_changed_fixed_command_invalidates_approval(self):
        plan = self.plan()
        approve(self.root, plan["id"], "reviewed", plan["id"])
        with patch.dict(CHECKS, {"compile": ["-m", "compileall", "src"]}):
            with self.assertRaises(SafeOpsError):
                run(self.root, plan["id"])

    def test_package_upgrade_invalidates_approval(self):
        plan = self.plan()
        approve(self.root, plan["id"], "reviewed", plan["id"])
        with patch("euromind_safeops.execution.__version__", "99.0.0"):
            with self.assertRaises(SafeOpsError):
                run(self.root, plan["id"])

    def test_skipped_case_with_executed_case_is_allowed(self):
        (self.root / "tests" / "test_smoke.py").write_text(
            "import unittest\nclass T(unittest.TestCase):\n"
            " @unittest.skip('optional')\n def test_skipped(self): pass\n"
            " def test_executed(self): self.assertTrue(True)\n", encoding="utf-8")
        plan = self.plan()
        approve(self.root, plan["id"], "reviewed", plan["id"])
        self.assertEqual(run(self.root, plan["id"])["status"], "passed")

    def test_zero_executed_custom_suite_fails_closed(self):
        (self.root / "tests" / "test_smoke.py").write_text(
            "import unittest\nclass EmptyRun(unittest.TestSuite):\n"
            " def countTestCases(self): return 1\n"
            " def run(self, result, debug=False): return result\n"
            "def load_tests(loader, standard_tests, pattern): return EmptyRun()\n",
            encoding="utf-8")
        plan = self.plan()
        approve(self.root, plan["id"], "reviewed", plan["id"])
        response = run(self.root, plan["id"])
        self.assertEqual(response["status"], "failed")
        self.assertIn("No non-skipped tests executed", response["checks"][-1]["stderr"])

    def test_zero_exit_during_discovery_is_not_success(self):
        (self.root / "tests" / "test_smoke.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
        plan = self.plan()
        approve(self.root, plan["id"], "reviewed", plan["id"])
        self.assertEqual(run(self.root, plan["id"])["status"], "failed")

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
