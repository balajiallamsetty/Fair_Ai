"""Storage abstraction for dataset and model artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class StorageBackend(Protocol):
    """Abstract storage backend for persisted artifacts."""

    def save_bytes(self, path: str, data: bytes) -> str:
        """Persist bytes and return a normalized storage path."""

    def save_text(self, path: str, data: str) -> str:
        """Persist text and return a normalized storage path."""


@dataclass
class LocalFilesystemStorage:
    """Local filesystem storage implementation."""

    base_dir: Path

    def _resolve(self, path: str) -> Path:
        resolved = self.base_dir / path
        resolved.parent.mkdir(parents=True, exist_ok=True)
        return resolved

    def save_bytes(self, path: str, data: bytes) -> str:
        resolved = self._resolve(path)
        resolved.write_bytes(data)
        return str(resolved)

    def save_text(self, path: str, data: str) -> str:
        resolved = self._resolve(path)
        resolved.write_text(data, encoding="utf-8")
        return str(resolved)


def get_storage_backend(base_dir: Path) -> StorageBackend:
    """Return the default storage backend."""

    return LocalFilesystemStorage(base_dir=base_dir)
