#!/usr/bin/env python3
"""Mutation checks for hosted CI security/provenance boundaries. No Gradle/network."""
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
from verify_wave_c import ROOT,MANUAL,CI,ACTION,EMULATOR,check

with TemporaryDirectory(prefix='wave-c-contract-') as temp:
    root=Path(temp)
    paths=[MANUAL,CI,ACTION]
    if EMULATOR:
        paths.append('.github/workflows/relatorio-emulator-tests.yml')
    for path in paths:
        p=root/path; p.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/path,p)
    assert check(root)
    cases=[(ACTION, 'apksigner', 'removed signer'),
           (ACTION, '--evidence', 'removed receipt'),
           (ACTION, ':app:assembleDebug', 'removed build'),
           (MANUAL, 'contents: read', 'permissions weakened'),
           (CI, 'uses: ./.github/actions/verified-debug-build', 'build bypassed'),
           (MANUAL, 'test "$DT_MODULE"', 'fixed dispatch bypassed')]
    for file,token,why in cases:
        p=root/file; original=p.read_text()
        assert token in original, (file,token)
        p.write_text(original.replace(token,'REMOVED_FOR_REGRESSION',1))
        try:
            check(root)
        except ValueError:
            pass
        else:
            raise AssertionError('Policy regression not caught: '+why)
        p.write_text(original)
    assert check(root)
# Integrity-only import: positive fixture and deliberate tampering must fail.
import importlib.util
import json
import hashlib
import zipfile
spec=importlib.util.spec_from_file_location('artifact_integrity',ROOT/'scripts/verify_wave_c_artifact.py')
artifact=importlib.util.module_from_spec(spec)
spec.loader.exec_module(artifact)
SHA='a'*40
RUN_ID=123456789
APK=b'SYNTHETIC_BYTES_NOT_AN_APK' * 10
with TemporaryDirectory(prefix='wave-c-artifact-') as temp:
    archive=Path(temp)/'artifact.zip'
    receipt={
        'schema_version':2,'repository':artifact.REPOSITORY,'source_sha':SHA,
        artifact.RUN_KEY:RUN_ID, artifact.ATTEMPT_KEY:1,
        'github_run_id':RUN_ID, 'github_run_attempt':1,
        'workflow_run_url':f'https://github.com/{artifact.REPOSITORY}/actions/runs/{RUN_ID}',
        'workflow_event':'workflow_dispatch','event':'workflow_dispatch',
        'package':artifact.PACKAGE,'module':'app','variant':'debug','format':'apk',
        'artifact_member':artifact.APK,'apk_size_bytes':len(APK),
        'apk_sha256':hashlib.sha256(APK).hexdigest(),
        'apk_signature_verified':True,'apk_manifest_verified':True,
        'unit_tests_and_lint_passed':True,'signing_certificate_sha256':'b'*64,
        'device_tests_executed':False,'device_qualified':False,
        'qualified_release':False,'release_qualified':False,
    }
    def write_receipt(r, data=APK, extra=False):
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(artifact.APK,data)
            z.writestr('build-evidence.json',json.dumps(r))
            if extra: z.writestr('extra-file.txt','INJECTED')
    write_receipt(receipt)
    assert artifact.verify(archive,SHA,RUN_ID,1)['integrity_verified']
    for change in ('wrong_sha','wrong_run','wrong_pkg','false_signature','extra_member','tamper_apk'):
        altered=dict(receipt)
        apk_data=APK
        extra=False
        if change=='wrong_sha':altered['source_sha']='c'*40
        elif change=='wrong_run':altered[artifact.RUN_KEY]=RUN_ID+1
        elif change=='wrong_pkg':altered['package']='com.attacker'
        elif change=='false_signature':altered['apk_signature_verified']=False
        elif change=='extra_member':extra=True
        elif change=='tamper_apk':apk_data=b'TAMPERED'+APK
        write_receipt(altered,apk_data,extra)
        try:
            artifact.verify(archive,SHA,RUN_ID,1)
        except ValueError:
            pass
        else:
            raise AssertionError('tampering was accepted: '+change)
print('PASS_WAVE_C_CI_AND_ARTIFACT_MUTATION_REGRESSIONS')

