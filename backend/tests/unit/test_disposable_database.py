"""Test runner refuses inherited application database/provider configuration."""
import importlib.util
from pathlib import Path

_SPEC=importlib.util.spec_from_file_location('test_database_runner',Path(__file__).parents[3]/'scripts/test_database.py')


def runner():
    module=importlib.util.module_from_spec(_SPEC)
    _SPEC.loader.exec_module(module)
    return module


def test_child_environment_discards_existing_database_and_provider_secrets():
    module=runner()
    env=module.child_environment({'PATH':'/bin','REKNYX_DATABASE_URL':'persistent',
        'REKNYX_TEST_DATABASE_URL':'persistent','REKNYX_GROQ_API_KEY':'private',
        'GROQ_API_KEY':'private','REKNYX_ANALYSIS_PROVIDER':'groq'},'owner-url','runtime-url')
    assert env['REKNYX_DATABASE_URL']=='runtime-url'
    assert env['REKNYX_TEST_DATABASE_URL']=='runtime-url'
    assert env['REKNYX_TEST_ADMIN_DATABASE_URL']=='owner-url'
    assert env['REKNYX_ANALYSIS_PROVIDER']=='deterministic'
    assert 'REKNYX_GROQ_API_KEY' not in env and 'GROQ_API_KEY' not in env
    assert env['PATH']=='/bin'


def test_failed_container_start_reconciles_owned_name(monkeypatch,capsys):
    import subprocess
    module=runner();calls=[]
    def fake(cmd,**kwargs):
        calls.append(cmd)
        if 'info' in cmd:return subprocess.CompletedProcess(cmd,0,'17\n')
        if 'inspect' in cmd:return subprocess.CompletedProcess(cmd,0,'sha256:test\n')
        if 'create' in cmd:return subprocess.CompletedProcess(cmd,1,'startup interrupted\n')
        if 'ls' in cmd:return subprocess.CompletedProcess(cmd,0,'owned-id\n')
        if 'rm' in cmd:return subprocess.CompletedProcess(cmd,0,'owned-id\n')
        raise AssertionError(cmd)
    monkeypatch.setattr(module.subprocess,'run',fake)
    assert module.main(['--docker-context','default'])==2
    assert any('rm' in cmd and 'owned-id' in cmd for cmd in calls)
    assert 'private' not in capsys.readouterr().out
