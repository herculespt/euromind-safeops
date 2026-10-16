# Reviewed original application — 0.3.0a18

<!-- safeops-version: 0.3.0a18 -->

[Português (Portugal)](pt-PT/APPLICATION.md)

Implemented in source. Public GitHub/PyPI 0.3.0a8 predates these commands.

The commands are `review-application STAGE_ID --run RUN_ID`,
`apply-stage STAGE_ID --run RUN_ID --confirm REVIEW_FINGERPRINT`,
`inspect-application APPLICATION_ID` and
`rollback-application APPLICATION_ID --confirm ROLLBACK_FINGERPRINT`.

Review requires current original-context compatibility, a matching stage, and a
current unchanged staged run with both compile and unit-tests passed under the
same configuration as the original. Review itself writes nothing and grants no
permission. Application requires its exact fingerprint, native guards and fresh
revalidation. No provider, subprocess or Git operation runs during application.

Prepare bounded private original backups and replacement files, then an immutable
hashed manifest before setting an owned pending marker or changing source. Only
existing writable UTF-8 candidate text files are replaced, one at a time, preserving
basic mode and POSIX owner/group where available. Source file operations cannot
create/delete/rename project paths. Internal same-filesystem replacement files
and control artifacts are necessary; there is no multi-file atomicity guarantee.
ACLs, extended attributes and timestamps are outside the initial metadata contract.

On failure retain backups, manifest, remaining replacements and pending marker.
The marker blocks approved runs and new applications on the original. Inspection
reports current candidate-file hashes/identities without content. Rollback needs
an exact fresh inspection fingerprint, original backups, known file identities,
matching current contents/modes and native guard. Refuse visible concurrent edits,
missing files, unsafe paths and unknown partial state; never force restoration or
automatically discard evidence. Restore only candidate files, not unrelated edits.

Hashes/guards are cooperative local evidence, not authentication or isolation.
Revalidation cannot eliminate races with uncooperative writers or transient/ABA
changes. Readers can observe intermediate files. Backups contain local source text
and must remain private and ignored by Git. Public metadata excludes file content,
captured output, tasks/advice, approval reasons and credentials. Existing plans,
approvals, proposals, stages, run receipts and Git history are retained.

## Controlled workflow

1. On the original, create an explicit-path plan, a local proposal and a separately confirmed stage as described in [proposals](PROPOSALS.md) and [staging](STAGING.md). Keep the original unchanged. No original execution approval is reused.
2. Inspect/trust the copied code, initialize that copy and retain the same validated configuration as the original, enabling both `compile` and `unit-tests`. Create/review/explicitly approve a fresh staged plan and run it in the copy. Keep its returned `run_id`. A compile-only or historical/stale passed receipt is insufficient.
3. On the original, run the read-only review below. Review every path, before/replacement hash, byte count and metadata policy. The fingerprint binds the observed source, control bytes, proposal, stage, run and current version/contract; review alone grants no consent.
4. Only after that review, supply its exact fingerprint to `apply-stage`. A fresh double review runs again while holding both native guards. Any observed change requires a new review; approval text or an earlier check approval cannot substitute.

```bash
safeops --json --root ORIGINAL_PROJECT review-application STAGE_ID --run RUN_ID
safeops --json --root ORIGINAL_PROJECT apply-stage STAGE_ID --run RUN_ID --confirm REVIEW_FINGERPRINT
safeops --json --root ORIGINAL_PROJECT inspect-application APPLICATION_ID
# Only after inspecting the current candidate states and retained journal:
safeops --json --root ORIGINAL_PROJECT rollback-application APPLICATION_ID --confirm ROLLBACK_FINGERPRINT
```

The last command uses the fresh `rollback_fingerprint` from inspection, not the application-review fingerprint. Rollback does not require the current configuration, plan, approval or staged directory; its own immutable journal/backups and current candidate ownership must remain valid. Repeated completed rollback is idempotent. After application or rollback, create a fresh reviewed execution plan/approval for subsequent checks.

## State, persistence and interruption

All records live under private `.safeops/applications/<12hex>/`. Intent schema 1 binds review/proposal/stage/run fingerprints and each path's before/prepared hash, size, device/inode identity, basic mode, owner/group and nanosecond observation stamps. Backups are `backup-<index>.bin`; prepared new/restore files are consumed by same-filesystem `os.replace`. Immutable `restore-<index>.json` binds each prepared restore before installation. `applied.json` and `rolled-back.json` are separate schema-1 completion records, linked by intent fingerprint. Records use canonical unkeyed SHA-256 and exclusive creation; backup/control files start with mode 0600 and owned directories with 0700 where supported. Replacement files receive original basic metadata.

