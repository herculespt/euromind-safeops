# Changelog

The format follows Keep a Changelog conventions; versions follow Semantic Versioning where practicable.

## [Unreleased]

No additional changes recorded beyond the source milestone below.

## [0.3.0a1] — 2026-10-15 (source prerelease; not a published release)

### Added
- Strict configuration schema with unique supported check names and UTF-8 JSON parsing that rejects duplicate keys and non-finite numbers.
- Internal unittest runner: discover and execute a nonempty suite inside the approved child process; reject all-skipped or zero-execution results and support nested regular test packages.
- Approval schema 2, bound to package version, fixed commands, runner protocol and UTF-8 stream policy.
- EN/PT-PT execution compatibility and implementation-status guides, ADR 0002, and automated checks for source, metadata, CLI and current-document version alignment.

### Compatibility
- Valid config schema 1 and stored plans remain supported. Legacy approvals are retained but require a new plan and explicit approval; no automatic migration or history deletion.
- Unknown config fields, duplicate checks, boolean/float schema values and malformed check types now fail with controlled errors.
- A configured unit-test check now fails when no non-skipped case executes. Compile-only configurations remain supported and do not claim test coverage.

### Fixed
- Prevent false-positive success for empty/all-skipped unittest suites and uncontrolled TypeError from malformed policy values.
- Correct the unsupported setuptools build floor; require the tested 83.0.0 baseline and remove the redundant standalone wheel build dependency.
- Preserve UTF-8 stdout and stderr from fixed Python checks even when the inherited environment requests ASCII or the operating system uses a legacy locale.

### Repository maintenance
- Pin reviewed checkout/setup-python v7 Actions to official commit SHAs, disable checkout credential persistence and require minimum/latest-backend artifact checks in `quality-gate`.
- Include public documentation, examples, tests and CI contracts in source distributions.
- Test the complete suite against the installed wheel outside the checkout, including the packaged child runner and current EN/PT-PT status guides.
- Document authorized enablement of private vulnerability reporting, dependency graph, Dependabot alerts and security updates; add the PT-PT security policy.
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
