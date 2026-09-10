#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def version_tuple(value: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", value)
    if not parts:
        fail(f"cannot parse version: {value!r}")
    return tuple(int(p) for p in parts)


def at_least(actual: str, minimum: str) -> bool:
    a = version_tuple(actual)
    b = version_tuple(minimum)
    width = max(len(a), len(b))
    return a + (0,) * (width - len(a)) >= b + (0,) * (width - len(b))


def require_match(text: str, pattern: str, label: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        fail(f"could not determine {label}")
    return match.group(1)


root_build = (ROOT / "build.gradle").read_text(encoding="utf-8")
app_build = (ROOT / "app" / "build.gradle").read_text(encoding="utf-8")
wrapper = (ROOT / "gradle" / "wrapper" / "gradle-wrapper.properties").read_text(encoding="utf-8")

agp = require_match(
    root_build,
    r"id\s+['\"]com\.android\.application['\"]\s+version\s+['\"]([^'\"]+)['\"]",
    "Android Gradle Plugin version",
)
gradle = require_match(wrapper, r"gradle-([0-9][0-9A-Za-z.\-]*)-bin\.zip", "Gradle wrapper version")
compile_sdk = require_match(app_build, r"\bcompileSdk\s*(?:=\s*)?(\d+)", "compileSdk")
min_sdk = require_match(app_build, r"\bminSdk\s*(?:=\s*)?(\d+)", "minSdk")
target_sdk = require_match(app_build, r"\btargetSdk\s*(?:=\s*)?(\d+)", "targetSdk")
build_tools = require_match(app_build, r"\bbuildToolsVersion\s*(?:=\s*)?['\"]([^'\"]+)['\"]", "Build Tools version")
ndk = require_match(app_build, r"\bndkVersion\s*(?:=\s*)?['\"]([^'\"]+)['\"]", "NDK version")
source_java = require_match(app_build, r"sourceCompatibility\s*(?:=\s*)?JavaVersion\.VERSION_(\d+)", "Java source compatibility")
target_java = require_match(app_build, r"targetCompatibility\s*(?:=\s*)?JavaVersion\.VERSION_(\d+)", "Java target compatibility")

requirements = [
    ("Gradle", gradle, "9.7"),
    ("Android Gradle Plugin", agp, "9.3.1"),
    ("compileSdk", compile_sdk, "36"),
    ("minSdk", min_sdk, "26"),
    ("targetSdk", target_sdk, "36"),
    ("Android Build Tools", build_tools, "36.0.0"),
    ("Android NDK", ndk, "29"),
    ("Java source compatibility", source_java, "21"),
    ("Java target compatibility", target_java, "21"),
]

for label, actual, minimum in requirements:
    if not at_least(actual, minimum):
        fail(f"{label} {actual} is below required baseline {minimum}")

print("Toolchain baseline OK")
print(f"  Gradle: {gradle} (>= 9.7)")
print(f"  AGP: {agp} (>= 9.3.1)")
print(f"  Java source/target: {source_java}/{target_java} (>= 21)")
print(f"  compileSdk/targetSdk: {compile_sdk}/{target_sdk} (>= 36)")
print(f"  minSdk: {min_sdk} (>= 26 for libxposed API 102)")
print(f"  Build Tools: {build_tools} (>= 36.0.0)")
print(f"  NDK: {ndk} (>= 29)")
