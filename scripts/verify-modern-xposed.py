#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY = "Telegram.Speed.Hook.MainHook"
SCOPES = ["org.telegram.messenger", "top.qwq2333.nullgram"]
META_ROOT = ROOT / "app" / "src" / "main" / "resources" / "META-INF" / "xposed"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read(path: Path) -> str:
    require(path.is_file(), f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def nonblank_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def parse_properties(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in nonblank_lines(text):
        if "=" not in line:
            fail(f"invalid module.prop line: {line!r}")
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


build_gradle = read(ROOT / "app" / "build.gradle")
manifest = read(ROOT / "app" / "src" / "main" / "AndroidManifest.xml")
hook = read(ROOT / "app" / "src" / "main" / "java" / "Telegram" / "Speed" / "Hook" / "MainHook.java")
proguard = read(ROOT / "app" / "proguard-rules.pro")
java_init = read(META_ROOT / "java_init.list")
scope_list = read(META_ROOT / "scope.list")
module_prop = read(META_ROOT / "module.prop")

require("io.github.libxposed:api:102.0.0" in build_gradle, "libxposed API 102.0.0 compileOnly dependency is missing")
require("de.robv.android.xposed" not in build_gradle, "legacy Xposed API dependency remains in app/build.gradle")
require(re.search(r"\bminSdk\s*(?:=\s*)?26\b", build_gradle) is not None, "minSdk must be 26 for libxposed API 102")
require(re.search(r"\bndkVersion\s*(?:=\s*)?['\"]29\.0\.14206865['\"]", build_gradle) is not None, "current reproducible NDK r29 pin is missing")

require("extends XposedModule" in hook, "MainHook does not extend XposedModule")
require("onModuleLoaded(" in hook, "MainHook is missing onModuleLoaded lifecycle handling")
require("onPackageReady(" in hook, "MainHook is missing onPackageReady lifecycle handling")
require("hook(updateParams)" in hook, "MainHook is not using the modern hook builder")
require(".intercept(" in hook, "MainHook is not using the modern interceptor chain")
require("chain.proceed()" in hook, "MainHook must preserve after-hook semantics through chain.proceed()")
require("de.robv.android.xposed" not in hook, "legacy Xposed classes remain in MainHook")
require("import de.robv.android.xposed" not in hook, "legacy Xposed imports remain in MainHook")
require('"maxDownloadRequests"' not in hook, "normal maxDownloadRequests must not be overridden")
for token in ["BIG_FILE_SIZE_FROM", "downloadChunkSizeBig", "maxDownloadRequestsBig", "forceSmallChunk", "isPreloadVideoOperation", "isStream"]:
    require(token in hook, f"hook safety/behavior token missing: {token}")

for legacy in ["xposedmodule", "xposeddescription", "xposedminversion", "xposedscope"]:
    require(legacy not in manifest, f"legacy manifest metadata remains: {legacy}")
require("android:description=\"@string/app_description\"" in manifest,
        "modern module description must come from android:description")

for legacy_path in [
    ROOT / "app" / "src" / "main" / "assets" / "xposed_init",
    ROOT / "app" / "src" / "main" / "assets" / "Xposed_init",
]:
    require(not legacy_path.exists(), f"legacy Xposed entry must be removed: {legacy_path.relative_to(ROOT)}")

require(nonblank_lines(java_init) == [ENTRY], "java_init.list must contain exactly the modern MainHook entry")
require(nonblank_lines(scope_list) == SCOPES, "scope.list must contain exactly Telegram and Nullgram")

props = parse_properties(module_prop)
expected_props = {
    "minApiVersion": "101",
    "targetApiVersion": "102",
    "staticScope": "true",
    "exceptionMode": "protective",
    "autoHotReload": "false",
}
for key, value in expected_props.items():
    require(props.get(key) == value, f"module.prop requires {key}={value}")
require(set(props) == set(expected_props), f"unexpected module.prop keys: {sorted(set(props) - set(expected_props))}")

require("META-INF/xposed/java_init.list" in proguard, "R8 java_init.list adaptation rule is missing")
require("extends io.github.libxposed.api.XposedModule" in proguard, "R8 XposedModule keep rule is missing")


def verify_apk(apk_path: Path) -> None:
    require(apk_path.is_file(), f"APK does not exist: {apk_path}")
    required = {
        "META-INF/xposed/java_init.list": [ENTRY],
        "META-INF/xposed/scope.list": SCOPES,
    }
    with zipfile.ZipFile(apk_path) as apk:
        names = set(apk.namelist())
        for member, expected_lines in required.items():
            require(member in names, f"built APK is missing {member}")
            actual = nonblank_lines(apk.read(member).decode("utf-8"))
            require(actual == expected_lines, f"built APK has wrong {member}: {actual!r}")
        require("META-INF/xposed/module.prop" in names, "built APK is missing META-INF/xposed/module.prop")
        apk_props = parse_properties(apk.read("META-INF/xposed/module.prop").decode("utf-8"))
        require(apk_props == expected_props, f"built APK module.prop differs from source: {apk_props!r}")
        require("assets/xposed_init" not in names and "assets/Xposed_init" not in names,
                "built APK still contains a legacy Xposed entry")


if len(sys.argv) > 2:
    fail("usage: verify-modern-xposed.py [path/to/app.apk]")
if len(sys.argv) == 2:
    verify_apk((ROOT / sys.argv[1]).resolve() if not Path(sys.argv[1]).is_absolute() else Path(sys.argv[1]))

print("Modern libxposed module contract OK")
print("  API dependency: io.github.libxposed:api:102.0.0")
print("  Java entry: META-INF/xposed/java_init.list -> " + ENTRY)
print("  scopes: " + ", ".join(SCOPES))
print("  module.prop: minApiVersion=101, targetApiVersion=102, staticScope=true")
if len(sys.argv) == 2:
    print("  APK packaging: verified")
