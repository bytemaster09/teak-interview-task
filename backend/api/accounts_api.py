from django.contrib.auth import authenticate
from ninja import Router
from ninja.errors import HttpError
from ninja.responses import Status

from .auth import create_access_token, create_refresh_token, decode_token, jwt_auth
from .schemas import (
    AccessTokenOut,
    ErrorOut,
    LoginIn,
    RefreshIn,
    RegisterIn,
    TokenOut,
    UserOut,
)

router = Router(tags=["auth"])


@router.post("/register", response={201: TokenOut, 400: ErrorOut})
def register(request, data: RegisterIn):
    from accounts.models import User

    if data.role not in ("author", "reader"):
        raise HttpError(400, "role must be 'author' or 'reader'")

    if User.objects.filter(email=data.email).exists():
        raise HttpError(400, "Email already registered")

    if User.objects.filter(username=data.username).exists():
        raise HttpError(400, "Username already taken")

    user = User.objects.create_user(
        email=data.email,
        username=data.username,
        password=data.password,
        role=data.role,
    )
    return Status(201, TokenOut(
        access=create_access_token(user.pk),
        refresh=create_refresh_token(user.pk),
    ))


@router.post("/login", response={200: TokenOut, 401: ErrorOut})
def login(request, data: LoginIn):
    user = authenticate(request, username=data.email, password=data.password)
    if user is None:
        raise HttpError(401, "Invalid credentials")
    return TokenOut(
        access=create_access_token(user.pk),
        refresh=create_refresh_token(user.pk),
    )


@router.post("/refresh", response={200: AccessTokenOut, 401: ErrorOut})
def refresh(request, data: RefreshIn):
    user_id = decode_token(data.refresh, "refresh")
    if user_id is None:
        raise HttpError(401, "Invalid or expired refresh token")
    from accounts.models import User
    try:
        user = User.objects.get(pk=user_id, is_active=True)
    except User.DoesNotExist:
        raise HttpError(401, "User not found")
    return AccessTokenOut(access=create_access_token(user.pk))


@router.get("/me", auth=jwt_auth, response={200: UserOut, 401: ErrorOut})
def me(request):
    u = request.user
    return UserOut(
        id=u.pk,
        email=u.email,
        username=u.username,
        role=u.role,
        bio=u.bio,
    )
