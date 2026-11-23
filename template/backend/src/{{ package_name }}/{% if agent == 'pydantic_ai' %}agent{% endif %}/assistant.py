"""The agent: its instructions, its tools and the limits of one run.

Grow it here: more tools (`@agent.tool_plain`, or `@agent.tool` with a `RunContext` to reach
dependencies), a richer output type, other agents next to it. The model is not set here: the caller
passes the one the `AI_MODEL` setting names (agent/model.py), so the API starts without a provider
key, and tests pass Pydantic AI's TestModel or FunctionModel instead.
"""

import datetime as dt

from pydantic import BaseModel
from pydantic_ai import Agent, UsageLimits

INSTRUCTIONS = (
    "You are the assistant of this application. Answer briefly and plainly. "
    "Use your tools when they help, and say so when you do not know."
)

#: What one run may spend, so a question cannot keep the model and its tools looping.
LIMITS = UsageLimits(request_limit=5, total_tokens_limit=20_000)


class AgentAnswer(BaseModel):
    """What the agent returns, validated by Pydantic."""

    answer: str


agent = Agent(None, name="assistant", instructions=INSTRUCTIONS, output_type=AgentAnswer)


@agent.tool_plain
def current_time() -> str:
    """The current date and time in UTC, in ISO 8601."""
    return dt.datetime.now(dt.UTC).isoformat()
