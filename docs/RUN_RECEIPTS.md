# Approved-check receipts — 0.3.0a20

<!-- safeops-version: 0.3.0a20 -->

[Português (Portugal)](pt-PT/RUN_RECEIPTS.md)

`run PLAN_ID` still requires a non-critical reviewed plan and explicit valid
execution approval. It now allocates a random 12-character lowercase hexadecimal
run ID and records bounded metadata under `.safeops/runs/RUN_ID/`. IDs are
exclusive: collisions fail without overwriting or automatically retrying.

```bash
safeops --json --root PROJECT run PLAN_ID
safeops --json --root PROJECT inspect-run RUN_ID
```

Only `run` invokes the fixed checks. `inspect-run` reads retained evidence without
writing, importing project code, contacting providers, launching checks, appending
audit or granting approval. It does not require current config/plan/approval files
or current-original compatibility. Keep this evidence out of public Git.

## Lifecycle and failure semantics

1. Safely read the plan and scope, acquire the existing native guard/owned marker,
   and compare two bounded observations of control/source/selected inputs. Reject
   stale approval before allocating a run or starting a check.
2. Exclusively create `intent.json` before the first child. It records schema 1,
   run/plan IDs, UTC start time, SafeOps version, ordered enabled fixed checks,
   per-check timeout and start `bindings` plus canonical fingerprint.
3. After **each** completed check, compare two more context observations. Stop
   before the next check if it failed/timed out, context changed, or context could
   not safely be observed. A successful child return alone cannot establish an
   unchanged tested context.
4. After successful owned-marker cleanup/native-guard release, append the observed
   run status to the audit log. Only then exclusively write `receipt.json`.
   Finalization is outside the guard; hashes describe the observed check inputs,
   not a filesystem frozen until/after persistence. A new run can start meanwhile.
5. Initialization, child-start, lock-cleanup, audit or final-write failures return
   operational error 2 and retain evidence. No automatic retry, cleanup, receipt
   repair, rollback or approval renewal occurs. A missing final receipt is
   incomplete. A partially written/malformed file is an integrity error.

Audit status describes observed check/input outcomes, not proof that final receipt
persistence succeeded. A write failure after the audit may leave a run event with
no final receipt; CLI exit 2 is still failure. A cleanup/audit failure never creates
a final receipt. Abrupt termination can retain both intent and blocking run marker;
use the independent human-reviewed [lock recovery](LOCKING.md) procedure.

| Run/inspection `status` | CLI exit | Meaning |
|---|---:|---|
| `passed` | 0 | Every enabled fixed check passed and observed context remained equal |
| `failed` | 1 | A recorded check failed, with unchanged observable context |
| `timed-out` | 1 | A recorded check timed out, with unchanged observable context |
| `changed-inputs` | 1 | One or more observed bindings changed, regardless of child success/failure |
| `incomplete` | 1 | Post-check context unavailable, or valid intent without final receipt during inspection |
| Handled policy/storage/usage/integrity error | 2 | No success result; inspect retained evidence before deciding what to do |

Each recorded check contains only `check`, `status` (`passed`, `failed`,
`timed-out`) and integer `exit_code`. Order must be an enabled-check prefix;
non-passing checks terminate the sequence. Timeouts use -1 and preserve the
1–300-second per-check limit. `changed-inputs` takes precedence over timeout/check
failure; unavailable post-check context takes precedence over all outcomes.

`run` retains its captured check output in the returned result and adds `run_id`,
`receipt_fingerprint` and fixed `reasons`. JSON envelopes remain schema 1. Returned
stdout/stderr are truncated to their last 12,000 characters each; subprocess
capture continuously drains bounded 65,536-byte tails per stream. Receipts never persist
this output, task/advice, approval reasons, arbitrary paths or raw OS errors.
Returned check output can still be sensitive.

## Binding and inspection contract

Start `bindings` and final `end_context` have exactly these keys:

| Key | Recorded observation |
|---|---|
| `plan_fingerprint` | Stored plan fingerprint |
| `plan_digest` | Canonical hash of the whole current plan record |
| `approval_digest` | Canonical hash of the whole current approval, including its reason without disclosing it |
| `workspace_digest` | Bounded original content snapshot |
| `config_digest` | Canonical hash of validated schema-1/2 configuration |
| `targets_digest` | Bounded selected-file digest for schema 2; `null` for schema 1 |
| `execution_contract` | Installed version and fixed runner/lock/check/environment/receipt contract |

