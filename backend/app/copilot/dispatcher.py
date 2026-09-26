# app/copilot/dispatcher.py

# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession

from app.copilot.tools import TOOLS

TOOL_REGISTRY = {tool.name: tool for tool in TOOLS}

# Defense in depth: even though no tool's schema exposes these as
# parameters the LLM can set, strip them from any incoming arguments
# before execution, in case a malformed/malicious tool call somehow
# includes them anyway. user_id must ALWAYS come from the authenticated
# session, never from the arguments dict.
FORBIDDEN_ARGUMENT_KEYS = {"user_id", "db"}


def get_tool_schemas() -> list:
    """Returns all tool definitions, for the LLM integration (Step 3) to
    translate into provider-specific tool declarations."""
    return TOOLS


async def execute_tool(
    db: AsyncSession, user_id, tool_name: str, arguments: dict
) -> dict:
    """
    The single, sole entry point for running a tool. Step 3's conversation
    loop must ALWAYS go through this function — never call an executor
    from app.copilot.tools directly. This is what makes tool execution
    safe and uniform: one place that enforces argument sanitization and
    guarantees a tool failure returns as data, never as a crash.
    """
    tool = TOOL_REGISTRY.get(tool_name)
    if tool is None:
        return {"error": f"Unknown tool: '{tool_name}'. No such tool exists."}

    safe_arguments = {
        k: v for k, v in arguments.items() if k not in FORBIDDEN_ARGUMENT_KEYS
    }

    try:
        return await tool.executor(db, user_id, **safe_arguments)
    except TypeError as e:
        # arguments didn't match the executor's signature — e.g. the model
        # omitted a required field or passed an unexpected one despite the
        # schema. Surface as data the LLM can read and adapt to.
        return {"error": f"Invalid arguments for tool '{tool_name}': {e}"}
    except Exception as e:
        # any other failure (DB error, external API failure inside a tool,
        # etc.) — a single tool failing must never crash the whole
        # conversation turn.
        return {"error": f"Tool '{tool_name}' failed to execute: {e}"}