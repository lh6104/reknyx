from copy import deepcopy
import hashlib
import json
from pathlib import Path
import pytest
from reknyx.evidence.storage import LocalArtifactStore, IntegrityError
from reknyx.security_analysis.knowledge_snapshots import ingest_snapshot, read_snapshot, KnowledgeImportError, main

FIXTURE=Path(__file__).parents[1]/'fixtures/knowledge/synthetic-snapshot-v1.json'


def test_archive_retains_original_bytes_and_verifies_after_restart(tmp_path):
    raw=FIXTURE.read_bytes();store=LocalArtifactStore(tmp_path/'archive')
    receipt=ingest_snapshot(store,raw)
    assert store.get(receipt['raw']['storage_key'])==raw
    reloaded=read_snapshot(LocalArtifactStore(tmp_path/'archive'),receipt)
    assert reloaded['sha256']==receipt['snapshot_sha256']
    assert receipt['raw']['sha256']==hashlib.sha256(raw).hexdigest()
    assert receipt['document_count']==3
    assert set(store.reconcile([receipt['raw']['storage_key'],receipt['normalized']['storage_key']])['unreferenced_blobs'])==set()


def test_rejection_retains_source_without_creating_normalized_success(tmp_path):
    store=LocalArtifactStore(tmp_path/'archive');raw=b'{"documents":[],"version":"bad"}'
    with pytest.raises(KnowledgeImportError) as caught:ingest_snapshot(store,raw)
    assert caught.value.code=='invalid_snapshot'
    assert store.get(caught.value.raw['storage_key'])==raw
    assert len(list(store.root.glob('*.receipt')))==1


def test_source_revision_creates_new_snapshot_without_overwriting_old(tmp_path):
    store=LocalArtifactStore(tmp_path/'archive');raw=FIXTURE.read_bytes()
    first=ingest_snapshot(store,raw)
    data=json.loads(raw);data['documents'][0]['source_revision']='new-revision'
    second=ingest_snapshot(store,json.dumps(data).encode())
    assert first['snapshot_sha256']!=second['snapshot_sha256']
    assert read_snapshot(store,first)['documents']!=read_snapshot(store,second)['documents']


def test_receipt_cannot_rebind_raw_bytes_to_a_different_snapshot(tmp_path):
    store=LocalArtifactStore(tmp_path/'archive');first=ingest_snapshot(store,FIXTURE.read_bytes())
    data=json.loads(FIXTURE.read_bytes());data['version']='changed'
    second=ingest_snapshot(store,json.dumps(data).encode())
    second['raw']=first['raw']
    with pytest.raises((ValueError,IntegrityError)):read_snapshot(store,second)


def test_tampered_blob_and_path_identifier_are_rejected(tmp_path):
    store=LocalArtifactStore(tmp_path/'archive');receipt=ingest_snapshot(store,FIXTURE.read_bytes())
    changed=deepcopy(receipt);changed['normalized']['storage_key']='../../private'
    with pytest.raises(ValueError):read_snapshot(store,changed)
    (store.root/receipt['normalized']['storage_key']).write_bytes(b'{}')
    with pytest.raises(IntegrityError):read_snapshot(store,receipt)


def test_cli_never_overwrites_receipts_and_reports_rejections(tmp_path,capsys):
    archive=tmp_path/'archive';receipt=tmp_path/'receipt.json'
    args=['import','--archive-root',str(archive),'--input',str(FIXTURE),'--receipt',str(receipt)]
    assert main(args)==0
    assert receipt.stat().st_mode & 0o777==0o600
    original=receipt.read_bytes();before=set(archive.iterdir())
    assert main(args)==2 and receipt.read_bytes()==original and set(archive.iterdir())==before
    assert main(['verify','--archive-root',str(archive),'--receipt',str(receipt)])==0
    invalid=tmp_path/'bad.json';invalid.write_bytes(b'not-json')
    rejected=tmp_path/'rejected.json'
    assert main(['import','--archive-root',str(archive),'--input',str(invalid),'--receipt',str(rejected)])==1
    assert json.loads(rejected.read_bytes())['status']=='rejected'
    assert 'content' not in capsys.readouterr().out


def test_deeply_nested_json_is_rejected_with_retained_raw_receipt(tmp_path):
    store=LocalArtifactStore(tmp_path/'archive')
    raw=b'['*2000+b'0'+b']'*2000
    with pytest.raises(KnowledgeImportError) as caught:ingest_snapshot(store,raw)
    assert store.get(caught.value.raw['storage_key'])==raw


def test_failed_final_write_preserves_durable_pending_receipt(tmp_path,monkeypatch):
    from reknyx.security_analysis import knowledge_snapshots as module
    receipt=tmp_path/'receipt.json';archive=tmp_path/'archive';original=module.json.dump
    def fail_ready(value,stream,**kwargs):
        if value.get('status')=='ready':
            stream.write('{"partial":')
            raise OSError('simulated write failure')
        return original(value,stream,**kwargs)
    monkeypatch.setattr(module.json,'dump',fail_ready)
    assert module.main(['import','--archive-root',str(archive),'--input',str(FIXTURE),'--receipt',str(receipt)])==2
    assert json.loads(receipt.read_bytes())['status']=='pending'
    assert len(list(archive.glob('*.receipt')))==2


def test_verification_rejects_excessive_source_nesting_without_recursion_trace(tmp_path):
    from dataclasses import asdict
    store=LocalArtifactStore(tmp_path/'archive');receipt=ingest_snapshot(store,FIXTURE.read_bytes())
    receipt['raw']=asdict(store.put(b'['*2000+b'0'+b']'*2000))
    with pytest.raises(IntegrityError):read_snapshot(store,receipt)
