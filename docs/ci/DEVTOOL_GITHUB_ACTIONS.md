# Telegram Speed Hook — Devtool + GitHub Actions

## Scope and safety

The `Telegram-Speed-Hook` repository has a single Android `app` module and a
Devtool target named `telegram_speed_hook`. This integration adds two workflows:

- `.github/workflows/devtool-android-build.yml`: manual **debug APK only** build,
  with source SHA, libxposed packaging, package ID and Android signature checks;
  uploads one APK and a SHA256/source/run-bound evidence JSON.
- `.github/workflows/telegram-speed-hook-ci.yml`: automatic source checks on push
  and PR, Android debug assemble/unit tests/lint, and independent packaged APK
  checks. Includes manual `lane` selection (`all`, `source`, `android`).

No workflow installs an APK, publishes releases, fetches secrets or performs
stable release signing. A debug APK and green CI do **not** prove device/LSPosed
compatibility or qualify a production release. There is no AAB lane because
LSPosed modules are installed as APKs and this project validates APK metadata.

The workflows use Java 21, Gradle wrapper 9.7.1, Android platform/build tools
36, and NDK 29.0.14206865, matching the existing repository. GitHub-hosted
Ubuntu installs the toolchain: it does **not** run the Termux-specific `gradle-termux`
launcher. The repository's own source and APK verifier scripts remain authoritative.

## Install with the supplied source-bound overlay

Use the outer bundle installer from this chat. It targets
`$HOME/Code/Telegram-Speed-Hook` by default and discovers
`$HOME/Code/telegram-speed-hook` if that is your actual checkout name.
Application is atomic, clean-worktree and source-snapshot bound, with no Git
commit or push performed automatically. The overlay also changes `.devtool.toml`:
legacy top-level `xposed`, `hook`, `checks`, and `commands` tables are moved to
`[extensions.*]`, and the two local tasks referencing the unsupported
`devtool run checks.source` are updated to invoke the existing Python verifiers
directly. Hook behavior and Android target metadata remain; legacy local Gradle build entrypoints are deliberately disabled by Wave A.

```sh
cd ~/Code/Telegram-Speed-Hook
python3 scripts/verify_telegram_speed_hook_actions.py --static
git status --short
git add .devtool.toml .github/workflows/devtool-android-build.yml \
  .github/workflows/telegram-speed-hook-ci.yml \
  scripts/verify_telegram_speed_hook_actions.py docs/ci/DEVTOOL_GITHUB_ACTIONS.md
git commit -m 'Add Devtool GitHub Actions APK CI'
git push
```

## GitHub authentication

```sh
gh auth status
# If required: gh auth login
```

Devtool uses GitHub CLI authentication or a suitable `GH_TOKEN`/`GITHUB_TOKEN`.
The token must have Actions write permission for dispatch. CI workflows need
only contents read; workflow files must be committed and pushed before GitHub
can dispatch them. A new workflow might have to exist on the repository's
default branch before GitHub exposes its manual dispatcher.

## Recommended Devtool lifecycle

```sh
REPO="$HOME/Code/Telegram-Speed-Hook"  # adjust if lowercase
REF="$(git -C "$REPO" branch --show-current)"

devtool -r "$REPO" actions diagnose --json
devtool -r "$REPO" actions workflows --json
devtool -r "$REPO" actions android discover --json

devtool -r "$REPO" actions android plan \
  --module app --variant debug --format apk --ref "$REF" --json

devtool -r "$REPO" actions android run \
  --module app --variant debug --format apk --ref "$REF" --yes --json
```

For `actions android plan/run`, Devtool requires clean, committed local source,
with the exact local HEAD already present at GitHub's chosen ref. This project's
Gradle application plugin is statically discoverable (`app/build.gradle`).

If you prefer the generic workflow dispatcher:

```sh
devtool -r "$REPO" actions plan devtool-android-build.yml \
  --ref "$REF" --input project_dir=. --input module=app \
  --input variant=debug --input format=apk --json

devtool -r "$REPO" actions run devtool-android-build.yml \
  --ref "$REF" --input project_dir=. --input module=app \
  --input variant=debug --input format=apk --yes --json
```

Never automatically re-dispatch an accepted or uncertain request. If there is
no trustworthy run ID, use `actions resume --request-id REQUEST_ID` to inspect
state, or independently find the GitHub run.

## Observe the remote work and obtain an APK

```sh
devtool -r "$REPO" actions runs --limit 10 --json
devtool -r "$REPO" actions view --run-id RUN_ID --json
devtool -r "$REPO" actions watch --run-id RUN_ID \
  --interval 5 --max-checks 120 --json
devtool -r "$REPO" actions artifacts --run-id RUN_ID --json

# Requires successful workflow_dispatch run and local Android SDK tools.
devtool -r "$REPO" actions android collect \
  --run-id RUN_ID --artifact-id ARTIFACT_ID \
  --format apk --variant debug \
  --expected-package Telegram.Speed.Hook \
  --download --json
```

Android collection checks the remote workflow, its successful status, artifact
SHA256/ZIP, APK signature, and application ID. It places the inspected APK in
`.devtool/artifacts/android-verified/` and marks `qualified_release=false`.
The archive also contains `build-evidence.json`; the source SHA/run ID and
APK SHA256 must match the independently observed remote data. The manifest's
claims do not substitute for Devtool's independent verification.

The automated CI workflow can be run separately:

```sh
devtool -r "$REPO" actions plan telegram-speed-hook-ci.yml \
  --ref "$REF" --input lane=all --json
devtool -r "$REPO" actions run telegram-speed-hook-ci.yml \
  --ref "$REF" --input lane=all --yes --json
```

## Limits of offline validation

The overlay tests YAML syntax/inputs, static source/toolchain contracts,
Devtool overlay application and fail-closed source guards. It does not execute
a GitHub-hosted Android build or test your actual LSPosed runtime. Do not
consider it device-qualified until you inspect real workflow evidence and
perform optional on-device checks yourself.
