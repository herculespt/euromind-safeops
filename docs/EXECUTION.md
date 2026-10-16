# Execution policy and upgrade compatibility

<!-- safeops-version: 0.3.0a19 -->

[Português (Portugal)](pt-PT/EXECUTION.md)

Current source version: **0.3.0a19**, alpha prerelease. This document describes
implemented behavior; see [status](STATUS.md) for exclusions and publication state.

## Configuration

The initialized `.safeops/config.json` keeps schema 1 by default:

```json
{"schema": 1, "checks": ["compile", "unit-tests"]}
```

Only those two keys are accepted. `schema` must be integer 1, not a boolean,
float or string. `checks` must be a nonempty list of unique strings from
`compile` and `unit-tests`; order is preserved. Unknown fields, unsupported
names and malformed types produce a controlled error. A configuration with
only `compile` remains valid and makes no claim that unit tests ran.

Stored JSON objects are read as UTF-8 (an optional UTF-8 BOM is accepted), with
a 256,000-byte limit. Duplicate object keys, non-finite numbers including
overflow, non-UTF-8 encoding and non-object top-level values are rejected.
Excessive nesting reported by the JSON decoder produces a controlled error.
Optional schema 2 adds explicit [check directory targets](TARGETS.md), while
schema 1 remains supported. Configuration does not support plugins, arbitrary
commands or OS-enforced filesystem isolation. Plan scope paths are advisory, not enforced isolation boundaries.

Schema 2 accepts exactly `schema`, `checks` and `targets`. The target mapping
names exactly the enabled checks. Selected directory trees are validated without
imports before approval/run, with the fixed child rechecking before execution.
See the [target guide](TARGETS.md) for the JSON example, limits and compatibility.

## Output and CI reporting

Source 0.3.0a5 introduced optional global `--json` envelopes and aggregate CI summaries;
see the [output contract](OUTPUT.md). Presentation does not change approval
authority. Config schemas 1/2, plan schema 1 and approval schema 2 are retained;
current source uses runner protocol 5 and lock protocol 3. The package-version
change requires a fresh plan/approval while preserving history. Invalid CLI arguments now return 2 from Python `main`; the
subprocess status remains 2. Help/version remain text actions.

## Advisory path preflight

Source 0.3.0a3 validates and normalizes declared paths before provider access and
plan persistence, and rechecks them before approval/run. Historical plans remain
reviewable; unsafe scopes cannot authorize checks. `--path` does not narrow the
workspace digest or the fixed check targets. See the [scope policy](SCOPE.md) for
portable syntax, future files, link handling and residual race limitations.

## Approval contract

Plans remain schema 1. New approvals use schema 2 and bind:

- Plan ID/fingerprint, source-tree snapshot and validated configuration hash.
- Installed SafeOps version, runner protocol version, native-lock protocol, fixed command table/target adapter and UTF-8 stream policy, through the execution-contract digest.
- With config schema 2, an additional `targets_digest` of every selected regular file, including ordinary snapshot exclusions.

`doctor` reports the current version, configuration schema, actual check targets,
approval schema and contract digest. Its
recursive filename count is diagnostic only; it does not import test code or
prove that a runnable suite exists.

On upgrade from 0.2.0, keep `.safeops` and its history. Valid schema-1 config and
stored plans remain readable, but legacy approvals cannot authorize execution.
Review the current source, create a new plan, review it and approve the new ID
explicitly. Old approval files are not modified, deleted or automatically
converted. Do not edit an old record to bypass this requirement.

Upgrading from 0.3.0a1 to 0.3.0a2 also requires a new plan and approval because
the existing execution contract binds the package version. Configuration/plan
schema 1 and approval schema 2 do not change in this provider-validation update.

Upgrading from 0.3.0a2 to 0.3.0a3 also requires a fresh plan and approval under
the version-bound contract. Configuration/plan schema 1 and approval schema 2
remain unchanged. Earlier unsupported path forms now fail before provider access;
old records can still be reviewed without rewriting them.

Upgrading to 0.3.0a4 requires a fresh plan/approval (runner protocol 2). Schema-1
configuration is retained; opting into schema 2 requires `targets_digest` in the
approval. Plan schema 1 and approval schema 2 remain supported. Generated caches
in selected trees can invalidate later runs; inspect and reapprove with a new plan.

Upgrading to 0.3.0a6 requires a fresh plan/approval: runner protocol 3 adds native
local locking and lock protocol 1. Existing PID/unknown run markers stay blocking;
use [diagnostics and explicit archival recovery](LOCKING.md) only after verifying
parent and child checks stopped. Never remove the persistent guard.

Source 0.3.0a7 added optional maintainer-only [JUnit reporting](REPORTING.md),
retaining runner protocol 3 and lock protocol 1. The version binding still requires
a new reviewed plan/approval. Approved checks do not create JUnit reports.

Source 0.3.0a8 added a maintainer [coverage gate](COVERAGE.md), retaining these
schemas/protocols and the package-version approval binding. Creating or merging
a GitHub PR does not create a SafeOps execution approval. For an authorized check
run, create a plan against the final unchanged tree, review it, explicitly approve
that new ID with a reason, and run its fixed checks. Never auto-renew old records.

Changes to the package version or fixed command contract invalidate an existing
approval even if workspace files and configuration are unchanged. Maintainers
must bump the package/runner protocol when behavior changes. These are local
integrity records, not signatures or protection against a malicious local actor.

## Fixed checks and results

| Check | Config schema 1 | Config schema 2 |
|---|---|---|
| `compile` | Fixed `compileall -q src tests`; requires both directories | Fixed internal adapter compiles selected `.py` sources in memory, without imports/bytecode writes |
| `unit-tests` | Internal unittest runner under `tests/`, pattern `test*.py` | Same runner under one explicitly selected directory |

