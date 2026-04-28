# 🐞 Bugs Report

## 1. Project Overview
- Summary of project purpose: Fair-AI Guardian is a FastAPI backend for dataset ingestion, bias analysis, model training, mitigation, explainability, monitoring, and governance workflows.
- Detected tech stack: FastAPI, Pydantic v2, Motor/PyMongo, Pandas, NumPy, scikit-learn, python-jose, passlib, pytest, httpx.
- High-level architecture:
  - API layer: [backend/app/api/routes/data_routes.py](backend/app/api/routes/data_routes.py), [backend/app/api/routes/bias_routes.py](backend/app/api/routes/bias_routes.py), [backend/app/api/routes/model_routes.py](backend/app/api/routes/model_routes.py), [backend/app/api/routes/monitoring_routes.py](backend/app/api/routes/monitoring_routes.py), [backend/app/api/routes/governance_routes.py](backend/app/api/routes/governance_routes.py)
  - Service layer: [backend/app/services](backend/app/services)
  - Core infra/config/security/db: [backend/app/core](backend/app/core)
  - Schemas/models/utilities/tests: [backend/app/schemas](backend/app/schemas), [backend/app/models](backend/app/models), [backend/app/utils](backend/app/utils), [backend/tests](backend/tests)
- Scope note: All project text source/config/test files were read line-by-line. Binary/generated artifacts were inspected as artifacts (CSV content and pickle header metadata), not decompiled.

## 2. Critical Issues (Must Fix Immediately)

