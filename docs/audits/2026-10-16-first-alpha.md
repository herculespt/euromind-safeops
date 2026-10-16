# First GitHub and PyPI alpha delivery — 2026-10-16

[Português (Portugal)](../pt-PT/audits/2026-10-16-first-alpha.md)

The maintainer authorized the first release. [v0.3.0a8](https://github.com/herculespt/euromind-safeops/releases/tag/v0.3.0a8)
is a published GitHub **prerelease**, at immutable source commit
`035c36b1b646a6c75178d5db6c19d8c55d624dcf`. Later main documentation does not
move that tag or replace its distributions.
The same original distributions were published to
[PyPI 0.3.0a8](https://pypi.org/project/euromind-safeops/0.3.0a8/) on the same date.

| Evidence | Verified result |
|---|---|
| Protected main | Ruleset 25151466 active; PR, strict quality-gate, resolved threads, zero required approvals, deletion/force-push blocked, no bypass actors |
| Source integration | PRs #33 and #34 merged after twelve successful jobs each |
| Exact main CI | [38838771250](https://github.com/herculespt/euromind-safeops/actions/runs/38838771250): twelve jobs successful |
| Candidate workflow | [38838948133](https://github.com/herculespt/euromind-safeops/actions/runs/38838948133): successful, publish=false |
| Published-byte workflow | [38839267524](https://github.com/herculespt/euromind-safeops/actions/runs/38839267524): downloaded exact release wheel/sdist/SHA256SUMS, hashes/metadata/scans/installed tests passed; publish=false |
| Local attached-wheel validation | Installed outside checkout: 209 tests, 3 platform-specific skips, zero failures/errors; strict Twine check passed |
| Independent scan | Network verification disabled; seven reviewed synthetic path/type/hash identities in source/sdist, zero wheel findings; changed fixture values and malformed baseline rejected |
| Private-byte comparison | Locally held provider credential bytes absent from public source and expanded distributions; values not logged or uploaded |
| Public assets | Exactly one wheel, one built sdist and SHA256SUMS, with matching GitHub asset digests; generated source ZIP/tar are additional GitHub links |
| Authorized Trusted Publisher | `herculespt/euromind-safeops`, `publish.yml`, environment `pypi`; explicit action-time authorization on 2026-10-16 |
| Publishing environment | Selected branch `main` only, one branch/zero tags, administrator bypass disabled; no environment secrets or variables; no required reviewer while there is one maintainer |
| PyPI delivery and registry installation | [38874124869](https://github.com/herculespt/euromind-safeops/actions/runs/38874124869), attempt 1: all three jobs passed, original distributions retrieved without rebuilding, installed-wheel suite passed 209 tests/3 platform skips, exact registry filenames/SHA-256 and fresh registry installation/CLI version verified |
| Publishing attestations | Both file-detail pages show Trusted Publishing used and a PyPI Publish attestation signed by GitHub Actions and verified by PyPI on 2026-10-16; subjects and SHA-256 match the two files below |

The first candidate [38836891550](https://github.com/herculespt/euromind-safeops/actions/runs/38836891550)
failed on synthetic fixtures. PR #34 added a strict reviewed hash policy and
nine regressions; no test file is excluded. The failed evidence is preserved.

```text
559e2b89c8d80d02562605c8a517b7b2096d4df9e9958eb35fbe93cdca18436c  packages/euromind_safeops-0.3.0a8-py3-none-any.whl
ff2bae29339d1ac5b9177711409d5e363575de6cda12e902035755f7367a2958  packages/euromind_safeops-0.3.0a8.tar.gz
```

Download SHA256SUMS and put the two packages in a `packages/` subdirectory.
Run `sha256sum --check SHA256SUMS` before installing the verified wheel. This is
not a claim of fully reproducible builds or signed provenance.

**PyPI delivery completed.** Earlier account-access interruptions are preserved
in issue #31; secure sign-in and the authorized publisher grant were subsequently
completed. The wheel was uploaded at 08:31:15 UTC and the sdist at 08:31:17 UTC.
The registry contains exactly the original wheel and sdist, with the SHA-256
values above. SHA256SUMS remains a GitHub release asset, not a registry package.

The [wheel details](https://pypi.org/project/euromind-safeops/0.3.0a8/#euromind_safeops-0.3.0a8-py3-none-any.whl)
and [sdist details](https://pypi.org/project/euromind-safeops/0.3.0a8/#euromind_safeops-0.3.0a8.tar.gz)
were inspected directly. Each attestation identifies repository
`herculespt/euromind-safeops`, workflow `.github/workflows/publish.yml`, publishing
commit `95a8bd51b2eb657233a9100f85c87be1b6548649` and workflow run 38874124869,
attempt 1. Transparency-log indices shown by PyPI are 3276393757 (wheel) and
3276393456 (sdist). These are verified publishing-identity observations, not an
independent local Sigstore verification, reproducible-build proof or signed
SafeOps plan/approval records. The publishing workflow ran from current main
and retrieved release bytes; package source remains commit `035c36b1b646a6c75178d5db6c19d8c55d624dcf`.

Install the published alpha in a fresh virtual environment:

```bash
python -m venv .venv
# Activate the virtual environment for your shell, then:
python -m pip install --no-cache-dir --no-deps --index-url https://pypi.org/simple euromind-safeops==0.3.0a8
safeops --version
```

At registry publication, main source 0.3.0a11 included later previews, proposals and staging copies;
these are absent from the immutable 0.3.0a8 registry package. Documentation and
release-note updates do not rewrite the package's embedded description.

No live model request was made for this delivery. Earlier OpenAI/Anthropic
smokes apply to source 0.3.0a2. At this tag, patch proposals, diff previews,
reviewed application, OS sandboxing and process-tree supervision remain planned.
See [current status](../STATUS.md), [roadmap](../../ROADMAP.md) and
[release procedure](../RELEASING.md) for current source and delivery boundaries.
