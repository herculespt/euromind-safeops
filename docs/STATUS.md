# Implementation and publication status

<!-- safeops-version: 0.3.0a10 -->

[Português (Portugal)](pt-PT/STATUS.md)

**Current source version: 0.3.0a10 — alpha prerelease.** Python 3.11–3.13 is
covered by CI on Linux, Windows and macOS. No third-party runtime dependencies.
The first [GitHub alpha v0.3.0a8](https://github.com/herculespt/euromind-safeops/releases/tag/v0.3.0a8)
was published on 2026-10-16 at `035c36b1b646a6c75178d5db6c19d8c55d624dcf`,
with verified wheel, sdist and SHA256SUMS. All twelve main CI jobs and candidate
validation passed; the installed release wheel passed 209 tests (3 platform skips,
zero failures/errors). See [dated evidence](audits/2026-10-16-first-alpha.md).
The workflow is prepared for PyPI, but account authentication, publisher registration
and actual registry publication remain pending. The sign-in request was interrupted;
no account grant, registry installation or attestation was verified.

Source 0.3.0a10 adds persisted plan-bound proposals and read-only review; it has not been published as a new release.

## Implemented

| Capability | Practical boundary |
|---|---|
| Persisted plan-bound local proposals | Exact explicit plan paths, snapshot/config/contract binding and read-only review; no source application or approval; [contract](PROPOSALS.md) |
| Local candidate text previews | Exact per-file base hashes and read-only unified diffs; manually supplied candidates only; [contract](PREVIEW.md) |
| CLI, offline plans, risk and specialist suggestions | Heuristic classification, advisory task scope |
| Source/plan integrity and local audit | SHA-256 linkage; mutable local records, not signatures |
| Strict configuration and stored JSON | Schema-1 defaults and opt-in schema-2 targets, unique fixed checks, UTF-8/finite/unique-key JSON |
| Approval schema 2 and execution-contract binding | Package/command changes require new plan and explicit approval |
| Fixed compile and unittest checks | Empty/all-skipped test execution fails; no isolation or coverage guarantee |
| UTF-8 check streams and timeout | Direct-child timeout; process-tree supervision not implemented |
| Native local run guard and owned marker | Cooperative POSIX/Windows locking; guard persists, abandoned/legacy markers block |
| Lock diagnostics and explicit archival recovery | Doctor fingerprint/status, human process verification, receipt/audit; no automatic stale inference or approval grant |
| OpenAI, Anthropic and compatible advisory adapters | Explicit consent, task-only request, strict UTF-8 response objects; offline contracts/loopback fixtures; separate live OpenAI `gpt-4.1-mini` and Anthropic `claude-haiku-5-5` requests and saved-plan reviews verified on 2026-10-15 |
| Portable advisory scope preflight | Validated before remote advice/persistence and rechecked at approval/run; paths do not restrict fixed checks |
| Explicit fixed-check directory targets | Optional schema 2; recursive link checks and selected-file approval digest; not an OS access boundary |
| Structured CLI JSON envelopes | Optional global `--json`; schema 1, handled results/errors/warnings and 0/1/2 exit codes; [contract](OUTPUT.md) |
| Aggregate CI summaries and local JUnit XML | Generated/validated in nine matrix and two installed-wheel jobs; synthetic cases and fixed outcomes; [contract](REPORTING.md) |
| Measured coverage gate | Linux/Python 3.12, package statements/branches and supported Python children, combined minimum 90%; [limits](COVERAGE.md) |
| Protected main and security-reporting workflow | Verified settings are dated operational observations |
| CI and distribution validation | Nine test environments, minimum/latest backend jobs and required aggregate gate |
| English/PT-PT current guides and version checks | Metadata, CLI help and versioned-document markers are tested |

## Planned or unsupported

| Capability | State |
|---|---|
| OS-enforced workspace filesystem allowlists | Planned; selecting check inputs does not restrict arbitrary reads |
| Autonomous multi-agent editing or patch application | Not implemented |
| SafeOps-generated Git commits or pull requests | Not implemented; repository maintenance is performed externally |
| General-purpose/plugin command execution | Not implemented |
| Container/OS sandboxing and hostile-code isolation | Not implemented |
| Signed approvals, tamper-proof audit, remote attestation | Not implemented |
| Production deployment or automatic release publication | Not implemented |
| Live compatible/local-model inference and broader account/model compatibility | Pending; separate successful OpenAI and Anthropic smokes do not establish these |
| Distributed/network-filesystem locks, process-tree supervision and automatic recovery decisions | Planned; current locking is cooperative/local and recovery explicitly human-confirmed |
| Broader coverage profiles and report-artifact uploads | Planned; measured Linux/Python 3.12 coverage, local JUnit and summaries are implemented |
| Workflow dependency lockfiles, complete reproducible builds, independent history-wide secret audit | Pending separate work |

The [roadmap](../ROADMAP.md) records future work without assigning delivery dates
or implying that a version number includes autonomous agents. The
[dated repository audit](audits/2026-10-15.md) preserves its historical source
baseline and test counts; it is not rewritten to pretend it examined later code.

## Version and documentation change control

Behavior changes update `pyproject.toml`, `__version__`, dynamic CLI help,
changelog, roadmap, this status and affected guides in English/PT-PT. Current
versioned documents carry a `safeops-version` marker checked by the test suite;
historical versions in changelogs and dated audits are retained. A new source
version does not create a tag, GitHub Release, store upload or package publication.

See [execution compatibility](EXECUTION.md), [trust model](TRUST_MODEL.md),
[CI contract](CI.md) and [release procedure](RELEASING.md).

Provider evidence distinguishes fixtures from the separate verified live requests in
[provider testing](PROVIDER_TESTING.md), the [OpenAI record](audits/2026-10-15-openai-smoke.md)
and the [Anthropic record](audits/2026-10-15-anthropic-smoke.md).
The live requests above were tested on source 0.3.0a2. Current source 0.3.0a10
adds [plan-bound proposals](PROPOSALS.md), retaining [local candidate previews](PREVIEW.md), [measured coverage](COVERAGE.md), [local JUnit reporting](REPORTING.md),
[native locking and explicit recovery](LOCKING.md),
[structured output and summaries](OUTPUT.md), optional
[check directory targets](TARGETS.md), advisory [scope preflight](SCOPE.md) and
schema-1 defaults. The version-bound contract
invalidates earlier execution approvals; schema-2 config also binds selected files.
A complete filesystem allowlist remains planned. See the publication status above.
