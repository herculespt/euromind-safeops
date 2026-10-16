# Changelog

The format follows Keep a Changelog conventions; versions follow Semantic Versioning where practicable.

## [Unreleased]

Current source milestone: **0.3.0a8**. No tag or public release is implied.

## [0.3.0a8] — 2026-10-15 (alpha source; publication tracked in docs/STATUS.md)

### Added / Adicionado
- Pinned development-only coverage.py 7.16.2, statements/branches and supported Python subprocess measurement in the existing Linux/Python 3.12 CI job. No new runtime dependency.
- Separate real subprocess probe, data reset before the full suite, combined minimum 90%, local JSON/Cobertura XML validation and numeric job summary. All package modules and zero excluded lines are required; the twelve-job layout and stable quality-gate remain.
- Guias EN/PT-PT de cobertura, CI, manutenção, versão/estado/roadmap e aprovação de execução atualizados. A versão do código, release GitHub e pacote PyPI são entregas distintas; primeira publicação autorizada em preparação.

### Publication preparation / Preparação da publicação
- Bilingual registry README with absolute links, metadata consistency check, pinned release tools and manual candidate-validation/PyPI OIDC workflow. Package-only artifact transfer; no test-report upload.
- Exact protected-main ancestry/latest successful CI, published alpha tag/version checks, isolated installed-wheel tests, SHA-256 transfer verification and post-upload registry/install checks.
- Independent secret scanning uses a reviewed hash-only baseline for seven synthetic fixture findings; changed/new values remain blocked in tracked source and expanded distributions.
- GitHub release publication is authorized; actual delivery is recorded in status. PyPI account sign-in/publisher registration remains pending.

### Compatibility and limits / Compatibilidade e limites
- Existing schemas and runner 3/lock 1 protocols retained. Version binding still requires a new reviewed plan and explicit approval; no approval migration.
- Coverage is an observed Linux/Python 3.12 profile, not correctness/security proof; abrupt exits, disabled instrumentation and platform-specific paths can remain unmeasured. Reports stay on the runner without upload.
- Broader coverage profiles and report publication remain planned. No provider request is involved. Publication evidence is tracked separately from this source change.

## [0.3.0a7] — 2026-10-15 (source prerelease; not a published release)

### Added / Adicionado
- Optional `ci_runner --junit PATH`: atomically replaced UTF-8 XML with synthetic case identifiers and fixed outcome categories. Test names, parameters, messages, traces, captured streams and environment data are excluded from XML; ordinary logs remain unchanged.
- Explicit mapping for failed subtests, fixture errors/skips, expected failures and unexpected successes. Code-2 unusable/incomplete checks add a synthetic runner error. XML counts describe emitted outcomes, not unittest methods.
- Report generation and XML validation in all nine matrix and two installed-wheel jobs; offline subprocess, privacy and write-failure regressions.
- Guia JUnit EN/PT-PT, CI/manutenção/compatibilidade/README/estado/roadmap atualizados; cobertura e publicação de relatórios permanecem planeadas.

### Compatibility and limits / Compatibilidade e limites
- Schemas and runner/lock protocols remain unchanged; the 0.3.0a7 version binding requires a fresh reviewed plan/approval. Approved fixed checks do not create reports.
- Report failures exit 2; XML metadata records check status, not later reporting errors. No process-kill reporting guarantee, coverage measurement or general hostile-test isolation.
- No new dependency, provider request, artifact upload, tag, release or package publication.

## [0.3.0a6] — 2026-10-15 (source prerelease; not a published release)

### Added
- Persistent nonblocking native run guard: POSIX flock / Windows byte-region locking, noninheritable descriptor and no unprotected fallback. The guard covers approval/config/snapshot validation and fixed checks.
- Exclusive schema-1 owned run marker with PID/plan/token/time; cleanup verifies file identity and exact content. Changed/missing markers cannot produce a successful run audit entry; legacy/abandoned markers remain blocking.
- Point-in-time `doctor.run_lock` diagnostics, bounded marker fingerprint/format and explicit `recover-lock` with exact fingerprint, reason and acknowledgement that parent/child checks stopped independently.
- Original-marker archival, recovery receipt and audit event without changing plans/approvals or executing checks. Unsafe/link/reparse/hard-link state is rejected.
- Real-process contention, normal/abrupt release, recovery/cleanup/IO regression cases; EN/PT-PT locking/output/compatibility/status and maintainer documentation, plus archive checks.

### Compatibility and limits
- Source 0.3.0a6 uses runner protocol 3 and lock protocol 1 in the execution contract; previous approvals require a fresh reviewed plan/approval. Config schemas 1/2, plan schema 1, approval schema 2 and output schema 1 are retained.
- `run.guard` persists and must not be removed. Native release after parent death never establishes child liveness; existing markers require independent verification and explicit archival recovery.
- Local cooperative locking is not distributed locking, process-tree supervision or a sandbox. Recovery receipt/archive/audit writes are not one transaction; post-archive failures may return an error with evidence retained.
- No provider request, runtime dependency addition, tag, release, package publication or real-project lock recovery.

## [0.3.0a5] — 2026-10-15 (source prerelease; not a published release)

