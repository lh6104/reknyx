"""Private immutable bytes and durable publication receipts.

Each write retains a receipt even if its caller's DB transaction rolls back.
Reconciliation is read-only: no automatic deletion can destroy evidence.
"""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from uuid import uuid4


class IntegrityError(Exception):
    pass


@dataclass(frozen=True)
class StoredBlob:
    storage_key: str
    sha256: str
    size: int


class LocalArtifactStore:
    def __init__(self, root, max_bytes=20 * 1024 * 1024):
        path = Path(root).absolute()
        if path.is_symlink() or any(p.is_symlink() for p in path.parents):
            raise ValueError("Artifact root must not traverse symlinks")
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(path, 0o700)
        self.root, self.max_bytes = path, max_bytes

    def _open_root(self):
        return os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)

    def put(self, content):
        if type(content) is not bytes or not 0 < len(content) <= self.max_bytes:
            raise ValueError("Artifact bytes must be nonempty and within the hard size limit")
        key, temp = uuid4().hex, ".pending-" + uuid4().hex
        digest = hashlib.sha256(content).hexdigest()
        root_fd = self._open_root()
        try:
            fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=root_fd)
            with os.fdopen(fd, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            # Persist the receipt first. A crash may leave a receipt without a blob;
            # reconciliation reports that gap rather than claiming publication.
            receipt_fd = os.open(key + ".receipt", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=root_fd)
            with os.fdopen(receipt_fd, "w") as stream:
                json.dump({"storage_key": key, "sha256": digest, "size_bytes": len(content)}, stream)
                stream.flush()
                os.fsync(stream.fileno())
            # link is atomic and refuses an existing destination, unlike replace.
            os.link(temp, key, src_dir_fd=root_fd, dst_dir_fd=root_fd, follow_symlinks=False)
            os.unlink(temp, dir_fd=root_fd)
            os.fsync(root_fd)
        finally:
            os.close(root_fd)
        return StoredBlob(key, digest, len(content))

    def get(self, storage_key, expected_sha256=None):
        if not isinstance(storage_key, str) or not re.fullmatch(r"[0-9a-f]{32}", storage_key):
            raise ValueError("Invalid internal storage identifier")
        root_fd = self._open_root()
        try:
            fd = os.open(storage_key, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=root_fd)
            with os.fdopen(fd, "rb") as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_size > self.max_bytes:
                    raise IntegrityError("Artifact is not a bounded regular file")
                raw = stream.read(self.max_bytes + 1)
            if len(raw) > self.max_bytes or (expected_sha256 is not None and hashlib.sha256(raw).hexdigest() != expected_sha256):
                raise IntegrityError("Artifact checksum mismatch")
            return raw
        except OSError as exc:
            raise IntegrityError("Artifact bytes unavailable") from exc
        finally:
            os.close(root_fd)

    def reconcile(self, referenced_keys):
        """Read-only diagnostics, including DB rollback or crash publication gaps."""
        referenced = set(referenced_keys)
        blobs = {p.name for p in self.root.iterdir() if re.fullmatch(r"[0-9a-f]{32}", p.name)}
        receipts = {p.name.removesuffix(".receipt") for p in self.root.glob("*.receipt")}
        return {"unreferenced_blobs": sorted(blobs - referenced), "missing_blobs": sorted(referenced - blobs), "receipt_without_blob": sorted(receipts - blobs), "pending_files": sorted(p.name for p in self.root.glob(".pending-*"))}
