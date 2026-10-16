# Advisory scope paths — 0.3.0a12

<!-- safeops-version: 0.3.0a12 -->

[Português (Portugal)](pt-PT/SCOPE.md)

`plan --path` describes advisory scope. Source 0.3.0a3 validates it before
calling a provider and before saving a plan, then checks the stored declarations
again at approval and run. Invalid preflight produces CLI exit 2 without
contacting a provider or saving a plan. This also applies to offline planning.

## Accepted declarations

- Zero to twenty paths, relative to the explicitly selected workspace.
- Forward slashes on every platform: `src/demo/calc.py`, `docs/new.md`.
- UTF-8 names, regular files, directories and paths for files not created yet.
- `.` denotes the workspace root; an empty list omits advisory declarations.
- New plans normalize `./`, repeated slashes and trailing separators.
  Duplicate normalized declarations are rejected.

Initialize the public demo once, then create a plan:

```bash
safeops --root examples/demo_project init
safeops --root examples/demo_project plan "Review demo documentation" --path README.md
```

## Rejected declarations

- Absolute, drive-relative, UNC and parent-traversal paths, including `a/../b`.
- Backslashes, ASCII control characters and Windows-special punctuation
  (`:`, `<`, `>`, `"`, `|`, `?`, `*`), reserved device names and components ending
  in a space or period. `--root` still accepts normal platform path syntax.
- Internal/generated component names from the existing snapshot exclusions,
  matched without case sensitivity: `.git`, `.safeops`, `.venv`, `venv`,
  `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.tox`, `node_modules`, `dist`, `build`.
  Ordinary names such as `.safeops-guide.md` are not internal components.
- Existing links, broken symbolic links, Windows junctions or other reparse
  points in a declared path or its ancestors; nonregular objects such as pipes;
  non-directory ancestors and filesystem inspection errors.

Missing descendants are permitted after existing ancestors have been inspected.
The resolved path must stay below the selected root. The validator reads metadata,
not file contents, and does not import tests. Filesystem checks are repeated at
the lifecycle boundaries; they are not atomic with later provider access or execution.

## Compatibility and limits

Schema-1 configuration remains the default; optional schema 2 selects
[check directories](TARGETS.md). Plan schema 1 and approval schema 2 remain supported.
Updating to 0.3.0a4 invalidates old execution approvals through the version-bound contract;
keep history and create a fresh reviewed plan and explicit approval. Existing
plans remain available through read-only `review`, including records whose
paths no longer satisfy the current approval/run policy.

This is not a filesystem allowlist or sandbox. Snapshots remain workspace-wide;
schema-1 checks operate on `src` and `tests`, while optional config schema 2
selects [fixed-check directories](TARGETS.md), independently of `--path`. The
validator does not recursively police every descendant of a declared directory.
Existing snapshot exclusions remain, filesystem races are possible and trusted
test code can access other files or the network. An OS-enforced boundary on arbitrary reads/execution remains [planned](../ROADMAP.md).

Regression tests in `tests/test_scope.py` replace remote advice with offline
fixtures. Windows CI exercises a real junction; POSIX CI exercises a named pipe.
The dated live-provider records retain their original source version 0.3.0a2;
this change makes no additional billable request.

See [execution compatibility](EXECUTION.md), [status](STATUS.md),
[Python pathlib](https://docs.python.org/3.11/library/pathlib.html) and
[Microsoft path naming](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file).

[Local proposals](PROPOSALS.md) require each proposed file to exactly match an explicit plan `--path`; directory entries do not cover descendants. This proposal-only rule does not change the advisory scope or fixed-check targets described above.

[Staging copies](STAGING.md) copy the supported ordinary project snapshot with documented omissions. Exact proposal plan paths restrict replacement targets, not all files read/copied. Copies do not enforce an OS filesystem allowlist.
