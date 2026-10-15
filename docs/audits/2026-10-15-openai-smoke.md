# Live OpenAI smoke test — 2026-10-15

[Português (Portugal)](../pt-PT/audits/2026-10-15-openai-smoke.md)

## Tested source and request

| Field | Observed value |
|---|---|
| Source version | `0.3.0a2`, alpha prerelease |
| Source commit | `5ff49659500005adf64cfaf12706b49a1de34b34` |
| Provider | Native `openai` adapter |
| Endpoint | `https://api.openai.com/v1/responses` |
| Requested model alias | `gpt-4.1-mini` |
| Result recorded | 2026-10-15 at 11:58:17 UTC |
| Remote consent | Explicit maintainer authorization and `--allow-remote` |
| Request policy | `store: false`, `max_output_tokens: 500`, network-operation timeout 30 seconds |
| Workspace | Fresh temporary workspace, separate from private/source projects |

Public task sent:

> Suggest one documentation check for a public Python CLI. Reply in one short sentence.

The native adapter sent this task, its fixed system instruction and request
metadata. No repository files or private SEND content were sent. The credential
was provisioned with explicit authorization, kept out of tool output, Git and
public artifacts, and supplied through the process environment. No credential or
private account identifier is included in this record.

## Observed result

- `init`: exit 0.
- `plan`: exit 0, one saved plan with provider `openai` and 125 characters of nonempty advice.
- `review`: exit 0, verifying the saved plan's integrity.
- Execution approvals created: 0. No fixed checks or model text were executed.
- Measured elapsed time for the planning call: 7.976 seconds; this is one observation, not a latency guarantee.

Returned advisory text:

> Verify that the CLI's usage instructions clearly describe all available commands, options, and expected input/output formats.

## Limits and documentation status

This demonstrates one authenticated native OpenAI request with usable model
output and successful local plan/review flow. It does not validate Anthropic,
compatible/local models, every OpenAI model/account, rate-limit recovery, model
security, quality beyond this response or production readiness. Token usage,
actual billed cost and account balance were not measured by this CLI test.
The requested alias is recorded; the adapter does not persist a returned model
snapshot, so no particular snapshot is asserted.

The [official model catalog](https://developers.openai.com/api/docs/models/gpt-4.1-mini)
labels this model deprecated at the time of this record. The test is historical
evidence of the successful request, not a new recommended/default model choice.
The project still requires an explicit model ID.

This documentation-only follow-up retains source version 0.3.0a2 and changes no
runtime code, schema or execution contract. Default CI remains offline/loopback,
without real API credentials or automatic billable requests. No tag, release or
package publication is part of this validation.

See [provider validation](../PROVIDER_TESTING.md), [implementation status](../STATUS.md)
and [issue #12](https://github.com/herculespt/euromind-safeops/issues/12).
