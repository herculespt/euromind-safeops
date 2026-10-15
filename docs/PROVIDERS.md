# AI advisory providers — v0.2.0

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

**Never commit, paste or log real API keys.** Prefer a secret manager or environment injection. `safeops providers` only reports whether variables are configured, never their contents.

## Security and limitations

- Provider calls are opt-in; no provider is contacted during `init`, `doctor`, `scan`, `review`, `approve`, `run`, or offline `plan`.
- OpenAI requests specify `store: false`; consult the provider's current API data policies for full data retention details.
- Provider calls have a 15-second default timeout (configurable from 1 to 60 seconds), bounded JSON responses, no follow-up model tool calls and no model-controlled execution.
- Model responses are recorded in `.safeops/plans` as **untrusted advisory text** and must be reviewed before approval.
- Risk classification, workspace integrity, and execution gates remain deterministic, unaffected by the text returned by any provider.
- Network tests use mocked HTTP transport. They do not prove live API authentication or compatibility with every individual model.
- Official API protocol references: [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses), [Anthropic Messages API](https://docs.anthropic.com/en/api/messages).
