# Devtool integration improvement ledger — Telegram-Speed-Hook

Last updated: 2026-10-30. Source baseline: uploaded 2026-10-30 repository and
Devtool snapshots. All status claims below are scoped to offline tests, not
live GitHub Actions, Termux, or device acceptance.

| ID | Priority | Improvement | Status | Evidence / next action |
|---|---|---|---|---|
| DT-CONS-P0-01 | P0 | Source-only wrapper default, no local Gradle in `ci-local` | DELIVERED (wrapper/DAG only) | Verified Devtool `wrapper resolve`, `preflight`, `invoke`; direct native `devtool build` still bypasses until core policy |
| DT-CONS-P0-02 | P0 | Typed Actions `plan`, `dispatch`, `watch`, `resume`, `artifacts` | DELIVERED (offline) | Native schema-2 resolves exact workflow, branch, inputs, request ID; no remote dispatch performed |
| DT-CONS-P0-03 | P0 | Guard old local Gradle scripts / legacy task aliases | DELIVERED (named entrypoints) | Read-only source policy test and explicit refusal; `./gradlew` itself remains available for GitHub builds |
| DT-CONS-P1-03 | P1 | Fix Kotlin multiline `include(...)` parser in Devtool | OPEN (upstream Wave B) | Parser rejects a legal terminal comma for relatorio-android |
| DT-CONS-P1-04 | P1 | Restructure source EXO DAG ownership, precise inputs | PARTIAL | Source workflow now portable and read-only where audited; deeper input/affected planning remains Wave B |
| DT-CONS-P1-05 | P1 | Hosted Gradle settings/declared artifact consistency | OPEN (Wave C) | CI and TOML values are not yet enforced as one shared policy |
| DT-CONS-P1-06 | P1 | Standardized SHA/run-bound remote evidence + verified import | OPEN (Wave C) | Source-only checks prove no cloud result; separate exact-run collection required |
| DT-CONS-P1-07 | P1 | Reduce duplicated CI build setup | OPEN (Wave C) | No hosted CI behavior modified in Wave A |
| DT-CONS-P1-08 | P1 | Real differentiated JVM/device test lanes | OPEN (Wave C) | Unit/emulator outcomes not claimed from static verification |
| DT-CONS-P2-09 | P2 | Adopt additional Devtool planning/retry/registry surfaces | PARTIAL | Wrapped Actions lifecycle and native DAG; remaining EXO features are future work |
| DT-CORE-P2-10 | P2 | Enforce hosted-Gradle-only admission across native Devtool CLI | OPEN (upstream Wave D) | Wrapper-only policy cannot intercept direct Gradle invocation |

**Release policy:** Wave A does not build or sign a release. Debug build
qualification requires independent remote evidence and optional device checks.

**Acceptance summary:** Devtool config parser, native typed wrapper resolution,
`wrapper verify`, `wrapper seal`, source DAG `plan/preflight/invoke`, and
source-bound overlay `apply-overlay` passed in disposable checkouts.
Actual GitHub dispatch, Termux and physical device testing were not performed.
