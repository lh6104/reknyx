"""Polling worker for immutable-byte imports and frozen-snapshot reports."""
import argparse
import logging
import signal
import time
from reknyx.config import Settings
from reknyx.evidence.storage import LocalArtifactStore
from reknyx.infrastructure.db import build_database
from reknyx.orchestration.import_worker import process_one as import_one
from reknyx.reporting.service import process_one as report_one


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    settings = Settings.from_env()
    engine, factory = build_database(settings)
    store = LocalArtifactStore(settings.artifact_root, settings.max_artifact_bytes)
    stopped = False
    def stop(_signum, _frame):
        nonlocal stopped
        stopped = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while not stopped:
            try:
                imported = import_one(factory, store)
                reported = report_one(factory, store)
            except Exception:
                logging.error('Worker operation failed; inspect private durable job state')
                if args.once:
                    raise SystemExit(1)
                imported = reported = False
            if args.once:
                break
            if not imported and not reported:
                time.sleep(1)
    finally:
        engine.dispose()

if __name__ == '__main__':
    main()
