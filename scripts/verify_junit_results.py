#!/usr/bin/env python3
"""Fail closed if hosted Gradle reports zero or failing *production* JVM tests."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

EXPECTED_SUITE = "Telegram.Speed.Hook.SpeedPolicyTest"
REQUIRED_TESTS = {
    "bigFileGetsEveryParameter", "belowThresholdSkipsWithoutMutation",
    "exactThresholdIsEligible", "unknownSizeFollowsLegacyDefault",
    "forceSmallChunkNeverMutates", "preloadNeverMutates", "streamNeverMutates",
    "repeatedApplicationIsIdempotent", "absentOrWronglyTypedForkFieldsFailOpenSafely",
    "nullOperationIsIgnored",
}


def verify(folder: Path) -> tuple[int, int]:
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("missing/unsafe Gradle JUnit result directory")
    result_files = sorted(folder.glob("TEST-*.xml"))
    if not result_files:
        raise ValueError("no JUnit XML reports (empty Gradle test task)")
    found: set[str] = set()
    total = 0
    for p in result_files:
        if not p.is_file() or p.is_symlink():
            raise ValueError("unsafe JUnit XML report")
        suite = ET.parse(p).getroot()
        if suite.tag != "testsuite":
            raise ValueError("invalid Gradle JUnit suite")
        name = suite.attrib.get("name", "")
        for case in suite.findall("testcase"):
            total += 1
            if case.find("failure") is not None or case.find("error") is not None or case.find("skipped") is not None:
                raise ValueError(f"failed/errored/skipped test: {case.attrib.get('name')}")
            if name == EXPECTED_SUITE and case.attrib.get("classname", name) == EXPECTED_SUITE:
                found.add(case.attrib.get("name", ""))
    if total < len(REQUIRED_TESTS) or not REQUIRED_TESTS <= found:
        raise ValueError("missing actual SpeedPolicyTest executions: " + ", ".join(sorted(REQUIRED_TESTS - found)))
    return total, len(found)


if __name__ == "__main__":
    try:
        total, required = verify(Path(sys.argv[1] if len(sys.argv) == 2 else "app/build/test-results/testDebugUnitTest"))
    except (OSError, ValueError, ET.ParseError) as exc:
        print(f"FAIL_HOSTED_JUNIT: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"PASS_HOSTED_JUNIT: executed={total} policy_cases={required}")
