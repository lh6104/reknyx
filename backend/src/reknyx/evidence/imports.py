"""Import intake and source normalization; caller owns database transactions."""
import ipaddress
from urllib.parse import urlsplit
from uuid import uuid4

from reknyx.assessments.service import require_membership
from reknyx.contracts import validate
from reknyx.evidence.service import ArtifactService
from reknyx.findings.priority import prioritize
from reknyx.infrastructure.errors import DomainError
from reknyx.infrastructure.events import append_event
from reknyx.shared.time import now, timestamp


def asset(identity):
    try:
        parsed = ipaddress.ip_address(identity)
        family, canonical = 'ipv' + str(parsed.version), str(parsed)
    except ValueError:
        family, canonical = 'hostname', identity.lower()
    return {'address_family': family, 'raw_identity': identity,
            'canonical_identity': canonical, 'authorized_asset_id': None}


def normalize(kind, raw, source):
    """Return validated canonical projections, retaining native fields separately."""
    if kind == 'zap_json':
        from reknyx.scanner_integrations.zap import parse
    elif kind == 'greenbone_xml':
        from reknyx.scanner_integrations.greenbone import parse
    elif kind == 'nmap_xml':
        from reknyx.scanner_integrations.nmap import parse
    else:
        raise ValueError('unsupported_format')
    batch = parse(raw)
    observations, findings, native = [], [], []
    for item in batch.observations:
        identifier = str(uuid4())
        if kind == 'zap_json':
            url = urlsplit(item.uri)
            observed_asset = asset(url.hostname)
            service = {'transport': 'tcp', 'port': url.port or (443 if url.scheme == 'https' else 80),
                       'scheme': url.scheme, 'observation_ids': [identifier]}
            location = {'scheme': url.scheme, 'host': url.hostname, 'port': service['port'],
                        'path': url.path or '/', 'raw_url': item.uri, 'method': item.method,
                        'parameter': item.parameter, 'redacted': False}
            observed_kind, native_id = 'vulnerability', item.native_id
            severity, confidence = item.raw_risk, item.raw_confidence
        elif kind == 'greenbone_xml':
            observed_asset = asset(item.address)
            service = {'transport': item.protocol if item.protocol in ('tcp','udp') else 'unknown',
                       'port': item.port, 'scheme': None, 'observation_ids': [identifier]}
            location, observed_kind, native_id = None, item.kind, item.native_id
            severity, confidence = item.raw_severity, item.raw_confidence
        else:
            observed_asset = asset(item.address)
            service = {'transport': item.protocol if item.protocol in ('tcp', 'udp') else 'unknown',
                       'port': item.port, 'scheme': None, 'observation_ids': [identifier]}
            location, observed_kind, native_id, severity, confidence = None, 'service', None, None, None
        observation = {**source, 'id': identifier, 'execution_id': None,
                       'raw_locator': item.raw_locator, 'kind': observed_kind,
                       'source_tool': {'zap_json':'zap','nmap_xml':'nmap','greenbone_xml':'greenbone'}[kind],
                       'native_id': native_id, 'asset': observed_asset, 'service': service,
                       'location': location, 'raw_severity': severity, 'raw_confidence': confidence}
        validate('Observation', observation)
        observations.append(observation)
        from dataclasses import asdict
        native.append(asdict(item))
        if observed_kind != 'vulnerability':
            continue
        unknown = {'value': 'unknown', 'observation_ids': [], 'analyst': None, 'observed_at': None}
        finding = {'id': str(uuid4()), 'assessment_id': source['assessment_id'], 'revision': 1,
                   'title': item.title, 'asset': observed_asset, 'service': service, 'location': location,
                   'severity': item.severity, 'cvss': None, 'cvss_vector': None, 'cvss_version': None,
                   'cvss_source': None, 'cve_ids': [], 'cwe_ids': [],
                   'confidence_method': 'ZAP native confidence code (uncalibrated)',
                   'confidence_value': confidence, 'validation_status': 'suspected', 'validation_evidence': None,
                   'analyst_disposition': 'needs_review', 'observation_ids': [identifier],
                   'correlation_reason': 'Single native instance; no cross-source merge performed.',
                   'exposure': unknown.copy(), 'exploitability': unknown.copy(), 'asset_impact': unknown.copy(),
                   'risk_input_sources': [],
                   'unknowns': ['Exposure, exploitability and asset impact are unknown.', 'CVSS is not supplied by this parser.'],
                   'remediation': item.solution or 'Review the source evidence and determine appropriate remediation.'}
        if kind == 'greenbone_xml':
            finding.update(cvss=item.cvss, cvss_vector=item.cvss_vector,
                           cvss_version=item.cvss_version, cvss_source=item.cvss_source,
                           cve_ids=list(item.cve_ids),
                           confidence_method='Greenbone native QoD (uncalibrated detection quality, not probability)')
            finding['unknowns'] = ['Exposure, exploitability and asset impact are unknown.']
            if item.cvss is None:
                finding['unknowns'].append('No supported explicit CVSS score/vector/version pair supplied; native NVT fields retained.')
        if finding['severity'] != 'unknown':
            finding['risk_input_sources'].append({'field':'severity','observation_ids':[identifier],'analyst':None})
        if finding['cvss'] is not None:
            finding['risk_input_sources'].append({'field':'cvss','observation_ids':[identifier],'analyst':None})
        finding.update(prioritize(finding))
        validate('Finding', finding)
        findings.append(finding)
    warnings = [{'code': w.code, 'message': 'Native parser warning: ' + w.code, 'raw_locator': w.raw_locator}
                for w in getattr(batch, 'warnings', ())]
    if len(warnings) > 100:
        raise ValueError('resource_limit: too many parser warnings')
    return {'observations': observations, 'findings': findings, 'native': native,
            'warnings': warnings, 'parser_version': batch.parser_version, 'outcome': batch.outcome}


