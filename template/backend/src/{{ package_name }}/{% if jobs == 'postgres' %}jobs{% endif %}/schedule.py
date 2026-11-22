"""When periodic tasks are due: every N minutes, or daily at a time (UTC).

Time is cut into periods ("slots"); a task is queued once per slot, whatever the number of
instances or ticks (queue.enqueue_scheduled). A slot nobody ticked in is not made up for: after a
pause, the task runs once, at the next tick.
"""

import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class Every:
    """Every `minutes`, counted from midnight UTC (minutes=15 runs at :00, :15, :30 and :45)."""

    task: str
    minutes: int

    def slot(self, now: dt.datetime) -> dt.datetime:
        seconds = self.minutes * 60
        return dt.datetime.fromtimestamp(now.timestamp() // seconds * seconds, dt.UTC)


@dataclass(frozen=True)
class Daily:
    """Once a day, at the first tick from `at` (UTC) on."""

    task: str
    at: dt.time

    def slot(self, now: dt.datetime) -> dt.datetime:
        today = dt.datetime.combine(now.astimezone(dt.UTC).date(), self.at, dt.UTC)
        return today if now >= today else today - dt.timedelta(days=1)


Periodic = Every | Daily
