"""Small native Windows job owner; no process enumeration or fallback."""

from __future__ import annotations

import ctypes
from ctypes import wintypes as w
import os


class _BasicLimits(ctypes.Structure):
    _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                ("flags", w.DWORD), ("minimum", ctypes.c_size_t), ("maximum", ctypes.c_size_t),
                ("active_limit", w.DWORD), ("affinity", ctypes.c_size_t),
                ("priority", w.DWORD), ("scheduling", w.DWORD)]


class _IO(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]


class _Limits(ctypes.Structure):
    _fields_ = [("basic", _BasicLimits), ("io", _IO), ("process_memory", ctypes.c_size_t),
                ("job_memory", ctypes.c_size_t), ("peak_process_memory", ctypes.c_size_t),
                ("peak_job_memory", ctypes.c_size_t)]


class _Accounting(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int64) for name in ("user", "kernel", "period_user", "period_kernel")] + [
        (name, w.DWORD) for name in ("faults", "total", "active", "terminated")]


class Job:
    def __init__(self):
        if os.name != "nt":
            raise OSError("Windows jobs unavailable")
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateJobObjectW": ([ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
            "SetInformationJobObject": ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
            "AssignProcessToJobObject": ([w.HANDLE, w.HANDLE], w.BOOL),
            "QueryInformationJobObject": ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p], w.BOOL),
            "TerminateJobObject": ([w.HANDLE, w.UINT], w.BOOL),
            "CloseHandle": ([w.HANDLE], w.BOOL),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self.api, name)
            function.argtypes, function.restype = args, result
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise OSError("Cannot allocate native job")
        try:
            limits = _Limits()
            limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway.
            if not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
                raise OSError("Cannot configure native job")
        except BaseException:
            self.close()
            raise

    def assign(self, process) -> None:
        # CPython keeps the original native process handle, unlike a PID lookup.
        handle = getattr(process, "_handle", None)
        if handle is None or not self.api.AssignProcessToJobObject(self.handle, int(handle)):
            raise OSError("Cannot assign gated launcher to native job")

    def active(self) -> int:
        information = _Accounting()
        if not self.api.QueryInformationJobObject(self.handle, 1, ctypes.byref(information), ctypes.sizeof(information), None):
            raise OSError("Cannot inspect native job")
        return information.active

    def terminate(self) -> None:
        if not self.api.TerminateJobObject(self.handle, 1):
            raise OSError("Cannot terminate native job")

    def close(self) -> None:
        if self.handle:
            handle, self.handle = self.handle, None
            if not self.api.CloseHandle(handle):
                raise OSError("Cannot release native job")