### Critical 1
- File: [backend/app/core/security.py](backend/app/core/security.py#L121), [backend/app/core/security.py](backend/app/core/security.py#L125), [backend/app/api/routes/data_routes.py](backend/app/api/routes/data_routes.py#L47), [backend/app/api/routes/data_routes.py](backend/app/api/routes/data_routes.py#L75), [backend/app/api/routes/model_routes.py](backend/app/api/routes/model_routes.py#L43), [backend/app/api/routes/bias_routes.py](backend/app/api/routes/bias_routes.py#L34)
- Line: 121, 125, 47, 75, 43, 34
- Issue: Broken dependency parameter mapping causes protected resource routes to return 422.
- Root Cause: Access dependency expects resource_id, but route path params are dataset_id/model_id; FastAPI treats resource_id as missing query parameter.
- Expected vs Actual:
  - Expected: Authorized user gets resource data.
  - Actual: 422 with missing query field resource_id.
- Impact: Core dataset/model/report retrieval endpoints are unusable.
- Fix Recommendation: Make dependency parameter names match route params, or use a dependency factory that accepts param name and extracts from request.path_params.
- Verification: Reproduced with TestClient; GET /api/v1/data/datasets/{id}, /profile, /api/v1/models/{id}, /api/v1/bias/datasets/{id}/report all returned 422.

### Critical 2
- File: [backend/app/services/model_service.py](backend/app/services/model_service.py#L76), [backend/app/services/model_service.py](backend/app/services/model_service.py#L83), [backend/app/services/mitigation_service.py](backend/app/services/mitigation_service.py#L48)
- Line: 76, 83, 48
- Issue: Unsafe pickle deserialization for model artifacts.
- Root Cause: Model artifacts are loaded with pickle.load directly from artifact_path in DB.
- Expected vs Actual:
  - Expected: Artifact loading should be integrity-checked and safe against code execution.
  - Actual: If artifact path or content is tampered, arbitrary code execution risk exists.
- Impact: High-severity RCE risk under DB compromise or path manipulation.
- Fix Recommendation: Replace pickle with a safer model serialization strategy (joblib with signed files at minimum, or ONNX/skops), validate artifact paths, and add integrity signatures (HMAC/SHA256 + key management).

### Critical 3
- File: [.env](.env#L1), [.env](.env#L4), [backend/app/main.py](backend/app/main.py#L29), [backend/app/core/database.py](backend/app/core/database.py#L89)
- Line: 1, 4, 29, 89
- Issue: Default startup fails with placeholder environment values.
- Root Cause: .env has placeholder MONGO_URI/JWT secret; startup immediately pings Mongo in lifespan.
- Expected vs Actual:
  - Expected: Project should start with documented valid env defaults or fail with clear setup mode guidance.
  - Actual: Uvicorn startup fails with ServerSelectionTimeoutError against placeholder host.
- Impact: Developer onboarding and deployment smoke tests fail out-of-box.
- Fix Recommendation: Provide .env.example with placeholders and require real .env; add startup preflight error message that explicitly points to required variables.

### Critical 4
- File: [backend/app/api/routes/bias_routes.py](backend/app/api/routes/bias_routes.py#L18), [backend/app/api/routes/bias_routes.py](backend/app/api/routes/bias_routes.py#L20)
- Line: 18, 20
- Issue: Bias analysis endpoint lacks ownership/resource access validation.
- Root Cause: Endpoint only checks role, not whether user owns dataset or is allowed to access it.
- Expected vs Actual:
  - Expected: Non-admin users should only analyze authorized datasets.
  - Actual: User can analyze another user’s dataset by ID.
- Impact: Cross-tenant data exposure and unauthorized processing.
- Fix Recommendation: Use get_current_user_with_access("datasets") (after fixing dependency bug) or explicit ownership checks in service layer.
- Verification: Reproduced with TestClient: user u1 successfully analyzed dataset owned by u2 (HTTP 200).

## 3. Major Issues

### Major 1
- File: [backend/app/services/mitigation_service.py](backend/app/services/mitigation_service.py#L91)
- Line: 91
- Issue: Mitigation retraining corrupts target labels for non-numeric classes.
- Root Cause: Target converted via pd.to_numeric(...).fillna(0).astype(int), collapsing string labels into 0.
- Expected vs Actual:
  - Expected: Mitigation should preserve trained class encoding semantics.
  - Actual: Non-numeric labels are coerced and information is lost.
- Impact: Wrong mitigation outcomes and invalid fairness/accuracy metrics.
- Fix Recommendation: Reuse label encoder from artifact (same as training pipeline) before split/fit.

### Major 2
- File: [backend/app/services/mitigation_service.py](backend/app/services/mitigation_service.py#L93)
- Line: 93
- Issue: Stratified split can fail on small datasets during mitigation.
- Root Cause: train_test_split stratify=y is enabled without minimum class-count/test-size guards.
- Expected vs Actual:
  - Expected: Small datasets should fall back gracefully.
  - Actual: ValueError may occur when class counts are too small.
- Impact: Mitigation endpoint becomes unstable on realistic small-team datasets.
- Fix Recommendation: Apply same can_stratify guard pattern used in training service.

### Major 3
- File: [backend/app/services/monitoring_service.py](backend/app/services/monitoring_service.py#L186), [backend/app/services/monitoring_service.py](backend/app/services/monitoring_service.py#L181), [backend/app/services/monitoring_service.py](backend/app/services/monitoring_service.py#L182)
- Line: 186, 181, 182
- Issue: Governance report cache key ignores pagination params.
- Root Cause: cache_key uses only dataset_id/model_id, not page/page_size.
- Expected vs Actual:
  - Expected: Different page requests produce different cache entries.
  - Actual: Same cached payload can be returned for different pages.
- Impact: Incorrect report pagination and stale governance decisions.
- Fix Recommendation: Include page/page_size and role/tenant context in cache key; add bounded cache eviction.

### Major 4
- File: [backend/app/services/monitoring_service.py](backend/app/services/monitoring_service.py#L20), [backend/app/core/config.py](backend/app/core/config.py#L41), [backend/app/services/monitoring_service.py](backend/app/services/monitoring_service.py#L69)
- Line: 20, 41, 69
- Issue: Live fairness cache/window behavior is inconsistent and fragile.
- Root Cause:
  - Cache deque maxlen is hard-coded 200 regardless of FAIRNESS_MONITOR_WINDOW.
  - FAIRNESS_MONITOR_WINDOW has no validator for >=1.
  - Query uses limit(settings.fairness_monitor_window - 1), which can become invalid.
- Expected vs Actual:
  - Expected: Runtime window should follow config safely.
  - Actual: Window can mismatch or fail under edge configs.
- Impact: Monitoring fairness snapshots can be inaccurate or crash on bad config.
- Fix Recommendation: Validate FAIRNESS_MONITOR_WINDOW >= 2 and bind deque maxlen to config.

### Major 5
- File: [backend/app/core/database.py](backend/app/core/database.py#L128)
- Line: 128
- Issue: collMod validator updates can fail startup in restricted DB roles.
- Root Cause: Startup always executes collMod/create_collection operations.
- Expected vs Actual:
  - Expected: App should run with least-privilege runtime role and optional migration/admin path.
  - Actual: Startup can fail when runtime DB user lacks DDL privileges.
- Impact: Production outages due to permission mismatch.
- Fix Recommendation: Move schema/index migration to an admin migration command, keep runtime startup read/write-only.

### Major 6
- File: [backend/app/core/security.py](backend/app/core/security.py#L86)
- Line: 86
- Issue: Malformed JWT subject returns 400 instead of 401.
- Root Cause: object_id_str can raise HTTPException 400 and is not mapped to credentials_exception.
- Expected vs Actual:
  - Expected: Invalid credentials should consistently return 401.
  - Actual: 400 Bad Request leaks internal validation behavior.
- Impact: Inconsistent auth semantics and noisy client handling.
- Fix Recommendation: Catch HTTPException from ObjectId conversion and rethrow credentials_exception.
- Verification: Reproduced via TestClient with validly signed token but non-ObjectId sub; got 400.

### Major 7
- File: [backend/app/schemas/model_schema.py](backend/app/schemas/model_schema.py#L25)
- Line: 25
- Issue: ModelTrainRequest lacks bounds validation for test_size.
- Root Cause: test_size is free float with no range constraint.
- Expected vs Actual:
  - Expected: Accept only sensible split range (e.g., 0.05 to 0.5).
  - Actual: Out-of-range values can trigger runtime split errors.
- Impact: Avoidable API failures and weak input contract.
- Fix Recommendation: Add Field(gt=0, lt=1) and service-level dataset-size checks.

### Major 8
- File: [backend/app/services/monitoring_service.py](backend/app/services/monitoring_service.py#L44), [backend/app/services/model_service.py](backend/app/services/model_service.py#L76)
- Line: 44, 76
- Issue: Model artifact is loaded from disk on every prediction.
- Root Cause: predict_and_monitor calls load_model_artifact each request with no in-memory model cache.
- Expected vs Actual:
  - Expected: Hot model cache to avoid repeated disk IO/deserialization.
  - Actual: Per-request disk read/deserialization overhead.
- Impact: Latency spikes and poor throughput under load.
- Fix Recommendation: Add bounded in-memory model cache with invalidation on artifact updates.

## 4. Minor Issues

### Minor 1
- File: [backend/app/core/security.py](backend/app/core/security.py#L4)
- Line: 4
- Issue: Unused import partial.
- Root Cause: Leftover import not used in module.
- Impact: Noise and maintainability drift.
- Fix Recommendation: Remove unused import.

### Minor 2
- File: [backend/app/api/routes/data_routes.py](backend/app/api/routes/data_routes.py#L5), [backend/app/api/routes/model_routes.py](backend/app/api/routes/model_routes.py#L5), [backend/app/api/routes/governance_routes.py](backend/app/api/routes/governance_routes.py#L7)
- Line: 5, 5, 7
- Issue: Unused imports (HTTPException/status in several routes).
- Root Cause: Import cleanup incomplete after refactor.
- Impact: Minor code quality and readability degradation.
- Fix Recommendation: Remove unused imports and enable lint gates.

### Minor 3
- File: [backend/app/services/mitigation_service.py](backend/app/services/mitigation_service.py#L52)
- Line: 52
- Issue: Orphan helper _predict_class_probability is declared but unused.
- Root Cause: Refactor artifact left behind.
- Impact: Dead code confusion.
- Fix Recommendation: Remove it or use shared helper from one module.

### Minor 4
- File: [backend/app/services/monitoring_service.py](backend/app/services/monitoring_service.py#L25), [backend/app/services/explainability_service.py](backend/app/services/explainability_service.py#L16)
- Line: 25, 16
- Issue: Duplicated predicted-class-probability helper logic.
- Root Cause: Utility duplication across services.
- Impact: Divergence risk on future bug fixes.
- Fix Recommendation: Move into shared utility function.

### Minor 5
- File: [backend/app/schemas/bias_schema.py](backend/app/schemas/bias_schema.py#L24), [backend/app/schemas/bias_schema.py](backend/app/schemas/bias_schema.py#L37), [backend/app/schemas/dataset_schema.py](backend/app/schemas/dataset_schema.py#L49)
- Line: 24, 37, 49
- Issue: Defined schemas are currently not used by route responses.
- Root Cause: Incomplete schema wiring.
- Impact: Weaker API contract consistency.
- Fix Recommendation: Use response_model declarations for these schemas where appropriate.

### Minor 6
- File: [backend/tests/test_auth.py](backend/tests/test_auth.py#L12), [backend/tests/test_data_model_prediction.py](backend/tests/test_data_model_prediction.py#L30)
- Line: 12, 30
- Issue: Test coverage is narrow (2 positive-path tests only).
- Root Cause: Missing negative-path and auth/access integration tests.
- Impact: Critical regressions escaped (notably 422 access dependency bug).
- Fix Recommendation: Add tests for protected read endpoints, auth failures, invalid token behavior, pagination cache correctness, and mitigation edge cases.

## 5. Failure Analysis
- Failing functionality 1: Default backend startup.
  - Why it fails: Placeholder DB URI in [.env](.env#L1) causes Mongo connection failure during lifespan startup at [backend/app/main.py](backend/app/main.py#L29) and [backend/app/core/database.py](backend/app/core/database.py#L89).
  - Execution breakdown: app startup -> lifespan -> mongo_db.connect -> ping -> server selection timeout -> app exits.

- Failing functionality 2: Dataset/model/profile/report fetch endpoints.
  - Why they fail: Dependency mismatch (resource_id query expected, dataset_id/model_id path provided).
  - Execution breakdown: request enters route -> dependency resolution requests query resource_id -> missing field -> 422 returned before handler.

- Failing functionality 3: Token validation consistency.
  - Why it fails: Invalid ObjectId in JWT subject leads to 400 in [backend/app/core/security.py](backend/app/core/security.py#L86), not normalized to 401.
  - Execution breakdown: decode token -> convert sub to ObjectId -> HTTP 400 thrown -> client sees Bad Request.

- Failing functionality 4: Cross-tenant bias analysis authorization.
  - Why it fails: analyze endpoint lacks ownership check.
  - Execution breakdown: role check passes -> service loads dataset by ID -> analysis runs even for non-owner.

## 6. Security Loopholes
- Vulnerability: Unsafe pickle deserialization from DB-driven path.
  - Risk Level: Critical
  - Exploit Scenario: Attacker alters model artifact path/content and triggers prediction/explain/mitigate to execute payload.
  - Fix: Signed artifacts, strict path allowlist, safer serialization format.

- Vulnerability: Broken object-level authorization (IDOR) in bias analyze endpoint.
  - Risk Level: Critical
  - Exploit Scenario: Authenticated user analyzes another tenant’s dataset by guessing ID.
  - Fix: Enforce ownership checks for all dataset/model operations.

- Vulnerability: Auth error leakage via 400 for malformed subject.
  - Risk Level: Medium
  - Exploit Scenario: Client can distinguish malformed-subject tokens from other invalid credentials.
  - Fix: Always normalize to 401 for credential failures.

- Vulnerability: Plaintext artifact CSV persistence with potentially sensitive fields.
  - Risk Level: Medium
  - Exploit Scenario: Filesystem compromise reveals full raw datasets.
  - Fix: Encrypt-at-rest, access-control filesystem boundary, retention policy.

## 7. Performance Issues
- Bottleneck: Per-request model artifact disk load/deserialization on predict path.
  - Evidence: [backend/app/services/monitoring_service.py](backend/app/services/monitoring_service.py#L44)
  - Optimization: Add memory cache with TTL and version invalidation.

- Bottleneck: Full governance report queries with repeated conversion and no selective projections.
  - Evidence: [backend/app/services/monitoring_service.py](backend/app/services/monitoring_service.py#L206)
  - Optimization: Add field projections, separate paginated endpoints by resource, and aggregate counts separately.

- Inefficient code pattern: Recomputing DB backfill for live window in cold cache path on prediction.
  - Evidence: [backend/app/services/monitoring_service.py](backend/app/services/monitoring_service.py#L63)
  - Optimization: Keep synchronized rolling window store and avoid repeated historical fetches.

## 8. Architecture & Design Problems
- Poor structure: Runtime schema models in [backend/app/models](backend/app/models) are not integrated into the service/route data flow.
- Tight coupling: Service modules perform direct persistence concerns, audit writes, and ML logic together, increasing change blast radius.
- Lack of modularity: Duplicate probability helper logic across services; no shared prediction utility boundary.
- Config management gap: Runtime-critical config validation is incomplete (window/test-size constraints missing).

## 9. Database Issues
- Connection problem: Startup hard-depends on immediate DB connectivity (no degraded mode).
  - Evidence: [backend/app/main.py](backend/app/main.py#L29), [backend/app/core/database.py](backend/app/core/database.py#L89)

- Missing resiliency in schema management:
  - Evidence: [backend/app/core/database.py](backend/app/core/database.py#L128)
  - Issue: collMod at startup can fail in restricted production roles.

- Query inefficiency risk:
  - Evidence: [backend/app/services/monitoring_service.py](backend/app/services/monitoring_service.py#L215)
  - Issue: audit_logs queried globally per report request; no tenant scoping or projection.

## 10. API Issues
- Broken endpoints: Protected resource GET endpoints return 422 due dependency wiring mismatch.
- Invalid auth semantics: malformed token subject returns 400 instead of 401.
- Integration failure points:
  - Startup fails if env placeholders unchanged.
  - Bias analyze endpoint bypasses object-level authorization.
- Request contract weakness: train request test_size unbounded can trigger runtime errors.

## 11. Missing / Risky Configurations
- Environment variables:
  - Placeholder DB URI in [.env](.env#L1)
  - Placeholder JWT secret in [.env](.env#L4)
- Secrets handling risk:
  - Real secret may be committed into .env in future; recommend .env excluded and .env.example committed.
- Deployment risks:
  - No startup mode separation for migration/admin DB operations.
  - No CORS/middleware policy configured for frontend integration in [backend/app/main.py](backend/app/main.py).
- Configuration drift:
  - passlib configured for pbkdf2 in [backend/app/core/security.py](backend/app/core/security.py#L18) but dependency still includes bcrypt extra in [requirements.txt](requirements.txt#L8).

## 12. Recommendations (Action Plan)
1. Fix authorization dependency contract immediately.
   - Refactor get_current_user_with_access to accept route param name and resolve from request.path_params.
   - Add regression tests for all protected read endpoints.
2. Remove unsafe pickle trust boundary.
   - Add artifact signature validation and strict artifact path allowlist.
   - Plan migration away from raw pickle load for untrusted paths.
3. Repair startup/deployment configuration flow.
   - Introduce .env.example, fail-fast validation with human-readable setup instructions.
   - Move index/validator migrations to separate admin task.
4. Harden model/mitigation data handling.
   - Reuse LabelEncoder for mitigation target transformations.
   - Add stratify fallback guards and strict request bounds.
5. Correct monitoring/governance cache design.
   - Include page/page_size/user scope in cache key.
   - Bound cache size and add explicit invalidation on write events.
6. Improve performance and scalability.
   - Add in-memory model cache for prediction path.
   - Add query projections and scoped report endpoints.
7. Raise quality bar in CI.
   - Add ruff + mypy + pytest coverage thresholds.
   - Add security scanners (bandit, pip-audit) and dependency checks.

## 13. Final Verdict
- Project health score (0–10): 5.8/10
- Production readiness status: Not production-ready in current state.
- Summary of biggest risks:
  - Core protected GET APIs are functionally broken (422).
  - Critical security risks exist (unsafe pickle load, object-level authorization gap).
  - Default runtime startup fails without manual env correction.
  - Monitoring/governance caching and mitigation logic contain correctness/scalability risks.