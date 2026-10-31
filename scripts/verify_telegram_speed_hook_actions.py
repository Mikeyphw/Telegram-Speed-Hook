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

    from verify_wave_c import check as validate_wave_c
    validate_wave_c(ROOT)
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
    event = os.environ.get('GITHUB_EVENT_NAME', '')
    require(event in ('workflow_dispatch','push','pull_request'),
            'evidence only allowed in supported GitHub workflow events')
    require(int(run_id) > 0 and int(attempt) > 0, 'invalid run numbers')
    require(os.environ.get('GITHUB_WORKFLOW', ''), 'missing GitHub workflow identity')
    import subprocess
    checked = subprocess.run(['git','-C',str(ROOT),'rev-parse','HEAD'],
                             capture_output=True,text=True,check=True,timeout=20).stdout.strip()
    require(checked == sha, 'checked-out source does not match GitHub SHA')
    sdk = Path(os.environ.get('ANDROID_HOME', '/nonexistent')) / 'build-tools/36.0.0'
    signature = subprocess.run([str(sdk/'apksigner'),'verify','--print-certs',str(apk)],
                              capture_output=True,text=True,check=True,timeout=30).stdout
    certs = re.findall(r'(?im)^Signer #1 certificate SHA-256 digest:\s*([0-9a-f]{64})\s*$',signature)
    require(len(certs)==1, 'APK certificate fingerprint missing or ambiguous')
    badging = subprocess.run([str(sdk/'aapt'),'dump','badging',str(apk)],
                             capture_output=True,text=True,check=True,timeout=30).stdout
    require(re.search(r"(?m)^package: name='Telegram\.Speed\.Hook'\s",badging),
            'APK manifest identity changed')
    evidence = {
        'schema_version': 2,
        'producer': 'telegram-speed-hook-devtool-github-actions',
        'repository': 'Mikeyphw/Telegram-Speed-Hook',
        'source_sha': sha,
        'run_id': int(run_id),
        'run_attempt': int(attempt),
        'github_run_id': int(run_id),
        'github_run_attempt': int(attempt),
        'event': event,
        'workflow_event': event,
        'workflow_name': os.environ['GITHUB_WORKFLOW'],
        'workflow_run_url': f"https://github.com/Mikeyphw/Telegram-Speed-Hook/actions/runs/{run_id}",
        'signing_certificate_sha256': certs[0].lower(),
        'apk_signature_verified': True,
        'apk_manifest_verified': True,
        'unit_tests_and_lint_passed': True,
        'device_tests_executed': False,
        'module': 'app',
        'variant': 'debug',
        'format': 'apk',
        'package': 'Telegram.Speed.Hook',
        'artifact_member': APK_NAME,
        'apk_size_bytes': apk.stat().st_size,
        'apk_sha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
        'original_packaging_verifier': 'PASS',
        'runner_apksigner': 'PASS',
        'qualified_release': False,
        'release_qualified': False,
        'signed_release': False,
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
