#!/usr/bin/env python3
"""Wave D source-only guard; runs in native host, never invokes Gradle/network."""
from pathlib import Path
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]

def check(root=ROOT):
    cfg = tomllib.loads((root/'.devtool.toml').read_text(encoding='utf-8'))
    assert cfg['execution']['environment']=='host', 'chroot may be selected'
    assert cfg['execution']['gradle_execution']=='github-actions-only', 'local Gradle policy removed'
    assert cfg['targets']["telegram_speed_hook"]['execution_environment']=='host', 'target is not host-bound'
    assert cfg['wrapper']['default_command']=='ci-source', 'local wrapper default must be source-only'
    commands = cfg['wrapper']['commands']
    for name,op in [('remote-debug-plan','plan'),('remote-debug-build','dispatch')]:
        assert commands[name]['devtool']=='actions', 'non-typed GitHub shortcut'
        assert commands[name]['actions']['operation']==op, 'wrong remote operation'
        assert commands[name]['actions']['workflow_id']=='devtool-android-build.yml', 'wrong workflow'
        assert commands[name]['actions']['inputs']=={'project_dir':'.','module':'app','variant':'debug','format':'apk'}, 'unexpected inputs'
    assert commands['remote-debug-build']['options']['yes']['command_argv']==['--yes'], 'dispatch lacks explicit confirmation'
    for kind in ('ci-preflight','ci-local','ci-source'):
        for item in cfg['targets']["telegram_speed_hook"]['workflows'][kind]:
            job_name = item['ref'].removeprefix('job:')
            assert item['ref'].startswith('job:'), 'local source DAG gained native runner'
            job = cfg['targets']["telegram_speed_hook"]['jobs'].get(job_name, cfg.get('jobs',{}).get(job_name))
            assert isinstance(job,dict) and job['execution_environment']=='host', 'source job might select chroot'
            assert job['runner'] in ('command','python'), 'source job is not a lightweight static check'
            assert job.get('metadata',{}).get('read_only') is True, 'source validation must be read-only'
    return True

if __name__=='__main__':
    try: check()
    except (AssertionError,ValueError,OSError,KeyError,TypeError) as exc:
        print(f'WAVE_D_POLICY_REJECTED: {exc}',file=sys.stderr)
        raise SystemExit(1)
    print('PASS_WAVE_D_HOSTED_ONLY_AND_WRAPPER_POLICY')
