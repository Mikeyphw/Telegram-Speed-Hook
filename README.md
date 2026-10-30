# Telegram Speed Hook

Telegram Speed Hook is an LSPosed/libxposed module that increases the large-file
request concurrency used by Telegram and Nullgram. The project was originally
created by **@AraafRoyall** and this fork retains that attribution while moving
the module to the modern libxposed API.

## Modern module format

Version 2 uses `io.github.libxposed:api:102.0.0` and the current module layout:

- Java entry: `META-INF/xposed/java_init.list`
- Static scope: `META-INF/xposed/scope.list`
- Module configuration: `META-INF/xposed/module.prop`
- Description: Android application `android:description`

The old `assets/xposed_init` entry and legacy `xposedmodule`,
`xposeddescription`, `xposedminversion`, and `xposedscope` manifest metadata are
intentionally removed.

## Scope

The static scope is intentionally limited to:

- `org.telegram.messenger`
- `top.qwq2333.nullgram`

The hook runs after `org.telegram.messenger.FileLoadOperation#updateParams()` and
adjusts only the large-file tuning fields. Small files, forced-small-chunk,
preload-video, and streaming operations are left alone. The normal
`maxDownloadRequests` field is intentionally not overridden.

## Build

Requirements:

- JDK 21+
- Gradle 9.7+
- Android SDK 36+
- Android Build Tools 36.0.0+
- NDK 29+ (current pin: 29.0.14206865)

Run source validation locally and dispatch the Android build to GitHub Actions:

```sh
./devtoolw                    # default: Python-only source + wrapper checks
./devtoolw remote-debug-plan # inspect hosted build request
./devtoolw remote-debug-build --yes  # after committing/pushing main
```

The hosted workflow verifies the **actual APK ZIP** and fails if any modern
`META-INF/xposed` member is missing or a legacy `assets/xposed_init` member
has returned. Read `docs/ci/DEVTOOL_ORCHESTRATION.md` for exact-request
resume, artifact inspection and qualifications; no Gradle is run locally.

## Install and test

1. Install the APK with Android's package manager.
2. Enable Telegram Speed Hook in an LSPosed/libxposed API 102-compatible framework.
3. Select Telegram and/or Nullgram in scope.
4. Force-stop the selected target and reopen it.
5. Inspect logs with `adb logcat -v time | grep TgSpeedHook`.

Opening the module app also performs a lightweight check of its installed base
APK and shows whether all three modern `META-INF/xposed` metadata files are
present.

## Attribution

Original project: @AraafRoyall (`Telegram-Speed-Hook`). The module is intended
for personal testing and development.
