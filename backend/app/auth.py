import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

bearer_scheme = HTTPBearer(auto_error=False)


def get_jwt_secret_key() -> str:
    jwt_secret_key = os.getenv("JWT_SECRET_KEY")

    if not jwt_secret_key:
        raise HTTPException(
            status_code=500,
            detail="JWT_SECRET_KEY is not configured on the server.",
        )

    return jwt_secret_key


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_context.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    user_id: UUID,
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    return jwt.encode(
        payload,
        get_jwt_secret_key(),
        algorithm=JWT_ALGORITHM,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization token.",
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization scheme.",
        )

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            get_jwt_secret_key(),
            algorithms=[JWT_ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload.",
            )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )

    user = (
        db.query(User)
        .filter(User.id == UUID(str(user_id)))
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is disabled.",
        )

    return user