# AI advisory providers — 0.3.0a15

<!-- safeops-version: 0.3.0a15 -->

[Português (Portugal)](pt-PT/PROVIDERS.md)

Native adapters were introduced in source version 0.2.0. Source 0.3.0a2 introduced strict response JSON validation; 0.3.0a3 adds [scope preflight](SCOPE.md) before provider access, with unchanged advisory-only request protocols. See [test evidence and live-test procedure](PROVIDER_TESTING.md); separate live OpenAI `gpt-4.1-mini` and Anthropic `claude-haiku-5-5` requests passed on source 0.3.0a2 on 2026-10-15. Compatible/local-model inference remains unverified; these smokes do not establish compatibility with all models or accounts.

EuroMind SafeOps supports four advisory backends. **All provider outputs are untrusted text, not executable actions.** Native integrations use fixed official HTTPS API endpoints with no endpoint override.

| Value for `--provider` | Protocol | Authentication | Remote consent |
|---|---|---|---|
| `offline` | Deterministic local advisory | None | Not applicable |
| `openai` | OpenAI Responses API (`/v1/responses`) | `OPENAI_API_KEY` | Required |
| `anthropic` | Anthropic Messages API (`/v1/messages`) | `ANTHROPIC_API_KEY` | Required |
| `openai-compatible` | Chat Completions compatible API | Optional `SAFEOPS_API_KEY` | Required |

The models are specified explicitly with `--model`; the project intentionally does not freeze a vendor-specific default model. Use a model ID that your API account supports. **A Claude.ai or ChatGPT subscription is not the same thing as API credits.** Provider API calls may incur usage charges.

## Prerequisites

Install with `python -m pip install -e .`, then run:

```bash
safeops providers
safeops --root examples/demo_project init
```

Initialize each workspace only once. For each remote advisory request SafeOps sends *only your task text* (not project files), plus a short system instruction. Avoid secrets, private details and source code in the task prompt; the heuristic secret detector is not exhaustive.

### OpenAI — native Responses API

```bash
export OPENAI_API_KEY="<api-key>"
safeops --root examples/demo_project plan "Review the module boundaries" \
  --provider openai --model YOUR_OPENAI_MODEL_ID --allow-remote
```

### Anthropic — native Messages API

```bash
export ANTHROPIC_API_KEY="<api-key>"
safeops --root examples/demo_project plan "Review the testing strategy" \
  --provider anthropic --model YOUR_CLAUDE_MODEL_ID --allow-remote
```

Use an Anthropic key scoped to one workspace. The current adapter does not send
`anthropic-workspace-id`; multi-workspace keys are not validated. The tested
model ID is evidence, not a new default. See the [dated Anthropic record](audits/2026-10-15-anthropic-smoke.md).

### Local OpenAI-compatible service

```bash
safeops --root examples/demo_project plan "Review code organization" \
  --provider openai-compatible \
  --endpoint http://127.0.0.1:8080/v1/chat/completions \
  --model YOUR_LOCAL_MODEL --allow-remote
```

Some compatible servers require `SAFEOPS_API_KEY`; others do not. The compatible adapter requires HTTPS except for literal loopback HTTP. It does not send source files. Redirects are rejected. The endpoint is user-configured and should only be used when trusted.

### Windows PowerShell

```powershell
$env:OPENAI_API_KEY = "<api-key>"
$env:ANTHROPIC_API_KEY = "<api-key>"

safeops --root examples/demo_project plan "Review architecture" `
  --provider openai --model YOUR_OPENAI_MODEL_ID --allow-remote

safeops --root examples/demo_project plan "Review architecture" `
  --provider anthropic --model YOUR_CLAUDE_MODEL_ID --allow-remote
```

**Never commit, paste or log real API keys.** Prefer a secret manager or environment injection. `safeops providers` reports native credential-variable presence, never their contents. For the compatible adapter, `configured: true` means adapter availability, not a verified endpoint or model.

SafeOps reads credentials from the process environment; it does not automatically
load `.env.local`. An approved local env file must remain outside Git/artifacts and
be loaded by a trusted launcher. The heuristic scanner still inspects ignored files
inside its workspace; validate public-source exports from a clean checkout without
local credentials instead of weakening scanner rules.

## Security and limitations

- Provider calls are opt-in; no provider is contacted during `init`, `doctor`, `scan`, `review`, `approve`, `run`, or offline `plan`.
- OpenAI requests specify `store: false`; consult the provider's current API data policies for full data retention details.
- Provider calls have a 15-second default network-operation timeout (configurable from 1 to 60 seconds), not a guaranteed total wall-clock deadline. The response read is limited to 256,001 bytes; objects above 256,000 bytes fail. Advice is limited to 6,000 characters. There are no automatic retries, follow-up model tool calls or model-controlled execution.
- Responses must be UTF-8 JSON objects (optional UTF-8 BOM accepted). Duplicate object keys, non-finite numbers/overflow, other encodings and malformed/non-object JSON are rejected with controlled errors. Unknown non-text content blocks are not executed; a usable text response is still required.
- Model responses are recorded in `.safeops/plans` as **untrusted advisory text** and must be reviewed before approval.
- Risk classification, workspace integrity, and execution gates remain deterministic, unaffected by the text returned by any provider.
- CI uses transport doubles and a real HTTP server on literal loopback with deterministic fixture responses. Native request/response contracts are tested without contacting vendors. These tests do not prove live API authentication, model inference or compatibility with every individual model. See the [testing guide](PROVIDER_TESTING.md).
- Official API protocol references: [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses), [Anthropic Messages API](https://docs.anthropic.com/en/api/messages).