class ImportService:
    def __init__(self, session, store, actor_id):
        self.session, self.store, self.actor_id = session, store, actor_id

    def create(self, assessment_id, metadata, raw):
        from reknyx.infrastructure.models import ImportRecord
        assessment = require_membership(self.session, self.actor_id, assessment_id, lock=True)
        validate('ImportCreate', {**metadata, 'file': 'original bytes'})
        if metadata['kind'] not in ('zap_json', 'nmap_xml', 'greenbone_xml'):
            raise DomainError(501, 'capability_not_implemented', 'This native format is in development')
        artifact = ArtifactService(self.session, self.store, self.actor_id).put_bytes(assessment_id, raw, {
            'source': 'import', 'content_type': 'application/json' if metadata['kind'] == 'zap_json' else 'application/xml',
            'observed_at': metadata['observed_at'], 'provenance': metadata['provenance'], 'historical': True})
        identifier, job_id, instant = str(uuid4()), str(uuid4()), now()
        created = timestamp(instant)
        job = {'id': job_id, 'assessment_id': assessment_id, 'kind': 'import', 'resource_id': identifier,
               'state': 'queued', 'attempt_id': None, 'created_at': created, 'started_at': None,
               'finished_at': None, 'failure_code': None}
        data = {'id': identifier, 'assessment_id': assessment_id, 'job': job, 'kind': metadata['kind'],
                'state': 'queued', 'artifact_id': artifact['id'], 'observation_ids': [], 'parser_version': None,
                'warnings': [], 'failure_code': None, 'created_at': created, 'finished_at': None}
        validate('Import', data)
        self.session.add(ImportRecord(id=identifier, assessment_id=assessment_id, created_at=instant,
                                      source_label=metadata['source_label'], data=data))
        assessment.data = {**assessment.data, 'state_revision': assessment.data['state_revision'] + 1}
        append_event(self.session, self.actor_id, assessment_id, 'import.queued', identifier, 'Immutable original bytes retained; parsing queued')
        return {'job_id': job_id, 'resource_id': identifier,
                'status_url': f'/api/v1/assessments/{assessment_id}/imports/{identifier}'}

    def get(self, assessment_id, import_id):
        from reknyx.infrastructure.models import ImportRecord
        require_membership(self.session, self.actor_id, assessment_id)
        record = self.session.get(ImportRecord, import_id)
        if record is None or record.assessment_id != assessment_id:
            raise DomainError(404, 'not_found')
        return record.data
