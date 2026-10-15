# Roadmap

This roadmap is directional, not a promise of dates or delivered features.

Current source version: **0.3.0a4** (alpha prerelease). See [status](docs/STATUS.md)
and [PT-PT](docs/pt-PT/STATUS.md). Source milestones are not published releases.

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

## Next — Policy and integration hardening (planned)
- [ ] OS-enforced workspace filesystem allowlists that restrict arbitrary reads; 0.3.0a4 check target selection does not implement this isolation boundary.
- [ ] Structured JSON output options and improved CI test reporting.
- [ ] Live compatible/local-model checks and broader account/model validation; the separate OpenAI and Anthropic smokes do not establish universal compatibility.
- [ ] Broader test adapters without permitting AI-generated commands.
- [ ] Cross-platform locking and clearer interrupted-run recovery.
- [ ] Expand the PT-PT documentation alongside English documentation.

## Future — Controlled agent workflows (planned; no version or date committed)
- [ ] Specialist plugin protocol and capability manifests.
- [ ] Candidate patch proposals without direct workspace mutation.
- [ ] Dry-run diffs, provenance records and human-reviewed application.
- [ ] Isolated worktrees and safer filesystem scopes.

## Long-term research directions
- [ ] OS/container sandboxing with verifiable isolation properties.
- [ ] Independently signed audit artifacts and supply-chain provenance.
- [ ] Additional advisory provider adapters where justified.
- [ ] Community-reviewed release automation integrations.
