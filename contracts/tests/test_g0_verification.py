"""Gate closure requires checks plus owner approval of the exact source bytes."""
from copy import deepcopy
import importlib
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))


def gate():
    return importlib.import_module('verify_g0')


def approval():
    return {'status': 'approved', 'reviewer': 'admin',
            'reviewed_at': '2026-11-06T08:51:45Z', 'openapi_sha256': 'a' * 64}


def test_gate_rejects_stale_owner_approval_even_after_successful_checks():
    review = {'frontend_owner': approval(), 'backend_owner': approval()}
    review['backend_owner']['openapi_sha256'] = 'b' * 64
    with pytest.raises(ValueError, match='backend_owner'):
        gate().require_owner_approvals(review, 'a' * 64)


@pytest.mark.parametrize('field,value', [('status', 'pending'), ('reviewer', ''), ('reviewed_at', '')])
def test_gate_never_fabricates_missing_owner_acceptance(field, value):
    review = {'frontend_owner': approval(), 'backend_owner': deepcopy(approval())}
    review['frontend_owner'][field] = value
    with pytest.raises(ValueError, match='frontend_owner'):
        gate().require_owner_approvals(review, 'a' * 64)


def test_all_exact_owner_approvals_are_accepted():
    gate().require_owner_approvals({'frontend_owner': approval(), 'backend_owner': approval()}, 'a' * 64)
