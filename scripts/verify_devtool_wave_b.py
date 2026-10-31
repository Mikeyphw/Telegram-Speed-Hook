#!/usr/bin/env python3
"""Wave B source ownership/DAG/host regression contract; no Gradle or SDK calls."""
from pathlib import Path
import tomllib
P = Path(__file__).resolve().parents[1]
c = tomllib.loads((P/'.devtool.toml').read_text())
t = c['targets']['telegram_speed_hook']
assert c['execution']['environment'] == t['execution_environment'] == 'host'
assert t['android']['prefer_native_termux'] is True
assert {'app/**', 'scripts/**', '.github/workflows/**', 'docs/ci/**'} <= set(t['inputs'])
source = {'ci-source', 'ci-local', 'ci-preflight'}
for name in source:
    nodes=t['workflows'][name]
    assert all(x['ref'].startswith('job:') for x in nodes), name
    assert 'job:ci-wave-b-contract' in [x['ref'] for x in nodes], name
for workflow in ('ci-source','ci-local'):
    nodes={x['id']: x for x in t['workflows'][workflow]}
    assert nodes['toolchain']['depends_on'] == [], 'independent toolchain must be parallel'
for name in ('ci-actions-contract','ci-source-contract','ci-wrapper-contract','ci-wave-b-contract'):
    job=t['jobs'][name]
    assert job['runner'] == 'command' and job['execution_environment'] == 'host'
    assert job['metadata']['read_only'] is True and 'outputs' not in job
for name in ('telegram-speed-hook-source-xposed','telegram-speed-hook-toolchain','telegram-speed-hook-packaged-xposed'):
    j=c['jobs'][name]
    assert j['execution_environment'] == 'host'
    assert j['metadata']['read_only'] is True and 'outputs' not in j
print('PASS_WAVE_B_TELEGRAM_SOURCE_DAG_AND_HOST_OWNERSHIP')
