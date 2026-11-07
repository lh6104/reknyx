"""Bounded, IO-free Greenbone/GMP XML report parser.

Only one completed report is accepted. Original bytes must be stored first;
worker process limits apply in addition to the structural limits here.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import ipaddress
import re
from xml.etree.ElementTree import TreeBuilder
from xml.parsers import expat

VERSION = 'greenbone_xml_results_v1.0'
MAX_BYTES = 20 * 1024 * 1024
MAX_RECORDS = 10000

class ParseError(ValueError):
    pass

@dataclass(frozen=True)
class Warning:
    code: str
    raw_locator: str

@dataclass(frozen=True)
class Observation:
    raw_locator: str
    native_id: str
    rule_id: str
    address: str
    hostname: str | None
    port: int | None
    protocol: str
    raw_port: str
    title: str
    description: str | None
    solution: str | None
    raw_severity: str
    raw_threat: str | None
    raw_confidence: str | None
    qod_type: str | None
    severity: str
    kind: str
    cve_ids: tuple[str, ...]
    cvss: float | None
    cvss_vector: str | None
    cvss_version: str | None
    cvss_source: str | None
    native_nvt_xml: str
    native_result_xml: str
    report_id: str | None

@dataclass(frozen=True)
class ParsedBatch:
    sha256: str
    parser_version: str
    producer_version: str
    observations: tuple[Observation, ...]
    warnings: tuple[Warning, ...]
    outcome: str


def _text(node, path, required=False):
    value = node.findtext(path)
    value = value.strip() if value else None
    if required and not value:
        raise ParseError('malformed: missing ' + path)
    return value


def _score(value, low=0, high=10):
    try:
        number = Decimal(value)
        if not number.is_finite() or not low <= number <= high:
            raise InvalidOperation
        return float(number)
    except (InvalidOperation, TypeError, ValueError):
        raise ParseError('malformed: invalid numeric source field') from None


def parse(raw_bytes: bytes) -> ParsedBatch:
    if type(raw_bytes) is not bytes:
        raise TypeError('parse accepts bytes only')
    if len(raw_bytes) > MAX_BYTES:
        raise ParseError('resource_limit: input exceeds 20 MiB')
    builder, parser = TreeBuilder(), expat.ParserCreate()
    depth = count = 0
    def start(name, attrs):
        nonlocal depth, count
        depth += 1
        count += 1
        if depth > 64 or count > 100000 or any(len(v)>100000 for v in attrs.values()):
            raise ParseError('resource_limit: XML structure exceeded')
        builder.start(name, attrs)
    def end(name):
        nonlocal depth
        builder.end(name)
        depth -= 1
    def reject(*args):
        raise ParseError('malformed: XML document types and entities are prohibited')
    parser.StartElementHandler, parser.EndElementHandler = start, end
    parser.CharacterDataHandler = builder.data
    parser.StartDoctypeDeclHandler = parser.EntityDeclHandler = parser.ExternalEntityRefHandler = reject
    try:
        parser.Parse(raw_bytes, True)
        root = builder.close()
    except expat.ExpatError as exc:
        raise ParseError('malformed: invalid XML') from exc
    for element in root.iter():
        if len(element.text or '') > 100000:
            raise ParseError('resource_limit: source text exceeded')
    prefix = '/' + root.tag
    if root.tag == 'get_reports_response':
        if root.get('status') != '200' or len(root.findall('report')) != 1:
            raise ParseError('unsupported_format: expected one successful report')
        root = root.find('report')
        prefix += '/report'
    if root.tag != 'report':
        raise ParseError('unsupported_format: expected Greenbone XML report')
    if root.find('report') is not None:
        if len(root.findall('report')) != 1:
            raise ParseError('unsupported_format: multiple reports')
        root = root.find('report')
        prefix += '/report'
    if root.find('results') is None or len(root.findall('results')) != 1:
        raise ParseError('unsupported_format: missing result collection')
    if _text(root, 'scan_run_status') != 'Done':
        raise ParseError('incomplete: completed report required')
    rows = root.findall('results/result')
    if len(rows) > MAX_RECORDS:
        raise ParseError('resource_limit: too many results')
    warnings, observations = [], []
    filtered = _text(root, 'result_count/filtered')
    if filtered is not None:
        if not re.fullmatch(r'\d{1,10}', filtered) or int(filtered) < len(rows):
            raise ParseError('malformed: inconsistent result count')
        if int(filtered) != len(rows):
            warnings.append(Warning('incomplete_export', prefix+'/results'))
    ids = set()
    from xml.etree.ElementTree import tostring
    for index, row in enumerate(rows, 1):
        locator = f'{prefix}/results/result[{index}]'
        native_id, nvt = row.get('id'), row.find('nvt')
        if not native_id or len(native_id)>200 or native_id in ids or nvt is None or not re.fullmatch(r'[0-9]+(?:\.[0-9]+)+', nvt.get('oid','')):
            raise ParseError('malformed: missing or duplicate result identity/NVT OID')
        ids.add(native_id)
        address = _text(row, 'host', True)
        try:
            ipaddress.ip_address(address)
        except ValueError:
            if len(address)>253 or not re.fullmatch(r'[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?', address):
                raise ParseError('malformed: invalid source host') from None
        raw_port = _text(row, 'port', True)
        match = re.fullmatch(r'(\d+|general)/(tcp|udp|icmp)', raw_port)
        if not match or (match[1]!='general' and not 1<=int(match[1])<=65535):
            raise ParseError('unsupported_format: unsupported source port')
        port = None if match[1]=='general' else int(match[1])
        raw_severity = _text(row, 'severity', True)
        score = _score(raw_severity, -3, 10)
        threat = _text(row, 'threat')
        kind = 'vulnerability' if score>0 else 'informational'
        severity = 'critical' if score>=9 else 'high' if score>=7 else 'medium' if score>=4 else 'low' if score>0 else 'informational' if score==0 else 'unknown'
        if score<0:
            warnings.append(Warning('source_error_or_false_positive', locator))
        qod = _text(row,'qod/value')
        if qod is not None:
            _score(qod,0,100)
        cves = set()
        candidates = [ref.get('id','') for ref in nvt.findall('refs/ref') if ref.get('type','').lower()=='cve']
        candidates += re.split(r'[,\s]+', _text(nvt,'cve') or '')
        for cve in candidates:
            if re.fullmatch(r'CVE-\d{4}-\d{4,}', cve): cves.add(cve)
        if len(cves)>100:
            raise ParseError('resource_limit: too many CVE references')
        cvss = vector = version = cvss_source = None
        # A result severity is not necessarily a CVSS base score (overrides apply).
        # Promote only an explicit paired source score and supported vector.
        for candidate in nvt.findall('severities/severity'):
            value, supplied_score = _text(candidate,'value'), _text(candidate,'score')
            if value and supplied_score and re.fullmatch(r'CVSS:3\.[01]/AV:[NALP]/AC:[LH]/PR:[NLH]/UI:[NR]/S:[UC]/C:[NLH]/I:[NLH]/A:[NLH]',value):
                cvss, vector, version = _score(supplied_score), value, value[5:8]
                cvss_source = 'Greenbone NVT ' + nvt.get('oid')
                origin = _text(candidate, 'origin')
                if origin:
                    cvss_source += ' (' + origin + ')'
                break
        tags = dict(part.split('=',1) for part in (_text(nvt,'tags') or '').split('|') if '=' in part)
        solution = _text(row,'solution') or tags.get('solution')
        observations.append(Observation(locator,native_id,'greenbone:'+nvt.get('oid'),address,
            _text(row,'host/hostname'),port,match[2],raw_port,_text(row,'name',True),
            _text(row,'description'),solution,raw_severity,threat,qod,_text(row,'qod/type'),
            severity,kind,tuple(sorted(cves)),cvss,vector,version,cvss_source,
            tostring(nvt,encoding='unicode'),tostring(row,encoding='unicode'),root.get('id')))
    if len(warnings)>100:
        raise ParseError('resource_limit: too many warnings')
    return ParsedBatch(hashlib.sha256(raw_bytes).hexdigest(),VERSION,_text(root,'gmp/version') or 'unknown',tuple(observations),tuple(warnings),'partial' if warnings else 'succeeded')
