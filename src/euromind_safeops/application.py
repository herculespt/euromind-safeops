"""Explicit reviewed application and conservative journal-backed restoration."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import secrets

from . import __version__
from . import application_journal as journal
from .core import SafeOpsError, audit, decode_json_object, sha256, utc_now
from .execution import execution_contract_digest, validate_config
from .locking import _guard, _marker, application_pending, lock_status
from .preview import MAX_BYTES, MAX_TOTAL_BYTES, _text
from .proposals import _load
from .run_receipts import inspect_run, stable_context
from .stage_inspection import _directory, _hex, inspect_stage
from .stage_review import _read, _source_snapshot, _target_manifest, review_stage

_ERRORS = (SafeOpsError, OSError, ValueError, TypeError, KeyError, UnicodeError,
           RecursionError, OverflowError, IndexError)


def _idle(root: Path, *, guarded: bool = False, allow_pending: bool = False) -> None:
    state = root / ".safeops"
    _directory(state)
    if _marker(state) is not None or not allow_pending and application_pending(state):
        raise ValueError("Retained operation marker")
    if not guarded and lock_status(root)["guard"] == "busy":
        raise ValueError("Native guard busy")


def _review(root: Path, stage_id: str, run_id: str, *, guarded: bool) -> dict:
    if not _hex(stage_id, 12) or not _hex(run_id, 12):
        raise ValueError("Invalid stage or run ID")
    _idle(root, guarded=guarded)
    compatibility = review_stage(root, stage_id)
    if compatibility["status"] != "current":
        raise ValueError("Original context is not current")
    stage = inspect_stage(root, stage_id)
    copied = root / ".safeops/stages" / stage_id / "workspace"
    _idle(copied, guarded=guarded)
    run = inspect_run(copied, run_id)
    if (run["status"] != "passed" or not run["version_matches"] or
            set(run["expected_checks"]) != {"compile", "unit-tests"} or
            {c["check"] for c in run["checks"] if c["status"] == "passed"} != {"compile", "unit-tests"}):
        raise ValueError("Both staged checks must have passed under this version")
    context, staged_plan, approved, config = stable_context(copied, run["plan_id"])
    if (context != run["bindings"] or context != run["end_context"] or
            context["workspace_digest"] != stage["observed_workspace_digest"] or
            staged_plan["risk"] == "critical" or staged_plan["workspace_digest"] != context["workspace_digest"] or
            type(approved.get("schema")) is not int or approved["schema"] != 2 or
            approved.get("plan_id") != run["plan_id"] or
            approved.get("fingerprint") != staged_plan["fingerprint"] or
            approved.get("workspace_digest") != context["workspace_digest"] or
            approved.get("config_digest") != context["config_digest"] or
            approved.get("execution_contract") != execution_contract_digest() or
            config["schema"] == 2 and approved.get("targets_digest") != context["targets_digest"]):
        raise ValueError("Staged execution context changed")
    proposal = _load(root, compatibility["proposal_id"])
    source_config_path = root / ".safeops/config.json"
    source_config = validate_config(root, decode_json_object(_read(root, source_config_path, 256_000)))
    if source_config != config:
        raise ValueError("Staged checks must use the original configuration")
    files, before_bytes, replacement_bytes, total = [], [], [], 0
    for entry in sorted(proposal["candidate"]["files"], key=lambda e: e["path"]):
        observed, raw = journal.observe_file(root, root / entry["path"])
        journal._info(observed)
        _text(raw)
        after = entry["content"].encode("utf-8")
        _text(after)
        total += len(raw) + len(after)
        if observed["sha256"] != entry["base_sha256"] or len(after) > MAX_BYTES or total > MAX_TOTAL_BYTES:
            raise ValueError("Candidate base or budget changed")
        files.append({"path": entry["path"], "before": observed,
                      "replacement_sha256": hashlib.sha256(after).hexdigest(), "replacement_bytes": len(after)})
        before_bytes.append(raw)
        replacement_bytes.append(after)
    source_files, digest = _source_snapshot(root)
    targets = _target_manifest(root, source_config)
    if digest != compatibility["observed_source_workspace_digest"]:
        raise ValueError("Original snapshot changed")
    plan_id = proposal["bindings"]["plan_id"]
    controls = [(source_config_path, 256_000),
                (root / ".safeops/plans" / (plan_id + ".json"), 256_000),
                (root / ".safeops/proposals" / (proposal["id"] + ".json"), 260_096)]
    control_hashes = [hashlib.sha256(_read(root, p, limit)).hexdigest() for p, limit in controls]
    public = {"schema": 1, "safeops_version": __version__, "stage_id": stage_id, "run_id": run_id,
              "plan_id": plan_id, "proposal_id": proposal["id"], "proposal_fingerprint": proposal["fingerprint"],
              "stage_receipt_fingerprint": stage["receipt_fingerprint"], "run_receipt_fingerprint": run["receipt_fingerprint"],
              "source_digest": digest, "source_controls_digest": sha256(control_hashes),
              "staged_context_digest": sha256(context), "files": files,
              "metadata_policy": "basic-mode-and-posix-owner-group; no ACL/xattr/timestamp preservation"}
    public["fingerprint"] = sha256(public)
    return {"public": public, "before_bytes": before_bytes, "replacement_bytes": replacement_bytes,
            "source_files": source_files, "targets": targets, "source_config": source_config,
            "controls": controls, "control_hashes": control_hashes, "stage": stage,
            "run": run, "staged_context": context, "copied": copied}


def _stable_review(root: Path, stage_id: str, run_id: str, *, guarded: bool = False) -> dict:
    reviewed = _review(root, stage_id, run_id, guarded=guarded)
    if _review(root, stage_id, run_id, guarded=guarded)["public"] != reviewed["public"]:
        raise ValueError("Application inputs changed during review")
    return reviewed


def review_application(root: Path, stage_id: str, run_id: str) -> dict:
    try:
        return {**_stable_review(root.resolve(strict=True), stage_id, run_id)["public"],
                "notice": "Review only; repeat this exact fingerprint to authorize listed original replacements"}
    except _ERRORS as exc:
        raise SafeOpsError("Application review failed: unsafe, stale, incomplete, changing or oversized evidence") from exc


def _pending(root: Path, manifest: dict, *, create: bool = False) -> None:
    path = root / ".safeops/application.pending"
    if create:
        journal.write_bytes(root, path, journal.marker_bytes(manifest))
    elif _read(root, path, 4096) != journal.marker_bytes(manifest):
        raise ValueError("Pending marker changed")


def _clear_pending(root: Path, manifest: dict) -> None:
    path = root / ".safeops/application.pending"
    before = journal.observe_file(root, path)[0]
    _pending(root, manifest)
    if journal.observe_file(root, path)[0] != before:
        raise ValueError("Pending marker changed before release")
    path.unlink()


def _install(root: Path, prepared: Path, target: Path, before: dict, after: dict) -> dict:
    current, _ = journal.observe_file(root, target)
    replacement, _ = journal.observe_file(root, prepared)
    if (not journal.same_file(current, before, stamps=True) or
            not journal.same_file(replacement, after, stamps=True) or
            current["identity"][0] != replacement["identity"][0]):
        raise ValueError("Replacement ownership, source or filesystem changed")
    os.replace(prepared, target)
    observed, _ = journal.observe_file(root, target)
    if not journal.same_file(observed, after):
        raise ValueError("Installed file differs")
    return observed


def _progress(root: Path, manifest: dict, reviewed: dict, expected_files: dict,
              targets: list | None, observations: list[dict]) -> None:
    _idle(root, guarded=True, allow_pending=True)
    _idle(reviewed["copied"], guarded=True)
    result, loaded, private = journal.read_journal(root, manifest["id"])
    if (loaded != manifest or result["completion"] is not None or result["pending_owner"] != "self" or
            private["identities"] != reviewed["journal_identities"] or
            [f["observed"] for f in result["files"]] != observations or
            _source_snapshot(root)[0] != expected_files or
            _target_manifest(root, reviewed["source_config"]) != targets or
            [hashlib.sha256(_read(root, p, limit)).hexdigest() for p, limit in reviewed["controls"]] != reviewed["control_hashes"] or
            inspect_stage(root, manifest["stage_id"]) != reviewed["stage"] or
            inspect_run(reviewed["copied"], manifest["run_id"]) != reviewed["run"] or
            stable_context(reviewed["copied"], reviewed["run"]["plan_id"])[0] != reviewed["staged_context"]):
        raise ValueError("Application progress differs from reviewed inputs")
    _pending(root, manifest)


def _terminal(root: Path, manifest: dict, status: str, observations: list[dict]) -> None:
    owned = root / ".safeops/applications" / manifest["id"]
    audit(root, "apply-stage" if status == "applied" else "rollback-application",
          manifest["plan_id"], status + ":" + manifest["id"], require_config=status == "applied")
    journal.write_record(root, owned / (status + ".json"),
                         {"schema": 1, "id": manifest["id"], "intent_fingerprint": manifest["fingerprint"],
                          "finished_at": utc_now(), "status": status, "files": observations})


def apply_stage(root: Path, stage_id: str, run_id: str, confirmation: str) -> dict:
    application_id = None
    try:
        root = root.resolve(strict=True)
        if not _hex(confirmation):
            raise ValueError("Exact review fingerprint required")
        reviewed = _stable_review(root, stage_id, run_id)
        if confirmation != reviewed["public"]["fingerprint"]:
            raise ValueError("Review fingerprint differs")
        with _guard(root / ".safeops"), _guard(reviewed["copied"] / ".safeops"):
            reviewed = _stable_review(root, stage_id, run_id, guarded=True)
            if confirmation != reviewed["public"]["fingerprint"]:
                raise ValueError("Review changed before guards")
            history = root / ".safeops/applications"
            history.mkdir(mode=0o700, exist_ok=True)
            _directory(history)
            application_id = secrets.token_hex(6)
            owned = history / application_id
            owned.mkdir(mode=0o700)
            reviewed["journal_identities"] = [_directory(p) for p in (root / ".safeops", history, owned)]
            entries = []
            for i, entry in enumerate(reviewed["public"]["files"]):
                journal.write_bytes(root, owned / f"backup-{i:03d}.bin", reviewed["before_bytes"][i])
                prepared = journal.write_bytes(root, owned / f"new-{i:03d}.bin", reviewed["replacement_bytes"][i], metadata=entry["before"])
                if prepared["identity"][0] != entry["before"]["identity"][0]:
                    raise ValueError("Cross-filesystem application unsupported")
                entries.append({"path": entry["path"], "before": entry["before"], "after": prepared})
            public = reviewed["public"]
            manifest = {"schema": 1, "id": application_id, "created_at": utc_now(), "safeops_version": __version__,
                        "stage_id": stage_id, "run_id": run_id, "plan_id": public["plan_id"], "proposal_id": public["proposal_id"],
                        "review_fingerprint": confirmation, "proposal_fingerprint": public["proposal_fingerprint"],
                        "stage_receipt_fingerprint": public["stage_receipt_fingerprint"],
                        "run_receipt_fingerprint": public["run_receipt_fingerprint"], "files": entries}
            manifest = journal.write_record(root, owned / "intent.json", manifest)
            journal._manifest(root, manifest, application_id)
            _pending(root, manifest, create=True)
            expected_files = dict(reviewed["source_files"])
            targets = None if reviewed["targets"] is None else [list(v) for v in reviewed["targets"]]
            observations = [e["before"] for e in entries]
            for i, entry in enumerate(entries):
                _progress(root, manifest, reviewed, expected_files, targets, observations)
                observations[i] = _install(root, owned / f"new-{i:03d}.bin", root / entry["path"], observations[i], entry["after"])
                expected_files[entry["path"]] = entry["after"]["sha256"]
                if targets is not None:
                    for item in targets:
                        if item[0] == entry["path"]:
                            item[1] = entry["after"]["sha256"]
            _progress(root, manifest, reviewed, expected_files, targets, observations)
            _terminal(root, manifest, "applied", observations)
            _clear_pending(root, manifest)
        return journal.inspect_application(root, application_id)
    except _ERRORS as exc:
        detail = f"Application {application_id} did not complete; inspect retained journal" if application_id else "Application refused before journal allocation"
        raise SafeOpsError(detail) from exc


def rollback_application(root: Path, application_id: str, confirmation: str) -> dict:
    try:
        root = root.resolve(strict=True)
        reviewed = journal.inspect_application(root, application_id)
        if not reviewed["rollback_candidate"] or confirmation != reviewed["rollback_fingerprint"]:
            raise ValueError("Rollback requires the exact fresh conflict-free inspection fingerprint")
        with _guard(root / ".safeops"):
            _idle(root, guarded=True, allow_pending=True)
            if journal.inspect_application(root, application_id) != reviewed:
                raise ValueError("Rollback inputs changed before guard")
            if reviewed["status"] == "rolled-back":
                return reviewed
            _, manifest, private = journal.read_journal(root, application_id)
            identities = private["identities"]
            if reviewed["pending_owner"] == "absent":
                _pending(root, manifest, create=True)
            else:
                _pending(root, manifest)
            owned = root / ".safeops/applications" / application_id
            observations = [f["observed"] for f in reviewed["files"]]
            for i in reversed(range(len(manifest["files"]))):
                _idle(root, guarded=True, allow_pending=True)
                current, loaded, private = journal.read_journal(root, application_id)
                if (loaded != manifest or private["identities"] != identities or
                        [f["observed"] for f in current["files"]] != observations):
                    raise ValueError("Rollback source or journal changed")
                _pending(root, manifest)
                if current["files"][i]["state"] in {"original", "restored"}:
                    continue
                if current["files"][i]["state"] != "applied":
                    raise ValueError("Rollback refuses concurrent edits")
                prepared = private["restores"].get(i)
                if prepared is None:
                    prepared = journal.write_bytes(root, owned / f"restore-{i:03d}.bin", private["backups"][i], metadata=manifest["files"][i]["before"])
                    journal.write_record(root, owned / f"restore-{i:03d}.json",
                                         {"schema": 1, "id": application_id, "intent_fingerprint": manifest["fingerprint"],
                                          "index": i, "prepared": prepared})
                observations[i] = _install(root, owned / f"restore-{i:03d}.bin", root / manifest["files"][i]["path"], observations[i], prepared)
            final, loaded, private = journal.read_journal(root, application_id)
            if (loaded != manifest or private["identities"] != identities or
                    [f["observed"] for f in final["files"]] != observations or
                    any(f["state"] not in {"original", "restored"} for f in final["files"])):
                raise ValueError("Rollback final state changed")
            if final["completion"] != "rolled-back":
                _terminal(root, manifest, "rolled-back", observations)
            _clear_pending(root, manifest)
        return journal.inspect_application(root, application_id)
    except _ERRORS as exc:
        raise SafeOpsError("Rollback refused or interrupted; inspect retained journal and current files") from exc
