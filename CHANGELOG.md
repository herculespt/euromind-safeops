# Changelog

The format follows Keep a Changelog conventions; versions follow Semantic Versioning where practicable.

## [Unreleased]

### Fixed
- Preserve UTF-8 stdout and stderr from fixed Python checks even when the inherited environment requests ASCII or the operating system uses a legacy locale.

### Repository maintenance
- Record the verified protected-main baseline and repository audit in English and Portuguese (Portugal).
- Synchronize the roadmap with native OpenAI and Anthropic adapters already implemented in source.
- Add a stable `quality-gate` CI job that requires the full nine-platform Python matrix.
- Add a package build verification step, automated dependency-update proposals, CODEOWNERS, and documented branch protection policy.
- Add maintainer and release guides and clarify current publication status.

## [0.2.0] — 2026-10-15

### Added
- First-party OpenAI Responses API and Anthropic Messages API advisory adapters.
- Provider configuration status command, setup guide and PowerShell examples.
- Offline protocol contract tests for both providers.

### Security
- Task content is checked before contacting any external provider.
- Fixed native HTTPS endpoints and per-provider environment variable credentials.
- Native provider responses remain advisory-only, with explicit user consent required.

## [0.1.0] — 2026-10-15 (initial public source commit)

### Added
- Initial installable SafeOps CLI and Python stdlib implementation.
- Risk classification, specialist routing, plan and snapshot hashing.
- Human approvals, fixed compile/unit-test checks, audit records.
- Opt-in OpenAI-compatible advisory provider and best-effort scanner.
- Demo, automated tests, security policy and contributor documentation.

**Note:** No published GitHub release or package registry entry is claimed until actually created.
