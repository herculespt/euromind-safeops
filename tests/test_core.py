import json
import tempfile
import unittest
from pathlib import Path

from euromind_safeops.core import SafeOpsError, sha256, tree_digest
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


if __name__ == "__main__":
    unittest.main()
