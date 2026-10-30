# Devtool wrapper — telegram

See [Devtool orchestration](ci/DEVTOOL_ORCHESTRATION.md) for complete source-only and GitHub Actions usage.

**Policy:** `./devtoolw` defaults to `ci-source`; all Gradle tasks execute only in GitHub Actions. `./devtoolw remote-debug-plan` is read-only; `./devtoolw remote-debug-build --yes` is the explicit mutating dispatch; `./devtoolw remote-resume --request-id REQUEST_ID` is the safe retry path.

Run `./devtoolw --help`, `devtool wrapper describe`, `devtool wrapper resolve ci-source`, and `devtool wrapper verify` to inspect the contract.
