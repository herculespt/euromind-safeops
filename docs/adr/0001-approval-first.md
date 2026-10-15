# ADR 0001 — Approval-first, no automatic model-generated commands

- **Status:** Accepted
- **Date:** 2026-10-15

## Context

Language models can produce helpful implementation suggestions but may be wrong or manipulated by untrusted inputs. Executing arbitrary model-generated shell commands or edits would expose developer machines to unacceptable risk, especially without a reviewed sandbox.

## Decision

The initial public release is a deliberately conservative **review-and-check orchestration tool**, not an autonomous coding agent. Plans and provider advice are recorded as data, classified by deterministic rules, approved with explicit confirmation, then used solely to authorize hard-coded validation commands. All critical tasks are blocked. Approved actions are bound to a snapshot of source files and configuration.

## Consequences

- Advantages: simple installation, auditable behavior, testability and clear fail-closed semantics.
- Limitations: no autonomous patches, no true agent parallelism and no sandbox; workspace tests remain executable code.
- Future autonomous capabilities require a separate security review and a new ADR before implementation.
