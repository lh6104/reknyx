"""Pure traditional-JSON ZAP format parser; no IO or execution authority.

This implementation is verified against synthetic shape cases only. Callers must
store original bytes first and run parsing in a resource-limited process. The
worker's ten-second wall deadline is not implemented by this pure function.
"""
from dataclasses import dataclass
import hashlib
import json
import re
from urllib.parse import urlsplit

VERSION = 'zap_traditional_json_v1.0'
MAX_BYTES = 20 * 1024 * 1024
MAX_RECORDS = 10000


class ParseError(ValueError):
    def __init__(self, code, reason):
        self.code = code
        super().__init__(f'{code}: {reason}')


@dataclass(frozen=True)
class Warning:
    code: str
    raw_locator: str


@dataclass(frozen=True)
class Observation:
    raw_locator: str
    rule_id: str
    plugin_id: str
    alert_ref: str | None
    native_id: str | None
    uri: str
    method: str | None
    parameter: str | None
    title: str
    description: str | None
    solution: str | None
    reference: str | None
    cwe_id: str | None
    evidence: str | None
    attack: str | None
    other_info: str | None
    raw_risk: str
    severity: str
    raw_confidence: str
    validation_status: str = 'suspected'


@dataclass(frozen=True)
class ParsedBatch:
    sha256: str
    parser_version: str
    producer_version: str
    observations: tuple[Observation, ...]
    warnings: tuple[Warning, ...]
    outcome: str
    observed_at: None = None


def _string(value, required=False):
    if value is None and not required:
        return None
    if not isinstance(value, str) or (required and not value) or len(value) > 100000:
        raise ParseError('malformed', 'Expected bounded source text')
    return value


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ParseError('malformed', 'Duplicate JSON member')
        result[key] = value
    return result


def _origin(uri):
    try:
        value = urlsplit(uri)
        if (value.scheme not in ('http', 'https') or not value.hostname
                or value.username is not None or value.password is not None
                or any(ord(char) <= 32 for char in uri)):
            raise ValueError('Invalid origin')
        return value.scheme, value.hostname.lower(), value.port or (443 if value.scheme == 'https' else 80)
    except ValueError as exc:
        raise ParseError('malformed', 'Invalid source URL') from exc


def parse(raw_bytes: bytes) -> ParsedBatch:
    """Parse bytes into artifact-local source records, never canonical finding IDs."""
    if type(raw_bytes) is not bytes:
        raise TypeError('parse accepts bytes only')
    if len(raw_bytes) > MAX_BYTES:
        raise ParseError('resource_limit', 'Input exceeds 20 MiB')
    # Bound container nesting before JSON decoding, respecting quoted brackets.
    depth = 0
    quoted = escaped = False
    for byte in raw_bytes:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            if depth > 64:
                raise ParseError('resource_limit', 'Input depth exceeds 64')
        elif byte in (93, 125):
            depth -= 1
    def invalid_constant(_):
        raise ParseError('malformed', 'Nonfinite JSON number')
    try:
        root = json.loads(raw_bytes.decode('utf-8'), object_pairs_hook=_pairs,
                          parse_constant=invalid_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        if isinstance(exc, ParseError):
            raise
        raise ParseError('malformed', 'Invalid UTF-8 JSON') from exc
    if (not isinstance(root, dict) or not isinstance(root.get('site'), list)
            or not isinstance(root.get('@programName'), str)
            or not isinstance(root.get('@version'), str)):
        raise ParseError('unsupported_format', 'Expected traditional report with producer and site array')
    warnings, observations = [], []
    if len(root['site']) > MAX_RECORDS:
        raise ParseError('resource_limit', 'Too many sites')
    visited = 0
    for s, site in enumerate(root['site']):
        if not isinstance(site, dict) or not isinstance(site.get('alerts'), list):
            raise ParseError('malformed', 'Expected site alerts array')
        origin = _origin(_string(site.get('@name'), True))
        for a, alert in enumerate(site['alerts']):
            visited += 1
            if visited > MAX_RECORDS:
                raise ParseError('resource_limit', 'Too many records')
            if not isinstance(alert, dict) or not isinstance(alert.get('instances'), list):
                raise ParseError('malformed', 'Expected alert instances array')
            pointer = f'/site/{s}/alerts/{a}'
            plugin = _string(alert.get('pluginid'), True)
            alert_ref = _string(alert.get('alertRef'))
            risk = _string(alert.get('riskcode'), True)
            confidence = _string(alert.get('confidence'), True)
            severity = {'0': 'informational', '1': 'low', '2': 'medium', '3': 'high'}.get(risk, 'unknown')
            if severity == 'unknown':
                warnings.append(Warning('unknown_risk', pointer))
            count = _string(alert.get('count'), True)
            if not re.fullmatch(r'\d{1,10}', count):
                raise ParseError('malformed', 'Invalid instance count')
            if int(count) != len(alert['instances']):
                warnings.append(Warning('count_mismatch', pointer))
            if not alert['instances']:
                warnings.append(Warning('empty_alert', pointer))
            for i, instance in enumerate(alert['instances']):
                visited += 1
                if visited > MAX_RECORDS:
                    raise ParseError('resource_limit', 'Too many records')
                if not isinstance(instance, dict):
                    raise ParseError('malformed', 'Expected instance object')
                locator = f'{pointer}/instances/{i}'
                uri = _string(instance.get('uri'), True)
                if _origin(uri) != origin:
                    warnings.append(Warning('origin_mismatch', locator))
                    continue
                observations.append(Observation(
                    locator, 'zap:' + (alert_ref or plugin), plugin, alert_ref,
                    _string(instance.get('id')), uri, _string(instance.get('method')),
                    _string(instance.get('param')) or None, _string(alert.get('alert'), True),
                    _string(alert.get('desc')), _string(alert.get('solution')),
                    _string(alert.get('reference')), _string(alert.get('cweid')),
                    _string(instance.get('evidence')), _string(instance.get('attack')),
                    _string(instance.get('otherinfo')), risk, severity, confidence,
                ))
    return ParsedBatch(hashlib.sha256(raw_bytes).hexdigest(), VERSION,
                       _string(root['@version'], True), tuple(observations),
                       tuple(warnings), 'partial' if warnings else 'succeeded')
