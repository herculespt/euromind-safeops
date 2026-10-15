# Roadmap

This roadmap is directional, not a promise of dates or delivered features.

Current source version: **0.3.0a2** (alpha prerelease). See [status](docs/STATUS.md)
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

## Next — Policy and integration hardening (planned)
- [ ] Explicit workspace filesystem allowlists.
- [ ] Structured JSON output options and improved CI test reporting.
- [ ] Live Anthropic/compatible-model checks and broader account/model validation; one OpenAI smoke test does not establish universal compatibility.
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
