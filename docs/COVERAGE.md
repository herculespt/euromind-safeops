# Measured CI coverage — 0.3.0a18

<!-- safeops-version: 0.3.0a18 -->

[Português (Portugal)](pt-PT/COVERAGE.md)

The existing Ubuntu/Python 3.12 matrix job measures package statements and
branches using development-only `coverage==7.16.2` from `requirements-ci.txt`.
The runtime package still has no third-party dependencies. Eight other matrix
jobs and both installed-wheel jobs retain uninstrumented full-suite execution.
There are still twelve jobs including the required `quality-gate`.

## Measurement and gate

`pyproject.toml` selects the complete `euromind_safeops` package, branch
measurement, subprocess patching and parallel data files. No module omission,
custom line exclusion or ignored source error is configured. Before testing,
a separate parent script invokes the CLI in a real child process. Its report
must contain executed `__main__.py` lines. The probe data is then erased, so it
cannot inflate the full-suite result. Data/report paths are under `runner.temp`.

After a successful full suite, CI combines child data, writes JSON and Cobertura
XML, and enforces **90% combined coverage**. The percentage is
`(covered statements + covered branch destinations) / (all statements + all
branch destinations) * 100`, not a minimum of 90% for each metric or module.
CI also requires every package `.py` module, branch data, zero excluded lines and
matching JSON/XML counts. Missing/invalid data, report-write errors, failed tests
or a below-threshold measurement fail the matrix job and therefore the gate.
Only aggregate counts/percentage enter the Markdown job summary.

The pre-change Linux/Python 3.12 baseline on source 0.3.0a7
(`8c7607335f966a005e3e9f438eed26bdd98be51d`, measured 2026-10-15) was:

| Metric | Observed |
|---|---:|
| Statements | 958 / 1,018 (94.11%) |
| Branch destinations | 311 / 362 (85.91%) |
| Combined | 91.96% |
| Excluded lines | 0 |
| Package modules | 14 |

These are dated observations, not a promise of identical future totals. Current
PR/main evidence belongs in the tracking issue and workflow logs. Review gaps
before changing a threshold; do not lower it to hide a regression.

## Reproduce locally — trusted environment

Prepare the dedicated supported environment through [locked tooling](TOOLING.md), then install the editable project with `python -m pip --isolated install --no-index --no-deps --no-build-isolation -e .`. Do not use the Linux wheel lock on other platforms.
Use an existing temporary directory **outside the checkout** for data/reports.
For Bash, after setting `SAFEOPS_REPORT_DIR` to that directory:

```bash
export COVERAGE_FILE="$SAFEOPS_REPORT_DIR/safeops-coverage"
export COVERAGE_RCFILE="$PWD/pyproject.toml"
python -m coverage erase
python -m coverage run -m euromind_safeops.ci_runner --tests tests --summary "$SAFEOPS_REPORT_DIR/summary.md" --junit "$SAFEOPS_REPORT_DIR/junit.xml"
python -m coverage combine --quiet
python -m coverage json -o "$SAFEOPS_REPORT_DIR/coverage.json"
python -m coverage xml -o "$SAFEOPS_REPORT_DIR/coverage.xml"
python -m coverage report
```

The exact child probe and cross-format checks are in [CI](../.github/workflows/ci.yml).
Coverage erase removes only that selected measurement's data; use a dedicated
location. Git ignore rules alone do not exempt generated files from SafeOps
workspace snapshots. Create/review/approve a fresh plan only after final source
changes; ordinary approved checks do not install or start coverage themselves.

## Limits and upstream references

Coverage records execution, not useful assertions, security or isolation. This
profile does not establish coverage on Windows/macOS/other Python versions,
live provider behavior or installed distributions. Abrupt death, `os._exit`,
disabled hooks and changed subprocess environments can lose measurements. The
subprocess patch is intentionally limited to the development profile; it does
not replace the ordinary uninstrumented platform tests.

JSON/XML and raw data can contain filesystem paths, source line numbers and
timestamps. They are local runner files, not the synthetic privacy-minimised
[JUnit report](REPORTING.md). No report upload, signing or publication is
configured here. Broader profiles and reviewed report uploads remain planned.

- [Upstream coverage configuration](https://coverage.readthedocs.io/en/7.16.2/config.html)
- [Upstream process measurement](https://coverage.readthedocs.io/en/7.16.2/subprocess.html)
- [Coverage.py package/version](https://pypi.org/project/coverage/7.16.2/)
- [CI contract](CI.md) and [execution approvals](EXECUTION.md)

Report basenames are `package-coverage.json` and `package-coverage.xml` in CI,
separate from the `safeops-coverage` data prefix. This prevents subprocess patch
automatic combination from treating reports as parallel coverage databases.
