"""Read back synthetic report/source bytes across a clean disposable restart."""
import hashlib
import json
import os
from pathlib import Path
import sys

import httpx


def capture():
    origin = os.environ['REKNYX_BROWSER_ORIGIN']
    result = {}
    with httpx.Client(base_url=origin, timeout=10, trust_env=False) as client:
        login = client.post('/api/v1/auth/login', headers={'Origin': origin}, json={
            'username': os.environ['REKNYX_BROWSER_USERNAME'],
            'password': os.environ['REKNYX_BROWSER_PASSWORD'],
        })
        login.raise_for_status()
        reports = client.get('/api/v1/workspace/reports', params={'limit': 100})
        reports.raise_for_status()
        page = reports.json()
        assert page['next_cursor'] is None, 'Unexpected pagination in disposable browser dataset'
        assert len(page['items']) == 2, 'Both browser workflows must produce a report'
        assessments = set()
        for item in page['items']:
            assessment_id, report = item['assessment']['id'], item['report']
            assert report['state'] == 'ready', 'A browser report is not ready'
            assessments.add(assessment_id)
            path = f"/api/v1/assessments/{assessment_id}/reports/{report['id']}/download"
            raw = client.get(path)
            raw.raise_for_status()
            assert raw.content.startswith(b'%PDF-')
            result[path] = hashlib.sha256(raw.content).hexdigest()
        for assessment_id in assessments:
            artifacts = client.get(f'/api/v1/assessments/{assessment_id}/artifacts', params={'limit': 100})
            artifacts.raise_for_status()
            page = artifacts.json()
            assert page['next_cursor'] is None
            for artifact in page['items']:
                path = artifact['download_url']
                raw = client.get(path)
                raw.raise_for_status()
                digest = hashlib.sha256(raw.content).hexdigest()
                assert digest == artifact['sha256'], 'Stored artifact integrity mismatch'
                result[path] = digest
    assert len(result) >= 6, 'Expected two PDF downloads and original/report artifacts'
    return result


if __name__ == '__main__':
    state = Path(os.environ['REKNYX_CI_STATE'])
    if sys.argv[1:] == ['capture']:
        state.touch(mode=0o600, exist_ok=False)
        state.write_text(json.dumps(capture(), sort_keys=True))
        print('Captured two synthetic reports and their artifact hashes')
    elif sys.argv[1:] == ['verify']:
        assert capture() == json.loads(state.read_text()), 'Restart changed persisted evidence/report bytes'
        print('Clean restart preserved synthetic report and artifact bytes')
    else:
        raise SystemExit('Usage: check-persistence.py capture|verify')
