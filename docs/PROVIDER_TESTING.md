# Provider validation and live-test procedure

<!-- safeops-version: 0.3.0a2 -->

[Português (Portugal)](pt-PT/PROVIDER_TESTING.md)

Current source: **0.3.0a2**, alpha prerelease. This is a validation record and
procedure, not a statement that a release or live model has been verified.

## Evidence — 2026-10-15

| Layer | Exercised | Boundary |
|---|---|---|
| Native OpenAI/Anthropic contracts | Fixed origins, authentication headers, request serialization and text blocks | Transport doubles; no vendor connection |
| Transport failures | HTTP 401/429/500, URL errors, timeout, malformed shapes and redacted errors | Deterministic offline fixtures |
| JSON and limits | UTF-8/BOM, duplicate keys, non-finite numbers, invalid encoding, 256,000-byte limit and 6,000-character advice | Valid objects supported; strict decoder shared with stored state |
| Compatible HTTP integration | Real POST on 127.0.0.1, CLI plan persistence, Portuguese text, no source upload or automatic approval | Local fixture server; no inference |
| Redirect policy | Real 301/302/303/307/308 responses; destination receives no request | Local fixture servers only |
| Live OpenAI/Anthropic or local-model inference | **Pending** | No API credentials or model endpoint available in the validation environment |

The compatible fixture is an HTTP service returning predetermined text, not a
provider model. The tests neither authenticate to a vendor nor prove model
quality, billing, TLS/account configuration, rate-limit recovery or universal
API compatibility. `safeops providers` reports native credential-variable presence. For the compatible
adapter, `configured: true` means adapter availability, without endpoint validation.
Neither indicator is a connectivity or model-health test.

The full suite runs in the nine Python/OS CI environments and against wheels
built with the minimum/latest backend. Integration requires the aggregate
`quality-gate`. Run these local integration tests without external access:

```bash
python -m unittest discover -s tests -p test_provider_transport.py -v
python -m unittest discover -s tests -v
```

Live validation is tracked in [issue #12](https://github.com/herculespt/euromind-safeops/issues/12), which remains open.

## Live smoke test — manual, opt-in and still pending

1. Install the reviewed source or wheel. Supply the chosen provider's credential
   securely through environment injection or a secret manager. Never paste a key
   into chat, issues, commands committed to Git, screenshots or test output.
2. Select a model ID supported by that account, or configure a trusted local
   compatible model endpoint. Chat subscriptions do not establish API access.
   A real vendor request may incur usage charges; do not enable it in default CI.
3. Use a fresh temporary workspace and the single public task below. Only task
   text and fixed request metadata are sent; do not add private project content.
4. Inspect the CLI exit code and saved plan with `safeops review PLAN_ID`.
   Success means usable textual advice was saved for that request/model only.
   Never automatically approve, run checks or execute model text as part of this test.
5. Record source version/commit, date, provider/model, exit status and outcome,
   with credentials and sensitive output excluded. Update this evidence table,
   status, roadmap and the tracking issue after verification. Leave the live test
   pending when credentials, endpoint access or usable advice are unavailable.

PowerShell, after securely configuring `OPENAI_API_KEY`:

```powershell
$SafeOpsTestModel = Read-Host "API model ID"
$SafeOpsTestRoot = Join-Path $env:TEMP ("safeops-live-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $SafeOpsTestRoot | Out-Null
safeops --root $SafeOpsTestRoot init
safeops --root $SafeOpsTestRoot plan "Suggest one documentation check for a public Python CLI." `
  --provider openai --model $SafeOpsTestModel --allow-remote --provider-timeout 30
# Inspect $LASTEXITCODE and the printed plan ID; review the plan without approving it.
```

For Anthropic, use `--provider anthropic` and `ANTHROPIC_API_KEY`. For a local
model, use `--provider openai-compatible --endpoint YOUR_TRUSTED_ENDPOINT`
and its actual model ID, optionally with `SAFEOPS_API_KEY`. Native origins cannot
be overridden. See [provider setup](PROVIDERS.md). Network-operation timeouts
are not a guaranteed total request deadline; no retry/fallback is automatic.

## Compatibility and primary references

Response validation is stricter in 0.3.0a2. Stored configuration/plan schema 1
and approval schema 2 remain unchanged; upgrading the package invalidates older
execution approvals through the existing version binding. Preserve history and
create a new plan and explicit approval before later executing checks. The live
smoke test itself never needs execution approval because it only obtains advice.

- [Execution compatibility](EXECUTION.md) and [implementation status](STATUS.md)
- [Python urllib request](https://docs.python.org/3.11/library/urllib.request.html)
- [RFC 8259 JSON interoperability](https://www.rfc-editor.org/rfc/rfc8259)
- [OpenAI Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create)
- [Anthropic Messages API](https://platform.claude.com/docs/en/api/http/messages)
