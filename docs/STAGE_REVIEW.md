# Current original-context review — 0.3.0a16

<!-- safeops-version: 0.3.0a16 -->

[Português (Portugal)](pt-PT/STAGE_REVIEW.md)

```bash
safeops --json --root ORIGINAL_PROJECT review-stage STAGE_ID
```

Use the exact 12-character lowercase stage ID under the original project's
`.safeops/stages`. This read-only review requires the retained proposal, intent,
receipt, bound plan and current configuration. It first performs the strict
[historical inspection](STAGING.md). A matching copy is necessary before the
original context is reviewed. No execution approval is required or created.

| Result `status` | Exit | Meaning |
|---|---:|---|
| `current` | 0 | Matching copy and all reviewed original-context bindings match |
| `stale` | 1 | Matching copy, valid readable evidence, but one or more original-context bindings differ |
| `incompatible` | 1 | Valid historical inspection reports changed/incomplete copy; original context is not reviewed |
| Handled policy/access/integrity/budget/concurrency error | 2 | Sanitized fixed error, `data: null`; retain all existing state |

`current` and `stale` include `source_context: "revalidated"`, stage/proposal
identifiers, proposal/receipt fingerprints, recorded version, `version_matches`,
recorded/observed original digests and boolean `checks`. These checks are:

- `plan`: integrity-valid non-critical plan still matches the proposal's plan
  fingerprint, recorded snapshot and exact candidate path set.
- `source`: current original snapshot matches the proposal's recorded digest.
- `candidate_bases`: every exact original candidate path still has its base hash.
- `configuration`: validated schema-1/2 configuration matches its recorded digest.
- `selected_targets`: schema-2 selected-file digest matches; schema 1 uses `null`.
- `version` and `execution_contract`: proposal bindings match the installed
  package version and fixed execution contract, including runner/lock protocols.

`reasons` contains fixed codes for false checks, in the order above:
`plan-changed`, `source-changed`, `candidate-bases-changed`,
`configuration-changed`, `selected-targets-changed`, `version-changed`,
`execution-contract-changed`. A changed/incomplete copy returns
`source_context: "not-reviewed"`, `stage_status` and `stage-not-matching`, without
claiming original revalidation. Unsafe or invalid configuration/targets/plan are
errors, rather than a valid stale observation. No file text, diffs, task/advice,
approval reasons or raw OS errors enter this result. Hashes and IDs can still be
sensitive.

Two complete original observations must agree. Each validates control files,
checks target selection before/after reading, hashes the original and rereads
control evidence/parent identities. A final historical inspection must equal the
initial one. The review writes no file, audit event, approval or receipt; invokes
no provider, subprocess or project code; and performs no persistence, cleanup,
rollback, Git operation or application to either workspace.

## Snapshot scope and limits

Original hashing preserves `tree_digest` ordering (sorted regular files before
sorted recursive directories) and exact generated-directory exclusions. Unlike
the filtered staging copy, the original snapshot **includes environment files**
and ordinary files named `.git`, `build`, etc.; their bytes are hashed locally and
never returned. Only actual directories with exact `SKIP_DIRS` names are pruned.
Included links/reparse points, nonregular or multiply linked files, ambiguous
Unicode/control names and case-colliding file paths fail. Excluded directory
contents are not read; links at excluded directory names are rejected too.
Unreadable entries fail instead of silently disappearing.

Each original scan allows 5,000 regular files, 12,000,000 bytes per file,
64,000,000 bytes total, 10,000 encountered entries and 64 directory levels below
the root. Names must be UTF-8 NFC without control characters. Empty directories
and file metadata are not part of the digest. Plan/config reads are each capped
at 256,000 bytes; intent/receipt/proposal retain their existing
4,096/1,000,000/260,096-byte limits and strict JSON parsing.

Schema-2 target metadata validation retains its 5,000-entry budget per check;
all selected regular files, including generated/environment files selected by
configuration, are then hashed with the same 5,000-file/12 MB-per-file/64 MB-total
budgets and safe ancestor checks. This matches the existing approval target
digest, while rejecting unsafe/unreadable/oversized input. No target code is
imported or run. Source and target budgets are independent.

## Meaning and compatibility

This is a point-in-time compatibility observation of mutable, unkeyed local
records. It does not authenticate provenance, prove passing tests, freeze the
filesystem, or eliminate every concurrent race. No OS lock or isolation is added.
An original can change immediately after review. A hostile local writer can
rewrite every record and fingerprint. `current` grants no execution/application
authority and never renews an existing approval.

Historical schema-1 stages remain independently inspectable after upgrades.
Reviewing an older stage with a newer installed version reports stale version
and/or execution-contract bindings when its other evidence is still valid.
Preserve that history; create a fresh reviewed plan/proposal and separate staged
copy if current bindings are needed. Running trusted staged checks still requires
initialization, a fresh plan and explicit execution approval in that copy.
[Explicit original application and rollback](APPLICATION.md) are implemented separately. Git worktrees, OS isolation and authenticated SafeOps provenance remain planned. Public GitHub/PyPI alpha remains 0.3.0a8.

[Approved-check receipts](RUN_RECEIPTS.md) are now implemented separately. This compatibility command neither runs tests nor consumes a passed receipt as application authority. [Original application/rollback](APPLICATION.md) require their own exact current confirmation; historical run evidence does not replace current context review.
