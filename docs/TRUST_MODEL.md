# Trust model and threat analysis

## Assets

Human approval intent; source code under review; local credentials; repository integrity; audit events; provider API keys.

## Trust boundaries

1. **User-authored task descriptions** are untrusted as executable input.
2. **AI advice** is untrusted text and can contain prompt injection or false claims.
3. **Workspace source files and tests** are trusted only to the extent the operator trusts the repository. They are executable during checks.
4. **Local `.safeops` state** is mutable by the user/other processes and is not an independent security domain.
5. **Remote provider** is an external data processor; only opt in with non-sensitive tasks.

## Protections implemented

| Threat | Current response | Residual risk |
|---|---|---|
| Model prompt-injection causing arbitrary commands | Model output is never passed to subprocess | Human may manually follow unsafe advice |
| Modified plan after approval | SHA-256 fingerprint and approval linkage | Local actor can edit and recompute hashes |
| Edited source after approval | Full content hash snapshot before execution | Ignored directories and symlinks are outside the snapshot |
| Check command injection | Fixed command table, `shell=False` | Python tests can execute arbitrary code |
| Reusing approval after tool/command changes | Schema-2 approval binds package version and fixed execution contract | Local actors can rewrite state and recompute hashes |
| Ambiguous policy JSON | Exact config keys/types, unique supported checks, strict UTF-8 JSON with unique keys and finite numbers | No filesystem allowlist or signed policy is implemented |
| Ambiguous provider JSON or error-body disclosure | Shared strict UTF-8 object decoder, bounded read and redacted HTTP/URL/timeout CLI errors; blocked redirects | CI uses doubles/local fixtures; separate OpenAI and Anthropic live smokes passed, without establishing other accounts/models, total request deadlines or model security |
| Invalid advisory scope causing provider access or unsafe approval | Portable path preflight before advice/persistence and revalidation at approval/run | Advisory only; whole-workspace checks and filesystem races remain, with no isolation |
| Empty or all-skipped unit-test suite | Child runner requires discovered cases and a non-skipped execution | Trusted tests can manipulate the interpreter; assertion quality is not verified |
| Remote data exfiltration | Opt-in provider, task-only payload, HTTPS/loopback-only | User may paste secrets into task; TLS trusts endpoint |
| Hidden credentials in repository | Heuristic scanner prints only file/line | Unknown secret formats will be missed |
| Concurrent check runs | Exclusive local lockfile | Crash can leave lock; filesystem races exist |
| Root symlink to private directory | Root resolves explicitly; `.safeops` symlink rejected | Other local filesystem races possible |

## Explicitly unsupported

No sandbox, untrusted-code isolation, signature-based approval, hardened secure enclave, reproducible attestation, protected CI release channels, cryptographic transparency log or guaranteed prompt-injection resistance.

## Operational guidance

Use a dedicated nonprivileged development account. Keep credentials outside the repository. Verify planned task and source-tree state. Run only trusted test suites. Treat every model suggestion as untrusted. Use independent secret scanning and security review before any public release.

Discovery imports executable test modules only after approval, in the child process. A compile-only configuration remains supported and makes no claim that unit tests ran. See [execution policy](EXECUTION.md), [ADR 0002](adr/0002-versioned-check-contract.md) and [current implementation status](STATUS.md).
