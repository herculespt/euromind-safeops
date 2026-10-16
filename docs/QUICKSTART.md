# Quickstart

<!-- safeops-version: 0.3.0a9 -->

Current source version: **0.3.0a9**, alpha prerelease. Requires Python 3.11+, Git optional, and a trusted source tree. The default schema-1 checks require `src/` and a nonempty unittest suite under `tests/`; optional [schema-2 targets](TARGETS.md) select other directories. Nested test packages need `__init__.py`.

```bash
git clone https://github.com/herculespt/euromind-safeops.git
cd euromind-safeops
python -m pip install -e .
python -m unittest discover -s tests -v
safeops --root examples/demo_project init
safeops --root examples/demo_project doctor
safeops --root examples/demo_project plan "Improve demo documentation"
```

The public repository contains the alpha source. For downloaded source archives, unpack the directory and run the install commands there.

The `plan` command prints an `id`. Use that ID:

```bash
safeops --root examples/demo_project review YOUR_PLAN_ID
safeops --root examples/demo_project approve YOUR_PLAN_ID --confirm YOUR_PLAN_ID --reason "I reviewed the local demo checks"
safeops --root examples/demo_project run YOUR_PLAN_ID
```

`approve` rejects critical risk plans; `run` aborts if the source, configuration or versioned execution contract has changed. To update code or upgrade SafeOps, review the current source, create a **new plan** and approval. Old approval files are preserved but are not migrated or reused. Valid configuration schema 1 remains supported; see [execution policy](EXECUTION.md). This source version does not alter project source files itself.

To inspect what may be committed:

```bash
safeops --root . scan
# Also use git status, git diff, and an independent secrets scanner.
```

## Windows notes

Open PowerShell in the project directory. Replace `python` with `py -3` if required, and use the exact 12-character plan ID shown on screen. Python module execution and the built-in file paths are cross-platform. On Windows, use `\` or `/` in `--root` as appropriate.

`--path` uses portable forward-slash relative names, even in PowerShell, such as
`--path src/demo/calc.py`. It describes advisory scope and does not restrict the
fixed checks. See the [scope policy](SCOPE.md).

## Troubleshooting

- `Workspace not initialized`: run `safeops --root PATH init`.
- `Workspace changed since planning`: regenerate the plan and approval.
- `No tests discovered`: provide discoverable `test*.py` modules containing genuine unittest cases; nested directories need `__init__.py`.
- `No non-skipped tests executed`: empty or all-skipped execution is a failed check; inspect discovery and skip conditions.
- `Invalid config`: use exactly `schema` (integer 1) and a nonempty `checks` list of unique supported names. Unknown fields, duplicate JSON keys and non-finite numbers are rejected.
- `Missing or stale approval`: review the current version and source, then create a new plan and approval; do not modify old approval files to bypass the check.
- `Critical-risk plans cannot be approved`: intentionally unsupported; use your organization's external review/release process.
- A retained `run.lock` blocks after interruption: inspect `doctor`, independently verify parent/child checks stopped, then use [explicit archival recovery](LOCKING.md). Never delete `run.guard`.

`doctor` counts candidate test filenames recursively without importing them. It does not prove that tests will be discovered or executed; only an approved run does discovery.

For automation, use global `--json` before the command; see the
[structured output and CI summary contract](OUTPUT.md). Default output remains
available. This does not grant execution approval.

## Inspect a local candidate without writing files

Use `safeops --root PROJECT --json preview CANDIDATE.json` for a manually supplied
text replacement candidate. No initialization or execution approval is required.
See [format, example and limits](PREVIEW.md); success is a preview only.
