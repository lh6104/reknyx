"""Offline configuration check: python -m reknyx.security_analysis.check_setup."""
import json
from reknyx.config import Settings
from .readiness import describe


def main():
    try:
        result=describe(Settings.from_env())
    except (KeyError,ValueError):
        print(json.dumps({'reason_code':'invalid_server_configuration','message':'Load a complete valid backend environment first. No provider request was sent.'}))
        return 2
    print(json.dumps({**result,'verification':'offline_configuration_only','provider_request_sent':False}))
    return 0 if result['reason_code'] in ('local_review_ready','groq_configured') else 1


if __name__=='__main__':
    raise SystemExit(main())
