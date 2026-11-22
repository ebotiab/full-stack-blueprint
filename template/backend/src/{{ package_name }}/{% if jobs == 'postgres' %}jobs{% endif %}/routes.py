"""/api/jobs/tick: a scheduler's way to run the due jobs, with `Authorization: Bearer <CRON_SECRET>`."""

import hmac
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from ..api.deps import ConnectionDep
from ..settings import PREFIX, get_settings
from . import queue

router = APIRouter(prefix="/jobs", tags=["jobs"])

#: How long a tick works: well inside a scheduler's timeout and a function's time limit.
TICK_SECONDS = 50.0


class Tick(BaseModel):
    ran: int


# GET as well as POST, because Vercel Cron calls with GET. Two decorators rather than
# `api_route(methods=[...])`, whose operation id depends on set order and changes between runs.
@router.get("/tick")
@router.post("/tick")
async def tick(conn: ConnectionDep, authorization: Annotated[str | None, Header()] = None) -> Tick:
    """Queue the periodic tasks that are due and run due jobs for up to 50 seconds.

    The secret replaces a user: nothing else can call it, and no browser can be tricked into it.
    """
    secret = get_settings().cron_secret
    if not secret:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, f"The tick is off: set {PREFIX}CRON_SECRET."
        )
    if not hmac.compare_digest((authorization or "").encode(), f"Bearer {secret}".encode()):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Wrong or missing CRON_SECRET.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Tick(ran=await queue.run_due(conn, seconds=TICK_SECONDS))
