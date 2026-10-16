# First GitHub alpha delivery — 2026-10-16

[Português (Portugal)](../pt-PT/audits/2026-10-16-first-alpha.md)

The maintainer authorized the first release. [v0.3.0a8](https://github.com/herculespt/euromind-safeops/releases/tag/v0.3.0a8)
is a published GitHub **prerelease**, at immutable source commit
`035c36b1b646a6c75178d5db6c19d8c55d624dcf`. Later main documentation does not
move that tag or replace its distributions.

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

**PyPI remains pending.** The secure sign-in request was interrupted; the account
still required sign-in at the last check. No Trusted Publisher grant, registry
upload, registry installation or registry attestation was verified. The manual
OIDC workflow is prepared, but has run only with publishing disabled.

No live model request was made for this delivery. Earlier OpenAI/Anthropic
smokes apply to source 0.3.0a2. At this tag, patch proposals, diff previews,
reviewed application, OS sandboxing and process-tree supervision remain planned.
See [current status](../STATUS.md), [roadmap](../../ROADMAP.md) and
[release procedure](../RELEASING.md) for current source and delivery boundaries.
