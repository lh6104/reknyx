#!/usr/bin/env python3
"""Run all offline G0 checks; optionally record exact-byte gate evidence.

This verifies executable contracts and the existing owner approvals only. It does
not establish HTTP, parser, provider, scanner, PDF or platform acceptance.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def require_owner_approvals(review, digest):
    for role in ('frontend_owner', 'backend_owner'):
        owner = review.get(role, {})
        if (owner.get('status') != 'approved' or not owner.get('reviewer')
                or not owner.get('reviewed_at') or owner.get('openapi_sha256') != digest):
            raise ValueError(f'{role}: current exact-byte approval is required')


def source_hashes(root):
    """Exclude mutable gate records, installed dependencies and generated outputs."""
    files = [p for p in (root / 'contracts').rglob('*')
             if p.is_file() and not any(part in ('node_modules', '__pycache__', '.pytest_cache')
                                       for part in p.parts)
             and p.name != 'review-status.json']
    files.extend(p for p in (root / 'scripts').glob('*')
                 if p.is_file() and ('contract' in p.name or p.name == 'verify_g0.py'))
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(files)}


def verify(root):
    record_path = root / 'contracts/review-status.json'
    review = json.loads(record_path.read_text())
    before = source_hashes(root)
    digest = before['contracts/openapi.yaml']
    require_owner_approvals(review, digest)
    commands = [
        [sys.executable, 'scripts/validate_contracts.py'],
        [sys.executable, '-m', 'pytest', 'contracts/tests', '-q'],
        ['npm', '--prefix', 'contracts', 'run', 'check:generated'],
        ['npm', '--prefix', 'contracts', 'run', 'check:types'],
        ['npm', '--prefix', 'contracts', 'run', 'check:hashes'],
    ]
    checks = []
    for command in commands:
        result = subprocess.run(command, cwd=root, capture_output=True, timeout=60)
        output = result.stdout + result.stderr
        if result.returncode:
            raise ValueError(f'Check failed: {command}\n{output.decode(errors="replace")}')
        checks.append({'command': command, 'exit_code': result.returncode,
                       'output_sha256': hashlib.sha256(output).hexdigest(),
                       'output': output.decode(errors='replace')})
    if before != source_hashes(root) or review != json.loads(record_path.read_text()):
        raise ValueError('Contract inputs or approval record changed during verification; rerun')
    return review, {'status': 'passed', 'verified_at': datetime.now(timezone.utc).isoformat(),
                    'openapi_sha256': digest, 'evidence_level': 'offline_contract',
                    'source_sha256': before, 'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', action='store_true', help='Record successful verification in review-status.json')
    args = parser.parse_args()
    try:
        review, evidence = verify(ROOT)
        if args.record:
            # Detailed run output stays ignored locally; the portable status
            # ledger retains only the exact-input attestation and evidence path.
            relative = 'docs/implementation/evidence/g0/' + evidence['verified_at'].replace(':', '-') + '.json'
            evidence_path = ROOT / relative
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text(json.dumps(evidence, indent=2) + '\n')
            review['status'] = 'g0_verified'
            review['gate_verification'] = {
                key: evidence[key] for key in ('status', 'verified_at', 'openapi_sha256', 'evidence_level')}
            review['gate_verification']['input_sha256'] = hashlib.sha256(
                json.dumps(evidence['source_sha256'], sort_keys=True).encode()).hexdigest()
            review['gate_verification']['local_evidence_path'] = relative
            path = ROOT / 'contracts/review-status.json'
            temporary = path.with_suffix('.json.tmp')
            temporary.write_text(json.dumps(review, indent=2) + '\n')
            temporary.replace(path)
        print(json.dumps(evidence, indent=2))
        return 0
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(f'G0 verification failed: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
