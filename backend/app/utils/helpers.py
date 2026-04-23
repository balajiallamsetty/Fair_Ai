"""Shared helper utilities for schemas, files, and audit events."""

from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeVar
from uuid import uuid4

import pandas as pd
from bson import ObjectId
from fastapi import HTTPException, UploadFile, status
from pydantic import BaseModel

from backend.app.core.storage import get_storage_backend


SchemaT = TypeVar("SchemaT", bound=BaseModel)


def utc_now() -> datetime:
    """Return a timezone-aware UTC datetime."""

    return datetime.now(timezone.utc)


def object_id_str(value: str | ObjectId, as_object_id: bool = False) -> str | ObjectId:
    """Normalize a string/ObjectId value for API or database usage."""

    if as_object_id:
        if isinstance(value, ObjectId):
            return value
        if ObjectId.is_valid(str(value)):
            return ObjectId(str(value))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ObjectId supplied.")
    if isinstance(value, ObjectId):
        return str(value)
    return str(value)


def serialize_document(document: dict[str, Any]) -> dict[str, Any]:
    """Convert MongoDB ObjectIds within a document to strings."""

    serialized: dict[str, Any] = {}
    for key, value in document.items():
        output_key = "id" if key == "_id" else key
        if isinstance(value, ObjectId):
            serialized[output_key] = str(value)
        elif isinstance(value, list):
            serialized[output_key] = [
                serialize_document(item) if isinstance(item, dict) else object_id_str(item)
                if isinstance(item, ObjectId)
                else item
                for item in value
            ]
        elif isinstance(value, dict):
            serialized[output_key] = serialize_document(value)
        else:
            serialized[output_key] = value
    return serialized


def document_to_schema(document: dict[str, Any], schema_type: type[SchemaT]) -> SchemaT:
    """Convert a MongoDB document into a Pydantic schema."""

    return schema_type.model_validate(serialize_document(document))


async def read_csv_upload(upload: UploadFile) -> pd.DataFrame:
    """Read a CSV upload into a DataFrame."""

    if not upload.filename or not upload.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV uploads are supported.")
    contents = await upload.read()
    try:
        return pd.read_csv(io.BytesIO(contents))
    except Exception as exc:  # pragma: no cover - library-specific error text
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unable to parse CSV: {exc}") from exc


def persist_dataframe(dataframe: pd.DataFrame, target_dir: Path, prefix: str) -> str:
    """Persist a DataFrame to a CSV artifact and return the path."""

    storage = get_storage_backend(target_dir)
    relative_path = f"{prefix}_{uuid4().hex}.csv"
    return storage.save_text(relative_path, dataframe.to_csv(index=False))


def persist_json(payload: dict[str, Any], target_dir: Path, prefix: str) -> str:
    """Persist JSON content to disk and return the file path."""

    storage = get_storage_backend(target_dir)
    relative_path = f"{prefix}_{uuid4().hex}.json"
    return storage.save_text(relative_path, json.dumps(payload, indent=2, default=str))


def clean_column_names(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Normalize DataFrame column names into snake_case-like values."""

    dataframe.columns = [
        str(column).strip().lower().replace(" ", "_").replace("-", "_")
        for column in dataframe.columns
    ]
    return dataframe


def infer_schema(dataframe: pd.DataFrame) -> dict[str, str]:
    """Infer a lightweight schema from a DataFrame."""

    return {column: str(dtype) for column, dtype in dataframe.dtypes.items()}


def build_dataset_profile(dataframe: pd.DataFrame) -> dict[str, Any]:
    """Build a profile summary for a DataFrame."""

    working_frame = dataframe.sample(n=min(len(dataframe), 10000), random_state=42) if len(dataframe) > 10000 else dataframe
    missing_counts = working_frame.isna().sum().to_dict()
    numeric_frame = working_frame.select_dtypes(include=["number"])
    numeric_summary = numeric_frame.describe().fillna(0).to_dict() if not numeric_frame.empty else {}
    return {
        "rows": int(dataframe.shape[0]),
        "columns": int(dataframe.shape[1]),
        "column_names": list(dataframe.columns),
        "dtypes": infer_schema(dataframe),
        "missing_values": {key: int(value) for key, value in missing_counts.items()},
        "numeric_summary": numeric_summary,
        "categorical_summary": {
            column: working_frame[column].astype(str).value_counts().head(5).to_dict()
            for column in working_frame.select_dtypes(exclude=["number"]).columns
        },
    }


async def create_audit_log(
    database,
    *,
    actor_id: str,
    actor_role: str,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict[str, Any] | None = None,
) -> None:
    """Persist an audit log entry."""

    await database["audit_logs"].insert_one(
        {
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": details or {},
            "created_at": utc_now(),
        }
    )
