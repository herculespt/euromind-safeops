# Security Policy

<!-- safeops-version: 0.3.0a17 -->

[Português (Portugal)](docs/pt-PT/SECURITY.md)

## Scope and maturity

EuroMind SafeOps 0.3.0a17 is an **alpha developer tool**. It is not a sandbox, cannot ensure the safety of source code being tested, and must not be used to authorize production operations. The risk classifier and pattern scanner are best-effort heuristics.

## Reporting vulnerabilities

**Do not open public issues containing exploits, credential material or details of an unpatched vulnerability.** Use **Security → Advisories → Report a vulnerability** for private reports. Private vulnerability reporting was enabled and verified on 2026-10-15 after maintainer authorization. If that channel later becomes unavailable, open a public issue asking the maintainer to enable a private disclosure channel, without revealing vulnerability details.

There is no guaranteed response-time SLA. No bug bounty is offered.

## Important warnings

- Run checks only on source code you already trust: Python test discovery executes code.
- The approval and audit files are local; they are not cryptographically signed or tamper-proof.
- No general-purpose secure sandboxing, container isolation or network segmentation is provided.
- A remote provider receives the **task description** if expressly enabled; never paste secrets.
- Keep `.safeops/`, environment variables, provider tokens and local `.env` files outside version control.
- A zero-findings scan is **not proof** that a codebase is free of secrets.
- Plans store task text and advisory output locally; avoid sensitive information.
- Source-tree snapshots exclude generated directories and ignore symlinks. Declared advisory paths reject link/reparse components at preflight/approval/run; this does not police all workspace descendants or isolate trusted tests. See [scope policy](docs/SCOPE.md).
- Empty and all-skipped unit-test suites fail, but trusted test code can still terminate the interpreter or falsify its behavior; nonempty discovery does not prove useful assertions or coverage.
- Provider JSON uses strict UTF-8 object decoding and bounded reads; HTTP/URL/timeout errors are exposed as controlled type-only CLI messages. Response bodies and exception detail are not printed by that error path. Test fixtures do not establish live-model security or vendor/account compatibility; see [provider testing](docs/PROVIDER_TESTING.md).
- Configuration schema 1 remains supported; approval schema 2 binds the version and fixed execution contract. Existing approvals are not silently migrated. See [execution policy](docs/EXECUTION.md).

[Preview output](docs/PREVIEW.md) contains local file text; do not publish it blindly. Candidate hashes are integrity records, not signatures or approval.

[Local proposal records](docs/PROPOSALS.md) contain full proposed text. Keep them private and out of Git. Recomputed local hashes cannot authenticate a malicious writer; successful review does not grant application or execution authority.

[Staging copies](docs/STAGING.md) omit conventional environment files and Git/SafeOps state, but other copied files can contain secrets. They do not sanitize inherited environment/network access or sandbox trusted tests. Partial copies remain on failure; do not upload or delete them automatically.

Read-only `inspect-stage` emits historical identifiers, relative paths, counts
and digests without file text. Keep those observations private when sensitive.
Matching unkeyed evidence is not authentication, current-original revalidation,
passing tests, an execution approval or authorization to apply changes.

`review-stage` separately revalidates current original-context bindings with bounded read-only observations and a matching copy prerequisite. Environment/selected-target bytes may be hashed locally but are never returned. Its `current` observation grants no approval, authentication or application authority. See [scope and race limits](docs/STAGE_REVIEW.md).

Run intents/final receipts persist only bounded metadata, hashes and fixed outcomes, excluding captured output/task/advice/approval reasons. `inspect-run` is historical-only and never authenticates provenance or renews approval. Post-check observations stop changed/unavailable input sequences; audit opens reject hardlinks/reparse/nonregular files without FIFO blocking. Trusted tests retain filesystem/process access and unkeyed records remain mutable. See [run receipt limits](docs/RUN_RECEIPTS.md).

Source 0.3.0a15 adds [explicit reviewed application and conservative rollback](docs/APPLICATION.md). Both staged fixed checks must pass with unchanged current bindings and the same configuration as the original; exact fresh human confirmation and native guards precede private backup/journal preparation and source writes. Any retained application marker blocks new approved runs/applications. Read-only inspection and separately confirmed rollback preserve evidence and refuse observed human edits. No multi-file transaction, power-loss guarantee, Git operation, provider request or OS isolation is added. That milestone used runner 4/lock 2. Fresh version-bound execution approval is required. Backups and proposals contain local source text: keep `.safeops` private and out of public artifacts. Local hashes and identity checks cannot prevent a malicious state owner or every check/replace race.

Source 0.3.0a16 adds [owned fixed-check supervision](docs/SUPERVISION.md): a gated launcher, POSIX group/PID anchor or Windows kill-on-close job, native completion/termination checks and continuously drained bounded stream tails. Timeout includes ordinary owned descendants and pipe retention; uncertain cleanup retains run.lock and incomplete intent without a final receipt. Runner 5/lock 3 require fresh version-bound approval. This covers cooperating same-group POSIX descendants/job members, not deliberate group/session escapes, hostile-code isolation or automatic stale recovery. The guide defines normal, timeout, cancellation and abrupt-parent-death limits.

Source 0.3.0a17 waits for final zero Windows job accounting within the same three-second cleanup budget used for launcher exit, EOF and failure cleanup. A transitional positive count cannot turn a completed failed check into an immediate operational error; persistent/unavailable confirmation remains fail-closed with retained state. Fixed-phase diagnostics exclude native exception text. Runner 5/lock 3 and schemas remain; the updated version/cleanup-policy binding requires fresh reviewed plans/proposals/approvals.
