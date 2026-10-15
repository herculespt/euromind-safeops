# Execution policy and upgrade compatibility

<!-- safeops-version: 0.3.0a2 -->

[Português (Portugal)](pt-PT/EXECUTION.md)

Current source version: **0.3.0a2**, alpha prerelease. This document describes
implemented behavior; see [status](STATUS.md) for exclusions and publication state.

## Configuration

The initialized `.safeops/config.json` keeps schema 1:

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
Configuration does not support plugins, arbitrary commands or a filesystem
allowlist. Plan scope paths are advisory, not enforced isolation boundaries.

## Approval contract

Plans remain schema 1. New approvals use schema 2 and bind:

- Plan ID/fingerprint, source-tree snapshot and validated configuration hash.
- Installed SafeOps version, runner protocol version, fixed command table and UTF-8 stream policy, through the execution-contract digest.

`doctor` reports the current version, approval schema and contract digest. Its
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

Changes to the package version or fixed command contract invalidate an existing
approval even if workspace files and configuration are unchanged. Maintainers
must bump the package/runner protocol when behavior changes. These are local
integrity records, not signatures or protection against a malicious local actor.

## Fixed checks and results

| Check | Implemented behavior |
|---|---|
| `compile` | Fixed Python `compileall -q src tests`; requires both directories |
| `unit-tests` | Fixed internal Python module using unittest discovery under `tests/`, pattern `test*.py` |

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
The exclusive run lock is released on controlled completion or error; a process
crash may still require manual recovery. Check failure is recorded in the local
audit log. UTF-8 stdout/stderr capture remains bounded in the returned result.

Tests and discovery hooks execute trusted Python and may mutate files, terminate
the interpreter with lower-level APIs, or manipulate results. This adapter does
not verify assertions, coverage or hostile-code behavior and is not a sandbox.

## Design and references

- [ADR 0002 — versioned fixed-check contract](adr/0002-versioned-check-contract.md)
- [Python unittest documentation](https://docs.python.org/3.11/library/unittest.html)
- [Python JSON documentation](https://docs.python.org/3.11/library/json.html)
- [CI and distribution contract](CI.md)
