# Changelog

The format follows Keep a Changelog conventions; versions follow Semantic Versioning where practicable.

## 0.3.0a15 — 2026-10-16

- Add `review-application`, `apply-stage`, `inspect-application` and `rollback-application` for explicitly reviewed existing writable UTF-8 replacements after unchanged staged compile and unit tests pass.
- Bind exact current confirmation to source/control/stage/run evidence; serialize original/stage operations with native guards and lock protocol 2. Retained application markers block later runs/applications.
- Prepare bounded private backups/replacements and immutable intent before source writes; retain per-file identity/hash metadata and completion records without public source/output/credential text.
- Restore only known owned candidate files after fresh inspection/confirmation; refuse observed human edits, unsafe/unknown partial evidence and foreign markers. Retain all history; no forced recovery, Git operation, multi-file atomicity, power-loss durability or OS isolation claim.
- Add interruption, intermediate failure, stale confirmation, rollback conflict, strict bounds and real installed-check regressions; synchronize EN/PT-PT guides, metadata, package contents and GitHub tracking.
- Runner 4, config 1/2, plan 1, approval 2 and envelope 1 retained; upgrading requires fresh version-bound execution approval/proposals. Public GitHub/PyPI 0.3.0a8 assets remain unchanged.
- PT-PT: aplicação explícita de substituições revistas ao original após testes aprovados na cópia, backups/journal privados, bloqueio de operações pendentes e rollback conservador confirmado; falhas e alterações humanas preservadas para inspeção.

## 0.3.0a14 — 2026-10-16

- Persist exclusive schema-1 run intents/results with bounded before/after plan, approval, source, configuration, selected-target and execution-contract hashes. Keep captured output, task/advice and approval reasons out of these records.
- Revalidate inputs after each completed fixed check and stop on change/unavailable context. Distinguish passed, failed, timed-out, changed-inputs and incomplete; finalize only after lock cleanup/audit, retaining partial evidence on operational failure without retry or deletion.
- Add read-only historical `inspect-run` with strict bounded schema/fingerprint/link/outcome checks. It never renews approval, revalidates current source or authenticates provenance.
- Runner protocol 4 binds receipt schema 1 and suppresses automatic Python import bytecode in fixed children. Config schemas 1/2, plan 1, approval 2, lock 1 and envelope 1 remain supported; upgrading requires fresh reviewed approval.
- Harden local audit opens against hardlinks/reparse points/nonregular files, including nonblocking FIFO rejection. Add offline/distribution regressions and synchronize English/PT-PT contracts, capability tables, roadmap and source version. Public GitHub/PyPI alpha stays 0.3.0a8.
- PT-PT: recibos locais ligados aos inputs e resultados dos checks aprovados, inspeção histórica sem escrita e deteção de alterações durante a execução; sem aplicação ao original nem renovação de aprovação.

## 0.3.0a13 — 2026-10-16

- Add read-only `review-stage`: require a matching retained stage, then compare two bounded observations of the current original snapshot, candidate bases, bound plan, configuration, selected targets, installed version and execution contract.
- Report `current`, `stale` or `incompatible` without file text, writes, approval renewal, code execution, provider access or original-workspace application. Reject malformed/unsafe/oversized/unreadable/changing evidence with a sanitized policy error.
- Reuse decoded configuration validation and preserve the historical `inspect-stage` contract. Original snapshots retain environment/ordinary generated-name files; selected targets include their configured snapshot exclusions.
- Update source/distribution contracts and English/PT-PT capability, compatibility, roadmap and status documentation. Published GitHub/PyPI alpha remains 0.3.0a8.
- PT-PT: acrescenta revisão sem escrita da compatibilidade com o original atual, com observações limitadas e testes offline; não concede aprovação nem aplica alterações ao original.

## [Unreleased]

