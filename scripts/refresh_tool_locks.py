"""Review wheelhouse metadata against PyPI and prepare lock changes for a PR.

Resolve/download first in the documented target; this does not install packages,
commit, approve, publish, or automatically select direct tool upgrades.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import runpy
import urllib.request
from zipfile import ZipFile


def main():
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name
    policy = runpy.run_path(str(Path(__file__).with_name("locked_tools.py")))
    if not policy["supported_profile"]():
        raise ValueError("Refresh requires the documented tooling target")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheelhouse", type=Path, required=True)
    args = parser.parse_args()
    def inspect_wheel(wheel):
        with ZipFile(wheel) as archive:
            names = [n for n in archive.namelist() if n.endswith(".dist-info/METADATA") and n.count("/") == 1]
            if len(names) != 1:
                raise ValueError("Ambiguous wheel metadata")
            m = BytesParser().parsebytes(archive.read(names[0]))
        name, version = canonicalize_name(m["Name"]), m["Version"]
        url = f"https://pypi.org/pypi/{name}/{version}/json"
        with urllib.request.urlopen(url, timeout=30) as response:
            raw = response.read(4_000_001)
        if len(raw) > 4_000_000:
            raise ValueError("Registry metadata too large")
        data = json.loads(raw)
        candidates = [r for r in data["urls"] if r["filename"] == wheel.name]
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
        if (len(candidates) != 1 or candidates[0]["digests"]["sha256"] != digest or
                candidates[0]["yanked"] or candidates[0]["packagetype"] != "bdist_wheel" or
                not candidates[0]["url"].startswith("https://files.pythonhosted.org/packages/")):
            raise ValueError("Wheel differs from approved registry origin")
        record = {"name": name, "version": version, "filename": wheel.name,
                           "digest": "sha256:" + digest, "url": candidates[0]["url"], "yanked": False}
        return name, record, m
    artifacts, metadata = {}, {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for name, record, m in pool.map(inspect_wheel, sorted(args.wheelhouse.glob("*.whl"))):
            if name in artifacts:
                raise ValueError("Multiple wheels for one tool; use a fresh wheelhouse")
            artifacts[name], metadata[name] = record, m
    root = policy["ROOT"]
    profiles = {}
    for profile in policy["PROFILES"]:
        direct = policy["read_pins"](root / "requirements" / f"{profile}.in", hashed=False)
        selected, pending = set(), list(direct)
        while pending:
            name = pending.pop()
            if name in selected:
                continue
            if name not in artifacts:
                raise ValueError("Missing dependency wheel")
            if name in direct and artifacts[name]["version"] != direct[name][0]:
                raise ValueError("Direct version mismatch")
            selected.add(name)
            for value in metadata[name].get_all("Requires-Dist", []):
                requirement = Requirement(value)
                if requirement.marker and not requirement.marker.evaluate({"extra": ""}):
                    continue
                dependency = canonicalize_name(requirement.name)
                if (requirement.url or requirement.extras or dependency not in artifacts or
                        artifacts[dependency]["version"] not in requirement.specifier):
                    raise ValueError("Unsupported or unsatisfied active dependency")
                pending.append(dependency)
        profiles[profile] = [artifacts[n] for n in sorted(selected)]
    manifest = {"schema": 1, "target": "cpython-3.12-linux-x86_64-glibc>=2.34", "profiles": profiles}
    (root / "requirements/tooling-locks.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for profile, records in profiles.items():
        lines = ["# Reviewed wheel closure: CPython 3.12 / Linux x86_64 / glibc >=2.34.",
                 "# Install with scripts/locked_tools.py; refresh policy: docs/TOOLING.md.",
                 "# Other platforms/Python versions are unsupported by this tooling lock."]
        lines += [f"{r['name']}=={r['version']} --hash=sha256:{r['digest'].removeprefix('sha256:')}" for r in records]
        (root / f"requirements-{profile}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        policy["validate_lock"](profile)
        print(f"Prepared {profile}: {len(records)} reviewed wheel identities; inspect diff before PR")


if __name__ == "__main__":
    main()
