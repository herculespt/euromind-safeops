# Security Policy

<!-- safeops-version: 0.3.0a9 -->

[Português (Portugal)](docs/pt-PT/SECURITY.md)

## Scope and maturity

EuroMind SafeOps 0.3.0a9 is an **alpha developer tool**. It is not a sandbox, cannot ensure the safety of source code being tested, and must not be used to authorize production operations. The risk classifier and pattern scanner are best-effort heuristics.

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
