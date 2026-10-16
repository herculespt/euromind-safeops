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
AI generation or original application by itself; those use separate reviewed contracts.

For [persisted proposals](PROPOSALS.md), review exact explicit plan paths, bindings, storage privacy and stale/tampered record failures. Keep candidate text/records/diffs out of public artifacts. Creation audit can fail after the record is saved; inspect local state before retrying. Explicit original application is covered by [its separate contract](APPLICATION.md); bounded AI generation is covered by [its explicit source-consent contract](GENERATION.md).

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

For `review-stage` (source 0.3.0a13), review the matching-copy prerequisite, original/plan/candidate-base/configuration/target/version/contract checks, sanitized bounds/race failures and no-write/no-provider/no-approval behavior. Keep [English](STAGE_REVIEW.md) and [PT-PT](pt-PT/STAGE_REVIEW.md), source metadata, distribution inclusion, capability tables and GitHub tracking aligned. A `current` result never authorizes original application or substitutes for trusted checks.

For source 0.3.0a14, review [run receipts](RUN_RECEIPTS.md) and [PT-PT](pt-PT/RUN_RECEIPTS.md): metadata-only persistence, before/after checks, failure/timeout/change/incomplete precedence, guard cleanup/audit/final-write failures, bounded historical inspection and fresh runner-protocol-4 approval. Do not treat a historical passed receipt as current compatibility or permission to apply source changes. Keep distribution contents, version/capability tables and GitHub tracking synchronized.

Source 0.3.0a15 adds [explicit reviewed application and conservative rollback](APPLICATION.md). Both staged fixed checks must pass with unchanged current bindings and the same configuration as the original; exact fresh human confirmation and native guards precede private backup/journal preparation and source writes. Any retained application marker blocks new approved runs/applications. Read-only inspection and separately confirmed rollback preserve evidence and refuse observed human edits. No multi-file transaction, power-loss guarantee, Git operation, provider request or OS isolation is added. That milestone used runner 4/lock 2. Fresh version-bound execution approval is required.

Source 0.3.0a16 adds [owned fixed-check supervision](SUPERVISION.md): a gated launcher, POSIX group/PID anchor or Windows kill-on-close job, native completion/termination checks and continuously drained bounded stream tails. Timeout includes ordinary owned descendants and pipe retention; uncertain cleanup retains run.lock and incomplete intent without a final receipt. Runner 5/lock 3 require fresh version-bound approval. This covers cooperating same-group POSIX descendants/job members, not deliberate group/session escapes, hostile-code isolation or automatic stale recovery. The guide defines normal, timeout, cancellation and abrupt-parent-death limits.

Source 0.3.0a17 waits for final zero Windows job accounting within the same three-second cleanup budget used for launcher exit, EOF and failure cleanup. A transitional positive count cannot turn a completed failed check into an immediate operational error; persistent/unavailable confirmation remains fail-closed with retained state. Fixed-phase diagnostics exclude native exception text. Runner 5/lock 3 and schemas remain; the updated version/cleanup-policy binding requires fresh reviewed plans/proposals/approvals.

Maintainer coverage/release tooling uses dedicated reviewed Linux/CPython 3.12 wheel/hash closures. See [tooling policy](TOOLING.md) for exact profiles, refusal/update procedure and deliberate unlocked compatibility jobs. This does not lock runner/interpreter bootstrap or certify dependency safety.

[Reviewed AI generation](GENERATION.md) is a separate source-sharing operation: offline full-request review, exact fingerprint plus source-upload consent, then an unapproved schema-2 proposal. Manual schema 1 remains supported; existing explicit review/staging/check/application gates still apply. Local request reviews contain source text and must not be published blindly. Ordinary `plan` calls remain task-only.
