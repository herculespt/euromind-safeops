# Explicit Git staging worktrees — 0.3.0a20

<!-- safeops-version: 0.3.0a20 -->

[Português (Portugal)](pt-PT/GIT_STAGING.md)

Implemented as an optional staging mode; ordinary `stage-proposal` still creates
an independent filesystem copy with schema-1 evidence and no Git invocation.
No account, provider credit or specialist-manifest feature is required.

Run `review-git-stage PROPOSAL_ID` locally, inspect its complete output, then
`stage-git-proposal PROPOSAL_ID --confirm FINGERPRINT`. The ordinary proposal
fingerprint does not authorize Git mutation. Review invokes read-only local Git
builtins and uses temporary disk-backed output capture outside the project; it
does not create a stage, modify Git, grant approval or access a provider/network.
The exact confirmation binds proposal/source/version/policy, installed Git path,
committed base, original HEAD/index/configuration/refs and tracked-entry hashes.
Review contains private local paths/hashes; keep it local.

Initial support requires the main worktree of a SHA-1 repository with a regular
`.git` directory, an existing commit, matching index and literal regular-file
contents. Each included file must be tracked at that commit, all tracked files
must be included, and literal bytes must match Git blob identities. Dirty or
untracked included files, staged edits, symlinks/reparse points/hardlinks,
submodules, tracked internal/generated/environment paths, extended include or
worktree configuration, unborn/bare/linked-root/SHA-256 repositories and ambiguous
portable paths are refused. Conventional untracked environment files are omitted,
never copied, and remain part of the original source snapshot. LF and byte-exact
requirements can reject checkouts transformed by autocrlf/filters even if Git
status calls them clean. No normalizing or resetting original files is attempted.

Creation acquires the existing original native run guard/owned marker, refusing
busy checks, stale markers or pending original application. It exclusively owns
`.safeops/stages/<id>/`, writes **schema-2 intent before Git mutation**, registers
a detached locked worktree using fixed `worktree add --no-checkout`, initializes
only its new index with `read-tree`, and copies the bounded reviewed source with
candidate replacements through the existing regular-file writer. No shell,
checkout filters, hooks, submodule initialization, branch creation, commit, fetch,
push, force option or automatic remove/prune/unlock is exposed. Git inherits only
a small OS environment allowlist; global/system configuration, interactive
credentials, replacement objects, hooks, fsmonitor and automatic maintenance are
disabled for the fixed operations. The installed Git executable and trusted local
repository/object database remain external trust boundaries.

Existing limits remain 5,000 files, 12,000,000 bytes per file, 64,000,000 copied
bytes and 1,000,000 receipt bytes. Git context is capped at 3,000 canonical JSON bytes before allocating a stage, keeping intent inspection within 4,096 bytes. Parsed Git output is capped at 2,000,000 bytes,
with 15 seconds per Git command and sanitized errors. Disk-backed capture avoids
unbounded parsed memory; it is not a hard temporary-disk quota, whole-operation
deadline or hostile-process containment guarantee. No arbitrary Git argument,
executable or environment override is accepted. Stored executable paths must
match the currently resolved installed Git before any inspection invocation.

A receipt is written only after copied content, proposal, original Git state and
new linkage/base/index are revalidated. Schema-2 intent/receipt extend the existing
stage fields with bounded Git context; proposal schemas remain manual 1 / AI 2.
`inspect-stage` supports both copy schema 1 and Git schema 2. For Git stages it
checks the pointer, common directory, backlink, retained lock, detached base and
index-entry digest before and after content scans. Historical inspection does not
require the original source/index to remain current, but needs the linked Git
metadata, original repository location and installed Git to remain available.
Changed/moved/repaired/committed/unlocked Git state can require explicit human
inspection outside this initial contract. No automatic repair or cleanup occurs.

Failures retain partial directories, intent and any registered locked worktree;
an absent receipt is incomplete, never successful staging. An audit/storage
failure may leave a valid unapproved stage. Inspect retained evidence and actual
Git registration before any independently authorized manual recovery. Residual
filesystem races and concurrent external Git mutations remain possible; native
guards serialize cooperative SafeOps operations, not every Git client.

Continue with existing explicit staged `init`, fresh plan/approval, compile and
unit tests, current original-context/application review, exact apply confirmation
and conservative rollback. No approval, checks or application run automatically.
The original index, HEAD, refs and source are preserved by staging; later explicit
application can replace approved original text while still leaving Git integration
to the maintainer. A regular `.git` metadata file is excluded from source digests,
as `.git` directories already were; linkage is validated separately for Git stages.
Upgrading requires fresh version-bound plans/proposals/approvals. All old records
remain retained and copy-stage inspection remains provider/Git-free.

Linked worktrees share repository objects, configuration and many refs. A distinct
working directory is **not OS isolation**. Authenticated SafeOps provenance is
still planned in [#61](https://github.com/herculespt/euromind-safeops/issues/61):
choose signer identity, canonical signed statement, trust/rotation/revocation and
verification before adding signing authority. Existing GitHub/PyPI publishing
attestations authenticate publication, not SafeOps approvals or receipts. No new
signing identity, credential, release or PyPI publication is created here.

References: [Git worktrees](https://git-scm.com/docs/git-worktree),
[read-tree](https://git-scm.com/docs/git-read-tree),
[checkout hook behavior](https://git-scm.com/docs/githooks).
