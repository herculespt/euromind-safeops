# Local run locking and recovery — 0.3.0a20

<!-- safeops-version: 0.3.0a20 -->

[Português (Portugal)](pt-PT/LOCKING.md)

Runs use two cooperating mechanisms: a persistent native guard and an exclusive
owned marker. Neither is a sandbox or a distributed lock. Source 0.3.0a20 uses
runner protocol 5 and lock protocol 3 in the version-bound execution contract.
Config schemas 1/2, plan schema 1, approval schema 2 and output schema 1 remain.
Upgrading requires a fresh reviewed plan/approval; records are not migrated.

## Guard and marker

- `.safeops/run.guard` is a persistent empty regular file. POSIX uses nonblocking
  `fcntl.flock`; Windows uses nonblocking `msvcrt.locking` on byte zero, including
  beyond EOF. Unsupported/unavailable locking fails; there is no unprotected fallback.
- The guard descriptor is not inheritable. It remains open across approval/config
  and snapshot validation and fixed checks. Never delete or replace this file:
  contenders may already have descriptors referring to it.
- `.safeops/run.lock` is created exclusively after acquiring the guard. Its JSON
  schema 1 records PID, plan ID, random ownership token and UTC creation time.
  The guard is held until validation/checks and owned-marker cleanup finish.
- Normal completion/error removes only the unchanged owned marker after identity
  and exact-content checks. Changed/missing/unsafe markers cause an error. A
  cleanup error cannot produce a successful run audit entry. Marker initialization
  failure retains any partial marker for inspection.
- An abrupt parent death releases its native lock, but leaves the marker blocking
  later runs. Legacy PID-only, partial and unknown markers also remain blocking.
  No marker is automatically declared stale or removed on PID inspection.

Lock operations reject symbolic links, broken links, reparse points/junctions,
nonregular objects and hard-link aliases for guard/marker files, and linked state
or recovery directories. Marker inspection reads at most 4,096 bytes; oversized
or inaccessible state requires independent investigation. Checks repeat at operation
boundaries, not atomically against a malicious local owner changing the filesystem.

## Diagnostics

```bash
safeops --json --root examples/demo_project doctor
```

Use an initialized workspace. `data.run_lock` reports `guard` (`absent`, `free`
or `busy`), marker presence, SHA-256 `marker_fingerprint`, format (`record-v1`,
`legacy-pid`, `unrecognized`), recognized PID/plan ID and a limitation notice.
Unsafe state/unsupported lock operations return a controlled error.

The diagnostic creates/removes no files and does not print raw marker contents.
It briefly probes an existing guard without waiting, then releases it. Results
are point-in-time observations: `busy` means a native operation may hold the
guard; `free` or a missing/dead/reused PID never proves child checks stopped.

## Explicit recovery

1. Independently inspect the workspace's parent **and child** check processes.
   Stop/finish them and verify no checks remain. Never acknowledge this while
   they are running; this command does not terminate processes or infer liveness.
2. Run `doctor` again and review the exact current marker fingerprint and format.
3. Only after verification, replace `MARKER_SHA256` below with that 64-character
   fingerprint, supply a meaningful reason and acknowledge the process check:

```bash
safeops --json --root examples/demo_project recover-lock --confirm MARKER_SHA256 --reason "Verified interrupted parent and child checks have stopped" --confirm-no-running-checks
```

The command requires all confirmations, a matching fingerprint and a free native
guard. It rechecks file identity/content before moving the original bytes to
`.safeops/recovered-locks/<random-id>/run.lock`. A `receipt.json` preserves the
requested action, fingerprint/format, reason, acknowledgement and UTC time.
An audit event links the recovery directory ID. Existing plans/approvals are
not modified; no check executes and no execution approval is granted. Inspect
interrupted changes and prefer a fresh reviewed plan/approval before running.

The result includes relative archive/receipt paths. Archive/receipt/audit writes
are not one transaction: failure before archival retains the current marker;
failure afterwards can return exit 2 with the original already archived. A
receipt without an archived marker records an attempted recovery. Inspect
`doctor`, archive and audit before retrying; do not blindly remove state files.

## Limits and validation