The final record contains schema/run ID, intent fingerprint, UTC finish time,
status, end context (or `null` when unavailable), check outcomes, reasons and its
own fingerprint. Fingerprints hash canonical JSON with only their own
`fingerprint` omitted. Receipts are local, unkeyed and mutable, not signatures.

Fixed change reasons are `plan-changed`, `approval-changed`, `source-changed`,
`configuration-changed`, `selected-targets-changed`, `execution-contract-changed`,
in that order. Unavailable post-check context uses `postcheck-context-unavailable`;
inspection of an absent final receipt uses `completion-receipt-absent`.

`inspect-run` strictly validates exact fields, integer schema/types, canonical
hashes, IDs, timestamps, fixed check names/order/outcomes and status/reason/context
consistency. It rereads files/parent identities before returning. Results include
recorded version, `version_matches`, IDs/fingerprints, times, bindings/check
metadata and `source_context: "historical-binding-only"`. A historically passed
receipt remains inspectable with exit 0 after upgrades/current edits or deletion
of current plan/approval/config. This does not renew approval or assert that the
original remains unchanged now. Unsupported/malformed/unsafe/oversized/unreadable
or changing evidence returns the fixed sanitized policy error with `data: null`.

## Bounds, compatibility and limits

Each intent/final receipt is capped at 16,000 bytes; control reads at 256,000 bytes
each. Reads reject duplicate keys, non-finite values, unsupported UTF-8/JSON,
links/reparse points, nonregular files and hardlink aliases. New directories/files
request 0700/0600 modes; platform ACLs/umask still apply. Exclusive writes are
flushed/fsynced and read back; interrupted writes can remain partial. Audit files
now use the existing strict regular-file/nonblocking open, rejecting links,
reparse points, hardlinks and FIFOs. No hostile-writer isolation is added.

Context observations reuse the [current-original review](STAGE_REVIEW.md) snapshot
and target bounds: 5,000 files, 12 MB/file, 64 MB total per source/selected scan;
source 10,000 entries/64 levels, target metadata 5,000 entries per enabled check.
Original environment files are hashed locally, never emitted; selected generated
data remains included. Conventional generated directories are excluded only from
the ordinary source digest. Metadata and empty-directory changes are not bound.

Runner protocol **5** binds receipt schema 1 and
`PYTHONDONTWRITEBYTECODE=1` for every fixed Python child. This suppresses automatic
import bytecode, allowing ordinary schema-2 unittest runs to preserve selected
inputs. Explicit schema-1 `compileall` still writes its generated bytecode;
tests may explicitly write files too. UTF-8 streams remain enforced. Config 1/2,
plan 1, approval 2, envelope 1 and native-lock protocol 3 remain supported.
Upgrading to 0.3.0a20 requires a fresh reviewed plan/approval; history is preserved.

Snapshots and double observations are point-in-time evidence: they cannot detect
every transient/ABA change, prove assertions, contain deliberately escaped descendants or restrict
trusted Python filesystem access. A malicious local actor can rewrite all records.
`passed` says only that enabled checks passed with equal observed inputs; a
compile-only configuration does not establish that unit tests ran. This receipt command performs no original application. [Explicit application/rollback](APPLICATION.md) are implemented separately; Git commit/push automation, authenticated provenance and OS sandboxing remain unsupported. [Git staging](GIT_STAGING.md) is separately implemented.
Public GitHub/PyPI alpha remains 0.3.0a8.

Source 0.3.0a16 adds [owned fixed-check supervision](SUPERVISION.md): a gated launcher, POSIX group/PID anchor or Windows kill-on-close job, native completion/termination checks and continuously drained bounded stream tails. Timeout includes ordinary owned descendants and pipe retention; uncertain cleanup retains run.lock and incomplete intent without a final receipt. Runner 5/lock 3 require fresh version-bound approval. This covers cooperating same-group POSIX descendants/job members, not deliberate group/session escapes, hostile-code isolation or automatic stale recovery. The guide defines normal, timeout, cancellation and abrupt-parent-death limits.

Source 0.3.0a20 waits for final zero Windows job accounting within the same three-second cleanup budget used for launcher exit, EOF and failure cleanup. A transitional positive count cannot turn a completed failed check into an immediate operational error; persistent/unavailable confirmation remains fail-closed with retained state. Fixed-phase diagnostics exclude native exception text. Runner 5/lock 3 and schemas remain; the updated version/cleanup-policy binding requires fresh reviewed plans/proposals/approvals.
