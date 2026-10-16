# Local plan-bound proposals — 0.3.0a10

<!-- safeops-version: 0.3.0a10 -->

[Português (Portugal)](pt-PT/PROPOSALS.md)

`propose` stores a manually authored [schema-1 candidate](PREVIEW.md) locally,
bound to an existing plan and its unchanged context. `review-proposal` revalidates
that record and returns the exact read-only diffs. Neither command applies source
changes, grants approval, executes checks, calls a provider or writes Git state.
A successful review is a point-in-time integrity check, not permission to apply.

## Workflow

Initialize the trusted project once. Use the candidate-generation example in
[the preview guide](PREVIEW.md) with the existing `PROJECT/hello.txt`. Keep
`candidate.json` outside `PROJECT`, since adding it inside after planning would
change the workspace snapshot. Candidate paths are relative to the project;
the candidate JSON filename is relative to the shell working directory, or absolute.

```bash
safeops --root PROJECT init
safeops --root PROJECT plan "Improve the greeting documentation" --path hello.txt
safeops --root PROJECT review PLAN_ID
safeops --root PROJECT --json propose PLAN_ID candidate.json
safeops --root PROJECT --json review-proposal PROPOSAL_ID
```

Replace `PLAN_ID` and `PROPOSAL_ID` with actual 12-character lowercase hex IDs.
Each proposed file must **exactly match** an explicit plan `--path` entry;
a directory entry does not implicitly permit descendants. A subset of the named
files is allowed; an empty scope or critical-risk plan is rejected. These
proposal restrictions do not change advisory plan scope into a filesystem
sandbox or restrict the separate fixed-check targets.

Creation stores a copy of the candidate. Later edits/deletion of the external
JSON file do not change it. To change the proposed content, create another
proposal. If source changed, create a fresh plan and regenerate base hashes.
Preserve earlier plans, proposals and approvals; there is no automatic renewal.

## Record schema 1 and bindings

Storage is `.safeops/proposals/PROPOSAL_ID.json`, excluded from ordinary snapshots.
The exact top-level keys are `schema` (integer 1), `id`, `created_at` (UTC timestamp),
`safeops_version`, `bindings`, `candidate`, `candidate_sha256` and `fingerprint`.
`candidate` keeps the strict preview schema and its content. The canonical
candidate must be at most 256,000 bytes; the whole record read is bounded to
260,096 bytes. All preview file/text/path/base/aggregate limits still apply.

`bindings` contains exactly:

| Field | Bound value |
|---|---|
| `plan_id` | Existing plan ID |
| `plan_fingerprint` | Integrity-checked plan fingerprint |
| `workspace_digest` | Current snapshot, equal to the plan snapshot |
| `config_digest` | Validated configuration hash |
| `targets_digest` | Schema-2 selected-file digest, or `null` for schema 1 |
| `execution_contract` | Installed version and fixed runner/lock/check contract |

The record fingerprint hashes canonical JSON with only `fingerprint` omitted;
`candidate_sha256` hashes canonical candidate JSON. Formatting/key order does
not matter, but file order does. Version, bindings and candidate hashes are
checked again on review. A change to any source file in the ordinary snapshot
invalidates the proposal, including an unrelated edit. Schema-2 selected generated
files are also bound. Configuration changes and package upgrades invalidate it.

Plan/context is checked before and after candidate validation. Source paths and
exact original bytes are rechecked by preview. Unsafe storage directories,
symlinks/reparse points and nonregular records are rejected. Newly created
proposal directories request mode 0700 and files mode 0600; actual access control
is platform-dependent, especially on Windows. This is not filesystem isolation,
an atomic snapshot or protection against hostile concurrent directory swaps.

## Output, audit and failure behavior

Both commands use the optional common [JSON envelope](OUTPUT.md) and exit 0 on
success, 2 for handled failures. Creation returns `schema`,
`status: "proposal-recorded"`, `proposal_id`, `plan_id`, candidate/record hashes
and a fixed notice; it does not print candidate content. Review returns
`status: "proposal-reviewed"`, the same identifiers/hashes, `files` with exact
preview diffs and the notice. Review is read-only, including the audit log.

Creation appends `action: "propose"`, the plan ID and `status: "recorded"` to the
local audit without source/proposed text. Record creation and audit append are
separate writes: an audit failure can return an error with the proposal retained.
Inspect existing state before retrying. Existing IDs are not deliberately replaced;
there is no concurrent-writer transaction guarantee.

Records contain full proposed text; review diffs contain original text too.
Treat both as sensitive, keep `.safeops` out of Git and review locally before
sharing. No automatic redaction/upload or secret-free guarantee is provided.
An actor able to rewrite records can recompute unkeyed hashes; these are not
signatures, authenticated provenance or a tamper-proof audit.

## Compatibility and next work

Config schemas 1/2, plan schema 1, approval schema 2, output schema 1 and runner
3/lock 1 protocols remain supported. This separate proposal schema grants no
execution approval. Upgrading to 0.3.0a10 requires a fresh reviewed plan and
explicit execution approval under the version-bound contract. A proposal is not
an input to `approve` or `run`, which still perform only the existing fixed checks.

AI-generated candidates, patch application/rollback, new/deleted/renamed files,
CRLF/binary edits, isolated worktrees and signed provenance remain planned.
Source versioning does not create a release; see [current status](STATUS.md).
