import os
import re
import tempfile
from pathlib import Path

from launchcase.domain.common import DomainError, digest


class ObjectStore:
    def __init__(self, root: Path):
        self.root = root / "objects"
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink():
            raise DomainError("UNSAFE_PATH", "Object root must not be a symlink")

    def path(self, sha: str):
        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise DomainError("UNSAFE_PATH", "Invalid content address")
        p = self.root / sha
        if p.is_symlink():
            raise DomainError("UNSAFE_PATH", "Object symlink rejected")
        return p

    def put(self, data: bytes) -> str:
        sha = digest(data)
        path = self.path(sha)
        if path.exists():
            self.get(sha)
            return sha
        fd, temp = tempfile.mkstemp(dir=self.root)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp, path)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
        return sha

    def get(self, sha: str) -> bytes:
        try:
            with os.fdopen(os.open(self.path(sha), os.O_RDONLY | os.O_NOFOLLOW), "rb") as f:
                data = f.read()
        except OSError as exc:
            raise DomainError("OBJECT_UNAVAILABLE", "Original object is unavailable", 409) from exc
        if digest(data) != sha:
            raise DomainError("OBJECT_CORRUPT", "Original object hash changed; review/export blocked", 409)
        return data


def read_import_file(path: Path) -> str:
    if ".." in path.parts or any(p.is_symlink() for p in [path, *path.parents]):
        raise DomainError("UNSAFE_PATH", "Traversal and symlink imports are not accepted")
    if not path.is_file() or path.stat().st_size > 1048576:
        raise DomainError("UNSAFE_FILE", "Expected a text file up to 1 MiB")
    return path.read_text(encoding="utf-8-sig")
