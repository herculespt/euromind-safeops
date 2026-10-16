# Project scope and provenance

<!-- safeops-version: 0.3.0a19 -->

[Português (Portugal)](pt-PT/PROJECT_SCOPE.md)

EuroMind SafeOps 0.3.0a19 is an original, independent, generic command-line policy and verification tool for development workflows. The [status](STATUS.md) distinguishes implemented capabilities from future work and public releases.

## Public components

- Generic planning and auditing algorithms.
- Conservative policy checks, specialist suggestions and fixed test runners.
- OpenAI-compatible advisory provider with opt-in transport.
- Native OpenAI and Anthropic advisory providers, strict configuration and version-bound approvals.
- Documentation, public examples and tests.

## Strict exclusions

- Cryptographic keys, private infrastructure configuration and deployment secrets.
- Any proprietary source code, customer data or vendor credentials.
- Claims of certification, security guarantees, package downloads, installed user base, community adoption or OSS eligibility that cannot be verified.

## IP review before publication

The project founder should confirm ownership of every contribution and verify no employer or third-party contractual rights are affected. Review all code, examples, generated artifacts and licensing before publication. The project repository can be public while proprietary applications remain private.

[Persisted local proposals](PROPOSALS.md) bind manually authored candidate replacements to an unchanged explicit plan and support read-only review. Explicit application has [a separate contract](APPLICATION.md); [Bounded AI-generated candidates](GENERATION.md) are now implemented with exact reviewed source-upload consent and unapproved schema-2 records; autonomous editing remains planned.

[Separate local staging copies](STAGING.md) support inspection/testing of reviewed replacements after exact fingerprint confirmation. They do not apply changes to the original source, initialize/approve checks automatically or implement Git worktrees/OS isolation.

Source 0.3.0a15 adds [explicit reviewed application and conservative rollback](APPLICATION.md). Both staged fixed checks must pass with unchanged current bindings and the same configuration as the original; exact fresh human confirmation and native guards precede private backup/journal preparation and source writes. Any retained application marker blocks new approved runs/applications. Read-only inspection and separately confirmed rollback preserve evidence and refuse observed human edits. No multi-file transaction, power-loss guarantee, Git operation, provider request or OS isolation is added. That milestone used runner 4/lock 2. Fresh version-bound execution approval is required.

Source 0.3.0a16 adds [owned fixed-check supervision](SUPERVISION.md): a gated launcher, POSIX group/PID anchor or Windows kill-on-close job, native completion/termination checks and continuously drained bounded stream tails. Timeout includes ordinary owned descendants and pipe retention; uncertain cleanup retains run.lock and incomplete intent without a final receipt. Runner 5/lock 3 require fresh version-bound approval. This covers cooperating same-group POSIX descendants/job members, not deliberate group/session escapes, hostile-code isolation or automatic stale recovery. The guide defines normal, timeout, cancellation and abrupt-parent-death limits.
