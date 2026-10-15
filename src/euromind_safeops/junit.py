"""Minimal JUnit dialect: synthetic identifiers and fixed outcome categories only."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from . import __version__


class OutcomeResult(unittest.TextTestResult):
    """Retain ordinary console diagnostics, collect no test-supplied report text."""

    def __init__(self, *args, outcomes: list[str], **kwargs):
        super().__init__(*args, **kwargs)
        self.outcomes = outcomes

    def addSuccess(self, test):
        super().addSuccess(test)
        self.outcomes.append("passed")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.outcomes.append("failure")

    def addError(self, test, err):
        super().addError(test, err)
        self.outcomes.append("error")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.outcomes.append("skipped")

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.outcomes.append("expected-failure")

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.outcomes.append("unexpected-success")

    def addSubTest(self, test, subtest, err):
        failures = len(self.failures)
        super().addSubTest(test, subtest, err)
        if err is not None:
            self.outcomes.append("failure" if len(self.failures) > failures else "error")


def write_report(destination: Path, outcomes: list[str], code: int, phase: str) -> None:
    """Atomically replace the selected local report; never create its parent."""
    rows = list(outcomes)
    if code == 2:
        rows.append("runner-error")
    # Only fixed strings/numbers are serialized. Even custom test identifiers,
    # subtest parameters and exceptions containing invalid XML stay in logs.
    mapping = {"passed": None, "failure": "failure", "error": "error",
               "skipped": "skipped", "expected-failure": "skipped",
               "unexpected-success": "failure", "runner-error": "error"}
    tags = [mapping[row] for row in rows]
    counts = {"tests": str(len(rows)), "failures": str(tags.count("failure")),
              "errors": str(tags.count("error")), "skipped": str(tags.count("skipped"))}
    root = ET.Element("testsuites", counts)
    suite = ET.SubElement(root, "testsuite", {"name": "safeops-unittest", **counts})
    properties = ET.SubElement(suite, "properties")
    for name, value in (("safeops_version", __version__), ("report_schema", "1"),
                        ("phase", phase), ("check_exit_code", str(code))):
        ET.SubElement(properties, "property", {"name": name, "value": value})
    for number, (row, tag) in enumerate(zip(rows, tags), 1):
        case = ET.SubElement(suite, "testcase", {"classname": "safeops.unittest", "name": f"case-{number}"})
        if tag:
            ET.SubElement(case, tag, {"type": row})
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=destination.parent,
                                         prefix=".safeops-junit-", delete=False) as handle:
            temporary = Path(handle.name)
            ET.ElementTree(root).write(handle, encoding="utf-8", xml_declaration=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
