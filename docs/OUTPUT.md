# Structured CLI output — 0.3.0a16

<!-- safeops-version: 0.3.0a16 -->

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

All twenty commands (`init`, `providers`, `doctor`, `scan`, `plan`, `review`,
`approve`, `run`, `recover-lock`, `preview`, `propose`, `review-proposal`, `stage-proposal`, `inspect-stage`, `review-stage`, `inspect-run`, `review-application`, `apply-stage`, `inspect-application`, `rollback-application`) emit one UTF-8 JSON object for handled outcomes
in this mode:

```json
{
  "schema": 1,
  "safeops_version": "0.3.0a16",
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

Exit 1 means scan findings, failed/timed-out/changed-inputs/incomplete approved runs, changed/incomplete stage inspection or stale/incompatible stage review. Those outcomes keep their
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

Source 0.3.0a16 preserves config schemas 1/2, plan schema 1 and approval schema 2;
runner protocol 5 uses native-lock protocol 3. The package-version
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

[Proposal creation/review](PROPOSALS.md) use this envelope too. Creation returns identifiers/hashes without candidate text; review includes full diffs. Success is not execution or application approval.

[Staging](STAGING.md) returns local identifiers, workspace path, receipt fingerprint and counts without file text. Handled failure after allocation identifies the retained stage; an audit failure may leave a ready receipt even with exit 2. Inspect actual state before retrying.

`inspect-stage` returns `matching` (0), `changed` (1) or `incomplete` (1), without
text/diffs, writes or audit append. Missing/extra/changed paths are relative and
sorted. Historical version/source fields never renew approval; see [the contract](STAGING.md).
Invalid/unsafe/oversized/unreadable/changing evidence returns a generic policy error (2).

`review-stage` uses the same envelope: `current` (0), `stale` (1) or `incompatible` (1), without file text/writes/approval. Invalid or unsafe evidence returns sanitized policy error (2). See [original-context review](STAGE_REVIEW.md) for boolean checks, fixed reason codes and limits.

`run` now adds `run_id`, `receipt_fingerprint` and fixed `reasons`. `run`/`inspect-run` use passed (0), failed/timed-out/changed-inputs/incomplete (1); operational/integrity errors use 2. Historical inspection returns no captured text or current-source revalidation and never renews approval. See [run receipts](RUN_RECEIPTS.md), including partial persistence and audit failure semantics.

`review-application` returns metadata and an exact current `fingerprint` without writes. `apply-stage` and `rollback-application` return journal inspection after a normal completion (0); handled failures use 2 and can retain partially changed source, an owned pending marker or a completion record. Always inspect retained state. `inspect-application` uses `applied`/`rolled-back` (0), `pending`/`conflicted` (1), unsafe/malformed/changing evidence (2); returns per-file metadata/states and a fresh `rollback_fingerprint`, never text. See [application state and limits](APPLICATION.md).

Source 0.3.0a16 adds [owned fixed-check supervision](SUPERVISION.md): a gated launcher, POSIX group/PID anchor or Windows kill-on-close job, native completion/termination checks and continuously drained bounded stream tails. Timeout includes ordinary owned descendants and pipe retention; uncertain cleanup retains run.lock and incomplete intent without a final receipt. Runner 5/lock 3 require fresh version-bound approval. This covers cooperating same-group POSIX descendants/job members, not deliberate group/session escapes, hostile-code isolation or automatic stale recovery. The guide defines normal, timeout, cancellation and abrupt-parent-death limits.
