from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from django.conf import settings
from ninja.security import HttpBearer


def _make_token(payload: dict, expire: timedelta) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {**payload, "iat": now, "exp": now + expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: int) -> str:
    return _make_token(
        {"sub": str(user_id), "type": "access"},
        timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: int) -> str:
    return _make_token(
        {"sub": str(user_id), "type": "refresh"},
        timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, expected_type: str) -> Optional[int]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != expected_type:
            return None
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


class JWTAuth(HttpBearer):
    def authenticate(self, request, token: str):
        user_id = decode_token(token, "access")
        if user_id is None:
            return None
        from accounts.models import User
        try:
            user = User.objects.get(pk=user_id, is_active=True)
            request.user = user
            return user
        except User.DoesNotExist:
            return None


jwt_auth = JWTAuth()