This is cooperative local locking tested on the supported CI filesystems, not
a lease across hosts, a network-filesystem guarantee or protection from an owner
who can rewrite `.safeops`. Ordinary source/selected-target integrity checks and
trusted-test restrictions remain. [Owned process supervision](SUPERVISION.md) now covers cooperative groups/jobs and bounded cleanup. Deliberate POSIX escapes, hostile-code containment and automatic stale recovery remain unsupported.
Legacy versions do not understand the native guard: their markers remain blocking
and require the same independent process verification before recovery.

Real subprocess tests cover two competing approved runs, busy recovery rejection,
normal release and abrupt parent death with a retained marker. Additional cases
cover changed/unsafe markers, hard links, receipts/audit failures and unchanged
plan/approval history. Windows CI exercises a real state-directory junction;
POSIX CI exercises a named pipe. All fixtures are temporary; no real project lock
is recovered and no provider request is made by these tests.

See [execution](EXECUTION.md), [output](OUTPUT.md), [status](STATUS.md) and
[CI](CI.md). Primary API references: [Python flock](https://docs.python.org/3.11/library/fcntl.html#fcntl.flock)
and [Python msvcrt locking](https://docs.python.org/3.11/library/msvcrt.html#msvcrt.locking).

Runner protocol 5 uses native-lock protocol 3. The guard now also covers bounded before/after input observation and run-intent allocation. Final [run receipt](RUN_RECEIPTS.md) is written only after owned-marker cleanup/guard release and audit append; a cleanup failure leaves intent without a terminal receipt. Finalization outside the guard does not freeze the observed source or block a later run. Existing recovery never finalizes interrupted receipts or grants approval.

Source 0.3.0a15 adds [explicit reviewed application and conservative rollback](APPLICATION.md). Both staged fixed checks must pass with unchanged current bindings and the same configuration as the original; exact fresh human confirmation and native guards precede private backup/journal preparation and source writes. Any retained application marker blocks new approved runs/applications. Read-only inspection and separately confirmed rollback preserve evidence and refuse observed human edits. No multi-file transaction, power-loss guarantee, Git operation, provider request or OS isolation is added. That milestone used runner 4/lock 2. Fresh version-bound execution approval is required.

`doctor.data.run_lock.application_pending` reports presence of any application marker entry without reading/removing it. Native-lock protocol 3 refuses new runs before allocating `run.lock` whenever that entry exists. Application holds original and staged native guards; rollback holds the original guard. Retained run markers also block either writer. `recover-lock` never clears application evidence. The [application guide](APPLICATION.md) defines owned-marker release and manual recovery limits.

Source 0.3.0a16 adds [owned fixed-check supervision](SUPERVISION.md): a gated launcher, POSIX group/PID anchor or Windows kill-on-close job, native completion/termination checks and continuously drained bounded stream tails. Timeout includes ordinary owned descendants and pipe retention; uncertain cleanup retains run.lock and incomplete intent without a final receipt. Runner 5/lock 3 require fresh version-bound approval. This covers cooperating same-group POSIX descendants/job members, not deliberate group/session escapes, hostile-code isolation or automatic stale recovery. The guide defines normal, timeout, cancellation and abrupt-parent-death limits.

Source 0.3.0a20 waits for final zero Windows job accounting within the same three-second cleanup budget used for launcher exit, EOF and failure cleanup. A transitional positive count cannot turn a completed failed check into an immediate operational error; persistent/unavailable confirmation remains fail-closed with retained state. Fixed-phase diagnostics exclude native exception text. Runner 5/lock 3 and schemas remain; the updated version/cleanup-policy binding requires fresh reviewed plans/proposals/approvals.


## Optional Git staging boundary

[Git staging worktrees](GIT_STAGING.md) require separate exact confirmation and schema-2 stage evidence. Default copies retain schema 1. Git-stage inspection/current review/application preflight invoke fixed read-only installed Git commands to validate linkage/base/index; they never execute project code or grant approval. A regular `.git` metadata file is excluded from source digests and validated separately for Git stages. Registration alone uses the original native guard and preserves partial locked worktrees on failure. Shared Git metadata is not OS isolation; signed SafeOps provenance remains planned in #61. Existing explicit fresh staged approval/check/application/rollback gates remain.
