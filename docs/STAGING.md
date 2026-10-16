# Separate local staging copies — 0.3.0a11

<!-- safeops-version: 0.3.0a11 -->

[Português (Portugal)](pt-PT/STAGING.md)

`stage-proposal` materializes a reviewed [local proposal](PROPOSALS.md) in a new,
separate copy. Replacement text is written only to that copy. The original
project source, plans, approvals and Git state are preserved; local stage state
and a content-free audit event are added. No provider or external command runs.
This is a regular directory copy, not a Git worktree, clone or OS sandbox.

## Workflow and confirmation

Create a fresh plan and proposal under the installed version, then review it:

```bash
safeops --root PROJECT --json review-proposal PROPOSAL_ID
safeops --root PROJECT --json stage-proposal PROPOSAL_ID --confirm PROPOSAL_FINGERPRINT
```

Use the exact 64-character `fingerprint` returned by `review-proposal`, not the
proposal ID or candidate hash. Inspect its diffs first. An old/changed fingerprint
or stale proposal fails; this confirmation authorizes only local copy creation,
never original-source application or code execution. The proposal and unchanged
source/configuration/target/contract bindings are revalidated before and after
copying. A later proposal/source change does not silently update an existing copy.

The result gives the absolute `workspace` path. Inspect those files and the
receipt before initializing the copy for trusted checks:

```bash
safeops --root STAGED_WORKSPACE init
safeops --root STAGED_WORKSPACE plan "Validate reviewed staged changes"
safeops --root STAGED_WORKSPACE review NEW_PLAN_ID
safeops --root STAGED_WORKSPACE approve NEW_PLAN_ID --confirm NEW_PLAN_ID --reason "Reviewed staged code and trusted tests"
safeops --root STAGED_WORKSPACE run NEW_PLAN_ID
```

Substitute actual paths and IDs; put `--json` before a command if needed.
The original approval is not copied/reused. The staged plan binds the modified
copy. `run` remains limited to the existing fixed compile/unittest checks;
no automatic checks or application follow staging. Tests can execute arbitrary
Python, read files outside the copy and use inherited environment/network access.
Only use source and tests that you trust. A successful check does not approve
applying the proposal to the original project.

## Copy scope, limits and privacy

The copy uses ordinary [snapshot enumeration](EXECUTION.md), with at most 5,000
regular files and 12,000,000 bytes per source file. Snapshot-generated directories
(`.git`, `.safeops`, `.venv`, `venv`, caches, `.tox`, `node_modules`, `dist`, `build`)
are omitted; matching internal file components such as a worktree `.git` file
are omitted too. Symlinks/nonregular entries are omitted by enumeration; selected
candidate paths still reject links. Every copied path undergoes portable scope
preflight and each opened source descriptor must be regular and match its
inspected identity. Unsupported paths or unsafe ancestors fail.

All `.env` and `.env.*` components, including `.env.example`, are omitted.
Candidates targeting them cannot be staged. Other files can contain credentials
or sensitive text: these exclusions are not a secret-free guarantee. No provider
request or upload is made. The operator must inspect any later sharing.
No environment sanitization or filesystem isolation is claimed.

Total materialized file content is capped at 64,000,000 bytes. The copied candidate
keeps all preview limits. Empty replacement content creates an existing empty
file. Files are independent new byte copies, not hard links. New directories
request mode 0700 and files 0600; actual ACLs depend on the platform. Executable
bits, timestamps, ownership and other metadata are not preserved. Generated
outputs, dependencies and environment files may need separate local preparation;
this is not a complete reproducible build environment or submodule/LFS checkout.

## Storage and receipt schema 1

Local storage is `.safeops/stages/STAGE_ID/`, excluded from the original snapshot:

- `intent.json`: stage/proposal IDs, creation time, installed version, exact proposal
  fingerprint, candidate hash and original workspace digest.
- `workspace/`: independent source bytes with reviewed replacements.
- `receipt.json`: created only after copy verification and final proposal review;
  includes the intent fields, `status: "staged"`, file manifest, total bytes,
  staged workspace digest and a canonical JSON `fingerprint` omitting itself.

Manifest entries contain `path`, original `source_sha256`, `staged_sha256`,
`bytes` and `replaced`. The receipt is capped at 1,000,000 bytes including its
final newline. Original `.safeops` records are not imported into the copy.
Neither intent nor receipt includes file text; names and content hashes can
still disclose information. Local files remain mutable and unsigned.

The command returns schema 1, status, stage/proposal IDs, proposal fingerprint,
workspace path, receipt fingerprint, copied-file/byte counts and a fixed notice.
The common [JSON envelope](OUTPUT.md) and handled 0/2 exit codes apply.

## Failures and authority

Stage IDs are created exclusively and never intentionally overwritten. After
allocation, failures return a controlled message identifying the retained stage;
no automatic cleanup/deletion is attempted. An absent receipt means incomplete
staging. Inspect partial state before retrying; retries create a separate ID.
Receipt creation and audit append are separate operations: an audit failure can
return an error even when the receipt/copy is ready. Check actual local evidence.

Source/manifest checks detect common concurrent edits, not every filesystem
race. A hostile local writer can replace files or recompute unkeyed hashes.
A receipt records point-in-time content; later editing/check execution can change
it. No stage-inspection command, authenticated provenance, write isolation or
transactional filesystem guarantee is provided.

Config 1/2, plan 1, approval 2, envelope 1 and runner 3/lock 1 remain supported.
Upgrading to 0.3.0a11 requires fresh version-bound proposals and execution
approval; history is retained without migration. Applying changes to the original
workspace, rollback, isolated Git worktrees and OS sandboxing remain planned.
See [status](STATUS.md) and [roadmap](../ROADMAP.md).
