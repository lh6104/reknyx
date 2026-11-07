"""Pure Nmap XML service parser. Run in an isolated, time-limited process.

The caller must retain original bytes first. This parser performs no network IO,
does not allocate canonical IDs, and does not infer vulnerabilities.
"""
from dataclasses import dataclass
import hashlib
import ipaddress
from xml.etree.ElementTree import TreeBuilder
from xml.parsers import expat

VERSION = 'nmap_xml_services_v1.0'
MAX_BYTES = 20 * 1024 * 1024
MAX_RECORDS = 10000


class ParseError(ValueError):
    pass


@dataclass(frozen=True)
class Observation:
    raw_locator: str
    address: str
    address_type: str
    protocol: str
    port: int
    state: str
    service_name: str | None
    product: str | None
    kind: str = 'service'


@dataclass(frozen=True)
class ParsedBatch:
    sha256: str
    parser_version: str
    producer_version: str
    observations: tuple[Observation, ...]
    outcome: str


def parse(raw_bytes: bytes) -> ParsedBatch:
    if type(raw_bytes) is not bytes:
        raise TypeError('parse accepts bytes only')
    if len(raw_bytes) > MAX_BYTES:
        raise ParseError('resource_limit: input exceeds 20 MiB')
    builder = TreeBuilder()
    parser = expat.ParserCreate()
    depth = count = 0

    def start(name, attrs):
        nonlocal depth, count
        depth += 1
        count += 1
        if depth > 64 or count > 100000:
            raise ParseError('resource_limit: XML nesting or elements exceeded')
        builder.start(name, attrs)

    def end(name):
        nonlocal depth
        builder.end(name)
        depth -= 1

    def doctype(name, system_id, public_id, internal):
        if name != 'nmaprun' or system_id or public_id or internal:
            raise ParseError('malformed: unsupported document type')

    def reject_entity(*_args):
        raise ParseError('malformed: XML entities are prohibited')

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CharacterDataHandler = builder.data
    parser.StartDoctypeDeclHandler = doctype
    parser.EntityDeclHandler = reject_entity
    parser.ExternalEntityRefHandler = reject_entity
    try:
        parser.Parse(raw_bytes, True)
        root = builder.close()
    except expat.ExpatError as exc:
        raise ParseError('malformed: invalid XML') from exc
    if root.tag != 'nmaprun' or root.get('scanner') != 'nmap' or not root.get('version'):
        raise ParseError('unsupported_format: expected Nmap report with version')
    finished = root.find('runstats/finished')
    if finished is None or finished.get('exit') != 'success':
        raise ParseError('incomplete: scan completion is not established')

    observations = []
    visited = 0
    for host_index, host in enumerate(root.findall('host'), 1):
        addresses = []
        for address in host.findall('address'):
            kind, value = address.get('addrtype'), address.get('addr')
            if kind in ('ipv4', 'ipv6'):
                try:
                    parsed = ipaddress.ip_address(value)
                    if parsed.version != (4 if kind == 'ipv4' else 6):
                        raise ValueError('address family mismatch')
                except ValueError as exc:
                    raise ParseError('malformed: invalid IP address') from exc
                addresses.append((value, kind))
        ports = host.find('ports')
        if ports is None:
            continue
        for port_index, port in enumerate(ports.findall('port'), 1):
            visited += 1
            if visited > MAX_RECORDS:
                raise ParseError('resource_limit: too many ports')
            state = port.find('state')
            if state is None or not state.get('state'):
                raise ParseError('malformed: missing port state')
            if state.get('state') != 'open':
                continue
            protocol, port_number = port.get('protocol'), port.get('portid', '')
            if protocol not in ('tcp', 'udp', 'sctp') or not port_number.isascii() or not port_number.isdecimal() or not 1 <= int(port_number) <= 65535 or not addresses:
                raise ParseError('malformed: invalid port or missing address')
            service = port.find('service')
            for address, address_type in addresses:
                if len(observations) >= MAX_RECORDS:
                    raise ParseError('resource_limit: too many observations')
                observations.append(Observation(
                    f'/nmaprun/host[{host_index}]/ports/port[{port_index}]',
                    address, address_type, protocol, int(port_number), 'open',
                    service.get('name') if service is not None else None,
                    service.get('product') if service is not None else None,
                ))
    return ParsedBatch(hashlib.sha256(raw_bytes).hexdigest(), VERSION, root.get('version'), tuple(observations), 'succeeded')
