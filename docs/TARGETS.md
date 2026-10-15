# Fixed-check directory targets — 0.3.0a6

<!-- safeops-version: 0.3.0a6 -->

[Português (Portugal)](pt-PT/TARGETS.md)

Configuration schema 2 optionally selects the directories used by the fixed
checks. `init` still writes schema 1 with its existing `src`/`tests` behavior.
`plan --path` remains advisory and does not configure these targets.

## Explicit configuration

After initialization, edit the local `.safeops/config.json`, review the selected
code and configuration, then create/review/approve a fresh plan before running:

```json
{
  "schema": 2,
  "checks": ["compile", "unit-tests"],
  "targets": {
    "compile": ["src/demo", "tests/unit"],
    "unit-tests": ["tests/unit"]
  }
}
```

These directories must already exist in the selected workspace. This example
does not create them. The public demo can use `src` and `tests` instead.
`doctor` reports the configuration schema and actual check targets. Its test-file
count refers to the selected unittest root (zero if disabled), without importing
tests or proving a runnable suite exists.

- Exactly `schema`, `checks` and `targets` are accepted; schema must be integer 2.
- Check names/order follow the existing policy. `targets` must name exactly the
  enabled checks. A compile-only or unittest-only configuration is valid.
- Each target value is a nonempty list of at most twenty canonical portable
  relative directory names: forward slashes, no `./`, trailing/repeated slashes,
  `.`, traversal, drive syntax, reserved names or internal/generated root components.
  See [portable scope syntax](SCOPE.md); future paths accepted by advisory scope
  are not accepted as execution targets.
- Compile roots must not overlap, duplicate or alias by case. Unittest supports
  exactly one discovery root in this version. The same directory can be selected
  by both checks. UTF-8 directory names and nested roots are supported.

## What executes

The parent validates the configured trees without importing tests at approval
and run, and again before each check. The fixed child adapter repeats validation.
Every descendant is inspected: no generated/internal descendants are silently
excluded. Links, broken links, Windows junctions/reparse points, nonregular
objects and filesystem errors fail. The metadata limit is 5,000 child entries
per check, including directories; each selected regular file is at most
12,000,000 bytes. A smaller target can be chosen when a limit is exceeded.

`compile` reads and compiles all selected `.py` sources in memory, without
importing them or writing bytecode. No selected Python source is an error.
Generated directories inside a selected root are included. `unit-tests` uses
the existing child unittest runner with `test*.py` under the selected root;
importable nested packages need `__init__.py`. The root is discovery's import
base, preserving the existing adapter's semantics. Empty discovery, all-skipped
suites, errors and timeouts fail. No shell or model-supplied command is accepted.

## Integrity and limits

The ordinary workspace-wide digest remains required, with its existing generated
directory exclusions. An additional `targets_digest` in approval schema 2 binds
the paths and contents of **all selected regular files**, including resources
and generated files excluded from the ordinary snapshot. Changes outside the
targets still invalidate approval when covered by the workspace snapshot.
Changing configuration or SafeOps version also requires a fresh plan/approval.
History is retained; old approval records are not rewritten or migrated.

Tests may generate `__pycache__` or other files in selected trees. Those changes
can make the selected-file digest stale for a subsequent run; inspect them and
create a fresh plan/approval rather than editing an old approval.

This selects compile/discovery inputs. It does not restrict arbitrary reads,
imports, discovery hooks, writes, interpreter startup or network access. Tests
remain trusted code, and filesystem metadata/content checks are not atomic with
execution. An OS-enforced allowlist and hostile-code isolation remain planned.
No provider request is required by this feature or its offline regression tests.

See [execution compatibility](EXECUTION.md), [status](STATUS.md),
[trust model](TRUST_MODEL.md) and [CI validation](CI.md).
