"""Offline tooling policy and real pip refusal regressions; no provider access."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
POLICY = runpy.run_path(str(ROOT / "scripts/locked_tools.py"))


class ToolingPolicyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        shutil.copytree(ROOT / "requirements", self.root / "requirements")
        for profile in POLICY["PROFILES"]:
            shutil.copyfile(ROOT / f"requirements-{profile}.txt", self.root / f"requirements-{profile}.txt")

    def test_committed_closures_match_direct_pins_and_manifest(self):
        for profile in POLICY["PROFILES"]:
            _, pins = POLICY["validate_lock"](profile, self.root)
            self.assertNotIn("pip", pins)
            self.assertIn("setuptools", pins)

    def test_unpinned_unhashed_duplicate_and_url_requirements_are_refused(self):
        for text in ("coverage>=7\n", "coverage==7.16.2\n", "https://example.invalid/tool.whl\n",
                     "coverage==7.16.2 --hash=sha256:" + "a" * 64 + "\n" +
                     "Coverage==7.16.2 --hash=sha256:" + "a" * 64 + "\n"):
            with self.subTest(text=text):
                (self.root / "requirements-ci.txt").write_text(text, encoding="utf-8")
                with self.assertRaises(ValueError):
                    POLICY["validate_lock"]("ci", self.root)

    def test_changed_direct_version_is_refused(self):
        (self.root / "requirements/ci.in").write_text("coverage==1.0\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            POLICY["validate_lock"]("ci", self.root)

    def test_lock_hash_must_match_manifest(self):
        p = self.root / "requirements-ci.txt"
        lines = p.read_text().splitlines()
        lines[-1] = lines[-1].split("--hash=")[0] + "--hash=sha256:" + "0" * 64
        p.write_text("\n".join(lines) + "\n")
        with self.assertRaises(ValueError):
            POLICY["validate_lock"]("ci", self.root)

    def test_non_registry_origin_or_yanked_artifact_is_refused(self):
        p = self.root / "requirements/tooling-locks.json"
        for field, value in (("url", "https://example.invalid/tool.whl"), ("yanked", True)):
            d = json.loads((ROOT / "requirements/tooling-locks.json").read_text())
            d["profiles"]["ci"][0][field] = value
            p.write_text(json.dumps(d))
            with self.assertRaises(ValueError):
                POLICY["validate_lock"]("ci", self.root)

    def test_unsupported_profile_stops_before_pip(self):
        main = POLICY["main"]
        with patch.dict(main.__globals__, {"supported_profile": lambda: False}), patch("subprocess.run") as run:
            self.assertEqual(main(["ci"]), 2)
        run.assert_not_called()

    def test_installer_discards_external_pip_configuration(self):
        with patch.dict(os.environ, {"PIP_EXTRA_INDEX_URL": "https://example.invalid/", "PIP_REQUIRE_HASHES": "0"}):
            env = POLICY["pip_environment"]()
        self.assertNotIn("PIP_EXTRA_INDEX_URL", env)
        self.assertNotIn("PIP_REQUIRE_HASHES", env)
        self.assertEqual(env["PIP_CONFIG_FILE"], os.devnull)


class RealToolingHashTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        cls.wheels = cls.root / "wheels"
        cls.wheels.mkdir()
        subprocess.run([sys.executable, "-I", "-m", "venv", str(cls.root / "env")], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cls.python = cls.root / "env" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        cls.child = cls.wheel("safeops_tool_child")
        cls.parent = cls.wheel("safeops_tool_fixture", dependency="safeops-tool-child==1.0")

    @classmethod
    def wheel(cls, name, dependency=None):
        info = f"{name}-1.0.dist-info"
        files = {name + "/__init__.py": "", info + "/WHEEL": "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
                 info + "/METADATA": f"Metadata-Version: 2.1\nName: {name}\nVersion: 1.0\n" +
                 (f"Requires-Dist: {dependency}\n" if dependency else "")}
        files[info + "/RECORD"] = "".join(p + ",,\n" for p in [*files, info + "/RECORD"])
        path = cls.wheels / f"{name}-1.0-py3-none-any.whl"
        with ZipFile(path, "w") as z:
            for p, content in files.items():
                z.writestr(p, content)
        return path

    def install(self, lines):
        lock = self.root / "fixture.txt"
        lock.write_text("\n".join(lines) + "\n", encoding="utf-8")
        command = POLICY["install_command"](lock, self.wheels)
        command[0] = str(self.python)
        return subprocess.run(command, env=POLICY["pip_environment"](), text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)

    def pin(self, name, wheel):
        return f"{name}==1.0 --hash=sha256:{hashlib.sha256(wheel.read_bytes()).hexdigest()}"

    def test_valid_offline_closure_and_changed_hash_even_if_already_installed(self):
        lines = [self.pin("safeops-tool-fixture", self.parent), self.pin("safeops-tool-child", self.child)]
        result = self.install(lines)
        self.assertEqual(result.returncode, 0, result.stderr)
        changed = [lines[0].split("--hash=")[0] + "--hash=sha256:" + "0" * 64, lines[1]]
        refused = self.install(changed)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("DO NOT MATCH", refused.stderr)

    def test_missing_transitive_pin_cannot_fall_back_to_resolution(self):
        refused = self.install([self.pin("safeops-tool-fixture", self.parent)])
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("--require-hashes", refused.stderr)


if __name__ == "__main__":
    unittest.main()
