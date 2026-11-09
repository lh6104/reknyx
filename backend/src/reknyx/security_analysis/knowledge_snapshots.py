"""Operator-only private snapshot archive; no fetching or assessment mutation.

Original bytes are retained before parsing. The caller owns persistence of the
returned receipt. Existing artifact receipts expose publication gaps honestly;
this module neither deletes orphan bytes nor automatically changes active snapshots.
"""
import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import re
import stat
import tempfile

from reknyx.contracts import canonical_request, parse_json
from reknyx.evidence.storage import LocalArtifactStore, IntegrityError
from .knowledge import load_snapshot

VERSION = 'knowledge-snapshot-import-v1'
MAX_BYTES = 2 * 1024 * 1024


class KnowledgeImportError(ValueError):
    def __init__(self, code, raw):
        super().__init__(code)
        self.code, self.raw = code, raw


def ingest_snapshot(store, raw: bytes) -> dict:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise ValueError('invalid_source_size')
    source = asdict(store.put(raw))
    try:
        snapshot = load_snapshot(parse_json(raw))
    except (ValueError, TypeError, RecursionError):
        raise KnowledgeImportError('invalid_snapshot', source) from None
    normalized = asdict(store.put(canonical_request(snapshot)))
    return {'version': VERSION, 'status': 'ready', 'raw': source, 'normalized': normalized,
            'snapshot_sha256': snapshot['sha256'], 'snapshot_version': snapshot['version'],
            'document_count': len(snapshot['documents'])}


def _read_blob(store, value):
    if (not isinstance(value, dict) or set(value) != {'storage_key','sha256','size'}
            or not isinstance(value['storage_key'], str) or not re.fullmatch('[a-f0-9]{32}',value['storage_key'])
            or not isinstance(value['sha256'], str) or not re.fullmatch('[a-f0-9]{64}',value['sha256'])
            or type(value['size']) is not int or not 1 <= value['size'] <= MAX_BYTES + 4096):
        raise ValueError('invalid_blob_receipt')
    raw = store.get(value['storage_key'],value['sha256'])
    if len(raw) != value['size']:
        raise IntegrityError('Snapshot byte size mismatch')
    return raw


def read_snapshot(store, receipt: dict) -> dict:
    if (not isinstance(receipt, dict) or set(receipt) != {'version','status','raw','normalized',
            'snapshot_sha256','snapshot_version','document_count'}
            or receipt['version'] != VERSION or receipt['status'] != 'ready'
            or type(receipt['document_count']) is not int):
        raise ValueError('invalid_snapshot_receipt')
    original = _read_blob(store,receipt['raw'])
    normalized = _read_blob(store,receipt['normalized'])
    try:
        snapshot = load_snapshot(parse_json(original))
        parsed_normalized = parse_json(normalized)
    except (ValueError, TypeError, RecursionError):
        raise IntegrityError('Invalid stored snapshot encoding') from None
    if (parsed_normalized != snapshot or canonical_request(snapshot) != normalized
            or snapshot['sha256'] != receipt['snapshot_sha256']
            or snapshot['version'] != receipt['snapshot_version']
            or len(snapshot['documents']) != receipt['document_count']):
        raise IntegrityError('Snapshot receipt does not match its source bytes')
    return snapshot


def _read_file(path, limit):
    fd = os.open(path,os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            raise ValueError('bounded_regular_file_required')
        raw = stream.read(limit + 1)
        if len(raw) > limit:
            raise ValueError('source_size_limit')
        return raw


def _sync_directory(path):
    fd = os.open(path,os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _publish_receipt(path, value):
    pending = None
    try:
        with tempfile.NamedTemporaryFile(mode='w',dir=path.parent,prefix='.'+path.name+'-',delete=False) as stream:
            pending = Path(stream.name)
            json.dump(value,stream,indent=2)
            stream.flush(); os.fsync(stream.fileno())
        os.replace(pending,path)
        _sync_directory(path.parent)
    finally:
        if pending is not None and pending.exists():
            pending.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='operation',required=True)
    for operation in ('import','verify'):
        command = commands.add_parser(operation)
        command.add_argument('--archive-root',type=Path,required=True)
        command.add_argument('--receipt',type=Path,required=True)
        if operation == 'import':
            command.add_argument('--input',type=Path,required=True)
    args = parser.parse_args(argv)
    if args.operation == 'verify':
        try:
            receipt = parse_json(_read_file(args.receipt,16384))
            snapshot = read_snapshot(LocalArtifactStore(args.archive_root),receipt)
        except (OSError,ValueError,IntegrityError,RecursionError):
            print('Snapshot verification failed; no source bytes were modified.')
            return 2
        print(json.dumps({'status':'verified','snapshot_sha256':snapshot['sha256'],
                          'document_count':len(snapshot['documents'])}))
        return 0
    try:
        fd = os.open(args.receipt,os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,0o600)
    except OSError:
        print('Receipt must be a new writable private file; no snapshot was imported.')
        return 2
    try:
        with os.fdopen(fd,'w') as stream:
            json.dump({'version':VERSION,'status':'pending',
                       'limitation':'Reconcile publication receipts after interruption; do not blindly repeat imports.'},stream,indent=2)
            stream.flush(); os.fsync(stream.fileno())
        _sync_directory(args.receipt.parent)
        raw = _read_file(args.input,MAX_BYTES)
        receipt = ingest_snapshot(LocalArtifactStore(args.archive_root),raw)
        _publish_receipt(args.receipt,receipt)
    except KnowledgeImportError as exc:
        try:
            _publish_receipt(args.receipt,{'version':VERSION,'status':'rejected','reason':exc.code,'raw':exc.raw})
        except OSError:
            print('Rejection publication failed; reconcile pending receipt and archive publication records.')
            return 2
        print('Snapshot rejected; original bytes retained in the private archive.')
        return 1
    except (OSError,ValueError,IntegrityError):
        print('Import did not finish; reconcile pending receipt and archive publication records.')
        return 2
    print(json.dumps({'status':'ready','snapshot_sha256':receipt['snapshot_sha256'],
                      'document_count':receipt['document_count']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
