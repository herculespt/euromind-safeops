"""Structured CLI contracts, using local fixtures and no provider requests."""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from euromind_safeops import __version__
from euromind_safeops.cli import main
from euromind_safeops.core import SafeOpsError


class JsonOutputTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "src" / "demo.py").write_text("value = 1\n", encoding="utf-8")
        (self.root / "tests" / "test_demo.py").write_text(
            "import unittest\nclass T(unittest.TestCase):\n def test_it(self): pass\n", encoding="utf-8")

    def invoke(self, *arguments):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(["--json", "--root", str(self.root), *arguments])
        self.assertEqual(err.getvalue(), "")
        payload = json.loads(out.getvalue())  # Reject any extra output/object.
        self.assertEqual(set(payload), {"schema", "safeops_version", "command", "ok", "exit_code",
                                        "data", "error", "warnings"})
        self.assertEqual(payload["schema"], 1)
        self.assertEqual(payload["safeops_version"], __version__)
        self.assertEqual(payload["exit_code"], code)
        self.assertEqual(payload["ok"], code == 0)
        return code, payload

    def test_all_commands_share_one_envelope(self):
        code, initialized = self.invoke("init")
        self.assertEqual(code, 0)
        self.assertEqual(initialized["data"]["config"]["schema"], 1)
        for command in ("providers", "doctor", "scan"):
            with self.subTest(command=command):
                code, payload = self.invoke(command)
                self.assertEqual(code, 0)
                self.assertEqual(payload["command"], command)
                self.assertIsNone(payload["error"])
        _, planned = self.invoke("plan", "Rever a documentação pública")
        plan = planned["data"]
        self.assertEqual(plan["task"], "Rever a documentação pública")
        _, reviewed = self.invoke("review", plan["id"])
        self.assertEqual(reviewed["data"], plan)
        self.assertEqual(self.invoke("approve", plan["id"], "--confirm", plan["id"],
                                     "--reason", "Código e testes revistos")[0], 0)
        code, result = self.invoke("run", plan["id"])
        self.assertEqual(code, 0)
        self.assertEqual(result["data"]["status"], "passed")

    def test_critical_warning_is_data_without_stderr(self):
        self.invoke("init")
        code, payload = self.invoke("plan", "Deploy production")
        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["risk"], "critical")
        self.assertEqual(len(payload["warnings"]), 1)
        plan_id = payload["data"]["id"]
        code, error = self.invoke("approve", plan_id, "--confirm", plan_id, "--reason", "reviewed")
        self.assertEqual(code, 2)
        self.assertEqual(error["error"]["code"], "policy_error")

    def test_failed_tests_preserve_exit_one_and_results(self):
        (self.root / "tests" / "test_demo.py").write_text(
            "import unittest\nclass T(unittest.TestCase):\n def test_it(self): self.fail('fixture')\n", encoding="utf-8")
        self.invoke("init")
        plan_id = self.invoke("plan", "Review documentation")[1]["data"]["id"]
        self.invoke("approve", plan_id, "--confirm", plan_id, "--reason", "reviewed")
        code, payload = self.invoke("run", plan_id)
        self.assertEqual(code, 1, payload)
        self.assertIsNone(payload["error"])
        self.assertEqual(payload["data"]["status"], "failed")

    def test_scan_findings_are_exit_one_with_data(self):
        with patch("euromind_safeops.cli.scan", return_value=[{"path": "fixture", "line": 1}]):
            code, payload = self.invoke("scan")
        self.assertEqual(code, 1)
        self.assertEqual(payload["data"]["count"], 1)
        self.assertIsNone(payload["error"])

    def test_uninitialized_workspace_and_reinit_are_structured(self):
        self.assertEqual(self.invoke("doctor")[1]["error"]["code"], "policy_error")
        self.invoke("init")
        code, payload = self.invoke("init")
        self.assertEqual(code, 2)
        self.assertIsNone(payload["data"])

    def test_recovery_command_uses_same_envelope_and_explicit_confirmation(self):
        self.invoke("init")
        marker = self.root / ".safeops" / "run.lock"
        marker.write_bytes(b"123")
        status = self.invoke("doctor")[1]["data"]["run_lock"]
        code, rejected = self.invoke("recover-lock", "--confirm", status["marker_fingerprint"],
                                     "--reason", "Reviewed fixture")
        self.assertEqual(code, 2)
        self.assertEqual(rejected["error"]["code"], "policy_error")
        code, result = self.invoke("recover-lock", "--confirm", status["marker_fingerprint"],
                                   "--reason", "Verificação dos processos concluída", "--confirm-no-running-checks")
        self.assertEqual(code, 0)
        self.assertEqual(result["command"], "recover-lock")
        self.assertEqual(result["data"]["status"], "recovered")
        self.assertFalse(marker.exists())

    def test_argument_errors_never_echo_values(self):
        sensitive = "private-argument-value-do-not-echo"
        for arguments in ((), ("unknown-command",), ("run", "id", "--timeout", sensitive),
                          ("approve", "id"), ("plan", "task", "--provider", sensitive),
                          ("plan", "task", "--unknown", sensitive)):
            with self.subTest(arguments=arguments):
                code, payload = self.invoke(*arguments)
                self.assertEqual(code, 2)
                self.assertIsNone(payload["command"])
                self.assertEqual(payload["error"]["code"], "invalid_arguments")
                self.assertNotIn(sensitive, json.dumps(payload))

    def test_missing_root_and_permission_errors_are_sanitized(self):
        with patch("euromind_safeops.cli.Path.resolve", side_effect=PermissionError("private detail")):
            code, payload = self.invoke("providers")
        self.assertEqual(code, 2)
        self.assertEqual(payload["error"]["code"], "filesystem_error")
        self.assertNotIn("private detail", json.dumps(payload))

    def test_provider_failure_retains_safe_error_and_saves_no_plan(self):
        self.invoke("init")
        with patch("euromind_safeops.cli.remote_advice", side_effect=SafeOpsError("Provider request failed")):
            code, payload = self.invoke("plan", "Review docs", "--provider", "openai", "--model", "fixture", "--allow-remote")
        self.assertEqual(code, 2)
        self.assertEqual(payload["error"]["message"], "Provider request failed")
        self.assertFalse(list((self.root / ".safeops" / "plans").glob("*.json")))

    def test_credentials_are_never_in_provider_status(self):
        value = "private-credential-fixture-value"
        with patch.dict(os.environ, {"OPENAI_API_KEY": value, "ANTHROPIC_API_KEY": value}):
            payload = self.invoke("providers")[1]
        self.assertNotIn(value, json.dumps(payload))

    def test_flag_must_precede_command_and_literal_task_is_not_a_flag(self):
        self.invoke("init")
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(["--root", str(self.root), "plan", "--", "--json"])
        self.assertEqual(code, 0)
        self.assertNotIn("safeops_version", json.loads(out.getvalue()))
        self.assertEqual(json.loads(out.getvalue())["task"], "--json")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--root", str(self.root), "doctor", "--json"]), 2)

    def test_json_flag_after_root_before_command(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(["--root", str(self.root), "--json", "providers"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["schema"], 1)

    def test_default_init_and_error_formats_remain_available(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(main(["--root", str(self.root), "init"]), 0)
            self.assertEqual(main(["--root", str(self.root), "init"]), 2)
        self.assertTrue(out.getvalue().startswith("Initialized: "))
        self.assertIn("safeops: Already initialized", err.getvalue())

    def test_help_and_version_are_standard_text_actions(self):
        for action in ("--help", "--version"):
            with self.subTest(action=action), redirect_stdout(io.StringIO()) as out:
                with self.assertRaises(SystemExit) as raised:
                    main(["--json", action])
                self.assertEqual(raised.exception.code, 0)
                self.assertIn(__version__, out.getvalue())

    def test_subprocess_utf8_under_inherited_ascii(self):
        self.invoke("init")
        completed = subprocess.run(
            [sys.executable, "-m", "euromind_safeops", "--json", "--root", str(self.root),
             "plan", "Rever documentação e aprovação"], capture_output=True,
            env={**os.environ, "PYTHONIOENCODING": "ascii"})
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stderr, b"")
        self.assertEqual(json.loads(completed.stdout.decode("utf-8"))["data"]["task"],
                         "Rever documentação e aprovação")
