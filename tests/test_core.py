import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from euromind_safeops.core import SafeOpsError, read_json, sha256, tree_digest
from euromind_safeops.planning import risk_for, specialization, create_plan, load_plan
from euromind_safeops.cli import main


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "src" / "file.py").write_text("answer=42\n", encoding="utf-8")
        (self.root / "tests" / "test_example.py").write_text("import unittest\nclass T(unittest.TestCase):\n def test_it(self):\n  self.assertTrue(True)\n", encoding="utf-8")
        self.assertEqual(main(["--root", str(self.root), "init"]), 0)

    def test_risk_low(self):
        self.assertEqual(risk_for("update docs", ["README.md"]), "low")

    def test_risk_medium(self):
        self.assertEqual(risk_for("refactor the backend", []), "medium")

    def test_risk_high(self):
        self.assertEqual(risk_for("review cryptography", []), "high")

    def test_risk_critical(self):
        self.assertEqual(risk_for("deploy to production", []), "critical")

    def test_critical_by_path(self):
        self.assertEqual(risk_for("review", [".env"]), "critical")

    def test_specialist(self):
        self.assertEqual(specialization("review Flutter build"), "mobile-app")

    def test_digest_changes_on_file_edit(self):
        before = tree_digest(self.root)
        (self.root / "src" / "file.py").write_text("answer=7\n")
        self.assertNotEqual(before, tree_digest(self.root))

    def test_digest_ignores_runtime(self):
        before = tree_digest(self.root)
        (self.root / ".safeops" / "audit.jsonl").write_text("foo\n")
        self.assertEqual(before, tree_digest(self.root))

    def test_plan_roundtrip(self):
        plan = create_plan(self.root, "update docs", ["README.md"], "test", "offline")
        self.assertEqual(load_plan(self.root, plan["id"]), plan)

    def test_plan_tampering_rejected(self):
        plan = create_plan(self.root, "update docs", [], "test", "offline")
        f = self.root / ".safeops" / "plans" / (plan["id"] + ".json")
        modified = json.loads(f.read_text())
        modified["risk"] = "low"
        modified["task"] = "deploy production"
        f.write_text(json.dumps(modified))
        with self.assertRaises(SafeOpsError):
            load_plan(self.root, plan["id"])

    def test_path_traversal_rejected(self):
        with self.assertRaises(SafeOpsError):
            create_plan(self.root, "test", ["../private"], "test", "offline")

    def test_secret_in_task_rejected(self):
        with self.assertRaises(SafeOpsError):
            create_plan(self.root, "sk-" + "a" * 28, [], "test", "offline")

    def test_reinit_fails(self):
        self.assertEqual(main(["--root", str(self.root), "init"]), 2)

    def test_hash_is_order_independent(self):
        self.assertEqual(sha256({"a": 1, "b": 2}), sha256({"b": 2, "a": 1}))

    def test_stored_json_rejects_ambiguous_or_non_utf8_input(self):
        samples = [
            b'{"schema":1,"schema":2}',
            b'{"nested":{"key":1,"key":2}}',
            b'{"value":NaN}', b'{"value":Infinity}', b'{"value":-Infinity}',
            b'{"value":1e999}',
            '{"value":1}'.encode("utf-16"), b'{"value":"\xff"}',
        ]
        path = self.root / ".safeops" / "invalid.json"
        for raw in samples:
            with self.subTest(raw=raw):
                path.write_bytes(raw)
                with self.assertRaises(SafeOpsError):
                    read_json(path)

    def test_stored_json_preserves_portuguese(self):
        path = self.root / ".safeops" / "portuguese.json"
        path.write_text('{"texto":"Aprovação e execução"}', encoding="utf-8")
        self.assertEqual(read_json(path)["texto"], "Aprovação e execução")
        path.write_bytes(b'\xef\xbb\xbf' + path.read_bytes())
        self.assertEqual(read_json(path)["texto"], "Aprovação e execução")

    def test_json_decoder_recursion_error_is_controlled(self):
        path = self.root / ".safeops" / "deep.json"
        path.write_text('{"nested":[]}', encoding="utf-8")
        with patch("euromind_safeops.core.json.loads", side_effect=RecursionError("decoder limit")), self.assertRaises(SafeOpsError):
            read_json(path)


if __name__ == "__main__":
    unittest.main()
