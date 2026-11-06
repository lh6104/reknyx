"""Strict v1 authority JSON encoding; this is deliberately not general JCS."""
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import re

SAFE_INTEGER = 9007199254740991
PROFILES = ("nmap_discovery_v1", "zap_baseline_v1")


def _object(value, fields):
    if type(value) is not dict or set(value) != set(fields):
        raise ValueError("authority object has missing or unknown fields")
    return {key: fields[key](value[key]) for key in fields}


def _string(value):
    if type(value) is not str or not value.isascii():
        raise ValueError("authority string must be ASCII")
    return value


def _integer(low, high=SAFE_INTEGER):
    def validate(value):
        if type(value) is not int or not low <= value <= high:
            raise ValueError("authority integer outside allowed range")
        return value
    return validate


def _enum(*values):
    def validate(value):
        if type(value) is not str or value not in values:
            raise ValueError("unsupported authority enum")
        return value
    return validate


def _uuid(value):
    value = _string(value)
    if not re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", value):
        raise ValueError("expected hyphenated UUID")
    return value.lower()


def _hostname(value):
    value = _string(value).lower()
    if value.endswith("."):
        value = value[:-1]
    if len(value) > 253 or not value or any(
        not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
        for label in value.split(".")
    ):
        raise ValueError("expected ASCII DNS hostname")
    return value


def _ipv4(value):
    value = _string(value)
    try:
        address = ipaddress.IPv4Address(value)
    except ipaddress.AddressValueError as exc:
        raise ValueError("expected canonical dotted IPv4") from exc
    if str(address) != value:
        raise ValueError("expected canonical dotted IPv4")
    return value


def _timestamp(value):
    value = _string(value)
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:Z|[+-][0-9]{2}:[0-9]{2})", value):
        raise ValueError("expected second-precision timestamp")
    if value.endswith("-00:00"):
        raise ValueError("unknown timezone is not authority")
    suffix = value[-6:]
    if suffix[0] in "+-" and (int(suffix[1:3]) > 23 or int(suffix[4:6]) > 59):
        raise ValueError("invalid timezone offset")
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, OverflowError) as exc:
        raise ValueError("invalid timestamp") from exc
    return f"{instant.year:04d}-{instant.month:02d}-{instant.day:02d}T{instant.hour:02d}:{instant.minute:02d}:{instant.second:02d}Z"


def _set(item, low=0, high=32):
    def validate(value):
        if type(value) is not list or not low <= len(value) <= high:
            raise ValueError("authority set outside allowed bounds")
        result = [item(member) for member in value]
        if len(result) != len(set(result)):
            raise ValueError("duplicate authority set member")
        return sorted(result)
    return validate


def _boolean(value):
    if type(value) is not bool:
        raise ValueError("expected boolean")
    return value


def _nullable_hostname(value):
    return None if value is None else _hostname(value)


def _asset(value):
    return _object(value, {"id": _uuid, "hostname": _nullable_hostname, "ipv4": _ipv4,
                           "aliases": _set(_hostname, 0, 16), "authorization_ref_id": _uuid})


def _budget(value):
    return _object(value, {"max_actions": _integer(0, 8), "max_runtime_seconds": _integer(0, 3600),
                           "max_model_calls": _integer(0, 8), "max_input_tokens": _integer(0, 1000000),
                           "max_output_tokens": _integer(0, 1000000)})


def _digest(value):
    if not re.fullmatch(r"[0-9a-f]{64}", _string(value)):
        raise ValueError("expected lowercase SHA-256")
    return value


def normalize(kind, payload):
    """Validate and copy one authority object into its normalized representation."""
    if kind == "scope":
        return _object(payload, {
            "assessment_id": _uuid, "version": _integer(1), "authorization_ref_id": _uuid,
            "asset": _asset, "allowed_ports": _set(_integer(1, 65535), 1, 16),
            "excluded_ports": _set(_integer(1, 65535), 0, 16),
            "allowed_profiles": _set(_enum(*PROFILES), 0, 2), "valid_from": _timestamp,
            "valid_until": _timestamp, "budget": _budget, "origin_wide": _boolean,
        })
    if kind == "action":
        if type(payload) is not dict or payload.get("profile") not in PROFILES:
            raise ValueError("unsupported action profile")
        if payload["profile"] == "nmap_discovery_v1":
            parameters = {"ports": _set(_integer(1, 65535), 1, 16), "deadline_seconds": _integer(1, 120)}
        else:
            parameters = {"scheme": _enum("http", "https"), "port": _integer(1, 65535),
                          "root_path": _enum("/"), "deadline_seconds": _integer(1, 180)}
        return _object(payload, {
            "action_id": _uuid, "assessment_id": _uuid, "state_revision": _integer(1),
            "profile": _enum(*PROFILES), "profile_version": _enum("1"), "target": _asset,
            "parameters": lambda value: _object(value, parameters), "scope_hash": _digest,
            "scope_version": _integer(1), "basis_observation_ids": _set(_uuid),
            "expires_at": _timestamp,
            "budget": lambda value: _object(value, {"actions": _integer(1, 1), "runtime_seconds": _integer(1, 180)}),
        })
    raise ValueError("unknown authority kind")


def canonical_bytes(kind, payload):
    """Return sorted-key compact ASCII JSON as UTF-8 with no newline or prefix."""
    return json.dumps(normalize(kind, payload), sort_keys=True, ensure_ascii=True,
                      allow_nan=False, separators=(",", ":")).encode("utf-8")


def authority_hash(kind, payload):
    """Return the lowercase SHA-256 digest of the complete canonical bytes."""
    return hashlib.sha256(canonical_bytes(kind, payload)).hexdigest()
