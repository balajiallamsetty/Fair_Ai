# Fair-AI Guardian Platform

## 1. Project Overview

Fair-AI Guardian Platform is a FastAPI-based backend for building fairer, safer, and more transparent ML workflows. It lets teams upload datasets, inspect bias, train models, run predictions, monitor live fairness signals, and generate governance reports from a single API surface.

What it solves:
- Centralizes dataset ingestion, model lifecycle, and fairness governance.
- Helps teams detect bias before and after training.
- Supports operational monitoring for live prediction workflows.
- Exposes clear APIs that a frontend can use to manage the full workflow.

Key features:
- Dataset upload and profiling
- Bias analysis and bias report storage
- Logistic regression model training
- Mitigation workflows: reweighting and resampling
- Explainability and counterfactual analysis
- Live prediction with fairness monitoring
- Governance reporting, review queue, and audit logging
- JWT authentication and role-based access control

---

## 2. Backend Setup

### Prerequisites

- Python 3.13+
- MongoDB instance or MongoDB Atlas
- Node.js only if you plan to build the frontend
- Git

### Installation Steps

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies.
4. Configure environment variables.
5. Run the FastAPI server.

### Virtual Environment Setup

From the project root:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Requirements Installation

```bash
pip install -r requirements.txt
```

### Run the FastAPI Server

Run from the repository root:

```bash
uvicorn backend.app.main:app --reload
```

If you want to specify the host and port:

```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Important Startup Note

The application validates security and MongoDB settings at startup. You must provide a real MongoDB URI and a strong JWT secret in `.env`, otherwise startup will fail.

---

## 3. Environment Configuration

Create a `.env` file at the repository root with the following values:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DATABASE=fair_ai_guardian
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=use_a_long_random_32_characters_minimum_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
MODEL_ARTIFACTS_DIR=backend/artifacts/models
DATASET_ARTIFACTS_DIR=backend/artifacts/datasets
LOG_LEVEL=INFO
FAIRNESS_MONITOR_WINDOW=200
PREDICTION_BIAS_THRESHOLD=0.2
MONGO_MAX_POOL_SIZE=50
MONGO_MIN_POOL_SIZE=5
MONGO_SERVER_SELECTION_TIMEOUT_MS=5000
MONGO_CONNECT_TIMEOUT_MS=10000
MONGO_SOCKET_TIMEOUT_MS=30000
```

### What each variable does

- `MONGO_URI`: MongoDB connection string.
- `MONGO_DATABASE`: Database name used by the backend.
- `REDIS_URL`: Optional Redis URL for future caching or background workflows.
- `JWT_SECRET_KEY`: Secret used to sign access tokens.
- `JWT_ALGORITHM`: JWT signing algorithm.
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token lifetime.
- `MODEL_ARTIFACTS_DIR`: Folder where trained model artifacts are saved.
- `DATASET_ARTIFACTS_DIR`: Folder where uploaded dataset artifacts are saved.
- `LOG_LEVEL`: Application log level.
- `FAIRNESS_MONITOR_WINDOW`: Window size used for live fairness snapshots.
- `PREDICTION_BIAS_THRESHOLD`: Threshold used to flag live monitoring risk.
- `MONGO_MAX_POOL_SIZE`, `MONGO_MIN_POOL_SIZE`: MongoDB client pool sizing.
- `MONGO_SERVER_SELECTION_TIMEOUT_MS`, `MONGO_CONNECT_TIMEOUT_MS`, `MONGO_SOCKET_TIMEOUT_MS`: MongoDB connection timeouts.

---

## 4. Backend File Structure

```text
backend/
├── app/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── api/
│   │   └── routes/
│   └── utils/
└── tests/
```

### Folder Purpose

- `core/`
  - App configuration, database lifecycle, authentication, authorization, and storage abstraction.
- `models/`
  - MongoDB-oriented document models used to describe persisted data structures.
- `schemas/`
  - Pydantic request/response models for API contracts.
- `services/`
  - Business logic for data ingestion, bias analysis, training, mitigation, explainability, and monitoring.
