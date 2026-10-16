# Maintainer guide — repository governance

## Verified protection baseline — 2026-10-15

After explicit maintainer authorization, the **Protect main** branch ruleset
([ID 25151466](https://github.com/herculespt/euromind-safeops/rules/25151466)) was
created and verified as **active**, targeting exactly `refs/heads/main`.

- Pull requests are required, with **zero required approving reviews** while the project has one maintainer.
- `quality-gate` is required from **GitHub Actions**; the branch must be up to date.
- Review conversations must be resolved.
- Deletion and non-fast-forward updates are blocked.
- The bypass list is empty; the authenticated maintainer's reported bypass permission was `never`.
- The branch API reported `protected: true`; source history was unchanged by this administrative action.

This is a dated observation, not a guarantee that repository settings cannot
change. Recheck the active ruleset before relying on it. See the
[audit](audits/2026-10-15.md) and [Português (Portugal)](pt-PT/MAINTAINER_GUIDE.md).

## Repository authority and trust

- Public source: `herculespt/euromind-safeops`; primary branch `main`.
- Current maintainer: `@herculespt`; project is currently single-maintainer.
- Accept contributions via reviewable pull requests only. No model output or bot account can bypass security decisions.
- Never introduce private application code, credentials, device-specific state or unpublished infrastructure to this repository.
- GitHub Actions is the current test gate; it is not a sandbox, security audit or supply-chain attestation.

## Protect `main` in GitHub settings

> Changes require repository administration access. The GitHub connector used
> for source changes does not expose administrative writes; the baseline above
> was applied through the authenticated GitHub settings UI after authorization.

1. Go to **Settings → Branches → Add branch protection rule** (or **Settings → Rules → Rulesets → New branch ruleset**) and target `main`.
2. Enable **Require a pull request before merging**. Maintain a PR-only workflow, even for documentation and CI changes.
3. Enable **Require status checks to pass before merging** and select **`quality-gate`** after it appears in a completed CI run. This one check requires all nine Python/OS environments and both distribution jobs; see [CI and package build contract](CI.md).
4. Enable **Require branches to be up to date before merging** and **Require conversation resolution before merging**.
5. Leave **Allow force pushes** and **Allow deletions** disabled; set **Do not allow bypassing the above settings** if available for the account and use case.
6. **Do not require an approving reviewer until a second trusted maintainer exists**: GitHub does not permit authors to approve their own PRs, so requiring one approval now can block legitimate maintenance. Continue human self-review with a written checklist until an independent reviewer is available.
7. Save changes, then reload **Settings → Branches** (or the ruleset view) and check that `main` is protected. Validate that an intentionally failing PR cannot merge.

These steps describe how to reproduce or review the baseline. The required check name is deliberately stable across CI changes. Do not require individual matrix checks unless necessary: the aggregate check covers all of them.

## Change-control procedure

1. Open an Issue for changes affecting permissions, provider protocols, task execution, or trust boundaries.
2. Create a focused `feature/`, `fix/`, `docs/` or `chore/` branch from the current `main`.
3. Keep PRs self-contained. Complete the PR template and test the exact commit being merged.
4. Confirm `quality-gate` success and review GitHub Actions logs. For security-related changes, inspect the full diff even when CI is green.
5. Merge the tested head through the PR with a merge commit to preserve the branch's commits and ancestry. Do not push directly to `main` or rewrite history.
6. For releases, use [Releasing](RELEASING.md); avoid claiming public packages or releases until they exist.

## Maintenance priorities

- Report security issues privately using [SECURITY.md](../SECURITY.md).
- Review Dependabot pull requests; updates are not automatically merged.
- Keep the changelog, roadmap, and implemented-versus-planned features in sync.
- Apply source and documentation changes as UTF-8; preserve PT-PT diacritics.
- Treat all tests as executable Python and run them only in a trusted development environment.

For execution-policy changes, update the source version, EN/PT-PT guides,
implemented/planned status and upgrade notes together. With schema-2 check
targets, review both the whole-workspace and selected-file approval boundary;
[generated caches](TARGETS.md) can invalidate a later run. Before closing the
Issue, update its checklist and the PR body with actual PR/main CI evidence,
remaining limits and publication status.

For JSON/CI changes, check the optional [envelope contract](OUTPUT.md), default
CLI compatibility and process codes. Inspect the job summaries as well as logs
for each matrix/distribution job. Summary totals do not replace failure gates or
prove coverage. Inspect generated local [JUnit reports](REPORTING.md), their fixed
outcome mapping and runner-error entries; synthetic identifiers deliberately do
not identify failing source tests. Keep broader coverage profiles/artifact publication planned. Review the measured
[coverage gate](COVERAGE.md), its subprocess probe and exclusions before changing
the 90% threshold; never lower it just to hide a regression.
Do not upload reports or ordinary logs without a separate data review.

For interrupted runs, follow [native-lock recovery](LOCKING.md): independently
verify parent/child checks stopped, inspect the marker fingerprint and archive
with explicit acknowledgement/reason. Never remove the persistent guard or
infer liveness from a PID. Inspect receipt/archive/audit after any recovery
error; recovery is not one transaction and grants no execution approval.

The [candidate preview](PREVIEW.md) command is read-only and separate from execution
approval. Review diffs locally; they can contain source text or secrets and must
not be automatically uploaded with reports. Candidate support does not implement
AI-generated patches or reviewed application.

For [persisted proposals](PROPOSALS.md), review exact explicit plan paths, bindings, storage privacy and stale/tampered record failures. Keep candidate text/records/diffs out of public artifacts. Creation audit can fail after the record is saved; inspect local state before retrying. Application and AI generation remain planned.

For [staging copies](STAGING.md), inspect exclusions, independent file writes, fingerprint confirmation and retained failure state. Never treat the receipt as a sandbox or original-source application approval. Do not delete partial stages automatically or publish their contents. Trusted staged checks require their own fresh approval; environment files/dependencies may need separate preparation.

## Registry delivery observation — 2026-10-16

The first [PyPI alpha 0.3.0a8](https://pypi.org/project/euromind-safeops/0.3.0a8/)
is published; main source at that delivery was 0.3.0a11. See [current source status](STATUS.md). The exact Trusted Publisher is
`herculespt/euromind-safeops`, `publish.yml`, environment `pypi`. That environment
allows only branch `main`, zero tags and no administrator bypass; there are no
environment secrets/variables or required reviewers. Publication still requires
manual dispatch with an explicit existing alpha release tag and `publish=true`.
Keep these environment rules alongside main protection, inspect any trust change,
and preserve immutable package bytes. Record distribution hashes, clean registry
installation and actual publishing attestations separately from source/version
and SafeOps execution approval. See [delivery evidence](audits/2026-10-16-first-alpha.md).

For `inspect-stage` (source 0.3.0a12), review the historical linkage and filtered
copy results separately from current-original state and test evidence. Exit 1
with data means changed/incomplete; malformed or unsafe evidence returns 2.
Retain all records on failure. Verify exclusions, byte/path bounds, no file-text
disclosure and no audit/approval writes in regression and installed-wheel tests.
