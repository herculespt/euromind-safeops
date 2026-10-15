# Maintainer guide — repository governance

This guide documents a **recommended policy**, not an assertion that branch protection has already been enabled.

## Repository authority and trust

- Public source: `herculespt/euromind-safeops`; primary branch `main`.
- Current maintainer: `@herculespt`; project is currently single-maintainer.
- Accept contributions via reviewable pull requests only. No model output or bot account can bypass security decisions.
- Never introduce private SEND code, credentials, device-specific state or unpublished infrastructure to this repository.
- GitHub Actions is the current test gate; it is not a sandbox, security audit or supply-chain attestation.

## Protect `main` in GitHub settings

> Repository owner action required. The ChatGPT GitHub connector cannot change repository branch protection, because GitHub application access excludes repository administration.

1. Go to **Settings → Branches → Add branch protection rule** (or **Settings → Rules → Rulesets → New branch ruleset**) and target `main`.
2. Enable **Require a pull request before merging**. Maintain a PR-only workflow, even for documentation and CI changes.
3. Enable **Require status checks to pass before merging** and select **`quality-gate`** after it appears in a completed CI run. This one check depends on successful completion of all nine Python/OS matrix jobs.
4. Enable **Require branches to be up to date before merging** and **Require conversation resolution before merging**.
5. Leave **Allow force pushes** and **Allow deletions** disabled; set **Do not allow bypassing the above settings** if available for the account and use case.
6. **Do not require an approving reviewer until a second trusted maintainer exists**: GitHub does not permit authors to approve their own PRs, so requiring one approval now can block legitimate maintenance. Continue human self-review with a written checklist until an independent reviewer is available.
7. Save changes, then reload **Settings → Branches** (or the ruleset view) and check that `main` is protected. Validate that an intentionally failing PR cannot merge.

This is a suggested minimal baseline, not a claim that GitHub settings have been changed. The required check name is deliberately stable across CI changes. Do not require individual matrix checks unless necessary: the aggregate check covers all of them.

## Change-control procedure

1. Open an Issue for changes affecting permissions, provider protocols, task execution, or trust boundaries.
2. Create a focused `feature/`, `fix/`, `docs/` or `chore/` branch from the current `main`.
3. Keep PRs self-contained. Complete the PR template and test the exact commit being merged.
4. Confirm `quality-gate` success and review GitHub Actions logs. For security-related changes, inspect the full diff even when CI is green.
5. Merge by squash to keep a concise history and avoid direct pushes to `main`.
6. For releases, use [Releasing](RELEASING.md); avoid claiming public packages or releases until they exist.

## Maintenance priorities

- Report security issues privately using [SECURITY.md](../SECURITY.md).
- Review Dependabot pull requests; updates are not automatically merged.
- Keep the changelog, roadmap, and implemented-versus-planned features in sync.
- Apply source and documentation changes as UTF-8; preserve PT-PT diacritics.
- Treat all tests as executable Python and run them only in a trusted development environment.
