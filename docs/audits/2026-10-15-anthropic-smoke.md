# Live Anthropic smoke test — 2026-10-15

[Português (Portugal)](../pt-PT/audits/2026-10-15-anthropic-smoke.md)

## Tested source and request

| Field | Observed value |
|---|---|
| Source version | `0.3.0a2`, alpha prerelease |
| Source commit | `c13c2cb039565512c50a98fec2f7cb17a941d2bf` |
| Provider | Native `anthropic` adapter |
| Endpoint | `https://api.anthropic.com/v1/messages` |
| Requested model ID | `claude-haiku-5-5` |
| Result recorded | 2026-10-15 at 13:22:49 UTC |
| Remote consent | Explicit maintainer authorization and `--allow-remote` |
| Request policy | `anthropic-version: 2023-06-01`, `max_tokens: 500`, network-operation timeout 30 seconds |
| Workspace | Fresh temporary workspace, separate from source/private projects |

The account's Models API listed the requested model before the advisory request.
The credential was created with explicit authorization, kept outside public
source and tool output, and injected through the process environment. No key,
private account identifier or billing state is included in this record.

Public task sent:

> Suggest one documentation check for a public Python CLI. Reply in one short sentence.

Only this task, the fixed system instruction and request metadata were sent;
no repository files or private data were uploaded.

## Observed result

- `init`: exit 0.
- `plan`: exit 0, exactly one saved plan with provider `anthropic` and 170 characters of nonempty advice.
- `review`: exit 0, verifying the saved plan's integrity.
- Execution approvals created: 0. No fixed checks or model text were executed by this smoke test.
- Measured elapsed time for the planning call: 7.692 seconds; one observation, not a latency guarantee.

Returned advisory text:

> Verify that the README's installation and quick-start commands run exactly as written on a clean environment, and that the `--help` output matches the documented options.

## Limits and documentation status

This demonstrates one authenticated native Anthropic request and successful
local plan/review flow. It does not validate compatible/local models, every
Anthropic account/model, rate-limit recovery, broad model quality, model security
or production readiness. The requested model ID is recorded; the adapter does
not persist a returned model snapshot or usage metadata. Actual token usage and
billed cost were not measured by this CLI test. The successful OpenAI request is
separate [historical evidence](2026-10-15-openai-smoke.md).

This documentation-only follow-up retains source version 0.3.0a2 and changes no
runtime code, schema or execution contract. Default CI remains offline/loopback,
without real API credentials or automatic billable requests. No tag, release or
package publication is part of this validation.

See [provider validation](../PROVIDER_TESTING.md), [implementation status](../STATUS.md)
and [issue #17](https://github.com/herculespt/euromind-safeops/issues/17).
