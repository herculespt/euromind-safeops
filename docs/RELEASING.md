# Alpha release and package procedure — 0.3.0a8

<!-- safeops-version: 0.3.0a8 -->

[Português (Portugal)](pt-PT/RELEASING.md)

The maintainer authorized this first alpha delivery on 2026-10-15. Future
releases require their own authorization. See [status](STATUS.md) and
[issue #31](https://github.com/herculespt/euromind-safeops/issues/31) for actual
publication evidence. A successful candidate validation does not publish to PyPI.

## Review and GitHub release

Merge through a reviewed PR, with active main protection and all required
checks passing. Verify the exact source/version, EN/PT-PT documentation,
license, public source contents and alpha limits. Preserve dated evidence and
Git history. Build tools are pinned in requirements-release.txt; transitive
dependencies and runner images are not fully locked.

The package uses bilingual [PACKAGE.md](PACKAGE.md), with absolute links for
registry display. Check wheel/sdist metadata with twine check --strict, run the
full installed-wheel suite outside the checkout, and inspect source/distributions
with the built-in and independent secret scanners. Disable network credential
verification. Scanners do not prove that every secret format is absent.

Create a new matching tag, such as v0.3.0a8, on the verified exact commit with
successful main push CI. Do not reuse/move public tags. Publish as Pre-release
with EN/PT-PT features, test/coverage evidence, upgrade approval requirements and
separate PyPI status. Attach the validated wheel, sdist and SHA256SUMS. Verify
the tag/commit, pre-release flag, notes and downloadable asset names/bytes.
GitHub's generated source ZIP/tar are distinct from built registry distributions.


The independent scanner uses a reviewed hash baseline for seven synthetic test
fixtures across three test files (reviewed 2026-10-16). It contains no credential
values and does not exclude test source files. The control file is validated
against a strict hash-only schema before excluding its own hashes, and a packaged
copy must match the reviewed source bytes. A changed or newly detected value must
be reviewed; never regenerate the baseline merely to make publication pass. Both
tracked source and expanded distributions use the same baseline with network
verification disabled.

## Manual package workflow

[Alpha package publication](../.github/workflows/publish.yml) is manual only
from this repository's main. It does not run on PRs, tags or releases.
The publish input defaults to false. An empty tag validates a candidate only.
An explicit tag requires an existing published alpha GitHub Release.

The build job verifies exact source ancestry on main, the latest successful
main push CI for that SHA, quality-gate and alpha tag/package version equality.
Candidate validation builds from source. A tagged run retrieves the exact
wheel/sdist/SHA256SUMS from the GitHub Release, validates filenames and hashes
and retains those reviewed package bytes for PyPI. It checks metadata, runs the
installed-wheel full suite, and stores only packages/checksums as a seven-day
Actions artifact. Test, JUnit, coverage and local-state reports are not uploaded.

With publish=true and an explicit alpha tag, a separate job in environment
pypi verifies transferred SHA-256 and invokes the pinned PyPA publisher.
Only that job receives id-token: write; it has no checkout or long-lived token.
The build has contents/actions read only. A final job compares actual PyPI
filenames/hashes and installs the exact version from the real registry into a
fresh environment, checking metadata and the CLI version. Upload is not undone
by a later verification failure. Inspect existing registry state before retrying;
never silently skip/replace an existing version.

### Reviewed Actions — 2026-10-15

| Action | Release | Official commit |
|---|---|---|
| upload-artifact | v7.0.2 | cf430e030ddbb5b0abf93d22962f4752f3646cd9 |
| download-artifact | v8.0.2 | 9000827ccba6bdab643e8b6fd33ac0654aef8333 |
| PyPA publisher | v1.14.2 | dc37677b2e1c63e2034f94d8a5b11f265b73ba33 |

Checkout/setup-python retain [CI](CI.md) pins. The publisher requests
attestations, but do not claim verified provenance until real registry evidence
has been examined. Reports remain separate from this package-only transfer.

## PyPI account prerequisite

Authenticate securely to the intended account, with email/2FA as PyPI requires.
Never put credentials or recovery codes into chat, Git or logs.
For a new project, register the following exact pending Trusted Publisher:

| Field | Value |
|---|---|
| PyPI project | euromind-safeops |
| GitHub owner | herculespt |
| Repository | euromind-safeops |
| Workflow filename | publish.yml |
| GitHub environment | pypi |

Confirm ownership/name availability and review the precise trust grant before
saving it. Pending registration does not reserve the project name. Committing
the workflow alone grants no PyPI access. No API token fallback is configured.
Verify the publisher and applicable environment protections before dispatching
publication. After a successful candidate dry run, publish only the authorized
alpha and record URLs, filenames, hashes, installation and actual attestations.
Keep PyPI pending if authentication, registration or verification is incomplete.

## Later changes

Never rewrite public tags or distribution bytes. Prepare a reviewed fix and a
newly authorized version for defects; use private security reporting as needed.
Documentation-only status updates can follow through PR without changing the
released version. Distinguish the immutable release commit from current main.
Source/configuration/version changes still require a new reviewed SafeOps
plan and explicit approval; no automatic renewal or history rewriting.

## Primary references

- [Pending publishers](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
- [Trusted Publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
- [Trust security model](https://docs.pypi.org/trusted-publishers/security-model/)
- [Official PyPA publisher](https://github.com/pypa/gh-action-pypi-publish)
