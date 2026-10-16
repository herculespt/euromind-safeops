# Local candidate previews — 0.3.0a15

<!-- safeops-version: 0.3.0a15 -->

[Português (Portugal)](pt-PT/PREVIEW.md)

`safeops --root PROJECT --json preview CANDIDATE.json` validates a locally
authored replacement candidate and returns unified diffs. The candidate path is
relative to the shell's working directory, independently of `--root`; absolute
paths are also accepted. No initialized `.safeops` workspace is required.
No files, approval/audit records or Git state are written; no provider, test or
external command is invoked. The default CLI also prints JSON data; `--json`
adds the common [schema-1 envelope](OUTPUT.md).

## Candidate schema 1

The top-level object has exactly `schema` (integer 1, never boolean) and `files`
(one to twenty entries). Every entry has exactly:

| Field | Contract |
|---|---|
| `path` | Canonical portable relative path to an existing regular workspace file |
| `base_sha256` | 64 lowercase hexadecimal digits hashing the exact original bytes |
| `content` | Full replacement text, not a shell command or unified-patch fragment |

Create a minimal local candidate for a trusted file with this Python example.
Run it from a directory containing `PROJECT/` and an existing `PROJECT/hello.txt`;
review the replacement text before previewing it. It writes only the explicitly
selected candidate file, outside the project, through the example script.

```python
import hashlib
import json
from pathlib import Path

original = Path("PROJECT/hello.txt").read_bytes()
candidate = {"schema": 1, "files": [{
    "path": "hello.txt",
    "base_sha256": hashlib.sha256(original).hexdigest(),
    "content": "Hello from EuroMind SafeOps!\n",
}]}
Path("candidate.json").write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
```

```bash
safeops --root PROJECT --json preview candidate.json
```

Strict JSON parsing rejects duplicate keys, non-finite numbers, invalid UTF-8,
non-object documents, unknown fields and unsupported schemas. Candidate and
each original/replacement are limited to 256,000 bytes. Combined original plus
replacement bytes across files cannot exceed 1,000,000. Each text has at most
5,000 lines and must be BOM-free UTF-8, LF only, with a final newline when
nonempty. Tabs are supported; other C0/C1/DEL controls are rejected. Empty
replacement text represents an empty file, not file deletion.

Paths must be NFC-normalized, with no empty/dot components, duplicates or
case-fold collisions. The [scope policy](SCOPE.md) additionally rejects absolute,
traversal, reserved, internal/generated and unsafe linked/reparse paths.
Future files, directories and nonregular objects cannot be preview targets.
Final input components and opened descriptors must be regular; source ancestors
are preflighted. Reads are bounded and use no-follow/nonblocking flags where
available. Exact base hashes must match, and no-op replacements are rejected.
After building all results, paths are rechecked and original bytes compared
again; a detected concurrent edit fails the whole preview without partial output.

## Output and authority

Successful `data` contains `schema: 1`, `status: "preview-only"`,
`candidate_sha256`, a `files` list and a fixed notice. Each file has `path`,
`before_sha256`, `after_sha256` and a unified `diff` with three context lines,
using `a/` and `b/` labels. Diffs are strings in JSON; decode them to display
line breaks. The candidate hash uses canonical JSON (sorted keys, compact
separators, UTF-8), so input whitespace/key order does not change its identity;
file hashes use exact bytes. File order remains significant. These are content
integrity records, not authenticated author identity or signed provenance.
Success exits 0; handled policy/filesystem/usage failures exit 2.

Preview output includes local source and proposed text, which can contain
secrets. It is not redacted, uploaded or automatically added to audit/CI reports.
Inspect it locally before sharing. The built-in scanner is a separate heuristic,
not a guarantee that a candidate is safe. A valid diff does not establish
correctness, test success, execution approval or permission to apply anything.

This is a point-in-time local check, not an atomic filesystem snapshot or OS
isolation. Concurrent changes after preview, hard links and hostile filesystem
races are not prevented. General unified-patch imports, new/deleted files,
renames, binary/CRLF/no-final-newline edits, automatic AI candidate generation
and sandboxing remain planned. [Reviewed application/rollback](APPLICATION.md) are implemented separately. [Existing execution approvals](EXECUTION.md) are independent;
upgrading to this version still needs a fresh reviewed plan and explicit approval.

Persisted [plan-bound local proposals](PROPOSALS.md) are now available separately. `preview` itself remains stateless and does not initialize or write `.safeops`.
