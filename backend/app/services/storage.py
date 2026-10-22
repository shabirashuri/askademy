import os
import uuid
from collections.abc import Iterable
from pathlib import Path
from typing import BinaryIO, Protocol

from app.core.config import settings

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class StorageBackend(Protocol):
    def save(self, key: str, chunks: Iterable[bytes]) -> None: ...

    def open(self, key: str) -> BinaryIO: ...

    def delete(self, key: str) -> None: ...


class LocalStorage:
    """Stores files on local disk under a root directory; keys are relative paths."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Invalid storage key.")
        return path

    def save(self, key: str, chunks: Iterable[bytes]) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_name(f"{path.name}.{uuid.uuid4().hex}.part")
        try:
            with open(partial, "wb") as out:
                for chunk in chunks:
                    out.write(chunk)
            os.replace(partial, path)
        except BaseException:
            partial.unlink(missing_ok=True)
            raise

    def open(self, key: str) -> BinaryIO:
        return open(self._path(key), "rb")  # noqa: SIM115 - caller closes

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)


def get_storage() -> StorageBackend:
    root = Path(settings.storage_dir)
    return LocalStorage(root if root.is_absolute() else BACKEND_ROOT / root)
