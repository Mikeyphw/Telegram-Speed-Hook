#!/usr/bin/env python3
"""Wave-A local fail-closed Devtool wrapper/CI policy regression contract.

Offline source policy check only. Does not establish remote build success or
prevent a user from directly invoking a Gradle executable or native Devtool runner.
"""
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]
CONFIG = tomllib.loads((ROOT / '.devtool.toml').read_text(encoding='utf-8'))
TARGET = 'telegram_speed_hook'
BRANCH = 'main'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)

wrapper = CONFIG['wrapper']
require(wrapper['schema'] == 2 and wrapper['default_command'] == 'ci-source', 'unsafe wrapper default')
commands = wrapper['commands']
for forbidden in ('build', 'test', 'lint', 'package', 'clean'):
    require(forbidden not in commands, f'local Gradle-capable wrapper entry remains: {forbidden}')
for name, config in commands.items():
    require(config.get('allow_passthrough') is not True, f'unsafe wrapper passthrough: {name}')
    if 'actions' in config:
        require(config['devtool'] == 'actions', f'non-native remote action: {name}')
        require(name.startswith('remote-'), 'remote action incorrectly named')
    else:
        require(config.get('workflow') in ('ci-source', 'ci-local', 'ci-preflight'),
                f'non-source workflow exposed in wrapper: {name}')
        require(config.get('target') == TARGET, f'wrong wrapper target: {name}')

for name, op in (('remote-debug-plan','plan'), ('remote-debug-build','dispatch'),
                 ('remote-watch','watch'), ('remote-resume','resume'), ('remote-artifacts','artifacts')):
    require(commands[name]['actions']['operation'] == op, f'wrong action: {name}')
for name in ('remote-debug-plan','remote-debug-build'):
    spec=commands[name]['actions']
    require(spec['workflow_id'] == 'devtool-android-build.yml' and spec['ref'] == BRANCH,
            f'wrong workflow/ref: {name}')
    require(spec['inputs'] == dict(project_dir='.',module='app',variant='debug',format='apk'),
            f'changed fixed build inputs: {name}')
require(commands['remote-debug-build']['options']['yes'] == dict(
    type='boolean', description='Explicitly authorize GitHub workflow dispatch',
    command_argv=['--yes']), 'dispatch no longer requires explicit yes')
for name in ('remote-watch','remote-resume','remote-artifacts'):
    request=commands[name]['options']['request_id']
    require(request['type'] == 'string' and request['required'] is True and
            request['aliases'] == ['request-id'] and
            request['command_argv'] == ['--request-id','{value}'],
            f'exact request ID binding missing: {name}')
for name in ('ci-source','ci-local','ci-preflight'):
    jobs=CONFIG['targets'][TARGET]['workflows'][name]
    require(jobs and all(isinstance(j,dict) and j['ref'].startswith('job:') for j in jobs),
            f'non-Python/native Gradle runner in source-only workflow: {name}')
for name in ('ci-source', 'ci-local'):
    refs=[j['ref'] for j in CONFIG['targets'][TARGET]['workflows'][name]]
    require('job:ci-wrapper-contract' in refs, f'wrapper contract not in source DAG: {name}')

# Local legacy aliases must not hide Gradle execution.
for name in ('clean','build_debug','release_check'):
    require(CONFIG['tasks'][name]['command'] == 'python3 scripts/hosted_gradle_only.py',
            f'legacy local Gradle task is executable: {name}')
for name in ('build',):
    require(CONFIG['extensions']['commands'][name] == 'python3 scripts/hosted_gradle_only.py',
            f'legacy extension command builds locally: {name}')
require('./gradle-termux' not in (ROOT / 'gradle-termux').read_text(),
        'termux launcher cannot delegate locally')
require('exit 2' in (ROOT / 'gradle-termux').read_text(), 'gradle-termux must fail closed')
print('PASS_WAVE_A_HOSTED_ONLY_WRAPPER_SOURCE_CONTRACT')
