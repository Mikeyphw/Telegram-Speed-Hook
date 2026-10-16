#!/usr/bin/env python3
"""Offline contracts and per-build evidence for Telegram Speed Hook GitHub CI.

--static is read-only and doesn't need network/Gradle. --evidence creates a
receipt only after the workflow has cryptographically verified its APK.
A successful receipt is not a release qualification or device test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
APK_NAME = "telegram-speed-hook-debug.apk"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def source(relative: str) -> str:
    file = ROOT / relative
    require(file.is_file() and not file.is_symlink(), f"missing or unsafe source: {relative}")
    return file.read_text(encoding="utf-8")


def validate_static() -> None:
    config = source(".devtool.toml")
    require('repo = "git@github.com:Mikeyphw/Telegram-Speed-Hook.git"' in config,
            "unexpected GitHub repository identity")
    require('[targets.telegram_speed_hook]' in config, "Devtool Android target missing")
    for preserved in ('[extensions.xposed]', '[extensions.xposed.scope]',
                      '[extensions.hook]', '[extensions.checks.source]',
                      '[extensions.commands]', '[tasks.verify]', '[tasks.release_check]'):
        require(preserved in config, f'preserved Devtool metadata/task missing: {preserved}')
    require('devtool run checks.source' not in config,
            'legacy unsupported check invocation remains in local tasks')
    import tomllib
    namespaces=tomllib.loads(config).keys()
    require(not (set(namespaces) & {'xposed', 'hook', 'checks', 'commands'}),
            'legacy unsupported Devtool top-level namespace remains')
    require('application_id = "Telegram.Speed.Hook"' in config,
            "expected Android package identity missing")
    require('include \':app\'' in source('settings.gradle'), "Gradle :app inclusion missing")
    root_build = source('build.gradle')
    app = source('app/build.gradle')
    require("id 'com.android.application' version '9.3.1'" in root_build,
            "Android Gradle plugin pin changed")
    for needle in ("id 'com.android.application'", 'compileSdk 36',
                   'buildToolsVersion "36.0.0"', 'ndkVersion "29.0.14206865"',
                   'applicationId "Telegram.Speed.Hook"', 'minSdk 26', 'targetSdk 36',
                   'JavaVersion.VERSION_21', "compileOnly 'io.github.libxposed:api:102.0.0'"):
        require(needle in app, f"Gradle source contract changed: {needle}")
    require('gradle-9.7.1-bin.zip' in source('gradle/wrapper/gradle-wrapper.properties'),
            'Gradle wrapper pin changed')
    require((ROOT / 'gradle/wrapper/gradle-wrapper.jar').is_file(), 'missing Gradle wrapper JAR')
    require((ROOT / 'scripts/verify-modern-xposed.py').is_file(),
            'original modern libxposed packaging verifier missing')
    require((ROOT / 'scripts/verify-toolchain.py').is_file(),
            'original toolchain verifier missing')

    manual = source('.github/workflows/devtool-android-build.yml')
    ci = source('.github/workflows/telegram-speed-hook-ci.yml')
    for path, body in (('manual', manual), ('CI', ci)):
        require(re.search(r'(?m)^permissions:\s*\n\s+contents: read\s*$', body) is not None,
                f"{path}: least-privilege permissions missing")
        for unsafe in ('secrets.', 'pull_request_target:', 'permissions: write-all',
                       'assembleRelease', 'bundleRelease', 'DEVTOOL_RELEASE_KEYSTORE_B64'):
            require(unsafe not in body, f'{path}: unsafe token {unsafe!r}')
        for needle in ('actions/checkout@v4', 'actions/setup-java@v4',
                       'android-actions/setup-android@v4', 'gradle/actions/setup-gradle@v4',
                       'sdkmanager --install', 'gradle-wrapper',
                       'python3 scripts/verify-modern-xposed.py',
                       'python3 scripts/verify-toolchain.py',
                       'python3 scripts/verify_telegram_speed_hook_actions.py --static',
                       ':app:assembleDebug', 'apksigner', 'aapt',
                       'Telegram.Speed.Hook', '29.0.14206865'):
            # Check runtime controls; wrapper check is represented by gradle/wrapper/... in YAML.
            search = 'gradle/wrapper/' if needle == 'gradle-wrapper' else needle
            require(search in body, f'{path}: required control missing: {needle}')
    for needle in ('workflow_dispatch:', 'project_dir:', 'module:', 'variant:', 'format:',
                   'options: [app]', 'options: [debug]', 'options: [apk]',
                   'test "$(git rev-parse HEAD)" = "$GITHUB_SHA"',
                   'test "$DT_MODULE" = app', 'test "$DT_VARIANT" = debug',
                   'test "$DT_FORMAT" = apk',
                   '--evidence', 'if-no-files-found: error', 'actions/upload-artifact@v4'):
        require(needle in manual, f'manual workflow missing: {needle}')
    for needle in ('push:', 'pull_request:', 'workflow_dispatch:', 'options: [all, source, android]',
                   ':app:testDebugUnitTest', ':app:lintDebug', 'app/build/test-results/'):
        require(needle in ci, f'CI workflow missing: {needle}')

    # PyYAML is optional here, but if installed, verify schema rather than only tokens.
    try:
        import yaml
    except ImportError:
        pass
    else:
        for name, body in (('manual', manual), ('CI', ci)):
            parsed = yaml.safe_load(body)
            require(isinstance(parsed, dict) and isinstance(parsed.get('jobs'), dict),
                    f'{name}: invalid YAML jobs')
            triggers = parsed.get('on', parsed.get(True))  # PyYAML YAML 1.1 treats 'on' as boolean.
            require(isinstance(triggers, dict) and 'workflow_dispatch' in triggers,
                    f'{name}: invalid workflow_dispatch definition')
            if name == 'manual':
                fields = triggers['workflow_dispatch']['inputs']
                require(set(fields) == {'project_dir', 'module', 'variant', 'format'},
                        'manual dispatch input contract changed')
                for key, expected in (('project_dir', ['.']), ('module', ['app']),
                                      ('variant', ['debug']), ('format', ['apk'])):
                    require(fields[key]['options'] == expected,
                            f'manual dispatch {key} choices changed')
    print('Telegram Speed Hook Actions source and workflow contract: PASS (offline)')


def write_evidence(apk: Path, dest: Path) -> None:
    require(apk.is_file() and not apk.is_symlink() and apk.stat().st_size > 0,
            'expected regular, nonempty APK')
    require(apk.name == APK_NAME, 'unexpected APK artifact name')
    require(not dest.is_symlink() and not dest.exists(), 'evidence output already exists')
    require(os.environ.get('GITHUB_ACTIONS') == 'true', 'build evidence requires GitHub Actions')
    sha = os.environ.get('GITHUB_SHA', '')
    run_id = os.environ.get('GITHUB_RUN_ID', '')
    attempt = os.environ.get('GITHUB_RUN_ATTEMPT', '')
    require(re.fullmatch('[0-9a-f]{40}', sha) is not None, 'missing source SHA')
    require(run_id.isdecimal() and attempt.isdecimal(), 'missing run identity')
    require(os.environ.get('GITHUB_REPOSITORY', '') == 'Mikeyphw/Telegram-Speed-Hook',
            'unexpected repository identity')
    require(os.environ.get('GITHUB_EVENT_NAME', '') == 'workflow_dispatch',
            'build evidence requires manual dispatch')
    evidence = {
        'schema_version': 1,
        'producer': 'telegram-speed-hook-devtool-github-actions',
        'repository': 'Mikeyphw/Telegram-Speed-Hook',
        'source_sha': sha,
        'run_id': int(run_id),
        'run_attempt': int(attempt),
        'event': 'workflow_dispatch',
        'module': 'app',
        'variant': 'debug',
        'format': 'apk',
        'package': 'Telegram.Speed.Hook',
        'artifact_member': APK_NAME,
        'apk_size_bytes': apk.stat().st_size,
        'apk_sha256': hashlib.file_digest(apk.open('rb'), 'sha256').hexdigest(),
        'original_packaging_verifier': 'PASS',
        'runner_apksigner': 'PASS',
        'qualified_release': False,
        'device_qualified': False,
    }
    with dest.open('x', encoding='utf-8') as out:
        json.dump(evidence, out, sort_keys=True, indent=2)
        out.write('\n')
    print(f'Wrote SHA256-bound debug APK evidence: {dest}')


def main() -> int:
    ap = argparse.ArgumentParser()
    action = ap.add_mutually_exclusive_group(required=True)
    action.add_argument('--static', action='store_true', help='offline source and workflow checks')
    action.add_argument('--evidence', nargs=2, metavar=('APK', 'JSON'),
                        help='write one source/run-bound receipt after runner APK checks')
    args = ap.parse_args()
    try:
        if args.static:
            validate_static()
        else:
            write_evidence(Path(args.evidence[0]), Path(args.evidence[1]))
        return 0
    except (ValueError, OSError) as error:
        print(f'Telegram Speed Hook Actions: FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