- `api/routes/`
  - FastAPI route handlers grouped by feature area.
- `utils/`
  - Shared helpers for serialization, logging, metrics, file persistence, and audit logging.
- `tests/`
  - Pytest test suite with fake MongoDB fixtures and end-to-end API coverage.

### Other important folders

- `backend/artifacts/models/`
  - Saved trained model artifacts.
- `backend/artifacts/datasets/`
  - Saved uploaded/cleaned dataset artifacts.
- `database/`
  - Currently empty in this workspace.
- `frontend/`
  - Currently empty in this workspace; recommended frontend structure is documented below.

---

## 5. Complete API Documentation

### Base URL

```text
http://localhost:8000/api/v1
```

### Authentication

Protected routes use JWT Bearer authentication.

#### Endpoint:

```text
POST /governance/auth/register
```

### Description

Registers a new platform user.

### Request

- Body: JSON

```json
{
  "email": "alice@example.com",
  "full_name": "Alice Example",
  "password": "StrongPass123!",
  "role": "user"
}
```

### Response

```json
{
  "id": "65f...",
  "email": "alice@example.com",
  "full_name": "Alice Example",
  "role": "user",
  "is_active": true,
  "created_at": "2026-04-23T12:00:00Z",
  "updated_at": "2026-04-23T12:00:00Z"
}
```

### Use Case

Used by the frontend registration page to create new users.

---

#### Endpoint:

```text
POST /governance/auth/login
```

### Description

Authenticates a user and returns a JWT access token.

### Request

- Body: JSON

```json
{
  "email": "alice@example.com",
  "password": "StrongPass123!"
}
```

### Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "65f...",
    "email": "alice@example.com",
    "full_name": "Alice Example",
    "role": "user",
    "is_active": true,
    "created_at": "2026-04-23T12:00:00Z",
    "updated_at": "2026-04-23T12:00:00Z"
  }
}
```

### Use Case

Used by the frontend login page to authenticate the session.

---

### Data APIs

#### Endpoint:

```text
POST /data/datasets/upload
```

### Description

Uploads a CSV dataset, normalizes column names, fills missing values, profiles the data, saves the file artifact, and stores dataset metadata.

### Request

- Body: form-data
- Fields:
  - `name` string
  - `description` optional string
  - `target_column` string
  - `sensitive_columns` comma-separated string
  - `feature_columns` optional comma-separated string
  - `file` CSV file

Example:

```text
name=sample
description=customer risk dataset
target_column=approved
sensitive_columns=gender
feature_columns=age,income
file=train.csv
```

### Response

```json
{
  "id": "65f...",
  "name": "sample",
  "description": "customer risk dataset",
  "owner_id": "65f...",
  "file_path": "backend/artifacts/datasets/dataset_x.csv",
  "schema_definition": {
    "age": "int64",
    "income": "int64",
    "gender": "object",
    "approved": "int64"
  },
  "target_column": "approved",
  "sensitive_columns": ["gender"],
  "feature_columns": ["age", "income"],
  "profile": {},
  "preprocessing": {},
  "bias_report": null,
  "sample_preview": [],
  "created_at": "2026-04-23T12:00:00Z",
  "updated_at": "2026-04-23T12:00:00Z"
}
```

### Use Case

Frontend needs this to upload training data and start the model workflow.

---

#### Endpoint:

```text
GET /data/datasets
```

### Description

Lists datasets. If `mine=true`, returns only the current user’s datasets.

### Request

- Query params:
  - `mine` optional boolean

### Response

```json
{
  "datasets": [],
  "total": 0
}
```

### Use Case

Used by dashboards to show available datasets.

---

#### Endpoint:

```text
GET /data/datasets/{dataset_id}
```

### Description

Returns a single dataset record.

### Request

- Path param: `dataset_id`

### Response

```json
{
  "id": "65f...",
  "name": "sample",
  "description": null,
  "owner_id": "65f...",
  "file_path": "backend/artifacts/datasets/dataset_x.csv",
  "schema_definition": {},
  "target_column": "approved",
  "sensitive_columns": ["gender"],
  "feature_columns": ["age", "income"],
  "profile": {},
  "preprocessing": {},
  "bias_report": null,
  "sample_preview": [],
  "created_at": "2026-04-23T12:00:00Z",
  "updated_at": "2026-04-23T12:00:00Z"
}
```

### Use Case

Used by dataset detail views.

---

#### Endpoint:

```text
GET /data/datasets/{dataset_id}/profile
```

### Description

Returns the stored dataset profile snapshot.

### Request

- Path param: `dataset_id`

### Response

```json
{
  "id": "65f...",
  "profile": {},
  "created_at": "2026-04-23T12:00:00Z"
}
```

### Use Case

Used by dataset profile cards and analytics views.

---

### Bias APIs

#### Endpoint:

```text
POST /bias/datasets/{dataset_id}/analyze
```

### Description

Runs dataset bias analysis and stores the bias report in the dataset document.

### Request

- Path param: `dataset_id`
- Body: none

### Response

```json
{
  "dataset_id": "65f...",
  "generated_at": "2026-04-23T12:00:00Z",
  "bias_score": 0.18,
  "group_analysis": {},
  "distribution_comparison": {},
  "proxy_detection": {},
  "intersectional_analysis": {},
  "recommendations": []
}
```

### Use Case

Used by frontend bias analysis actions and governance workflows.

---

#### Endpoint:

```text
GET /bias/datasets/{dataset_id}/report
```

### Description

Returns the latest stored bias report for a dataset.

### Request

- Path param: `dataset_id`

### Response

```json
{
  "dataset_id": "65f...",
  "bias_report": {
    "generated_at": "2026-04-23T12:00:00Z",
    "bias_score": 0.18,
    "group_analysis": {},
    "distribution_comparison": {},
    "proxy_detection": {},
    "intersectional_analysis": {},
    "recommendations": []
  }
}
```

### Use Case

Used by the bias report page.

---

### Model APIs

#### Endpoint:

```text
POST /models/train
```

### Description

Trains a logistic regression model from a dataset, stores the model artifact, and saves training/fairness metadata.

### Request

- Body: JSON

```json
{
  "dataset_id": "65f...",
  "name": "model-1",
  "test_size": 0.25,
  "random_state": 42
}
```

### Response

```json
{
  "id": "65f...",
  "name": "model-1",
  "dataset_id": "65f...",
  "owner_id": "65f...",
  "algorithm": "logistic_regression",
  "target_column": "approved",
  "sensitive_columns": ["gender"],
  "feature_columns": ["age", "income"],
  "artifact_path": "backend/artifacts/models/model_x.pkl",
  "preprocessing_artifact_path": null,
  "training_summary": {},
  "fairness_metrics": {},
  "mitigation_results": null,
  "explainability": null,
  "model_card": {},
  "status": "ready",
  "created_at": "2026-04-23T12:00:00Z",
  "updated_at": "2026-04-23T12:00:00Z"
}
```

### Use Case

Used by the model training page after a dataset is uploaded.

---

#### Endpoint:

```text
GET /models
```

### Description

Lists trained models. If `mine=true`, returns only the current user’s models.

### Request

- Query params:
  - `mine` optional boolean

### Response

```json
[
  {
    "id": "65f...",
    "name": "model-1",
    "dataset_id": "65f...",
    "owner_id": "65f...",
    "algorithm": "logistic_regression",
    "target_column": "approved",
    "sensitive_columns": ["gender"],
    "feature_columns": ["age", "income"],
    "artifact_path": "backend/artifacts/models/model_x.pkl",
    "preprocessing_artifact_path": null,
    "training_summary": {},
    "fairness_metrics": {},
    "mitigation_results": null,
    "explainability": null,
    "model_card": {},
    "status": "ready",
    "created_at": "2026-04-23T12:00:00Z",
    "updated_at": "2026-04-23T12:00:00Z"
  }
]
```

### Use Case

Used by dashboards and model inventory views.

---

#### Endpoint:

```text
GET /models/{model_id}
```

### Description

Returns a single model record.

### Request

- Path param: `model_id`

### Response

```json
{
  "id": "65f...",
  "name": "model-1",
  "dataset_id": "65f...",
  "owner_id": "65f...",
  "algorithm": "logistic_regression",
  "target_column": "approved",
  "sensitive_columns": ["gender"],
  "feature_columns": ["age", "income"],
  "artifact_path": "backend/artifacts/models/model_x.pkl",
  "preprocessing_artifact_path": null,
  "training_summary": {},
  "fairness_metrics": {},
  "mitigation_results": null,
  "explainability": null,
  "model_card": {},
  "status": "ready",
  "created_at": "2026-04-23T12:00:00Z",
  "updated_at": "2026-04-23T12:00:00Z"
}
```

### Use Case

Used by model detail pages.

---

#### Endpoint:

```text
POST /models/{model_id}/mitigate
```

### Description

Applies a mitigation strategy to the trained model and stores before/after fairness comparison.

### Request

- Body: JSON

```json
{
  "strategy": "reweighting"
}
```

### Response

```json
{
  "model_id": "65f...",
  "mitigation": {
    "strategy": "reweighting",
    "before": {},
    "after": {},
    "applied_at": "2026-04-23T12:00:00Z"
  }
}
```

### Use Case

Used by governance and model fairness remediation screens.

---

#### Endpoint:

```text
POST /models/{model_id}/explain
```

### Description

Generates feature importance and counterfactual outcomes for a model.

### Request

- Body: JSON

```json
{
  "base_features": {
    "age": 30,
    "income": 300
  },
  "candidate_changes": [
    {
      "income": 320
    }
  ]
}
```

### Response

```json
{
  "feature_importance": [],
  "baseline_prediction": {
    "prediction": 1,
    "probability": 0.82
  },
  "counterfactuals": [
    {
      "changes": {
        "income": 320
      },
      "prediction": 1,
      "probability": 0.84,
      "prediction_changed": false
    }
  ]
}
```

### Use Case

Used by explainability screens and model review workflows.

---

### Monitoring APIs

#### Endpoint:

```text
POST /monitoring/models/{model_id}/predict
```

### Description

Runs a live prediction, computes fairness snapshot, stores a decision log, and creates alerts/review items when needed.

### Request

- Body: JSON

```json
{
  "features": {
    "age": 30,
    "income": 300
  },
  "sensitive_attributes": {
    "gender": "F"
  },
  "metadata": {
    "source": "frontend"
  }
}
```

### Response

```json
{
  "model_id": "65f...",
  "prediction": 1,
  "probability": 0.82,
  "fairness_snapshot": {
    "window_size": 1,
    "group_positive_rates": {
      "F": 1.0
    },
    "parity_gap": 0.0
  },
  "flags": [],
  "requires_review": false,
  "decision_log_id": "65f..."
}
```

### Use Case

Used by the prediction UI and live monitoring dashboards.

---

#### Endpoint:

```text
GET /monitoring/alerts
```

### Description

Lists monitoring alerts.

### Request

- Query params:
  - `model_id` optional string
  - `status` optional string

### Response

```json
{
  "alerts": [],
  "total": 0
}
```

### Use Case

Used by the monitoring page and alert center.

---

### Governance APIs

#### Endpoint:

```text
GET /governance/report
```

### Description

Generates a governance report containing the dataset, model, alerts, open reviews, and audit logs.

### Request

- Query params:
  - `dataset_id` optional string
  - `model_id` optional string
  - `page` optional integer, default 1
  - `page_size` optional integer, default 50

### Response

```json
{
  "generated_at": "2026-04-23T12:00:00Z",
  "dataset": null,
  "model": null,
  "alerts": [],
  "open_reviews": [],
  "audit_logs": []
}
```

### Use Case

Used by governance dashboards and compliance exports.

---

#### Endpoint:

```text
GET /governance/model-card/{model_id}
```

### Description

Returns model card details for a trained model.

### Request

- Path param: `model_id`

### Response

```json
{
  "model_id": "65f...",
  "model_card": {}
}
```

### Use Case

Used by model governance views.

---

#### Endpoint:

```text
GET /governance/review-queue
```

### Description

Lists pending or filtered review items.

### Request

- Query params:
  - `status_filter` optional string, default `pending`

### Response

```json
{
  "items": [],
  "total": 0
}
```

### Use Case

Used by the human review queue page.

---

#### Endpoint:

```text
POST /governance/review-queue/{review_id}/resolve
```

### Description

Marks a review queue item as approved or rejected and closes related alerts when present.

### Request

- Path param: `review_id`
- Query/body value: `decision` must be `approved` or `rejected`

Example:

```json
{
  "decision": "approved"
}
```

### Response

```json
{
  "id": "65f...",
  "decision_log_id": "65f...",
  "model_id": "65f...",
  "reason": ["low_confidence_prediction"],
  "status": "approved",
  "assigned_to": null,
  "created_at": "2026-04-23T12:00:00Z",
  "updated_at": "2026-04-23T12:00:00Z",
  "alert_id": "65f...",
  "reviewed_by": "65f...",
  "reviewed_by_role": "auditor"
}
```

### Use Case

Used by governance review workflows.

---

### Health API

#### Endpoint:

```text
GET /health
```

### Description

Returns service health for liveness checks.

### Response

```json
{
  "status": "ok",
  "service": "Fair-AI Guardian Platform"
}
```

### Use Case

Used by deployment health checks and monitoring.

---

## 6. Complete API Flow

```text
Register → Login → Upload Dataset → Analyze Bias → Train Model → Predict → Monitor → Review → Resolve
```

Typical flow:
1. Register or login through governance auth.
2. Upload a CSV dataset.
3. Run bias analysis on the dataset.
4. Train a model on that dataset.
5. Send live prediction requests.
6. Monitor alerts and fairness snapshots.
7. Review queued decisions.
8. Resolve review outcomes.

---

## 7. Data Flow

How data moves through the system:

1. A user uploads a CSV dataset through the data API.
2. The backend cleans column names, fills missing values, stores the artifact, and saves metadata in MongoDB.
3. Bias analysis reads the dataset artifact, computes group, proxy, and intersectional fairness indicators, and writes the bias report back into the dataset document.
4. Training loads the saved dataset artifact, prepares features and labels, trains a logistic regression pipeline, stores the model artifact, and writes model metadata to MongoDB.
5. Prediction loads the saved model artifact, validates feature payloads, returns the prediction probability for the predicted class, and stores a decision log.
6. Monitoring checks the current prediction against recent history, creates fairness snapshots, raises alerts, and queues human review items when thresholds are exceeded.
7. Governance endpoints aggregate models, alerts, audit logs, and review outcomes into a single report for compliance and oversight.

---

## 8. Frontend File Structure

Recommended frontend structure:

```text
frontend/
│
├── src/
│   ├── components/
│   ├── pages/
│   ├── services/
│   ├── hooks/
│   ├── utils/
│   ├── App.jsx
│   ├── main.jsx
│
├── public/
```

### Folder Purpose

- `components/`
  - Reusable UI pieces like tables, cards, modals, charts, forms, and alerts.
- `pages/`
  - Top-level screens such as Login, Dashboard, Dataset Upload, Bias Report, Model Training, Monitoring, and Governance.
- `services/`
  - API client wrappers for calling the backend.
- `hooks/`
  - Shared React hooks for auth, data loading, polling, and state management.
- `utils/`
  - Helpers for formatting dates, numbers, auth tokens, and API errors.
- `App.jsx`
  - Main application shell and routing setup.
- `main.jsx`
  - Frontend entry point.
- `public/`
  - Static assets like logos and icons.

---

## 9. How to Build Frontend

Use React and Tailwind CSS.

### Step 1: Create React App

```bash
npm create vite@latest frontend
cd frontend
npm install
```

### Step 2: Install Tailwind CSS

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### Step 3: Configure Tailwind

Update `tailwind.config.js` so Tailwind scans your source files:

```js
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

