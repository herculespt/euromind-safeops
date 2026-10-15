"""Opt-in directory target selection for trusted fixed checks, not isolation."""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path, PurePosixPath

from .check_runner import main as run_tests
from .core import SafeOpsError
from .scope import validate_scope_paths

TARGET_COMMAND = ["-m", "euromind_safeops.target_runner"]
MAX_ENTRIES = 5000
MAX_SOURCE_BYTES = 12_000_000


def validate_targets(root: Path, check: str, paths: list[str], *, all_files: bool = False) -> list[Path]:
    """Inspect metadata only; return selected Python sources (or all files) in stable order.

    All descendants are inspected, including generated directories. No paths
    are silently pruned. A concurrent filesystem mutation can still race this.
    """
    if check not in {"compile", "unit-tests"}:
        raise SafeOpsError("Invalid target check")
    canonical = validate_scope_paths(root, paths)
    if not canonical or canonical != paths or "." in canonical:
        raise SafeOpsError("Targets require nonempty canonical subdirectory paths")
    if check == "unit-tests" and len(canonical) != 1:
        raise SafeOpsError("unit-tests requires exactly one target directory")
    folded = [PurePosixPath(p.casefold()) for p in canonical]
    for index, path in enumerate(folded):
        if any(path == other or path in other.parents or other in path.parents
               for other in folded[:index]):
            raise SafeOpsError("Target directories must not overlap or alias")
    sources = []
    python_sources = 0
    entries = 0
    try:
        root = root.resolve(strict=True)
        for path in canonical:
            start = root / path
            if not start.is_dir():
                raise SafeOpsError("Targets must be existing directories")
            pending = [start]
            while pending:
                directory = pending.pop()
                # Recheck directory metadata before each descent.
                info = directory.lstat()
                if (stat.S_ISLNK(info.st_mode) or
                        getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT or
                        not stat.S_ISDIR(info.st_mode)):
                    raise SafeOpsError("Unsafe target directory")
                with os.scandir(directory) as children:
                    for child in children:
                        entries += 1
                        if entries > MAX_ENTRIES:
                            raise SafeOpsError("Target metadata limit exceeded (5000 entries)")
                        info = child.stat(follow_symlinks=False)
                        if (stat.S_ISLNK(info.st_mode) or
                                getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                            raise SafeOpsError("Targets cannot contain links or reparse points")
                        if stat.S_ISDIR(info.st_mode):
                            pending.append(Path(child.path))
                        elif stat.S_ISREG(info.st_mode):
                            if info.st_size > MAX_SOURCE_BYTES:
                                raise SafeOpsError("Selected file exceeds 12000000 bytes")
                            if child.name.endswith(".py"):
                                python_sources += 1
                            if all_files or child.name.endswith(".py"):
                                sources.append(Path(child.path))
                        else:
                            raise SafeOpsError("Targets require regular files and directories")
    except (OSError, RuntimeError) as exc:
        raise SafeOpsError("Cannot inspect target directories") from exc
    if check == "compile" and not python_sources:
        raise SafeOpsError("No Python sources in compile targets")
    return sorted(sources)


def main(arguments: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if arguments is None else arguments
    try:
        if not arguments:
            raise SafeOpsError("A fixed check and target directories are required")
        check, *paths = arguments
        root = Path.cwd()
        sources = validate_targets(root, check, paths)
        if check == "unit-tests":
            return run_tests(str(root / paths[0]))
        for source in sources:
            # Compile in memory: no imports, bytecode files or directory writes.
            with source.open("rb") as handle:
                content = handle.read(MAX_SOURCE_BYTES + 1)
                if len(content) > MAX_SOURCE_BYTES:
                    raise SafeOpsError("Selected Python source exceeds 12000000 bytes")
                compile(content, str(source), "exec", dont_inherit=True)
        print(f"SafeOps: compiled {len(sources)} selected Python sources")
        return 0
    except SafeOpsError as exc:
        print(f"SafeOps: {exc}", file=sys.stderr)
        return 2
    except (OSError, SyntaxError, ValueError) as exc:
        print(f"SafeOps: selected compilation failed ({type(exc).__name__})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
