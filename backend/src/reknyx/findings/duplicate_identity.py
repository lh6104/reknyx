"""Exact capture-instance identity; never title/CVE/model similarity."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib

from reknyx.contracts import canonical_request
from .correlation import asset_identity, service_identity

VERSION = 'exact-capture-v1'
NOTICE = ' Exact-capture duplicate observations are linked; every original observation and artifact remains retained.'


class DuplicatePublicationError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def capture_fingerprint(observation, native, artifact, parser_version):
    observed_at = observation['observed_at']
    if observed_at:
        instant = datetime.fromisoformat(observed_at.replace('Z', '+00:00'))
        if instant.tzinfo is None:
            raise DuplicatePublicationError('invalid_capture_time')
        observed_at = instant.astimezone(timezone.utc).isoformat()
    identity = {'version':VERSION, 'assessment_id':observation['assessment_id'],
        'sha256':artifact['sha256'], 'parser_version':parser_version,
        'raw_locator':observation['raw_locator'], 'source_tool':observation['source_tool'],
        'rule_id':native.get('rule_id'), 'observed_at':observed_at,
        'provenance':artifact['provenance'], 'historical':artifact['historical'],
        'asset':asset_identity(observation), 'service':service_identity(observation),
        'location':observation.get('location')}
    return hashlib.sha256(canonical_request(identity)).hexdigest()


def link_duplicate(finding, observation_id):
    result = deepcopy(finding)
    if observation_id in finding['observation_ids']:
        return result
    if len(finding['observation_ids']) >= 10000:
        raise DuplicatePublicationError('finding_membership_limit')
    reason = finding['correlation_reason']
    if NOTICE not in reason:
        reason += NOTICE
    if len(reason) > 2000:
        raise DuplicatePublicationError('finding_trace_limit')
    result.update(revision=finding['revision']+1,
                  observation_ids=finding['observation_ids']+[observation_id],
                  correlation_reason=reason)
    return result