In your main CSS file, add Tailwind directives:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### Step 4: Run Frontend

```bash
npm run dev
```

---

## 10. Frontend ↔ Backend Integration

### Base URL

```text
http://localhost:8000
```

The API is served under:

```text
http://localhost:8000/api/v1
```

### Calling APIs

Use `fetch` or `axios` from the frontend.

Example with `fetch`:

```javascript
fetch("http://localhost:8000/api/v1/data/datasets", {
  method: "GET",
  headers: {
    Authorization: `Bearer ${token}`,
  },
});
```

Example with `axios`:

```javascript
import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000/api/v1",
});

api.get("/models", {
  headers: { Authorization: `Bearer ${token}` },
});
```

### Auth Header

Protected routes require:

```text
Authorization: Bearer <JWT_TOKEN>
```

### Upload Example

```javascript
const formData = new FormData();
formData.append("name", "sample");
formData.append("target_column", "approved");
formData.append("sensitive_columns", "gender");
formData.append("file", file);

fetch("http://localhost:8000/api/v1/data/datasets/upload", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`,
  },
  body: formData,
});
```

---

## 11. Frontend Pages Required

### Login/Register Page
- Registers users.
- Logs users in and stores JWT token.

### Dashboard
- Shows datasets, models, alerts, and governance status.

### Upload Dataset Page
- Uploads CSV data and configures target/sensitive columns.

### Bias Report Page
- Shows stored bias analysis and recommendations.

### Model Training Page
- Starts model training and shows training summary.

### Monitoring Page
- Shows live predictions, alerts, and fairness snapshot information.

### Governance Page
- Shows review queue, audit logs, and governance report output.

---

## 12. Error Handling

### Common Backend Errors

- `400 Bad Request`
  - Invalid CSV, invalid ObjectId, invalid input values, or malformed request data.
- `401 Unauthorized`
  - Missing or invalid JWT token.
- `403 Forbidden`
  - User does not have access to the resource.
- `404 Not Found`
  - Dataset, model, or review item not found.
- `409 Conflict`
  - Duplicate registration email.
- `422 Unprocessable Entity`
  - Validation failures in request payloads or dependency parameters.
- `500 Internal Server Error`
  - Unexpected runtime or infrastructure failure.

### Frontend Handling Guidance

- Show user-friendly validation messages for `400` and `422`.
- Redirect to login on `401`.
- Show permission denied UI on `403`.
- Show not found state on `404`.
- Show retry or fallback state for `500`.
- For upload/training actions, display loading and progress states clearly.

---

## 13. Testing

### FastAPI Docs

Run the backend and open:

```text
http://localhost:8000/docs
```

Use Swagger UI to test authenticated and public endpoints.

### Postman

You can also test the APIs in Postman by:
1. Registering a user.
2. Logging in to obtain a JWT.
3. Adding the token to the Authorization header.
4. Calling dataset, model, monitoring, bias, and governance endpoints.

### Existing Backend Tests

Run:

```bash
pytest backend/tests -q
```

Current tests cover:
- User registration and login
- Dataset upload → model train → prediction flow

---

## 14. Security Notes

- JWT tokens are required for protected routes.
- Authentication is handled through OAuth2 password bearer tokens.
- Role-based access control is used for admin, auditor, and user access.
- Resource-level authorization is intended for dataset/model access.
- Model artifacts are stored on disk and loaded by the backend, so artifact integrity should be protected carefully in production.

---

## 15. Final Summary

Fair-AI Guardian Platform provides a backend foundation for dataset management, model training, bias analysis, monitoring, explainability, and governance.

What the system achieves:
- Centralizes fairness-aware ML workflows.
- Gives frontend apps a stable contract for auth, data, model, monitoring, and governance operations.
- Supports a full review loop from upload to prediction to governance resolution.

How to extend it:
- Add richer model types and retraining workflows.
- Add frontend dashboards for bias and governance analytics.
- Introduce background jobs for long-running training and monitoring.
- Strengthen artifact signing, audit retention, and observability for production deployment.
