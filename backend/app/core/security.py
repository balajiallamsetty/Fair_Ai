"""Authentication and authorization utilities."""

from datetime import datetime, timedelta, timezone
from functools import partial
from typing import Any, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.app.core.config import get_settings
from backend.app.core.database import get_database
from backend.app.schemas.user_schema import TokenPayload, UserPublic
from backend.app.utils.helpers import document_to_schema, object_id_str


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{get_settings().api_prefix}/governance/auth/login")


def _validate_secret_strength(secret: str) -> None:
    """Reject weak or placeholder JWT secrets."""

    placeholders = {"change_this_to_a_long_random_secret_in_production", "replace_with_secure_jwt_secret", ""}
    if secret in placeholders or len(secret) < 32:
        raise ValueError("JWT secret must be at least 32 characters and not a placeholder value.")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a secure hash."""

    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""

    return pwd_context.hash(password)


def create_access_token(subject: str, role: str, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""

    settings = get_settings()
    _validate_secret_strength(settings.jwt_secret_key)
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"sub": subject, "role": role, "exp": int(expire.timestamp())}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def authenticate_user(database: Any, email: str, password: str) -> dict[str, Any] | None:
    """Authenticate a user by email/password pair."""

    user = await database["users"].find_one({"email": email})
    if user is None:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    if not user.get("is_active", True):
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    database=Depends(get_database),
) -> UserPublic:
    """Resolve the current authenticated user from a JWT."""

    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        token_data = TokenPayload(**payload)
    except (JWTError, ValueError):
        raise credentials_exception from None

    user = await database["users"].find_one({"_id": object_id_str(token_data.sub, as_object_id=True)})
    if user is None:
        raise credentials_exception

    return document_to_schema(user, UserPublic)


def require_roles(*roles: str) -> Callable[[UserPublic], UserPublic]:
    """Return a dependency that enforces one of the allowed roles."""

    async def role_dependency(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' does not have access to this resource.",
            )
        return current_user

    return role_dependency


def require_resource_access(resource_owner_id: str) -> Callable[[UserPublic], UserPublic]:
    """Return a dependency that allows admins or the resource owner."""

    async def access_dependency(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
        if current_user.role == "admin" or current_user.id == resource_owner_id:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this resource.",
        )

    return access_dependency


def get_current_user_with_access(collection_name: str) -> Callable[..., Any]:
    """Return a dependency that checks resource ownership by collection name."""

    async def access_dependency(
        resource_id: str,
        current_user: UserPublic = Depends(get_current_user),
        database=Depends(get_database),
    ) -> UserPublic:
        if current_user.role == "admin":
            return current_user

        resource = await database[collection_name].find_one({"_id": object_id_str(resource_id, as_object_id=True)})
        if resource is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found.")
        if resource.get("owner_id") != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this resource.")
        return current_user

    return access_dependency


def validate_runtime_security_settings() -> None:
    """Validate runtime security settings during startup."""

    settings = get_settings()
    _validate_secret_strength(settings.jwt_secret_key)
