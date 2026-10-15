# ADR 0002 — Versioned fixed-check contract and nonempty execution

- Status: Accepted for source version 0.3.0a1
- Date: 2026-10-15
- [Português (Portugal)](../pt-PT/adr/0002-versioned-check-contract.md)

## Problem

A test filename does not establish that a suite contains cases. Discovery also
imports executable code, so pre-approval discovery in the parent would move code
execution outside the existing approval boundary. Config hashes alone do not
invalidate an approval after the installed tool or fixed runner changes.

## Decision

Keep config and plan schema 1. Validate config keys/types and fixed unique check
names, and parse stored state as unambiguous UTF-8 JSON. Use approval schema 2,
binding the source, plan, config and versioned fixed execution contract.

Replace the raw unittest command with a package-owned, fixed stdlib adapter.
It discovers and runs tests only in the approved child process and rejects empty,
zero-execution and all-skipped suites. Preserve the fixed-command table,
shell-free invocation, UTF-8 streams, exclusive lock and per-check timeout.

Use source version 0.3.0a1 to signal the approval compatibility change and alpha
maturity. Retain historical records; require a fresh plan and explicit approval
after upgrade instead of migrating authorization intent.

## Consequences

No new remote access, runtime dependency, autonomous capability or sandbox is
introduced. Compile-only config remains allowed without a unit-test coverage
claim. Trusted tests and load hooks can still manipulate the interpreter;
nonempty execution does not certify assertions, coverage or security. Future
runner behavior changes must update the version/contract and compatibility docs.
