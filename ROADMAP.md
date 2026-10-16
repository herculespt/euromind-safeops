# Roadmap

This roadmap is directional, not a promise of dates or delivered features.

Current source version: **0.3.0a18** (alpha prerelease). See [status](docs/STATUS.md)
and [PT-PT](docs/pt-PT/STATUS.md). The first [GitHub alpha](https://github.com/herculespt/euromind-safeops/releases/tag/v0.3.0a8) and [PyPI 0.3.0a8](https://pypi.org/project/euromind-safeops/0.3.0a8/) were published on 2026-10-16. Registry hashes, clean installation and PyPI-verified publishing attestations were checked. See [delivery evidence](docs/audits/2026-10-16-first-alpha.md). Current source 0.3.0a18 remains unpublished.

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

## 0.3.0a10 — Plan-bound local proposals (implemented in source)
- [x] Persist bounded, fingerprinted local candidates using `propose`; require exact explicit plan file paths and a non-critical unchanged plan.
- [x] Bind plan/workspace/configuration/selected targets/execution contract and package version; `review-proposal` revalidates bindings and exact diffs.
- [x] Reject stale/tampered records and unsafe storage without applying source changes, granting approval or contacting a provider.
- [x] Offline lifecycle regressions, installed-wheel checks and synchronized EN/PT-PT guides, versions and GitHub tracking.

## 0.3.0a11 — Separate local staging copies (implemented in source)
- [x] Explicit `stage-proposal` fingerprint confirmation and proposal/context revalidation before and after copying.
- [x] Bounded regular-file copies with replacements only in a new local workspace, private requested modes and no inherited SafeOps/Git state or conventional environment files.
- [x] Intent plus manifest/hashed receipt; incomplete copies retained for inspection without automatic deletion or execution approval.
- [x] Offline regressions, fresh-approval trusted checks on staged code and installed-wheel/EN/PT-PT documentation validation.
- [ ] Publication of a later source milestone; public v0.3.0a8 remains unchanged.

## 0.3.0a12 — Historical stage inspection (implemented in source)
- [x] Read-only `inspect-stage` validates strict intent/receipt metadata, canonical fingerprint and retained proposal/candidate linkage.
- [x] Two bounded scans compare included regular paths, content hashes, lengths and digest; report matching/changed/incomplete without file text, writes or checks.
- [x] Preserve old schema-1 records across version/source changes, explicitly reporting historical source context without renewing execution/application authority.
- [x] Offline lifecycle/tamper/path/budget/concurrency tests and EN/PT-PT contracts, version and distribution validation.

## 0.3.0a13 — Current original-context review (implemented in source)
- [x] Read-only `review-stage` requires strict historical evidence and a matching staged copy before reviewing the original.
- [x] Bounded double observations revalidate the original snapshot, exact candidate bases, plan, configuration, selected targets, installed version and execution contract.
- [x] Explicit current/stale/incompatible observations with sanitized errors; no file text, writes, execution, provider calls, approval renewal or original application.
- [x] Offline and installed-wheel regressions, EN/PT-PT contracts, version/capability updates and required PR/main CI.

## 0.3.0a14 — Approved-check receipts (implemented in source)
- [x] Exclusive bounded run intent and schema-1 result receipt, linked to before/after plan/approval/configuration/source/selected-target/execution-contract hashes.
- [x] Revalidate inputs after every completed check; distinguish passed, failed, timed-out, changed-inputs and incomplete, and stop before the next check on change/unavailable context.
- [x] Finalize only after native-marker cleanup and audit append; retain incomplete evidence without automatic retry or deletion. Reject unsafe audit files with nonblocking regular-file opens.
- [x] Read-only historical `inspect-run`, strict schema/fingerprint/outcome validation, no captured output or free-form private text in persisted receipts.
- [x] Runner protocol 4 disables automatic import bytecode and binds receipt schema 1; config/plan/approval/lock schemas remain 1/2, 1, 2, 1.
- [x] Offline/installed-wheel regressions, required CI and synchronized EN/PT-PT contracts, version and distribution validation.

## 0.3.0a15 — Reviewed original application and recovery (implemented in source)
- [x] Read-only application review binds current original/proposal/stage and a current unchanged passed staged run containing both fixed checks.
- [x] Exact fresh human confirmation, original/stage native guards, lock protocol 2 and retained pending marker that blocks new runs/applications.
- [x] Private bounded backups and prepared files, immutable intent before source writes, per-file checks and terminal metadata; no Git operations or multi-file atomicity.
- [x] Read-only journal inspection and fresh-confirmed conservative rollback, with retained partial state and refusal of observed human edits/unsafe evidence.
- [x] Offline and installed-wheel regression validation, real interruption recovery and synchronized EN/PT-PT documentation/distribution checks.

## 0.3.0a16 — Owned fixed-check lifecycle supervision (implemented in source)
- [x] Gated fixed-command launcher, POSIX group/PID anchor and Windows kill-on-close Job Object, with no project code before native assignment.
- [x] Wait for owned descendants, bounded timeout/termination and EOF, with private bounded stream tails instead of complete in-memory capture.
- [x] Retain run marker/intent without final receipt when owned cleanup cannot be confirmed; preserve independent explicit recovery and application-pending blocks.
- [x] Real child/grandchild, parent death, unrelated-child preservation, cancellation, output and fail-closed regressions; EN/PT-PT contracts, metadata and distribution synchronized.

## 0.3.0a17 — Final job-accounting verification (implemented in source)
- [x] Recheck final zero Windows job membership within one shared cleanup budget; preserve failed-check results across transitional positive accounting.
- [x] Keep persistent/unavailable accounting fail-closed with retained marker/intent, and fixed-phase diagnostics without native error text.
- [x] Native delayed/persistent-accounting regressions and current EN/PT-PT metadata/contracts synchronized; [issue #51](https://github.com/herculespt/euromind-safeops/issues/51) tracks final validation.

## Next — Policy and integration hardening (planned)
- [ ] OS-enforced workspace filesystem allowlists that restrict arbitrary reads; 0.3.0a4 check target selection does not implement this isolation boundary.
- [ ] Broader OS/Python coverage profiles and reviewed report-artifact publication; Linux/Python 3.12 measurement and local JUnit/summaries are implemented.
- [x] Manual alpha package validation/publishing workflow, pinned Actions, registry-ready bilingual metadata and exact source/CI/hash checks.
- [x] First authorized GitHub alpha v0.3.0a8, exact tested commit, verified wheel/sdist/checksums and bilingual delivery evidence (2026-10-16).
- [x] Authorized PyPI Trusted Publisher, main-only environment without administrator bypass, original v0.3.0a8 distributions, matching registry hashes, clean installation and PyPI-verified publishing attestations (2026-10-16).
- [ ] Live compatible/local-model checks and broader account/model validation; the separate OpenAI and Anthropic smokes do not establish universal compatibility.
- [ ] Broader test adapters without permitting AI-generated commands.
- [x] Cooperative owned process-group/Job Object supervision and termination with bounded streams/cleanup (0.3.0a16, [issue #51](https://github.com/herculespt/euromind-safeops/issues/51)); deliberate POSIX escapes and hostile-code containment are outside that boundary.
- [ ] Independently verified automatic recovery, hostile/escaped-process containment and distributed/network-filesystem leases; current recovery remains explicitly human-confirmed and local.
- [ ] Expand the PT-PT documentation alongside English documentation.

## 0.3.0a18 — Reviewed maintainer tooling locks (implemented in source)
- [x] Complete direct/transitive wheel identities for two CPython 3.12/Linux x86_64/glibc profiles, mandatory hashes and exact inventory/dependency validation; [issue #53](https://github.com/herculespt/euromind-safeops/issues/53).
- [x] Dedicated coverage/release tool environments, unsupported-profile refusal, real offline hash/missing-dependency tests and controlled registry-verified refresh; [policy](docs/TOOLING.md).
- [x] EN/PT-PT tooling/CI/release/security/status contracts and archive inclusion; minimum/latest backend compatibility remains a documented deliberate exception.
- [ ] Complete build reproducibility and independent history-wide secret audit remain separate work.

## Future — Controlled agent workflows (planned; no version or date committed)
- [ ] Specialist plugin protocol and capability manifests.
- [x] Persisted manually authored candidate proposals without source mutation (0.3.0a10).
- [x] Read-only diffs and content-hash records for manually supplied existing-text replacements (0.3.0a9).
- [ ] AI-generated candidates, richer patch operations and authenticated provenance.
- [x] Explicit human-reviewed original existing-text replacements with recoverable journals and conservative rollback (0.3.0a15); [issue #49](https://github.com/herculespt/euromind-safeops/issues/49).
- [x] Separate local staging copies for reviewed candidates, with no source mutation (0.3.0a11).
- [x] Verify staging receipts and detect later staged-file changes (0.3.0a12); [issue #42](https://github.com/herculespt/euromind-safeops/issues/42), without granting source-application or execution authority.
- [x] Review current original-source compatibility before any application (0.3.0a13); [issue #45](https://github.com/herculespt/euromind-safeops/issues/45), without granting application or execution authority.
- [x] Integrity-bound local results for approved checks (0.3.0a14); [issue #47](https://github.com/herculespt/euromind-safeops/issues/47), without granting application authority.
- [ ] Isolated Git worktrees and OS-enforced filesystem scopes; local copies do not implement these boundaries.

## Long-term research directions
- [ ] OS/container sandboxing with verifiable isolation properties.
- [ ] Independently signed audit artifacts and supply-chain provenance.
- [ ] Additional advisory provider adapters where justified.
- [ ] Community-reviewed release automation integrations.
