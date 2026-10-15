"""Offline contract tests for the native REST adapters (no network requests)."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from euromind_safeops.cli import main
from euromind_safeops.core import SafeOpsError
from euromind_safeops.providers import (
    ANTHROPIC_ENDPOINT, OPENAI_ENDPOINT, provider_status, remote_advice,
)


class NativeProviderTests(unittest.TestCase):
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-openai-only"})
    @patch("euromind_safeops.providers._post_json")
    def test_openai_responses_contract(self, post):
        post.return_value = {
            "output": [
                {"type": "reasoning", "summary": []},
                {"type": "message", "content": [{"type": "output_text", "text": "Review coverage."}]},
            ]
        }
        result = remote_advice("Improve docs", provider="openai", model="test-openai-model", allow_remote=True)
        self.assertEqual(result, "Review coverage.")
        endpoint, payload, headers, timeout = post.call_args.args
        self.assertEqual(endpoint, OPENAI_ENDPOINT)
        self.assertEqual(payload["input"], "Improve docs")
        self.assertFalse(payload["store"])
        self.assertNotIn("tools", payload)
        self.assertEqual(headers["Authorization"], "Bearer test-openai-only")
        self.assertEqual(timeout, 15)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-anthropic-only"})
    @patch("euromind_safeops.providers._post_json")
    def test_anthropic_messages_contract(self, post):
        post.return_value = {"content": [{"type": "text", "text": "Review API boundaries."}]}
        result = remote_advice("Check architecture", provider="anthropic", model="test-claude", allow_remote=True)
        self.assertEqual(result, "Review API boundaries.")
        endpoint, payload, headers, _ = post.call_args.args
        self.assertEqual(endpoint, ANTHROPIC_ENDPOINT)
        self.assertEqual(headers["x-api-key"], "test-anthropic-only")
        self.assertEqual(headers["anthropic-version"], "2023-06-01")
        self.assertEqual(payload["messages"], [{"role": "user", "content": "Check architecture"}])
        self.assertNotIn("tools", payload)

    @patch.dict(os.environ, {"SAFEOPS_API_KEY": "test-local"})
    @patch("euromind_safeops.providers._post_json")
    def test_existing_compatible_provider_preserved(self, post):
        post.return_value = {"choices": [{"message": {"content": "Independent advice"}}]}
        result = remote_advice("Hello", endpoint="http://localhost:8080/v1/chat/completions",
                               model="my-local-model", allow_remote=True)
        self.assertEqual(result, "Independent advice")
        self.assertIn("Bearer test-local", post.call_args.args[2]["Authorization"])

    @patch("euromind_safeops.providers._post_json")
    def test_missing_consent_is_fail_closed(self, post):
        with self.assertRaisesRegex(SafeOpsError, "allow-remote"):
            remote_advice("hello", provider="openai", model="test", allow_remote=False)
        post.assert_not_called()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test"})
    @patch("euromind_safeops.providers._post_json")
    def test_sensitive_task_rejected_before_network(self, post):
        with self.assertRaisesRegex(SafeOpsError, "secret"):
            remote_advice("Do not reveal sk-" + "x" * 32, provider="openai",
                          model="test", allow_remote=True)
        post.assert_not_called()

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"})
    @patch("euromind_safeops.providers._post_json")
    def test_native_endpoints_cannot_be_overridden(self, post):
        with self.assertRaisesRegex(SafeOpsError, "only for"):
            remote_advice("hello", provider="anthropic", endpoint="https://example.org/v1/chat/completions",
                          model="test", allow_remote=True)
        post.assert_not_called()

    def test_no_key_does_not_fallback_to_other_provider(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(SafeOpsError, "OPENAI_API_KEY"):
                remote_advice("hello", provider="openai", model="test", allow_remote=True)
            with self.assertRaisesRegex(SafeOpsError, "ANTHROPIC_API_KEY"):
                remote_advice("hello", provider="anthropic", model="test", allow_remote=True)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"})
    @patch("euromind_safeops.providers._post_json")
    def test_empty_text_or_tool_only_response_rejected(self, post):
        post.return_value = {"content": [{"type": "tool_use", "input": {"shell": "echo unsafe"}}]}
        with self.assertRaisesRegex(SafeOpsError, "no usable text"):
            remote_advice("check docs", provider="anthropic", model="test", allow_remote=True)

    def test_do_not_expose_key_values_in_provider_status(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sensitive-example-key"}):
            serialized = json.dumps(provider_status())
        self.assertNotIn("sensitive-example-key", serialized)
        self.assertIn('"configured": true', serialized)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test"})
    @patch("euromind_safeops.cli.remote_advice", return_value="Document tests")
    def test_cli_plan_native_integration(self, provider):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(main(["--root", str(root), "init"]), 0)
            self.assertEqual(main(["--root", str(root), "plan", "Improve documentation",
                                   "--provider", "openai", "--model", "test",
                                   "--allow-remote"]), 0)
            self.assertEqual(provider.call_args.kwargs["provider"], "openai")
            plans = list((root / ".safeops" / "plans").glob("*.json"))
            self.assertEqual(len(plans), 1)
            plan = json.loads(plans[0].read_text())
            self.assertEqual(plan["provider"], "openai")
            self.assertEqual(plan["advice"], "Document tests")

    @patch("euromind_safeops.cli.remote_advice")
    def test_cli_rejects_secret_before_api(self, provider):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["--root", str(root), "init"])
            result = main(["--root", str(root), "plan", "sk-" + "A" * 40,
                           "--provider", "anthropic", "--model", "test", "--allow-remote"])
            self.assertEqual(result, 2)
            provider.assert_not_called()

    def test_status_cli_works_without_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(main(["--root", tmp, "providers"]), 0)


if __name__ == "__main__":
    unittest.main()
