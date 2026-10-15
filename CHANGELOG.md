# Changelog

The format follows Keep a Changelog conventions; versions follow Semantic Versioning where practicable.

## [Unreleased]

Documentation-only follow-up for source 0.3.0a2: verified a live Anthropic `claude-haiku-5-5` advisory request, saved plan and integrity review on 2026-10-15. Added dated EN/PT-PT evidence and synchronized current status, roadmap and provider guides. Compatible/local-model inference and broader account/model compatibility remain pending; runtime code, schemas and version are unchanged.

Clarified the standalone project scope and used generic confidentiality rules throughout public documentation. Added the corresponding PT-PT project-scope guide; source version remains 0.3.0a2.

Documentation-only follow-up for source 0.3.0a2: verified a live OpenAI `gpt-4.1-mini` advisory request, saved plan and integrity review on 2026-10-15. Updated EN/PT-PT status, roadmap and evidence without changing runtime code, schemas or version. The subsequent Anthropic validation is recorded above; compatible/local-model validation remains pending. No release was published.

## [0.3.0a2] — 2026-10-15 (source prerelease; not a published release)

### Fixed
- Reject ambiguous or non-UTF-8 provider JSON using the same strict decoder as stored state: duplicate keys, non-finite numbers, overflow and UTF-16 are not accepted.

### Added
- Offline provider transport and malformed-response regression tests, including HTTP/URL/timeout failures, exact response-size limits, native request serialization, Unicode and bounded advisory text.
- Real loopback HTTP integration tests for the compatible adapter, CLI plan persistence, rejected redirects and redacted HTTP error bodies. These use deterministic fixtures, not a live AI model.
- English/PT-PT provider testing evidence and secure live-test instructions, plus a complete PT-PT provider setup guide.

### Compatibility
- Configuration/plan schema 1 and approval schema 2 are unchanged. The package-version change invalidates earlier execution approvals: retain records and create a fresh plan and explicit approval.
- Previously accepted ambiguous/non-UTF-8 provider responses now fail with controlled errors. Valid UTF-8 JSON objects remain supported, with optional UTF-8 BOM.
- The initial transport-hardening milestone used no real API credentials or local model endpoint. Subsequent live OpenAI and Anthropic smoke tests are recorded above; compatible/local-model inference and broader account/model compatibility remain unverified. No release or package was published.

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
