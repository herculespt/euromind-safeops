# Release procedure

There is **no claim that a GitHub Release or PyPI distribution already exists**. Repository commits are not release tags, and successful CI does not publish software.

## Preconditions

- `main` is protected and `quality-gate` is required.
- The intended release scope and risk are reviewed in a pull request.
- Versions in `pyproject.toml` and `src/euromind_safeops/__init__.py` agree.
- CLI help, current EN/PT-PT document markers, [status](STATUS.md), roadmap and changelog agree; dated audit baselines remain historical.
- Execution-contract changes have an explicit compatibility decision; approvals are never silently migrated.
- `CHANGELOG.md`, `README.md`, support notes, and provider docs describe what is implemented, with unresolved limitations stated clearly.
- No private credentials, proprietary code or source-tree runtime `.safeops` data are included.

## Local checks

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m compileall -q src tests
safeops --root . scan
python -m pip wheel --no-deps --wheel-dir dist .
```

A built-in scanner is not sufficient for secure release. Inspect `git diff`, use an independent secret scanner, and review the source distribution for unexpected assets.

## Publish a GitHub release (human maintainer)

1. Merge the release PR after all required checks pass.
2. In GitHub, open **Releases → Draft a new release**.
3. Create a new version tag matching the approved package version on the verified release commit; do not reuse tags. Use an alpha suffix such as `v0.3.0a6` for the current source milestone if that prerelease is separately authorized for publication.
4. Use the matching changelog section as release notes and explicitly label the release **Alpha** or **Pre-release** if applicable.
5. Verify that the released tag matches the tested source commit and that license, archive and documentation are present.
6. Publish the GitHub Release only after the maintainer has checked the tag, notes and source archives.

## Package registry publication

PyPI publishing, signing, attestations and trusted publishing have **not** been configured. Do not publish with a long-lived API token or automate this step until trusted-publishing permissions, package ownership, provenance and a separate release security review are implemented. Avoid describing the project as released on PyPI until the registry entry has been verified.

## Rollback

Do not rewrite a public release tag after publication. If a fault is found, open an Issue/advisory as appropriate, prepare a reviewed fix, and issue a new patch version. For security problems, follow the private disclosure process.
