# Structured CLI output — 0.3.0a9

<!-- safeops-version: 0.3.0a9 -->

[Português (Portugal)](pt-PT/OUTPUT.md)

Use the global `--json` option **before the command** for a common output
contract. Put it first when validating automation invocations. Existing default
output remains available: two text lines for successful `init`, plain data JSON
for the other commands, and diagnostic text on stderr for handled errors.

```bash
safeops --json --root examples/demo_project init
safeops --json --root examples/demo_project doctor
safeops --json --root examples/demo_project plan "Review public documentation"
```

Initialize once; repeating initialization is an error. Do not use `doctor --json`:
the option belongs before `doctor`. A task passed after `plan --` can literally
contain `--json` without enabling the global mode.

## Envelope schema 1

All ten commands (`init`, `providers`, `doctor`, `scan`, `plan`, `review`,
`approve`, `run`, `recover-lock`, `preview`) emit one UTF-8 JSON object for handled outcomes
in this mode:

```json
{
  "schema": 1,
  "safeops_version": "0.3.0a9",
  "command": "scan",
  "ok": true,
  "exit_code": 0,
  "data": {
    "findings": [],
    "count": 0,
    "note": "Pattern checks are not a full security audit"
  },
  "error": null,
  "warnings": []
}
```

| Field | Meaning |
|---|---|
| `schema` | Integer envelope version 1; separate from config/plan/approval schemas |
| `safeops_version` | Installed source/package version |
| `command` | Parsed command, or `null` when argument parsing fails |
| `ok` | Whether the command exit code is zero; not execution approval or a security guarantee |
| `exit_code` | Matches the process status: 0, 1 or 2 |
| `data` | Original command result object; `init` adds workspace location and initialized config; `null` on handled operational/usage errors |
| `error` | `null` or an object with `code` and `message` |
| `warnings` | List of strings; critical-plan policy warning is included here |

Exit 1 means scan findings or failed approved checks. Those outcomes keep their
result in `data`, with `ok: false` and `error: null`. Exit 2 represents handled
usage/policy/filesystem errors. Error codes are `invalid_arguments`,
`policy_error` and `filesystem_error`. Usage errors have a generic message and
do not echo argument values; filesystem errors also omit raw OS details. Existing
policy/provider errors retain their controlled messages. Invalid CLI arguments
return 2 from `main` rather than raising argparse's error `SystemExit` to callers.

Handled warnings/errors do not also print on stderr in JSON mode. A critical
plan can be saved with exit 0 and `ok: true`, but its warning and risk still block
execution approval. Check `data`, `warnings` and the process status; never treat
`ok` as permission to execute code.

`--help` and `--version` remain ordinary text actions, even with `--json`. The
contract covers full documented flags and handled outcomes, not unexpected bugs,
process kills, broken output pipes or interpreter startup failures. stdout is
configured as UTF-8 in the recognized JSON mode. Python callers redirecting
stdout to their own text stream are responsible for that stream's encoding.

## Privacy and compatibility

Provider status never includes credential values. Result data can still contain
task text, advice, approval reasons, local paths and captured output of trusted
checks. Treat saved JSON as potentially sensitive. This is not a new redaction
service, signature, machine authorization or sandbox. No provider request is
needed for the output feature or its offline tests.

Source 0.3.0a9 preserves config schemas 1/2, plan schema 1 and approval schema 2;
runner protocol 3 retains native-lock protocol 1. The package-version
binding still invalidates old execution approvals: preserve history and create a fresh reviewed plan and approval.
No automatic migration, release or package publication occurs.

`doctor.data.run_lock` adds point-in-time native guard/marker diagnostics.
`recover-lock` uses the same envelope and requires explicit [recovery confirmations](LOCKING.md).
Recovery can fail after archival; inspect the archive/receipt and doctor status
before retrying. It never grants execution approval.

## CI summaries

The maintainer adapter `python -m euromind_safeops.ci_runner --tests tests`
uses the same fail-closed unittest implementation as approved checks. It requires
`GITHUB_STEP_SUMMARY` or explicit `--summary PATH`. It appends UTF-8 Markdown with
discovered/run/failure/error/skipped/expected-failure/unexpected-success counts,
completion phase and check exit code. Run counts include skipped tests.

Empty/all-skipped suites and discovery/execution failures do not pass. Summary
write failure exits 2. If discovery or execution is interrupted by a handled
exception, phase identifies the incomplete result; counts may be incomplete.
Only aggregate counts and fixed metadata enter the summary; test names,
messages and captured content remain in ordinary CI logs. This does not sanitize
those logs or prove coverage, assertions or hostile-code isolation. Process kills
may prevent a summary. Optional `--junit PATH` writes a local XML report with
synthetic outcome cases; see the [JUnit contract](REPORTING.md). Reporting-write
errors exit 2; report metadata describes check status, which can differ from the
adapter status. [Coverage measurement](COVERAGE.md) is implemented in the
Linux/Python 3.12 profile; broader coverage profiles and uploads remain planned.

Both the nine-environment matrix and the two installed-wheel jobs use this
adapter. The stable required `quality-gate` and existing permissions remain.
See [CI details](CI.md), [execution](EXECUTION.md) and [status](STATUS.md).

[Candidate previews](PREVIEW.md) use this envelope; diffs contain local file text and are potentially sensitive. Preview success grants no execution authority.
