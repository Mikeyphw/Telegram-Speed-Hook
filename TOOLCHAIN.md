# Android and libxposed toolchain baseline

Telegram-Speed-Hook v2 is a modern libxposed module. The project enforces
minimum toolchain versions so future changes cannot silently downgrade the APK
or reintroduce the legacy Xposed API.

Current concrete pins/floors:

- Gradle wrapper: 9.7.1 (policy floor: 9.7+)
- Android Gradle Plugin: 9.3.1 or newer compatible release
- Java/JDK: 21 or newer; Java source/target compatibility 21
- compileSdk: 36 or newer
- targetSdk: 36 or newer
- Android Build Tools: 36.0.0 or newer compatible release
- Android NDK: **29 or newer**; currently pinned to **29.0.14206865**
- Android minSdk: **26**, matching the published libxposed API 102.0.0 floor
- libxposed module API: `io.github.libxposed:api:102.0.0` (`compileOnly`)
- module behavior target: API 102; minimum framework API declared as 101

The module currently has no JNI/CMake/native source, so no native `.so` is
added just to force NDK execution. `ndkVersion` still pins r29 for any native
work introduced later, and `scripts/verify-toolchain.py` rejects NDK versions
below 29.

Modern module packaging is verified by `scripts/verify-modern-xposed.py`:

- `META-INF/xposed/java_init.list`
- `META-INF/xposed/scope.list`
- `META-INF/xposed/module.prop`
- no `assets/xposed_init` legacy entry
- no legacy `xposed*` manifest metadata
- no `de.robv.android.xposed` dependency or hook classes