Current source milestone: **0.3.0a12**. First GitHub alpha and [PyPI 0.3.0a8](https://pypi.org/project/euromind-safeops/0.3.0a8/) published on 2026-10-16. Source 0.3.0a12 remains unpublished. See [delivery evidence](docs/audits/2026-10-16-first-alpha.md).

### Registry delivery follow-up / Conclusão da entrega no registo — 2026-10-16

- Registered the explicitly authorized Trusted Publisher for `herculespt/euromind-safeops`, workflow `publish.yml`, environment `pypi`; exact `main` deployment branch only, zero tags and administrator bypass disabled.
- Published original v0.3.0a8 wheel/sdist without rebuilding or changing the tag. Workflow 38874124869 passed all three jobs, including registry filename/hash equality and fresh installation/CLI version verification. Both registry files show publishing attestations verified by PyPI.
- Atualizados README, estado, roadmap, guias de publicação/manutenção, descrição do pacote, evidência EN/PT-PT e textos GitHub. O commit do publisher é 95a8bd5; o código distribuído mantém o commit 035c36b. Sem nova versão, alteração de comportamento ou pedido a fornecedores; a descrição incorporada nos pacotes já publicados mantém os bytes originais.

## [0.3.0a12] — 2026-10-16 (source alpha; no new published release)

- Add read-only `inspect-stage STAGE_ID` for retained schema-1 stages: strict bounded intent/receipt parsing, canonical fingerprint, manifest validation and historical proposal/candidate/source linkage.
- Compare two bounded scans of included independent regular files and report sorted missing/extra/changed paths, counts and digests without file text. Matching returns 0; changed/incomplete return 1; invalid/unsafe/unreadable/oversized/changing evidence returns sanitized error 2.
- Inspect old versions without renewing current-original/configuration bindings, execution approvals or source-application authority. Preserve partial copies and every record; no writes, cleanup, provider requests or code execution.
- Testes offline de integridade, ciclo de vida, caminhos, limites, concorrência e ausência de escrita; CLI, versão, documentação EN/PT-PT, capacidades, roadmap e contratos de distribuição atualizados. A release GitHub/PyPI 0.3.0a8 mantém os ficheiros originais.
- Content-disclosure assertions use exact fixture text and an explicit `private` path component, avoiding false failures for normal macOS `/private/` workspace paths.
- Config/plan/approval/output schemas and runner 3/lock 1 retained; new execution approvals/proposals still require a fresh reviewed plan after this version update. Original-workspace application, rollback, Git worktrees, OS isolation and signed SafeOps provenance remain planned.

## [0.3.0a11] — 2026-10-16 (source alpha; no new published release)

- Add `stage-proposal PROPOSAL_ID --confirm FINGERPRINT`: materialize replacements only in a new local copy after exact reviewed-fingerprint confirmation. Revalidate proposal/source context; leave original source, approvals and Git untouched.
- Bounded independent regular-file copying with conventional environment, Git/SafeOps and generated-state exclusions; private requested file/directory modes, intent, copy manifest and fingerprinted receipt and no execution permission grant.
- Retain incomplete stage directories on failure; no automatic deletion or rollback. Ready receipt and audit are separate writes, so audit failure can return an error with the ready copy retained.
- 21 offline lifecycle/failure regressions, including separate fresh approval and real fixed checks on staged code. Document-link hygiene now scopes exclusions relative to the package root so staged copies under `.safeops` are checked.
- Cópias locais, versão, guias EN/PT-PT, README, capacidades, roadmap, changelog e registos GitHub sincronizados. Sem novas dependências, pedidos a fornecedores ou aplicação ao projeto original.
- Config/plan/approval/output schemas and runner/lock protocols retained; version binding requires fresh reviewed execution approval and proposals under this version. Git worktrees, original-source application/rollback, OS isolation and signed SafeOps provenance remain planned. Public v0.3.0a8 remains unchanged; PyPI was pending at this milestone and is delivered in the follow-up above.

## [0.3.0a10] — 2026-10-16 (source alpha; no new published release)

- Add `propose PLAN_ID CANDIDATE` and read-only `review-proposal PROPOSAL_ID` for locally authored candidates. Strict schema-1 records contain the original candidate, canonical hashes and plan/workspace/configuration/selected-target/execution-contract bindings.
- Require explicit exact plan file paths and a non-critical unchanged plan. Recheck context around validation; reject stale/tampered records, unsafe storage, invalid schemas and bounded-input violations.
- Store proposals with private file permissions where supported and a content-free creation audit event. Source, approvals and Git state are untouched; reviewing grants no application or execution authority. Local records remain mutable and unsigned.
- Propostas locais e guias EN/PT-PT, README, estado, arquitetura, compatibilidade, roadmap e versão sincronizados. Atualizações continuam a exigir novo plano/revisão/aprovação de execução; sem migração automática.
- Config/plan/approval/output schemas and runner/lock protocols retained. No runtime dependency or provider request added. Application/rollback, AI generation and later source publication remain planned; public v0.3.0a8 assets stay unchanged. PyPI was pending at this milestone; see the delivery follow-up above.

## [0.3.0a9] — 2026-10-16 (source alpha; no new published release)

- Add read-only `preview` for strict local schema-1 replacement candidates: exact base SHA-256, UTF-8 unified diffs and canonical-candidate/result hashes. No files, approvals, audit state or Git history are changed; no provider or checks run.
- Reject unknown fields, stale/nonregular/linked paths, duplicate/case-colliding names, malformed JSON/text and byte/line limits. Current support is existing BOM-free LF text with final newlines; creation/deletion/renames/binaries/application remain planned.
- Preview e documentação EN/PT-PT, tabelas de capacidades, estado, arquitetura, compatibilidade e roadmap atualizados. Versão ligada ao contrato exige novo plano/revisão/aprovação para execução; schemas anteriores mantidos.
- Separate CI report basenames from the parallel coverage data prefix, avoiding report-as-database warnings without changing the coverage threshold or measured scope.
- Published v0.3.0a8 and its distributions stay immutable; PyPI was pending at this milestone and is delivered in the follow-up above. No new release or live provider request is implied by this source milestone.

## [0.3.0a8] — 2026-10-15 (alpha source; publication tracked in docs/STATUS.md)

### Added / Adicionado
- Pinned development-only coverage.py 7.16.2, statements/branches and supported Python subprocess measurement in the existing Linux/Python 3.12 CI job. No new runtime dependency.
- Separate real subprocess probe, data reset before the full suite, combined minimum 90%, local JSON/Cobertura XML validation and numeric job summary. All package modules and zero excluded lines are required; the twelve-job layout and stable quality-gate remain.
- Guias EN/PT-PT de cobertura, CI, manutenção, versão/estado/roadmap e aprovação de execução atualizados. A versão do código, release GitHub e pacote PyPI são entregas distintas; primeira alpha GitHub publicada em 2026-10-16, com evidência datada. O PyPI ficou inicialmente pendente e foi concluído no seguimento acima.

### Publication preparation / Preparação da publicação
- Bilingual registry README with absolute links, metadata consistency check, pinned release tools and manual candidate-validation/PyPI OIDC workflow. Package-only artifact transfer; no test-report upload.
- Exact protected-main ancestry/latest successful CI, published alpha tag/version checks, isolated installed-wheel tests, SHA-256 transfer verification and post-upload registry/install checks.
- Independent secret scanning uses a reviewed hash-only baseline for seven synthetic fixture findings; changed/new values remain blocked in tracked source and expanded distributions. Nine offline regression cases cover path/type/hash boundaries, strict control metadata and standalone archives.
- Published GitHub prerelease v0.3.0a8 on 2026-10-16 at `035c36b1b646a6c75178d5db6c19d8c55d624dcf`; attached wheel/sdist/checksums match verified bytes. Twelve main CI jobs and candidate workflow passed; 209 installed-wheel tests, zero failures/errors, three platform skips. PyPI sign-in/publisher registration was initially pending; completion is recorded above. This documentation follow-up does not move the public tag or rebuild assets.

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