Discovery happens only inside the approved child process. Importable nested test
packages with `__init__.py` are supported. Empty discovery, zero executed cases
and all-skipped suites fail. A mixed suite with skipped and successful executed
cases may pass; expected failures retain unittest's normal semantics. Import
errors, failing tests, unexpected exits and timeouts fail the check. Ordinary
`SystemExit(0)` during discovery is rejected rather than counted as success.

The internal runner returns 0 on successful non-skipped execution, 1 for test
failure and 2 for unusable discovery/execution. `safeops run` reports a failed
check with CLI exit 1; invalid configuration or stale approval uses CLI exit 2.
Timeouts retain the result exit code -1 and the 1–300-second per-check limit.
A persistent native guard covers approval/config/snapshot validation and checks.
Normal completion/error removes only the unchanged owned marker; abrupt parent
death releases the native lock but retains the blocking marker. The [lock guide](LOCKING.md)
describes diagnostics, explicit archival recovery, legacy state and filesystem
limits. Check failure is recorded in the local audit log. Returned UTF-8 stdout/stderr are truncated to their last 12,000 characters each; capture now drains bounded 65,536-byte tails in private readers rather than retaining complete output in memory. Receipts exclude that output.

Tests and discovery hooks execute trusted Python and may mutate files, terminate
the interpreter with lower-level APIs, or manipulate results. This adapter does
not verify assertions, coverage or hostile-code behavior and is not a sandbox.

## Design and references

- [ADR 0002 — versioned fixed-check contract](adr/0002-versioned-check-contract.md)
- [Python unittest documentation](https://docs.python.org/3.11/library/unittest.html)
- [Python JSON documentation](https://docs.python.org/3.11/library/json.html)
- [CI and distribution contract](CI.md)

Source 0.3.0a9 introduced [local candidate previews](PREVIEW.md). Preview requires no initialized workspace and cannot approve/apply/run a candidate. Execution still needs a fresh reviewed plan and explicit approval bound to this installed version; no schema migration or automatic renewal occurs.

## Local proposals and version compatibility

Source 0.3.0a10 introduced [persisted local proposals](PROPOSALS.md). Proposal schema 1 is separate from execution approval. `propose` requires exact explicit plan file paths; this does not restrict fixed-check execution. `review-proposal` rechecks bindings and returns diffs without application, approval or checks. Preserve old records; this version still requires a fresh reviewed plan and explicit execution approval. Proposal records have a separate 260,096-byte read limit; existing plan/configuration/approval reads retain 256,000 bytes.

## Checking a staged copy

Source 0.3.0a11 adds [local staging copies](STAGING.md), requiring exact proposal-fingerprint confirmation. No approval or original SafeOps state is inherited. Inspect copied code and initialize/plan/review/approve separately before running fixed checks in that copy. Copies and receipts do not grant execution permission or OS isolation. [Explicit original application](APPLICATION.md) is now implemented separately.

Source 0.3.0a12 adds read-only `inspect-stage` for retained schema-1 copies.
Matching/changed/incomplete observations never renew approval, import project
code or execute checks. Old records remain inspectable across version/source
changes with explicit historical-only context. Execution still requires a fresh
reviewed plan and version-bound approval; see [staging inspection](STAGING.md).

Source 0.3.0a13 adds read-only [current original-context review](STAGE_REVIEW.md). `review-stage` requires a matching stage and revalidates original/plan/base/configuration/target/version/contract bindings. `current` is a point-in-time observation, never execution/application approval. No approval is created or renewed. Existing version binding requires a fresh plan and explicit approval after upgrading.

Source 0.3.0a14 adds [approved-check receipts](RUN_RECEIPTS.md). Runner protocol 4 binds receipt schema 1 and suppresses automatic import bytecode in fixed children. Bounded context observations run before execution and after each completed check; changes/unavailable context stop subsequent checks and prevent passed status. Final receipt follows guard cleanup and audit; operational failures retain incomplete evidence. `run` adds run ID/fingerprint/reasons; `inspect-run` reads historical metadata without current-source revalidation or approval. Compile-only receipts make no unit-test claim. Fresh plan/approval is required after upgrade.

Source 0.3.0a15 adds [explicit reviewed application and conservative rollback](APPLICATION.md). Both staged fixed checks must pass with unchanged current bindings and the same configuration as the original; exact fresh human confirmation and native guards precede private backup/journal preparation and source writes. Any retained application marker blocks new approved runs/applications. Read-only inspection and separately confirmed rollback preserve evidence and refuse observed human edits. No multi-file transaction, power-loss guarantee, Git operation, provider request or OS isolation is added. That milestone used runner 4/lock 2. Fresh version-bound execution approval is required.

Source 0.3.0a16 adds [owned fixed-check supervision](SUPERVISION.md): a gated launcher, POSIX group/PID anchor or Windows kill-on-close job, native completion/termination checks and continuously drained bounded stream tails. Timeout includes ordinary owned descendants and pipe retention; uncertain cleanup retains run.lock and incomplete intent without a final receipt. Runner 5/lock 3 require fresh version-bound approval. This covers cooperating same-group POSIX descendants/job members, not deliberate group/session escapes, hostile-code isolation or automatic stale recovery. The guide defines normal, timeout, cancellation and abrupt-parent-death limits.

Source 0.3.0a19 waits for final zero Windows job accounting within the same three-second cleanup budget used for launcher exit, EOF and failure cleanup. A transitional positive count cannot turn a completed failed check into an immediate operational error; persistent/unavailable confirmation remains fail-closed with retained state. Fixed-phase diagnostics exclude native exception text. Runner 5/lock 3 and schemas remain; the updated version/cleanup-policy binding requires fresh reviewed plans/proposals/approvals.
