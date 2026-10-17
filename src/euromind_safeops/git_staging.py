"""Opt-in local Git staging; fixed commands, no checkout hooks or filters."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from . import __version__
from .core import MAX_FILES, MAX_FILE_BYTES, SKIP_DIRS, SafeOpsError, json_bytes, sha256, source_files
from .preview import _read_regular
from .proposals import review_proposal
from .scope import validate_scope_paths

MAX_GIT_OUTPUT = 2_000_000
GIT_TIMEOUT = 15
POLICY = {"schema": 1, "mode": "detached-linked-worktree", "checkout": False,
          "hooks": False, "filters": False, "network": False, "automatic_cleanup": False,
          "git_output_bytes": MAX_GIT_OUTPUT, "git_command_timeout": GIT_TIMEOUT}
_FIELDS = {"schema", "git_dir", "executable", "commit", "head_sha256", "index_sha256",
           "config_sha256", "refs_sha256", "tracked_sha256"}
_ERROR = "Git staging refused: unsupported, unsafe, changed or unavailable local Git context"


def _directory(path):
    from .stage_inspection import _directory as check
    return check(path)


def _raw(path, limit=MAX_GIT_OUTPUT):
    if path.lstat().st_nlink != 1:
        raise ValueError("Hardlinked Git control file")
    return _read_regular(path, limit=limit)


def _environment():
    allowed = {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "TMPDIR", "COMSPEC", "PATHEXT"}
    env = {k: v for k, v in os.environ.items() if k.upper() in allowed}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_SYSTEM=os.devnull,
               GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never",
               GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1", GIT_ATTR_NOSYSTEM="1", LC_ALL="C")
    return env


def _git(root, executable, *arguments):
    command = [executable, "--no-pager", "-c", "core.hooksPath=" + os.devnull,
               "-c", "core.fsmonitor=false", "-c", "submodule.recurse=false",
               "-c", "gc.auto=0", "-c", "maintenance.auto=false",
               "-c", "core.sparseCheckout=false", "-c", "worktree.useRelativePaths=false",
               "-C", str(root), *arguments]
    try:
        # Disk-backed capture bounds parsed memory; no claim of a hard disk quota.
        with tempfile.TemporaryFile() as output:
            subprocess.run(command, env=_environment(), stdin=subprocess.DEVNULL,
                           stdout=output, stderr=subprocess.DEVNULL, timeout=GIT_TIMEOUT,
                           check=True)
            if output.tell() > MAX_GIT_OUTPUT:
                raise ValueError("Excessive Git output")
            output.seek(0)
            return output.read(MAX_GIT_OUTPUT + 1)
    except (OSError, subprocess.SubprocessError) as exc:
        raise SafeOpsError(_ERROR) from exc


def _entries(root, raw, *, index=False):
    result, folded = {}, set()
    for entry in raw.split(b"\0")[:-1]:
        prefix, path = entry.decode("utf-8").split("\t", 1)
        mode, middle, last = prefix.split(" ")
        oid = middle if index else last
        if (mode not in ("100644", "100755") or (last != "0" if index else middle != "blob") or
                not re.fullmatch(r"[0-9a-f]{40}", oid) or path.casefold() in folded or
                len(result) >= MAX_FILES or len(path) > 1024 or
                any(p in SKIP_DIRS or p.casefold() == ".env" or p.casefold().startswith(".env.")
                    for p in path.split("/")) or validate_scope_paths(root, [path]) != [path]):
            raise ValueError("Unsupported tracked entry")
        folded.add(path.casefold())
        result[path] = {"mode": mode, "oid": oid}
    if not raw.endswith(b"\0") or not result:
        raise ValueError("Empty or incomplete tracked entries")
    return result


def validate_context(value, root):
    current = shutil.which("git")
    if (not isinstance(value, dict) or set(value) != _FIELDS or type(value["schema"]) is not int or
            value["schema"] != 1 or value["git_dir"] != str(root / ".git") or
            not isinstance(value["executable"], str) or not Path(value["executable"]).is_absolute() or
            len(value["executable"]) > 1024 or not current or
            value["executable"] != str(Path(current).resolve(strict=True)) or
            not re.fullmatch(r"[0-9a-f]{40}", value["commit"]) or
            any(not isinstance(value[k], str) or not re.fullmatch(r"[0-9a-f]{64}", value[k])
                for k in _FIELDS - {"schema", "git_dir", "executable", "commit"})):
        raise ValueError("Invalid Git context")


def _repository(root):
    directory = root / ".git"
    identity = _directory(directory)
    executable = shutil.which("git")
    if not executable or len(str(root)) > 1024 or any(ord(c) < 32 for c in str(root)):
        raise ValueError("Git unavailable or unsupported root")
    executable = str(Path(executable).resolve(strict=True))
    config, index, head = (_raw(directory / n) for n in ("config", "index", "HEAD"))
    if (re.search(rb"(?im)^\s*\[\s*include(?:if)?\b", config) or
            (directory / "config.worktree").exists() or (directory / "config.worktree").is_symlink()):
        raise ValueError("Extended configuration unsupported")
    if (Path(os.fsdecode(_git(root, executable, "rev-parse", "--show-toplevel")).strip()).resolve() != root or
            Path(os.fsdecode(_git(root, executable, "rev-parse", "--absolute-git-dir")).strip()).resolve() != directory):
        raise ValueError("Main repository required")
    commit = _git(root, executable, "rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Initial support requires SHA-1 repositories")
    entries = _entries(root, _git(root, executable, "ls-tree", "-r", "-z", "--full-tree", commit))
    if _entries(root, _git(root, executable, "ls-files", "--stage", "-z"), index=True) != entries:
        raise ValueError("Index differs from committed base")
    included = {}
    total = 0
    for path in source_files(root):
        relative = path.relative_to(root).as_posix()
        if any(p.casefold() == ".env" or p.casefold().startswith(".env.") for p in relative.split("/")):
            continue
        if relative not in entries or path.lstat().st_nlink != 1:
            raise ValueError("Untracked or hardlinked source")
        raw = _read_regular(path, limit=MAX_FILE_BYTES)
        total += len(raw)
        if total > 64_000_000:
            raise ValueError("Copy budget exceeded")
        oid = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if oid != entries[relative]["oid"]:
            raise ValueError("Literal source differs from commit")
        included[relative] = entries[relative]
    if included != entries or _directory(directory) != identity:
        raise ValueError("Incomplete or changed repository")
    value = {"schema": 1, "git_dir": str(directory), "executable": executable, "commit": commit,
             "tracked_sha256": sha256(entries), "refs_sha256": hashlib.sha256(
                 _git(root, executable, "for-each-ref", "--format=%(refname)%00%(objectname)")).hexdigest()}
    for name, raw in (("config", config), ("index", index), ("head", head)):
        if _raw(directory / ("HEAD" if name == "head" else name)) != raw:
            raise ValueError("Git context changed")
        value[name + "_sha256"] = hashlib.sha256(raw).hexdigest()
    validate_context(value, root)
    return value, entries


def review_git_stage(root, proposal_id):
    try:
        proposal = review_proposal(root, proposal_id)
        context, _ = _repository(root)
        if review_proposal(root, proposal_id) != proposal or _repository(root)[0] != context:
            raise ValueError("Review changed")
        result = {"schema": 1, "status": "git-stage-review", "safeops_version": __version__,
                  "proposal_id": proposal_id, "proposal_fingerprint": proposal["fingerprint"],
                  "git": context, "policy": POLICY,
                  "notice": "Review local shared Git metadata mutation; no worktree, approval or checks created"}
        result["fingerprint"] = sha256(result)
        return result
    except (SafeOpsError, OSError, ValueError, TypeError, KeyError, UnicodeError, RecursionError) as exc:
        raise SafeOpsError(_ERROR) from exc


def create_link(root, destination, context):
    if _repository(root)[0] != context:
        raise SafeOpsError(_ERROR)
    _git(root, context["executable"], "worktree", "add", "--detach", "--no-checkout", "--lock",
         "--reason", "SafeOps stage " + destination.parent.name, str(destination), context["commit"])
    _git(destination, context["executable"], "read-tree", "--no-sparse-checkout", context["commit"])
    return _entries(root, _git(root, context["executable"], "ls-tree", "-r", "-z", "--full-tree", context["commit"]))


def inspect_link(root, destination, context):
    validate_context(context, root)
    directory = root / ".git"
    _directory(directory)
    _directory(directory / "worktrees")
    raw = _raw(destination / ".git", 4096).decode("utf-8")
    if not raw.startswith("gitdir: ") or not raw.endswith("\n"):
        raise ValueError("Invalid Git pointer")
    admin = Path(raw[8:].strip())
    if not admin.is_absolute() or admin.parent != directory / "worktrees":
        raise ValueError("Foreign Git pointer")
    _directory(admin)
    if (Path(_raw(admin / "gitdir", 4096).decode().strip()) != destination / ".git" or
            (admin / _raw(admin / "commondir", 4096).decode().strip()).resolve() != directory or
            _raw(admin / "locked", 4096).decode().strip() != "SafeOps stage " + destination.parent.name):
        raise ValueError("Broken Git linkage")
    executable = context["executable"]
    if (_git(destination, executable, "rev-parse", "--verify", "HEAD^{commit}").decode().strip() != context["commit"] or
            _git(destination, executable, "rev-parse", "--symbolic-full-name", "HEAD").strip() != b"HEAD"):
        raise ValueError("Git base changed")
    entries = _entries(destination, _git(destination, executable, "ls-files", "--stage", "-z"), index=True)
    if sha256(entries) != context["tracked_sha256"]:
        raise ValueError("Git index changed")
    return {"mode": POLICY["mode"], "commit": context["commit"], "tracked_sha256": sha256(entries)}


def stage_git_proposal(root, proposal_id, confirmation):
    from .locking import execution_lock
    from .proposals import _load
    from .staging import stage_proposal
    reviewed = review_git_stage(root, proposal_id)
    if confirmation != reviewed["fingerprint"]:
        raise SafeOpsError("Git staging requires --confirm matching the exact review-git-stage fingerprint")
    with execution_lock(root, _load(root, proposal_id)["bindings"]["plan_id"]):
        if review_git_stage(root, proposal_id) != reviewed:
            raise SafeOpsError(_ERROR)
        return stage_proposal(root, proposal_id, reviewed["proposal_fingerprint"], _git_context=reviewed["git"])
