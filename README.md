# EuroMind SafeOps

<!-- safeops-version: 0.3.0a13 -->

**A safety-focused, provider-agnostic engineering orchestration CLI.**

[![CI](https://github.com/herculespt/euromind-safeops/actions/workflows/ci.yml/badge.svg)](https://github.com/herculespt/euromind-safeops/actions/workflows/ci.yml)
![Status](https://img.shields.io/badge/status-alpha-orange)
![License](https://img.shields.io/badge/license-Apache--2.0-blue)

> **Source version: 0.3.0a13 (alpha prerelease).** See [current implementation and publication status](docs/STATUS.md) and [Implemented vs. planned](#implemented-vs-planned). The first [GitHub alpha v0.3.0a8](https://github.com/herculespt/euromind-safeops/releases/tag/v0.3.0a8) and [PyPI 0.3.0a8](https://pypi.org/project/euromind-safeops/0.3.0a8/) were published on 2026-10-16. Original wheel/sdist hashes, registry installation and PyPI-verified publishing attestations were checked; see [delivery evidence](docs/audits/2026-10-16-first-alpha.md). Source 0.3.0a13 adds current original-context review and has additional features and is not a published package.
>

EuroMind SafeOps helps software maintainers plan engineering tasks, classify risk, obtain an explicit human approval, and run a small set of deterministic checks while maintaining a locally stored integrity and audit trail. Optional OpenAI, Anthropic Claude, and OpenAI-compatible providers can provide **advice only**; their text cannot be executed as code or shell commands by SafeOps.

EuroMind SafeOps is developed independently as a general-purpose open-source tool. Contributions must be original or appropriately licensed and free of credentials, private infrastructure configuration and proprietary components.

## Features

- Python 3.11+ and no third-party runtime dependencies.
- Risk classification: low, medium, high, critical; critical execution blocked.
- Specialist routing suggestion: general engineering, backend, DevOps, mobile, security, documentation.
- Advisory provider adapters: offline, OpenAI Responses API, Anthropic Messages API, and OpenAI-compatible chat-completions (remote access is opt-in).
- SHA-256 plan fingerprints, workspace snapshots and approval linkage.
- Strict UTF-8 JSON policy validation and approvals bound to the installed version and fixed execution contract.
- Unit-test checks require discovery and execution of at least one non-skipped case; nested regular test packages are supported.
- Portable advisory path preflight before provider access, persistence, approval and run; see [scope policy](docs/SCOPE.md).
- Human confirmation before running any check; every check is a fixed Python command (no shell interpolation).
- Offline audit events (`.safeops/audit.jsonl`) and basic credential-pattern scanner.
- Portable CLI and `unittest`-based CI for Linux/macOS/Windows.

## Quick start

Install the published alpha in a virtual environment with
`python -m pip install euromind-safeops==0.3.0a8`.
That release predates candidate previews, persisted proposals, staging copies and receipt inspection.
Use the source checkout below for the current 0.3.0a13 capabilities.

In a shell at the root of this repository:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
safeops --version
```

SafeOps operates **on the repository you point it at**, not automatically on this package. Try the bundled isolated demo:

```bash
safeops --root examples/demo_project init
safeops --root examples/demo_project doctor
safeops --root examples/demo_project scan
safeops --root examples/demo_project plan "Improve documentation for calculator"
```

The last command prints a 12-character **plan ID**. Replace `YOUR_PLAN_ID` below with the actual ID from the output:

```bash
safeops --root examples/demo_project review YOUR_PLAN_ID
safeops --root examples/demo_project approve YOUR_PLAN_ID --confirm YOUR_PLAN_ID --reason "Reviewed scope and trusted demo tests"
safeops --root examples/demo_project run YOUR_PLAN_ID
```

**Important:** `approve` does not modify code. `run` executes only the predefined `compile` and `unit-tests` checks on trusted local source. Existing repository tests can execute arbitrary Python; this tool is **not a sandbox**. Do not run against untrusted repositories or code.

**Upgrading from 0.2.0:** keep the workspace and its history. Valid schema-1 configuration remains supported, but old approvals are rejected. Review the current source, create a new plan and approve it explicitly. See [execution policy and compatibility](docs/EXECUTION.md).

The existing version binding also requires new execution approval when upgrading
to 0.3.0a13. Schema-1 defaults remain supported; optional schema 2 selects
[fixed-check directories](docs/TARGETS.md). Plan schema 1 and approval schema 2
remain supported, with an additional target digest required for schema-2 config.

For automation, put `--json` before the command, for example
`safeops --json --root examples/demo_project doctor`. Default output remains
available; see the [JSON and CI summary contract](docs/OUTPUT.md).

### Optional AI advice — OpenAI, Anthropic and local models

All remote integrations require explicit consent (`--allow-remote`) and the model ID you wish to use. They send only the task description, not repository files. Official provider API access may be billed separately from chat subscriptions.

```bash
safeops providers

# OpenAI Responses API (requires OPENAI_API_KEY):
safeops --root examples/demo_project plan "Review the design" \
  --provider openai --model YOUR_OPENAI_MODEL_ID --allow-remote

# Anthropic Claude Messages API (requires ANTHROPIC_API_KEY):
safeops --root examples/demo_project plan "Review the design" \
  --provider anthropic --model YOUR_CLAUDE_MODEL_ID --allow-remote

# An optional local OpenAI-compatible server:
safeops --root examples/demo_project plan "Review the design" \
  --provider openai-compatible \
  --endpoint http://127.0.0.1:8080/v1/chat/completions \
  --model YOUR_LOCAL_MODEL --allow-remote
```

**See [Provider setup and PowerShell examples](docs/PROVIDERS.md).** Never commit keys or include confidential text in prompts. AI advice cannot authorize code execution or repository modifications.

Read-only candidate inspection: `safeops --root PROJECT --json preview CANDIDATE.json`.
See the [candidate format and limits](docs/PREVIEW.md); no initialization, model request or execution approval is involved.

Local proposal lifecycle: `propose PLAN_ID CANDIDATE.json` and `review-proposal PROPOSAL_ID`.
Requires an initialized workspace and exact explicit plan file paths; see [proposal bindings and limits](docs/PROPOSALS.md).

Prepare a reviewed proposal for local inspection/testing with `stage-proposal PROPOSAL_ID --confirm PROPOSAL_FINGERPRINT`. See [staging copies and fresh execution approval](docs/STAGING.md).

Recheck a retained copy with `safeops --root ORIGINAL_PROJECT --json inspect-stage STAGE_ID`.
It reports matching/changed/incomplete state without file text, writes or approval;
see [historical inspection and limits](docs/STAGING.md).

Review compatibility with the current original using
`safeops --root ORIGINAL_PROJECT --json review-stage STAGE_ID`. It reports
current/stale/incompatible context without applying changes or renewing approval;
see [the review contract](docs/STAGE_REVIEW.md).

## Implemented vs. planned

| Capability | 0.3.0a13 |
|---|---|
| Current original-context review | Implemented; `review-stage` requires a matching copy and revalidates original/proposal/plan/config/target/version bindings without writes or approval; [contract](docs/STAGE_REVIEW.md) |
| Read-only stage receipt inspection | Implemented; strict historical linkage, bounded double scan and missing/extra/changed paths; source context is not revalidated and no approval is granted |
| CLI + offline task planning | Implemented |
| Separate local staging copies | Implemented; exact proposal-fingerprint confirmation, replacements only in a new copy and manifest/receipt; [limits](docs/STAGING.md) |
| Persisted plan-bound local proposals | Implemented; exact explicit plan paths, stale-context rejection and read-only review; [contract](docs/PROPOSALS.md) |
| Local candidate diff previews | Implemented; exact per-file hashes, existing UTF-8 text replacements, no writes or approval; [contract](docs/PREVIEW.md) |
| Optional structured CLI output | Implemented; global `--json`, schema-1 envelope, handled errors/warnings and stable exit codes; [contract](docs/OUTPUT.md) |
| Aggregate CI summaries and local JUnit XML | Implemented and validated across nine matrix and two installed-wheel jobs; synthetic identifiers, fixed outcomes; [contract](docs/REPORTING.md). [Coverage gate](docs/COVERAGE.md) implemented on Linux/Python 3.12; report uploads remain planned |
| Local native run guard and owned marker | Implemented on supported POSIX/Windows filesystems; retained markers block after crashes; [limits](docs/LOCKING.md) |
| Lock diagnostics and explicit archival recovery | Implemented; doctor fingerprint, human process verification, receipt/audit and no automatic stale removal |
| Deterministic rule-based risk routing | Implemented; conservative heuristic, not a security classifier |
| SHA-256 plan integrity and workspace snapshots | Implemented with documented scope and limits |
| Approvals and local audit log | Implemented; local integrity checks, not tamper-proof security logs |
| Strict configuration schema and UTF-8 JSON parsing | Implemented; duplicate keys, non-finite numbers and unsupported policy fields rejected |
| Versioned execution contract | Implemented; old, changed-command or changed-version approvals rejected |
| Compile + Python `unittest` execution | Implemented; unit-test checks reject empty/all-skipped suites; trusted code, not isolated |
| Best-effort credential pattern scan | Implemented; incomplete by design |
| OpenAI, Anthropic Claude and OpenAI-compatible advisory providers | Implemented, strictly opt-in |
| Native Anthropic Messages API and OpenAI Responses API | Implemented; separate OpenAI `gpt-4.1-mini` and Anthropic `claude-haiku-5-5` live smokes passed on source 0.3.0a2 on 2026-10-15 |
| Strict provider responses and transport regression tests | Implemented; loopback fixtures plus separate verified OpenAI and Anthropic live smoke tests |
| Advisory scope-path preflight | Implemented; validates declared paths before side effects and rechecks links; does not restrict fixed check targets |
| Explicit fixed-check directory targets | Implemented in optional config schema 2; recursive link checks and selected-file approval digest; [limits](docs/TARGETS.md) |
| OS-enforced filesystem allowlist / check isolation | **Not implemented**; trusted Python retains filesystem access |
| Container or OS sandboxing / isolation | **Not implemented** |
| Original-workspace patch application, Git writes, PR generation | **Not implemented**; reviewed replacements can be materialized only in a separate local copy |
| Multi-agent autonomous orchestration | **Not implemented** |
| Policy signing / remote attestation | **Not implemented** |

## Safety model

1. A plan records its source-tree hash (excluding `.safeops`, `.git`, virtual environments, and other generated dirs) and a SHA-256 fingerprint.
2. Human approval requires explicitly repeating the plan ID and providing a reason. A schema-2 approval binds the plan, repository snapshot, validated configuration, package version and fixed execution contract.
3. Execution fails if those approved inputs change; upgrading requires a new plan and approval. Tests are imported only inside an approved child process.
4. **Critical tasks are blocked** in this alpha version, including production deployments, deletion and credentials management.
5. `run` executes only predefined compile and unit-test commands, never task text or model output.

This is a **safety workflow, not an isolation boundary**. Workspace hashes can be recomputed by a malicious local actor; symlinks and ignored trees may need independent review. `unittest` is executable code. See [Trust model](docs/TRUST_MODEL.md), [Security policy](SECURITY.md), and [Architecture](docs/ARCHITECTURE.md).

## Project & community

- [Getting started](docs/QUICKSTART.md) · [Provider setup](docs/PROVIDERS.md) · [Architecture](docs/ARCHITECTURE.md) · [Trust model](docs/TRUST_MODEL.md)
- [Português (Portugal)](docs/pt-PT/README.md) · [Project scope](docs/PROJECT_SCOPE.md)
- [Contributing](CONTRIBUTING.md) · [Code of conduct](CODE_OF_CONDUCT.md) · [Governance](GOVERNANCE.md)
- [Maintainer guide & branch protection](docs/MAINTAINER_GUIDE.md) · [Release procedure](docs/RELEASING.md)
- [CI and package build contract](docs/CI.md) · [JSON output and CI summaries](docs/OUTPUT.md)
- [Measured coverage and CI threshold](docs/COVERAGE.md)
- [Local JUnit reports and outcome mapping](docs/REPORTING.md)
- [Local run locking and explicit recovery](docs/LOCKING.md)
- [Alpha package publication procedure](docs/RELEASING.md) · [Registry package description](docs/PACKAGE.md)
- [Provider testing and live validation status](docs/PROVIDER_TESTING.md)
- [Current implementation status](docs/STATUS.md) · [Execution policy and upgrade compatibility](docs/EXECUTION.md)
- [Repository audit — 2026-10-15](docs/audits/2026-10-15.md) · [Auditoria em PT-PT](docs/pt-PT/audits/2026-10-15.md)
- [Security reporting](SECURITY.md) · [Roadmap](ROADMAP.md) · [Changelog](CHANGELOG.md)

No claims of user adoption, downloads or external contributors are made. Community contributions are welcome. GitHub Releases and PyPI publication are separate, manual steps and should not be assumed from a commit or CI badge.

## License

Copyright 2026 Sérgio Ribeiro. Licensed under [Apache License 2.0](LICENSE).
