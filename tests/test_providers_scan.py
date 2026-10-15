import tempfile
import unittest
from pathlib import Path

from euromind_safeops.core import SafeOpsError
from euromind_safeops.providers import offline_advice, remote_advice
from euromind_safeops.scanning import scan


class ProvidersAndScannerTests(unittest.TestCase):
    def test_offline_provider(self):
        self.assertIn("advisory", offline_advice("write docs", "documentation"))

    def test_remote_requires_consent(self):
        with self.assertRaises(SafeOpsError):
            remote_advice("hello", endpoint="https://example.org/v1/chat/completions", model="test", allow_remote=False)

    def test_remote_disallows_insecure_http(self):
        with self.assertRaises(SafeOpsError):
            remote_advice("hello", endpoint="http://example.org/v1/chat/completions", model="test", allow_remote=True)

    def test_remote_disallows_url_credentials(self):
        with self.assertRaises(SafeOpsError):
            remote_advice("hello", endpoint="https://person:secret@example.org/v1/chat/completions", model="test", allow_remote=True)

    def test_scan_finds_key_and_does_not_output_value(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = "ghp_" + "B" * 35
            (root / "oops.txt").write_text(value)
            result = scan(root)
            self.assertEqual(result[0]["rule"], "github-classic-token")
            self.assertNotIn(value, str(result))

    def test_scan_ignores_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".safeops").mkdir()
            (root / ".safeops" / "config.json").write_text("ghp_" + "B" * 35)
            self.assertEqual(scan(root), [])


if __name__ == "__main__":
    unittest.main()
