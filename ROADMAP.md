# Roadmap

This roadmap is directional, not a promise of dates or delivered features.

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

## Next — Policy and integration hardening (proposed)
- [ ] Explicit workspace allowlists and policy schema validation.
- [ ] Structured JSON output options and improved CI test reporting.
- [ ] Broader HTTP transport failure and malformed-response tests.
- [ ] Broader test adapters without permitting AI-generated commands.
- [ ] Cross-platform locking and clearer interrupted-run recovery.
- [ ] Pin CI actions to reviewed commit SHAs and verify minimum build-tool versions.
- [ ] Expand the PT-PT documentation alongside English documentation.

## v0.3 — Controlled agent workflows (proposed)
- [ ] Specialist plugin protocol and capability manifests.
- [ ] Candidate patch proposals without direct workspace mutation.
- [ ] Dry-run diffs, provenance records and human-reviewed application.
- [ ] Isolated worktrees and safer filesystem scopes.

## Long-term research directions
- [ ] OS/container sandboxing with verifiable isolation properties.
- [ ] Independently signed audit artifacts and supply-chain provenance.
- [ ] Additional advisory provider adapters where justified.
- [ ] Community-reviewed release automation integrations.
