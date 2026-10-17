# Trust model and threat analysis

## Assets

Human approval intent; source code under review; local credentials; repository integrity; audit events; provider API keys.

## Trust boundaries

1. **User-authored task descriptions** are untrusted as executable input.
2. **AI advice** is untrusted text and can contain prompt injection or false claims.
3. **Workspace source files and tests** are trusted only to the extent the operator trusts the repository. They are executable during checks.
4. **Local `.safeops` state** is mutable by the user/other processes and is not an independent security domain.
5. **Remote provider** is an external data processor; only opt in with reviewed non-sensitive tasks/source context.

## Protections implemented

| Threat | Current response | Residual risk |
|---|---|---|
| Model prompt-injection causing arbitrary commands | No model-supplied command/tool is dispatched; candidates require explicit review/staged checks/application | Approved candidate Python remains executable trusted test/source code |
| Modified plan after approval | SHA-256 fingerprint and approval linkage | Local actor can edit and recompute hashes |
| Edited source after approval | Full content hash snapshot before execution | Ignored directories and symlinks are outside the snapshot |
| Check command injection | Fixed command table, `shell=False` | Python tests can execute arbitrary code |
| Reusing approval after tool/command changes | Schema-2 approval binds package version and fixed execution contract | Local actors can rewrite state and recompute hashes |
| Ambiguous policy JSON | Exact config keys/types, unique supported checks, strict UTF-8 JSON with unique keys and finite numbers | No filesystem allowlist or signed policy is implemented |
| Ambiguous provider JSON or error-body disclosure | Shared strict UTF-8 object decoder, bounded read and redacted HTTP/URL/timeout CLI errors; blocked redirects | CI uses doubles/local fixtures; separate OpenAI and Anthropic live smokes passed, without establishing other accounts/models, total request deadlines or model security |
| Invalid advisory scope causing provider access or unsafe approval | Portable path preflight before advice/persistence and revalidation at approval/run | Advisory only; whole-workspace checks and filesystem races remain, with no isolation |
| Empty or all-skipped unit-test suite | Child runner requires discovered cases and a non-skipped execution | Trusted tests can manipulate the interpreter; assertion quality is not verified |
| Remote data exfiltration | Task-only advisory; separate exact-source/fingerprint upload consent for generation, bounded selected files and heuristic checks | Unknown private data/secrets, residual file races and provider retention remain; TLS trusts endpoint |
| Hidden credentials in repository | Heuristic scanner prints only file/line | Unknown secret formats will be missed |
| Concurrent check runs/recovery | Persistent native guard, owned marker and fingerprint/acknowledgement-bound archival recovery; [policy](LOCKING.md) | Local cooperative lock; retained markers do not prove child liveness; no distributed guarantee, hostile descendant containment or protection from a state owner rewriting files |
| Root symlink to private directory | Root resolves explicitly; `.safeops` symlink rejected | Other local filesystem races possible |

## Explicitly unsupported

SafeOps does not provide a sandbox, untrusted-code isolation, signature-based
approval, hardened secure enclave, reproducible-build proof or guaranteed
prompt-injection resistance. The separate maintainer publication workflow uses
protected main, PyPI OIDC and PyPI-verified publishing attestations; those do not
sign local SafeOps plans, approvals or stage records.

## Operational guidance

Use a dedicated nonprivileged development account. Keep credentials outside the repository. Verify planned task and source-tree state. Run only trusted test suites. Treat every model suggestion as untrusted. Use independent secret scanning and security review before any public release.

Discovery imports executable test modules only after approval, in the child process. A compile-only configuration remains supported and makes no claim that unit tests ran. See [execution policy](EXECUTION.md), [ADR 0002](adr/0002-versioned-check-contract.md) and [current implementation status](STATUS.md).

## Local proposal boundary

[Plan-bound proposals](PROPOSALS.md) add bounded local candidate persistence and context revalidation. Exact plan file membership is required only for proposals. Review detects common stale/tampered state but hashes are unkeyed and records mutable. Stored candidate text and diffs can be sensitive; no automatic publication/redaction, application or execution authority is added.

## Staging copy boundary

[Staging](STAGING.md) requires the exact reviewed proposal fingerprint and materializes replacements only in independent local files. Snapshot/exclusion checks are point-in-time, not transactional isolation. Receipts are mutable/unkeyed and no original approval is reused. Copied code can still access the host when explicitly approved checks execute it.

Read-only `inspect-stage` checks historical integrity and current filtered copy
bytes, not current-original equivalence or authorship. Excluded state, file
metadata and every concurrent race are outside the comparison. A matching result
does not establish passing tests or grant execution/application approval.

`review-stage` requires a matching staged copy and independently revalidates current original/plan/base/configuration/target/version/contract bindings. This is a bounded point-in-time read of unkeyed mutable local evidence, without writes, approval renewal, application or proof of passing checks. Original environment files may be hashed locally; no contents are emitted. Double observations and final stage inspection do not eliminate every filesystem race. See [the review contract](STAGE_REVIEW.md).

Approved-check [run receipts](RUN_RECEIPTS.md) bind observed before/after context and fixed outcomes but remain unkeyed mutable local evidence. Terminal receipts require successful lock cleanup and audit; absent/partial files cannot prove completion. Historical passed results do not establish current compatibility or application authority. Trusted code can still mutate inputs between observations, spoof test outcomes or spawn descendants. Returned check output can contain sensitive data; it is excluded from persisted receipts.

Source 0.3.0a15 adds [explicit reviewed application and conservative rollback](APPLICATION.md). Both staged fixed checks must pass with unchanged current bindings and the same configuration as the original; exact fresh human confirmation and native guards precede private backup/journal preparation and source writes. Any retained application marker blocks new approved runs/applications. Read-only inspection and separately confirmed rollback preserve evidence and refuse observed human edits. No multi-file transaction, power-loss guarantee, Git operation, provider request or OS isolation is added. That milestone used runner 4/lock 2. Fresh version-bound execution approval is required.

Source 0.3.0a16 adds [owned fixed-check supervision](SUPERVISION.md): a gated launcher, POSIX group/PID anchor or Windows kill-on-close job, native completion/termination checks and continuously drained bounded stream tails. Timeout includes ordinary owned descendants and pipe retention; uncertain cleanup retains run.lock and incomplete intent without a final receipt. Runner 5/lock 3 require fresh version-bound approval. This covers cooperating same-group POSIX descendants/job members, not deliberate group/session escapes, hostile-code isolation or automatic stale recovery. The guide defines normal, timeout, cancellation and abrupt-parent-death limits.

Source 0.3.0a17 waits for final zero Windows job accounting within the same three-second cleanup budget used for launcher exit, EOF and failure cleanup. A transitional positive count cannot turn a completed failed check into an immediate operational error; persistent/unavailable confirmation remains fail-closed with retained state. Fixed-phase diagnostics exclude native exception text. Runner 5/lock 3 and schemas remain; the updated version/cleanup-policy binding requires fresh reviewed plans/proposals/approvals.


## Worktrees and provenance — 0.3.0a20

[Git staging](GIT_STAGING.md) requires separate exact consent, verified base/index/linkage and unchanged human gates. Worktrees share objects/configuration/refs and do not isolate hostile code. Regular `.git` files are metadata, excluded from source digests and validated separately for Git stages. Signed SafeOps provenance (#61) remains planned: expected identity, canonical signed bytes and a trust/revocation policy are required; local SHA-256 does not authenticate a signer. Existing PyPI attestations concern publication, not SafeOps approval.
