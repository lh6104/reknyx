from datetime import datetime, timezone


def now():
    # Internal keyset ordering retains subsecond precision. Public timestamps use
    # the contract's UTC-second encoding in timestamp().
    return datetime.now(timezone.utc)


def timestamp(value=None):
    return (value or now()).astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
