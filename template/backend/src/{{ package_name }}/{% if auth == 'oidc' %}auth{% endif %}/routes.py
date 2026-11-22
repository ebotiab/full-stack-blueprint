"""Sign-in routes under /api/auth. Signing in and out happen at the provider, not here."""

from fastapi import APIRouter

from .deps import CurrentUser, User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def me(user: CurrentUser) -> User:
    """The caller of a valid token: 401 without one."""
    return user
