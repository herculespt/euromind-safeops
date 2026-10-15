"""Offline transport doubles and real loopback HTTP; no live model or credentials."""

import io
import json
import os
import tempfile
import threading
import unittest
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from euromind_safeops.cli import main
from euromind_safeops.core import SafeOpsError
from euromind_safeops.providers import ANTHROPIC_ENDPOINT, MAX_ADVICE_CHARS, MAX_RESPONSE_BYTES, OPENAI_ENDPOINT, _post_json, remote_advice


@contextmanager
def loopback_provider(body, *, status=200, location=None):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            requests.append({"path": self.path, "headers": self.headers,
                             "body": json.loads(self.rfile.read(int(self.headers["Content-Length"])))})
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            if location:
                self.send_header("Location", location)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            requests.append({"path": self.path, "method": "GET"})
            self.send_response(500)
            self.end_headers()

        def log_message(self, *_args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    try:
        with patch.dict(os.environ, {"no_proxy": "127.0.0.1", "NO_PROXY": "127.0.0.1", "SAFEOPS_API_KEY": ""}):
            yield f"http://127.0.0.1:{server.server_port}/v1/chat/completions", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


class ProviderTransportTests(unittest.TestCase):
    def post_bytes(self, data):
        response = MagicMock()
        response.read.side_effect = io.BytesIO(data).read
        response.__enter__.return_value = response
        with patch("euromind_safeops.providers.build_opener") as opener:
            opener.return_value.open.return_value = response
            result = _post_json("https://example.invalid/v1/messages", {"task": "Revisão"}, {}, 7)
            self.assertEqual(opener.return_value.open.call_args.kwargs["timeout"], 7)
        response.read.assert_called_once_with(MAX_RESPONSE_BYTES + 1)
        response.__exit__.assert_called_once()
        return result

    def test_utf8_object_and_optional_bom(self):
        for prefix in (b"", b"\xef\xbb\xbf"):
            with self.subTest(prefix=prefix):
                self.assertEqual(self.post_bytes(prefix + '{"text":"Aprovação e revisão"}'.encode("utf-8")),
                                 {"text": "Aprovação e revisão"})

    def test_response_size_boundary_and_single_bounded_read(self):
        prefix, suffix = b'{"text":"', b'"}'
        exact = prefix + b"x" * (MAX_RESPONSE_BYTES - len(prefix) - len(suffix)) + suffix
        self.assertEqual(len(self.post_bytes(exact)["text"]), MAX_RESPONSE_BYTES - len(prefix) - len(suffix))
        with self.assertRaisesRegex(SafeOpsError, "too large"):
            self.post_bytes(exact + b" ")

    def test_invalid_json_and_nonobject_responses_are_redacted(self):
        marker = "private-fixture-body"
        for data in (marker.encode(), b'{"text":"\xff"}', b'[]', b'null', b'"text"', b'1'):
            with self.subTest(data=data):
                with self.assertRaises(SafeOpsError) as caught:
                    self.post_bytes(data)
                self.assertIn("Provider call failed", str(caught.exception))
                self.assertNotIn(marker, str(caught.exception))

    def test_ambiguous_or_non_utf8_json_is_rejected(self):
        for data in (b'{"text":"first","text":"second"}', b'{"nested":{"x":1,"x":2}}',
                     b'{"x":NaN}', b'{"x":Infinity}', b'{"x":-Infinity}', b'{"x":1e999}',
                     '{"text":"UTF16"}'.encode("utf-16")):
            with self.subTest(data=data), self.assertRaises(SafeOpsError):
                self.post_bytes(data)

    def test_transport_failures_hide_exception_details(self):
        marker = "private-fixture-credential"
        errors = [HTTPError("https://example.invalid/?private=" + marker, code, marker, {}, io.BytesIO(marker.encode()))
                  for code in (401, 429, 500)]
        errors += [URLError(marker), TimeoutError(marker), OSError(marker)]
        for error in errors:
            with self.subTest(error=type(error).__name__), patch("euromind_safeops.providers.build_opener") as opener:
                opener.return_value.open.side_effect = error
                with self.assertRaises(SafeOpsError) as caught:
                    _post_json("https://example.invalid/v1/messages", {}, {}, 3)
                self.assertEqual(str(caught.exception), f"Provider call failed ({type(error).__name__})")
                self.assertNotIn(marker, str(caught.exception))
                opener.return_value.open.assert_called_once()
            if isinstance(error, HTTPError):
                error.close()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "fixture-openai", "ANTHROPIC_API_KEY": "fixture-anthropic"})
    def test_native_advice_uses_real_request_serialization_and_transport_decoder(self):
        cases = [
            ("openai", OPENAI_ENDPOINT, {"output": [{"type": "message", "content": [{"type": "output_text", "text": "Revisão"}]}]}),
            ("anthropic", ANTHROPIC_ENDPOINT, {"content": [{"type": "text", "text": "Revisão"}]}),
        ]
        for provider, endpoint, body in cases:
            response = MagicMock()
            response.__enter__.return_value = response
            response.read.return_value = json.dumps(body, ensure_ascii=False).encode("utf-8")
            with self.subTest(provider=provider), patch("euromind_safeops.providers.build_opener") as opener:
                opener.return_value.open.return_value = response
                self.assertEqual(remote_advice("Rever documentação", provider=provider, model="fixture", allow_remote=True), "Revisão")
                request = opener.return_value.open.call_args.args[0]
                self.assertEqual(request.full_url, endpoint)
                self.assertEqual(request.get_method(), "POST")
                payload = json.loads(request.data)
                self.assertNotIn("tools", payload)
                if provider == "openai":
                    self.assertEqual(request.get_header("Authorization"), "Bearer fixture-openai")
                    self.assertEqual(payload["input"], "Rever documentação")
                    self.assertFalse(payload["store"])
                else:
                    self.assertEqual(request.get_header("X-api-key"), "fixture-anthropic")
                    self.assertEqual(payload["messages"][-1]["content"], "Rever documentação")
                response.read.assert_called_once_with(MAX_RESPONSE_BYTES + 1)

    def test_loopback_cli_plan_uses_real_http_and_preserves_untrusted_advice(self):
        advice = "Rever aprovação e documentação — não executar comandos."
        body = json.dumps({"choices": [{"message": {"content": advice}}]}, ensure_ascii=False).encode("utf-8")
        with loopback_provider(body) as (endpoint, requests), tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "local_only.py").write_text("private_source_fixture = True\n", encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--root", tmp, "init"]), 0)
                self.assertEqual(main(["--root", tmp, "plan", "Rever documentação pública",
                                       "--provider", "openai-compatible", "--model", "fixture-model",
                                       "--endpoint", endpoint, "--allow-remote"]), 0)
            self.assertEqual(len(requests), 1)
            request = requests[0]
            self.assertEqual(request["path"], "/v1/chat/completions")
            self.assertEqual(request["headers"]["Content-Type"], "application/json")
            self.assertIsNone(request["headers"].get("Authorization"))
            self.assertEqual(request["body"]["messages"][-1], {"role": "user", "content": "Rever documentação pública"})
            self.assertEqual(request["body"]["model"], "fixture-model")
            self.assertEqual(set(request["body"]), {"model", "max_tokens", "messages"})
            self.assertNotIn("private_source_fixture", json.dumps(request["body"]))
            plan = json.loads(next((root / ".safeops" / "plans").glob("*.json")).read_text(encoding="utf-8"))
            self.assertEqual(plan["advice"], advice)
            self.assertEqual(plan["provider"], "openai-compatible")
            self.assertEqual(list((root / ".safeops" / "approvals").iterdir()), [])
            self.assertFalse((root / ".safeops" / "run.lock").exists())

    def test_real_http_redirects_never_reach_destination(self):
        with loopback_provider(b'{}') as (target, target_requests):
            for code in (301, 302, 303, 307, 308):
                with self.subTest(status=code), loopback_provider(b'{}', status=code, location=target) as (endpoint, requests):
                    with self.assertRaises(SafeOpsError):
                        remote_advice("Review docs", endpoint=endpoint, model="fixture-model", allow_remote=True)
                    self.assertEqual(len(requests), 1)
                    self.assertEqual(target_requests, [])

    def test_real_http_error_body_not_printed_by_cli(self):
        marker = "private-fixture-error-body"
        with loopback_provider(marker.encode(), status=429) as (endpoint, requests), tempfile.TemporaryDirectory() as tmp:
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                main(["--root", tmp, "init"])
                result = main(["--root", tmp, "plan", "Review docs", "--provider", "openai-compatible",
                               "--model", "fixture-model", "--endpoint", endpoint, "--allow-remote"])
            self.assertEqual(result, 2)
            self.assertNotIn(marker, out.getvalue() + err.getvalue())
            self.assertNotIn("Traceback", err.getvalue())
            self.assertEqual(len(requests), 1)
            self.assertEqual(list((Path(tmp) / ".safeops" / "plans").iterdir()), [])

    def test_missing_consent_or_sensitive_task_causes_no_http_request(self):
        with loopback_provider(b'{}') as (endpoint, requests):
            with self.assertRaises(SafeOpsError):
                remote_advice("Review docs", endpoint=endpoint, model="fixture-model", allow_remote=False)
            with self.assertRaises(SafeOpsError):
                remote_advice("sk-" + "X" * 40, endpoint=endpoint, model="fixture-model", allow_remote=True)
            self.assertEqual(requests, [])

    @patch.dict(os.environ, {"OPENAI_API_KEY": "fixture-openai", "ANTHROPIC_API_KEY": "fixture-anthropic"})
    @patch("euromind_safeops.providers._post_json")
    def test_malformed_provider_shapes_fail_with_controlled_error(self, post):
        samples = {
            "openai": [{}, {"output": None}, {"output": 2}, {"output": [{"type": "message", "content": None}]},
                       {"output": [{"type": "message", "content": [{"type": "output_text", "text": 7}]}]}],
            "anthropic": [{}, {"content": None}, {"content": 3}, {"content": [{"type": "text", "text": []}]}],
            "openai-compatible": [{}, {"choices": []}, {"choices": None}, {"choices": [{}]},
                                  {"choices": [{"message": {"content": None}}]},
                                  {"choices": [{"message": {"content": "  "}}]}],
        }
        for provider, responses in samples.items():
            for response in responses:
                with self.subTest(provider=provider, response=response):
                    post.return_value = response
                    endpoint = "http://127.0.0.1:8080/v1/chat/completions" if provider == "openai-compatible" else ""
                    with self.assertRaisesRegex(SafeOpsError, "no usable text"):
                        remote_advice("Review docs", provider=provider, endpoint=endpoint, model="fixture", allow_remote=True)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "fixture-openai", "ANTHROPIC_API_KEY": "fixture-anthropic"})
    @patch("euromind_safeops.providers._post_json")
    def test_native_multiple_text_blocks_and_nontext_blocks(self, post):
        post.return_value = {"output": [{"type": "reasoning"}, {"type": "message", "content": [
            {"type": "output_text", "text": "Revisão"}, {"type": "tool_call"},
            {"type": "output_text", "text": "Aprovação"}]}]}
        self.assertEqual(remote_advice("Review docs", provider="openai", model="fixture", allow_remote=True), "Revisão\nAprovação")
        post.return_value = {"content": [{"type": "text", "text": "Revisão"},
                                        {"type": "tool_use"}, {"type": "text", "text": "Aprovação"}]}
        self.assertEqual(remote_advice("Review docs", provider="anthropic", model="fixture", allow_remote=True), "Revisão\nAprovação")

    @patch("euromind_safeops.providers._post_json")
    def test_advice_length_is_bounded(self, post):
        post.return_value = {"choices": [{"message": {"content": "ã" * (MAX_ADVICE_CHARS + 1)}}]}
        advice = remote_advice("Review docs", endpoint="http://127.0.0.1:8080/v1/chat/completions",
                               model="fixture", allow_remote=True)
        self.assertEqual(advice, "ã" * MAX_ADVICE_CHARS)


if __name__ == "__main__":
    unittest.main()
