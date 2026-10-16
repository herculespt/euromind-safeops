"""Explicit source consent, offline AI candidates and real loopback transport."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from euromind_safeops import candidate_transport as transport, generation, proposals
from euromind_safeops.cli import main
from euromind_safeops.core import SafeOpsError, json_bytes, sha256
from euromind_safeops.planning import create_plan
from test_provider_transport import loopback_provider


def response(document, provider="openai-compatible"):
    text = document if isinstance(document, str) else json_bytes(document).decode()
    if provider == "openai":
        return {"status": "completed", "output": [{"type": "message", "status": "completed",
                "content": [{"type": "output_text", "text": text}]}]}
    if provider == "anthropic":
        return {"stop_reason": "end_turn", "content": [{"type": "text", "text": text}]}
    return {"choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": text}}]}


class GenerationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "project"
        self.root.mkdir()
        self.source = self.root / "hello.txt"
        self.source.write_bytes("Olá\nworld\n".encode())
        (self.root / "unselected.txt").write_text("unrelated_private_fixture\n")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--root", str(self.root), "init"]), 0)
        self.plan = self.plan_for()
        self.options = {"provider": "openai-compatible", "model": "fixture", "endpoint": "http://127.0.0.1:9000/v1/chat/completions"}
        self.document = self.candidate()

    def plan_for(self, paths=None, task="Improve the greeting documentation"):
        return create_plan(self.root, task, ["hello.txt"] if paths is None else paths, "Advice not uploaded", "offline")

    def candidate(self, path="hello.txt", content="Olá\nPortugal\n"):
        return {"schema": 1, "files": [{"path": path,
                "base_sha256": hashlib.sha256((self.root / path).read_bytes()).hexdigest(), "content": content}]}

    def review(self, **changes):
        return generation.review_generation(self.root, self.plan["id"], **(self.options | changes))

    def generate(self, text=None, **changes):
        fingerprint = self.review()["fingerprint"]
        with patch.object(generation, "send_request", return_value=json_bytes(self.document).decode() if text is None else text):
            return generation.generate_proposal(self.root, self.plan["id"], fingerprint,
                allow_source_upload=True, **(self.options | changes))

    def record(self, result):
        return self.root / ".safeops/proposals" / (result["proposal_id"] + ".json")

    def no_proposal(self):
        self.assertFalse(list((self.root / ".safeops/proposals").glob("*.json")))
        self.assertEqual(list((self.root / ".safeops/approvals").iterdir()), [])
        self.assertFalse((self.root / ".safeops/run.lock").exists())

    def test_review_is_offline_exact_stable_and_has_no_state_side_effect(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        with patch.object(transport, "_post_json") as post:
            review = self.review()
            self.assertEqual(review, self.review())
        post.assert_not_called()
        uploaded = json.loads(review["request"]["payload"]["messages"][-1]["content"])
        self.assertEqual(uploaded, {"schema": 1, "task": self.plan["task"], "files": [
            {"path": "hello.txt", "base_sha256": self.document["files"][0]["base_sha256"], "content": "Olá\nworld\n"}]})
        self.assertNotIn("unrelated_private_fixture", json.dumps(review))
        self.assertNotIn(self.plan["advice"], json.dumps(review))
        body = json.dumps(review["request"]["payload"]).encode()
        self.assertEqual(review["request"]["body_sha256"], hashlib.sha256(body).hexdigest())
        self.assertEqual(review["request"]["body_bytes"], len(body))
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_explicit_source_consent_and_exact_fingerprint_required_before_request(self):
        fingerprint = self.review()["fingerprint"]
        for confirm, consent in ((fingerprint, False), (None, True), ("bad", True), ("0" * 64, True)):
            with patch.object(generation, "send_request") as send, self.assertRaises(SafeOpsError):
                generation.generate_proposal(self.root, self.plan["id"], confirm, allow_source_upload=consent, **self.options)
            send.assert_not_called()
        self.no_proposal()

    def test_provider_model_endpoint_and_timeout_are_confirmation_bound(self):
        fingerprint = self.review()["fingerprint"]
        for changes in ({"model": "other"}, {"timeout": 31}, {"endpoint": self.options["endpoint"].replace(":9000", ":9001")},
                        {"provider": "openai", "endpoint": ""}):
            with patch.object(generation, "send_request") as send, self.assertRaises(SafeOpsError):
                generation.generate_proposal(self.root, self.plan["id"], fingerprint, allow_source_upload=True,
                                            **(self.options | changes))
            send.assert_not_called()

    def test_valid_ai_record_is_unapproved_labelled_and_reviewable(self):
        before = self.source.read_bytes()
        result = self.generate()
        record = json.loads(self.record(result).read_bytes())
        self.assertEqual(record["schema"], 2)
        self.assertEqual(record["origin"]["kind"], "ai")
        self.assertEqual(result["origin"]["request_sha256"], self.review()["fingerprint"])
        self.assertNotIn("Portugal", json.dumps(result))
        reviewed = proposals.review_proposal(self.root, result["proposal_id"])
        self.assertEqual(reviewed["origin"], record["origin"])
        self.assertIn("+Portugal", reviewed["files"][0]["diff"])
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(list((self.root / ".safeops/approvals").iterdir()), [])
        audit = (self.root / ".safeops/audit.jsonl").read_text()
        self.assertIn('"generate-proposal"', audit)
        self.assertNotIn("Portugal", audit)
        self.assertNotIn("Advice not uploaded", self.record(result).read_text())

    def test_cli_loopback_has_exact_reviewed_payload_and_no_authority_side_effect(self):
        body = json_bytes(response(self.document))
        with loopback_provider(body) as (endpoint, requests):
            args = ["--root", str(self.root), "--json"]
            options = ["--provider", "openai-compatible", "--model", "fixture", "--endpoint", endpoint]
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(main(args + ["review-generation", self.plan["id"], *options]), 0)
            review = json.loads(out.getvalue())["data"]
            self.assertEqual(requests, [])
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(main(args + ["generate-proposal", self.plan["id"], *options,
                    "--confirm", review["fingerprint"], "--allow-source-upload"]), 0)
            result = json.loads(out.getvalue())["data"]
            self.assertEqual(len(requests), 1)
            self.assertEqual(requests[0]["body"], review["request"]["payload"])
            self.assertEqual(result["origin"]["provider"], "openai-compatible")
            self.assertEqual(self.source.read_bytes(), "Olá\nworld\n".encode())
            self.assertEqual(list((self.root / ".safeops/approvals").iterdir()), [])

    def test_old_task_consent_flag_does_not_authorize_source_upload(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main(["--root", str(self.root), "--json", "generate-proposal", self.plan["id"],
                "--provider", "openai", "--model", "fixture", "--confirm", "0" * 64, "--allow-remote"]), 2)
        self.assertEqual(json.loads(out.getvalue())["error"]["code"], "invalid_arguments")
        self.no_proposal()

    def test_critical_missing_scope_directory_and_many_files_are_refused(self):
        for paths, task in ((["hello.txt"], "Publish production"), ([], "Improve docs"), (["folder"], "Improve docs"),
                            ([f"f{i}.txt" for i in range(5)], "Improve docs")):
            (self.root / "folder").mkdir(exist_ok=True)
            for i in range(5): (self.root / f"f{i}.txt").write_text("fixture\n")
            self.plan = self.plan_for(paths, task)
            with self.assertRaises(SafeOpsError): self.review()
        self.no_proposal()

    def test_non_utf8_bom_crlf_controls_and_missing_final_newline_are_refused(self):
        for raw in (b"\xff", b"\xef\xbb\xbftext\n", b"text\r\n", b"text\x00\n", b"text"):
            self.source.write_bytes(raw)
            self.plan = self.plan_for()
            with self.assertRaises(SafeOpsError): self.review()

    def test_source_file_and_total_bounds_are_enforced(self):
        self.source.write_bytes(b"x" * generation.MAX_SOURCE_BYTES + b"\n")
        self.plan = self.plan_for()
        with self.assertRaises(SafeOpsError): self.review()
        paths = []
        for i in range(3):
            p = self.root / f"bounded{i}.txt"; p.write_bytes(b"x" * 6000 + b"\n"); paths.append(p.name)
        self.plan = self.plan_for(paths)
        with self.assertRaisesRegex(SafeOpsError, "total"): self.review()

    def test_source_disappears_or_gains_hardlink_during_read_is_refused(self):
        original = generation._read_regular
        for operation in ("unlink", "hardlink"):
            self.source.write_text("fixture\n"); self.plan = self.plan_for()
            def changing(path, **kwargs):
                raw = original(path, **kwargs)
                if operation == "unlink": path.unlink()
                else: os.link(path, self.base / "external-link")
                return raw
            with patch.object(generation, "_read_regular", side_effect=changing), self.assertRaises(SafeOpsError):
                self.review()
            self.no_proposal()

    def test_source_change_after_snapshot_is_detected_by_second_bounded_read(self):
        original, count = generation._context, 0
        def changing(*args):
            nonlocal count
            result = original(*args); count += 1
            if count == 2: self.source.write_text("human edit\n")
            return result
        with patch.object(generation, "_context", side_effect=changing), self.assertRaises(SafeOpsError):
            self.review()
        self.no_proposal()

    def test_policy_drift_between_confirmation_and_send_is_refused(self):
        fingerprint = self.review()["fingerprint"]
        original, count = generation.review_generation, 0
        def changing(*args, **kwargs):
            nonlocal count
            result = original(*args, **kwargs); count += 1
            if count == 1: transport.OUTPUT_TOKENS -= 1
            return result
        with patch.object(transport, "OUTPUT_TOKENS", transport.OUTPUT_TOKENS), \
                patch.object(generation, "review_generation", side_effect=changing), \
                patch.object(generation, "send_request") as send, self.assertRaises(SafeOpsError):
            generation.generate_proposal(self.root, self.plan["id"], fingerprint, allow_source_upload=True, **self.options)
        send.assert_not_called(); self.no_proposal()

    def test_source_hardlink_and_symlink_are_refused(self):
        linked = self.root / "linked.txt"
        try: os.link(self.source, linked)
        except OSError: self.skipTest("Hardlinks unavailable")
        self.plan = self.plan_for()
        with self.assertRaises(SafeOpsError): self.review()
        linked.unlink()
        external = self.base / "external.txt"; external.write_text("private fixture\n")
        self.source.unlink()
        try: self.source.symlink_to(external)
        except OSError: self.skipTest("Symlinks unavailable")
        with self.assertRaises(SafeOpsError): self.review()

    def test_obvious_credentials_in_source_or_model_are_refused_without_echo(self):
        marker = "sk-" + "x" * 40
        self.source.write_text(marker + "\n")
        self.plan = self.plan_for()
        with self.assertRaises(SafeOpsError) as error: self.review()
        self.assertNotIn(marker, str(error.exception))
        self.source.write_text("fixture\n"); self.plan = self.plan_for()
        with self.assertRaises(SafeOpsError): self.review(model=marker)
        with self.assertRaises(SafeOpsError): self.review(model=None)

    def test_changed_source_config_plan_or_version_invalidates_confirmation(self):
        fingerprint = self.review()["fingerprint"]
        self.source.write_text("human edit\n")
        with patch.object(generation, "send_request") as send, self.assertRaises(SafeOpsError):
            generation.generate_proposal(self.root, self.plan["id"], fingerprint, allow_source_upload=True, **self.options)
        send.assert_not_called()
        self.plan = self.plan_for(); fingerprint = self.review()["fingerprint"]
        with patch.object(generation, "__version__", "changed"), patch.object(generation, "send_request") as send, self.assertRaises(SafeOpsError):
            generation.generate_proposal(self.root, self.plan["id"], fingerprint, allow_source_upload=True, **self.options)
        send.assert_not_called()

    def test_context_change_between_reviews_prevents_http(self):
        fingerprint = self.review()["fingerprint"]
        original = generation.review_generation
        def changing(*args, **kwargs):
            result = original(*args, **kwargs)
            (self.root / "unselected.txt").write_text("human edit\n")
            return result
        with patch.object(generation, "review_generation", side_effect=changing), patch.object(generation, "send_request") as send:
            with self.assertRaises(SafeOpsError):
                generation.generate_proposal(self.root, self.plan["id"], fingerprint, allow_source_upload=True, **self.options)
        send.assert_not_called(); self.no_proposal()

    def test_observed_change_during_provider_call_retains_no_candidate(self):
        for target in (self.source, self.root / ".safeops/config.json"):
            if target == self.source: self.source.write_text("fixture\n")
            else: target.write_bytes(json_bytes({"schema": 1, "checks": ["compile"]}))
            self.plan = self.plan_for(); fingerprint = self.review()["fingerprint"]
            def changing(request):
                if target == self.source: target.write_text("human edit\n")
                else: target.write_bytes(json_bytes({"schema": 1, "checks": ["unit-tests"]}))
                return json_bytes(self.document).decode()
            with patch.object(generation, "send_request", side_effect=changing), self.assertRaises(SafeOpsError):
                generation.generate_proposal(self.root, self.plan["id"], fingerprint, allow_source_upload=True, **self.options)
            self.no_proposal()

    def test_invalid_json_and_candidate_shape_are_redacted_and_not_persisted(self):
        samples = ['private-fixture-body', '[]', '{"schema":1,"schema":1}', '{"schema":NaN}',
                   json.dumps(self.document | {"commands": ["untrusted text"]}),
                   json.dumps({"schema": True, "files": self.document["files"]}),
                   json.dumps({"schema": 1, "files": []}), " " * (transport.MAX_CANDIDATE_BYTES + 1)]
        for sample in samples:
            with self.subTest(sample=sample[:20]), self.assertRaises(SafeOpsError) as error: self.generate(sample)
            self.assertNotIn("private-fixture-body", str(error.exception)); self.no_proposal()

    def test_unselected_path_is_rejected_before_local_candidate_reads(self):
        text = json_bytes(self.candidate("unselected.txt", "changed\n")).decode()
        with patch("euromind_safeops.preview._read_regular") as read, self.assertRaises(SafeOpsError):
            generation._candidate(self.root, text, ["hello.txt"])
        read.assert_not_called()

    def test_stale_base_duplicate_noop_extra_fields_and_secret_output_are_refused(self):
        entries = self.document["files"]
        variants = [dict(entries[0], base_sha256="0" * 64), dict(entries[0], content="Olá\nworld\n"),
                    dict(entries[0], extra=True), dict(entries[0], content="sk-" + "x" * 40 + "\n")]
        for entry in variants:
            with self.assertRaises(SafeOpsError): self.generate(json_bytes({"schema": 1, "files": [entry]}).decode())
        with self.assertRaises(SafeOpsError): self.generate(json_bytes({"schema": 1, "files": entries * 2}).decode())
        self.no_proposal()

    def test_replacement_byte_limits_are_enforced(self):
        self.document["files"][0]["content"] = "x" * generation.MAX_REPLACEMENT_BYTES + "\n"
        with self.assertRaises(SafeOpsError): self.generate()
        paths = []
        entries = []
        for i in range(3):
            p = self.root / f"f{i}.txt"; p.write_text("fixture\n"); paths.append(p.name)
            entries += self.candidate(p.name, "x" * 12000 + "\n")["files"]
        self.plan = self.plan_for(paths); self.document = {"schema": 1, "files": entries}
        with self.assertRaises(SafeOpsError): self.generate()

    def test_schema2_origin_tampering_and_unknown_fields_are_rejected(self):
        result = self.generate(); path = self.record(result); original = json.loads(path.read_bytes())
        variants = [("kind", "manual"), ("provider", "offline"), ("model", ""), ("request_sha256", "bad"), ("extra", True)]
        for key, value in variants:
            changed = json.loads(json.dumps(original)); changed["origin"][key] = value
            changed.pop("fingerprint"); changed["fingerprint"] = sha256(changed); path.write_bytes(json_bytes(changed))
            with self.assertRaisesRegex(SafeOpsError, "integrity"): proposals.review_proposal(self.root, result["proposal_id"])

    def test_audit_failure_retains_only_valid_unapproved_proposal(self):
        with patch.object(proposals, "audit", side_effect=OSError("fixture")), self.assertRaises(OSError): self.generate()
        records = list((self.root / ".safeops/proposals").glob("*.json")); self.assertEqual(len(records), 1)
        self.assertEqual(proposals._load(self.root, records[0].stem)["schema"], 2)
        self.assertEqual(list((self.root / ".safeops/approvals").iterdir()), [])

    def test_generated_schema2_follows_explicit_stage_checks_apply_and_rollback(self):
        from euromind_safeops.staging import stage_proposal
        from euromind_safeops.stage_inspection import inspect_stage
        from euromind_safeops.stage_review import review_stage
        from euromind_safeops.execution import approve, run
        from euromind_safeops.application import review_application, apply_stage, rollback_application
        from euromind_safeops.application_journal import inspect_application
        (self.root / "src").mkdir(); (self.root / "src/main.py").write_text("value = 1\n")
        (self.root / "tests").mkdir(); test = self.root / "tests/test_text.py"
        test.write_text("import unittest\nfrom pathlib import Path\nclass T(unittest.TestCase):\n def test_text(self): self.assertIn('world', Path('hello.txt').read_text(encoding='utf-8'))\n")
        self.plan = self.plan_for(["hello.txt", "tests/test_text.py"])
        self.document = self.candidate(); self.document["files"] += self.candidate("tests/test_text.py", test.read_text().replace("'world'", "'Portugal'"))["files"]
        result = self.generate(); reviewed = proposals.review_proposal(self.root, result["proposal_id"])
        staged = stage_proposal(self.root, result["proposal_id"], reviewed["fingerprint"])
        self.assertEqual(inspect_stage(self.root, staged["stage_id"])["status"], "matching")
        self.assertEqual(review_stage(self.root, staged["stage_id"])["status"], "current")
        staged_root = self.root / ".safeops/stages" / staged["stage_id"] / "workspace"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--root", str(staged_root), "init"]), 0)
        plan = create_plan(staged_root, "Validate reviewed greeting", ["hello.txt"], "offline", "offline")
        approve(staged_root, plan["id"], "reviewed fixture", plan["id"])
        outcome = run(staged_root, plan["id"]); self.assertEqual(outcome["status"], "passed")
        application = review_application(self.root, staged["stage_id"], outcome["run_id"])
        applied = apply_stage(self.root, staged["stage_id"], outcome["run_id"], application["fingerprint"])
        self.assertEqual(self.source.read_bytes(), "Olá\nPortugal\n".encode())
        inspected = inspect_application(self.root, applied["application_id"])
        rollback_application(self.root, applied["application_id"], inspected["rollback_fingerprint"])
        self.assertEqual(self.source.read_bytes(), "Olá\nworld\n".encode())


class CandidateTransportTests(unittest.TestCase):
    def prepare(self, provider="openai-compatible", **changes):
        return transport.prepare_request({"schema": 1, "task": "Improve docs", "files": []},
            **({"provider": provider, "model": "fixture", "endpoint": "http://127.0.0.1:9000/v1/chat/completions" if provider == "openai-compatible" else ""} | changes))

    def test_native_payloads_and_credential_headers_are_separate_from_review(self):
        for provider, variable in (("openai", "OPENAI_API_KEY"), ("anthropic", "ANTHROPIC_API_KEY"), ("openai-compatible", "SAFEOPS_API_KEY")):
            request = self.prepare(provider)
            self.assertNotIn("test-value", json.dumps(request))
            with patch.dict(os.environ, {variable: "test-value"}), patch.object(transport, "_post_json", return_value=response("{}", provider)) as post:
                self.assertEqual(transport.send_request(request), "{}")
            args = post.call_args.args
            self.assertEqual(args[0], request["endpoint"]); self.assertEqual(args[1], request["payload"])
            self.assertEqual(args[3], 30)
            self.assertNotIn("tools", args[1]); self.assertEqual(args[1].get("max_tokens", args[1].get("max_output_tokens")), 8192)
            if provider == "openai": self.assertFalse(args[1]["store"])
            self.assertTrue(args[2])

    def test_missing_native_key_refuses_before_network(self):
        for provider, variable in (("openai", "OPENAI_API_KEY"), ("anthropic", "ANTHROPIC_API_KEY")):
            with patch.dict(os.environ, {variable: ""}), patch.object(transport, "_post_json") as post, self.assertRaises(SafeOpsError):
                transport.send_request(self.prepare(provider))
            post.assert_not_called()

    def test_invalid_provider_model_endpoint_and_timeout_are_refused(self):
        cases = [{"provider": "offline"}, {"model": ""}, {"model": "bad\nmodel"}, {"timeout": 0}, {"timeout": True}, {"timeout": 61},
                 {"provider": "openai", "endpoint": "https://example.invalid/chat/completions"}, {"endpoint": "https://" + "user" + ":" + "pass" + "@example.invalid/chat/completions"}]
        for changes in cases:
            provider = changes.pop("provider", "openai-compatible")
            with self.subTest(changes=changes), self.assertRaises(SafeOpsError): self.prepare(provider, **changes)

    def test_actual_serialized_payload_limit_includes_unicode_escaping(self):
        with self.assertRaises(SafeOpsError):
            transport.prepare_request({"text": "ã" * 12000}, provider="openai", model="fixture")

    def test_truncation_refusals_tools_bad_shapes_and_oversize_are_refused(self):
        cases = [("openai", {"status": "incomplete"}), ("openai", {"status": "completed", "output": None}),
                 ("openai", {"status": "completed", "output": [{"type": "function_call"}]}),
                 ("openai", {"status": "completed", "output": [{"type": "reasoning"}]}),
                 ("openai", {"status": "completed", "output": [{"type": "message", "status": "incomplete"}]}),
                 ("openai", {"status": "completed", "output": [{"type": "message", "status": "completed", "content": [{"type": "refusal", "refusal": "fixture"}]}]}),
                 ("anthropic", {"stop_reason": "max_tokens"}), ("anthropic", {"stop_reason": "end_turn", "content": [{"type": "tool_use"}]}),
                 ("anthropic", {"stop_reason": "end_turn", "content": None}), ("anthropic", {"stop_reason": "end_turn", "content": []}),
                 ("openai-compatible", {"choices": []}), ("openai-compatible", {"choices": [{"finish_reason": "length"}]}),
                 ("openai-compatible", {"choices": [{"finish_reason": "stop", "message": {"tool_calls": [{}]}}]}),
                 ("openai-compatible", response(" ")), ("openai-compatible", response("x" * (transport.MAX_CANDIDATE_BYTES + 1))),
                 ("openai-compatible", response("\ud800"))]
        with patch.dict(os.environ, {name: "test" for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY")}):
            for provider, data in cases:
                with self.subTest(provider=provider, data=str(data)[:40]), patch.object(transport, "_post_json", return_value=data), self.assertRaisesRegex(SafeOpsError, "complete bounded"):
                    transport.send_request(self.prepare(provider))

    def test_transport_error_is_propagated_without_retry(self):
        with patch.object(transport, "_post_json", side_effect=SafeOpsError("Provider call failed (HTTPError)")) as post, self.assertRaises(SafeOpsError):
            transport.send_request(self.prepare())
        post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
