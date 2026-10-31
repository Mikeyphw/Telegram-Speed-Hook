# Wave E — real Telegram/Nullgram policy unit tests

`SpeedPolicy` is the Android-independent production decision engine, called by
`MainHook` *after* libxposed's `chain.proceed()` and before the activation toast.
JVM JUnit 4 tests cover file-size boundaries, small-chunk/preload/stream skips,
reflection on inherited or missing fork fields, all four tuned parameters,
and idempotence. Source-only `scripts/test_wave_e.py` checks test wiring and
negative JUnit receipt cases; it does not pretend to execute Android Gradle.

Both hosted workflows reuse the same composite; after the GitHub-only Gradle
`:app:testDebugUnitTest` task, `verify_junit_results.py` refuses missing/empty,
incomplete, skipped, failed or errored policy suites. No local Gradle or chroot.

The checks verify decision/policy behavior; they **do not** establish that
Telegram/Nullgram's current obfuscated/runtime `FileLoadOperation` matches the
hook, or that LSPosed scope and downloads work on a device. Those tests remain
pending with a real APK and installed target application.
