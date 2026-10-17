# Reviewed AI candidates — 0.3.0a20

<!-- safeops-version: 0.3.0a20 -->

[Português (Portugal)](pt-PT/GENERATION.md)

This contract adds a separate, explicitly consented source-sharing operation to
OpenAI Responses, Anthropic Messages and compatible providers. Existing `plan`
continues to send task text only. Manual previews/proposals remain provider-free.

`review-generation PLAN_ID --provider PROVIDER --model MODEL` performs no network
request or persistence. It shows the exact provider endpoint, timeout and JSON
body (including selected source text), local bindings and a confirmation
fingerprint. Use `--endpoint` only for a compatible provider. An initialized,
unchanged noncritical plan must name every selected existing file explicitly.
Directories, links/reparse points/hardlinks, internal/environment/generated paths,
non-UTF-8 or unsupported text and obvious credential patterns are refused.

`generate-proposal PLAN_ID` with the same options requires both
`--allow-source-upload` and `--confirm FINGERPRINT`. Task-only `--allow-remote` is
not consent for source upload. Read the complete review before confirming;
pattern checks cannot identify all private information or credentials. This sends
only the plan task and selected path/base-hash/content objects, fixed schema and
response instructions, plus the chosen model and fixed limits. It never sends
plan advice, repository history, configuration/state files or unrelated content.
Provider credentials are added only as request headers, never previewed/stored.
OpenAI uses store=false; provider retention/account policies remain external.

Initial bounds: 1–4 files, 8,192 source bytes each, 16,384 total source bytes,
64,000 bytes for the provider JSON payload and generated candidate respectively,
16,384 replacement bytes per file and 32,768 replacement bytes in total. Text is
BOM-free UTF-8/LF, final-newline terminated and free of controls (tab/LF allowed),
within existing 5,000-line limits. Provider output tokens are fixed at 8,192;
timeout is 1–60 seconds (default 30). These bound individual operations/storage,
not account spend, provider billing, total network wall time or OS resource use.

The confirmation binds exact payload, endpoint/provider/model/timeout, source
version/policy and current plan/source/configuration/targets/execution contract.
Bounded source reads and context are checked before sending and after return,
and again before proposal persistence. Observed changes abort; residual
filesystem/ABA races remain, and an already-sent request cannot be recalled.
No cooperative run lock is held across the network and no isolation is claimed.

One request only: no redirect, retry, continuation, fallback, tools or streaming.
The existing bounded transport/strict JSON decoder is reused. Native completion
must be explicit (OpenAI completed, Anthropic end_turn, compatible finish_reason
stop). Refusal, truncation, tools/nontext output, malformed/duplicate/nonfinite
JSON, unknown fields/paths/operations, stale bases, no-op edits or exceeded bounds
are refused without persisting provider text. Returned candidates must use the
existing schema-1 replacement shape and a nonempty subset of selected files.

Valid output becomes an **unapproved schema-2 proposal**, with strict origin
metadata: kind=ai, provider, model and reviewed request SHA-256. Manual proposals
continue to use schema 1; both schemas remain readable by review/staging/application.
Origin metadata is local/unkeyed, not authenticated provenance. Only validated
candidate text and bounded metadata persist in the private proposal; raw provider
responses and upload payloads are not retained. Generic audit stores only action,
plan ID and fixed status. A storage/audit failure may retain a valid unapproved
proposal; inspect retained records, never infer approval or automatically delete.

Continue explicitly with `review-proposal`, `stage-proposal`, fresh staged plan
and execution approval, both fixed checks, current original-context/application
review and exact application confirmation. Generation never runs checks, stages,
applies, rolls back, changes Git or grants/renews approval. The version change
requires fresh plans/proposals/approvals. Public GitHub/PyPI 0.3.0a8 predates this
capability and stays unchanged.

The offline/loopback tests establish contracts and refusals, not model quality.
Any separate live smoke must use reviewed non-private synthetic files and report
its exact provider/model/version/limits without credentials. Provider availability
and semantic correctness are never inferred from a valid candidate or prior smoke.

Primary references: [OpenAI Responses](https://developers.openai.com/api/reference/resources/responses/methods/create),
[Anthropic stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons).


## Optional Git staging boundary

[Git staging worktrees](GIT_STAGING.md) require separate exact confirmation and schema-2 stage evidence. Default copies retain schema 1. Git-stage inspection/current review/application preflight invoke fixed read-only installed Git commands to validate linkage/base/index; they never execute project code or grant approval. A regular `.git` metadata file is excluded from source digests and validated separately for Git stages. Registration alone uses the original native guard and preserves partial locked worktrees on failure. Shared Git metadata is not OS isolation; signed SafeOps provenance remains planned in #61. Existing explicit fresh staged approval/check/application/rollback gates remain.
