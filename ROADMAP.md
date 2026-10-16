# Roadmap

This roadmap is directional, not a promise of dates or delivered features.

Current source version: **0.3.0a9** (alpha prerelease). See [status](docs/STATUS.md)
and [PT-PT](docs/pt-PT/STATUS.md). The first [GitHub alpha](https://github.com/herculespt/euromind-safeops/releases/tag/v0.3.0a8) was published on 2026-10-16; PyPI remains pending. See [delivery evidence](docs/audits/2026-10-16-first-alpha.md).

## v0.1.0 — Initial open-source foundation (implemented)
- [x] Packageable CLI, offline plans and specialist suggestions.
- [x] Conservative risk classes and blocked critical executions.
- [x] Approval fingerprinting and workspace integrity checks.
- [x] Fixed test/compile checks, local audit trail and best-effort scan.
- [x] Optional explicit OpenAI-compatible advisory provider.
- [x] Architecture, threat model, security and contribution documentation.

## v0.2.0 — Native advisory integrations (implemented in source)
- [x] Native OpenAI Responses and Anthropic Messages adapters, with explicit remote consent.
- [x] Provider configuration status without credential disclosure.
- [x] Offline provider contract tests and setup documentation.
- [x] Nine-environment CI matrix and stable aggregate `quality-gate`.
- [x] Active `main` ruleset with PRs, strict checks and no bypass exceptions (verified 2026-10-15).

No tagged release or package publication is implied by this source version.

## 0.3.0a1 — Policy and execution hardening (implemented in source)
- [x] Strict config schema and UTF-8 JSON validation, including duplicate keys and non-finite numbers.
- [x] Versioned execution contract and approval schema 2; old approvals require a new plan and review.
- [x] Child-process unittest discovery; empty and all-skipped suites fail.
- [x] Nested regular test packages, discovery errors and timeout regression coverage.
- [x] Source, metadata, CLI help and current-document version consistency checks.
- [x] English/PT-PT execution policy, compatibility guide and implemented-versus-planned status.
- [x] Pinned CI Actions and minimum/latest-backend builds, with the full suite tested against installed wheels.

## 0.3.0a2 — Provider transport validation (implemented in source)
- [x] Shared strict UTF-8 JSON object decoding for stored state and provider responses.
- [x] HTTP/URL/timeout errors, response byte limits, malformed provider responses and redacted CLI failures covered by offline tests.
- [x] Real loopback HTTP integration, including CLI plan creation and blocked redirects; no model inference is claimed.
- [x] EN/PT-PT provider setup, test evidence and live-test procedure.
- [x] Separate live OpenAI `gpt-4.1-mini` smoke test on 2026-10-15: one saved advisory plan, successful integrity review and no execution approval; see [evidence](docs/audits/2026-10-15-openai-smoke.md).
- [x] Separate live Anthropic `claude-haiku-5-5` smoke test on 2026-10-15: one saved advisory plan, successful integrity review and no execution approval; see [evidence](docs/audits/2026-10-15-anthropic-smoke.md).

## 0.3.0a3 — Advisory scope preflight (implemented in source)
- [x] Portable relative path validation before any provider invocation and plan persistence.
- [x] Recheck declared path components at approval/run; reject links, junctions, traversal and internal/generated paths.
- [x] Canonical advisory path records, future-path support and regression tests without real provider access.
- [x] EN/PT-PT scope policy and upgrade documentation; existing configuration/plan/approval schemas retained.

## 0.3.0a4 — Explicit check directory targets (implemented in source)
- [x] Opt-in config schema 2 selects compile directories and one unittest discovery root; schema 1 defaults and advisory `--path` remain unchanged.
- [x] Recursive metadata preflight in the parent and fixed child rejects links, reparse points, nonregular objects and inspection failures.
- [x] Compile selected Python sources in memory; keep empty/all-skipped test checks failing.
- [x] Bind selected regular files, including generated descendants, in the approval; preserve the workspace-wide snapshot.
- [x] EN/PT-PT targeting, compatibility and status guides, plus installed-wheel regression coverage.

## 0.3.0a5 — Structured output and CI summaries (implemented in source)
- [x] Optional global `--json`: one schema-1 envelope for handled command results, errors and warnings, preserving default output and process exit codes.
- [x] UTF-8 output and argument-error messages that do not echo supplied values; explicit help/version and process-failure boundaries.
- [x] Shared fail-closed unittest statistics and aggregate Markdown summaries in all nine matrix and two installed-wheel jobs.
- [x] Offline output/reporting regressions, EN/PT-PT contract and synchronized current documentation/version/status.

## 0.3.0a6 — Native local locking and explicit recovery (implemented in source)
- [x] Persistent nonblocking POSIX/Windows native guard and exclusively created owned marker; no unprotected fallback.
- [x] Guard covers approval/snapshot validation and checks; descriptor noninheritance and unchanged-owner cleanup.
- [x] Read-only point-in-time doctor diagnostics, bounded marker fingerprint/format and no PID-based liveness inference.
- [x] Explicit recovery confirmation/acknowledgement/reason, busy-guard rejection, original-marker archive, receipt and audit without granting approval.
- [x] Real subprocess contention/abrupt-death regressions and EN/PT-PT lock/compatibility/status/maintainer guides.

## 0.3.0a7 — Local JUnit reporting (implemented in source)
- [x] Optional atomic UTF-8 JUnit export from maintainer CI; synthetic case identifiers and fixed outcome categories without test-supplied text.
- [x] Subtest/fixture outcomes, expected failures, unexpected successes and visible runner errors for unusable/incomplete checks.
- [x] Generate and validate XML in nine matrix and two installed-wheel jobs; no upload or coverage claim.
- [x] Offline reporting regressions and synchronized EN/PT-PT contract, compatibility, version and implemented/planned status.

## 0.3.0a8 — Measured CI coverage (implemented in source)
- [x] Development-only pinned coverage tool, package statements/branches and supported subprocess measurement in Linux/Python 3.12.
- [x] Independent child probe, clean measurement data, local JSON/Cobertura XML, numeric summary and minimum 90% combined gate.
- [x] Require all package modules, zero excluded lines and matching JSON/XML counts without changing the twelve-job CI layout.
- [x] EN/PT-PT coverage/CI/status/upgrade documentation and explicit fresh-plan/review/approval/run procedure.

## 0.3.0a9 — Local candidate previews (implemented in source)
- [x] Read-only `preview` command for locally authored strict schema-1 text replacement candidates.
- [x] Exact per-file base hashes, bounded regular-file reads, portable path checks and unified diffs with candidate/result hashes.
- [x] Reject stale files, duplicate/case-colliding paths, links/reparse points, malformed JSON/UTF-8 and unsupported text forms; no write, provider request or approval grant.
- [x] Offline regressions, installed-package validation and EN/PT-PT preview/compatibility/status documentation.
- [ ] A separately authorized release of this source milestone; public v0.3.0a8 remains unchanged.

## Next — Policy and integration hardening (planned)
- [ ] OS-enforced workspace filesystem allowlists that restrict arbitrary reads; 0.3.0a4 check target selection does not implement this isolation boundary.
- [ ] Broader OS/Python coverage profiles and reviewed report-artifact publication; Linux/Python 3.12 measurement and local JUnit/summaries are implemented.
- [x] Manual alpha package validation/publishing workflow, pinned Actions, registry-ready bilingual metadata and exact source/CI/hash checks.
- [x] First authorized GitHub alpha v0.3.0a8, exact tested commit, verified wheel/sdist/checksums and bilingual delivery evidence (2026-10-16).
- [ ] Actual PyPI publisher registration/publication and registry installation/attestations; blocked on secure account authentication and precise trust-grant review.
- [ ] Live compatible/local-model checks and broader account/model validation; the separate OpenAI and Anthropic smokes do not establish universal compatibility.
- [ ] Broader test adapters without permitting AI-generated commands.
- [ ] Process-tree supervision/termination, independently verified automatic recovery and distributed/network-filesystem leases; current recovery remains explicitly human-confirmed and local.
- [ ] Expand the PT-PT documentation alongside English documentation.

## Future — Controlled agent workflows (planned; no version or date committed)
- [ ] Specialist plugin protocol and capability manifests.
- [ ] Candidate patch proposals without direct workspace mutation.
- [x] Read-only diffs and content-hash records for manually supplied existing-text replacements (0.3.0a9).
- [ ] AI-generated candidates, richer patch operations, authenticated provenance and human-reviewed application.
- [ ] Isolated worktrees and safer filesystem scopes.

## Long-term research directions
- [ ] OS/container sandboxing with verifiable isolation properties.
- [ ] Independently signed audit artifacts and supply-chain provenance.
- [ ] Additional advisory provider adapters where justified.
- [ ] Community-reviewed release automation integrations.
