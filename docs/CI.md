# CI and package build contract

[Português (Portugal)](pt-PT/CI.md)

## Required gate

`quality-gate` retains its stable required-check name. It runs with `always()`
and succeeds only when both the nine-environment test matrix and the two
distribution jobs succeed. Failed, cancelled or skipped prerequisites cannot
produce a successful gate. Branch protection also requires an up-to-date PR.

The test matrix covers Python 3.11, 3.12 and 3.13 on GitHub-hosted Linux, Windows
and macOS. Each job installs the package, runs unit tests, compiles the source,
checks credential patterns and builds a wheel. Jobs have explicit timeouts.

Provider tests use transport doubles and bind temporary HTTP fixture servers only
to 127.0.0.1 on OS-assigned ports. They need no API keys or external model access.
The same tests run against installed wheels. See [provider validation](PROVIDER_TESTING.md)
for the separate successful OpenAI and Anthropic smoke tests and remaining provider/model gaps. Live requests are not added to CI.

## Reviewed Actions — 2026-10-15

| Action | Release | Official commit |
|---|---|---|
| `actions/checkout` | v7.0.0 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| `actions/setup-python` | v7.0.0 | `5fda3b95a4ea91299a34e894583c3862153e4b97` |

Both SHAs were resolved from the official `actions/*` repositories and reviewed
against upstream release notes and action metadata. They use Node 24, requiring
runner 2.327.1 or later; this project uses GitHub-hosted runners. Checkout v7's
additional restrictions affect privileged `pull_request_target` / `workflow_run`
fork checkouts, which this CI does not use. The removed setup-python `pip-install`
input is not used here. The `python-version` input remains supported.

Checkout uses `persist-credentials: false`: these jobs do not push. The workflow
keeps `contents: read`, does not receive production secrets and has no publishing
step. Dependabot remains responsible for proposing reviewed updates to pinned
Actions; tags and comments alone do not authorize integration.

These pins address direct Action references. They do not make runner images,
downloaded Python interpreters or all build dependencies immutable. Workflow
dependency lockfiles and complete build reproducibility remain separate work.

## Build backend and artifacts

The previous `setuptools>=68` floor was reproduced failing to parse the SPDX
license expression in `pyproject.toml`. Although that metadata requires version
77 or later, the tested supported floor is **83.0.0**, including later upstream
dependency and Unicode manifest fixes. Python 3.11+ remains supported. Setuptools
provides its wheel builder; a separate unversioned `wheel` build requirement is
unnecessary. There are still no third-party runtime dependencies.

Two Linux / Python 3.11 distribution jobs install exactly setuptools 83.0.0 or
the latest compatible setuptools, respectively. Both use `python -m build
--no-isolation`: the wheel is built from the generated source archive, using
the selected backend without silently replacing it. They verify name, version,
SPDX license, included license, type marker, absence of runtime dependencies,
public English/PT-PT documentation and absence of common runtime/`.env` paths.
These path checks complement the heuristic scanner and do not prove that every
secret format is absent.

`MANIFEST.in` includes community documents, detailed documentation, the demo,
tests and the CI files needed by the repository hygiene tests in source archives.
Generated state and environment files are excluded. Each job then installs the
wheel with no index or dependency resolution in a fresh virtual environment and
checks both CLI entry points outside the checkout. It also runs the complete test
suite against the installed wheel from that external working directory. This
exercises the packaged child runner, rather than relying only on editable source
imports. Tests remain in the source archive, not in the runtime wheel. No artifact
is published.

## Review and rollback

After a green PR, inspect its complete diff and merge the tested head. If a CI
change fails after integration, prepare a revert PR and run the same gate; do not
rewrite history or weaken the required checks. Releases need separate approval.

## Primary references

- [Checkout v7.0.0 release notes](https://github.com/actions/checkout/releases/tag/v7.0.0)
- [Setup-python v7.0.0 release notes](https://github.com/actions/setup-python/releases/tag/v7.0.0)
- [GitHub secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [Setuptools pyproject configuration](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html)
- [Setuptools history](https://setuptools.pypa.io/en/latest/history.html)
- [Upstream setuptools path-traversal advisory](https://github.com/pypa/setuptools/security/advisories/GHSA-5rjg-fvgr-3xxf)
