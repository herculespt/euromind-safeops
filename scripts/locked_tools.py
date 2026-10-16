"""Install reviewed maintainer tools; never used by the runtime package."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("ci", "release")
PIN = re.compile(r"([A-Za-z0-9][A-Za-z0-9._-]*)==([0-9][A-Za-z0-9.!+_-]*)")
HASHED = re.compile(PIN.pattern + r" --hash=sha256:([0-9a-f]{64})")


def canonical(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def supported_profile():
    libc, version = platform.libc_ver()
    return (sys.implementation.name == "cpython" and sys.version_info[:2] == (3, 12)
            and sys.platform == "linux" and platform.machine() == "x86_64"
            and libc == "glibc" and tuple(map(int, version.split(".")[:2])) >= (2, 34))


def read_pins(path, *, hashed):
    pins = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        match = (HASHED if hashed else PIN).fullmatch(line)
        if not match or canonical(match[1]) in pins:
            raise ValueError("Invalid, duplicate or unpinned tool requirement")
        pins[canonical(match[1])] = match.groups()[1:]
    if not pins:
        raise ValueError("Empty tool requirements")
    return pins


def validate_lock(profile, root=ROOT):
    if profile not in PROFILES:
        raise ValueError("Unsupported tooling profile")
    lock = root / f"requirements-{profile}.txt"
    pins = read_pins(lock, hashed=True)
    direct = read_pins(root / "requirements" / f"{profile}.in", hashed=False)
    if any(name not in pins or pins[name][0] != value[0] for name, value in direct.items()):
        raise ValueError("Direct tool requirements differ from lock")
    manifest = json.loads((root / "requirements/tooling-locks.json").read_text(encoding="utf-8"))
    if type(manifest["schema"]) is not int or manifest["schema"] != 1 or manifest["target"] != "cpython-3.12-linux-x86_64-glibc>=2.34":
        raise ValueError("Unsupported tooling manifest")
    records = manifest["profiles"][profile]
    if any(not re.fullmatch(r"sha256:[0-9a-f]{64}", r["digest"]) for r in records):
        raise ValueError("Invalid approved wheel digest")
    observed = {r["name"]: (r["version"], r["digest"].removeprefix("sha256:")) for r in records}
    if len(observed) != len(records) or observed != pins:
        raise ValueError("Tooling lock/manifest mismatch")
    for r in records:
        if (not r["filename"].endswith(".whl") or "/" in r["filename"] or
                not r["url"].startswith("https://files.pythonhosted.org/packages/") or
                r["yanked"] is not False):
            raise ValueError("Invalid approved wheel origin")
    return lock, pins


def pip_environment():
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("PIP_")}
    env["PIP_CONFIG_FILE"] = os.devnull
    return env


def install_command(lock, wheelhouse=None):
    command = [sys.executable, "-I", "-m", "pip", "--isolated", "--disable-pip-version-check",
               "install", "--require-hashes", "--only-binary=:all:", "--force-reinstall", "--no-cache-dir",
               "--no-input", "--keyring-provider", "disabled"]
    if wheelhouse is None:
        command += ["--index-url", "https://pypi.org/simple"]
    else:
        directory = wheelhouse.resolve(strict=True)
        if not directory.is_dir():
            raise ValueError("Wheelhouse must be a local directory")
        command += ["--no-index", "--find-links", str(directory)]
    return command + ["-r", str(lock)]


def inventory():
    values = [(canonical(d.metadata["Name"]), d.version) for d in importlib.metadata.distributions()]
    if len(dict(values)) != len(values):
        raise ValueError("Duplicate installed tool metadata")
    return dict(values)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", choices=PROFILES)
    parser.add_argument("--check", action="store_true", help="Check profile and committed lock without installation")
    parser.add_argument("--wheelhouse", type=Path, help="Use only a local wheel directory with the same reviewed hashes")
    args = parser.parse_args(argv)
    try:
        if not supported_profile():
            raise ValueError("Tooling requires CPython 3.12 / Linux x86_64 / glibc >=2.34")
        lock, pins = validate_lock(args.profile)
        if args.check:
            print(f"Reviewed {args.profile} tooling lock verified ({len(pins)} wheels)")
            return 0
        if sys.prefix == sys.base_prefix:
            raise ValueError("Create a dedicated virtual environment before installing tools")
        expected = {n: v[0] for n, v in pins.items()}
        before = inventory()
        if "pip" not in before:
            raise ValueError("Trusted bootstrap pip is unavailable")
        expected["pip"] = before["pip"]
        if set(before) - (set(expected) | {"pip", "setuptools"}):
            raise ValueError("Tool environment contains unrelated packages; create a fresh venv")
        env = pip_environment()
        subprocess.run(install_command(lock, args.wheelhouse), env=env, check=True)
        subprocess.run([sys.executable, "-I", "-m", "pip", "--isolated", "check"], env=env, check=True)
        # Query in a fresh interpreter: pip may replace metadata imported by this process.
        code = "import importlib.metadata as m,json,re;print(json.dumps([(re.sub(r'[-_.]+','-',d.metadata['Name']).lower(),d.version) for d in m.distributions()]))"
        actual = json.loads(subprocess.check_output([sys.executable, "-I", "-c", code], env=env, text=True))
        if len(actual) != len(expected) or dict(actual) != expected:
            raise ValueError("Installed tool inventory differs from reviewed closure")
        print(f"Installed exact {args.profile} tooling closure ({len(pins)} wheels); dependency check passed")
        return 0
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError):
        print("Tooling validation/installation failed; no unrestricted fallback", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
