# EuroMind SafeOps

**A safety-focused, provider-agnostic engineering orchestration CLI.**

[![CI](https://github.com/herculespt/euromind-safeops/actions/workflows/ci.yml/badge.svg)](https://github.com/herculespt/euromind-safeops/actions/workflows/ci.yml)
![Status](https://img.shields.io/badge/status-alpha-orange)
![License](https://img.shields.io/badge/license-Apache--2.0-blue)

> **Status: v0.1.0 alpha.** This is a genuinely executable initial release, **not** a complete multi-agent IDE, sandbox, autonomous coding system, or security guarantee. See [Implemented vs. planned](#implemented-vs-planned).
>
> The GitHub links in these files are the **intended** home of the project; verify the repository exists before announcing a public release.

EuroMind SafeOps helps software maintainers plan engineering tasks, classify risk, obtain an explicit human approval, and run a small set of deterministic checks while maintaining a locally stored integrity and audit trail. An optional OpenAI-compatible provider can provide **advice only**; its text cannot be executed as code or shell commands by SafeOps.

The project is written from scratch as a general-purpose, independent tool. It contains **no SEND source code, private infrastructure configuration, credentials, or proprietary components**.

## Features

- Python 3.11+ and no third-party runtime dependencies.
- Risk classification: low, medium, high, critical; critical execution blocked.
- Specialist routing suggestion: general engineering, backend, DevOps, mobile, security, documentation.
- Advisory provider adapters: offline deterministic suggestions and opt-in OpenAI-compatible chat-completions.
- SHA-256 plan fingerprints, workspace snapshots and approval linkage.
- Human confirmation before running any check; every check is a fixed Python command (no shell interpolation).
- Offline audit events (`.safeops/audit.jsonl`) and basic credential-pattern scanner.
- Portable CLI and `unittest`-based CI for Linux/macOS/Windows.

## Quick start

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

### Optional remote advisory provider

```bash
# Use an explicitly trusted OpenAI-compatible endpoint:
export SAFEOPS_API_KEY="YOUR_KEY"
safeops --root examples/demo_project plan "Suggest improvements for this demo" \
  --provider openai-compatible \
  --endpoint https://YOUR_TRUSTED_PROVIDER/v1/chat/completions \
  --model YOUR_MODEL_NAME --allow-remote
```

PowerShell:

```powershell
$env:SAFEOPS_API_KEY = "YOUR_KEY"
safeops --root examples/demo_project plan "Review the demo design" `
  --provider openai-compatible `
  --endpoint "https://YOUR_TRUSTED_PROVIDER/v1/chat/completions" `
  --model "YOUR_MODEL_NAME" --allow-remote
```

Only task text and a minimal system instruction are sent to the configured endpoint; project files are **not** automatically uploaded. HTTPS is mandatory except for literal local loopback HTTP. External calls require `--allow-remote`. Do not include confidential text in the task. Advice is stored in a local plan and **never authorized as executable code**.

## Implemented vs. planned

| Capability | v0.1.0 |
|---|---|
| CLI + offline task planning | Implemented |
| Deterministic rule-based risk routing | Implemented; conservative heuristic, not a security classifier |
| SHA-256 plan integrity and workspace snapshots | Implemented with documented scope and limits |
| Approvals and local audit log | Implemented; local integrity checks, not tamper-proof security logs |
| Compile + Python `unittest` execution | Implemented; runs trusted repository code, not isolated |
| Best-effort credential pattern scan | Implemented; incomplete by design |
| OpenAI-compatible advisory provider | Implemented, strictly opt-in |
| Claude SDK / direct provider integration | Planned |
| Container or OS sandboxing / isolation | **Not implemented** |
| Automatic code patches, Git writes, PR generation | **Not implemented** |
| Multi-agent autonomous orchestration | **Not implemented** |
| Policy signing / remote attestation | **Not implemented** |

## Safety model

1. A plan records its source-tree hash (excluding `.safeops`, `.git`, virtual environments, and other generated dirs) and a SHA-256 fingerprint.
2. Human approval requires explicitly repeating the plan ID and providing a reason. An approval is tied to the plan, repository snapshot and check configuration.
3. Execution fails if the plan, code tree or check configuration changes after approval.
4. **Critical tasks are blocked** in this alpha version, including production deployments, deletion and credentials management.
5. `run` executes only predefined compile and unit-test commands, never task text or model output.

This is a **safety workflow, not an isolation boundary**. Workspace hashes can be recomputed by a malicious local actor; symlinks and ignored trees may need independent review. `unittest` is executable code. See [Trust model](docs/TRUST_MODEL.md), [Security policy](SECURITY.md), and [Architecture](docs/ARCHITECTURE.md).

## Project & community

- [Getting started](docs/QUICKSTART.md) · [Architecture](docs/ARCHITECTURE.md) · [Trust model](docs/TRUST_MODEL.md)
- [Português (Portugal)](docs/pt-PT/README.md) · [Project scope](docs/PROJECT_SCOPE.md)
- [Contributing](CONTRIBUTING.md) · [Code of conduct](CODE_OF_CONDUCT.md) · [Governance](GOVERNANCE.md)
- [Security reporting](SECURITY.md) · [Roadmap](ROADMAP.md) · [Changelog](CHANGELOG.md)

No claims of user adoption, downloads or external contributors are made. Community contributions are welcome once the public repository is created.

## License

Copyright 2026 Sérgio Ribeiro. Licensed under [Apache License 2.0](LICENSE).
