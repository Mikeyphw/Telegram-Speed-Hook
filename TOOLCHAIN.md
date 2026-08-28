# Android toolchain baseline

Telegram-Speed-Hook must not use an Android build toolchain older than the
chrootctl Android baseline used when this file was created.

Current concrete pins:

- Gradle wrapper: 9.7.1 (policy floor: 9.7+)
- Android Gradle Plugin: 9.3.1 or newer compatible release
- Java/JDK: 21 or newer to run the build; Java source/target compatibility 21
- compileSdk: 36 or newer
- targetSdk: 36 or newer
- Android Build Tools: 36.0.0 or newer compatible release
- Android NDK: major 29; currently pinned to 29.0.14206865
- minSdk: 21 is intentionally retained because it is an app compatibility
  choice rather than a build-tool version

The project currently contains no Kotlin/KSP/CMake/native source, so those
components are not added merely to mirror chrootctl.
