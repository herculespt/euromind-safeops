# OpenAI reviewed-generation smoke — 2026-10-17

[Português (Portugal)](../pt-PT/audits/2026-10-17-openai-generation-smoke.md)

Observed at 2026-10-16T23:28:36Z (2026-10-17 00:28:36 Europe/Lisbon), using
source **0.3.0a19**. This is separate from the source-0.3.0a2 advisory smokes.

One real OpenAI Responses request used the previously authorized project key,
read locally from ignored `.env.local` without displaying or rewriting it.
Requested model: `gpt-4.1-mini`; returned model: `gpt-4.1-mini-2025-04-14`.
Observed usage: **250 input + 66 output = 316 total tokens**. Fixed output cap:
8,192 tokens; configured network timeout: 60 seconds; no retry/fallback.

## Exact non-private fixture and outcome

A new temporary workspace outside the repository contained only this 19-byte
selected source, `greeting.py`:

```python
GREETING = "Hello"
```

The offline task asked to change GREETING from Hello to Olá, preserving the name
and final newline. The complete reviewed request was checked to include only that
task, schema and selected path/base-hash/content, fixed instructions/model/limits.
No repository source, configuration, Git history or private state was uploaded.
Serialized provider body: 1,101 bytes; OpenAI store=false. Source upload consent
used the exact current review fingerprint before the single request.

- Plan ID: `370dd85cb5c4`; proposal ID: `9ff1860119cd`.
- Reviewed request fingerprint: `sha256:7e922c20383bd1616acad51556540655679de0cab04387088a00910dc3b7d9ab`.
- Original source: `sha256:3ffca746f9bd94691434fdba37ed9d5eab5a5a493346981edacda449eb8e8809`.
- Validated replacement: `sha256:cbb5ec4cae0a9897cbf39aabeac4a7219f66dc506f5e1aee6ea70496c1b429e9`.
- Strict schema-2 proposal and origin metadata passed local `review-proposal`.
- AST inspection, without execution, confirmed exactly one assignment to GREETING
  with constant value Olá. The provider's raw response was not retained publicly.
- Original fixture source and the existing credential file remained byte-identical.
- Zero execution approvals/checks, staging, original application, Git operations or
  new release/publication. The candidate stayed unapproved.

These are local observations and unkeyed fingerprints, not authenticated
provenance. A successful one-file smoke does not prove general model quality,
provider retention behavior, all accounts/models, native Anthropic generation or
compatible/local-model inference. The ordinary CI remains offline/loopback and
must pass separately before protected integration. Existing GitHub/PyPI 0.3.0a8
source/tag/assets remain unchanged.
