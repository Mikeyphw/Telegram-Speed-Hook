#!/usr/bin/env python3
"""Wave C source-only CI and receipt boundaries. No Gradle, network, chroot, or dispatch.

The jobs invoking these checks execute on host; the composite action runs only in
GitHub-hosted workflows. YAML parsing is optional to remain pip-free in Termux;
required structural and security tokens are checked even without PyYAML.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MANUAL = '.github/workflows/devtool-android-build.yml'
CI = '.github/workflows/telegram-speed-hook-ci.yml'
ACTION = '.github/actions/verified-debug-build/action.yml'
PACKAGE = 'Telegram.Speed.Hook'
GRADLE_TOKENS = (':app:assembleDebug', ':app:testDebugUnitTest', ':app:lintDebug', '29.0.14206865')
JAVA = '21'
EMULATOR = False


def require(value, message):
    if not value:
        raise ValueError(message)


def read(root, rel):
    path = root / rel
    require(path.is_file() and not path.is_symlink(), f'missing/unsafe {rel}')
    return path.read_text(encoding='utf-8')


def check(root=ROOT):
    manual, ci, action = [read(root, r) for r in (MANUAL, CI, ACTION)]
    for label, body in ((MANUAL, manual), (CI, ci), (ACTION, action)):
        for forbidden in ('secrets.', 'pull_request_target:', 'permissions: write-all',
                          'assembleRelease', 'bundleRelease', 'DEVTOOL_RELEASE_KEYSTORE',
                          'softprops/action-gh-release'):
            require(forbidden not in body, f'{label} contains forbidden {forbidden}')
    for label, body in ((MANUAL, manual), (CI, ci)):
        require(re.search(r'(?m)^permissions:\s*\n\s+contents: read\s*$', body),
                f'{label} missing explicit minimal permissions')
        require(body.count('uses: ./.github/actions/verified-debug-build') == 1,
                f'{label} must use the same hosted composite exactly once')
        require('actions/checkout@v4' in body and 'persist-credentials: false' in body,
                f'{label} must checkout source without persisted credentials')
        require('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"' in (body + action),
                f'{label} must check source SHA')
        require('./gradlew' not in body, f'{label} duplicates Gradle outside shared composite')
    require('workflow_dispatch:' in manual and 'pull_request:' not in manual
            and re.search(r'(?m)^  push:', manual) is None,
            'Devtool build must be manual-only')
    for key, options in (('project_dir', "['.']"),('module', '[app]'),
                         ('variant', '[debug]'),('format', '[apk]')):
        require(re.search(rf'(?m)^      {key}:\s*$', manual) is not None,
                f'missing Devtool dispatch field {key}')
        require(f'options: {options}' in manual, f'dispatch choices changed for {key}')
    for value in ('DT_PROJECT', 'DT_MODULE', 'DT_VARIANT', 'DT_FORMAT'):
        require(f'test "${value}"' in manual, f'missing fixed input guard {value}')
    require('workflow_dispatch:' in ci and 'pull_request:' in ci and 'push:' in ci,
            'automatic CI events removed')
    require('runs:' in action and 'using: composite' in action, 'not a composite action')
    steps = ('source-contract','setup-java','setup-sdk','install-sdk',
             'gradle-cache','gradle-build','package','upload-apk')
    locations = [action.find('id: ' + k) for k in steps]
    require(all(n >= 0 for n in locations) and locations == sorted(locations),
            'source -> build -> verification -> upload ordering broken')
    for token in ('actions/setup-java@v4',f"java-version: '{JAVA}'",
                  'android-actions/setup-android@v4','gradle/actions/setup-gradle@v4',
                  'sdkmanager --install','platforms;android-36',
                  'build-tools;36.0.0', 'test -f gradle/wrapper/',
                  'test "$(git rev-parse HEAD)" = "$GITHUB_SHA"',
                  'python3 scripts/verify_', './gradlew --no-daemon',
                  'apksigner', 'aapt', PACKAGE, 'sha256sum',
                  '--evidence', 'if-no-files-found: error',
                  'actions/upload-artifact@v4','build-evidence.json') + GRADLE_TOKENS:
        require(token in action, f'composite lost mandatory {token}')
    require('test ! -L "$apk"' in action, 'APK symlink rejection missing')
    require(action.index('apksigner') < action.index('--evidence'),
            'receipt issued before APK signature verification')
    require(action.index('aapt') < action.index('--evidence'),
            'receipt issued before APK manifest verification')
    require('if: ${{ always() }}' in action and 'test-results' in action,
            'failure diagnostics/report capture missing')
    if EMULATOR:
        emulator_wf = read(root, '.github/workflows/relatorio-emulator-tests.yml')
        require('workflow_dispatch:' in emulator_wf and 'pull_request:' not in emulator_wf,
                'emulator must remain an opt-in GitHub-only lane')
        for token in ('permissions:', 'contents: read',
                      'reactivecircus/android-emulator-runner@v2',
                      ':app:connectedDebugAndroidTest', 'api-level: 35',
                      'actions/upload-artifact@v4'):
            require(token in emulator_wf, f'missing emulator safeguard: {token}')
    try:
        import yaml
    except ImportError:
        return True
    for label, body in ((MANUAL,manual),(CI,ci),(ACTION,action)):
        parsed = yaml.safe_load(body)
        require(isinstance(parsed, dict), f'malformed yaml {label}')
        if label == ACTION:
            require(parsed.get('runs',{}).get('using') == 'composite',
                    'invalid composite runner')
            require(len(parsed['runs']['steps']) >= 8, 'incomplete composite steps')
            continue
        triggers = parsed.get('on', parsed.get(True))
        require(isinstance(triggers,dict) and 'workflow_dispatch' in triggers,
                f'missing event trigger {label}')
        require(isinstance(parsed.get('jobs'),dict), f'missing jobs {label}')
        if label == MANUAL:
            fields=triggers['workflow_dispatch']['inputs']
            require(set(fields) == {'project_dir','module','variant','format'},
                    'Devtool ACTIONS-05 inputs changed')
            for name, choices in (('project_dir',['.']),('module',['app']),
                                  ('variant',['debug']),('format',['apk'])):
                require(fields[name].get('type') == 'choice' and
                        fields[name].get('required') is True and
                        fields[name].get('options') == choices,
                        f'noncanonical dispatch choice {name}')
        for job in parsed['jobs'].values():
            require(any(s.get('uses') == './.github/actions/verified-debug-build'
                        for s in job['steps']) if label == MANUAL
                    else True, 'manual job bypassed hosted action')
    return True


if __name__ == '__main__':
    try:
        check()
    except (OSError, ValueError) as exc:
        print(f'FAIL_WAVE_C_CI_CONTRACT: {exc}',file=sys.stderr)
        raise SystemExit(1)
    print('PASS_WAVE_C_HOSTED_CI_AND_ARTIFACT_CONTRACT')
