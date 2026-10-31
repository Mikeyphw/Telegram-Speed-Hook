#!/usr/bin/env python3
"""Offline integrity check of a downloaded GitHub Actions APK+receipt ZIP.

Verifies ZIP integrity, strict members, SHA, stated run identity and receipt
fields. This is NOT APK cryptographic re-verification, nor proof of a trusted
GitHub run. Cross-check run metadata in GitHub separately before deployment.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

REPOSITORY = 'Mikeyphw/Telegram-Speed-Hook'
PACKAGE = 'Telegram.Speed.Hook'
APK = 'telegram-speed-hook-debug.apk'
RUN_KEY = 'run_id'
ATTEMPT_KEY = 'run_attempt'
MAX_APK_BYTES = 150 * 1024 * 1024


def require(ok,message):
    if not ok:
        raise ValueError(message)


def verify(archive, source_sha, run_id, attempt):
    require(re.fullmatch('[0-9a-f]{40}',source_sha) is not None,'invalid expected SHA')
    require(run_id > 0 and attempt > 0,'run identity must be positive')
    require(archive.is_file() and not archive.is_symlink(),'missing or unsafe ZIP')
    with zipfile.ZipFile(archive) as z:
        entries = z.infolist()
        require(len(entries)==2 and {e.filename for e in entries} == {APK,'build-evidence.json'},
                'ZIP must contain exactly the expected APK and receipt')
        for e in entries:
            require(not e.is_dir() and not (e.external_attr >> 16) & 0o170000 == 0o120000,
                    'unsafe ZIP member type')
            limit=MAX_APK_BYTES if e.filename==APK else 32*1024
            require(0 < e.file_size <= limit,'invalid ZIP member size')
            require(e.compress_size > 0 and e.file_size <= 250*e.compress_size,
                    'suspicious compression ratio')
        require(z.testzip() is None,'ZIP CRC mismatch')
        receipt=json.loads(z.read('build-evidence.json'))
        require(isinstance(receipt,dict) and receipt.get('schema_version')==2,
                'invalid Wave C receipt schema')
        require(receipt.get('repository')==REPOSITORY,'wrong source repository')
        require(receipt.get('source_sha')==source_sha,'wrong source commit')
        require(receipt.get('github_run_id')==run_id and
                receipt.get('github_run_attempt')==attempt and
                receipt.get(RUN_KEY)==run_id and receipt.get(ATTEMPT_KEY)==attempt,
                'receipt belongs to a different GitHub request')
        require(receipt.get('workflow_run_url') ==
                f'https://github.com/{REPOSITORY}/actions/runs/{run_id}',
                'wrong run link')
        require(receipt.get('package')==PACKAGE and receipt.get('module')=='app' and
                receipt.get('variant')=='debug' and receipt.get('format')=='apk',
                'APK identity or build coordinates changed')
        require(receipt.get('artifact_member')==APK, 'wrong APK filename in receipt')
        require(receipt.get('apk_size_bytes')==z.getinfo(APK).file_size,'APK byte length mismatch')
        require(receipt.get('apk_signature_verified') is True and
                receipt.get('apk_manifest_verified') is True and
                receipt.get('unit_tests_and_lint_passed') is True,
                'missing build verification claims')
        require(receipt.get('device_qualified') is False and
                receipt.get('device_tests_executed') is False,
                'unexpected device-qualification claims')
        require(receipt.get('qualified_release',receipt.get('release_qualified')) is False,
                'unexpected release qualification claim')
        require(re.fullmatch('[0-9a-f]{64}', receipt.get('signing_certificate_sha256','')) is not None,
                'missing signing certificate digest')
        require(receipt.get('event',receipt.get('workflow_event')) in
                ('workflow_dispatch','push','pull_request'),'invalid build event')
        sha=hashlib.sha256()
        with z.open(APK) as binary:
            while chunk:=binary.read(1024*1024):
                sha.update(chunk)
        require(sha.hexdigest()==receipt.get('apk_sha256'),'APK SHA256 mismatch')
        return {'repository': REPOSITORY,'source_sha':source_sha,
                'github_run_id':run_id,'github_run_attempt':attempt,
                'apk_sha256':sha.hexdigest(), 'apk_size_bytes':z.getinfo(APK).file_size,
                'integrity_verified':True,
                'github_run_independently_verified':False,
                'apk_signature_independently_verified':False,
                'device_qualified':False,'release_qualified':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('zip',type=Path)
    p.add_argument('--source-sha',required=True)
    p.add_argument('--run-id',required=True,type=int)
    p.add_argument('--attempt',required=True,type=int)
    args=p.parse_args()
    try:
        result=verify(args.zip,args.source_sha,args.run_id,args.attempt)
    except (OSError,ValueError,zipfile.BadZipFile,KeyError,json.JSONDecodeError) as e:
        print(f'ARTIFACT_INTEGRITY_FAIL: {e}',file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(result,indent=2,sort_keys=True))
