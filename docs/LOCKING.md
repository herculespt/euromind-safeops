# Local run locking and recovery — 0.3.0a12

<!-- safeops-version: 0.3.0a12 -->

[Português (Portugal)](pt-PT/LOCKING.md)

Runs use two cooperating mechanisms: a persistent native guard and an exclusive
owned marker. Neither is a sandbox or a distributed lock. Source 0.3.0a12 uses
runner protocol 3 and lock protocol 1 in the version-bound execution contract.
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
trusted-test restrictions remain. Timeouts concern the direct subprocess; process
tree supervision/termination and automatic stale recovery are not implemented.
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
