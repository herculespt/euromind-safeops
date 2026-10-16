# Reviewed maintainer tooling — 0.3.0a18

<!-- safeops-version: 0.3.0a18 -->

[Português (Portugal)](pt-PT/TOOLING.md)

The source 0.3.0a18 tooling policy covers dedicated **CPython 3.12, Linux x86_64,
glibc >=2.34** environments. It does not change the dependency-free runtime or
its Linux/Windows/macOS Python 3.11–3.13 compatibility matrix.

| Profile | Direct tools | Installation use |
|---|---|---|
| `ci` | setuptools 83.0.0, coverage 7.16.2 | Linux/Python 3.12 measured tests |
| `release` | build 1.6.1, setuptools 83.0.0, twine 7.0.0, detect-secrets 1.5.0 | Manual candidate/release validation |

[Direct CI inputs](../requirements/ci.in) and [release inputs](../requirements/release.in)
are separate from complete [CI](../requirements-ci.txt) and
[release](../requirements-release.txt) closures. The reviewed
[manifest](../requirements/tooling-locks.json) records each exact wheel filename,
version, SHA-256 and PyPI file URL, including platform-specific transitive wheels.
The glibc floor includes the selected cryptography wheel, not just coverage.

## Installation and refusal

Create a fresh virtual environment using the supported interpreter, then run:

```sh
python3.12 -m venv /tmp/safeops-tools
/tmp/safeops-tools/bin/python scripts/locked_tools.py ci
# For release tools, create a separate fresh venv and select release instead.
```

`--check` checks the target and committed direct/lock/manifest bindings without
installing. The installer rejects unrelated installed packages and global Python.
It disables external pip environment/configuration, keyring, cache and interactive
input; requires SHA-256 for every pinned direct/transitive dependency; accepts only
wheels from the explicit PyPI index; reinstalls even already-present versions; runs
`pip check`; and verifies the exact final inventory in a fresh interpreter.
Missing pins, modified bytes, missing wheels, unsupported profiles or dependency
conflicts fail with no unrestricted retry. A failure can leave a partially installed
tool venv: discard that disposable environment and investigate before recreating it.

For a previously verified local wheel directory, add `--wheelhouse /absolute/path`.
This uses `--no-index`, with the same hashes and dependency checks. It does not trust
the directory's contents merely because they are local. Do not install from `.in`
files or omit the installer/hash flags during normal use.

After the CI tools are installed, install the local project with that interpreter:

```sh
/tmp/safeops-tools/bin/python -m pip --isolated install --no-index --no-deps --no-build-isolation -e .
```

The local project is reviewed repository code, rather than a third-party hashed
wheel. Its backend is already locked; this command cannot fetch build/runtime
dependencies. Build release candidates with `python -m build --no-isolation` in
the release environment. No additional wheel package is needed by setuptools 83.

## Workflow boundaries

CI creates the `ci` environment before measured-project installation. The other
eight platform jobs deliberately exercise ordinary project build isolation. The two
Linux/Python 3.11 distribution jobs deliberately resolve minimum/latest compatible
setuptools and build tooling. Those compatibility jobs are **not locked release
environments**; their independent wheel suites and stable twelve-job quality-gate
remain required. This exception tests compatibility rather than claiming identical
dependency bytes across every test environment.

The manual publication workflow creates the `release` environment from the
**workflow source before checking out an historical release tag**. Historical tags
may lack these files; they do not choose the current workflow's installer policy.
Exact tag ancestry/main CI, original release-byte checks, publication=false default,
OIDC/environment authority and registry verification remain mandatory. This policy
change does not run publication, move tags or replace public 0.3.0a8 assets.

Interpreter/ensurepip bootstrap, runner images, system libraries, GitHub Actions
and publication-action container dependencies are separate trust boundaries. The bootstrap pip is not upgraded by these profiles; its observed version is preserved and checked in the final inventory.
Hashes establish approved artifact identity, not absence of vulnerabilities,
reproducible builds, signed SafeOps approvals or hostile-code containment.

## Controlled refresh

Use a separate supported disposable environment. Review upstream releases and
advisories before changing direct `.in` versions. Resolve into an empty temporary
wheel directory using only the official index:

```sh
python -m pip --isolated download --only-binary=:all: --index-url https://pypi.org/simple \
  --dest /tmp/safeops-reviewed-wheels -r requirements/ci.in -r requirements/release.in
python scripts/refresh_tool_locks.py --wheelhouse /tmp/safeops-reviewed-wheels
```

The refresh helper requires packaging from the existing release tools. It reads
wheel metadata without importing their code, checks local hashes against exact,
non-yanked PyPI file records, evaluates active target dependencies and prepares both
closures/manifest. Resolution here intentionally selects new transitive versions;
it is a maintainer review step, never an automatic CI fallback. Inspect every changed
version, filename, dependency, license and platform floor. Add no unrelated wheels
or alternative origins without a reviewed policy change.

Validate fresh online and offline installations, `pip check`, coverage, build,
strict Twine, secret scans and an installed-wheel suite. Offline regression tests
also use real pip to reject an altered hash even for an already-installed version
and a missing transitive pin. Update both languages, status/roadmap/changelog and
version bindings as needed; use a branch/PR and require green PR/main CI. No release
or new publishing permission is implied by a lock refresh.

Primary references: [pip secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/),
[pip configuration](https://pip.pypa.io/en/stable/topics/configuration/),
[PyPI JSON API](https://docs.pypi.org/api/json/).