### Added
- Global optional `--json` before the CLI command: schema-1 envelope for all eight commands, handled usage/policy/filesystem errors and critical-plan warnings, with matching 0/1/2 process codes.
- UTF-8 JSON stdout, sanitized argument-error messages without argument values, and explicit data/error/warning semantics. Default command output and text help/version remain available.
- Shared fail-closed unittest statistics and a stdlib `ci_runner` that appends aggregate numeric Markdown summaries. Empty/all-skipped suites, unusable discovery and summary-write errors cannot pass normally.
- CI summaries in nine matrix jobs and two installed-wheel distribution jobs, keeping pinned Actions, permissions and the stable required `quality-gate`.
- Offline output/reporting tests, EN/PT-PT output contract, status/roadmap/README/CI/maintainer and archive coverage.

### Compatibility and limits
- Source 0.3.0a5 invalidates previous approvals through the existing package-version binding. Preserve history and create a new reviewed plan/approval. Config schemas 1/2, plan schema 1, approval schema 2 and runner protocol 2 remain supported.
- Invalid CLI arguments now return 2 from the Python `main` function instead of raising argparse's error `SystemExit`; subprocess exit status remains 2. Help/version retain their standard text/SystemExit behavior.
- Handled filesystem access errors now return a controlled CLI failure. JSON does not sanitize trusted check output or authorize execution; interrupted processes may not emit an envelope/summary.
- JUnit, coverage and uploaded report artifacts remain planned. No new dependency, live provider request, tag, release or package publication.

## [0.3.0a4] — 2026-10-15 (source prerelease; not a published release)

### Added
- Opt-in configuration schema 2 with explicit directory targets for fixed compile/unittest adapters; schema 1 remains the initialization default.
- Recursive metadata preflight before approval/run and inside the fixed child; links, junctions/reparse points, nonregular objects, inspection errors and excessive selections fail closed.
- Selected Python compilation in memory without imports/bytecode writes, and unittest discovery under one explicit root. Empty compilation selections and empty/all-skipped test suites fail.
- `doctor` reports configuration schema, effective targets and a test-file count under the selected unittest root.
- Additional approval digest for every selected regular file, including generated descendants excluded by the ordinary workspace snapshot. The workspace-wide snapshot remains required.
- Offline regression tests and EN/PT-PT target-selection, compatibility, status and distribution documentation.

### Compatibility and limits
- Source version 0.3.0a4 and runner protocol 2 invalidate earlier approvals; preserve records and create a new reviewed plan and explicit approval. Plan schema 1 and approval schema 2 remain supported; schema-2 configuration requires the additional selected-target digest.
- `plan --path` remains advisory. Target selection is not an OS filesystem allowlist or sandbox; imports/hooks remain trusted code, races are possible and generated cache changes can invalidate a later run.
- No live provider request, dependency addition, tag, release or package publication.

## [0.3.0a3] — 2026-10-15 (source prerelease; not a published release)

### Fixed
- Reject invalid advisory scope paths before contacting a provider, rather than making an unnecessary request and failing only when saving the plan.
- Validate declared path components again before persistence, approval and run, including links/reparse points added without changing the existing regular-file snapshot.

### Added
- Shared portable scope preflight: relative forward-slash paths, normalized records, future files and controlled filesystem errors; reject traversal, absolute/drive/UNC paths, reserved or ambiguous names, internal/generated components, duplicate normalized paths and nonregular files.
- Twenty regression cases covering offline/remote admission, unchanged whole-workspace checks, read-only historical review, symbolic links, Windows junctions and POSIX named pipes.
- English/PT-PT scope and compatibility guides, packaged source documentation and installed-wheel coverage.

### Compatibility
- Source version changes to 0.3.0a3. Existing execution approvals become stale through the version-bound contract; retain history and create a fresh plan and explicit approval. Configuration/plan schema 1 and approval schema 2 remain unchanged.
- Existing plans remain reviewable; approval/run reject scopes that violate the current policy. New records normalize `./` and repeated/trailing separators. Ordinary names such as `.safeops-guide.md` are supported; the former overbroad prefix rejection is removed.
- `--path` remains advisory. Snapshots stay workspace-wide; fixed checks still target `src`/`tests`. Filesystem allowlists, sandboxing and race-free filesystem isolation remain unimplemented.
- Native provider protocols are unchanged. Live OpenAI and Anthropic evidence remains tied to the separately recorded 0.3.0a2 source; no new billable request was used for this fix.

## [0.3.0a2] — 2026-10-15 (source prerelease; not a published release)

### Documentation follow-ups before 0.3.0a3

Documentation-only follow-up for source 0.3.0a2: verified a live Anthropic `claude-haiku-5-5` advisory request, saved plan and integrity review on 2026-10-15. Added dated EN/PT-PT evidence and synchronized current status, roadmap and provider guides. Compatible/local-model inference and broader account/model compatibility remain pending; runtime code, schemas and version are unchanged.

Clarified the standalone project scope and used generic confidentiality rules throughout public documentation. Added the corresponding PT-PT project-scope guide; source version remains 0.3.0a2.

Documentation-only follow-up for source 0.3.0a2: verified a live OpenAI `gpt-4.1-mini` advisory request, saved plan and integrity review on 2026-10-15. Updated EN/PT-PT status, roadmap and evidence without changing runtime code, schemas or version. The subsequent Anthropic validation is recorded above; compatible/local-model validation remains pending. No release was published.

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
