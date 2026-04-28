"""Application entry point for Fair-AI Guardian backend."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes.bias_routes import router as bias_router
from backend.app.api.routes.data_routes import router as data_router
from backend.app.api.routes.governance_routes import router as governance_router
from backend.app.api.routes.model_routes import router as model_router
from backend.app.api.routes.monitoring_routes import router as monitoring_router
from backend.app.core.config import get_settings
from backend.app.core.database import mongo_db
from backend.app.core.security import validate_runtime_security_settings
from backend.app.utils.logger import get_logger


logger = get_logger(__name__)
settings = get_settings()

# Parse CORS origins from environment variable
def get_cors_origins() -> list[str]:
	"""Get CORS origins from environment variable or use defaults."""
	cors_env = os.getenv("CORS_ORIGINS", "")
	if cors_env:
		return [origin.strip() for origin in cors_env.split(",")]
	# Default origins for local development
	return [
		"http://127.0.0.1:5173",
		"http://127.0.0.1:5174",
		"http://localhost:5173",
		"http://localhost:5174",
		"http://localhost:3000",
	]


@asynccontextmanager
async def lifespan(_: FastAPI):
	"""Handle application startup and shutdown lifecycle."""

	validate_runtime_security_settings()
	await mongo_db.connect()
	logger.info("MongoDB connection established.")
	yield
	await mongo_db.disconnect()
	logger.info("MongoDB connection closed.")


app = FastAPI(
	title=settings.app_name,
	version=settings.app_version,
	debug=settings.debug,
	lifespan=lifespan,
)

# Configure CORS with dynamic origins from environment
cors_origins = get_cors_origins()
logger.info(f"CORS Origins configured: {cors_origins}")

app.add_middleware(
	CORSMiddleware,
	allow_origins=cors_origins,
	allow_credentials=False,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
	"""Return health status for liveness probes."""

	return {"status": "ok", "service": settings.app_name}


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
	"""Return API information."""

	return {
		"message": "Fair AI Guardian API",
		"version": settings.app_version,
		"docs": "/docs",
		"health": "/health",
	}


app.include_router(data_router, prefix=settings.api_prefix)
app.include_router(bias_router, prefix=settings.api_prefix)
app.include_router(model_router, prefix=settings.api_prefix)
app.include_router(monitoring_router, prefix=settings.api_prefix)
app.include_router(governance_router, prefix=settings.api_prefix)

