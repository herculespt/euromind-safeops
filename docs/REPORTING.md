# Local JUnit reporting — 0.3.0a11

<!-- safeops-version: 0.3.0a11 -->

[Português (Portugal)](pt-PT/REPORTING.md)

The maintainer CI adapter can write a minimal JUnit-style XML report using only
the standard library. This is a local reporting feature, separate from the
approved `safeops run` checks. Only run trusted Python tests.

```bash
python -m euromind_safeops.ci_runner --tests tests --summary summary.md --junit results.xml
```

`--summary` or `GITHUB_STEP_SUMMARY` remains required. `--junit` is optional and
has no environment default. Its parent directory must already exist. The selected
XML file is replaced, not appended: a temporary sibling is written, flushed and
atomically replaced. Normal handled write failures clean up that temporary file;
process termination may leave it. Existing XML is preserved if replacement fails.
Summary and XML destinations must differ; detected path/hard-link aliases are
rejected before discovery. These are trusted operator-selected paths, not a
filesystem access policy or protection against concurrent path replacement.

## Report contract — schema 1

One `testsuites` root contains one `testsuite` named `safeops-unittest`. Both have
`tests`, `failures`, `errors` and `skipped` counts derived from emitted cases.
Suite properties contain `safeops_version`, `report_schema` (`1`), discovery/
execution/completed `phase` and `check_exit_code`. Cases use the fixed classname
`safeops.unittest` and sequential names `case-1`, `case-2`, etc. They are numbered
outcome events, not stable test identities or source locations. No durations,
timestamps, hostnames or custom properties are exported. This minimal dialect
has no vendor-specific consumer certification.

| Observed result | XML representation |
|---|---|
| Successful test | Case with no result child |
| Assertion failure / test error | `failure type="failure"` / `error type="error"` |
| Skipped test or fixture | `skipped type="skipped"` |
| Expected failure | `skipped type="expected-failure"` |
| Unexpected success | `failure type="unexpected-success"` |
| Failed/errored subtest | One failure/error case per reported unsuccessful subtest |
| Passing subtests | No separate cases; unittest reports the successful parent |
| Fixture setup/teardown error | Error case, even when no method ran |
| Check exit code 2 | Additional `error type="runner-error"` case |

Multiple subtest failures, fixture events and runner errors mean XML totals may
differ from unittest's method-level run/discovery counts in the Markdown summary.
Expected failures are skipped in XML but retain their separate summary count.
Empty, wholly skipped, unusable or handled interrupted checks cannot appear as a
successful empty XML suite. Previously observed outcomes survive handled execution
interruptions; summary counters can be incomplete and the phase identifies this.

## Exit status, privacy and CI

Check exit codes remain 0 (usable successful suite), 1 (test failure) and 2
(unusable/incomplete suite). XML records that check result. Either XML or summary
write failure makes the adapter exit 2; XML can therefore describe passed tests
even when the adapter failed to write its summary. A failed XML write is also
recorded in the summary when that destination works. Never use XML alone as the
integration gate or assume an existing file came from the latest failed attempt.
Usage errors and unhandled interpreter/process termination may produce no report.

Only fixed labels, version and numeric metadata enter XML. Test names, subtest
parameters, skip/failure messages, exceptions, tracebacks, stdout/stderr and
environment variables are excluded. Tests still produce ordinary console logs,
which can contain sensitive data. Synthetic cases deliberately require consulting
those logs to locate a failure. This does not sanitize logs or isolate malicious
tests, which can modify their own process and files.

The nine matrix and two installed-wheel jobs generate XML under `runner.temp`
and parse it to verify counts, version and successful completed status. Reports
stay on that runner; no upload Action, package inclusion or report publication is
configured. `quality-gate` remains required. [Measured coverage](COVERAGE.md) is
implemented for Linux/Python 3.12; broader profiles and reviewed artifact
publication remain planned. No provider request is involved.

See [CI](CI.md), [structured output](OUTPUT.md), [execution compatibility](EXECUTION.md)
and [implementation status](STATUS.md).
