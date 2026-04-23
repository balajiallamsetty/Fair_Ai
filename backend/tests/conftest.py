"""Pytest fixtures for Fair-AI Guardian backend tests."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import ObjectId


os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGO_DATABASE", "fair_ai_guardian_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "0123456789abcdef0123456789abcdef")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("MODEL_ARTIFACTS_DIR", "backend/artifacts/models")
os.environ.setdefault("DATASET_ARTIFACTS_DIR", "backend/artifacts/datasets")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("FAIRNESS_MONITOR_WINDOW", "50")
os.environ.setdefault("PREDICTION_BIAS_THRESHOLD", "0.2")
os.environ.setdefault("MONGO_MAX_POOL_SIZE", "5")
os.environ.setdefault("MONGO_MIN_POOL_SIZE", "1")
os.environ.setdefault("MONGO_SERVER_SELECTION_TIMEOUT_MS", "1000")
os.environ.setdefault("MONGO_CONNECT_TIMEOUT_MS", "1000")
os.environ.setdefault("MONGO_SOCKET_TIMEOUT_MS", "1000")

from backend.app.core.database import mongo_db


@dataclass
class InsertOneResult:
    """Simple insert-one result object."""

    inserted_id: ObjectId


class FakeCursor:
    """Async iterable cursor for fake MongoDB collections."""

    def __init__(self, documents: list[dict[str, Any]]):
        self._documents = documents

    def sort(self, key: str, direction: int):
        self._documents.sort(key=lambda item: item.get(key), reverse=direction < 0)
        return self

    def skip(self, amount: int):
        self._documents = self._documents[amount:]
        return self

    def limit(self, amount: int):
        self._documents = self._documents[:amount]
        return self

    def __aiter__(self):
        self._iterator = iter(self._documents)
        return self

    async def __anext__(self):
        try:
            return next(self._iterator)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


def _matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, value in query.items():
        if document.get(key) != value:
            return False
    return True


class FakeCollection:
    """In-memory collection with a tiny MongoDB-like API."""

    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    async def insert_one(self, document: dict[str, Any]) -> InsertOneResult:
        stored = dict(document)
        stored.setdefault("_id", ObjectId())
        self.documents.append(stored)
        return InsertOneResult(inserted_id=stored["_id"])

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        for document in self.documents:
            if _matches(document, query):
                return dict(document)
        return None

    def find(self, query: dict[str, Any]) -> FakeCursor:
        return FakeCursor([dict(document) for document in self.documents if _matches(document, query)])

    async def update_one(self, query: dict[str, Any], update: dict[str, Any]):
        document = await self.find_one(query)
        if document is None:
            return type("UpdateResult", (), {"modified_count": 0})()
        for stored in self.documents:
            if _matches(stored, query):
                if "$set" in update:
                    stored.update(update["$set"])
                break
        return type("UpdateResult", (), {"modified_count": 1})()

    async def find_one_and_update(self, query: dict[str, Any], update: dict[str, Any], return_document=None):
        document = await self.find_one(query)
        if document is None:
            return None
        for stored in self.documents:
            if _matches(stored, query):
                if "$set" in update:
                    stored.update(update["$set"])
                return dict(stored)
        return None

    async def create_index(self, *args, **kwargs):
        return None


class FakeDatabase:
    """Dictionary-like fake database object."""

    def __init__(self) -> None:
        self.collections = {
            "users": FakeCollection(),
            "datasets": FakeCollection(),
            "models": FakeCollection(),
            "decision_logs": FakeCollection(),
            "monitoring_alerts": FakeCollection(),
            "review_queue": FakeCollection(),
            "audit_logs": FakeCollection(),
        }

    def __getitem__(self, name: str) -> FakeCollection:
        return self.collections[name]

    async def command(self, *args, **kwargs):
        return {"ok": 1}

    async def list_collection_names(self):
        return list(self.collections.keys())

    async def create_collection(self, name: str, *args, **kwargs):
        self.collections.setdefault(name, FakeCollection())
        return self.collections[name]


@pytest.fixture()
def fake_db() -> FakeDatabase:
    """Return a fresh in-memory fake database."""

    return FakeDatabase()


@pytest.fixture(autouse=True)
def patch_mongo_lifecycle(monkeypatch):
    """Prevent real MongoDB connections during tests."""

    async def _noop_connect():
        return None

    async def _noop_disconnect():
        return None

    monkeypatch.setattr(mongo_db, "connect", _noop_connect)
    monkeypatch.setattr(mongo_db, "disconnect", _noop_disconnect)
