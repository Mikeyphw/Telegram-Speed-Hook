#!/usr/bin/env python3
"""Host-only regression of real test receipts and Wave E source wiring."""
from pathlib import Path
import tempfile
import sys
import tomllib
from verify_junit_results import verify, EXPECTED_SUITE, REQUIRED_TESTS

ROOT = Path(__file__).resolve().parents[1]

def run():
    config = tomllib.loads((ROOT / '.devtool.toml').read_text())
    assert config['execution']['gradle_execution'] == 'github-actions-only'
    assert config['targets']['telegram_speed_hook']['jobs']['ci-wave-e-policy-tests']['execution_environment'] == 'host'
    source = (ROOT / 'app/src/main/java/Telegram/Speed/Hook/MainHook.java').read_text()
    policy = (ROOT / 'app/src/main/java/Telegram/Speed/Hook/SpeedPolicy.java').read_text()
    tests = (ROOT / 'app/src/test/java/Telegram/Speed/Hook/SpeedPolicyTest.java').read_text()
    gradle = (ROOT / 'app/build.gradle').read_text()
    action = (ROOT / '.github/actions/verified-debug-build/action.yml').read_text()
    assert 'SpeedPolicy.apply(operation)' in source
    assert 'private static boolean setInt' in policy
    assert "testImplementation 'junit:junit:4.13.2'" in gradle
    assert ':app:testDebugUnitTest' in action
    assert 'python3 scripts/verify_junit_results.py app/build/test-results/testDebugUnitTest' in action
    for name in REQUIRED_TESTS:
        assert 'void ' + name + '(' in tests
    with tempfile.TemporaryDirectory() as tmp:
        folder=Path(tmp)
        try:
            verify(folder)
        except ValueError:
            pass
        else:
            raise AssertionError('empty test directory accepted')
        def write(cases):
            (folder / ('TEST-' + EXPECTED_SUITE + '.xml')).write_text('<testsuite name="'+EXPECTED_SUITE+'" tests="'+str(len(cases))+'">'+''.join('<testcase classname="'+EXPECTED_SUITE+'" name="'+name+'"/>' for name in cases)+'</testsuite>')
        write(sorted(REQUIRED_TESTS))
        assert verify(folder)==(len(REQUIRED_TESTS),len(REQUIRED_TESTS))
        write(sorted(REQUIRED_TESTS - {'nullOperationIsIgnored'}))
        try:
            verify(folder)
        except ValueError:
            pass
        else:
            raise AssertionError('omitted test accepted')
        write(sorted(REQUIRED_TESTS))
        file=next(folder.glob('TEST-*.xml'))
        file.write_text(file.read_text().replace('/>', '><skipped/></testcase>', 1))
        try:
            verify(folder)
        except ValueError:
            pass
        else:
            raise AssertionError('skipped test accepted')
    return True

if __name__ == '__main__':
    run()
    print('PASS_WAVE_E_REAL_TESTS_AND_FAIL_CLOSED_JUNIT')
