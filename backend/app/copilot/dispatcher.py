# app/copilot/dispatcher.py

# pyrefly: ignore [missing-import]

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit
from app.consent.service import has_active_consent
from app.copilot.tools import TOOLS


TOOL_REGISTRY = {tool.name: tool for tool in TOOLS}


# Defense in depth: even though no tool's schema exposes these as
# parameters the LLM can set, strip them from any incoming arguments
# before execution in case a malformed/malicious tool call somehow
# includes them anyway. user_id must ALWAYS come from the authenticated
# session, never from the arguments dict.
FORBIDDEN_ARGUMENT_KEYS = {"user_id", "db"}


def get_tool_schemas() -> list:
    """Returns all tool definitions for the LLM integration."""
    return TOOLS


async def execute_tool(
    db: AsyncSession,
    user_id,
    tool_name: str,
    arguments: dict,
) -> dict:
    """
    The single entry point for running a tool.

    Every tool execution goes through this function so that argument
    sanitization and consent enforcement happen consistently.
    """
    tool = TOOL_REGISTRY.get(tool_name)

    if tool is None:
        return {
            "error": f"Unknown tool: '{tool_name}'. No such tool exists."
        }

    safe_arguments = {
        k: v
        for k, v in arguments.items()
        if k not in FORBIDDEN_ARGUMENT_KEYS
    }

    try:
        # Defense in depth:
        # API routes already enforce consent where applicable, but
        # Copilot tools can be invoked internally by the LLM conversation
        # loop, so consent must also be checked here.
        
        consent_granted = await has_active_consent(
            db,
            user_id,
            tool.required_consent,
        )

        print(
            "COPILOT CONSENT CHECK:",
            "user_id=", user_id,
            "purpose=", tool.required_consent,
            "granted=", consent_granted,
        )

        if not consent_granted:
            await record_audit(
                db,
                "copilot.tool_call",
                user_id=user_id,
                details={
                    "tool": tool_name,
                    "outcome": "denied",
                },
            )

            return {
                "error": (
                    f"The user has not granted consent for "
                    f"'{tool.required_consent}', so this tool cannot be used. "
                    "Tell them they can grant it in the Consent Center."
                )
            }

        result = await tool.executor(
            db,
            user_id,
            **safe_arguments,
        )

        await record_audit(
            db,
            "copilot.tool_call",
            user_id=user_id,
            details={
                "tool": tool_name,
                "outcome": "error" if "error" in result else "ok",
            },
        )

        return result

    except TypeError as e:
        # Arguments didn't match the executor's signature.
        return {
            "error": f"Invalid arguments for tool '{tool_name}': {e}"
        }

    except Exception as e:
        # A single tool failure must never crash the whole conversation turn.
        return {
            "error": f"Tool '{tool_name}' failed to execute: {e}"
        }