"""Database connection and collection access helpers."""

from __future__ import annotations

from typing import AsyncIterator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING

from backend.app.core.config import get_settings


COLLECTION_VALIDATORS: dict[str, dict[str, object]] = {
    "users": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["email", "full_name", "hashed_password", "role", "is_active", "created_at", "updated_at"],
            "properties": {
                "email": {"bsonType": "string"},
                "full_name": {"bsonType": "string"},
                "hashed_password": {"bsonType": "string"},
                "role": {"enum": ["admin", "auditor", "user"]},
                "is_active": {"bsonType": "bool"},
            },
        }
    },
    "datasets": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["name", "owner_id", "file_path", "schema_definition", "target_column", "sensitive_columns", "feature_columns", "profile", "preprocessing", "sample_preview", "created_at", "updated_at"],
            "properties": {
                "name": {"bsonType": "string"},
                "owner_id": {"bsonType": "string"},
                "file_path": {"bsonType": "string"},
            },
        }
    },
    "models": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["name", "dataset_id", "owner_id", "algorithm", "target_column", "feature_columns", "artifact_path", "training_summary", "fairness_metrics", "model_card", "status", "created_at", "updated_at"],
            "properties": {
                "name": {"bsonType": "string"},
                "dataset_id": {"bsonType": "string"},
                "owner_id": {"bsonType": "string"},
                "artifact_path": {"bsonType": "string"},
            },
        }
    },
    "decision_logs": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["model_id", "input_payload", "prediction", "probability", "fairness_snapshot", "flags", "requires_review", "created_at"],
            "properties": {
                "model_id": {"bsonType": "string"},
                "prediction": {"bsonType": ["int", "long"]},
                "probability": {"bsonType": "double"},
            },
        }
    },
}


class MongoDatabase:
    """Manage MongoDB Atlas client lifecycle and indexes."""

    def __init__(self) -> None:
        self._client: AsyncIOMotorClient | None = None
        self._database: AsyncIOMotorDatabase | None = None

    async def connect(self) -> None:
        """Initialize the MongoDB client and database handle."""

        if self._database is not None:
            return

        settings = get_settings()
        self._client = AsyncIOMotorClient(
            settings.mongo_uri,
            appname=settings.app_name,
            maxPoolSize=settings.mongo_max_pool_size,
            minPoolSize=settings.mongo_min_pool_size,
            connectTimeoutMS=settings.mongo_connect_timeout_ms,
            socketTimeoutMS=settings.mongo_socket_timeout_ms,
            serverSelectionTimeoutMS=settings.mongo_server_selection_timeout_ms,
            maxIdleTimeMS=300000,
        )
        self._database = self._client[settings.mongo_database]
        await self._database.command("ping")
        await self._ensure_indexes()

    async def disconnect(self) -> None:
        """Close the MongoDB client."""

        if self._client is not None:
            self._client.close()
            self._client = None
            self._database = None

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Return the active database handle."""

        if self._database is None:
            raise RuntimeError("Database connection has not been initialized.")
        return self._database

    async def _ensure_indexes(self) -> None:
        """Create critical indexes for operational workloads."""

        database = self.db
        await self._ensure_collection_validators(database)
        await database["users"].create_index([("email", ASCENDING)], unique=True, background=True)
        await database["datasets"].create_index([("owner_id", ASCENDING), ("created_at", DESCENDING)], background=True)
        await database["models"].create_index([("owner_id", ASCENDING), ("created_at", DESCENDING)], background=True)
        await database["models"].create_index([("dataset_id", ASCENDING)], background=True)
        await database["decision_logs"].create_index([("model_id", ASCENDING), ("created_at", DESCENDING)], background=True)
        await database["monitoring_alerts"].create_index([("model_id", ASCENDING), ("status", ASCENDING)], background=True)
        await database["review_queue"].create_index([("status", ASCENDING), ("created_at", DESCENDING)], background=True)
        await database["audit_logs"].create_index([("created_at", DESCENDING)], background=True)

    async def _ensure_collection_validators(self, database: AsyncIOMotorDatabase) -> None:
        """Create or update collection validators for core collections."""

        existing_collections = set(await database.list_collection_names())
        for collection_name, validator in COLLECTION_VALIDATORS.items():
            if collection_name in existing_collections:
                await database.command({"collMod": collection_name, "validator": validator, "validationLevel": "moderate"})
            else:
                await database.create_collection(collection_name, validator=validator)


mongo_db = MongoDatabase()


async def get_database() -> AsyncIterator[AsyncIOMotorDatabase]:
    """FastAPI dependency that yields the active MongoDB database."""

    yield mongo_db.db

