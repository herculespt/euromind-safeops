# Quickstart

Requires Python 3.11+, Git optional, a trusted source tree with `src/` and `tests/test*.py`.

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

`approve` rejects critical risk plans; `run` aborts if source files or configuration have changed since planning. To update code, create a **new plan** and approval. This release does not alter project source files itself.

To inspect what may be committed:

```bash
safeops --root . scan
# Also use git status, git diff, and an independent secrets scanner.
```

## Windows notes

Open PowerShell in the project directory. Replace `python` with `py -3` if required, and use the exact 12-character plan ID shown on screen. Python module execution and the built-in file paths are cross-platform. On Windows, use `\` or `/` in `--root` as appropriate.

## Troubleshooting

- `Workspace not initialized`: run `safeops --root PATH init`.
- `Workspace changed since planning`: regenerate the plan and approval.
- `No test*.py files`: provide genuine `unittest` tests; an empty suite must not pass silently.
- `Critical-risk plans cannot be approved`: intentionally unsupported; use your organization's external review/release process.
- `run.lock` exists after a crash: confirm no check process is running before manually removing the lock.
