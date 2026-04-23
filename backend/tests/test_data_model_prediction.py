"""Dataset upload, model training, and prediction tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from backend.app.core.database import get_database
from backend.app.core.security import get_current_user
from backend.app.main import app


def _current_user():
    from backend.app.schemas.user_schema import UserPublic
    from datetime import datetime, timezone

    return UserPublic(
        id="user-1",
        email="tester@example.com",
        full_name="Test User",
        role="user",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def test_upload_train_predict_flow(fake_db, tmp_path):
    """Dataset upload should feed training and prediction end-to-end."""

    app.dependency_overrides[get_database] = lambda: fake_db
    app.dependency_overrides[get_current_user] = _current_user
    client = TestClient(app)

    csv_path = tmp_path / "train.csv"
    pd.DataFrame(
        {
            "age": [18, 25, 40, 30],
            "income": [100, 250, 400, 300],
            "gender": ["F", "M", "F", "M"],
            "approved": [0, 1, 0, 1],
        }
    ).to_csv(csv_path, index=False)

    with csv_path.open("rb") as file_handle:
        upload_response = client.post(
            "/api/v1/data/datasets/upload",
            data={
                "name": "sample",
                "target_column": "approved",
                "sensitive_columns": "gender",
            },
            files={"file": ("train.csv", file_handle, "text/csv")},
        )
    assert upload_response.status_code == 200
    dataset_id = upload_response.json()["id"]

    train_response = client.post(
        "/api/v1/models/train",
        json={"dataset_id": dataset_id, "name": "model-1", "test_size": 0.25, "random_state": 42},
    )
    assert train_response.status_code == 200
    model_id = train_response.json()["id"]

    dataset_doc = fake_db["datasets"].documents[0]
    training_frame = pd.read_csv(Path(dataset_doc["file_path"]))
    feature_payload = {"age": int(training_frame.loc[0, "age"]), "income": int(training_frame.loc[0, "income"])}

    predict_response = client.post(
        f"/api/v1/monitoring/models/{model_id}/predict",
        json={
            "features": feature_payload,
            "sensitive_attributes": {"gender": "F"},
            "metadata": {"source": "pytest"},
        },
    )
    assert predict_response.status_code == 200
    assert predict_response.json()["decision_log_id"]

    app.dependency_overrides.clear()
