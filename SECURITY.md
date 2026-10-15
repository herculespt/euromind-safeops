# Security Policy

<!-- safeops-version: 0.3.0a1 -->

[Português (Portugal)](docs/pt-PT/SECURITY.md)

## Scope and maturity

EuroMind SafeOps 0.3.0a1 is an **alpha developer tool**. It is not a sandbox, cannot ensure the safety of source code being tested, and must not be used to authorize production operations. The risk classifier and pattern scanner are best-effort heuristics.

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
- Source-tree snapshots exclude generated directories and ignore symlinks. Review these limitations before relying on approvals.
- Empty and all-skipped unit-test suites fail, but trusted test code can still terminate the interpreter or falsify its behavior; nonempty discovery does not prove useful assertions or coverage.
- Configuration schema 1 remains supported; approval schema 2 binds the version and fixed execution contract. Existing approvals are not silently migrated. See [execution policy](docs/EXECUTION.md).
