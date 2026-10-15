# Implementation and publication status

<!-- safeops-version: 0.3.0a3 -->

[Português (Portugal)](pt-PT/STATUS.md)

**Current source version: 0.3.0a3 — alpha prerelease.** Python 3.11–3.13 is
covered by CI on Linux, Windows and macOS. No third-party runtime dependencies.
This source milestone is not a published release: GitHub Releases/tags require
separate approval, and package-registry publication is not configured or verified.

## Implemented

| Capability | Practical boundary |
|---|---|
| CLI, offline plans, risk and specialist suggestions | Heuristic classification, advisory task scope |
| Source/plan integrity and local audit | SHA-256 linkage; mutable local records, not signatures |
| Strict configuration and stored JSON | Exact schema-1 config, unique fixed checks, UTF-8/finite/unique-key JSON |
| Approval schema 2 and execution-contract binding | Package/command changes require new plan and explicit approval |
| Fixed compile and unittest checks | Empty/all-skipped test execution fails; no isolation or coverage guarantee |
| UTF-8 check streams, lock and timeout | Existing crash/race and trusted-code limits remain |
| OpenAI, Anthropic and compatible advisory adapters | Explicit consent, task-only request, strict UTF-8 response objects; offline contracts/loopback fixtures; separate live OpenAI `gpt-4.1-mini` and Anthropic `claude-haiku-5-5` requests and saved-plan reviews verified on 2026-10-15 |
| Portable advisory scope preflight | Validated before remote advice/persistence and rechecked at approval/run; paths do not restrict fixed checks |
| Protected main and security-reporting workflow | Verified settings are dated operational observations |
| CI and distribution validation | Nine test environments, minimum/latest backend jobs and required aggregate gate |
| English/PT-PT current guides and version checks | Metadata, CLI help and versioned-document markers are tested |

## Planned or unsupported

| Capability | State |
|---|---|
| Explicit workspace filesystem allowlists | Planned |
| Autonomous multi-agent editing or patch application | Not implemented |
| SafeOps-generated Git commits or pull requests | Not implemented; repository maintenance is performed externally |
| General-purpose/plugin command execution | Not implemented |
| Container/OS sandboxing and hostile-code isolation | Not implemented |
| Signed approvals, tamper-proof audit, remote attestation | Not implemented |
| Production deployment or automatic release publication | Not implemented |
| Live compatible/local-model inference and broader account/model compatibility | Pending; separate successful OpenAI and Anthropic smokes do not establish these |
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
The live requests above were tested on source 0.3.0a2. Current source 0.3.0a3
adds [advisory scope preflight](SCOPE.md), preserves the JSON schemas and
invalidates earlier execution approvals through the version-bound contract.
A complete filesystem allowlist remains planned. No release is published.
