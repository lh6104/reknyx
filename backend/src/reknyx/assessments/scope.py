"""Pure destination checks; they do not establish live authorization or DNS policy."""
from datetime import datetime
import ipaddress

from reknyx.contracts import HASH_AUTHORITY
from reknyx.shared.time import now


def allows_destination(scope, host, port, *, clock=now):
    if type(port) is not int or not 1 <= port <= 65535 or not isinstance(host, str):
        return False
    try:
        value = {key: item for key, item in scope.items() if key != "hash"}
        normalized = HASH_AUTHORITY.normalize("scope", value)
        start = datetime.fromisoformat(normalized["valid_from"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(normalized["valid_until"].replace("Z", "+00:00"))
        if not start <= clock() < end or port in normalized["excluded_ports"] or port not in normalized["allowed_ports"]:
            return False
        asset = normalized["asset"]
        try:
            return str(ipaddress.ip_address(host)) == asset["ipv4"]
        except ValueError:
            canonical = HASH_AUTHORITY._hostname(host)
            return canonical in [asset["hostname"], *asset["aliases"]]
    except (ValueError, KeyError, TypeError):
        return False
