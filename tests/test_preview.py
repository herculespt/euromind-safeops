"""Offline candidate previews: exact bases, bounded parsing and no authority."""

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

from euromind_safeops import preview
from euromind_safeops.cli import main
from euromind_safeops.core import SafeOpsError, sha256


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "project"
        self.root.mkdir()
        self.source = self.root / "hello.txt"
        self.source.write_bytes("Olá\nworld\n".encode())
        self.candidate = self.base / "candidate.json"
        self.doc = {"schema": 1, "files": [{"path": "hello.txt",
                    "base_sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
                    "content": "Olá\nPortugal\n"}]}

    def save(self):
        self.candidate.write_text(json.dumps(self.doc, ensure_ascii=True), encoding="utf-8")

    def call(self):
        self.save()
        return preview.preview_candidate(self.root, self.candidate)

    def test_exact_base_unicode_diff_and_provenance_without_writes(self):
        before = self.source.read_bytes()
        result = self.call()
        self.assertEqual(result["status"], "preview-only")
        self.assertEqual(result["candidate_sha256"], sha256(self.doc))
        item = result["files"][0]
        self.assertEqual(item["diff"], "--- a/hello.txt\n+++ b/hello.txt\n@@ -1,2 +1,2 @@\n Olá\n-world\n+Portugal\n")
        self.assertEqual(item["after_sha256"], hashlib.sha256("Olá\nPortugal\n".encode()).hexdigest())
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(list(self.root.iterdir()), [self.source])

    def test_cli_json_without_initialization_or_side_effects(self):
        self.save()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["--root", str(self.root), "--json", "preview", str(self.candidate)])
        result = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(result["command"], "preview")
        self.assertEqual(result["data"]["status"], "preview-only")
        self.assertFalse((self.root / ".safeops").exists())

    def test_stale_hash_fails_without_returning_diff(self):
        self.source.write_text("changed\n", encoding="utf-8")
        with self.assertRaisesRegex(SafeOpsError, "base hash"):
            self.call()

    def test_semantic_candidate_hash_ignores_formatting_and_key_order(self):
        first = self.call()["candidate_sha256"]
        self.candidate.write_text(json.dumps({"files": self.doc["files"], "schema": 1}, indent=4))
        self.assertEqual(preview.preview_candidate(self.root, self.candidate)["candidate_sha256"], first)

    def test_later_invalid_entry_produces_no_partial_cli_result(self):
        self.doc["files"].append({**self.doc["files"][0], "path": "missing.txt"})
        self.save()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["--root", str(self.root), "--json", "preview", str(self.candidate)])
        result = json.loads(out.getvalue())
        self.assertEqual(code, 2)
        self.assertIsNone(result["data"])
        self.assertNotIn("Portugal", out.getvalue())
        self.assertEqual(self.source.read_bytes(), "Olá\nworld\n".encode())

    def test_multiple_replacements_return_separate_exact_diffs(self):
        second = self.root / "second.txt"
        second.write_bytes(b"before\n")
        self.doc["files"].append({"path": "second.txt", "base_sha256": hashlib.sha256(b"before\n").hexdigest(),
                                  "content": "after\n"})
        result = self.call()
        self.assertEqual([f["path"] for f in result["files"]], ["hello.txt", "second.txt"])
        self.assertIn("-before\n+after\n", result["files"][1]["diff"])
        self.assertEqual(second.read_bytes(), b"before\n")

    def test_schema_and_unknown_fields_fail_closed(self):
        for document in ({}, {"schema": True, "files": []}, {"schema": 2, "files": []},
                         {"schema": 1, "files": {}}, {"schema": 1, "files": []},
                         {**self.doc, "approval": True}, {"schema": 1, "files": self.doc["files"] * 21}):
            with self.subTest(document=document):
                self.candidate.write_text(json.dumps(document))
                with self.assertRaises(SafeOpsError):
                    preview.preview_candidate(self.root, self.candidate)

    def test_malformed_file_fields_fail_closed(self):
        original = self.doc["files"][0].copy()
        for entry in (None, {}, {**original, "extra": 1}, {**original, "path": 2},
                      {**original, "base_sha256": "A" * 64}, {**original, "base_sha256": None},
                      {**original, "content": []}):
            with self.subTest(entry=entry):
                self.doc["files"] = [entry]
                with self.assertRaises(SafeOpsError): self.call()

    def test_unsafe_and_noncanonical_paths(self):
        for name in ("../outside", "/absolute", "C:/windows", "a\\b", ".safeops/state", ".git/config",
                     "dist/x", "./hello.txt", "a//b", "a/", "", "NUL", "bad\nname", "e\u0301.txt"):
            with self.subTest(name=name):
                self.doc["files"][0]["path"] = name
                with self.assertRaises(SafeOpsError): self.call()

    def test_case_collision_and_duplicate_paths(self):
        item = self.doc["files"][0]
        for name in ("hello.txt", "HELLO.txt"):
            self.doc["files"] = [item, {**item, "path": name}]
            with self.assertRaisesRegex(SafeOpsError, "case collisions"): self.call()

    def test_missing_and_directory_inputs(self):
        for path in ("missing.txt", "folder"):
            (self.root / "folder").mkdir(exist_ok=True)
            self.doc["files"][0]["path"] = path
            with self.assertRaises(SafeOpsError): self.call()

    def test_text_boundaries_and_noop(self):
        for content in ("no newline", "bad\r\n", "\ufeffBOM\n", "nul\0\n", "escape\x1b\n",
                        "control\x85\n", "\ud800\n", "Olá\nworld\n", "x\n" * 5001):
            with self.subTest(content=repr(content[:20])):
                self.doc["files"][0]["content"] = content
                with self.assertRaises(SafeOpsError): self.call()

    def test_invalid_original_text(self):
        for raw in (b"\xff\n", b"no final newline", b"CRLF\r\n"):
            self.source.write_bytes(raw)
            self.doc["files"][0]["base_sha256"] = hashlib.sha256(raw).hexdigest()
            with self.assertRaises(SafeOpsError): self.call()

    def test_empty_file_replacement_is_not_deletion(self):
        self.doc["files"][0]["content"] = ""
        self.assertIn("-world\n", self.call()["files"][0]["diff"])
        self.assertTrue(self.source.is_file())

    def test_bad_json_is_sanitized(self):
        for raw in (b'{"schema":1,"schema":1}', b'[]', b'{"oops":NaN}', b'\xff', b'PRIVATE-INVALID'):
            self.candidate.write_bytes(raw)
            with self.assertRaisesRegex(SafeOpsError, "unambiguous UTF-8 JSON") as error:
                preview.preview_candidate(self.root, self.candidate)
            self.assertNotIn("PRIVATE", str(error.exception))

    def test_candidate_and_source_size_limits(self):
        self.candidate.write_bytes(b" " * (preview.MAX_BYTES + 1))
        with self.assertRaisesRegex(SafeOpsError, "exceeds"): preview.preview_candidate(self.root, self.candidate)
        self.source.write_bytes(b"x" * (preview.MAX_BYTES + 1))
        with self.assertRaisesRegex(SafeOpsError, "exceeds"): self.call()

    def test_total_content_budget(self):
        with patch.object(preview, "MAX_TOTAL_BYTES", 1):
            with self.assertRaisesRegex(SafeOpsError, "byte limits"): self.call()

    def test_concurrent_edit_detected_before_return(self):
        self.save()
        original = preview._read_regular
        reads = []
        def read(path):
            reads.append(path)
            if len(reads) == 3: self.source.write_bytes(b"concurrent\n")
            return original(path)
        with patch.object(preview, "_read_regular", side_effect=read):
            with self.assertRaisesRegex(SafeOpsError, "Source changed"):
                preview.preview_candidate(self.root, self.candidate)

    def test_opened_file_identity_change_rejected(self):
        self.save()
        actual = os.fstat
        def changed(fd):
            value = actual(fd)
            return type("Changed", (), {"st_mode": value.st_mode, "st_dev": -1, "st_ino": -1})()
        with patch.object(preview.os, "fstat", side_effect=changed):
            with self.assertRaisesRegex(SafeOpsError, "changed during inspection"):
                preview.preview_candidate(self.root, self.candidate)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX FIFO required")
    def test_fifo_is_rejected_without_opening(self):
        fifo = self.root / "pipe"
        os.mkfifo(fifo)
        with self.assertRaisesRegex(SafeOpsError, "regular"):
            preview._read_regular(fifo)

    def test_symlink_file_and_parent_rejected(self):
        link = self.root / "link"
        try: link.symlink_to(self.source)
        except OSError: self.skipTest("Symlinks unavailable")
        with self.assertRaises(SafeOpsError): preview._read_regular(link)
        self.doc["files"][0]["path"] = "link"
        with self.assertRaises(SafeOpsError): self.call()
        link.unlink()
        link.symlink_to(self.root, target_is_directory=True)
        self.doc["files"][0]["path"] = "link/hello.txt"
        with self.assertRaises(SafeOpsError): self.call()


if __name__ == "__main__":
    unittest.main()
