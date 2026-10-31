# Devtool integration improvement ledger — Telegram-Speed-Hook

Last reviewed: 2026-10-31. Current consumer source baseline: `main` at
`2e1d8ebe6306e9488401fdcfb4ccd5e8677b3eb3`. This living ledger includes
verified hosted GitHub Actions evidence, as well as offline Devtool source tests.
The status table and current acceptance addendum supersede the dated Wave A–E
notes retained below as implementation history. Hosted CI success does not
establish real-device or release qualification.

| ID | Priority | Improvement | Status | Evidence / next action |
|---|---|---|---|---|
| DT-CONS-P0-01 | P0 | Source-only wrapper default, no local Gradle in `ci-local` | DELIVERED (Wave A/B) | Host-only `ci-source` wrapper and 9/9 Wave E source DAG stages passed in disposable acceptance. Direct `./gradlew` remains outside the wrapper guard. |
| DT-CONS-P0-02 | P0 | Typed Actions `plan`, `dispatch`, `watch`, `resume`, `artifacts` | DELIVERED (wrapper); live manual dispatch OPEN | Typed plan/dispatch/watch/resume/artifacts and exact-ref source guards implemented. Successful push CI does not demonstrate a manual Devtool dispatch/resume cycle. |
| DT-CONS-P0-03 | P0 | Guard old local Gradle scripts / legacy task aliases | DELIVERED (reviewed entrypoints) | Legacy build command aliases refuse local Gradle; raw `./gradlew` and custom commands remain outside those entrypoint checks. |
| DT-CONS-P1-03 | P1 | Fix Kotlin multiline `include(...)` parser in Devtool | DELIVERED upstream (Wave B) | Devtool parser patch and tests implemented; CI24 passed on upstream run [#41167603646](https://github.com/Mikeyphw/devtool/actions/runs/41167603646). Cross-project parser issue is not a Telegram runtime acceptance gate. |
| DT-CONS-P1-04 | P1 | Restructure source EXO DAG ownership, precise inputs | PARTIAL (Wave B) | Host-pinned read-only DAG, owned inputs and source workflow implemented; more granular per-job affected pruning remains open. |
| DT-CONS-P1-05 | P1 | Hosted Gradle settings/declared artifact consistency | PARTIAL (Wave C/D) | Pinned hosted Java/SDK/Gradle and APK contract passed on GitHub; complete one-to-one synchronization of every declared Gradle setting/output remains unproven. |
| DT-CONS-P1-06 | P1 | Standardized SHA/run-bound remote evidence + verified import | PARTIAL (Wave C/D) | SHA/run-bound schema-2 receipt, independent ZIP verifier, and GitHub artifact upload delivered; automated exact-run verified Devtool registry import remains open. |
| DT-CONS-P1-07 | P1 | Reduce duplicated CI build setup | DELIVERED (Wave C) | Push/PR CI and manual workflow share `.github/actions/verified-debug-build/action.yml`; hosted source/test/lint/APK build passed. |
| DT-CONS-P1-08 | P1 | Real differentiated JVM/device test lanes | PARTIAL (Wave E JVM delivered) | Hosted 10/10 mandatory production `SpeedPolicyTest` cases passed. No emulator or physical-device Telegram/Nullgram runtime evidence yet. |
| DT-CONS-P2-09 | P2 | Adopt additional Devtool planning/retry/registry surfaces | PARTIAL | Native source DAG and typed Actions lifecycle present; exact-run APK import and selective affected-node scheduling still open. |
| DT-CORE-P2-10 | P2 | Enforce hosted-Gradle-only admission across native Devtool CLI | DELIVERED for audited native Devtool paths (Wave D) | `[execution].gradle_execution = "github-actions-only"` protects supported native Android operations before chroot; direct `./gradlew` / arbitrary shell / third-party invocations are not intercepted. |

**Release policy:** Hosted workflows build debug APKs only. A CI success or
SHA-bound receipt is not a signed release and does not establish runtime usability.

**Historical Wave A acceptance (2026-10-30):** Devtool parser, typed wrapper,
source DAG and source-bound overlay passed in disposable checkouts; the hosted
CI and physical-device gates were still open at that earlier checkpoint.
See the current hosted acceptance addendum below.


### Wave B (2026-10-30): ownership, source DAG and host routing

- **Status:** OVERLAY IMPLEMENTED, device-side acceptance pending.
- **Evidence:** source-only EXO workflows reference `job:` nodes with host execution and explicit read-only input ownership; Gradle remains cloud-only by wrapper.
- **Consumer changes:** conservative target-level ownership for app, Python scripts, CI YAML and documentation; `scripts/verify_devtool_wave_b.py` provides fail-closed policy regression.
- **Open:** affected-target selection is conservative and does not prune individual job nodes; hosted Android test/receipt acceptance belongs to Wave C.
- **Correction:** Wave A Telegram `auto` affinity could also enter chroot; Wave B pins source checks to host.

## 2026-10-30 — Wave C: hosted CI deduplication and artifact evidence

- **Delivered locally:** shared hosted-only composite action; manual and automatic CI share source/Gradle/test/lint/APK verification; upgraded schema-2 run-bound receipts; offline downloaded-ZIP identity/hash checks; source-only Devtool `ci-wave-c-contract` job with mutation tests. See `docs/ci/WAVE_C_HOSTED_CI_AND_PROVENANCE.md`.
- **Xposed packaging verification retained.** No credential-bearing release lane.
- **Acceptance:** static schema and mutation tests, local Devtool source DAG, transactional overlay apply in disposable checkout; GitHub execution and emulator/device runtime remain **pending**.
- **Open:** verify actual GitHub artifacts/run identity, independently attest remote artifacts before registry import, core Devtool hosted-only Gradle enforcement, and live device/emulator qualification.


## Wave E — Telegram real hosted JVM tests (2026-10-31)

- **Root cause:** `:app:testDebugUnitTest` could succeed without any checked-in policy test; static contracts alone did not prove hook parameter behavior.
- **Fix:** extract pure Java `SpeedPolicy` from the production hook, add ten JUnit4 cases, wire Gradle `testImplementation`, enforce actual JUnit XML execution in the shared GitHub action, add host-only source/DAG contract and negative XML tests.
- **Boundaries:** no local Gradle or chroot; no release signing, no automatic GitHub dispatch. Changes to Telegram/Nullgram runtime remain observational until device acceptance.
- **Hosted acceptance completed:** push-triggered [run #41170772881](https://github.com/Mikeyphw/Telegram-Speed-Hook/actions/runs/41170772881) succeeded on commit `2e1d8ebe6306e9488401fdcfb4ccd5e8677b3eb3`. Job log: `PASS_HOSTED_JUNIT: executed=10 policy_cases=10` following hosted assemble/test/lint.
- **Still open:** independent downloaded-artifact verification for this Wave E run; installed APK, LSPosed attachment and real download behavior on Telegram/Nullgram; release qualification is not claimed.


## Current consumer acceptance — 2026-10-31

| Promise / gate | Status | Grounded evidence / limitation |
|---|---|---|
| Wave A/B source-only host DAG | DELIVERED / source-tested | Wave E disposable source DAG: 9/9 stages. No local Gradle or chroot through the reviewed wrapper. |
| Wave C hosted CI and debug APK evidence | ACCEPTED on GitHub | [Run #41170772881](https://github.com/Mikeyphw/Telegram-Speed-Hook/actions/runs/41170772881), attempt 1, source SHA `2e1d8ebe6306e9488401fdcfb4ccd5e8677b3eb3`; both CI jobs succeeded. |
| Wave D native hosted-only and source identity policy | IMPLEMENTED / source-tested | `[execution].gradle_execution = "github-actions-only"`; shared hosted action checks `git rev-parse HEAD == GITHUB_SHA`. No claim of intercepting arbitrary `./gradlew`. |
| Wave E production JVM policy tests | ACCEPTED on GitHub | Gradle `:app:assembleDebug :app:testDebugUnitTest :app:lintDebug` passed; CI output: `PASS_HOSTED_JUNIT: executed=10 policy_cases=10` (no required cases skipped). |
| Debug APK and diagnostic artifact publication | ACCEPTED on GitHub | APK+receipt `telegram-speed-hook-debug-apk-41170772881-1` (artifact ID `13030718164`); diagnostics `telegram-speed-hook-diagnostics-41170772881-1` (artifact ID `13030812645`). Signature, manifest and hash receipt checks occur in the GitHub shared action. |
| Manual typed Actions dispatch and recovery | OPEN for live consumer acceptance | Successful push CI is **not** evidence of Devtool manual dispatch/watch/resume deduplication. |
| Automatic verified exact-run APK registry import | OPEN | Offline ZIP verifier exists, but there is no completed end-to-end automated exact-run download/import feature. |
| Telegram/Nullgram runtime compatibility and speed gains | OPEN | No recorded LSPosed hook attachment, compatibility with actual installed app versions, before/after throughput or crash/fallback measurements. |
| Release signing and device qualification | OUT OF SCOPE | Debug artifacts and tests are not release-authorization evidence. |

**Evidence references:** [GitHub run #41170772881](https://github.com/Mikeyphw/Telegram-Speed-Hook/actions/runs/41170772881), [hosted action](../.github/actions/verified-debug-build/action.yml), [JUnit guard](../scripts/verify_junit_results.py), [Wave C evidence contract](ci/WAVE_C_HOSTED_CI_AND_PROVENANCE.md), [Wave D policy](ci/WAVE_D_HOSTED_POLICY.md).

**Ledger maintenance:** Keep this table and current acceptance section updated on subsequent consumer work. Retain dated sections for audit history; do not convert offline, test-only or APK-metadata evidence into live-device/release claims.
