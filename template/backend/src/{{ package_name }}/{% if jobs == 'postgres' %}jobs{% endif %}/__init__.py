"""Background jobs kept in PostgreSQL: queued work with retries, and periodic tasks.

- `tasks.py` is the project's list: a task is an async function `(conn, payload) -> None`, named in
  `TASKS`; periodic ones are also in `SCHEDULE`.
- A route queues work with `queue.enqueue(conn, "task", {...})`, inside the same transaction as the
  change that needs it, then calls `queue.run_soon(background, request)` so it starts right after the
  response instead of at the next tick.
- `queue.run_due` runs what is due. Three things call it: a loop inside the API process
  (`JOBS_IN_PROCESS`), the `jobs run` / `jobs work` commands, and `/api/jobs/tick`, which a
  scheduler calls with `CRON_SECRET` (the generated GitHub Actions workflow, or the platform's cron).

Delivery is at least once: a job whose worker dies, or that outlives its lease, runs again. Make
tasks idempotent (safe to repeat), and keep them short; long work belongs in a dedicated worker.
"""
