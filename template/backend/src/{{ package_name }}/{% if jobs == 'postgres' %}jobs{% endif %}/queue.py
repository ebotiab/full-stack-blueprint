"""The job queue: plain SQL on the `jobs` table.

A worker claims one due job at a time with `FOR UPDATE SKIP LOCKED`. While a lease is active,
other workers skip the job. After expiry another worker can claim it, and only the worker with
the latest lease can record an outcome. Tasks must be safe to repeat. A failure is
retried later, each time after twice the delay; after `MAX_ATTEMPTS` the job is kept as failed.
A finished job is deleted, so the table only holds pending and failed work.
"""

import asyncio
import datetime as dt
import time
from collections.abc import Mapping, Sequence
from typing import Any, cast

import asyncpg
import logfire
from fastapi import BackgroundTasks, Request

from ..db.pool import Database
from .schedule import Periodic
from .tasks import SCHEDULE, TASKS, Task

#: How long a claimed job stays reserved for its worker. A job that runs longer may run twice.
LEASE = dt.timedelta(minutes=5)
MAX_ATTEMPTS = 5
#: Delay before the first retry; it doubles each time (30 s, 1, 2, 4 minutes), up to `MAX_RETRY`.
FIRST_RETRY = dt.timedelta(seconds=30)
MAX_RETRY = dt.timedelta(hours=1)
#: How often the worker loop looks again when nothing was due.
POLL_SECONDS = 5.0
#: How long `run_soon` works after a response.
RUN_SOON_SECONDS = 10.0

_CLAIM = """
UPDATE jobs SET attempts = attempts + 1, locked_until = now() + $1::interval,
                lease_id = gen_random_uuid()
WHERE id = (
    SELECT id FROM jobs
    WHERE failed_at IS NULL AND run_at <= now()
      AND (locked_until IS NULL OR locked_until < now())
    ORDER BY run_at, id
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
RETURNING id, task, payload, attempts, lease_id
"""


async def enqueue(
    conn: asyncpg.Connection,
    task: str,
    payload: Mapping[str, Any] | None = None,
    *,
    delay: dt.timedelta = dt.timedelta(0),
) -> int:
    """Queue `task` with `payload` (JSON), to run after `delay`; returns the job's id.

    Call it inside the transaction of the change that needs the job: if that change is rolled
    back, the job is never queued.
    """
    if task not in TASKS:
        raise ValueError(f"Unknown task {task!r}: add it to TASKS in jobs/tasks.py.")
    job_id = await conn.fetchval(
        "INSERT INTO jobs (task, payload, run_at) VALUES ($1, $2, now() + $3::interval) RETURNING id",
        task,
        dict(payload or {}),
        delay,
    )
    return cast(int, job_id)


async def enqueue_scheduled(
    conn: asyncpg.Connection,
    schedule: Sequence[Periodic] = SCHEDULE,
    now: dt.datetime | None = None,
) -> list[str]:
    """Queue each periodic task whose current slot is not queued yet; returns their names.

    The upsert on `job_schedule` moves `last_slot` forward only once per slot, so concurrent ticks
    and instances queue a periodic task once.
    """
    now = now or dt.datetime.now(dt.UTC)
    queued: list[str] = []
    for periodic in schedule:
        async with conn.transaction():
            moved = await conn.fetchval(
                """
                INSERT INTO job_schedule (task, last_slot) VALUES ($1, $2)
                ON CONFLICT (task) DO UPDATE SET last_slot = EXCLUDED.last_slot
                WHERE job_schedule.last_slot < EXCLUDED.last_slot
                RETURNING task
                """,
                periodic.task,
                periodic.slot(now),
            )
            if moved is not None:
                await enqueue(conn, periodic.task)
                queued.append(periodic.task)
    return queued


async def run_due(
    conn: asyncpg.Connection,
    *,
    seconds: float,
    tasks: Mapping[str, Task] = TASKS,
    schedule: Sequence[Periodic] = SCHEDULE,
) -> int:
    """Queue the periodic tasks that are due, then run due jobs for up to `seconds`.

    Returns how many jobs ran (failed attempts included).
    """
    deadline = time.monotonic() + seconds
    await enqueue_scheduled(conn, schedule)
    ran = 0
    while time.monotonic() < deadline:
        job = await conn.fetchrow(_CLAIM, LEASE)
        if job is None:
            break
        await _run(conn, job, tasks)
        ran += 1
    return ran


async def _run(conn: asyncpg.Connection, job: asyncpg.Record, tasks: Mapping[str, Task]) -> None:
    name = job["task"]
    with logfire.span("job {task}", task=name, job_id=job["id"], attempt=job["attempts"]):
        task = tasks.get(name)
        try:
            if task is None:
                raise LookupError(f"No task named {name!r} in TASKS.")
            await task(conn, job["payload"])
        except Exception as error:
            logfire.exception("job {task} failed", task=name, attempt=job["attempts"])
            final = task is None or job["attempts"] >= MAX_ATTEMPTS
            delay = min(FIRST_RETRY * 2 ** (job["attempts"] - 1), MAX_RETRY)
            await conn.execute(
                """
                UPDATE jobs SET locked_until = NULL, lease_id = NULL, last_error = $2,
                    run_at = now() + $3::interval, failed_at = CASE WHEN $4 THEN now() END
                WHERE id = $1 AND lease_id = $5
                """,
                job["id"],
                f"{type(error).__name__}: {error}"[:2000],
                delay,
                final,
                job["lease_id"],
            )
        else:
            await conn.execute(
                "DELETE FROM jobs WHERE id = $1 AND lease_id = $2", job["id"], job["lease_id"]
            )


async def run_forever(database: Database, poll_seconds: float = POLL_SECONDS) -> None:
    """The worker loop of the API process (`JOBS_IN_PROCESS`) and of `jobs work`; ends when cancelled.

    A failing round (the database is down, a migration is missing) is logged and retried later:
    the loop must not die with the process still serving.
    """
    while True:
        ran = 0
        try:
            pool = await database.pool()
            async with pool.acquire() as conn:
                ran = await run_due(cast(asyncpg.Connection, conn), seconds=60)
        except Exception:
            logfire.exception("background jobs could not run")
        if ran == 0:
            await asyncio.sleep(poll_seconds)


def run_soon(background: BackgroundTasks, request: Request) -> None:
    """After the response, run due jobs for a few seconds: what the route queued starts now."""
    background.add_task(_run_briefly, request.app.state.database)


async def _run_briefly(database: Database) -> None:
    try:
        pool = await database.pool()
        async with pool.acquire() as conn:
            await run_due(cast(asyncpg.Connection, conn), seconds=RUN_SOON_SECONDS)
    except Exception:
        logfire.exception("background jobs could not run after the response")