| Observation | Meaning and next action |
|---|---|
| Preparation failure before valid intent/pending | Source has not been written; retain partial directory for manual review. No automatic cleanup or repair. |
| `pending` | Valid journal with retained own marker or without matching terminal completion. Inspect per-file `original`, `applied` or `restored` states and confirm rollback if conflict-free. |
| `applied` | Completion record, every candidate matches installed metadata and no own pending marker. Historical result, not new execution approval. |
| `rolled-back` | Completion record, every candidate matches original/owned restored metadata and no own pending marker. |
| `conflicted` | A candidate differs in observed bytes/identity/metadata. Preserve human edits; automatic rollback is refused. |
| Inspection error (2) | Missing/unsafe/oversized/changing/malformed journal, backup, candidate or unknown partial artifact. Preserve evidence and investigate manually. |

Before each write and after the last application write, recheck all candidate observations, original snapshot/selected targets, control bytes, journal directory identities and unchanged stage/run context. Rollback checks candidate observations and journal ownership at each step and restores only applied files, in reverse order. An interruption after rename but before return can be recognized by the bound prepared identity/hash. A valid restore intent plus its unconsumed prepared file permits explicit continuation. An unbound partial restore file, corrupt backup, missing candidate or malformed completion is intentionally refused; there is no force, repair or discard command.

Audit append precedes each terminal record. An audit/terminal/marker-release failure can return 2 after some or all source replacements; a completion can exist while `status` remains `pending`. Inspect before retrying. A fresh confirmed rollback can finish a known partial rollback or clear its unchanged owned pending marker. It never removes another journal's marker. `recover-lock` deals only with `run.lock`, never `application.pending`. Abrupt process death releases native guards but preserves pending state; no liveness or automatic recovery decision is inferred.

Files are flushed/fsynced before source replacement. Directory entries are not fsynced: power loss/storage durability and multi-file transactions are outside this contract. Native locks coordinate local cooperating versions only; readers and uncooperative writers remain possible. Windows basic mode differs from POSIX, and replacing a file held open externally can fail. No ACL/xattr/timestamp, network-filesystem or hostile-owner guarantee is made.

## Bounds, output and compatibility

- Candidate limits: 1–20 existing files, at most 256,000 bytes per original/replacement and 1,000,000 bytes combined old/new; existing preview LF/BOM-free/final-newline rules remain. No special mode bits or read-only owner mode; all paths/ancestors must be safe regular files without hard links/reparse points.
- Journal records: 64,000 bytes each; at most 85 known artifacts per application. Strict UTF-8 object decoding rejects duplicate keys/non-finite values, extra fields, malformed timestamps/IDs/fingerprints, invalid identity/mode/size metadata and unknown artifacts. Existing source/stage/selected-target/context budgets also apply; see [current review](STAGE_REVIEW.md) and [run receipts](RUN_RECEIPTS.md).
- Review and inspection write nothing and invoke neither provider nor project code. Successful operations use the common schema-1 envelope. Inspection returns 0 for `applied`/`rolled-back`, 1 for `pending`/`conflicted`; handled operational/integrity errors return sanitized 2. Output contains local paths, hashes, sizes and file metadata, never file content. Review returns `fingerprint`; inspection returns `rollback_fingerprint` and a point-in-time `rollback_candidate`, which is not permission by itself.
- Runner protocol is 5; native-lock protocol is 3 because any pending application entry blocks new approved runs/applications. Config 1/2, plan 1, approval 2 and envelope 1 remain. Upgrades require fresh version-bound plans/proposals/approvals; retained schema-1 application journals remain independently inspectable/recoverable with `version_matches` reported, not approval renewed.

Offline regressions cover multiple files, real trusted checks, actual parent termination, partial application/rollback, audit/finalization/release failures, stale confirmations, human edits, ownership, unsafe paths and strict bounds. The same suite runs against installed wheels and the supported OS/Python matrix. No paid provider request or real repository application is needed for these fixtures. AI candidate generation, create/delete/rename operations, Git worktrees/writes, signed provenance, OS isolation and hostile-process containment remain planned.

Most lifecycle/parser fixtures use synthetic successful fixed-check responses; a separate case executes the real approved compile/unittest pair. The abrupt-death case runs the application in an actual child process and terminates it after the first replacement.

Source 0.3.0a16 adds [owned fixed-check supervision](SUPERVISION.md): a gated launcher, POSIX group/PID anchor or Windows kill-on-close job, native completion/termination checks and continuously drained bounded stream tails. Timeout includes ordinary owned descendants and pipe retention; uncertain cleanup retains run.lock and incomplete intent without a final receipt. Runner 5/lock 3 require fresh version-bound approval. This covers cooperating same-group POSIX descendants/job members, not deliberate group/session escapes, hostile-code isolation or automatic stale recovery. The guide defines normal, timeout, cancellation and abrupt-parent-death limits.
