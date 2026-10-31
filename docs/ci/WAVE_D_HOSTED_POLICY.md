# Wave D — Hosted Gradle and exact source binding

All checked-in Gradle builds run in GitHub Actions. `[execution].gradle_execution = "github-actions-only"` blocks Devtool's standalone native Android builder and reviewed Gradle model execution on the invoking host *before chroot delegation*. `--bootstrap-only` is allowed for toolchain setup only. It does **not** intercept users directly invoking `./gradlew`, custom shell jobs, or third-party tools.

The schema-2 wrapper's typed `remote-debug-plan` and `remote-debug-build --yes` use Devtool's new `--require-local-head` guard automatically. It refuses uncommitted changes or an unpublished local HEAD before creating a dispatch request. The selected ref must match local HEAD at preflight; GitHub's mutable-branch race after the read remains possible, so the run and receipt must still be verified independently.

Wave C APK/receipt archives are verified by Devtool when downloaded, and reverified on `actions verify`: GitHub run ID, attempt, commit, ZIP safety, embedded APK SHA and receipt integrity are checked. These are integrity/claim checks, **not independent APK signature or device/release qualification**.

Run `./devtoolw ci-source`, commit and push, then `./devtoolw remote-debug-plan`. Never dispatch from an uncommitted repository.
