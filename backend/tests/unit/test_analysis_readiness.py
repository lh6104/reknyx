from dataclasses import replace
from pathlib import Path
from reknyx.config import Settings
from reknyx.security_analysis.readiness import describe


def test_readiness_is_explicit_and_does_not_expose_key():
    base=Settings(database_url='postgresql+psycopg://unused:unused@localhost/unused',artifact_root=Path('/tmp/unused'),password_hash='scrypt$unused')
    assert describe(base)['reason_code']=='local_review_ready'
    model=replace(base,analysis_provider='groq')
    assert describe(model)['reason_code']=='groq_key_missing'
    model=replace(model,groq_api_key='private-test-secret')
    assert describe(model)['reason_code']=='groq_free_plan_unconfirmed'
    model=replace(model,groq_free_plan_confirmed=True)
    assert describe(model)['reason_code']=='groq_data_use_unconfirmed'
    model=replace(model,groq_synthetic_enabled=True)
    assert describe(model)['reason_code']=='groq_configured'
    assert 'private-test-secret' not in str(describe(model))
    assert 'private-test-secret' not in repr(model)


def test_offline_checker_reports_missing_setup_without_requests(monkeypatch,capsys):
    from reknyx.security_analysis.check_setup import main
    from reknyx.security_analysis.model_providers import groq
    monkeypatch.setattr(groq,'review',lambda *args:(_ for _ in ()).throw(AssertionError('no network allowed')))
    for key in ('REKNYX_DATABASE_URL','REKNYX_ARTIFACT_ROOT','REKNYX_PASSWORD_HASH'):
        monkeypatch.delenv(key,raising=False)
    assert main()==2
    assert 'invalid_server_configuration' in capsys.readouterr().out
    monkeypatch.setenv('REKNYX_DATABASE_URL','postgresql+psycopg://unused:unused@localhost/unused')
    monkeypatch.setenv('REKNYX_ARTIFACT_ROOT','/tmp/unused')
    monkeypatch.setenv('REKNYX_PASSWORD_HASH','scrypt$unused')
    monkeypatch.setenv('REKNYX_ANALYSIS_PROVIDER','deterministic')
    assert main()==0
    assert '"provider_request_sent": false' in capsys.readouterr().out
    monkeypatch.setenv('REKNYX_ANALYSIS_PROVIDER','groq')
    monkeypatch.delenv('REKNYX_GROQ_API_KEY',raising=False)
    assert main()==1
    assert 'groq_key_missing' in capsys.readouterr().out
